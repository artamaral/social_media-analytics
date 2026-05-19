import os
import sys
from pathlib import Path
from datetime import UTC, datetime, timedelta

import requests


# ==============================
# CONFIG
# ==============================

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except AttributeError:
    pass


def load_local_env():
    """
    Carrega variaveis de um arquivo `.env` localizado ao lado do script.

    O objetivo e facilitar execucao manual do backfill sem depender de export
    previo no shell. O carregamento e conservador:
    - ignora linhas vazias e comentarios
    - aceita pares `CHAVE=valor`
    - nao sobrescreve variaveis que ja existam no ambiente

    Isso permite manter um `.env` local fora do Git, enquanto o script segue
    compativel com configuracao via ambiente quando necessario.
    """
    env_path = Path(__file__).with_name(".env")

    if not env_path.exists():
        return

    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()

        if not line or line.startswith("#") or "=" not in line:
            continue

        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")

        if key and key not in os.environ:
            os.environ[key] = value


load_local_env()

# Reusa a mesma base de configuracao do pipeline online.
# Isso reduz a divergencia operacional entre o script offline e o Cloud Run.
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
YOUTUBE_API_KEY = os.environ.get("YOUTUBE_API_KEY")


def normalize_supabase_url(url):
    """
    Normaliza a URL base do Supabase para evitar duplicacao de `/rest/v1`.

    Na pratica, alguns ambientes guardam:
    - apenas `https://<project>.supabase.co`
    - ou a URL completa `https://<project>.supabase.co/rest/v1`

    Como o script monta os endpoints adicionando `/rest/v1/...`, esta funcao
    remove o sufixo quando necessario para que os dois formatos funcionem.
    """
    if not url:
        return url

    normalized = url.rstrip("/")

    if normalized.endswith("/rest/v1"):
        normalized = normalized[: -len("/rest/v1")]

    return normalized


SUPABASE_URL = normalize_supabase_url(SUPABASE_URL)

HEADERS = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json",
}

# Parametros operacionais da fase 1.
# Mantidos como constantes simples para facilitar ajuste manual inicial.
DEFAULT_BATCH_SIZE = 50
LEGACY_AGE_DAYS = 7
MAX_TOTAL_CHECKS = 2
SUPABASE_PAGE_SIZE = 1000
SUPABASE_CHUNK_SIZE = 100


def validate_config():
    """
    Valida as variaveis de ambiente obrigatorias antes de iniciar o backfill.

    Esta funcao existe para falhar cedo e de forma clara. Como o script usa os
    mesmos servicos do pipeline online, nao faz sentido continuar se Supabase ou
    YouTube nao estiverem configurados.

    Responsabilidade:
    - verificar presenca das credenciais minimas
    - interromper a execucao com erro explicito se faltar algo
    """
    missing = []

    if not SUPABASE_URL:
        missing.append("SUPABASE_URL")
    if not SUPABASE_KEY:
        missing.append("SUPABASE_KEY")
    if not YOUTUBE_API_KEY:
        missing.append("YOUTUBE_API_KEY")

    if missing:
        raise RuntimeError(
            "Variaveis de ambiente ausentes: " + ", ".join(missing)
        )


def fetch_paginated(endpoint, params):
    """
    Busca um endpoint REST do Supabase em modo paginado.

    Esta funcao encapsula a paginacao basica para evitar repeticao nas rotinas
    de leitura de `posts` e `post_metrics_history`. Ela usa `limit` e `offset`
    porque o backfill offline pode precisar varrer mais de uma pagina para
    levantar os candidatos legados.

    Responsabilidade:
    - executar requests GET em paginas sucessivas
    - acumular todos os registros retornados
    - abortar com erro claro em caso de falha HTTP

    Saida:
    - lista unica com todos os objetos retornados pelo endpoint
    """
    rows = []
    offset = 0

    while True:
        page_params = params.copy()
        page_params["limit"] = SUPABASE_PAGE_SIZE
        page_params["offset"] = offset

        response = requests.get(
            f"{SUPABASE_URL}/rest/v1/{endpoint}",
            headers=HEADERS,
            params=page_params,
            timeout=60,
        )

        print(f"📡 {endpoint} page status:", response.status_code, "offset:", offset)

        if response.status_code != 200:
            raise RuntimeError(
                f"Erro ao buscar {endpoint}: {response.status_code} - {response.text}"
            )

        page_rows = response.json()
        rows.extend(page_rows)

        if len(page_rows) < SUPABASE_PAGE_SIZE:
            break

        offset += SUPABASE_PAGE_SIZE

    return rows


def chunk_list(values, chunk_size):
    """
    Divide uma lista grande em blocos menores.

    O Supabase REST e a query string do endpoint ficam mais previsiveis quando
    os `post_id` sao enviados em lotes controlados. Essa funcao isola essa
    responsabilidade e permite reaproveitar o mesmo padrao para consultar
    features e historico.

    Responsabilidade:
    - receber uma lista qualquer
    - devolver sublistas menores e ordenadas pela ordem original
    """
    for start in range(0, len(values), chunk_size):
        yield values[start : start + chunk_size]


def fetch_old_posts():
    """
    Busca posts candidatos ao cleanup temporario do guardrail.

    Aqui aplicamos apenas o primeiro filtro estrutural do problema:
    `created_at < now() - 7 days`.

    Ainda nao filtramos por historico insuficiente, porque essa informacao esta
    em `post_metrics_history` e sera cruzada depois.

    Responsabilidade:
    - buscar posts com idade acima da janela de cold start
    - retornar dados minimos para desempate e rastreabilidade

    Saida esperada por item:
    - post_id
    - post_date
    - created_at
    - collected_at
    """
    cutoff = (datetime.now(UTC) - timedelta(days=LEGACY_AGE_DAYS)).isoformat()

    print("🔍 Buscando posts antigos elegiveis para legado...")
    print("📌 Corte de created_at:", cutoff)

    return fetch_paginated(
        "posts",
        {
            "select": "post_id,post_date,created_at,collected_at",
            "post_id": "not.is.null",
        },
    )


def parse_supabase_datetime(value):
    if not value:
        return None

    normalized = value.replace("Z", "+00:00")

    try:
        return datetime.fromisoformat(normalized)
    except ValueError:
        return None


def classify_video_age_bucket(row):
    """
    Classifica o post pela idade do video.

    Entrada:
    - linha de `posts` contendo `post_date` e `created_at`

    Saida:
    - `new_0_3d`
    - `recent_4_7d`
    - `warm_8_30d`
    - `old_30d_plus`
    """
    reference_date = parse_supabase_datetime(row.get("post_date"))

    if reference_date is None:
        reference_date = parse_supabase_datetime(row.get("created_at"))

    if reference_date is None:
        return "old_30d_plus"

    if reference_date.tzinfo is None:
        reference_date = reference_date.replace(tzinfo=UTC)

    age_days = (datetime.now(UTC) - reference_date).total_seconds() / 86400.0

    if age_days <= 3:
        return "new_0_3d"
    if age_days <= 7:
        return "recent_4_7d"
    if age_days <= 30:
        return "warm_8_30d"

    return "old_30d_plus"


def target_checks_for_age_bucket(age_bucket):
    """
    Define a meta temporaria de cleanup por idade do video.

    Saida:
    - `3` para `warm_8_30d` e `old_30d_plus`
    - `2` para `new_0_3d` e `recent_4_7d`
    """
    if age_bucket in {"warm_8_30d", "old_30d_plus"}:
        return 3

    return 2


def fetch_low_feature_scores(post_ids):
    """
    Busca o `priority_score_v2` apenas para posts que estao em `history_level=low`.

    O backfill de fase 1 precisa ordenar os candidatos por `priority_score_v2`,
    mas nao depende de banda. Esta funcao le a view analitica `v2` e traz so o
    necessario para a priorizacao offline.

    Responsabilidade:
    - consultar `v_post_priority_score_features_v2`
    - restringir aos `post_id` informados
    - restringir a `history_level = low`
    - devolver um mapa por `post_id`

    Saida:
    - dicionario {post_id: {priority_score_v2, history_level}}
    """
    print("🧮 Buscando priority_score_v2 para candidatos low...")

    features_by_post = {}

    for chunk in chunk_list(post_ids, SUPABASE_CHUNK_SIZE):
        ids_filter = ",".join(chunk)
        response = requests.get(
            f"{SUPABASE_URL}/rest/v1/v_post_priority_score_features_v2",
            headers=HEADERS,
            params={
                "select": "post_id,priority_score_v2,history_level",
                "post_id": f"in.({ids_filter})",
                "history_level": "eq.low",
                "limit": SUPABASE_PAGE_SIZE,
            },
            timeout=60,
        )

        print("📡 v2 features status:", response.status_code, "chunk:", len(chunk))

        if response.status_code != 200:
            raise RuntimeError(
                "Erro ao buscar v_post_priority_score_features_v2: "
                f"{response.status_code} - {response.text}"
            )

        for row in response.json():
            features_by_post[row["post_id"]] = row

    return features_by_post


def fetch_queue_scores(post_ids):
    """
    Busca a pontuacao operacional atual da fila para os candidatos de cleanup.

    A estrategia nova de limpeza do guardrail nao depende mais de
    `history_level` nem de `priority_score_v2`. Ainda assim, `priority_score`
    segue util como desempate dentro do mesmo nivel de checagem e idade.

    Responsabilidade:
    - consultar `post_update_queue`
    - restringir aos `post_id` informados
    - trazer apenas posts ainda marcados como `needs_update = true`
    - devolver um mapa por `post_id`

    Saida:
    - dicionario {post_id: {priority_score, next_check, needs_update}}
    """
    print("🧮 Buscando priority_score atual da fila...")

    queue_by_post = {}

    for chunk in chunk_list(post_ids, SUPABASE_CHUNK_SIZE):
        ids_filter = ",".join(chunk)
        response = requests.get(
            f"{SUPABASE_URL}/rest/v1/post_update_queue",
            headers=HEADERS,
            params={
                "select": "post_id,priority_score,next_check,needs_update",
                "post_id": f"in.({ids_filter})",
                "needs_update": "eq.true",
                "limit": SUPABASE_PAGE_SIZE,
            },
            timeout=60,
        )

        print("📡 post_update_queue status:", response.status_code)

        if response.status_code != 200:
            raise RuntimeError(
                "Erro ao buscar post_update_queue: "
                f"{response.status_code} - {response.text}"
            )

        for row in response.json():
            queue_by_post[row["post_id"]] = row

    return queue_by_post


def fetch_unavailable_status(post_ids):
    """
    Busca videos ja confirmados como indisponiveis para remove-los do cleanup.

    A mesma regra existe na fila online. O cleanup offline deve respeitar esse
    estado para nao gastar quota tentando coletar videos que ja foram
    confirmados como indisponiveis.

    Saida:
    - conjunto de post_ids com `status = unavailable`
    """
    print("🧮 Buscando videos indisponiveis confirmados...")

    unavailable_ids = set()

    for chunk in chunk_list(post_ids, SUPABASE_CHUNK_SIZE):
        ids_filter = ",".join(chunk)
        response = requests.get(
            f"{SUPABASE_URL}/rest/v1/post_collection_failures",
            headers=HEADERS,
            params={
                "select": "post_id,status",
                "post_id": f"in.({ids_filter})",
                "status": "eq.unavailable",
                "limit": SUPABASE_PAGE_SIZE,
            },
            timeout=60,
        )

        print("📡 post_collection_failures status:", response.status_code)

        if response.status_code != 200:
            raise RuntimeError(
                "Erro ao buscar post_collection_failures: "
                f"{response.status_code} - {response.text}"
            )

        for row in response.json():
            unavailable_ids.add(row["post_id"])

    return unavailable_ids


def fetch_history_counts(post_ids):
    """
    Conta quantas checagens cada post ja possui em `post_metrics_history`.

    Essa funcao resolve a parte que distingue um `low` de cold start de um
    `legacy_low`: o script precisa saber se o post tem `<= 1` snapshot total.
    Como nao estamos introduzindo uma view nova nesta etapa, a contagem e feita
    no proprio script a partir do endpoint REST.

    Responsabilidade:
    - consultar `post_metrics_history` em blocos de IDs
    - contar ocorrencias por `post_id`
    - devolver um dicionario simples de contagens

    Saida:
    - dicionario {post_id: total_checagens}
    """
    print("📚 Contando historico existente dos candidatos...")

    counts = {post_id: 0 for post_id in post_ids}

    for chunk in chunk_list(post_ids, SUPABASE_CHUNK_SIZE):
        ids_filter = ",".join(chunk)
        rows = fetch_paginated(
            "post_metrics_history",
            {
                "select": "post_id",
                "post_id": f"in.({ids_filter})",
            },
        )

        for row in rows:
            counts[row["post_id"]] = counts.get(row["post_id"], 0) + 1

    return counts


def fetch_legacy_low_batch_priority_first(batch_size=DEFAULT_BATCH_SIZE):
    """
    Mantem a primeira estrategia de selecao usada no backfill de `legacy_low`.

    Esta versao foi mantida como referencia historica da regra inicial. Nela,
    o lote era ordenado primeiro por `priority_score_v2 desc`.

    Ordenacao original:
    - `priority_score_v2 desc`
    - `total_checagens asc`
    - `collected_at asc nulls first`
    - `post_id`

    Esta funcao nao esta mais ativa no fluxo principal.
    A chamada ativa do lote atualmente acontece dentro de `run_backfill_batch()`
    na linha 603, usando `fetch_legacy_low_batch(...)`.
    """
    old_posts = fetch_old_posts()

    if not old_posts:
        print("?? Nenhum post antigo encontrado para backfill")
        return []

    post_ids = [row["post_id"] for row in old_posts]
    features_by_post = fetch_low_feature_scores(post_ids)
    history_counts = fetch_history_counts(post_ids)

    batch_candidates = []

    for row in old_posts:
        post_id = row["post_id"]
        total_checks = history_counts.get(post_id, 0)
        feature_row = features_by_post.get(post_id)

        if not feature_row:
            continue

        if total_checks > MAX_TOTAL_CHECKS:
            continue

        batch_candidates.append(
            {
                "post_id": post_id,
                "created_at": row.get("created_at"),
                "collected_at": row.get("collected_at"),
                "total_checagens": total_checks,
                "priority_score_v2": float(feature_row.get("priority_score_v2", 0)),
                "history_level": feature_row.get("history_level"),
            }
        )

    batch_candidates.sort(
        key=lambda item: (
            -item["priority_score_v2"],
            item["total_checagens"],
            item["collected_at"] is not None,
            item["collected_at"] or "",
            item["post_id"],
        )
    )

    selected = batch_candidates[:batch_size]

    print(f"?? Legacy low candidatos (priority first): {len(batch_candidates)}")
    print(f"? Legacy low selecionados (priority first): {len(selected)}")

    return selected


def fetch_legacy_low_batch(batch_size=DEFAULT_BATCH_SIZE):
    """
    Seleciona o lote offline ativo para limpeza temporaria do guardrail.

    Esta funcao manteve o nome historico para reduzir impacto no restante do
    script, mas a estrategia deixou de ser `legacy_low`.

    A regra de elegibilidade agora e:
    1. `warm_8_30d` e `old_30d_plus` com menos de `3` checagens
    2. `new_0_3d` e `recent_4_7d` com menos de `2` checagens
    3. `needs_update = true`
    4. nao estar confirmado como `unavailable`

    O cleanup nao usa mais `history_level` nem `priority_score_v2`. Como o
    objetivo e abrir espaco no guardrail, o lote e ordenado por prioridade de
    cleanup:
    - `warm_8_30d` e `old_30d_plus` primeiro
    - `total_checagens asc`
    - `post_date asc`
    - `priority_score desc`
    - `post_id`

    Isso faz com que:
    - posts warm e old sejam limpos ate `3` checagens
    - posts new e recent sejam limpos ate `2` checagens
    - dentro de cada grupo, os menos observados venham primeiro
    - dentro de cada camada, os videos mais velhos venham primeiro
    - `priority_score` seja apenas desempate de valor

    Responsabilidade:
    - produzir o lote final ativo do cleanup de guardrail
    - devolver a estrutura simples esperada pelas proximas etapas
    """
    old_posts = fetch_old_posts()

    if not old_posts:
        print("?? Nenhum post antigo encontrado para backfill")
        return []

    post_ids = [row["post_id"] for row in old_posts]
    queue_by_post = fetch_queue_scores(post_ids)
    unavailable_ids = fetch_unavailable_status(post_ids)
    history_counts = fetch_history_counts(post_ids)

    batch_candidates = []

    for row in old_posts:
        post_id = row["post_id"]
        total_checks = history_counts.get(post_id, 0)
        queue_row = queue_by_post.get(post_id)
        age_bucket = classify_video_age_bucket(row)
        target_checks = target_checks_for_age_bucket(age_bucket)

        if not queue_row:
            continue

        if post_id in unavailable_ids:
            continue

        if total_checks >= target_checks:
            continue

        batch_candidates.append(
            {
                "post_id": post_id,
                "post_date": row.get("post_date"),
                "created_at": row.get("created_at"),
                "collected_at": row.get("collected_at"),
                "total_checagens": total_checks,
                "target_checagens": target_checks,
                "video_age_bucket": age_bucket,
                "priority_score": float(queue_row.get("priority_score", 0)),
                "next_check": queue_row.get("next_check"),
            }
        )

    batch_candidates.sort(
        key=lambda item: (
            0 if item["video_age_bucket"] in {"old_30d_plus", "warm_8_30d"} else 1,
            item["total_checagens"],
            item["post_date"] or item["created_at"] or "",
            -item["priority_score"],
            item["post_id"],
        )
    )

    selected = batch_candidates[:batch_size]

    print(f"?? Guardrail cleanup candidatos: {len(batch_candidates)}")
    print(f"? Guardrail cleanup selecionados: {len(selected)}")

    return selected

def extract_ids(rows):
    """
    Extrai apenas os `post_id` do lote selecionado.

    Esta funcao e reaproveitada do desenho do `postMetrics/main.py` e mantida
    separada para preservar a mesma estrutura mental do pipeline online.

    Responsabilidade:
    - traduzir linhas ricas em uma lista simples de IDs
    """
    return [row["post_id"] for row in rows]


def fetch_youtube_stats(video_ids):
    """
    Busca estatisticas atuais dos videos no endpoint `videos.list`.

    A implementacao segue o mesmo contrato do pipeline online:
    - usa uma unica chamada para varios IDs
    - pede `part=statistics`
    - devolve a lista `items`

    Responsabilidade:
    - integrar com a YouTube Data API
    - devolver o payload bruto necessario para normalizacao
    """
    print("🌐 Chamando YouTube API...")

    response = requests.get(
        "https://www.googleapis.com/youtube/v3/videos",
        params={
            "part": "statistics",
            "id": ",".join(video_ids),
            "key": YOUTUBE_API_KEY,
        },
        timeout=60,
    )

    print("📡 YouTube status:", response.status_code)

    if response.status_code != 200:
        raise RuntimeError(
            f"Erro YouTube: {response.status_code} - {response.text}"
        )

    return response.json().get("items", [])


def normalize(items):
    """
    Normaliza a resposta da YouTube API para o contrato de `post_metrics_history`.

    Esta funcao preserva o mesmo formato do pipeline online. Isso e importante
    porque os triggers do banco ja conhecem esse payload e atualizam o restante
    do sistema automaticamente.

    Responsabilidade:
    - extrair `viewCount`, `likeCount` e `commentCount`
    - preencher defaults seguros quando um campo nao vier
    - marcar `collected_at` no momento da coleta
    """
    collected_at = datetime.now(UTC).isoformat()
    records = []

    for video in items:
        stats = video.get("statistics", {})
        records.append(
            {
                "post_id": video["id"],
                "views": int(stats.get("viewCount", 0)),
                "likes": int(stats.get("likeCount", 0)),
                "comments": int(stats.get("commentCount", 0)),
                "collected_at": collected_at,
            }
        )

    return records


def insert_history(records):
    """
    Insere o lote normalizado em `post_metrics_history`.

    O objetivo desta funcao e permanecer o mais proximo possivel do
    `postMetrics/main.py`. O script offline nao deve atualizar `posts` nem
    `post_update_queue` diretamente; ele so insere historico e deixa os
    triggers do banco cuidarem do restante.

    Responsabilidade:
    - fazer POST do lote para o endpoint REST
    - validar retorno HTTP
    - interromper com erro claro em caso de falha
    """
    print("📝 Inserindo histórico batch...")

    response = requests.post(
        f"{SUPABASE_URL}/rest/v1/post_metrics_history",
        headers=HEADERS,
        json=records,
        timeout=60,
    )

    print("📡 History batch:", response.status_code)

    if response.status_code >= 300:
        raise RuntimeError(
            f"Erro ao inserir histórico: {response.status_code} - {response.text}"
        )


def log_missing_posts(requested_ids, returned_items):
    """
    Registra discrepancias entre IDs enviados e itens retornados pela API.

    Em rotinas offline, e importante nao perder visibilidade sobre posts
    removidos, privados ou simplesmente nao retornados pela YouTube API.
    Essa funcao nao bloqueia a execucao; ela apenas informa a diferenca.

    Responsabilidade:
    - comparar IDs pedidos com IDs retornados
    - registrar em log os que nao voltaram
    """
    returned_ids = {item["id"] for item in returned_items}
    missing_ids = [post_id for post_id in requested_ids if post_id not in returned_ids]

    if missing_ids:
        print(f"⚠️ IDs sem retorno da YouTube API: {len(missing_ids)}")
        print("⚠️ Lista:", ",".join(missing_ids))


def run_backfill_batch(batch_size=DEFAULT_BATCH_SIZE):
    """
    Executa uma rodada completa do cleanup offline do guardrail.

    Esta funcao equivale ao `run_pipeline()` do worker online, mas a origem dos
    IDs vem da selecao de posts antigos com `total_checagens < 3`. Todo o
    restante do pipeline segue a mesma logica operacional:
    - selecionar origem
    - extrair IDs
    - buscar estatisticas
    - normalizar
    - inserir historico

    Responsabilidade:
    - orquestrar o lote de ponta a ponta
    - manter logs suficientes para observacao manual
    """
    selected_rows = fetch_legacy_low_batch(batch_size=batch_size)

    if not selected_rows:
        print("⚠️ Nada para processar no backfill legacy_low")
        return

    video_ids = extract_ids(selected_rows)
    youtube_items = fetch_youtube_stats(video_ids)

    if not youtube_items:
        print("⚠️ Sem dados do YouTube para o lote selecionado")
        return

    log_missing_posts(video_ids, youtube_items)

    records = normalize(youtube_items)
    insert_history(records)

    print(f"✅ Processados no backfill: {len(records)}")


def run():
    """
    Entry point simples para execucao manual do backfill offline.

    Mantem a mesma ideia de inicializacao do script online:
    - logar inicio
    - validar configuracao
    - executar o pipeline
    - capturar erros em um bloco unico

    Responsabilidade:
    - oferecer um ponto unico e previsivel de execucao
    """
    started_at = datetime.now(UTC)
    print("🚀 Backfill offline legacy_low iniciado")
    print("📌 Script: legacy_low_backfill_phase1.py")

    try:
        validate_config()
        run_backfill_batch()

        finished_at = datetime.now(UTC)
        print("✅ Backfill finalizado com sucesso")
        print("⏱️ Duração:", finished_at - started_at)
    except Exception as exc:
        finished_at = datetime.now(UTC)
        print("❌ ERRO:", str(exc))
        print("⏱️ Duração até erro:", finished_at - started_at)
        raise


if __name__ == "__main__":
    run()
