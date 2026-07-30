import argparse
import csv
import hashlib
import json
import os
import re
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
import unicodedata
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


BASE_DIR = Path(__file__).resolve().parent
REPO_DIR = BASE_DIR.parent.parent
DEFAULT_SKILL_PATH = REPO_DIR / "docs" / "external_data" / "58_GPT_VIDEO_CLASSIFIER_SKILL_V2.md"

TAXONOMY_VERSION = "taxonomia_video_v2"
PROMPT_CONTRACT_VERSION = "video_taxonomy_v2_classifier_r2"
OUTPUT_SCHEMA_VERSION = "video_taxonomy_v2_output_schema_r2"
# Marcador operacional para confirmar se a copia local/VPS esta atualizada.
SCRIPT_VERSION = "2026-07-30-r18-topic-context-vehicle-guards"
DEFAULT_TITLE_MODEL = "gpt-5-nano"
DEFAULT_TRANSCRIPT_MODEL = "gpt-5-nano"
DEFAULT_MAX_OUTPUT_TOKENS = 6000
OPENAI_RESPONSES_URL = "https://api.openai.com/v1/responses"
DEFAULT_AUDIO_WORKDIR = Path("/opt/social-media-analytics/tmp/audio")
if os.name == "nt":
    DEFAULT_AUDIO_WORKDIR = REPO_DIR / "tmp" / "video_classification_audio"

CONDITIONAL_MODEL_KEYS = {"100", "bora", "link", "tipo"}

TRANSCRIPT_QUALITY_ISSUES = [
    "too_short",
    "truncated",
    "incoherent",
    "degraded_entities",
    "degraded_technical_terms",
    "excessive_noise",
]

DEFAULT_CONTENT_TYPES = [
    "educativo",
    "tutorial",
    "review",
    "comparativo",
    "noticia",
    "opiniao",
    "entretenimento",
    "alerta",
    "ranking",
    "case",
]

DEFAULT_AUDIENCE_INTENTS = [
    "resolver_problema",
    "evitar_prejuizo",
    "aprender_manutencao",
    "decidir_compra",
    "comparar_opcoes",
    "acompanhar_lancamento",
    "entender_powertrain",
    "entender_mercado",
    "entretenimento",
]

DEFAULT_SKILL = """Voce e um classificador da industria automotiva.
Classifique um unico video por chamada, usando apenas as evidencias textuais
recebidas no input e a Taxonomia Video V2 fornecida pelo sistema.

Nao invente informacoes. Se uma informacao nao estiver explicitamente
sustentada pelo titulo, descricao, transcricao ou metadado confiavel recebido no
input, deixe o campo como null quando permitido ou registre a limitacao em
validation_issues.

Regras obrigatorias:
- Videos de moto ou duas rodas sao fora_escopo.
- Fora_escopo tem precedencia quando houver evidencia textual de moto,
  nao-automotivo, transito/comportamento ou entretenimento sem tema tecnico,
  comercial ou produto automotivo principal.
- Se o video parecer automotivo, mas nao houver match seguro em topic_path
  especifico, use sem_match_taxonomico.
- sem_match_taxonomico exige needs_human_review=true, confidence_score < 0.50,
  technical_contexts=[] e motivo em validation_issues.
- Titulos genericos de alerta, cuidado, perigo ou entretenimento nao autorizam
  inferir diagnostico, luz de painel, scanner, motor, cambio ou componente sem
  esses termos aparecerem no input.
- Videos fora do escopo automotivo nao devem receber contexto tecnico primary.
- topic_path e topic_path_secondary devem existir na lista recebida.
- topic_path representa a proposta principal do video, nao o primeiro detalhe
  tecnico citado na transcricao.
- topic_path_secondary so entra com segundo tema forte e explicito.
- Em review_teste ou mercado_produto, motor, cambio, bateria, autonomia,
  turbo, flex ou eletrico devem ir para technical_contexts[] ou
  topic_path_secondary quando forem atributos do veiculo, nao topic_path
  principal.
- powertrain so e topic_path principal quando o video for explicitamente sobre
  motorizacao, autonomia, recarga, consumo, cambio ou tecnologia de propulsao.
- technical_contexts[] so entra com evidencia explicita.
- Cada technical_context representa uma unica combinacao de sistema, componente e problema.
- Se houver apenas dominio/topico generico, nao crie technical_context.
- Se um contexto tecnico nao existir na matriz recebida, marque
  compatibility_status=needs_review e needs_human_review=true.
- Nao use valores concatenados por ponto e virgula.
- motor e cambio nao sao rotulos soltos de tema.
- barulho e sinal textual; problem canonico deve ser ruido.
- Marca, modelo, ano e geracao devem preservar o valor bruto encontrado no input.
- Termos fora da taxonomia devem ir para taxonomy_gaps, nunca para campo canonico.
- confidence_score deve medir a forca da evidencia disponivel:
  0.90-1.00 evidencia direta, clara e especifica;
  0.70-0.89 evidencia boa, mas com alguma ambiguidade;
  0.50-0.69 evidencia parcial ou titulo pouco especifico;
  abaixo de 0.50 evidencia insuficiente e needs_human_review=true.
- Nao aumente confianca por conhecimento externo ou plausibilidade do canal.
- Seja conciso: evidence_summary, taxonomy_gaps e validation_issues devem ter
  apenas a evidencia necessaria para auditoria.
- Para title_metadata, use no maximo 3 technical_contexts e 2 vehicle_entities.
- Para transcript_90s, use no maximo 6 technical_contexts e 4 vehicle_entities.
- Para transcript_90s, avalie primeiro a qualidade textual do transcript e
  preencha transcript_quality. Voce nao esta avaliando o audio original.
- Para title_metadata, use quality_score=null, quality_status=not_evaluated,
  issues=[], impact_on_classification=none e needs_retranscription=false.
- impact_on_classification=medium exige needs_human_review=true e
  confidence_score <= 0.69; impact_on_classification=high exige
  needs_human_review=true e confidence_score <= 0.49.
- Transcript poor ou empty exige needs_retranscription=true.
- Contradicao entre titulo e transcript deve usar impact_on_classification=high.

Ordem para transcript_90s:
1. identifique se e fora_escopo;
2. identifique a intencao central do video;
3. escolha topic_path pela intencao central;
4. coloque termos tecnicos explicitos em technical_contexts[];
5. use topic_path_secondary so para segundo tema editorial forte.

Exemplos do Batch 1:
- aXbFPJMVGKw: avaliacao Changan Uni-T 2026 com motor 1.5 turbo deve manter
  review_teste__review_veiculo como principal; powertrain__combustao__turbo
  entra como contexto tecnico ou secundario.
- CjFrJg6VCjc: teste de autonomia deve preferir
  review_teste__teste_autonomia como principal; powertrain__eletrico__autonomia
  pode ser secundario/contexto.
- z55GnDEg7_U: se a transcricao mostra desmontagem, diagnostico e reparo de
  motor, use manutencao_reparo__reparo_corretivo__reparo_motor.
- RTZHxSE2t5M: gargalo de oficinas, pecas e reparacao deve usar
  pos_venda_reparacao como principal.
- 6qSnrkGd70I: radiador, aditivo, agua desmineralizada, drenagem ou
  limpa-radiador devem manter manutencao_reparo__manutencao_preventiva__arrefecimento.

Responda somente com JSON valido no schema video_taxonomy_v2_output_schema_r2.
"""

DEFAULT_SCHEMA = {
    "$id": OUTPUT_SCHEMA_VERSION,
    "title": "Video Taxonomy V2 GPT Classification Output",
    "type": "object",
    "additionalProperties": False,
    "required": [
        "classification_result",
        "transcript_quality",
        "technical_contexts",
        "vehicle_entities",
    ],
    "properties": {
        "classification_result": {
            "type": "object",
            "additionalProperties": False,
            "required": [
                "post_id",
                "evaluation_stage",
                "input_evidence_level",
                "automotive_domain",
                "activity_type",
                "topic_path",
                "topic_path_secondary",
                "content_type",
                "audience_intent",
                "confidence_score",
                "evidence_summary",
                "taxonomy_gaps",
                "validation_issues",
                "needs_human_review",
                "taxonomy_version",
            ],
            "properties": {
                "post_id": {"type": "string"},
                "evaluation_stage": {
                    "type": "string",
                    "enum": ["title_metadata", "transcript_90s"],
                },
                "input_evidence_level": {
                    "type": "string",
                    "enum": [
                        "metadata_only",
                        "title_description",
                        "transcript_90s",
                        "insufficient_evidence",
                    ],
                },
                "automotive_domain": {"type": "string"},
                "activity_type": {"type": "string"},
                "topic_path": {"type": "string"},
                "topic_path_secondary": {"type": ["string", "null"]},
                "content_type": {"type": ["string", "null"]},
                "audience_intent": {"type": ["string", "null"]},
                "confidence_score": {"type": "number"},
                "evidence_summary": {"type": "string"},
                "taxonomy_gaps": {"type": ["string", "null"]},
                "validation_issues": {"type": ["string", "null"]},
                "needs_human_review": {"type": "boolean"},
                "taxonomy_version": {"type": "string"},
            },
        },
        "transcript_quality": {
            "type": "object",
            "additionalProperties": False,
            "required": [
                "quality_score",
                "quality_status",
                "issues",
                "impact_on_classification",
                "needs_retranscription",
            ],
            "properties": {
                "quality_score": {"type": ["number", "null"]},
                "quality_status": {
                    "type": "string",
                    "enum": [
                        "not_evaluated",
                        "usable",
                        "partially_usable",
                        "poor",
                        "empty",
                    ],
                },
                "issues": {
                    "type": "array",
                    "items": {"type": "string", "enum": TRANSCRIPT_QUALITY_ISSUES},
                },
                "impact_on_classification": {
                    "type": "string",
                    "enum": ["none", "low", "medium", "high"],
                },
                "needs_retranscription": {"type": "boolean"},
            },
        },
        "technical_contexts": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "required": [
                    "context_order",
                    "topic_path",
                    "topic_path_secondary",
                    "automotive_system",
                    "component",
                    "problem",
                    "context_role",
                    "evidence_text",
                    "compatibility_status",
                    "validation_issue",
                    "needs_human_review",
                ],
                "properties": {
                    "context_order": {"type": "integer"},
                    "topic_path": {"type": "string"},
                    "topic_path_secondary": {"type": ["string", "null"]},
                    "automotive_system": {"type": ["string", "null"]},
                    "component": {"type": ["string", "null"]},
                    "problem": {"type": ["string", "null"]},
                    "context_role": {
                        "type": "string",
                        "enum": ["primary", "secondary", "supporting", "incidental"],
                    },
                    "evidence_text": {"type": "string"},
                    "compatibility_status": {
                        "type": "string",
                        "enum": [
                            "allowed",
                            "allowed_with_evidence",
                            "not_applicable",
                            "needs_review",
                        ],
                    },
                    "validation_issue": {"type": ["string", "null"]},
                    "needs_human_review": {"type": "boolean"},
                },
            },
        },
        "vehicle_entities": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "required": [
                    "entity_order",
                    "vehicle_brand_raw",
                    "vehicle_model_raw",
                    "vehicle_year",
                    "vehicle_generation",
                    "evidence_text",
                    "entity_status",
                ],
                "properties": {
                    "entity_order": {"type": "integer"},
                    "vehicle_brand_raw": {"type": ["string", "null"]},
                    "vehicle_model_raw": {"type": ["string", "null"]},
                    "vehicle_year": {"type": ["integer", "null"]},
                    "vehicle_generation": {"type": ["string", "null"]},
                    "evidence_text": {"type": "string"},
                    "entity_status": {
                        "type": "string",
                        "enum": ["extracted", "matched", "not_found", "needs_review"],
                    },
                },
            },
        },
    },
}


def load_local_env():
    candidates = [
        BASE_DIR / ".env",
        Path.cwd() / ".env",
        Path("/opt/social-media-analytics/config/classifier.env"),
        REPO_DIR / ".env",
    ]

    for env_path in candidates:
        if not env_path.exists():
            continue

        for raw_line in env_path.read_text(encoding="utf-8").splitlines():
            line = raw_line.strip()

            if not line or line.startswith("#") or "=" not in line:
                continue

            key, value = line.split("=", 1)
            key = key.strip()
            value = value.strip().strip('"').strip("'")

            if key and key not in os.environ:
                os.environ[key] = value


def require_env(name):
    value = os.environ.get(name)

    if not value:
        raise RuntimeError(f"Variavel de ambiente obrigatoria ausente: {name}")

    return value


def normalize_supabase_url(url):
    normalized = url.rstrip("/")

    if normalized.endswith("/rest/v1"):
        normalized = normalized[: -len("/rest/v1")]

    return normalized


def rest_url(base_url, table):
    return f"{base_url}/rest/v1/{table}"


def build_supabase_headers(supabase_key, prefer=None):
    headers = {
        "apikey": supabase_key,
        "Authorization": f"Bearer {supabase_key}",
        "Content-Type": "application/json",
    }

    if prefer:
        headers["Prefer"] = prefer

    return headers


def request_json(method, url, headers, params=None, payload=None, timeout=90):
    if params:
        separator = "&" if "?" in url else "?"
        url = f"{url}{separator}{urlencode(params)}"

    body = None
    if payload is not None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")

    request = Request(url, data=body, headers=headers, method=method)

    try:
        with urlopen(request, timeout=timeout) as response:
            text = response.read().decode("utf-8")
            return json.loads(text) if text else None
    except HTTPError as exc:
        error_text = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(
            f"Request falhou: {method} {url} status={exc.code} "
            f"body={error_text[:800]}"
        ) from exc


def load_text(path, default):
    if not path:
        return default

    file_path = Path(path)
    if not file_path.exists():
        raise RuntimeError(f"Arquivo nao encontrado: {file_path}")

    return file_path.read_text(encoding="utf-8")


def load_skill_text(path):
    if path:
        return load_text(path, DEFAULT_SKILL), str(Path(path))

    if DEFAULT_SKILL_PATH.exists():
        return DEFAULT_SKILL_PATH.read_text(encoding="utf-8"), str(DEFAULT_SKILL_PATH)

    return DEFAULT_SKILL, "embedded_default_skill"


def load_schema(path):
    if not path:
        return DEFAULT_SCHEMA

    return json.loads(load_text(path, ""))


def schema_for_openai(schema):
    if isinstance(schema, list):
        return [schema_for_openai(item) for item in schema]

    if not isinstance(schema, dict):
        return schema

    stripped = {}
    for key, value in schema.items():
        if key in {"$id", "$schema", "title"}:
            continue
        stripped[key] = schema_for_openai(value)
    return stripped


def validate_json_schema_shape(value, schema, path="$"):
    expected_type = schema.get("type")

    if expected_type:
        if not matches_type(value, expected_type):
            raise ValueError(f"{path}: tipo invalido, esperado={expected_type}")

    if isinstance(value, dict):
        allowed = set(schema.get("properties", {}).keys())
        if schema.get("additionalProperties") is False:
            extra = sorted(set(value.keys()) - allowed)
            if extra:
                raise ValueError(f"{path}: campos extras nao permitidos: {extra}")

        for key in schema.get("required", []):
            if key not in value:
                raise ValueError(f"{path}: campo obrigatorio ausente: {key}")

        for key, child_schema in schema.get("properties", {}).items():
            if key in value:
                validate_json_schema_shape(value[key], child_schema, f"{path}.{key}")

    if isinstance(value, list):
        item_schema = schema.get("items")
        if item_schema:
            for idx, item in enumerate(value):
                validate_json_schema_shape(item, item_schema, f"{path}[{idx}]")

    if "enum" in schema and value not in schema["enum"]:
        raise ValueError(f"{path}: valor fora do enum: {value}")


def matches_type(value, expected_type):
    if isinstance(expected_type, list):
        return any(matches_type(value, item) for item in expected_type)

    if expected_type == "object":
        return isinstance(value, dict)
    if expected_type == "array":
        return isinstance(value, list)
    if expected_type == "string":
        return isinstance(value, str)
    if expected_type == "number":
        return isinstance(value, (int, float)) and not isinstance(value, bool)
    if expected_type == "integer":
        return isinstance(value, int) and not isinstance(value, bool)
    if expected_type == "boolean":
        return isinstance(value, bool)
    if expected_type == "null":
        return value is None

    return True


def coalesce_text(value):
    if value is None:
        return None

    text = str(value).strip()
    return text if text else None


def normalize_nullable(value):
    if value is None:
        return None

    if isinstance(value, str) and not value.strip():
        return None

    return value


def strip_accents(value):
    return "".join(
        char
        for char in unicodedata.normalize("NFKD", value)
        if not unicodedata.combining(char)
    )


def normalize_catalog_key(value):
    value = "" if value is None else str(value)
    value = re.sub(r"\s+", " ", value.replace("\n", " ")).strip()
    value = strip_accents(value).lower()
    value = re.sub(r"[^a-z0-9]+", " ", value)
    return re.sub(r"\s+", " ", value).strip()


def contains_catalog_phrase(normalized_text, normalized_phrase):
    if not normalized_text or not normalized_phrase:
        return False

    return f" {normalized_phrase} " in f" {normalized_text} "


def has_nearby_catalog_phrase(normalized_text, normalized_phrase, normalized_anchor, window=8):
    if not (
        normalized_text
        and normalized_phrase
        and normalized_anchor
        and contains_catalog_phrase(normalized_text, normalized_phrase)
        and contains_catalog_phrase(normalized_text, normalized_anchor)
    ):
        return False

    tokens = normalized_text.split()
    phrase_tokens = normalized_phrase.split()
    anchor_tokens = normalized_anchor.split()
    if not phrase_tokens or not anchor_tokens:
        return False

    def positions(needle):
        size = len(needle)
        return [
            index
            for index in range(0, len(tokens) - size + 1)
            if tokens[index:index + size] == needle
        ]

    phrase_positions = positions(phrase_tokens)
    anchor_positions = positions(anchor_tokens)
    return any(
        abs(phrase_position - anchor_position) <= window
        for phrase_position in phrase_positions
        for anchor_position in anchor_positions
    )


def model_key_requires_explicit_manufacturer(model_key):
    return model_key in CONDITIONAL_MODEL_KEYS


def has_strong_vehicle_context_for_model(normalized_text, model_key, rows):
    if not model_key_requires_explicit_manufacturer(model_key):
        return True

    return any(
        has_nearby_catalog_phrase(normalized_text, model_key, row.get("manufacturer_key"))
        for row in rows
    )


def evidence_snippet(source_text, normalized_phrase, max_chars=180):
    if not source_text:
        return ""

    normalized_source = normalize_catalog_key(source_text)
    position = normalized_source.find(normalized_phrase)
    if position < 0:
        return compact_text(source_text, max_chars) or ""

    ratio = len(source_text) / max(len(normalized_source), 1)
    approx_position = int(position * ratio)
    start = max(0, approx_position - 70)
    end = min(len(source_text), approx_position + 110)
    return compact_text(source_text[start:end].strip(), max_chars) or ""


def extract_nearby_year(source_text, normalized_phrase):
    if not source_text:
        return None

    normalized_source = normalize_catalog_key(source_text)
    position = normalized_source.find(normalized_phrase)
    candidates = [
        int(match.group(0))
        for match in re.finditer(r"\b(?:19\d{2}|20\d{2}|2100)\b", source_text)
    ]
    if not candidates:
        return None

    if position < 0:
        return candidates[0] if len(set(candidates)) == 1 else None

    ratio = len(source_text) / max(len(normalized_source), 1)
    approx_position = int(position * ratio)
    for match in re.finditer(r"\b(?:19\d{2}|20\d{2}|2100)\b", source_text):
        if abs(match.start() - approx_position) <= 90:
            return int(match.group(0))

    return candidates[0] if len(set(candidates)) == 1 else None


def get_supabase_client():
    load_local_env()
    base_url = normalize_supabase_url(require_env("SUPABASE_URL"))
    key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY") or os.environ.get("SUPABASE_KEY")

    if not key:
        raise RuntimeError("Configure SUPABASE_SERVICE_ROLE_KEY ou SUPABASE_KEY")

    return base_url, build_supabase_headers(key), key


def get_taxonomy(base_url, headers, taxonomy_version):
    versions = request_json(
        "GET",
        rest_url(base_url, "video_taxonomy_versions"),
        headers,
        params={
            "select": "id,taxonomy_version,status",
            "taxonomy_version": f"eq.{taxonomy_version}",
            "limit": "1",
        },
    )

    if not versions:
        raise RuntimeError(
            "Taxonomia V2 nao encontrada no Supabase. "
            "Aplique a DDL e carregue video_taxonomy_versions/topic_paths antes."
        )

    taxonomy = versions[0]
    taxonomy_id = taxonomy["id"]
    topic_paths = request_json(
        "GET",
        rest_url(base_url, "video_taxonomy_topic_paths"),
        headers,
        params={
            "select": (
                "topic_path_code,label_pt,parent_code,level,automotive_domain,"
                "default_activity_type,description,example_signals,"
                "requires_technical_context,allows_secondary_topic"
            ),
            "taxonomy_version_id": f"eq.{taxonomy_id}",
            "is_active": "eq.true",
            "order": "level.asc,topic_path_code.asc",
            "limit": "1000",
        },
    )
    compatibility = request_json(
        "GET",
        rest_url(base_url, "video_taxonomy_technical_compatibility"),
        headers,
        params={
            "select": (
                "compatibility_id,topic_path_code,automotive_system,component,"
                "problem,compatibility_status,required_evidence,example_signals,"
                "validation_rule"
            ),
            "taxonomy_version_id": f"eq.{taxonomy_id}",
            "is_active": "eq.true",
            "order": "compatibility_id.asc",
            "limit": "2000",
        },
    )
    terms = request_json(
        "GET",
        rest_url(base_url, "video_taxonomy_terms"),
        headers,
        params={
            "select": "dimension,term_code,label_pt",
            "taxonomy_version_id": f"eq.{taxonomy_id}",
            "is_active": "eq.true",
            "order": "dimension.asc,term_code.asc",
            "limit": "1000",
        },
    )

    if not topic_paths:
        raise RuntimeError("Taxonomia V2 sem topic_paths ativos no Supabase.")

    return {
        "id": taxonomy_id,
        "version": taxonomy["taxonomy_version"],
        "topic_paths": topic_paths or [],
        "compatibility": compatibility or [],
        "terms": terms or [],
    }


def fetch_posts(base_url, headers, post_ids, limit, include_already_classified, stage):
    if post_ids:
        raw_posts = request_json(
            "GET",
            rest_url(base_url, "posts"),
            headers,
            params={
                "select": (
                    "post_id,title,video_type,duration,views,likes,comments,"
                    "post_date,creator_id"
                ),
                "post_id": f"in.({','.join(post_ids)})",
                "limit": str(max(limit, len(post_ids))),
            },
        )
    else:
        raw_posts = request_json(
            "GET",
            rest_url(base_url, "posts"),
            headers,
            params={
                "select": (
                    "post_id,title,video_type,duration,views,likes,comments,"
                    "post_date,creator_id"
                ),
                "post_id": "not.is.null",
                "title": "not.is.null",
                "video_type": "in.(long,short)",
                "order": "post_date.desc",
                "limit": str(limit * 5 if not include_already_classified else limit),
            },
        )

    posts = raw_posts or []
    attach_creators(base_url, headers, posts)

    if not include_already_classified and posts:
        classified = fetch_already_classified(base_url, headers, [p["post_id"] for p in posts], stage)
        posts = [post for post in posts if post["post_id"] not in classified]

    return posts[:limit]


def attach_creators(base_url, headers, posts):
    creator_ids = sorted({str(post.get("creator_id")) for post in posts if post.get("creator_id")})

    if not creator_ids:
        for post in posts:
            post["creator"] = None
            post["followers"] = None
        return

    creators = request_json(
        "GET",
        rest_url(base_url, "creators"),
        headers,
        params={
            "select": "id,username,followers",
            "id": f"in.({','.join(creator_ids)})",
            "limit": str(len(creator_ids)),
        },
    )
    by_id = {row["id"]: row for row in creators or []}

    for post in posts:
        creator = by_id.get(post.get("creator_id"), {})
        post["creator"] = creator.get("username")
        post["followers"] = creator.get("followers")


def fetch_already_classified(base_url, headers, post_ids, stage):
    if not post_ids:
        return set()

    rows = request_json(
        "GET",
        rest_url(base_url, "v_video_classification_latest"),
        headers,
        params={
            "select": "post_id",
            "post_id": f"in.({','.join(post_ids)})",
            "evaluation_stage": f"eq.{stage}",
            "limit": str(len(post_ids)),
        },
    )
    return {row["post_id"] for row in rows or []}


def load_transcripts_csv(path):
    if not path:
        return {}

    transcripts = {}
    with Path(path).open("r", encoding="utf-8-sig", newline="") as handle:
        for row in csv.DictReader(handle):
            post_id = row.get("post_id")
            if not post_id:
                continue

            transcript = row.get("transcript_90s") or ""
            transcripts[post_id] = {
                "text": transcript,
                "metadata": build_transcription_metadata(
                    transcript,
                    source_method=row.get("source_method") or "transcripts_csv",
                    model=row.get("whisper_model"),
                    compute_type=row.get("compute_type"),
                    language=row.get("language") or "pt",
                    duration_seconds=to_optional_int(row.get("transcribed_duration_seconds")),
                ),
            }
    return transcripts


def load_descriptions_csv(path):
    if not path:
        return {}

    descriptions = {}
    with Path(path).open("r", encoding="utf-8-sig", newline="") as handle:
        for row in csv.DictReader(handle):
            post_id = row.get("post_id")
            if not post_id:
                continue

            status = (row.get("description_status") or row.get("status") or "").strip()
            description = row.get("description") or ""
            if status and status != "success":
                description = ""

            descriptions[post_id] = {
                "description": description,
                "status": status or ("success" if description else "empty"),
                "description_length": len(description),
            }
    return descriptions


def to_optional_int(value):
    if value in (None, ""):
        return None

    try:
        return int(float(value))
    except (TypeError, ValueError):
        return None


def build_transcription_metadata(
    transcript,
    source_method,
    model,
    compute_type,
    language,
    duration_seconds,
):
    transcript_bytes = (transcript or "").encode("utf-8")
    return {
        "source_method": source_method,
        "model": model,
        "compute_type": compute_type,
        "language": language,
        "transcribed_duration_seconds": duration_seconds,
        "transcript_sha256": hashlib.sha256(transcript_bytes).hexdigest(),
        "transcript_char_count": len(transcript or ""),
    }


def ensure_whisper_runtime(model_name, device, compute_type):
    try:
        import imageio_ffmpeg
        from faster_whisper import WhisperModel
    except ImportError as exc:
        raise RuntimeError(
            "Dependencias ausentes. Instale scripts/video_classification/requirements.txt."
        ) from exc

    ffmpeg_path = imageio_ffmpeg.get_ffmpeg_exe()
    if not ffmpeg_path or not Path(ffmpeg_path).exists():
        raise RuntimeError("imageio-ffmpeg nao retornou um binario ffmpeg valido")

    model = WhisperModel(model_name, device=device, compute_type=compute_type)
    return {"model": model, "ffmpeg_path": ffmpeg_path}


def seconds_to_timestamp(seconds):
    minutes, remainder = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    return f"{hours:02d}:{minutes:02d}:{remainder:02d}"


def target_transcription_duration(post_duration, transcript_seconds):
    duration = to_optional_int(post_duration)
    if duration and duration > 0:
        return min(duration, transcript_seconds)
    return transcript_seconds


def run_subprocess(command, timeout):
    env = os.environ.copy()
    env["PYTHONWARNINGS"] = "ignore"
    return subprocess.run(
        command,
        cwd=REPO_DIR,
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=timeout,
        check=False,
    )


def ytdlp_common_options(cookies_path=None, user_agent=None, referer=None, extractor_args=None, plugin_dirs=None, proxy=None):
    options = []
    for plugin_dir in plugin_dirs or []:
        options.extend(["--plugin-dirs", str(plugin_dir)])
    for extractor_arg in extractor_args or []:
        options.extend(["--extractor-args", extractor_arg])
    if cookies_path:
        options.extend(["--cookies", str(cookies_path)])
    if user_agent:
        options.extend(["--user-agent", user_agent])
    if referer:
        options.extend(["--referer", referer])
    if proxy:
        options.extend(["--proxy", proxy])
    return options


def download_audio_segment(
    post_id,
    duration_seconds,
    output_path,
    ffmpeg_path,
    cookies_path=None,
    user_agent=None,
    referer=None,
    extractor_args=None,
    plugin_dirs=None,
    proxy=None,
    use_section=True,
):
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_template = str(output_path.with_suffix(""))
    video_url = f"https://www.youtube.com/watch?v={post_id}"
    command = [
        sys.executable,
        "-m",
        "yt_dlp",
        "--quiet",
        "--no-warnings",
        "--no-playlist",
        "--extract-audio",
        "--audio-format",
        "wav",
        "--audio-quality",
        "0",
        "--ffmpeg-location",
        ffmpeg_path,
        "--force-overwrites",
        "-o",
        f"{output_template}.%(ext)s",
        video_url,
    ]
    extra_options = ytdlp_common_options(
        cookies_path,
        user_agent,
        referer,
        extractor_args,
        plugin_dirs,
        proxy,
    )
    if use_section:
        extra_options.extend([
            "--download-sections",
            f"*00:00:00-{seconds_to_timestamp(duration_seconds)}",
        ])
    command[-1:-1] = extra_options
    result = run_subprocess(command, timeout=300)
    if result.returncode != 0:
        detail = (result.stderr or result.stdout).strip()
        raise RuntimeError(detail[:1200] if detail else "yt-dlp falhou sem detalhe")

    if output_path.exists():
        return

    candidates = sorted(output_path.parent.glob(f"{output_path.stem}.*"))
    if not candidates:
        raise RuntimeError("audio baixado nao foi encontrado no caminho esperado")
    candidates[0].replace(output_path)


def download_audio_source(
    post_id,
    output_stem,
    cookies_path=None,
    user_agent=None,
    referer=None,
    extractor_args=None,
    plugin_dirs=None,
    proxy=None,
):
    video_url = f"https://www.youtube.com/watch?v={post_id}"
    command = [
        sys.executable,
        "-m",
        "yt_dlp",
        "--quiet",
        "--no-warnings",
        "--no-playlist",
        "-f",
        "139/140/18/best[height<=360][ext=mp4]/bestaudio[ext=m4a]/bestaudio/best",
        "--force-overwrites",
        "-o",
        f"{output_stem}.%(ext)s",
        video_url,
    ]
    command[-1:-1] = ytdlp_common_options(
        cookies_path,
        user_agent,
        referer,
        extractor_args,
        plugin_dirs,
        proxy,
    )
    result = run_subprocess(command, timeout=300)
    if result.returncode != 0:
        detail = (result.stderr or result.stdout).strip()
        raise RuntimeError(detail[:1200] if detail else "yt-dlp source download falhou sem detalhe")

    candidates = sorted(output_stem.parent.glob(f"{output_stem.name}.*"))
    if not candidates:
        raise RuntimeError("arquivo fonte de audio/video nao foi encontrado")
    return candidates[0]


def convert_audio_source_to_wav(source_path, output_path, ffmpeg_path, duration_seconds):
    command = [
        ffmpeg_path,
        "-y",
        "-hide_banner",
        "-loglevel",
        "error",
        "-ss",
        "0",
        "-t",
        str(duration_seconds),
        "-i",
        str(source_path),
        "-vn",
        "-ac",
        "1",
        "-ar",
        "16000",
        str(output_path),
    ]
    result = run_subprocess(command, timeout=180)
    if result.returncode != 0:
        detail = (result.stderr or result.stdout).strip()
        raise RuntimeError(detail[:1200] if detail else "ffmpeg fallback falhou sem detalhe")
    if not output_path.exists():
        raise RuntimeError("audio wav do fallback nao foi encontrado")


def download_audio_segment_stable(
    post_id,
    duration_seconds,
    output_path,
    ffmpeg_path,
    cookies_path=None,
    user_agent=None,
    referer=None,
    extractor_args=None,
    plugin_dirs=None,
    proxy=None,
):
    output_path.parent.mkdir(parents=True, exist_ok=True)
    source_stem = output_path.parent / f"{output_path.stem}_source"
    source_path = None
    try:
        source_path = download_audio_source(
            post_id,
            source_stem,
            cookies_path,
            user_agent,
            referer,
            extractor_args,
            plugin_dirs,
            proxy,
        )
        convert_audio_source_to_wav(source_path, output_path, ffmpeg_path, duration_seconds)
    finally:
        for candidate in output_path.parent.glob(f"{source_stem.name}.*"):
            if candidate.exists():
                candidate.unlink()


def transcribe_post_local(post, runtime, args):
    post_id = post["post_id"]
    post_duration = to_optional_int(post.get("duration"))
    target_duration = target_transcription_duration(
        post_duration,
        args.transcript_seconds,
    )

    audio_path = args.audio_workdir / f"{post_id}_{target_duration}s.wav"
    source_method = "yt-dlp+faster-whisper-local"
    try:
        try:
            download_audio_segment(
                post_id,
                target_duration,
                audio_path,
                runtime["ffmpeg_path"],
                args.yt_dlp_cookies,
                args.yt_dlp_user_agent,
                args.yt_dlp_referer,
                args.yt_dlp_extractor_args,
                args.yt_dlp_plugin_dir,
                args.yt_dlp_proxy,
            )
        except RuntimeError as first_error:
            try:
                download_audio_segment_stable(
                    post_id,
                    target_duration,
                    audio_path,
                    runtime["ffmpeg_path"],
                    args.yt_dlp_cookies,
                    args.yt_dlp_user_agent,
                    args.yt_dlp_referer,
                    args.yt_dlp_extractor_args,
                    args.yt_dlp_plugin_dir,
                    args.yt_dlp_proxy,
                )
                source_method = "yt-dlp-source+ffmpeg-segment+faster-whisper-local"
            except RuntimeError as fallback_error:
                raise RuntimeError(
                    "falha no download/conversao de audio; "
                    f"tentativa_yt_dlp={first_error}; fallback_estavel={fallback_error}"
                ) from fallback_error
        segments, _info = runtime["model"].transcribe(
            str(audio_path),
            language=args.whisper_language,
            vad_filter=True,
        )
        transcript = " ".join(
            segment.text.strip() for segment in segments if segment.text.strip()
        )
        transcript = " ".join(transcript.split())
        metadata = build_transcription_metadata(
            transcript,
            source_method=source_method,
            model=args.whisper_model,
            compute_type=args.whisper_compute_type,
            language=args.whisper_language,
            duration_seconds=target_duration,
        )
        return {"text": transcript, "metadata": metadata, "status": "success" if transcript else "partial"}
    finally:
        if audio_path.exists():
            audio_path.unlink()


def write_transcription_rows(output_path, rows):
    if not output_path:
        return

    fields = [
        "post_id",
        "video_url",
        "transcription_status",
        "transcribed_duration_seconds",
        "transcript_90s",
        "language",
        "whisper_model",
        "compute_type",
        "source_method",
        "error_message",
        "created_at",
    ]
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, quoting=csv.QUOTE_ALL)
        writer.writeheader()
        writer.writerows(rows)


def group_terms(terms):
    grouped = {}
    for row in terms:
        grouped.setdefault(row["dimension"], []).append(row["term_code"])

    grouped.setdefault("content_type", DEFAULT_CONTENT_TYPES)
    grouped.setdefault("audience_intent", DEFAULT_AUDIENCE_INTENTS)
    grouped.setdefault("context_role", ["primary", "secondary", "supporting", "incidental"])
    grouped.setdefault(
        "compatibility_status",
        ["allowed", "allowed_with_evidence", "not_applicable", "needs_review"],
    )
    return grouped


def compact_text(value, max_chars=180):
    if value is None:
        return None

    text = str(value).strip()
    if len(text) <= max_chars:
        return text

    return text[: max_chars - 3].rstrip() + "..."


def compact_topic_paths(topic_paths):
    compacted = []
    for row in topic_paths:
        compacted.append(
            {
                "code": row.get("topic_path_code"),
                "parent": row.get("parent_code"),
                "domain": row.get("automotive_domain"),
                "activity": row.get("default_activity_type"),
                "requires_technical_context": row.get("requires_technical_context"),
                "allows_secondary_topic": row.get("allows_secondary_topic"),
                "signals": compact_text(row.get("example_signals"), 140),
            }
        )
    return compacted


def compact_technical_compatibility(compatibility_rows):
    compacted = []
    for row in compatibility_rows:
        compacted.append(
            {
                "topic_path": row.get("topic_path_code"),
                "system": row.get("automotive_system"),
                "component": row.get("component"),
                "problem": row.get("problem"),
                "status": row.get("compatibility_status"),
                "signals": compact_text(row.get("example_signals"), 120),
            }
        )
    return compacted


def build_harness_input(
    post,
    stage,
    taxonomy,
    terms,
    transcript=None,
    transcription_metadata=None,
    description=None,
):
    evidence_level = "metadata_only"
    if description:
        evidence_level = "title_description"
    if stage == "transcript_90s":
        evidence_level = "transcript_90s" if transcript else "insufficient_evidence"

    video = {
        "post_id": post.get("post_id"),
        "evaluation_stage": stage,
        "input_evidence_level": evidence_level,
        "title": post.get("title"),
        "creator": post.get("creator"),
        "video_type": post.get("video_type"),
        "duration": post.get("duration"),
        "views": post.get("views"),
        "likes": post.get("likes"),
        "comments": post.get("comments"),
        "post_date": post.get("post_date"),
        "description": description,
        "transcript_90s": transcript if stage == "transcript_90s" else None,
        "transcription_metadata": (
            transcription_metadata if stage == "transcript_90s" else None
        ),
    }

    return {
        "video": video,
        "taxonomy_version": taxonomy["version"],
        "topic_paths": compact_topic_paths(taxonomy["topic_paths"]),
        "technical_compatibility": compact_technical_compatibility(taxonomy["compatibility"]),
        "controlled_terms": terms,
        "output_contract": {
            "prompt_contract_version": PROMPT_CONTRACT_VERSION,
            "output_schema_version": OUTPUT_SCHEMA_VERSION,
            "required_blocks": [
                "classification_result",
                "transcript_quality",
                "technical_contexts",
                "vehicle_entities",
            ],
        },
    }


def sanitize_harness_input_for_storage(harness_input):
    sanitized = json.loads(json.dumps(harness_input))
    video = sanitized.get("video", {})
    if "transcript_90s" in video:
        video["transcript_90s"] = None
        video["transcript_redacted"] = True
    return sanitized


def call_openai(model, skill_text, schema, harness_input, max_output_tokens):
    api_key = require_env("OPENAI_API_KEY")
    payload = {
        "model": model,
        "instructions": skill_text,
        "input": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "input_text",
                        "text": (
                            "Classifique este video e responda somente JSON valido "
                            "no schema informado.\n\n"
                            + json.dumps(harness_input, ensure_ascii=False)
                        ),
                    }
                ],
            }
        ],
        "text": {
            "format": {
                "type": "json_schema",
                "name": OUTPUT_SCHEMA_VERSION,
                "strict": True,
                "schema": schema_for_openai(schema),
            }
        },
        "max_output_tokens": max_output_tokens,
    }
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    response = request_json(
        "POST",
        OPENAI_RESPONSES_URL,
        headers,
        payload=payload,
        timeout=180,
    )
    text = extract_response_text(response)

    if not text:
        if response.get("status") == "incomplete":
            reason = (response.get("incomplete_details") or {}).get("reason")
            if reason == "max_output_tokens":
                raise RuntimeError(
                    "Resposta OpenAI incompleta por max_output_tokens. "
                    f"Tente aumentar --max-output-tokens acima de {max_output_tokens} "
                    "ou reduza o lote para reprocessar este post_id."
                )

        raise RuntimeError(f"Resposta OpenAI sem output_text: {json.dumps(response)[:800]}")

    try:
        parsed = json.loads(text)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"Resposta OpenAI nao e JSON valido: {exc}: {text[:500]}") from exc

    return parsed, response


def extract_response_text(response):
    if isinstance(response, dict) and response.get("output_text"):
        return response["output_text"]

    for item in response.get("output", []) if isinstance(response, dict) else []:
        for content in item.get("content", []):
            if content.get("type") in {"output_text", "text"} and content.get("text"):
                return content["text"]

    return None


def validate_classification(result, schema, taxonomy, stage, post_id):
    validate_json_schema_shape(result, schema)
    classification = result["classification_result"]
    transcript_quality = result["transcript_quality"]

    topic_codes = {row["topic_path_code"] for row in taxonomy["topic_paths"]}
    compatibility_rows = taxonomy["compatibility"]
    compatibility_keys = {
        (
            row["topic_path_code"],
            normalize_nullable(row.get("automotive_system")),
            normalize_nullable(row.get("component")),
            normalize_nullable(row.get("problem")),
        )
        for row in compatibility_rows
    }

    normalize_technical_contexts_for_validation(result, compatibility_keys)

    if classification["post_id"] != post_id:
        raise ValueError("post_id da resposta difere do video enviado")

    if classification["evaluation_stage"] != stage:
        raise ValueError("evaluation_stage da resposta difere do estagio enviado")

    if classification["taxonomy_version"] != taxonomy["version"]:
        raise ValueError("taxonomy_version da resposta difere da versao carregada")

    validate_transcript_quality(transcript_quality, classification, stage)

    if classification["topic_path"] not in topic_codes:
        raise ValueError(f"topic_path inexistente: {classification['topic_path']}")

    secondary = classification.get("topic_path_secondary")
    if secondary and secondary not in topic_codes:
        raise ValueError(f"topic_path_secondary inexistente: {secondary}")

    confidence = classification["confidence_score"]
    if confidence < 0 or confidence > 1:
        raise ValueError(f"confidence_score fora de 0..1: {confidence}")
    if confidence < 0.5 and not classification["needs_human_review"]:
        raise ValueError("confidence_score abaixo de 0.50 exige needs_human_review=true")
    if confidence < 0.5 and not classification.get("validation_issues"):
        raise ValueError("confidence_score abaixo de 0.50 exige validation_issues")
    if classification["topic_path"] == "sem_match_taxonomico":
        if not classification["needs_human_review"]:
            raise ValueError("sem_match_taxonomico exige needs_human_review=true")
        if confidence >= 0.5:
            raise ValueError("sem_match_taxonomico exige confidence_score abaixo de 0.50")
        if result["technical_contexts"]:
            raise ValueError("sem_match_taxonomico nao pode ter technical_contexts")
        if not classification.get("validation_issues"):
            raise ValueError("sem_match_taxonomico exige validation_issues")

    for context in result["technical_contexts"]:
        validate_context(context, topic_codes, compatibility_keys, classification["topic_path"])

    for entity in result["vehicle_entities"]:
        if entity["entity_order"] < 1:
            raise ValueError("vehicle_entities.entity_order deve ser >= 1")
        year = entity.get("vehicle_year")
        if year is not None and (year < 1900 or year > 2100):
            raise ValueError(f"vehicle_year invalido: {year}")
        if not any(
            entity.get(key)
            for key in [
                "vehicle_brand_raw",
                "vehicle_model_raw",
                "vehicle_year",
                "vehicle_generation",
            ]
        ):
            raise ValueError("vehicle_entity sem valor bruto extraido")


def validate_transcript_quality(quality, classification, stage):
    score = quality.get("quality_score")
    status = quality["quality_status"]
    impact = quality["impact_on_classification"]
    issues = quality["issues"]
    confidence = classification["confidence_score"]

    if len(issues) != len(set(issues)):
        raise ValueError("transcript_quality.issues contem valores duplicados")

    if stage == "title_metadata":
        if status != "not_evaluated" or score is not None:
            raise ValueError(
                "title_metadata exige transcript_quality not_evaluated e quality_score null"
            )
        if impact != "none" or quality["needs_retranscription"]:
            raise ValueError("title_metadata nao pode solicitar retranscricao")
        return

    if score is None or score < 0 or score > 1:
        raise ValueError("transcript_quality.quality_score deve ficar entre 0 e 1")

    if status == "not_evaluated":
        raise ValueError("transcript_90s exige avaliacao de qualidade textual")
    if status == "usable" and score < 0.70:
        raise ValueError("transcript_quality usable exige quality_score >= 0.70")
    if status == "partially_usable" and not 0.50 <= score < 0.70:
        raise ValueError("partially_usable exige quality_score entre 0.50 e 0.69")
    if status == "poor" and not 0 <= score < 0.50:
        raise ValueError("transcript_quality poor exige quality_score abaixo de 0.50")
    if status == "empty" and score != 0:
        raise ValueError("transcript_quality empty exige quality_score igual a 0")
    if status in {"poor", "empty"} and not quality["needs_retranscription"]:
        raise ValueError("transcript_quality poor/empty exige needs_retranscription=true")

    if impact == "medium":
        if not classification["needs_human_review"] or confidence > 0.69:
            raise ValueError(
                "impact medium exige needs_human_review=true e confidence_score <= 0.69"
            )
    if impact == "high":
        if not classification["needs_human_review"] or confidence > 0.49:
            raise ValueError(
                "impact high exige needs_human_review=true e confidence_score <= 0.49"
            )


def normalize_technical_contexts_for_validation(result, compatibility_keys):
    normalized_contexts = []

    for context in result["technical_contexts"]:
        has_technical_value = any(
            normalize_nullable(context.get(field))
            for field in ["automotive_system", "component", "problem"]
        )
        if not has_technical_value:
            continue

        key = (
            context["topic_path"],
            normalize_nullable(context.get("automotive_system")),
            normalize_nullable(context.get("component")),
            normalize_nullable(context.get("problem")),
        )

        if key not in compatibility_keys and context["compatibility_status"] != "needs_review":
            issue = (
                "technical_context sem combinacao compativel na matriz V2; "
                "marcado para revisao humana"
            )
            context["compatibility_status"] = "needs_review"
            context["needs_human_review"] = True
            context["validation_issue"] = append_validation_issue(
                context.get("validation_issue"), issue
            )

        normalized_contexts.append(context)

    result["technical_contexts"] = normalized_contexts


def append_validation_issue(current, issue):
    if not current:
        return issue

    if issue in current:
        return current

    return f"{current}; {issue}"


def validate_context(context, topic_codes, compatibility_keys, primary_topic):
    if context["context_order"] < 1:
        raise ValueError("technical_context.context_order deve ser >= 1")

    if context["topic_path"] not in topic_codes:
        raise ValueError(f"context topic_path inexistente: {context['topic_path']}")

    secondary = context.get("topic_path_secondary")
    if secondary and secondary not in topic_codes:
        raise ValueError(f"context topic_path_secondary inexistente: {secondary}")

    for field in ["automotive_system", "component", "problem"]:
        value = context.get(field)
        if isinstance(value, str) and ";" in value:
            raise ValueError(f"{field} contem multiplos valores concatenados")

    if context.get("problem") == "barulho":
        raise ValueError("problem canonico nao pode ser barulho; usar ruido")

    if primary_topic.startswith("fora_escopo") and context["context_role"] == "primary":
        raise ValueError("fora_escopo nao pode ter contexto tecnico primary")

    key = (
        context["topic_path"],
        normalize_nullable(context.get("automotive_system")),
        normalize_nullable(context.get("component")),
        normalize_nullable(context.get("problem")),
    )

    if key not in compatibility_keys and context["compatibility_status"] != "needs_review":
        raise ValueError(
            "technical_context sem compatibilidade e sem needs_review: "
            f"{context['topic_path']} / {context.get('automotive_system')} / "
            f"{context.get('component')} / {context.get('problem')}"
        )


def create_run(base_url, headers, taxonomy_id, round_id, stage, model, input_source, total):
    payload = {
        "round_id": round_id,
        "taxonomy_version_id": taxonomy_id,
        "classification_stage": stage,
        "model_used": model,
        "prompt_contract_version": PROMPT_CONTRACT_VERSION,
        "output_schema_version": OUTPUT_SCHEMA_VERSION,
        "input_source": input_source,
        "status": "running",
        "total_requested": total,
        "total_succeeded": 0,
        "total_failed": 0,
        "started_at": datetime.now(timezone.utc).isoformat(),
    }
    inserted = request_json(
        "POST",
        rest_url(base_url, "video_classification_runs"),
        build_supabase_headers(headers["apikey"], prefer="return=representation"),
        payload=payload,
    )
    return inserted[0]["id"]


def update_run(base_url, headers, run_id, status, succeeded, failed, error_summary=None):
    payload = {
        "status": status,
        "total_succeeded": succeeded,
        "total_failed": failed,
        "completed_at": datetime.now(timezone.utc).isoformat(),
    }

    if error_summary:
        payload["error_summary"] = error_summary[:2000]

    request_json(
        "PATCH",
        rest_url(base_url, "video_classification_runs"),
        build_supabase_headers(headers["apikey"], prefer="return=minimal"),
        params={"id": f"eq.{run_id}"},
        payload=payload,
    )


def fetch_vehicle_catalog_page(base_url, headers, offset, limit):
    return request_json(
        "GET",
        rest_url(base_url, "v_carrosnaweb_vehicle_catalog"),
        headers,
        params={
            "select": (
                "catalog_row_id,catalog_model_id,manufacturer_name,manufacturer_key,"
                "model_name,model_key,model_year"
            ),
            "order": "model_key.asc,model_year.desc",
            "limit": str(limit),
            "offset": str(offset),
        },
    ) or []


def fetch_vehicle_catalog(base_url, headers):
    rows = []
    page_size = 1000
    offset = 0
    while True:
        page = fetch_vehicle_catalog_page(base_url, headers, offset, page_size)
        rows.extend(page)
        if len(page) < page_size:
            return rows
        offset += page_size


def fetch_vehicle_catalog_candidates(base_url, headers, entity):
    brand_key = normalize_catalog_key(entity.get("vehicle_brand_raw"))
    model_key = normalize_catalog_key(entity.get("vehicle_model_raw"))
    vehicle_year = entity.get("vehicle_year")

    if not brand_key and not model_key:
        return []

    params = {
        "select": (
            "catalog_row_id,catalog_model_id,manufacturer_name,manufacturer_key,"
            "model_name,model_key,model_year"
        ),
        "limit": "50",
        "order": "model_year.desc",
    }

    if brand_key and model_key:
        params["manufacturer_key"] = f"eq.{brand_key}"
        params["model_key"] = f"eq.{model_key}"
    elif model_key:
        params["model_key"] = f"eq.{model_key}"
    else:
        params["manufacturer_key"] = f"eq.{brand_key}"

    if vehicle_year:
        params["model_year"] = f"eq.{vehicle_year}"

    candidates = request_json(
        "GET",
        rest_url(base_url, "v_carrosnaweb_vehicle_catalog"),
        headers,
        params=params,
    ) or []

    if candidates or not (brand_key and model_key):
        return candidates

    # O catalogo usa fabricante canonico; textos como "Caoa Changan" podem
    # nao bater exatamente. Nesse caso, tente modelo exato e valide ambiguidade.
    fallback_params = {
        "select": (
            "catalog_row_id,catalog_model_id,manufacturer_name,manufacturer_key,"
            "model_name,model_key,model_year"
        ),
        "model_key": f"eq.{model_key}",
        "limit": "50",
        "order": "model_year.desc",
    }
    if vehicle_year:
        fallback_params["model_year"] = f"eq.{vehicle_year}"
    return request_json(
        "GET",
        rest_url(base_url, "v_carrosnaweb_vehicle_catalog"),
        headers,
        params=fallback_params,
    ) or []


def unique_vehicle_model_keys(rows):
    return {
        (row["manufacturer_key"], row["model_key"])
        for row in rows
    }


def first_model_year_row(rows, vehicle_year=None):
    ordered = sorted(
        rows,
        key=lambda row: (
            row.get("model_year") or 0,
            row.get("catalog_row_id") or 0,
        ),
        reverse=True,
    )
    if vehicle_year:
        for row in ordered:
            if row.get("model_year") == vehicle_year:
                return row
    return ordered[0] if ordered else None


def resolve_vehicle_entity_from_candidates(entity, candidates):
    resolved = {
        "entity_status": entity["entity_status"],
        "canonical_manufacturer_name": None,
        "canonical_model_name": None,
        "canonical_model_year": None,
        "catalog_row_id": None,
        "catalog_model_id": None,
        "catalog_match_level": None,
        "match_source": "carrosnaweb_catalog",
        "match_confidence": None,
        "validation_issue": None,
    }

    if not candidates:
        resolved.update(
            {
                "entity_status": "not_found",
                "catalog_match_level": "not_found",
                "validation_issue": "entidade explicita nao encontrada em v_carrosnaweb_vehicle_catalog",
            }
        )
        return resolved

    vehicle_year = entity.get("vehicle_year")
    unique_models = unique_vehicle_model_keys(candidates)
    first = first_model_year_row(candidates, vehicle_year)

    resolved.update(
        {
            "canonical_manufacturer_name": first["manufacturer_name"],
            "canonical_model_name": first["model_name"],
            "catalog_model_id": first.get("catalog_model_id"),
        }
    )

    if vehicle_year:
        exact_year_candidates = [
            row for row in candidates if row.get("model_year") == vehicle_year
        ]
        if not exact_year_candidates:
            resolved.update(
                {
                    "entity_status": "needs_review",
                    "catalog_match_level": "not_found",
                    "match_confidence": 0.60,
                    "validation_issue": "ano informado nao existe para o modelo no catalogo",
                }
            )
            return resolved

        exact_models = unique_vehicle_model_keys(exact_year_candidates)
        first = first_model_year_row(exact_year_candidates, vehicle_year)
        resolved.update(
            {
                "entity_status": "matched" if len(exact_models) == 1 else "needs_review",
                "canonical_manufacturer_name": first["manufacturer_name"],
                "canonical_model_name": first["model_name"],
                "canonical_model_year": first["model_year"],
                "catalog_row_id": first["catalog_row_id"] if len(exact_models) == 1 else None,
                "catalog_model_id": first.get("catalog_model_id"),
                "catalog_match_level": "model_year" if len(exact_models) == 1 else "ambiguous",
                "match_confidence": 0.98 if len(exact_models) == 1 else 0.70,
                "validation_issue": None
                if len(exact_models) == 1
                else "ano informado encontrou multiplos registros no catalogo",
            }
        )
        return resolved

    if len(unique_models) == 1:
        resolved.update(
            {
                "entity_status": "matched",
                "catalog_match_level": "model",
                "match_confidence": 0.90,
                "validation_issue": None,
            }
        )
        return resolved

    resolved.update(
        {
            "entity_status": "needs_review",
            "catalog_match_level": "ambiguous",
            "match_confidence": 0.55,
            "validation_issue": "modelo/brand ambiguo no catalogo Carros na Web",
        }
    )
    return resolved


def resolve_vehicle_entity(base_url, headers, entity):
    candidates = fetch_vehicle_catalog_candidates(base_url, headers, entity)
    return resolve_vehicle_entity_from_candidates(entity, candidates)


def build_catalog_indexes(vehicle_catalog):
    by_model = {}
    for row in vehicle_catalog:
        model_key = row.get("model_key")
        if model_key:
            by_model.setdefault(model_key, []).append(row)
    return {"by_model": by_model}


def vehicle_evidence_sources(harness_input):
    video = harness_input.get("video") or {}
    sources = [
        ("title", video.get("title")),
        ("description", video.get("description")),
        ("transcript_90s", video.get("transcript_90s")),
    ]
    return [(name, text) for name, text in sources if text]


def select_script_vehicle_candidates(harness_input, vehicle_catalog):
    sources = vehicle_evidence_sources(harness_input)
    if not sources:
        return []

    indexes = build_catalog_indexes(vehicle_catalog)
    normalized_sources = [
        (name, text, normalize_catalog_key(text))
        for name, text in sources
    ]
    selected = []
    selected_model_keys = set()
    model_keys = sorted(indexes["by_model"].keys(), key=lambda item: (-len(item), item))

    for model_key in model_keys:
        if len(model_key) < 3:
            continue

        source_match = None
        for source_name, source_text, normalized_text in normalized_sources:
            if contains_catalog_phrase(normalized_text, model_key):
                source_match = (source_name, source_text, normalized_text)
                break

        if not source_match:
            continue

        if any(contains_catalog_phrase(previous, model_key) for previous in selected_model_keys):
            continue

        source_name, source_text, normalized_text = source_match
        rows = indexes["by_model"][model_key]
        if not has_strong_vehicle_context_for_model(normalized_text, model_key, rows):
            continue

        manufacturer_key = None
        for candidate in rows:
            if contains_catalog_phrase(normalized_text, candidate["manufacturer_key"]):
                manufacturer_key = candidate["manufacturer_key"]
                break

        filtered_rows = [
            row for row in rows if not manufacturer_key or row["manufacturer_key"] == manufacturer_key
        ]
        if not filtered_rows:
            filtered_rows = rows

        vehicle_year = extract_nearby_year(source_text, model_key)
        if vehicle_year:
            year_rows = [row for row in filtered_rows if row.get("model_year") == vehicle_year]
            if year_rows:
                filtered_rows = year_rows

        first = first_model_year_row(filtered_rows, vehicle_year)
        if not first:
            continue

        entity = {
            "entity_order": len(selected) + 1,
            "vehicle_brand_raw": first["manufacturer_name"] if manufacturer_key else None,
            "vehicle_model_raw": first["model_name"],
            "vehicle_year": vehicle_year,
            "vehicle_generation": None,
            "evidence_text": evidence_snippet(source_text, model_key),
            "entity_status": "extracted",
            "match_source": f"carrosnaweb_catalog_script:{source_name}",
        }
        resolved = resolve_vehicle_entity_from_candidates(entity, filtered_rows)
        resolved["match_source"] = entity["match_source"]
        entity.update(
            {
                "resolved_entity_status": resolved["entity_status"],
                "canonical_manufacturer_name": resolved["canonical_manufacturer_name"],
                "canonical_model_name": resolved["canonical_model_name"],
                "canonical_model_year": resolved["canonical_model_year"],
                "catalog_row_id": resolved["catalog_row_id"],
                "catalog_model_id": resolved["catalog_model_id"],
                "catalog_match_level": resolved["catalog_match_level"],
                "match_source": resolved["match_source"],
                "match_confidence": resolved["match_confidence"],
                "validation_issue": resolved["validation_issue"],
            }
        )
        selected.append(entity)
        selected_model_keys.add(model_key)

    return selected


def vehicle_entity_dedupe_key(entity):
    if entity.get("catalog_row_id"):
        return ("row", entity["catalog_row_id"])
    if entity.get("catalog_model_id"):
        return ("model", entity["catalog_model_id"])
    return (
        "raw",
        normalize_catalog_key(entity.get("vehicle_brand_raw")),
        normalize_catalog_key(entity.get("vehicle_model_raw")),
        entity.get("vehicle_year"),
    )


def merge_vehicle_entities(gpt_entities, script_entities):
    merged = []
    seen = set()
    for entity in list(script_entities) + list(gpt_entities):
        key = vehicle_entity_dedupe_key(entity)
        if key in seen:
            continue
        seen.add(key)
        copied = dict(entity)
        copied["entity_order"] = len(merged) + 1
        merged.append(copied)
    return merged


def build_vehicle_entity_row(base_url, headers, result_id, entity):
    resolved = {
        "entity_status": entity.get("resolved_entity_status"),
        "canonical_manufacturer_name": entity.get("canonical_manufacturer_name"),
        "canonical_model_name": entity.get("canonical_model_name"),
        "canonical_model_year": entity.get("canonical_model_year"),
        "catalog_row_id": entity.get("catalog_row_id"),
        "catalog_model_id": entity.get("catalog_model_id"),
        "catalog_match_level": entity.get("catalog_match_level"),
        "match_source": entity.get("match_source"),
        "match_confidence": entity.get("match_confidence"),
        "validation_issue": entity.get("validation_issue"),
    }
    if not resolved["entity_status"]:
        resolved = resolve_vehicle_entity(base_url, headers, entity)

    return {
        "classification_result_id": result_id,
        "entity_order": entity["entity_order"],
        "vehicle_brand_raw": entity["vehicle_brand_raw"],
        "vehicle_model_raw": entity["vehicle_model_raw"],
        "vehicle_year": entity["vehicle_year"],
        "vehicle_generation": entity["vehicle_generation"],
        "evidence_text": entity["evidence_text"],
        "entity_status": resolved["entity_status"],
        "canonical_manufacturer_name": resolved["canonical_manufacturer_name"],
        "canonical_model_name": resolved["canonical_model_name"],
        "canonical_model_year": resolved["canonical_model_year"],
        "catalog_row_id": resolved["catalog_row_id"],
        "catalog_model_id": resolved["catalog_model_id"],
        "catalog_match_level": resolved["catalog_match_level"],
        "match_source": resolved["match_source"],
        "match_confidence": resolved["match_confidence"],
        "validation_issue": resolved["validation_issue"],
    }


def resolve_vehicle_entity_with_catalog(entity, vehicle_catalog):
    indexes = build_catalog_indexes(vehicle_catalog)
    model_key = normalize_catalog_key(entity.get("vehicle_model_raw"))
    brand_key = normalize_catalog_key(entity.get("vehicle_brand_raw"))
    candidates = indexes["by_model"].get(model_key, []) if model_key else []

    if brand_key:
        branded_candidates = [
            row for row in candidates if row.get("manufacturer_key") == brand_key
        ]
        candidates = branded_candidates or candidates

    if entity.get("vehicle_year"):
        year_candidates = [
            row for row in candidates if row.get("model_year") == entity["vehicle_year"]
        ]
        candidates = year_candidates or candidates

    return resolve_vehicle_entity_from_candidates(entity, candidates)


def enrich_vehicle_entities_with_catalog(base_url, headers, result, harness_input=None, vehicle_catalog=None):
    script_entities = []
    topic_path = result["classification_result"].get("topic_path") or ""
    if harness_input and not topic_path.startswith("fora_escopo"):
        vehicle_catalog = vehicle_catalog or fetch_vehicle_catalog(base_url, headers)
        script_entities = select_script_vehicle_candidates(harness_input, vehicle_catalog)

    enriched = []
    for entity in result["vehicle_entities"]:
        if vehicle_catalog is None:
            resolved = resolve_vehicle_entity(base_url, headers, entity)
        else:
            resolved = resolve_vehicle_entity_with_catalog(entity, vehicle_catalog)
        enriched_entity = dict(entity)
        enriched_entity.update(
            {
                "resolved_entity_status": resolved["entity_status"],
                "canonical_manufacturer_name": resolved["canonical_manufacturer_name"],
                "canonical_model_name": resolved["canonical_model_name"],
                "canonical_model_year": resolved["canonical_model_year"],
                "catalog_row_id": resolved["catalog_row_id"],
                "catalog_model_id": resolved["catalog_model_id"],
                "catalog_match_level": resolved["catalog_match_level"],
                "match_source": resolved["match_source"],
                "match_confidence": resolved["match_confidence"],
                "validation_issue": resolved["validation_issue"],
            }
        )
        enriched.append(enriched_entity)
    result["vehicle_entities"] = merge_vehicle_entities(enriched, script_entities)
    return result


def write_classification(base_url, headers, run_id, taxonomy_id, model, harness_input, result, raw_response):
    classification = result["classification_result"]
    transcript_quality = result["transcript_quality"]
    result_payload = {
        "run_id": run_id,
        "taxonomy_version_id": taxonomy_id,
        "post_id": classification["post_id"],
        "evaluation_stage": classification["evaluation_stage"],
        "input_evidence_level": classification["input_evidence_level"],
        "automotive_domain": classification["automotive_domain"],
        "activity_type": classification["activity_type"],
        "topic_path": classification["topic_path"],
        "topic_path_secondary": classification["topic_path_secondary"],
        "content_type": classification["content_type"],
        "audience_intent": classification["audience_intent"],
        "confidence_score": classification["confidence_score"],
        "evidence_summary": classification["evidence_summary"],
        "taxonomy_gaps": classification["taxonomy_gaps"],
        "validation_issues": classification["validation_issues"],
        "needs_human_review": classification["needs_human_review"],
        "transcript_quality_score": transcript_quality["quality_score"],
        "transcript_quality_status": transcript_quality["quality_status"],
        "transcript_quality_issues": transcript_quality["issues"],
        "transcript_quality_impact": transcript_quality["impact_on_classification"],
        "needs_retranscription": transcript_quality["needs_retranscription"],
        "model_used": model,
        "prompt_contract_version": PROMPT_CONTRACT_VERSION,
        "output_schema_version": OUTPUT_SCHEMA_VERSION,
        "input_payload": sanitize_harness_input_for_storage(harness_input),
        "raw_response": raw_response,
    }
    inserted = request_json(
        "POST",
        rest_url(base_url, "video_classification_results"),
        build_supabase_headers(headers["apikey"], prefer="return=representation"),
        payload=result_payload,
    )
    result_id = inserted[0]["id"]

    context_rows = [
        {
            "classification_result_id": result_id,
            "taxonomy_version_id": taxonomy_id,
            "context_order": row["context_order"],
            "topic_path": row["topic_path"],
            "topic_path_secondary": row["topic_path_secondary"],
            "automotive_system": row["automotive_system"],
            "component": row["component"],
            "problem": row["problem"],
            "context_role": row["context_role"],
            "evidence_text": row["evidence_text"],
            "compatibility_status": row["compatibility_status"],
            "validation_issue": row["validation_issue"],
            "needs_human_review": row["needs_human_review"],
            "raw_context": row,
        }
        for row in result["technical_contexts"]
    ]
    if context_rows:
        request_json(
            "POST",
            rest_url(base_url, "video_classification_technical_contexts"),
            build_supabase_headers(headers["apikey"], prefer="return=minimal"),
            payload=context_rows,
        )

    entity_rows = [
        build_vehicle_entity_row(base_url, headers, result_id, row)
        for row in result["vehicle_entities"]
    ]
    if entity_rows:
        request_json(
            "POST",
            rest_url(base_url, "video_classification_vehicle_entities"),
            build_supabase_headers(headers["apikey"], prefer="return=minimal"),
            payload=entity_rows,
        )


def default_round_id(stage):
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return f"v2_{stage}_{stamp}"


def transcription_output_row(post_id, transcript_record=None, error_message=""):
    record = transcript_record or {}
    metadata = record.get("metadata") or {}
    return {
        "post_id": post_id,
        "video_url": f"https://www.youtube.com/watch?v={post_id}",
        "transcription_status": record.get("status") or ("failed" if error_message else "success"),
        "transcribed_duration_seconds": metadata.get("transcribed_duration_seconds"),
        "transcript_90s": record.get("text", ""),
        "language": metadata.get("language"),
        "whisper_model": metadata.get("model"),
        "compute_type": metadata.get("compute_type"),
        "source_method": metadata.get("source_method"),
        "error_message": error_message,
        "created_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }


def parse_args():
    parser = argparse.ArgumentParser(
        description="Classifica videos com GPT usando Taxonomia Video V2 e grava no Supabase."
    )
    parser.add_argument("--stage", choices=["title_metadata", "transcript_90s"], default="title_metadata")
    parser.add_argument("--limit", type=int, default=5)
    parser.add_argument("--post-id", action="append", default=[])
    parser.add_argument("--taxonomy-version", default=TAXONOMY_VERSION)
    parser.add_argument("--round-id")
    parser.add_argument("--input-source", default="supabase_posts")
    parser.add_argument("--skill-path")
    parser.add_argument("--schema-path")
    parser.add_argument("--descriptions-csv")
    parser.add_argument("--transcripts-csv")
    parser.add_argument("--transcripts-output", type=Path)
    parser.add_argument("--whisper-model", default="small")
    parser.add_argument("--whisper-device", default="cpu")
    parser.add_argument("--whisper-compute-type", default="int8")
    parser.add_argument("--whisper-language", default="pt")
    parser.add_argument("--transcript-seconds", type=int, default=90)
    parser.add_argument("--audio-workdir", type=Path, default=DEFAULT_AUDIO_WORKDIR)
    parser.add_argument("--yt-dlp-cookies", type=Path)
    parser.add_argument("--yt-dlp-user-agent")
    parser.add_argument("--yt-dlp-referer")
    parser.add_argument("--yt-dlp-extractor-args", action="append", default=[])
    parser.add_argument("--yt-dlp-plugin-dir", action="append", type=Path, default=[])
    parser.add_argument("--yt-dlp-proxy")
    parser.add_argument("--max-output-tokens", type=int, default=DEFAULT_MAX_OUTPUT_TOKENS)
    parser.add_argument("--sleep-seconds", type=float, default=0.5)
    parser.add_argument("--include-already-classified", action="store_true")
    parser.add_argument(
        "-V",
        "--version",
        "--script-version",
        action="version",
        version=f"%(prog)s {SCRIPT_VERSION}",
    )
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()

    if args.dry_run == args.write:
        parser.error("Use exatamente uma opcao: --dry-run ou --write")

    if args.limit < 1:
        parser.error("--limit deve ser >= 1")

    if args.post_id and args.limit < len(args.post_id):
        args.limit = len(args.post_id)

    if args.transcript_seconds < 1:
        parser.error("--transcript-seconds deve ser >= 1")

    if args.transcripts_output and args.stage != "transcript_90s":
        parser.error("--transcripts-output so pode ser usado com --stage transcript_90s")

    if args.yt_dlp_cookies and not args.yt_dlp_cookies.exists():
        parser.error("--yt-dlp-cookies aponta para arquivo inexistente")

    missing_plugin_dirs = [path for path in args.yt_dlp_plugin_dir if not path.exists()]
    if missing_plugin_dirs:
        parser.error(
            "--yt-dlp-plugin-dir aponta para caminho inexistente: "
            + ", ".join(str(path) for path in missing_plugin_dirs)
        )

    return args


def main():
    args = parse_args()
    base_url, headers, _ = get_supabase_client()
    taxonomy = get_taxonomy(base_url, headers, args.taxonomy_version)
    terms = group_terms(taxonomy["terms"])
    schema = load_schema(args.schema_path)
    skill_text, skill_source = load_skill_text(args.skill_path)
    descriptions = load_descriptions_csv(args.descriptions_csv)
    transcripts = load_transcripts_csv(args.transcripts_csv)
    whisper_runtime = None
    transcription_rows = []
    model = os.environ.get(
        "CLASSIFIER_MODEL_TRANSCRIPT" if args.stage == "transcript_90s" else "CLASSIFIER_MODEL_TITLE",
        DEFAULT_TRANSCRIPT_MODEL if args.stage == "transcript_90s" else DEFAULT_TITLE_MODEL,
    )
    posts = fetch_posts(
        base_url,
        headers,
        args.post_id,
        args.limit,
        args.include_already_classified,
        args.stage,
    )

    if not posts:
        print("Nenhum video elegivel encontrado.")
        return 0

    if args.stage == "transcript_90s" and not args.transcripts_csv:
        print(
            "Carregando faster-whisper "
            f"model={args.whisper_model} device={args.whisper_device} "
            f"compute_type={args.whisper_compute_type}..."
        )
        whisper_runtime = ensure_whisper_runtime(
            args.whisper_model,
            args.whisper_device,
            args.whisper_compute_type,
        )

    round_id = args.round_id or default_round_id(args.stage)
    run_id = None
    succeeded = 0
    failed = 0
    errors = []

    print("Classificador GPT Taxonomia V2")
    print(f"- script_version: {SCRIPT_VERSION}")
    print(f"- skill_source: {skill_source}")
    print(f"- stage: {args.stage}")
    print(f"- model: {model}")
    print(f"- max_output_tokens: {args.max_output_tokens}")
    print(f"- taxonomy_version: {taxonomy['version']} id={taxonomy['id']}")
    print(f"- topic_paths: {len(taxonomy['topic_paths'])}")
    print(f"- technical_compatibility: {len(taxonomy['compatibility'])}")
    print(f"- videos selecionados: {len(posts)}")
    if args.descriptions_csv:
        print(f"- descriptions_source: csv ({len(descriptions)})")
    if args.stage == "transcript_90s":
        source = "csv" if args.transcripts_csv else "faster-whisper-local"
        print(f"- transcription_source: {source}")
        if not args.transcripts_csv:
            print(f"- transcript_seconds: {args.transcript_seconds}")
    print(f"- modo: {'write' if args.write else 'dry-run'}")

    if args.write:
        run_id = create_run(
            base_url,
            headers,
            taxonomy["id"],
            round_id,
            args.stage,
            model,
            args.input_source,
            len(posts),
        )
        print(f"- run_id: {run_id}")

    vehicle_catalog = None
    for idx, post in enumerate(posts, start=1):
        post_id = post["post_id"]
        transcript_record = None

        if args.stage == "transcript_90s":
            if args.transcripts_csv:
                transcript_record = transcripts.get(post_id)
                if transcript_record is None:
                    failed += 1
                    message = f"{post_id}: transcript_90s ausente no CSV"
                    errors.append(message)
                    print(f"[{idx}/{len(posts)}] {message}")
                    continue
            else:
                print(f"[{idx}/{len(posts)}] transcrevendo {post_id}...")
                try:
                    transcript_record = transcribe_post_local(post, whisper_runtime, args)
                    transcription_rows.append(
                        transcription_output_row(post_id, transcript_record)
                    )
                    write_transcription_rows(args.transcripts_output, transcription_rows)
                except Exception as exc:
                    failed += 1
                    message = f"{post_id}: falha na transcricao local: {exc}"
                    errors.append(message)
                    transcription_rows.append(
                        transcription_output_row(post_id, error_message=str(exc))
                    )
                    write_transcription_rows(args.transcripts_output, transcription_rows)
                    print(f"ERRO: {message}")
                    continue

        transcript = transcript_record["text"] if transcript_record else None
        transcription_metadata = (
            transcript_record["metadata"] if transcript_record else None
        )
        description_record = descriptions.get(post_id) or {}
        description = description_record.get("description") or None
        harness_input = build_harness_input(
            post,
            args.stage,
            taxonomy,
            terms,
            transcript,
            transcription_metadata,
            description,
        )
        print(f"[{idx}/{len(posts)}] classificando {post_id}...")

        try:
            result, raw_response = call_openai(
                model,
                skill_text,
                schema,
                harness_input,
                args.max_output_tokens,
            )
            validate_classification(result, schema, taxonomy, args.stage, post_id)
            topic_path = result["classification_result"].get("topic_path") or ""
            if vehicle_catalog is None and not topic_path.startswith("fora_escopo"):
                vehicle_catalog = fetch_vehicle_catalog(base_url, headers)
            enrich_vehicle_entities_with_catalog(
                base_url,
                headers,
                result,
                harness_input,
                vehicle_catalog,
            )

            if args.write:
                write_classification(
                    base_url,
                    headers,
                    run_id,
                    taxonomy["id"],
                    model,
                    harness_input,
                    result,
                    raw_response,
                )
            else:
                print(json.dumps(result, ensure_ascii=False, indent=2))

            succeeded += 1
        except Exception as exc:
            failed += 1
            message = f"{post_id}: {exc}"
            errors.append(message)
            print(f"ERRO: {message}")

        if args.sleep_seconds:
            time.sleep(args.sleep_seconds)

    if args.write and run_id:
        status = "completed" if failed == 0 else "failed"
        update_run(base_url, headers, run_id, status, succeeded, failed, "\n".join(errors))

    print("\nResumo")
    print(f"- round_id: {round_id}")
    print(f"- sucesso: {succeeded}")
    print(f"- falhas: {failed}")

    return 0 if failed == 0 else 1


if __name__ == "__main__":
    try:
        sys.exit(main())
    except RuntimeError as exc:
        print(f"Erro: {exc}")
        sys.exit(1)
