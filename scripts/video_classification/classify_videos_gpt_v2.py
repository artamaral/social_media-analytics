import argparse
import csv
import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


BASE_DIR = Path(__file__).resolve().parent
REPO_DIR = BASE_DIR.parent.parent
DEFAULT_SKILL_PATH = REPO_DIR / "docs" / "external_data" / "58_GPT_VIDEO_CLASSIFIER_SKILL_V2.md"

TAXONOMY_VERSION = "taxonomia_video_v2"
PROMPT_CONTRACT_VERSION = "video_taxonomy_v2_classifier_r1"
OUTPUT_SCHEMA_VERSION = "video_taxonomy_v2_output_schema_r1"
# Marcador operacional para confirmar se a copia local/VPS esta atualizada.
SCRIPT_VERSION = "2026-07-24-r4-documented-confidence"
DEFAULT_TITLE_MODEL = "gpt-5-nano"
DEFAULT_TRANSCRIPT_MODEL = "gpt-5-nano"
DEFAULT_MAX_OUTPUT_TOKENS = 6000
OPENAI_RESPONSES_URL = "https://api.openai.com/v1/responses"

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
- Videos fora do escopo automotivo nao devem receber contexto tecnico primary.
- topic_path e topic_path_secondary devem existir na lista recebida.
- topic_path_secondary so entra com segundo tema forte e explicito.
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

Responda somente com JSON valido no schema video_taxonomy_v2_output_schema_r1.
"""

DEFAULT_SCHEMA = {
    "$id": OUTPUT_SCHEMA_VERSION,
    "title": "Video Taxonomy V2 GPT Classification Output",
    "type": "object",
    "additionalProperties": False,
    "required": ["classification_result", "technical_contexts", "vehicle_entities"],
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
            transcript = row.get("transcript_90s")
            if post_id and transcript:
                transcripts[post_id] = transcript
    return transcripts


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


def build_harness_input(post, stage, taxonomy, terms, transcript=None):
    evidence_level = "metadata_only"
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
        "description": None,
        "transcript_90s": transcript if stage == "transcript_90s" else None,
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
                "technical_contexts",
                "vehicle_entities",
            ],
        },
    }


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


def write_classification(base_url, headers, run_id, taxonomy_id, model, harness_input, result, raw_response):
    classification = result["classification_result"]
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
        "model_used": model,
        "prompt_contract_version": PROMPT_CONTRACT_VERSION,
        "output_schema_version": OUTPUT_SCHEMA_VERSION,
        "input_payload": harness_input,
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
        {
            "classification_result_id": result_id,
            "entity_order": row["entity_order"],
            "vehicle_brand_raw": row["vehicle_brand_raw"],
            "vehicle_model_raw": row["vehicle_model_raw"],
            "vehicle_year": row["vehicle_year"],
            "vehicle_generation": row["vehicle_generation"],
            "evidence_text": row["evidence_text"],
            "entity_status": row["entity_status"],
        }
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
    parser.add_argument("--transcripts-csv")
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

    if args.stage == "transcript_90s" and not args.transcripts_csv:
        parser.error("--transcripts-csv e obrigatorio para --stage transcript_90s nesta versao")

    return args


def main():
    args = parse_args()
    base_url, headers, _ = get_supabase_client()
    taxonomy = get_taxonomy(base_url, headers, args.taxonomy_version)
    terms = group_terms(taxonomy["terms"])
    schema = load_schema(args.schema_path)
    skill_text, skill_source = load_skill_text(args.skill_path)
    transcripts = load_transcripts_csv(args.transcripts_csv)
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

    for idx, post in enumerate(posts, start=1):
        post_id = post["post_id"]
        transcript = transcripts.get(post_id)

        if args.stage == "transcript_90s" and not transcript:
            failed += 1
            message = f"{post_id}: transcript_90s ausente"
            errors.append(message)
            print(f"[{idx}/{len(posts)}] {message}")
            continue

        harness_input = build_harness_input(post, args.stage, taxonomy, terms, transcript)
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
