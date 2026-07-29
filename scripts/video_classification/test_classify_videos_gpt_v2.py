import importlib.util
import json
import unittest
import uuid
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch


SCRIPT_PATH = Path(__file__).with_name("classify_videos_gpt_v2.py")
SPEC = importlib.util.spec_from_file_location("classifier_v2", SCRIPT_PATH)
CLASSIFIER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(CLASSIFIER)


class ClassifierContractTests(unittest.TestCase):
    def test_sanitized_payload_does_not_store_transcript(self):
        payload = {
            "video": {
                "post_id": "video1",
                "transcript_90s": "texto completo",
                "transcription_metadata": {"transcript_sha256": "abc"},
            }
        }

        sanitized = CLASSIFIER.sanitize_harness_input_for_storage(payload)

        self.assertIsNone(sanitized["video"]["transcript_90s"])
        self.assertTrue(sanitized["video"]["transcript_redacted"])
        self.assertEqual(payload["video"]["transcript_90s"], "texto completo")

    def test_title_stage_requires_not_evaluated_quality(self):
        quality = {
            "quality_score": None,
            "quality_status": "not_evaluated",
            "issues": [],
            "impact_on_classification": "none",
            "needs_retranscription": False,
        }
        classification = {"confidence_score": 0.85, "needs_human_review": False}

        CLASSIFIER.validate_transcript_quality(quality, classification, "title_metadata")

    def test_high_impact_caps_confidence(self):
        quality = {
            "quality_score": 0.40,
            "quality_status": "poor",
            "issues": ["incoherent"],
            "impact_on_classification": "high",
            "needs_retranscription": True,
        }
        classification = {"confidence_score": 0.70, "needs_human_review": True}

        with self.assertRaisesRegex(ValueError, "impact high"):
            CLASSIFIER.validate_transcript_quality(
                quality,
                classification,
                "transcript_90s",
            )

    def test_transcript_csv_keeps_empty_row_for_quality_evaluation(self):
        temp_dir = SCRIPT_PATH.parents[2] / "tmp" / "video_classification_tests"
        temp_dir.mkdir(parents=True, exist_ok=True)
        path = temp_dir / f"transcripts_{uuid.uuid4().hex}.csv"
        try:
            path.write_text(
                "post_id,transcript_90s,source_method\nvideo1,,manual\n",
                encoding="utf-8",
            )

            rows = CLASSIFIER.load_transcripts_csv(path)
        finally:
            if path.exists():
                path.unlink()

        self.assertIn("video1", rows)
        self.assertEqual(rows["video1"]["text"], "")
        self.assertEqual(rows["video1"]["metadata"]["transcript_char_count"], 0)

    def test_external_schema_matches_embedded_required_blocks(self):
        schema_path = (
            SCRIPT_PATH.parents[2]
            / "docs"
            / "external_data"
            / "58_GPT_VIDEO_CLASSIFIER_OUTPUT_SCHEMA_V2.json"
        )
        external = json.loads(schema_path.read_text(encoding="utf-8"))

        self.assertEqual(external["required"], CLASSIFIER.DEFAULT_SCHEMA["required"])
        self.assertEqual(external["$id"], CLASSIFIER.OUTPUT_SCHEMA_VERSION)
        self.assertIn("transcript_quality", external["properties"])

    def test_transcription_duration_uses_full_short_video_and_caps_long_video(self):
        self.assertEqual(CLASSIFIER.target_transcription_duration(42, 90), 42)
        self.assertEqual(CLASSIFIER.target_transcription_duration(600, 90), 90)
        self.assertEqual(CLASSIFIER.target_transcription_duration(None, 90), 90)

    def test_download_audio_segment_passes_po_token_options_to_ytdlp(self):
        temp_dir = SCRIPT_PATH.parents[2] / "tmp" / "video_classification_tests"
        temp_dir.mkdir(parents=True, exist_ok=True)
        plugin_dir = temp_dir / "yt_dlp_plugins"
        plugin_dir.mkdir(exist_ok=True)
        output_path = temp_dir / f"audio_{uuid.uuid4().hex}.wav"
        output_path.write_bytes(b"placeholder")
        try:
            with patch.object(
                CLASSIFIER,
                "run_subprocess",
                return_value=SimpleNamespace(returncode=0, stderr="", stdout=""),
            ) as run_subprocess:
                CLASSIFIER.download_audio_segment(
                    "video1",
                    90,
                    output_path,
                    "ffmpeg",
                    extractor_args=["youtube:player-client=default,mweb"],
                    plugin_dirs=[plugin_dir],
                )

            command = run_subprocess.call_args.args[0]
            self.assertIn("--extractor-args", command)
            self.assertIn("youtube:player-client=default,mweb", command)
            self.assertIn("--plugin-dirs", command)
            self.assertIn(str(plugin_dir), command)
        finally:
            if output_path.exists():
                output_path.unlink()

    def test_write_persists_quality_and_redacts_transcript(self):
        result = {
            "classification_result": {
                "post_id": "video1",
                "evaluation_stage": "transcript_90s",
                "input_evidence_level": "transcript_90s",
                "automotive_domain": "review_teste",
                "activity_type": "review",
                "topic_path": "review_teste__review_veiculo",
                "topic_path_secondary": None,
                "content_type": "review",
                "audience_intent": "decidir_compra",
                "confidence_score": 0.85,
                "evidence_summary": "evidencia",
                "taxonomy_gaps": None,
                "validation_issues": None,
                "needs_human_review": False,
                "taxonomy_version": "taxonomia_video_v2",
            },
            "transcript_quality": {
                "quality_score": 0.85,
                "quality_status": "usable",
                "issues": [],
                "impact_on_classification": "low",
                "needs_retranscription": False,
            },
            "technical_contexts": [],
            "vehicle_entities": [],
        }
        harness = {"video": {"transcript_90s": "texto completo"}}

        with patch.object(CLASSIFIER, "request_json", return_value=[{"id": 10}]) as request:
            CLASSIFIER.write_classification(
                "https://example.supabase.co",
                {"apikey": "test"},
                1,
                1,
                "gpt-5-nano",
                harness,
                result,
                {"id": "response1"},
            )

        payload = request.call_args_list[0].kwargs["payload"]
        self.assertEqual(payload["transcript_quality_score"], 0.85)
        self.assertIsNone(payload["input_payload"]["video"]["transcript_90s"])


if __name__ == "__main__":
    unittest.main()
