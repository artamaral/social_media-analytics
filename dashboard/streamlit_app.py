from typing import Any

import streamlit as st


st.set_page_config(
    page_title="Social Media Analytics",
    page_icon="SM",
    layout="wide",
    initial_sidebar_state="expanded",
)


def inject_theme() -> None:
    st.markdown(
        """
        <style>
        :root {
            --bg: #15171c;
            --surface: #24272f;
            --sidebar: #20212b;
            --card: #f4f6f7;
            --card-dark: #2a2c36;
            --text: #f5f7fa;
            --muted: #aeb4bf;
            --text-dark: #252733;
            --accent: #ff8069;
            --positive: #98df96;
            --warning: #f2c14e;
            --danger: #ff6f61;
        }

        .stApp {
            background: var(--bg);
            color: var(--text);
        }

        section[data-testid="stSidebar"] {
            background: var(--sidebar);
        }

        section[data-testid="stSidebar"] * {
            color: var(--text);
        }

        .block-container {
            padding-top: 1.5rem;
            padding-bottom: 2rem;
            max-width: 1380px;
        }

        h1, h2, h3 {
            color: var(--text);
            letter-spacing: 0;
        }

        .dashboard-title {
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 1rem;
            margin-bottom: 1rem;
        }

        .dashboard-title small {
            color: var(--muted);
            font-size: 0.9rem;
        }

        .metric-card {
            background: var(--card);
            color: var(--text-dark);
            border-radius: 8px;
            min-height: 132px;
            overflow: hidden;
            border: 1px solid rgba(255, 255, 255, 0.06);
        }

        .metric-card-header {
            background: #252733;
            color: var(--text);
            padding: 0.7rem 0.85rem;
            font-weight: 700;
            text-transform: uppercase;
            font-size: 0.8rem;
            letter-spacing: 0;
        }

        .metric-card-body {
            padding: 1rem 1.05rem;
        }

        .metric-value {
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 1rem;
            font-size: 1.9rem;
            font-weight: 800;
            line-height: 1.15;
        }

        .metric-picto {
            width: 48px;
            height: 48px;
            border-radius: 50%;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            background: #252733;
            color: var(--accent);
            font-size: 1rem;
            font-weight: 900;
            flex: 0 0 auto;
        }

        .metric-caption {
            margin-top: 0.75rem;
            color: #606774;
            font-size: 0.78rem;
            text-transform: uppercase;
            font-weight: 700;
        }

        .section-card {
            background: var(--card-dark);
            color: var(--text);
            border-radius: 8px;
            border: 1px solid rgba(255, 255, 255, 0.06);
            padding: 1rem;
            min-height: 220px;
        }

        .section-card h3 {
            margin-top: 0;
            color: var(--text);
        }

        .section-card p {
            color: var(--muted);
        }

        .status-pill {
            display: inline-flex;
            align-items: center;
            gap: 0.45rem;
            color: var(--text-dark);
            background: var(--warning);
            border-radius: 999px;
            padding: 0.35rem 0.7rem;
            font-size: 0.8rem;
            font-weight: 800;
            text-transform: uppercase;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def metric_card(title: str, value: str, caption: str, picto: str) -> None:
    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-card-header">{title}</div>
            <div class="metric-card-body">
                <div class="metric-value">
                    <span>{value}</span>
                    <span class="metric-picto">{picto}</span>
                </div>
                <div class="metric-caption">{caption}</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def status_card(title: str, value: Any, status: str, picto: str) -> None:
    status_color = {
        "ok": "#98df96",
        "warning": "#f2c14e",
        "danger": "#ff6f61",
        "neutral": "#aeb4bf",
    }.get(status, "#aeb4bf")
    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-card-header">{title}</div>
            <div class="metric-card-body">
                <div class="metric-value">
                    <span>{value}</span>
                    <span class="metric-picto" style="color: {status_color};">{picto}</span>
                </div>
                <div class="metric-caption">Status de confiabilidade</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def placeholder_card(title: str, body: str) -> None:
    st.markdown(
        f"""
        <div class="section-card">
            <h3>{title}</h3>
            <p>{body}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def get_secret(name: str) -> str | None:
    value = st.secrets.get(name)
    if value is None:
        return None
    return str(value).strip() or None


def is_supabase_configured() -> bool:
    return bool(get_secret("SUPABASE_URL") and get_secret("SUPABASE_ANON_KEY"))


@st.cache_resource(show_spinner=False)
def get_supabase_client():
    from supabase import create_client

    supabase_url = get_secret("SUPABASE_URL")
    supabase_anon_key = get_secret("SUPABASE_ANON_KEY")
    if not supabase_url or not supabase_anon_key:
        return None
    return create_client(supabase_url, supabase_anon_key)


@st.cache_data(ttl=300, show_spinner=False)
def load_data_quality_status() -> dict[str, Any] | None:
    client = get_supabase_client()
    if client is None:
        return None

    response = (
        client.table("v_dashboard_data_quality_status")
        .select("*")
        .limit(1)
        .execute()
    )

    if not response.data:
        return None
    return response.data[0]


def get_data_quality_status() -> tuple[dict[str, Any] | None, str | None]:
    if not is_supabase_configured():
        return None, "Supabase ainda nao configurado. Adicione SUPABASE_URL e SUPABASE_ANON_KEY nos secrets."

    try:
        return load_data_quality_status(), None
    except Exception as exc:
        return None, f"Falha ao consultar Supabase: {exc}"


def render_connection_notice(error: str | None) -> None:
    if error:
        st.warning(error)
    else:
        st.success("Conexao com Supabase ativa usando secrets.")


def render_data_quality_cards(data_quality: dict[str, Any] | None) -> None:
    if not data_quality:
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            metric_card("Data Quality", "Pendente", "Configure secrets para consultar Supabase", "DQ")
        with col2:
            metric_card("Sem historico", "--", "Aguardando v_dashboard_data_quality_status", "HS")
        with col3:
            metric_card("Coleta nula", "--", "Aguardando v_dashboard_data_quality_status", "CL")
        with col4:
            metric_card("Stale 24h", "--", "Aguardando v_dashboard_data_quality_status", "24")
        return

    is_ready = bool(data_quality.get("is_analytics_ready"))
    readiness = "OK" if is_ready else "Atencao"
    readiness_status = "ok" if is_ready else "warning"

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        status_card("Analytics Ready", readiness, readiness_status, "DQ")
    with col2:
        status_card(
            "Sem historico",
            data_quality.get("posts_without_history", 0),
            "ok" if data_quality.get("posts_without_history", 0) == 0 else "danger",
            "HS",
        )
    with col3:
        status_card(
            "Coleta nula",
            data_quality.get("posts_with_null_collected_at", 0),
            "ok" if data_quality.get("posts_with_null_collected_at", 0) == 0 else "danger",
            "CL",
        )
    with col4:
        status_card(
            "Stale 24h",
            data_quality.get("posts_stale_24h", 0),
            "ok" if data_quality.get("posts_stale_24h", 0) == 0 else "warning",
            "24",
        )


def render_overview() -> None:
    data_quality, error = get_data_quality_status()
    st.markdown(
        """
        <div class="dashboard-title">
            <div>
                <h1>Social Media Analytics</h1>
                <small>Dashboard interno para estudos de mercado automotivo</small>
            </div>
            <span class="status-pill">Setup inicial</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    render_connection_notice(error)
    render_data_quality_cards(data_quality)

    st.write("")
    left, right = st.columns([1, 2])
    with left:
        placeholder_card(
            "Proximo passo",
            "Validar grants/RLS das views e depois liberar ranking de creators e crescimento semanal.",
        )
    with right:
        placeholder_card(
            "Area de analise",
            "Este bloco recebera graficos e tabelas depois da validacao das views existentes no Supabase.",
        )


def render_placeholder_page(title: str, description: str) -> None:
    st.title(title)
    placeholder_card(title, description)


def render_data_quality_page() -> None:
    data_quality, error = get_data_quality_status()
    st.title("Data quality")
    render_connection_notice(error)
    render_data_quality_cards(data_quality)

    if data_quality:
        st.write("")
        st.markdown("### Registro bruto da view")
        st.dataframe([data_quality], use_container_width=True)


inject_theme()

with st.sidebar:
    st.markdown("## SM Analytics")
    st.caption("Automotivo Americas")
    page = st.radio(
        "Navegacao",
        [
            "Overview",
            "Creators",
            "Videos em crescimento",
            "Hot now",
            "Data quality",
            "Fila operacional",
        ],
    )

if page == "Overview":
    render_overview()
elif page == "Creators":
    render_placeholder_page("Creators", "Ranking por views, engajamento e frequencia sera conectado na proxima etapa.")
elif page == "Videos em crescimento":
    render_placeholder_page("Videos em crescimento", "Ranking semanal de crescimento usando v_dashboard_post_growth_7d.")
elif page == "Hot now":
    render_placeholder_page("Hot now", "View futura para velocidade recente, velocidade anterior e aceleracao.")
elif page == "Data quality":
    render_data_quality_page()
else:
    render_placeholder_page("Fila operacional", "Revisao de videos indisponiveis e problemas de coleta.")
