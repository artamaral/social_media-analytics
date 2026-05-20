from html import escape
from typing import Any

import pandas as pd
import plotly.express as px
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

        .fenabrave-card-grid {
            display: grid;
            grid-template-columns: repeat(3, minmax(0, 1fr));
            gap: 1rem;
            margin-top: 0.75rem;
            margin-bottom: 1.25rem;
        }

        .fenabrave-card-grid .metric-picto {
            font-size: 1.5rem;
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


FENABRAVE_PICTOS = {
    "CAR": "🚙",
    "VAN": "🚐",
    "TRK": "🚚",
    "BUS": "🚌",
    "MOTO": "🏍️",
    "TRL": "▰",
}


def metric_card_html(title: str, value: str, caption: str, picto: str, accent_color: str | None = None) -> str:
    picto_style = f' style="color: {accent_color};"' if accent_color else ""
    return (
        '<div class="metric-card">'
        f'<div class="metric-card-header">{escape(title)}</div>'
        '<div class="metric-card-body">'
        '<div class="metric-value">'
        f"<span>{escape(value)}</span>"
        f'<span class="metric-picto"{picto_style}>{escape(picto)}</span>'
        "</div>"
        f'<div class="metric-caption">{escape(caption)}</div>'
        "</div>"
        "</div>"
    )


def metric_card(title: str, value: str, caption: str, picto: str, accent_color: str | None = None) -> None:
    st.markdown(
        metric_card_html(title, value, caption, picto, accent_color),
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
def load_single_row_view(view_name: str) -> dict[str, Any] | None:
    client = get_supabase_client()
    if client is None:
        return None

    response = (
        client.table(view_name)
        .select("*")
        .limit(1)
        .execute()
    )

    if not response.data:
        return None
    return response.data[0]


@st.cache_data(ttl=300, show_spinner=False)
def load_view_rows(view_name: str) -> list[dict[str, Any]]:
    client = get_supabase_client()
    if client is None:
        return []

    response = client.table(view_name).select("*").execute()
    return response.data or []


def get_single_row_view(view_name: str) -> tuple[dict[str, Any] | None, str | None]:
    if not is_supabase_configured():
        return None, "Supabase ainda nao configurado. Adicione SUPABASE_URL e SUPABASE_ANON_KEY nos secrets."

    try:
        return load_single_row_view(view_name), None
    except Exception as exc:
        return None, f"Falha ao consultar {view_name}: {exc}"


def get_view_rows(view_name: str) -> tuple[list[dict[str, Any]], str | None]:
    if not is_supabase_configured():
        return [], "Supabase ainda nao configurado. Adicione SUPABASE_URL e SUPABASE_ANON_KEY nos secrets."

    try:
        return load_view_rows(view_name), None
    except Exception as exc:
        return [], f"Falha ao consultar {view_name}: {exc}"


def render_connection_notice(error: str | None) -> None:
    if error:
        st.warning(error)
    else:
        st.success("Conexao com Supabase ativa usando secrets.")


def render_data_quality_cards(
    guardrail_rows: list[dict[str, Any]],
    dead_posts: dict[str, Any] | None,
    errors: list[str],
) -> None:
    if errors:
        st.warning(" | ".join(errors))

    col1, col2 = st.columns(2)

    if guardrail_rows:
        legacy_posts = sum(
            int(row.get("total_posts") or 0)
            for row in guardrail_rows
            if row.get("is_legacy_guardrail")
        )
        under_minimum = sum(int(row.get("total_posts") or 0) for row in guardrail_rows)
        legacy_ready = legacy_posts == 0
        with col1:
            status_card(
                "Legado guardrail",
                legacy_posts,
                "ok" if legacy_ready else "warning",
                "LG",
            )
            st.caption(f"{under_minimum} posts abaixo de 3 checagens.")
    else:
        with col1:
            status_card("Legado guardrail", "Erro", "danger", "LG")
            st.caption("View v_dashboard_guardrail_coverage_status indisponivel.")

    if dead_posts:
        pending_review = int(dead_posts.get("pending_human_review") or 0)
        total_dead_posts = int(dead_posts.get("total_dead_posts") or 0)
        review_ready = bool(dead_posts.get("dead_posts_review_ready"))
        with col2:
            status_card(
                "Posts mortos",
                pending_review,
                "ok" if review_ready else "warning",
                "PM",
            )
            st.caption(f"{total_dead_posts} posts mortos/candidatos monitorados.")
    else:
        with col2:
            status_card("Posts mortos", "Erro", "danger", "PM")
            st.caption("View v_dashboard_dead_post_validation_status indisponivel.")


def load_data_quality_context() -> tuple[list[dict[str, Any]], dict[str, Any] | None, list[str]]:
    guardrail_rows, guardrail_error = get_view_rows("v_dashboard_guardrail_coverage_status")
    dead_posts, dead_posts_error = get_single_row_view("v_dashboard_dead_post_validation_status")
    errors = [error for error in [guardrail_error, dead_posts_error] if error]
    return guardrail_rows, dead_posts, errors


def render_data_quality_raw_tables(
    guardrail_rows: list[dict[str, Any]],
    dead_posts: dict[str, Any] | None,
) -> None:
    if guardrail_rows:
        guardrail_rows = sorted(
            guardrail_rows,
            key=lambda row: (int(row.get("bucket_sort") or 0), int(row.get("total_checagens") or 0)),
        )
        st.write("")
        st.markdown("### Legado guardrail")
        st.dataframe(
            guardrail_rows,
            use_container_width=True,
            hide_index=True,
            column_order=["intervalo_video", "total_checagens", "total_posts"],
            column_config={
                "intervalo_video": "Intervalo do video",
                "total_checagens": "Total de checagens",
                "total_posts": "Total de posts",
            },
        )
    if dead_posts:
        st.write("")
        st.markdown("### Posts mortos e validacao humana")
        st.dataframe([dead_posts], use_container_width=True)
        return


def render_overview() -> None:
    guardrail_rows, dead_posts, errors = load_data_quality_context()
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

    render_connection_notice(errors[0] if errors else None)
    render_data_quality_cards(guardrail_rows, dead_posts, errors)

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
    guardrail_rows, dead_posts, errors = load_data_quality_context()
    st.title("Data quality")
    render_connection_notice(errors[0] if errors else None)
    render_data_quality_cards(guardrail_rows, dead_posts, errors)
    render_data_quality_raw_tables(guardrail_rows, dead_posts)


def format_int(value: Any) -> str:
    try:
        return f"{int(value):,}".replace(",", ".")
    except (TypeError, ValueError):
        return "--"


def format_month_label(period: pd.Timestamp) -> str:
    month_names = {
        1: "jan",
        2: "fev",
        3: "mar",
        4: "abr",
        5: "mai",
        6: "jun",
        7: "jul",
        8: "ago",
        9: "set",
        10: "out",
        11: "nov",
        12: "dez",
    }
    return f"{month_names[int(period.month)]}/{int(period.year)}"


def render_fenabrave_page() -> None:
    rows, error = get_view_rows("v_dashboard_fenabrave_monthly_segments")
    st.title("Fenabrave")
    render_connection_notice(error)

    if not rows:
        placeholder_card(
            "Fenabrave",
            "Aguardando a view v_dashboard_fenabrave_monthly_segments retornar dados.",
        )
        return

    df = pd.DataFrame(rows)
    df["reference_period"] = pd.to_datetime(df["reference_period"])
    df["month_display"] = df["reference_period"].apply(format_month_label)
    month_order = (
        df.sort_values("reference_period")
        .drop_duplicates("reference_period")["month_display"]
        .tolist()
    )
    latest_period = df["reference_period"].max()
    latest_df = df[df["reference_period"] == latest_period].sort_values("segment_sort")

    st.caption(f"Mes de referencia: {format_month_label(latest_period)}")

    cards = []
    for _, row in latest_df.iterrows():
        picto = FENABRAVE_PICTOS.get(str(row["picto_code"]), str(row["picto_code"]))
        cards.append(
            metric_card_html(
                str(row["segment_label"]),
                format_int(row["monthly_units"]),
                f"Acumulado ano: {format_int(row['current_year_accumulated_units'])}",
                picto,
                str(row["color_hex"]),
            )
        )

    st.markdown(
        '<div class="fenabrave-card-grid">' + "".join(cards) + "</div>",
        unsafe_allow_html=True,
    )

    st.write("")
    st.markdown("### Resultados mensais por categoria")

    fig = px.bar(
        df.sort_values(["reference_period", "segment_sort"]),
        x="month_display",
        y="monthly_units",
        color="segment_label",
        barmode="group",
        category_orders={"month_display": month_order},
        color_discrete_map={
            row["segment_label"]: row["color_hex"]
            for _, row in df.drop_duplicates("segment_label").iterrows()
        },
        labels={
            "month_display": "Mes",
            "monthly_units": "Emplacamentos",
            "segment_label": "Categoria",
        },
    )
    fig.update_layout(
        paper_bgcolor="#15171c",
        plot_bgcolor="#24272f",
        font_color="#f5f7fa",
        legend_title_text="Categoria",
        margin=dict(l=16, r=16, t=24, b=16),
    )
    fig.update_xaxes(type="category", gridcolor="#343844")
    fig.update_yaxes(gridcolor="#343844")
    st.plotly_chart(fig, use_container_width=True)


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
            "Fenabrave",
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
elif page == "Fenabrave":
    render_fenabrave_page()
else:
    render_placeholder_page("Fila operacional", "Revisao de videos indisponiveis e problemas de coleta.")
