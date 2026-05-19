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


def render_overview() -> None:
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

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        metric_card("Data Quality", "Pendente", "Primeira view: v_dashboard_data_quality_status", "DQ")
    with col2:
        metric_card("Creators", "--", "Ranking sera conectado ao Supabase", "CR")
    with col3:
        metric_card("Videos", "--", "Crescimento semanal em preparacao", "PL")
    with col4:
        metric_card("Hot Now", "--", "Velocidade e aceleracao temporal", "UP")

    st.write("")
    left, right = st.columns([1, 2])
    with left:
        placeholder_card(
            "Proximo passo",
            "Conectar o app ao Supabase via secrets e carregar a view de qualidade dos dados antes de qualquer ranking.",
        )
    with right:
        placeholder_card(
            "Area de analise",
            "Este bloco recebera os primeiros graficos e tabelas depois da validacao das views existentes no Supabase.",
        )


def render_placeholder_page(title: str, description: str) -> None:
    st.title(title)
    placeholder_card(title, description)


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
    render_placeholder_page("Data quality", "Primeira tela real: status de confiabilidade antes dos rankings.")
else:
    render_placeholder_page("Fila operacional", "Revisao de videos indisponiveis e problemas de coleta.")
