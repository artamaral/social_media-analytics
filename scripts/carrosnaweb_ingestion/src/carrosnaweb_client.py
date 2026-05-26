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


def create_session():
    """
    Cria uma sessao HTTP persistente e faz warm-up em paginas publicas.
    """
    session = requests.Session()
    session.headers.update(HEADERS)

    print("Aquecendo sessao...")
    for path in ("/default.asp", "/avancada.asp"):
        response = session.get(f"{BASE_URL}{path}", timeout=20)
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
    response = session.get(url, timeout=timeout)
    print(f"[DEBUG] Status HTTP: {response.status_code}")
    print(f"[DEBUG] Tamanho HTML: {len(response.text)}")
    print(f"[DEBUG] URL final: {response.url}")
    time.sleep(uniform(delay_min, delay_max))
    return response

