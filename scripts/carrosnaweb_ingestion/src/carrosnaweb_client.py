import time
from random import uniform

import requests


BASE_URL = "https://www.carrosnaweb.com.br"
DEFAULT_REFERER = f"{BASE_URL}/avancada.asp"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 "
        "(Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 "
        "(KHTML, like Gecko) "
        "Chrome/124.0.0.0 "
        "Safari/537.36"
    ),
    "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8",
    "Accept": (
        "text/html,"
        "application/xhtml+xml,"
        "application/xml;q=0.9,"
        "image/webp,*/*;q=0.8"
    ),
    "Referer": DEFAULT_REFERER,
    "Connection": "keep-alive",
}


def request_with_retry(session, url, timeout, max_attempts=4, base_sleep=2.0):
    """
    Executa GET com retry para falhas transitórias de conexao.
    """
    last_error = None

    for attempt in range(1, max_attempts + 1):
        try:
            return session.get(url, timeout=timeout)
        except requests.exceptions.RequestException as exc:
            last_error = exc
            print(
                f"[HTTP RETRY] tentativa {attempt}/{max_attempts} falhou para {url}: {exc}"
            )
            if attempt >= max_attempts:
                break

            sleep_seconds = base_sleep * attempt + uniform(0.5, 1.5)
            print(f"[HTTP RETRY] aguardando {sleep_seconds:.1f}s antes de tentar novamente.")
            time.sleep(sleep_seconds)

    raise last_error


def create_session():
    """
    Cria uma sessao HTTP persistente e faz warm-up em paginas publicas.
    """
    session = requests.Session()
    session.headers.update(HEADERS)

    print("Aquecendo sessao...")
    for path in ("/default.asp", "/avancada.asp"):
        response = request_with_retry(
            session,
            f"{BASE_URL}{path}",
            timeout=20,
            max_attempts=4,
            base_sleep=2.0,
        )
        print(
            f"[SESSION] warm-up {path} "
            f"status={response.status_code} size={len(response.text)}"
        )
        time.sleep(uniform(1.0, 2.0))

    print("Sessao pronta.")
    return session


def safe_get(session, url, timeout=30, delay_min=1.5, delay_max=3.0):
    """
    Executa GET com logging simples e delay apos a chamada.
    """
    print(f"[DEBUG] URL acessada: {url}")
    response = request_with_retry(
        session,
        url,
        timeout=timeout,
        max_attempts=4,
        base_sleep=2.0,
    )
    print(f"[DEBUG] Status HTTP: {response.status_code}")
    print(f"[DEBUG] Tamanho HTML: {len(response.text)}")
    print(f"[DEBUG] URL final: {response.url}")
    time.sleep(uniform(delay_min, delay_max))
    return response

