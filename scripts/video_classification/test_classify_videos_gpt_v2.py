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

    def test_description_csv_sets_title_description_evidence(self):
        temp_dir = SCRIPT_PATH.parents[2] / "tmp" / "video_classification_tests"
        temp_dir.mkdir(parents=True, exist_ok=True)
        path = temp_dir / f"descriptions_{uuid.uuid4().hex}.csv"
        try:
            path.write_text(
                "post_id,description_status,description\n"
                "video1,success,Descricao automotiva\n",
                encoding="utf-8",
            )

            descriptions = CLASSIFIER.load_descriptions_csv(path)
            harness = CLASSIFIER.build_harness_input(
                {"post_id": "video1", "title": "Teste"},
                "title_metadata",
                {"version": "taxonomia_video_v2", "topic_paths": [], "compatibility": []},
                {},
                description=descriptions["video1"]["description"],
            )
        finally:
            if path.exists():
                path.unlink()

        self.assertEqual(harness["video"]["description"], "Descricao automotiva")
        self.assertEqual(harness["video"]["input_evidence_level"], "title_description")

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
                    proxy="socks5://127.0.0.1:11080",
                )

            command = run_subprocess.call_args[0][0]
            self.assertIn("--extractor-args", command)
            self.assertIn("youtube:player-client=default,mweb", command)
            self.assertIn("--plugin-dirs", command)
            self.assertIn(str(plugin_dir), command)
            self.assertIn("--proxy", command)
            self.assertIn("socks5://127.0.0.1:11080", command)
        finally:
            if output_path.exists():
                output_path.unlink()

    def test_ytdlp_common_options_passes_cookies_file(self):
        options = CLASSIFIER.ytdlp_common_options(cookies_path="config/youtube_cookies.txt")

        self.assertIn("--cookies", options)
        self.assertIn("config/youtube_cookies.txt", options)
        self.assertNotIn("--no-cookies-update", options)

    def test_run_subprocess_returns_timeout_result(self):
        timeout = CLASSIFIER.subprocess.TimeoutExpired(["cmd"], 3)
        with patch.object(CLASSIFIER.subprocess, "run", side_effect=timeout):
            result = CLASSIFIER.run_subprocess(["cmd"], timeout=3)

        self.assertEqual(result.returncode, 124)
        self.assertIn("timed out", result.stderr)

    def test_timing_helpers_are_noops_when_disabled(self):
        start = CLASSIFIER.timing_start(False)

        self.assertIsNone(start)
        self.assertEqual(CLASSIFIER.timing_elapsed(start), 0.0)

    def test_transcribe_post_local_uses_stable_audio_fallback(self):
        temp_dir = SCRIPT_PATH.parents[2] / "tmp" / "video_classification_tests"
        temp_dir.mkdir(parents=True, exist_ok=True)

        class Segment:
            text = "texto transcrito"

        class FakeModel:
            def transcribe(self, audio_path, language, vad_filter):
                self.audio_path = audio_path
                self.language = language
                self.vad_filter = vad_filter
                return [Segment()], {}

        fake_model = FakeModel()
        args = SimpleNamespace(
            transcript_seconds=90,
            audio_workdir=temp_dir,
            yt_dlp_cookies=None,
            yt_dlp_user_agent=None,
            yt_dlp_referer=None,
            yt_dlp_extractor_args=[],
            yt_dlp_plugin_dir=[],
            yt_dlp_proxy="socks5://127.0.0.1:11080",
            whisper_language="pt",
            whisper_model="small",
            whisper_compute_type="int8",
        )

        def stable_download(*call_args):
            call_args[2].write_bytes(b"wav")

        with patch.object(CLASSIFIER, "download_audio_segment", side_effect=RuntimeError("ffmpeg exited with code -11")), patch.object(
            CLASSIFIER,
            "download_audio_segment_stable",
            side_effect=stable_download,
        ) as fallback:
            record = CLASSIFIER.transcribe_post_local(
                {"post_id": "video1", "duration": 300},
                {"ffmpeg_path": "ffmpeg", "model": fake_model},
                args,
            )

        self.assertEqual(record["text"], "texto transcrito")
        self.assertEqual(
            record["metadata"]["source_method"],
            "yt-dlp-source+ffmpeg-segment+faster-whisper-local",
        )
        fallback.assert_called_once()

    def test_transcribe_post_local_uses_temporary_cookie_copy(self):
        temp_dir = SCRIPT_PATH.parents[2] / "tmp" / "video_classification_tests"
        temp_dir.mkdir(parents=True, exist_ok=True)
        source_cookies = temp_dir / f"cookies_{uuid.uuid4().hex}.txt"
        source_cookies.write_text("# Netscape\n.youtube.com\tTRUE\t/\tTRUE\t0\tSID\tabc\n", encoding="utf-8")

        class Segment:
            text = "texto transcrito"

        class FakeModel:
            def transcribe(self, audio_path, language, vad_filter):
                return [Segment()], {}

        args = SimpleNamespace(
            transcript_seconds=90,
            audio_workdir=temp_dir,
            yt_dlp_cookies=source_cookies,
            yt_dlp_user_agent=None,
            yt_dlp_referer=None,
            yt_dlp_extractor_args=[],
            yt_dlp_plugin_dir=[],
            yt_dlp_proxy=None,
            whisper_language="pt",
            whisper_model="small",
            whisper_compute_type="int8",
        )
        seen = {}

        def fake_download(*call_args):
            seen["cookies_path"] = Path(call_args[4])
            call_args[2].write_bytes(b"wav")

        with patch.object(CLASSIFIER, "download_audio_segment", side_effect=fake_download):
            CLASSIFIER.transcribe_post_local(
                {"post_id": "video_cookie", "duration": 300},
                {"ffmpeg_path": "ffmpeg", "model": FakeModel()},
                args,
            )

        self.assertEqual(source_cookies.read_text(encoding="utf-8").splitlines()[0], "# Netscape")
        self.assertNotEqual(seen["cookies_path"], source_cookies)
        self.assertFalse(seen["cookies_path"].exists())

    def test_stable_source_download_prefers_progressive_format(self):
        temp_dir = SCRIPT_PATH.parents[2] / "tmp" / "video_classification_tests"
        temp_dir.mkdir(parents=True, exist_ok=True)
        output_stem = temp_dir / f"source_{uuid.uuid4().hex}"
        output_file = output_stem.with_suffix(".mp4")

        def fake_run(command, timeout):
            output_file.write_bytes(b"mp4")
            return SimpleNamespace(returncode=0, stderr="", stdout="")

        try:
            with patch.object(CLASSIFIER, "run_subprocess", side_effect=fake_run) as run_subprocess:
                source = CLASSIFIER.download_audio_source(
                    "video1",
                    output_stem,
                    proxy="socks5://127.0.0.1:11080",
                )

            command = run_subprocess.call_args[0][0]
            format_index = command.index("-f") + 1
            self.assertTrue(command[format_index].startswith("139/140/18/"))
            self.assertEqual(source, output_file)
        finally:
            if output_file.exists():
                output_file.unlink()

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

        payload = request.call_args_list[0][1]["payload"]
        self.assertEqual(payload["transcript_quality_score"], 0.85)
        self.assertIsNone(payload["input_payload"]["video"]["transcript_90s"])

    def test_vehicle_entity_exact_year_matches_carrosnaweb_catalog(self):
        entity = {
            "entity_order": 1,
            "vehicle_brand_raw": "Caoa Changan",
            "vehicle_model_raw": "Uni-T",
            "vehicle_year": 2026,
            "vehicle_generation": None,
            "evidence_text": "Caoa Changan Uni-T 2026",
            "entity_status": "extracted",
        }
        catalog_row = {
            "catalog_row_id": 123,
            "catalog_model_id": 77,
            "manufacturer_name": "Changan",
            "manufacturer_key": "changan",
            "model_name": "Uni-T",
            "model_key": "uni t",
            "model_year": 2026,
        }

        with patch.object(CLASSIFIER, "request_json", side_effect=[[], [catalog_row]]):
            row = CLASSIFIER.build_vehicle_entity_row(
                "https://example.supabase.co",
                {"apikey": "test"},
                10,
                entity,
            )

        self.assertEqual(row["entity_status"], "matched")
        self.assertEqual(row["catalog_row_id"], 123)
        self.assertEqual(row["catalog_model_id"], 77)
        self.assertEqual(row["catalog_match_level"], "model_year")
        self.assertEqual(row["canonical_manufacturer_name"], "Changan")
        self.assertEqual(row["canonical_model_name"], "Uni-T")
        self.assertEqual(row["canonical_model_year"], 2026)

    def test_vehicle_entity_without_year_matches_model_level(self):
        entity = {
            "entity_order": 1,
            "vehicle_brand_raw": "Renault",
            "vehicle_model_raw": "Kwid",
            "vehicle_year": None,
            "vehicle_generation": None,
            "evidence_text": "Kwid",
            "entity_status": "extracted",
        }
        catalog_rows = [
            {
                "catalog_row_id": 1,
                "catalog_model_id": 10,
                "manufacturer_name": "Renault",
                "manufacturer_key": "renault",
                "model_name": "Kwid",
                "model_key": "kwid",
                "model_year": 2025,
            },
            {
                "catalog_row_id": 2,
                "catalog_model_id": 10,
                "manufacturer_name": "Renault",
                "manufacturer_key": "renault",
                "model_name": "Kwid",
                "model_key": "kwid",
                "model_year": 2024,
            },
        ]

        with patch.object(CLASSIFIER, "request_json", return_value=catalog_rows):
            row = CLASSIFIER.build_vehicle_entity_row(
                "https://example.supabase.co",
                {"apikey": "test"},
                10,
                entity,
            )

        self.assertEqual(row["entity_status"], "matched")
        self.assertIsNone(row["catalog_row_id"])
        self.assertEqual(row["catalog_model_id"], 10)
        self.assertEqual(row["catalog_match_level"], "model")
        self.assertEqual(row["canonical_manufacturer_name"], "Renault")
        self.assertEqual(row["canonical_model_name"], "Kwid")
        self.assertIsNone(row["validation_issue"])

    def test_script_vehicle_match_fills_unique_manufacturer_from_model(self):
        harness = {
            "video": {
                "title": "Quanto custa o motor do Kwid ?",
                "description": None,
                "transcript_90s": None,
            }
        }
        catalog_rows = [
            {
                "catalog_row_id": 1,
                "catalog_model_id": 10,
                "manufacturer_name": "Renault",
                "manufacturer_key": "renault",
                "model_name": "Kwid",
                "model_key": "kwid",
                "model_year": 2025,
            },
            {
                "catalog_row_id": 2,
                "catalog_model_id": 10,
                "manufacturer_name": "Renault",
                "manufacturer_key": "renault",
                "model_name": "Kwid",
                "model_key": "kwid",
                "model_year": 2024,
            },
        ]

        entities = CLASSIFIER.select_script_vehicle_candidates(harness, catalog_rows)

        self.assertEqual(len(entities), 1)
        self.assertIsNone(entities[0]["vehicle_brand_raw"])
        self.assertEqual(entities[0]["vehicle_model_raw"], "Kwid")
        self.assertEqual(entities[0]["resolved_entity_status"], "matched")
        self.assertEqual(entities[0]["canonical_manufacturer_name"], "Renault")
        self.assertEqual(entities[0]["catalog_model_id"], 10)
        self.assertIsNone(entities[0]["catalog_row_id"])
        self.assertEqual(entities[0]["catalog_match_level"], "model")

    def test_script_vehicle_match_rejects_common_words_without_manufacturer(self):
        harness = {
            "video": {
                "title": "Bora para o canal, link na descricao e carro 100% eletrico",
                "description": "Tipo SKD e CKD aparecem como contexto industrial.",
                "transcript_90s": "O carro chega a 99 km por hora e nao chega a 100 por hora.",
            }
        }
        catalog_rows = [
            {
                "catalog_row_id": 1,
                "catalog_model_id": 10,
                "manufacturer_name": "Audi",
                "manufacturer_key": "audi",
                "model_name": "100",
                "model_key": "100",
                "model_year": 1995,
            },
            {
                "catalog_row_id": 2,
                "catalog_model_id": 20,
                "manufacturer_name": "Volkswagen",
                "manufacturer_key": "volkswagen",
                "model_name": "Bora",
                "model_key": "bora",
                "model_year": 2010,
            },
            {
                "catalog_row_id": 3,
                "catalog_model_id": 30,
                "manufacturer_name": "Fiat",
                "manufacturer_key": "fiat",
                "model_name": "Tipo",
                "model_key": "tipo",
                "model_year": 1994,
            },
            {
                "catalog_row_id": 4,
                "catalog_model_id": 40,
                "manufacturer_name": "Rely",
                "manufacturer_key": "rely",
                "model_name": "Link",
                "model_key": "link",
                "model_year": 2014,
            },
        ]

        entities = CLASSIFIER.select_script_vehicle_candidates(harness, catalog_rows)

        self.assertEqual(entities, [])

    def test_script_vehicle_match_accepts_common_model_with_nearby_manufacturer(self):
        harness = {
            "video": {
                "title": "Review do Fiat Tipo usado",
                "description": "Comparativo com Volkswagen Bora em mercado de usados.",
                "transcript_90s": "O Audi 100 aparece como referencia historica.",
            }
        }
        catalog_rows = [
            {
                "catalog_row_id": 1,
                "catalog_model_id": 10,
                "manufacturer_name": "Audi",
                "manufacturer_key": "audi",
                "model_name": "100",
                "model_key": "100",
                "model_year": 1995,
            },
            {
                "catalog_row_id": 2,
                "catalog_model_id": 20,
                "manufacturer_name": "Volkswagen",
                "manufacturer_key": "volkswagen",
                "model_name": "Bora",
                "model_key": "bora",
                "model_year": 2010,
            },
            {
                "catalog_row_id": 3,
                "catalog_model_id": 30,
                "manufacturer_name": "Fiat",
                "manufacturer_key": "fiat",
                "model_name": "Tipo",
                "model_key": "tipo",
                "model_year": 1994,
            },
        ]

        entities = CLASSIFIER.select_script_vehicle_candidates(harness, catalog_rows)
        models = {entity["vehicle_model_raw"] for entity in entities}

        self.assertEqual(models, {"100", "Bora", "Tipo"})
        self.assertTrue(all(entity["resolved_entity_status"] == "matched" for entity in entities))

    def test_default_skill_documents_topic_path_priority(self):
        skill = CLASSIFIER.DEFAULT_SKILL

        self.assertIn("topic_path representa a proposta principal", skill)
        self.assertIn("powertrain so e topic_path principal", skill)

    def test_repair_topic_path_code_fixes_single_obvious_typo(self):
        topic_codes = {
            "mercado_produto__lancamentos",
            "mercado_produto__mercado_eletrificados",
        }

        repaired = CLASSIFIER.repair_topic_path_code(
            "mercado_procuto__lancamentos",
            topic_codes,
        )

        self.assertEqual(repaired, "mercado_produto__lancamentos")

    def test_normalize_vehicle_entities_resequences_invalid_orders(self):
        result = {
            "vehicle_entities": [
                {
                    "entity_order": 0,
                    "vehicle_brand_raw": "Changan",
                    "vehicle_model_raw": "Uni-T",
                    "vehicle_year": 2026,
                    "vehicle_generation": None,
                },
                {
                    "entity_order": -1,
                    "vehicle_brand_raw": "BYD",
                    "vehicle_model_raw": "Dolphin",
                    "vehicle_year": None,
                    "vehicle_generation": None,
                },
            ]
        }

        CLASSIFIER.normalize_vehicle_entities_for_validation(result)

        self.assertEqual([entity["entity_order"] for entity in result["vehicle_entities"]], [1, 2])

    def test_normalize_score_scales_repairs_percent_values(self):
        result = {
            "classification_result": {"confidence_score": "92"},
            "transcript_quality": {"quality_score": 85},
        }

        CLASSIFIER.normalize_score_scales_for_validation(result)

        self.assertEqual(result["classification_result"]["confidence_score"], 0.92)
        self.assertEqual(result["transcript_quality"]["quality_score"], 0.85)

    def test_normalize_score_scales_keeps_null_quality_score(self):
        result = {
            "classification_result": {"confidence_score": 0.72},
            "transcript_quality": {"quality_score": None},
        }

        CLASSIFIER.normalize_score_scales_for_validation(result)

        self.assertEqual(result["classification_result"]["confidence_score"], 0.72)
        self.assertIsNone(result["transcript_quality"]["quality_score"])


if __name__ == "__main__":
    unittest.main()
