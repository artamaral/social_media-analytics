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

    def test_transcribe_post_local_uses_stable_audio_first(self):
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

        with patch.object(
            CLASSIFIER,
            "download_audio_segment_stable",
            side_effect=stable_download,
        ) as stable, patch.object(CLASSIFIER, "download_audio_segment") as direct:
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
        stable.assert_called_once()
        direct.assert_not_called()

    def test_transcribe_post_local_uses_direct_recovery_after_stable_failure(self):
        temp_dir = SCRIPT_PATH.parents[2] / "tmp" / "video_classification_tests"
        temp_dir.mkdir(parents=True, exist_ok=True)

        class Segment:
            text = "texto transcrito"

        class FakeModel:
            def transcribe(self, audio_path, language, vad_filter):
                return [Segment()], {}

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

        def direct_download(*call_args):
            call_args[2].write_bytes(b"wav")

        with patch.object(
            CLASSIFIER,
            "download_audio_segment_stable",
            side_effect=RuntimeError("bot block"),
        ) as stable, patch.object(
            CLASSIFIER,
            "download_audio_segment",
            side_effect=direct_download,
        ) as direct:
            record = CLASSIFIER.transcribe_post_local(
                {"post_id": "video1", "duration": 300},
                {"ffmpeg_path": "ffmpeg", "model": FakeModel()},
                args,
            )

        self.assertEqual(record["text"], "texto transcrito")
        self.assertEqual(record["metadata"]["source_method"], "yt-dlp+faster-whisper-local")
        stable.assert_called_once()
        direct.assert_called_once()

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

        with patch.object(CLASSIFIER, "download_audio_segment_stable", side_effect=fake_download):
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

    def test_promote_specific_topic_path_from_primary_context(self):
        result = {
            "classification_result": {
                "topic_path": "manutencao_reparo",
            },
            "technical_contexts": [
                {
                    "topic_path": "manutencao_reparo__reparo_corretivo__troca_motor",
                    "context_role": "primary",
                },
                {
                    "topic_path": "diagnostico__falha_motor",
                    "context_role": "secondary",
                },
            ],
        }

        CLASSIFIER.promote_specific_topic_path_from_contexts(result)

        self.assertEqual(
            result["classification_result"]["topic_path"],
            "manutencao_reparo__reparo_corretivo__troca_motor",
        )

    def test_promote_specific_topic_path_does_not_cross_domain(self):
        result = {
            "classification_result": {
                "topic_path": "review_teste__review_veiculo",
            },
            "technical_contexts": [
                {
                    "topic_path": "powertrain__ice",
                    "context_role": "primary",
                },
            ],
        }

        CLASSIFIER.promote_specific_topic_path_from_contexts(result)

        self.assertEqual(
            result["classification_result"]["topic_path"],
            "review_teste__review_veiculo",
        )

    def test_promote_sem_match_autonomy_to_existing_review_topic(self):
        result = {
            "classification_result": {
                "topic_path": "sem_match_taxonomico",
                "confidence_score": 0.42,
                "needs_human_review": True,
                "validation_issues": "sem_match_taxonomico utilizado",
            },
            "technical_contexts": [],
        }
        harness = {
            "video": {
                "title": "Testei a autonomia do Byd Dolphin Mini Gs no extremo",
                "description": None,
                "transcript_90s": "Teste de autonomia do carro eletrico ate o limite.",
            }
        }
        topic_codes = {
            "sem_match_taxonomico",
            "review_teste__teste_autonomia",
            "powertrain__eletrificados",
        }

        CLASSIFIER.promote_topic_path_from_evidence(result, harness, topic_codes)

        classification = result["classification_result"]
        self.assertEqual(classification["topic_path"], "review_teste__teste_autonomia")
        self.assertGreaterEqual(classification["confidence_score"], 0.70)
        self.assertFalse(classification["needs_human_review"])
        self.assertIsNone(classification["validation_issues"])

    def test_promote_generic_maintenance_engine_repair_topic(self):
        result = {
            "classification_result": {
                "topic_path": "manutencao_reparo",
                "confidence_score": 0.78,
                "needs_human_review": False,
                "validation_issues": None,
            },
            "technical_contexts": [],
        }
        harness = {
            "video": {
                "title": "Quanto custa o motor do Kwid ?",
                "description": None,
                "transcript_90s": "O motor foi desmontado para avaliar falha, custo e reparo.",
            }
        }
        topic_codes = {
            "manutencao_reparo",
            "manutencao_reparo__reparo_corretivo__reparo_motor",
        }

        CLASSIFIER.promote_topic_path_from_evidence(result, harness, topic_codes)

        self.assertEqual(
            result["classification_result"]["topic_path"],
            "manutencao_reparo__reparo_corretivo__reparo_motor",
        )

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

    def test_vehicle_entity_trim_suffix_is_not_canonical_dimension(self):
        entity = {
            "entity_order": 1,
            "vehicle_brand_raw": "BYD",
            "vehicle_model_raw": "Dolphin SE",
            "vehicle_year": None,
            "vehicle_generation": "SE",
            "evidence_text": "NOVO BYD Dolphin SE",
            "entity_status": "extracted",
        }
        catalog_rows = [
            {
                "catalog_row_id": 1,
                "catalog_model_id": 20,
                "manufacturer_name": "BYD",
                "manufacturer_key": "byd",
                "model_name": "Dolphin",
                "model_key": "dolphin",
                "model_year": 2025,
            }
        ]

        with patch.object(CLASSIFIER, "request_json", return_value=catalog_rows):
            row = CLASSIFIER.build_vehicle_entity_row(
                "https://example.supabase.co",
                {"apikey": "test"},
                10,
                entity,
            )

        self.assertEqual(row["vehicle_model_raw"], "Dolphin")
        self.assertIsNone(row["vehicle_generation"])
        self.assertEqual(row["canonical_model_name"], "Dolphin")
        self.assertEqual(row["catalog_match_level"], "model")

    def test_vehicle_entity_yaris_cross_xr_drops_trim_suffix(self):
        entity = {
            "entity_order": 1,
            "vehicle_brand_raw": "Toyota",
            "vehicle_model_raw": "Yaris Cross XR",
            "vehicle_year": 2026,
            "vehicle_generation": "XR",
            "evidence_text": "Toyota Yaris Cross XR 2026",
            "entity_status": "extracted",
        }
        catalog_row = {
            "catalog_row_id": 1,
            "catalog_model_id": 30,
            "manufacturer_name": "Toyota",
            "manufacturer_key": "toyota",
            "model_name": "Yaris Cross",
            "model_key": "yaris cross",
            "model_year": 2026,
        }

        with patch.object(CLASSIFIER, "request_json", return_value=[catalog_row]):
            row = CLASSIFIER.build_vehicle_entity_row(
                "https://example.supabase.co",
                {"apikey": "test"},
                10,
                entity,
            )

        self.assertEqual(row["vehicle_model_raw"], "Yaris Cross")
        self.assertIsNone(row["vehicle_generation"])
        self.assertEqual(row["canonical_model_name"], "Yaris Cross")
        self.assertEqual(row["catalog_match_level"], "model_year")

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
        self.assertEqual(entities[0]["canonical_model_name"], "Kwid")
        self.assertIsNone(entities[0]["canonical_model_year"])
        self.assertEqual(entities[0]["catalog_model_id"], 10)
        self.assertIsNone(entities[0]["catalog_row_id"])
        self.assertEqual(entities[0]["catalog_match_level"], "model")

    def test_script_vehicle_match_rejects_common_words_without_manufacturer(self):
        harness = {
            "video": {
                "title": "Bora para o canal, amigo, picape, link na descricao e carro 100% eletrico",
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
            {
                "catalog_row_id": 5,
                "catalog_model_id": 50,
                "manufacturer_name": "Isuzu",
                "manufacturer_key": "isuzu",
                "model_name": "Amigo",
                "model_key": "amigo",
                "model_year": 1998,
            },
            {
                "catalog_row_id": 6,
                "catalog_model_id": 60,
                "manufacturer_name": "Shineray",
                "manufacturer_key": "shineray",
                "model_name": "Picape",
                "model_key": "picape",
                "model_year": 2024,
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

    def test_script_vehicle_match_rejects_model_when_term_is_known_brand(self):
        harness = {
            "video": {
                "title": "Jeep Commander hibrido chega ao mercado",
                "description": None,
                "transcript_90s": None,
            }
        }
        catalog_rows = [
            {
                "catalog_row_id": 1,
                "catalog_model_id": 10,
                "manufacturer_name": "Ford",
                "manufacturer_key": "ford",
                "model_name": "Jeep",
                "model_key": "jeep",
                "model_year": 1967,
            },
            {
                "catalog_row_id": 2,
                "catalog_model_id": 20,
                "manufacturer_name": "Jeep",
                "manufacturer_key": "jeep",
                "model_name": "Commander",
                "model_key": "commander",
                "model_year": 2027,
            },
        ]

        entities = CLASSIFIER.select_script_vehicle_candidates(harness, catalog_rows)

        models = {entity["vehicle_model_raw"] for entity in entities}
        self.assertEqual(models, {"Commander"})
        self.assertEqual(entities[0]["canonical_manufacturer_name"], "Jeep")

    def test_script_vehicle_match_rejects_picape_without_matching_manufacturer(self):
        harness = {
            "video": {
                "title": "Uma picape nova da Volkswagen aparece em testes",
                "description": None,
                "transcript_90s": None,
            }
        }
        catalog_rows = [
            {
                "catalog_row_id": 1,
                "catalog_model_id": 10,
                "manufacturer_name": "Shineray",
                "manufacturer_key": "shineray",
                "model_name": "Picape",
                "model_key": "picape",
                "model_year": 2025,
            }
        ]

        entities = CLASSIFIER.select_script_vehicle_candidates(harness, catalog_rows)

        self.assertEqual(entities, [])

    def test_script_vehicle_match_gr_yaris_does_not_create_gr_ares(self):
        harness = {
            "video": {
                "title": "Avaliação GR Yaris manual",
                "description": None,
                "transcript_90s": "Toyota GR Yaris com cambio manual.",
            }
        }
        catalog_rows = [
            {
                "catalog_row_id": 1,
                "catalog_model_id": 10,
                "manufacturer_name": "Toyota",
                "manufacturer_key": "toyota",
                "model_name": "Yaris",
                "model_key": "yaris",
                "model_year": 2025,
            },
            {
                "catalog_row_id": 2,
                "catalog_model_id": 20,
                "manufacturer_name": "Ficticia",
                "manufacturer_key": "ficticia",
                "model_name": "GR-Ares",
                "model_key": "gr ares",
                "model_year": 2025,
            },
        ]

        entities = CLASSIFIER.select_script_vehicle_candidates(harness, catalog_rows)
        models = {entity["canonical_model_name"] for entity in entities}

        self.assertEqual(models, {"Yaris"})

    def test_filter_weak_vehicle_entities_drops_transcript_trim_noise(self):
        result = {
            "vehicle_entities": [
                {
                    "entity_order": 1,
                    "vehicle_brand_raw": None,
                    "vehicle_model_raw": "GR-Ares",
                    "vehicle_year": None,
                    "vehicle_generation": None,
                    "evidence_text": "transcript menciona GR-Ares",
                    "entity_status": "not_found",
                    "resolved_entity_status": "not_found",
                    "catalog_match_level": "not_found",
                }
            ]
        }
        harness = {
            "video": {
                "title": "Avaliacao GR Yaris manual",
                "description": None,
                "transcript_90s": "O narrador fala algo parecido com GR-Ares uma vez.",
            }
        }
        script_entities = [
            {
                "entity_order": 1,
                "vehicle_brand_raw": None,
                "vehicle_model_raw": "Yaris",
                "entity_status": "matched",
                "resolved_entity_status": "matched",
                "catalog_model_id": 1361,
                "catalog_match_level": "model",
                "canonical_manufacturer_name": "Toyota",
                "canonical_model_name": "Yaris",
            }
        ]

        CLASSIFIER.filter_weak_vehicle_entities(result, harness, script_entities)

        self.assertEqual(result["vehicle_entities"], [])

    def test_filter_weak_vehicle_entities_keeps_explicit_brand_not_found(self):
        result = {
            "vehicle_entities": [
                {
                    "entity_order": 1,
                    "vehicle_brand_raw": "Lotus",
                    "vehicle_model_raw": "Evija",
                    "vehicle_year": None,
                    "vehicle_generation": None,
                    "evidence_text": "Lotus Evija aparece no titulo",
                    "entity_status": "not_found",
                    "resolved_entity_status": "not_found",
                    "catalog_match_level": "not_found",
                }
            ]
        }
        harness = {
            "video": {
                "title": "Review Lotus Evija no Brasil",
                "description": None,
                "transcript_90s": None,
            }
        }

        CLASSIFIER.filter_weak_vehicle_entities(result, harness, [])

        self.assertEqual(len(result["vehicle_entities"]), 1)

    def test_merge_vehicle_entities_keeps_more_specific_model_year(self):
        model_entity = {
            "entity_order": 1,
            "vehicle_brand_raw": "Jeep",
            "vehicle_model_raw": "Commander",
            "vehicle_year": None,
            "catalog_model_id": 20,
            "catalog_row_id": None,
            "catalog_match_level": "model",
            "canonical_manufacturer_name": "Jeep",
            "canonical_model_name": "Commander",
            "canonical_model_year": None,
        }
        model_year_entity = {
            "entity_order": 2,
            "vehicle_brand_raw": "Jeep",
            "vehicle_model_raw": "Commander",
            "vehicle_year": 2027,
            "catalog_model_id": 20,
            "catalog_row_id": 99,
            "catalog_match_level": "model_year",
            "canonical_manufacturer_name": "Jeep",
            "canonical_model_name": "Commander",
            "canonical_model_year": 2027,
        }

        merged = CLASSIFIER.merge_vehicle_entities([model_entity, model_year_entity], [])

        self.assertEqual(len(merged), 1)
        self.assertEqual(merged[0]["catalog_match_level"], "model_year")
        self.assertEqual(merged[0]["canonical_model_year"], 2027)
        self.assertEqual(merged[0]["entity_order"], 1)

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

    def test_repair_topic_path_code_fixes_orcamento_alias(self):
        topic_codes = {
            "manutencao_reparo__custo_reparo__orcamento_manutencao",
        }

        repaired = CLASSIFIER.repair_topic_path_code(
            "manutencao_reparo__custo_reparo__orcamento",
            topic_codes,
        )

        self.assertEqual(
            repaired,
            "manutencao_reparo__custo_reparo__orcamento_manutencao",
        )

    def test_repair_topic_path_code_fixes_market_analysis_alias(self):
        topic_codes = {"mercado_produto__analise_mercado"}

        repaired = CLASSIFIER.repair_topic_path_code(
            "mercado_produto__analise mercado",
            topic_codes,
        )

        self.assertEqual(repaired, "mercado_produto__analise_mercado")

    def test_repair_topic_path_code_demotes_traction_attribute_to_review_context(self):
        topic_codes = {"review_teste__review_veiculo", "powertrain__transmissao"}

        repaired = CLASSIFIER.repair_topic_path_code(
            "powertrain__transmissao__tracao_integral",
            topic_codes,
        )

        self.assertEqual(repaired, "review_teste__review_veiculo")

    def test_normalize_unit_score_accepts_percent_string(self):
        self.assertEqual(CLASSIFIER.normalize_unit_score("85%"), 0.85)

    def test_normalize_unit_score_caps_invalid_high_value(self):
        self.assertEqual(CLASSIFIER.normalize_unit_score(850), 1.0)

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

    def test_normalize_result_collections_drops_null_items(self):
        result = {
            "technical_contexts": [None, {"context_order": 1}],
            "vehicle_entities": None,
        }

        CLASSIFIER.normalize_result_collections(result)

        self.assertEqual(result["technical_contexts"], [{"context_order": 1}])
        self.assertEqual(result["vehicle_entities"], [])

    def test_normalize_result_collections_rejects_non_list(self):
        result = {
            "technical_contexts": {},
            "vehicle_entities": [],
        }

        with self.assertRaisesRegex(ValueError, "technical_contexts deve ser lista"):
            CLASSIFIER.normalize_result_collections(result)

    def test_normalize_required_result_blocks_rejects_null_classification(self):
        result = {
            "classification_result": None,
            "transcript_quality": {"issues": []},
        }

        with self.assertRaisesRegex(ValueError, "classification_result veio null"):
            CLASSIFIER.normalize_required_result_blocks(result)

    def test_normalize_required_result_blocks_defaults_null_issues(self):
        result = {
            "classification_result": {},
            "transcript_quality": {"issues": None},
        }

        CLASSIFIER.normalize_required_result_blocks(result)

        self.assertEqual(result["transcript_quality"]["issues"], [])

    def test_validate_json_schema_shape_ignores_null_schema_branch(self):
        CLASSIFIER.validate_json_schema_shape("qualquer", None)

    def test_validation_step_wraps_attribute_error(self):
        with self.assertRaisesRegex(ValueError, "validacao:teste: erro interno"):
            CLASSIFIER.validation_step("teste", lambda: None.get("x"))

    def test_validate_taxonomy_rows_rejects_null_row(self):
        with self.assertRaisesRegex(ValueError, "compatibility\\[1\\] deve ser objeto"):
            CLASSIFIER.validate_taxonomy_rows([None], "compatibility")

    def test_normalize_technical_contexts_marks_missing_compatibility_issue(self):
        result = {
            "technical_contexts": [
                {
                    "topic_path": "diagnostico__falha_motor",
                    "automotive_system": "motor",
                    "component": "cilindro",
                    "problem": "falha_de_motor",
                    "compatibility_status": "allowed",
                    "needs_human_review": False,
                    "validation_issue": None,
                }
            ]
        }

        CLASSIFIER.normalize_technical_contexts_for_validation(result, set())

        context = result["technical_contexts"][0]
        self.assertEqual(context["compatibility_status"], "needs_review")
        self.assertTrue(context["needs_human_review"])
        self.assertIn("technical_context sem combinacao compativel", context["validation_issue"])

    def test_normalize_technical_contexts_repairs_motor_action_problem_alias(self):
        result = {
            "technical_contexts": [
                {
                    "topic_path": "manutencao_reparo__reparo_corretivo__troca_motor",
                    "automotive_system": "motor",
                    "component": "motor_conjunto",
                    "problem": "troca_motor",
                    "compatibility_status": "allowed",
                    "needs_human_review": False,
                    "validation_issue": None,
                }
            ]
        }
        compatibility_keys = {
            (
                "manutencao_reparo__reparo_corretivo__troca_motor",
                "motor",
                "motor_conjunto",
                "falha_de_motor",
            )
        }

        CLASSIFIER.normalize_technical_contexts_for_validation(result, compatibility_keys)

        context = result["technical_contexts"][0]
        self.assertEqual(context["problem"], "falha_de_motor")
        self.assertEqual(context["compatibility_status"], "allowed")
        self.assertFalse(context["needs_human_review"])

    def test_normalize_technical_contexts_drops_nontechnical_budget_problem(self):
        result = {
            "technical_contexts": [
                {
                    "topic_path": "manutencao_reparo__custo_reparo__orcamento_manutencao",
                    "automotive_system": None,
                    "component": None,
                    "problem": "orcamento",
                    "compatibility_status": "needs_review",
                    "needs_human_review": True,
                    "validation_issue": "orcamento usado como problema",
                }
            ]
        }

        CLASSIFIER.normalize_technical_contexts_for_validation(result, set())

        self.assertEqual(result["technical_contexts"], [])

    def test_normalize_technical_contexts_keeps_sensor_and_drops_cleaning_problem(self):
        result = {
            "technical_contexts": [
                {
                    "topic_path": "manutencao_reparo__manutencao_preventiva__limpeza_componentes",
                    "automotive_system": "eletrica_eletronica",
                    "component": "sensor_maf",
                    "problem": "limpeza",
                    "compatibility_status": "allowed",
                    "needs_human_review": False,
                    "validation_issue": None,
                }
            ]
        }
        compatibility_keys = {
            (
                "manutencao_reparo__manutencao_preventiva__limpeza_componentes",
                "eletrica_eletronica",
                "sensor_maf",
                None,
            )
        }

        CLASSIFIER.normalize_technical_contexts_for_validation(result, compatibility_keys)

        context = result["technical_contexts"][0]
        self.assertEqual(context["component"], "sensor_maf")
        self.assertIsNone(context["problem"])
        self.assertFalse(context["needs_human_review"])

    def test_normalize_technical_contexts_turns_battery_autonomy_into_attribute(self):
        result = {
            "technical_contexts": [
                {
                    "topic_path": "review_teste__teste_autonomia",
                    "automotive_system": "powertrain",
                    "component": "bateria_tracao",
                    "problem": "autonomia",
                    "compatibility_status": "allowed",
                    "needs_human_review": False,
                    "validation_issue": None,
                }
            ]
        }
        compatibility_keys = {
            (
                "review_teste__teste_autonomia",
                "powertrain",
                "autonomia",
                None,
            )
        }

        CLASSIFIER.normalize_technical_contexts_for_validation(result, compatibility_keys)

        context = result["technical_contexts"][0]
        self.assertEqual(context["component"], "autonomia")
        self.assertIsNone(context["problem"])
        self.assertFalse(context["needs_human_review"])

    def test_normalize_technical_contexts_drops_pleonastic_hybrid_context(self):
        result = {
            "technical_contexts": [
                {
                    "topic_path": "powertrain__eletrificados",
                    "automotive_system": "powertrain",
                    "component": "sistema_hibrido",
                    "problem": None,
                    "compatibility_status": "needs_review",
                    "needs_human_review": True,
                    "validation_issue": "pleonasmo",
                }
            ]
        }

        CLASSIFIER.normalize_technical_contexts_for_validation(result, set())

        self.assertEqual(result["technical_contexts"], [])

    def test_normalize_technical_contexts_drops_manual_transmission_problem(self):
        result = {
            "technical_contexts": [
                {
                    "topic_path": "review_teste__review_veiculo",
                    "automotive_system": "transmissao",
                    "component": "cambio_manual",
                    "problem": "manual_cambio",
                    "compatibility_status": "allowed",
                    "needs_human_review": False,
                    "validation_issue": None,
                }
            ]
        }
        compatibility_keys = {
            (
                "review_teste__review_veiculo",
                "transmissao",
                "cambio_manual",
                None,
            )
        }

        CLASSIFIER.normalize_technical_contexts_for_validation(result, compatibility_keys)

        context = result["technical_contexts"][0]
        self.assertEqual(context["component"], "cambio_manual")
        self.assertIsNone(context["problem"])

    def test_normalize_technical_contexts_turns_turbo_problem_into_component(self):
        result = {
            "technical_contexts": [
                {
                    "topic_path": "powertrain__ice",
                    "automotive_system": "motor",
                    "component": "motor",
                    "problem": "turbo",
                    "compatibility_status": "allowed",
                    "needs_human_review": False,
                    "validation_issue": None,
                }
            ]
        }
        compatibility_keys = {
            (
                "powertrain__ice",
                "motor",
                "turbo",
                None,
            )
        }

        CLASSIFIER.normalize_technical_contexts_for_validation(result, compatibility_keys)

        context = result["technical_contexts"][0]
        self.assertEqual(context["component"], "turbo")
        self.assertIsNone(context["problem"])
        self.assertFalse(context["needs_human_review"])

    def test_repair_topic_path_code_maps_historical_powertrain_to_operational_bucket(self):
        topic_codes = {"powertrain__eletrificados", "powertrain__ice"}

        self.assertEqual(
            CLASSIFIER.repair_topic_path_code(
                "powertrain__hibrido__sistema_hibrido",
                topic_codes,
            ),
            "powertrain__eletrificados",
        )
        self.assertEqual(
            CLASSIFIER.repair_topic_path_code(
                "powertrain__combustao__turbo",
                topic_codes,
            ),
            "powertrain__ice",
        )

    def test_normalize_technical_contexts_simplifies_internal_engine_component(self):
        result = {
            "technical_contexts": [
                {
                    "topic_path": "manutencao_reparo__reparo_corretivo__retifica_motor",
                    "automotive_system": "motor",
                    "component": "cilindro_bloco",
                    "problem": "retifica_motor",
                    "compatibility_status": "allowed",
                    "needs_human_review": False,
                    "validation_issue": None,
                }
            ]
        }
        compatibility_keys = {
            (
                "manutencao_reparo__reparo_corretivo__retifica_motor",
                "motor",
                "motor_conjunto",
                "falha_de_motor",
            )
        }

        CLASSIFIER.normalize_technical_contexts_for_validation(result, compatibility_keys)

        context = result["technical_contexts"][0]
        self.assertEqual(context["component"], "motor_conjunto")
        self.assertEqual(context["problem"], "falha_de_motor")
        self.assertFalse(context["needs_human_review"])

    def test_normalize_technical_contexts_drops_generic_market_context(self):
        result = {
            "technical_contexts": [
                {
                    "topic_path": "mercado_produto__analise_mercado",
                    "automotive_system": "market",
                    "component": None,
                    "problem": None,
                    "compatibility_status": "needs_review",
                    "needs_human_review": True,
                    "validation_issue": "generico",
                }
            ]
        }

        CLASSIFIER.normalize_technical_contexts_for_validation(result, set())

        self.assertEqual(result["technical_contexts"], [])

    def test_normalize_technical_contexts_drops_generic_motor_context(self):
        result = {
            "technical_contexts": [
                {
                    "topic_path": "review_teste__review_veiculo",
                    "automotive_system": "motor",
                    "component": "motor",
                    "problem": None,
                    "compatibility_status": "needs_review",
                    "needs_human_review": True,
                    "validation_issue": "generico",
                }
            ]
        }

        CLASSIFIER.normalize_technical_contexts_for_validation(result, set())

        self.assertEqual(result["technical_contexts"], [])

    def test_normalize_technical_contexts_drops_hybrid_light_as_problem_only(self):
        result = {
            "technical_contexts": [
                {
                    "topic_path": "mercado_produto__lancamentos",
                    "automotive_system": None,
                    "component": None,
                    "problem": "hibrido_leve",
                    "compatibility_status": "needs_review",
                    "needs_human_review": True,
                    "validation_issue": "atributo",
                }
            ]
        }

        CLASSIFIER.normalize_technical_contexts_for_validation(result, set())

        self.assertEqual(result["technical_contexts"], [])

    def test_append_issue_text_handles_null_current(self):
        self.assertEqual(CLASSIFIER.append_issue_text(None, "novo"), "novo")
        self.assertEqual(CLASSIFIER.append_issue_text("antigo", "novo"), "antigo; novo")
        self.assertEqual(CLASSIFIER.append_issue_text("antigo", "antigo"), "antigo")

    def test_propagate_child_review_flags_marks_parent_review(self):
        result = {
            "classification_result": {
                "needs_human_review": False,
                "validation_issues": None,
            },
            "technical_contexts": [
                {
                    "needs_human_review": True,
                    "compatibility_status": "needs_review",
                }
            ],
            "vehicle_entities": [],
        }

        CLASSIFIER.propagate_child_review_flags(result)

        classification = result["classification_result"]
        self.assertTrue(classification["needs_human_review"])
        self.assertIn("technical_context_needs_review", classification["validation_issues"])

    def test_propagate_child_review_flags_keeps_clean_parent(self):
        result = {
            "classification_result": {
                "needs_human_review": False,
                "validation_issues": None,
            },
            "technical_contexts": [
                {
                    "needs_human_review": False,
                    "compatibility_status": "allowed",
                }
            ],
            "vehicle_entities": [
                {
                    "resolved_entity_status": "matched",
                    "validation_issue": None,
                }
            ],
        }

        CLASSIFIER.propagate_child_review_flags(result)

        self.assertFalse(result["classification_result"]["needs_human_review"])
        self.assertIsNone(result["classification_result"]["validation_issues"])

    def test_normalize_score_scales_repairs_percent_values(self):
        result = {
            "classification_result": {"confidence_score": "92"},
            "transcript_quality": {"quality_score": 85},
        }

        CLASSIFIER.normalize_score_scales_for_validation(result)

        self.assertEqual(result["classification_result"]["confidence_score"], 0.92)
        self.assertEqual(result["transcript_quality"]["quality_score"], 0.85)

    def test_normalize_score_scales_repairs_fraction_strings(self):
        result = {
            "classification_result": {"confidence_score": "92/100"},
            "transcript_quality": {"quality_score": "85/100"},
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

    def test_normalize_vehicle_entities_drops_empty_entity(self):
        result = {
            "vehicle_entities": [
                {
                    "entity_order": 1,
                    "vehicle_brand_raw": None,
                    "vehicle_model_raw": None,
                    "vehicle_year": None,
                    "vehicle_generation": None,
                    "evidence_text": None,
                    "entity_status": "extracted",
                },
                {
                    "entity_order": 2,
                    "vehicle_brand_raw": "Toyota",
                    "vehicle_model_raw": "Yaris Cross XR",
                    "vehicle_year": 2026,
                    "vehicle_generation": None,
                    "evidence_text": "Toyota Yaris Cross XR 2026",
                    "entity_status": "extracted",
                },
            ]
        }

        CLASSIFIER.normalize_vehicle_entities_for_validation(result)

        self.assertEqual(len(result["vehicle_entities"]), 1)
        self.assertEqual(result["vehicle_entities"][0]["entity_order"], 1)
        self.assertEqual(result["vehicle_entities"][0]["vehicle_model_raw"], "Yaris Cross")

    def test_promote_generic_review_from_evidence(self):
        result = {
            "classification_result": {
                "topic_path": "review_teste",
                "confidence_score": 0.78,
                "needs_human_review": False,
                "validation_issues": None,
            },
            "technical_contexts": [],
        }
        harness = {
            "video": {
                "title": "Avaliacao GM Cruze Hatch Turbo",
                "description": None,
                "transcript_90s": "Review do carro com pontos positivos e negativos.",
            }
        }
        topic_codes = {"review_teste", "review_teste__review_veiculo"}

        CLASSIFIER.promote_topic_path_from_evidence(result, harness, topic_codes)

        self.assertEqual(
            result["classification_result"]["topic_path"],
            "review_teste__review_veiculo",
        )

    def test_promote_generic_out_of_scope_from_evidence(self):
        result = {
            "classification_result": {
                "topic_path": "fora_escopo",
                "confidence_score": 0.82,
                "needs_human_review": False,
                "validation_issues": None,
            },
            "technical_contexts": [],
        }
        harness = {
            "video": {
                "title": "MOTOS CLASSICAS EM SOCORRO",
                "description": None,
                "transcript_90s": "Centro Cultural Movimento e garagem moto.",
            }
        }
        topic_codes = {"fora_escopo", "fora_escopo__nao_automotivo"}

        CLASSIFIER.promote_topic_path_from_evidence(result, harness, topic_codes)

        self.assertEqual(
            result["classification_result"]["topic_path"],
            "fora_escopo__nao_automotivo",
        )

    def test_promote_generic_off_road_from_evidence(self):
        result = {
            "classification_result": {
                "topic_path": "off_road",
                "confidence_score": 0.80,
                "needs_human_review": False,
                "validation_issues": None,
            },
            "technical_contexts": [],
        }
        harness = {
            "video": {
                "title": "Melhores projetos de caminhonete",
                "description": None,
                "transcript_90s": "Preparacao off road com suspensao e trilha.",
            }
        }
        topic_codes = {"off_road", "off_road__preparacao_off_road"}

        CLASSIFIER.promote_topic_path_from_evidence(result, harness, topic_codes)

        self.assertEqual(
            result["classification_result"]["topic_path"],
            "off_road__preparacao_off_road",
        )

    def test_normalize_transcript_quality_status_uses_score_as_source(self):
        result = {
            "classification_result": {
                "needs_human_review": False,
                "validation_issues": None,
            },
            "transcript_quality": {
                "quality_score": 0.85,
                "quality_status": "partially_usable",
                "impact_on_classification": "low",
                "needs_retranscription": False,
            },
        }

        CLASSIFIER.normalize_transcript_quality_status(result)

        self.assertEqual(result["transcript_quality"]["quality_status"], "usable")
        self.assertFalse(result["classification_result"]["needs_human_review"])

    def test_normalize_transcript_quality_status_marks_poor_for_low_score(self):
        result = {
            "classification_result": {
                "needs_human_review": False,
                "validation_issues": None,
            },
            "transcript_quality": {
                "quality_score": 0.42,
                "quality_status": "usable",
                "impact_on_classification": "high",
                "needs_retranscription": False,
            },
        }

        CLASSIFIER.normalize_transcript_quality_status(result)

        self.assertEqual(result["transcript_quality"]["quality_status"], "poor")
        self.assertTrue(result["transcript_quality"]["needs_retranscription"])
        self.assertTrue(result["classification_result"]["needs_human_review"])
        self.assertIn("transcript_quality abaixo", result["classification_result"]["validation_issues"])

    def test_parse_args_defaults_to_sixty_second_sleep_and_medium_fallback(self):
        with patch("sys.argv", ["classifier", "--dry-run"]):
            args = CLASSIFIER.parse_args()

        self.assertEqual(args.sleep_seconds, 60.0)
        self.assertEqual(args.fallback_whisper_model, "medium")
        self.assertEqual(args.fallback_quality_threshold, 0.70)
        self.assertFalse(args.disable_medium_fallback)

    def test_medium_fallback_reasons_for_low_quality(self):
        result = {
            "classification_result": {
                "automotive_domain": "review_teste",
                "topic_path": "review_teste__review_veiculo",
            },
            "transcript_quality": {
                "quality_score": 0.69,
                "quality_status": "partially_usable",
            },
            "technical_contexts": [],
            "vehicle_entities": [],
        }
        args = SimpleNamespace(
            stage="transcript_90s",
            transcripts_csv=None,
            disable_medium_fallback=False,
            whisper_model="small",
            fallback_whisper_model="medium",
            fallback_quality_threshold=0.70,
        )

        reasons = CLASSIFIER.medium_fallback_reasons(result, {"video": {}}, args)

        self.assertEqual(reasons, ["transcript_quality_below_threshold"])

    def test_medium_fallback_reasons_ignores_csv_transcripts(self):
        result = {
            "classification_result": {
                "automotive_domain": "diagnostico",
                "topic_path": "diagnostico",
            },
            "transcript_quality": {"quality_score": 0.30, "quality_status": "poor"},
            "technical_contexts": [],
            "vehicle_entities": [],
        }
        args = SimpleNamespace(
            stage="transcript_90s",
            transcripts_csv=Path("transcripts.csv"),
            disable_medium_fallback=False,
            whisper_model="small",
            fallback_whisper_model="medium",
            fallback_quality_threshold=0.70,
        )

        self.assertEqual(CLASSIFIER.medium_fallback_reasons(result, {"video": {}}, args), [])

    def test_medium_fallback_reasons_for_generic_topic_vehicle_and_context(self):
        result = {
            "classification_result": {
                "automotive_domain": "diagnostico",
                "topic_path": "diagnostico",
            },
            "transcript_quality": {"quality_score": 0.86, "quality_status": "usable"},
            "technical_contexts": [
                {
                    "compatibility_status": "needs_review",
                    "validation_issue": "sem combinacao compativel",
                }
            ],
            "vehicle_entities": [
                {
                    "vehicle_brand_raw": None,
                    "vehicle_model_raw": "Modelo X",
                    "resolved_entity_status": "not_found",
                }
            ],
        }
        args = SimpleNamespace(
            stage="transcript_90s",
            transcripts_csv=None,
            disable_medium_fallback=False,
            whisper_model="small",
            fallback_whisper_model="medium",
            fallback_quality_threshold=0.70,
        )

        reasons = CLASSIFIER.medium_fallback_reasons(result, {"video": {}}, args)

        self.assertEqual(
            reasons,
            [
                "technical_context_needs_review",
                "topic_path_generico",
                "vehicle_entity_mal_resolvida",
            ],
        )

    def test_medium_fallback_reasons_for_strategic_term_without_context(self):
        result = {
            "classification_result": {
                "automotive_domain": "manutencao_reparo",
                "topic_path": "manutencao_reparo__manutencao_preventiva",
            },
            "transcript_quality": {"quality_score": 0.90, "quality_status": "usable"},
            "technical_contexts": [],
            "vehicle_entities": [],
        }
        harness_input = {"video": {"title": "Como cuidar do radiador do carro"}}
        args = SimpleNamespace(
            stage="transcript_90s",
            transcripts_csv=None,
            disable_medium_fallback=False,
            whisper_model="small",
            fallback_whisper_model="medium",
            fallback_quality_threshold=0.70,
        )

        reasons = CLASSIFIER.medium_fallback_reasons(result, harness_input, args)

        self.assertEqual(reasons, ["termo_tecnico_estrategico_sem_contexto"])

    def test_fallback_regression_reasons_rejects_semantic_loss(self):
        initial = {
            "classification_result": {
                "automotive_domain": "review_teste",
                "topic_path": "review_teste__review_veiculo",
                "confidence_score": 0.92,
            },
            "technical_contexts": [
                {
                    "automotive_system": "motor",
                    "component": "turbo",
                    "problem": None,
                }
            ],
        }
        fallback = {
            "classification_result": {
                "automotive_domain": "sem_match_taxonomico",
                "topic_path": "mercado_produto__lancamentos",
                "confidence_score": 0.70,
            },
            "technical_contexts": [],
        }

        reasons = CLASSIFIER.fallback_regression_reasons(initial, fallback)

        self.assertIn("fallback_domain_topic_inconsistente", reasons)
        self.assertIn("fallback_domain_sem_match", reasons)
        self.assertIn("fallback_perdeu_contexto_tecnico", reasons)
        self.assertIn("fallback_confidence_menor", reasons)

    def test_fallback_regression_reasons_accepts_more_specific_result(self):
        initial = {
            "classification_result": {
                "automotive_domain": "review_teste",
                "topic_path": "review_teste",
                "confidence_score": 0.62,
            },
            "technical_contexts": [],
        }
        fallback = {
            "classification_result": {
                "automotive_domain": "review_teste",
                "topic_path": "review_teste__review_veiculo",
                "confidence_score": 0.82,
            },
            "technical_contexts": [
                {
                    "automotive_system": "motor",
                    "component": "turbo",
                    "problem": None,
                }
            ],
        }

        self.assertEqual(CLASSIFIER.fallback_regression_reasons(initial, fallback), [])

    def test_attach_fallback_summary_adds_initial_attempt_metadata(self):
        harness_input = {
            "video": {
                "transcription_metadata": {
                    "model": "medium",
                    "transcript_sha256": "abc",
                }
            }
        }
        initial_result = {
            "classification_result": {
                "topic_path": "diagnostico",
                "confidence_score": 0.62,
            },
            "transcript_quality": {
                "quality_score": 0.68,
                "quality_status": "partially_usable",
            },
        }
        args = SimpleNamespace(whisper_model="small", fallback_whisper_model="medium")

        enriched = CLASSIFIER.attach_fallback_summary(
            harness_input,
            initial_result,
            ["topic_path_generico"],
            args,
        )

        metadata = enriched["video"]["transcription_metadata"]
        self.assertTrue(metadata["fallback_triggered"])
        self.assertEqual(metadata["fallback_trigger_reasons"], ["topic_path_generico"])
        self.assertEqual(metadata["initial_whisper_model"], "small")
        self.assertEqual(metadata["fallback_whisper_model"], "medium")
        self.assertEqual(metadata["initial_topic_path"], "diagnostico")
        self.assertEqual(metadata["initial_confidence_score"], 0.62)

    def test_attach_fallback_summary_records_rejected_regression(self):
        harness_input = {"video": {"transcription_metadata": {}}}
        initial_result = {
            "classification_result": {
                "topic_path": "review_teste__review_veiculo",
                "confidence_score": 0.92,
            },
            "transcript_quality": {
                "quality_score": 0.72,
                "quality_status": "usable",
            },
        }
        args = SimpleNamespace(whisper_model="small", fallback_whisper_model="medium")

        enriched = CLASSIFIER.attach_fallback_summary(
            harness_input,
            initial_result,
            ["technical_context_needs_review"],
            args,
            fallback_rejected_reasons=["fallback_perdeu_contexto_tecnico"],
        )

        metadata = enriched["video"]["transcription_metadata"]
        self.assertTrue(metadata["fallback_rejected"])
        self.assertEqual(
            metadata["fallback_rejected_reasons"],
            ["fallback_perdeu_contexto_tecnico"],
        )


if __name__ == "__main__":
    unittest.main()
