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

        section[data-testid="stSidebar"] [data-testid="stButton"] button {
            width: 100%;
            border-radius: 8px;
            border: 1px solid transparent;
            background: transparent;
            color: var(--text);
            text-align: left;
            padding: 0.6rem 0.8rem;
            font-size: 0.92rem;
            font-weight: 700;
            line-height: 1.2;
            justify-content: flex-start;
        }

        section[data-testid="stSidebar"] [data-testid="stButton"] button:hover {
            background: rgba(255, 255, 255, 0.05);
            border-color: rgba(255, 255, 255, 0.08);
        }

        section[data-testid="stSidebar"] [data-testid="stButton"] button > div {
            justify-content: flex-start;
        }

        section[data-testid="stSidebar"] [data-testid="stButton"] button[kind="primary"] {
            background: var(--accent);
            border-color: var(--accent);
            color: #15171c;
        }

        section[data-testid="stSidebar"] [data-testid="stButton"] button[kind="primary"]:hover {
            background: #ff907d;
            border-color: #ff907d;
        }

        .sidebar-nav-block {
            margin-top: 0.35rem;
            margin-bottom: 0.35rem;
        }

        .sidebar-nav-section {
            color: var(--muted);
            font-size: 0.74rem;
            font-weight: 800;
            text-transform: uppercase;
            letter-spacing: 0;
            margin: 0.75rem 0 0.35rem;
            padding: 0 0.2rem;
        }

        .sidebar-nav-spacer {
            height: 0.25rem;
        }

        .sidebar-nav-child {
            padding-left: 0.9rem;
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

        .page-subtitle {
            color: var(--muted);
            font-size: 1.15rem;
            font-weight: 700;
            margin-top: -0.35rem;
            margin-bottom: 1rem;
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

        .fenabrave-card-grid .metric-caption {
            font-size: 1.17rem;
            line-height: 1.2;
            overflow-wrap: anywhere;
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

        .dq-kpi-grid {
            display: grid;
            grid-template-columns: repeat(2, minmax(0, 1fr));
            gap: 1rem;
            margin-top: 1rem;
        }

        .dq-kpi-card {
            background: var(--card-dark);
            color: var(--text);
            border-radius: 8px;
            border: 1px solid rgba(255, 255, 255, 0.06);
            border-top: 4px solid var(--accent);
            padding: 1rem 1.05rem 1.05rem;
            min-height: 250px;
            overflow: hidden;
        }

        .dq-kpi-title {
            font-size: 1.425rem;
            font-weight: 900;
            text-transform: uppercase;
            letter-spacing: 0;
            line-height: 1.1;
            white-space: normal;
            overflow-wrap: anywhere;
            min-height: 3.15rem;
        }

        .dq-kpi-value {
            font-size: 2.35rem;
            line-height: 1.05;
            font-weight: 900;
            margin-top: 0.35rem;
        }

        .dq-kpi-subtitle {
            margin-top: 0.45rem;
            color: var(--muted);
            font-size: 0.95rem;
            font-weight: 700;
            line-height: 1.2;
            overflow-wrap: anywhere;
        }

        .dq-chip-row {
            display: flex;
            flex-wrap: wrap;
            gap: 0.45rem;
            margin-top: 0.9rem;
        }

        .dq-chip {
            display: inline-flex;
            align-items: center;
            gap: 0.4rem;
            padding: 0.35rem 0.65rem;
            border-radius: 999px;
            background: #252733;
            color: var(--text);
            font-size: 0.78rem;
            font-weight: 700;
            line-height: 1;
            white-space: nowrap;
        }

        .dq-chip.alert-red {
            background: #7a2323;
        }

        .dq-chip.alert-yellow {
            background: #8b6b10;
            color: #fff7d6;
        }

        .dq-chip.ok-green {
            background: #214d37;
        }

        .dq-chip.neutral {
            background: #252733;
        }

        .dq-chip strong {
            display: inline-flex;
            align-items: center;
            font-size: inherit;
            line-height: 1;
            color: var(--text);
        }

        .dq-detail {
            margin-top: 1rem;
        }

        .worker-grid {
            display: grid;
            grid-template-columns: repeat(3, minmax(0, 1fr));
            gap: 1rem;
            margin-top: 1rem;
        }

        .worker-panel {
            background: var(--card-dark);
            color: var(--text);
            border-radius: 8px;
            border: 1px solid rgba(255, 255, 255, 0.06);
            border-top: 4px solid var(--accent);
            padding: 1rem 1.05rem 1.05rem;
            min-height: 240px;
        }

        .worker-panel-title {
            font-size: 1.25rem;
            font-weight: 900;
            line-height: 1.1;
            text-transform: uppercase;
        }

        .worker-panel-subtitle {
            margin-top: 0.35rem;
            color: var(--muted);
            font-size: 0.92rem;
            font-weight: 700;
        }

        .worker-stat {
            margin-top: 0.9rem;
            padding-top: 0.75rem;
            border-top: 1px solid rgba(255, 255, 255, 0.08);
        }

        .worker-stat-label {
            color: var(--muted);
            font-size: 0.78rem;
            font-weight: 700;
            text-transform: uppercase;
        }

        .worker-stat-value {
            margin-top: 0.2rem;
            font-size: 1.5rem;
            font-weight: 900;
            line-height: 1.1;
        }

        .worker-stat-caption {
            margin-top: 0.25rem;
            color: var(--muted);
            font-size: 0.85rem;
        }

        .process-banner {
            background: linear-gradient(135deg, #252733 0%, #1e2027 100%);
            border: 1px solid rgba(255, 255, 255, 0.08);
            border-left: 4px solid var(--accent);
            border-radius: 8px;
            padding: 1rem 1.05rem;
            margin-bottom: 1rem;
        }

        .process-banner-title {
            color: var(--text);
            font-size: 1rem;
            font-weight: 900;
            text-transform: uppercase;
        }

        .process-banner-copy {
            color: var(--muted);
            font-size: 0.92rem;
            margin-top: 0.35rem;
        }

        .process-step-grid {
            display: grid;
            grid-template-columns: repeat(4, minmax(0, 1fr));
            gap: 1rem;
            margin-top: 1rem;
            margin-bottom: 1rem;
        }

        .process-step-card {
            background: var(--card-dark);
            border: 1px solid rgba(255, 255, 255, 0.06);
            border-top: 4px solid var(--accent);
            border-radius: 8px;
            padding: 0.95rem 1rem;
            min-height: 170px;
        }

        .process-step-kicker {
            color: var(--muted);
            font-size: 0.76rem;
            font-weight: 800;
            text-transform: uppercase;
        }

        .process-step-title {
            color: var(--text);
            font-size: 1.05rem;
            font-weight: 900;
            line-height: 1.15;
            margin-top: 0.35rem;
        }

        .process-step-copy {
            color: var(--muted);
            font-size: 0.88rem;
            line-height: 1.35;
            margin-top: 0.55rem;
        }

        .process-step-card .dq-chip-row {
            margin-top: 0.8rem;
        }

        .review-grid {
            display: grid;
            grid-template-columns: repeat(2, minmax(0, 1fr));
            gap: 1rem;
            margin-top: 1rem;
        }

        .review-card {
            background: var(--card-dark);
            border: 1px solid rgba(255, 255, 255, 0.06);
            border-radius: 8px;
            padding: 1rem 1.05rem;
        }

        .review-card-title {
            color: var(--text);
            font-size: 1.1rem;
            font-weight: 900;
            line-height: 1.15;
        }

        .review-card-subtitle {
            color: var(--muted);
            font-size: 0.88rem;
            margin-top: 0.35rem;
            line-height: 1.35;
        }

        .review-card-grid {
            display: grid;
            grid-template-columns: repeat(2, minmax(0, 1fr));
            gap: 0.75rem;
            margin-top: 0.9rem;
        }

        .review-field {
            background: rgba(255, 255, 255, 0.03);
            border: 1px solid rgba(255, 255, 255, 0.06);
            border-radius: 8px;
            padding: 0.7rem 0.75rem;
            min-height: 68px;
        }

        .review-field-label {
            color: var(--muted);
            font-size: 0.72rem;
            font-weight: 800;
            text-transform: uppercase;
        }

        .review-field-value {
            color: var(--text);
            font-size: 0.92rem;
            font-weight: 700;
            margin-top: 0.25rem;
            overflow-wrap: anywhere;
        }

        .review-card .dq-chip-row {
            margin-top: 0.9rem;
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


def page_header(title: str, subtitle: str | None = None, badge: str | None = None) -> None:
    badge_html = f'<span class="status-pill">{escape(badge)}</span>' if badge else ""
    subtitle_html = f"<small>{escape(subtitle)}</small>" if subtitle else ""
    st.markdown(
        (
            '<div class="dashboard-title">'
            f"<div><h1>{escape(title)}</h1>{subtitle_html}</div>"
            f"{badge_html}"
            "</div>"
        ),
        unsafe_allow_html=True,
    )


def page_subtitle(text: str) -> None:
    st.markdown(f'<div class="page-subtitle">{escape(text)}</div>', unsafe_allow_html=True)


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


def metric_card_grid(cards: list[str], class_name: str = "fenabrave-card-grid") -> None:
    st.markdown(
        f'<div class="{escape(class_name)}">' + "".join(cards) + "</div>",
        unsafe_allow_html=True,
    )


def dq_kpi_card(title: str, value: str, subtitle: str, accent_color: str, chips: list[str]) -> str:
    chip_html = "".join(chips)
    return (
        f'<div class="dq-kpi-card" style="border-top-color: {escape(accent_color)};">'
        f'<div class="dq-kpi-title">{escape(title)}</div>'
        f'<div class="dq-kpi-value">{escape(value)}</div>'
        f'<div class="dq-kpi-subtitle">{escape(subtitle)}</div>'
        f'<div class="dq-chip-row">{chip_html}</div>'
        "</div>"
    )


def dq_chip(label: str, amount: str, tone: str = "neutral") -> str:
    return f'<span class="dq-chip {escape(tone)}">{escape(label)} <strong>{escape(amount)}</strong></span>'


def review_state_chip(review_ready: bool | None, pending_review: int, confirmed: int, candidates: int) -> str:
    if review_ready and pending_review == 0:
        return dq_chip("Estado", "Dados OK", "ok-green")
    if pending_review > 0:
        return dq_chip("Estado", "Necessita validação", "alert-yellow")
    if confirmed > 0 and candidates == 0:
        return dq_chip("Estado", "Confirmado", "alert-yellow")
    return dq_chip("Estado", "Estado indefinido", "alert-yellow")


def status_card(title: str, value: Any, status: str, picto: str) -> None:
    status_color = {
        "ok": "#98df96",
        "warning": "#f2c14e",
        "danger": "#ff6f61",
        "neutral": "#aeb4bf",
    }.get(status, "#aeb4bf")
    metric_card(title, str(value), "Status de confiabilidade", picto, status_color)


def section_card_html(title: str, body: str) -> str:
    return (
        '<div class="section-card">'
        f"<h3>{escape(title)}</h3>"
        f"<p>{escape(body)}</p>"
        "</div>"
    )


def placeholder_card(title: str, body: str) -> None:
    st.markdown(
        section_card_html(title, body),
        unsafe_allow_html=True,
    )


def worker_stat_html(label: str, value: str, caption: str, tone: str | None = "neutral") -> str:
    chip_class = {
        "ok": "ok-green",
        "atencao": "alert-yellow",
        "warning": "alert-yellow",
        "nok": "alert-red",
        "danger": "alert-red",
        "neutral": "neutral",
    }.get(tone, "neutral")
    caption_html = f'<div class="worker-stat-caption">{escape(caption)}</div>' if caption else ""
    chip_html = (
        f'<div class="dq-chip-row"><span class="dq-chip {escape(chip_class)}">{escape(tone)}</span></div>'
        if tone
        else ""
    )
    return (
        '<div class="worker-stat">'
        f'<div class="worker-stat-label">{escape(label)}</div>'
        f'<div class="worker-stat-value">{escape(value)}</div>'
        f"{caption_html}"
        f"{chip_html}"
        "</div>"
    )


def worker_panel_html(title: str, subtitle: str, stats: list[str], accent_color: str, status_code: str) -> str:
    status_tone = normalize_worker_tone(status_code)
    return (
        f'<div class="worker-panel" style="border-top-color: {escape(accent_color)};">'
        f'<div class="worker-panel-title">{escape(title)}</div>'
        f'<div class="worker-panel-subtitle">{escape(subtitle)}</div>'
        f'<div class="dq-chip-row"><span class="dq-chip {escape(status_tone)}">Status <strong>{escape(status_code)}</strong></span></div>'
        f'{"".join(stats)}'
        "</div>"
    )


def worker_panel_grid(panels: list[str]) -> None:
    st.markdown(
        '<div class="worker-grid">' + "".join(panels) + "</div>",
        unsafe_allow_html=True,
    )


def normalize_worker_tone(status_code: str) -> str:
    return {
        "ok": "ok-green",
        "atencao": "alert-yellow",
        "warning": "alert-yellow",
        "nok": "alert-red",
        "danger": "alert-red",
    }.get(status_code, "neutral")


def process_banner(title: str, body: str) -> None:
    st.markdown(
        (
            '<div class="process-banner">'
            f'<div class="process-banner-title">{escape(title)}</div>'
            f'<div class="process-banner-copy">{escape(body)}</div>'
            "</div>"
        ),
        unsafe_allow_html=True,
    )


def process_step_card(step: str, title: str, body: str, tone: str, chip_text: str) -> str:
    chip = dq_chip("Status", chip_text, tone)
    return (
        '<div class="process-step-card">'
        f'<div class="process-step-kicker">{escape(step)}</div>'
        f'<div class="process-step-title">{escape(title)}</div>'
        f'<div class="process-step-copy">{escape(body)}</div>'
        f'<div class="dq-chip-row">{chip}</div>'
        "</div>"
    )


def process_step_grid(cards: list[str]) -> None:
    st.markdown(
        '<div class="process-step-grid">' + "".join(cards) + "</div>",
        unsafe_allow_html=True,
    )


def review_field_html(label: str, value: Any) -> str:
    display_value = "--" if value in (None, "") else str(value)
    return (
        '<div class="review-field">'
        f'<div class="review-field-label">{escape(label)}</div>'
        f'<div class="review-field-value">{escape(display_value)}</div>'
        "</div>"
    )


def review_card_html(row: dict[str, Any]) -> str:
    review_tone = "ok-green" if row.get("review_result") == "READY_TO_INSERT" else "alert-yellow"
    status_tone = "ok-green" if row.get("status") == "published" else "alert-yellow"
    entity_name = row.get("existing_entity_name") or "Entidade nova"
    entity_id = row.get("existing_entity_id") or "Pendente"
    return (
        '<div class="review-card">'
        f'<div class="review-card-title">{escape(str(row.get("raw_name") or "--"))}</div>'
        f'<div class="review-card-subtitle">{escape(str(row.get("sub_niche_name") or "--"))}</div>'
        '<div class="review-card-grid">'
        f'{review_field_html("Status", row.get("status"))}'
        f'{review_field_html("Resultado da revisao", row.get("review_result"))}'
        f'{review_field_html("Entidade existente", entity_name)}'
        f'{review_field_html("Id da entidade", entity_id)}'
        f'{review_field_html("Subnicho correspondente", row.get("matched_sub_niche_name"))}'
        f'{review_field_html("Id do subnicho", row.get("sub_niche_id"))}'
        '</div>'
        f'<div class="dq-chip-row">{dq_chip("Review", str(row.get("review_result") or "--"), review_tone)}{dq_chip("Fluxo", str(row.get("status") or "--"), status_tone)}</div>'
        f'<div class="review-card-subtitle" style="margin-top:0.85rem;">{escape(str(row.get("notes") or "--"))}</div>'
        "</div>"
    )


def review_card_grid(rows: list[dict[str, Any]]) -> None:
    st.markdown(
        '<div class="review-grid">' + "".join(review_card_html(row) for row in rows) + "</div>",
        unsafe_allow_html=True,
    )


def apply_plotly_theme(fig: Any, legend_title: str = "Categoria") -> Any:
    fig.update_layout(
        paper_bgcolor="#15171c",
        plot_bgcolor="#24272f",
        font_color="#f5f7fa",
        legend_title_text=legend_title,
        margin=dict(l=16, r=16, t=24, b=16),
    )
    fig.update_xaxes(type="category", gridcolor="#343844")
    fig.update_yaxes(gridcolor="#343844")
    return fig


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
        total_guardrail_posts = sum(int(row.get("total_posts") or 0) for row in guardrail_rows)
        legacy_posts = sum(
            int(row.get("total_posts") or 0)
            for row in guardrail_rows
            if row.get("is_legacy_guardrail")
        )
        chips = [
            dq_chip("Novos", str(sum(int(row.get("total_posts") or 0) for row in guardrail_rows if row.get("video_age_bucket") == "new_0_3d"))),
            dq_chip("Recentes", str(sum(int(row.get("total_posts") or 0) for row in guardrail_rows if row.get("video_age_bucket") == "recent_4_7d"))),
            dq_chip("Em aquecimento", str(sum(int(row.get("total_posts") or 0) for row in guardrail_rows if row.get("video_age_bucket") == "warm_8_30d"))),
            dq_chip("Sem checagem", str(sum(int(row.get("total_posts") or 0) for row in guardrail_rows if row.get("video_age_bucket") == "old_30d_plus")), "alert-red" if legacy_posts > 0 else "neutral"),
        ]
        with col1:
            st.markdown(
                dq_kpi_card(
                    "Monitoramento de posts sem checagem",
                    format_int(total_guardrail_posts),
                    "Posts com menos de 3 checagens",
                    "#f2c14e",
                    chips,
                ),
                unsafe_allow_html=True,
            )
            st.caption(f"Posts sem checagem suficiente na faixa de risco: {format_int(legacy_posts)}.")
    else:
        with col1:
            st.markdown(
                dq_kpi_card(
                    "Monitoramento de posts sem checagem",
                    "Erro",
                    "View v_dashboard_guardrail_coverage_status indisponivel.",
                    "#f2c14e",
                    [
                        dq_chip("Novos", "--"),
                        dq_chip("Recentes", "--"),
                        dq_chip("Em aquecimento", "--"),
                        dq_chip("Sem checagem", "--", "alert-red"),
                    ],
                ),
                unsafe_allow_html=True,
            )

    if dead_posts:
        total_dead_posts = int(dead_posts.get("total_dead_posts") or 0)
        pending_review = int(dead_posts.get("pending_human_review") or 0)
        confirmed = int(dead_posts.get("confirmed_unavailable") or 0)
        candidates = int(dead_posts.get("unavailable_candidates") or 0)
        review_ready = bool(dead_posts.get("dead_posts_review_ready"))
        chips = [
            dq_chip("Pendente de revisão", str(pending_review), "alert-yellow" if pending_review > 0 else "neutral"),
            dq_chip("Confirmados", str(confirmed), "neutral"),
            dq_chip("Candidatos", str(candidates), "neutral"),
            review_state_chip(review_ready, pending_review, confirmed, candidates),
        ]
        with col2:
            st.markdown(
                dq_kpi_card(
                    "Posts mortos e validação humana",
                    f"{format_int(confirmed)}/{format_int(total_dead_posts)}",
                    "Confirmados / monitorados",
                    "#ff8069",
                    chips,
                ),
                unsafe_allow_html=True,
            )
            st.caption(f"Pendentes de revisão humana: {format_int(pending_review)}.")
    else:
        with col2:
            st.markdown(
                dq_kpi_card(
                    "Posts mortos e validação humana",
                    "Erro",
                    "View v_dashboard_dead_post_validation_status indisponivel.",
                    "#ff8069",
                    [
                        dq_chip("Pendente de revisão", "--", "alert-yellow"),
                        dq_chip("Confirmados", "--"),
                        dq_chip("Candidatos", "--"),
                        dq_chip("Estado", "--"),
                    ],
                ),
                unsafe_allow_html=True,
            )


def load_data_quality_context() -> tuple[list[dict[str, Any]], dict[str, Any] | None, list[str]]:
    guardrail_rows, guardrail_error = get_view_rows("v_dashboard_guardrail_coverage_status")
    dead_posts, dead_posts_error = get_single_row_view("v_dashboard_dead_post_validation_status")
    errors = [error for error in [guardrail_error, dead_posts_error] if error]
    return guardrail_rows, dead_posts, errors


def render_data_quality_raw_tables(
    guardrail_rows: list[dict[str, Any]],
    dead_posts: dict[str, Any] | None,
) -> None:
    with st.expander("Detalhamento tecnico", expanded=False):
        if guardrail_rows:
            guardrail_rows = sorted(
                guardrail_rows,
                key=lambda row: (int(row.get("bucket_sort") or 0), int(row.get("total_checagens") or 0)),
            )
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


def render_overview() -> None:
    guardrail_rows, dead_posts, errors = load_data_quality_context()
    page_header(
        "Social Media Analytics",
        "Dashboard interno para estudos de mercado automotivo",
        "Setup inicial",
    )

    render_connection_notice(errors[0] if errors else None)
    render_data_quality_cards(guardrail_rows, dead_posts, errors)

    st.write("")
    left, right = st.columns([1, 2])
    with left:
        placeholder_card(
            "Proximo passo",
            "Validar grants/RLS das views e depois liberar ranking de criadores e crescimento semanal.",
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
    page_header("Data quality", "Confiabilidade operacional antes das análises")
    render_connection_notice(errors[0] if errors else None)
    render_data_quality_cards(guardrail_rows, dead_posts, errors)
    render_collection_integrity_section()
    render_data_quality_raw_tables(guardrail_rows, dead_posts)


def format_int(value: Any) -> str:
    try:
        return f"{int(value):,}".replace(",", ".")
    except (TypeError, ValueError):
        return "--"


def format_timestamp_br(value: Any) -> str:
    if value in (None, ""):
        return "--"
    if isinstance(value, str):
        try:
            value = pd.to_datetime(value, errors="coerce")
        except Exception:
            return str(value)
    if pd.isna(value):
        return "--"
    return pd.Timestamp(value).strftime("%d/%m/%Y %H:%M")


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
    page_header("Fenabrave")
    page_subtitle("Emplacamento Automóveis (vendas diretas e venda varejo)")
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
    period_options = df.sort_values("reference_period")["reference_period"].drop_duplicates().tolist()
    selected_period = st.selectbox(
        "Mês dos blocos",
        period_options,
        index=len(period_options) - 1,
        format_func=format_month_label,
    )
    selected_df = df[df["reference_period"] == selected_period].sort_values("segment_sort")
    latest_accumulated_by_segment = latest_df.set_index("segment_code")[
        "current_year_accumulated_units"
    ].to_dict()

    st.caption(f"Mês de referência: {format_month_label(latest_period)}")

    cards = []
    for _, row in selected_df.iterrows():
        picto = FENABRAVE_PICTOS.get(str(row["picto_code"]), str(row["picto_code"]))
        accumulated_units = latest_accumulated_by_segment.get(
            row["segment_code"],
            row["current_year_accumulated_units"],
        )
        cards.append(
            metric_card_html(
                str(row["segment_label"]),
                format_int(row["monthly_units"]),
                f"Acumulado ano: {format_int(accumulated_units)}",
                picto,
                str(row["color_hex"]),
            )
        )

    metric_card_grid(cards)

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
    apply_plotly_theme(fig)
    st.plotly_chart(fig, use_container_width=True)


def render_collection_integrity_section() -> None:
    worker_status, error = get_single_row_view("v_dashboard_worker_health_status")
    discovery_status, discovery_error = get_single_row_view("v_dashboard_new_post_discovery_status")
    operational_signals, operational_signals_error = get_single_row_view("v_dashboard_post_update_operational_signals")
    st.write("")
    st.markdown("### Integridade da coleta")

    if error:
        st.warning(error)
    if discovery_error:
        st.warning(discovery_error)
    if operational_signals_error:
        st.warning(operational_signals_error)

    if worker_status:
        raw_status_code = str(worker_status.get("status_code") or "atencao").lower()
        snapshot_value = str(
            worker_status.get("ultima_evidencia_de_execucao_br")
            or format_timestamp_br(worker_status.get("ultima_evidencia_de_execucao"))
        )
        updated_posts = format_int(worker_status.get("posts_atualizados_24h"))
        delay_minutes = f"{format_int(worker_status.get('idade_da_ultima_evidencia_minutos'))} min"
        queue_ready = format_int(worker_status.get("fila_itens_prontos"))
        queue_delayed = format_int(worker_status.get("fila_itens_atrasados"))
        recent_failures = format_int(worker_status.get("falhas_recentes_24h"))
        status_label = str(worker_status.get("status_label") or "Sem classificacao")
        status_reason = str(worker_status.get("status_reason") or "Sem detalhe adicional.")
    else:
        raw_status_code = "atencao"
        snapshot_value = "--"
        updated_posts = "--"
        delay_minutes = "--"
        queue_ready = "--"
        queue_delayed = "--"
        recent_failures = "--"
        status_label = "Aguardando a view consolidada"
        status_reason = "A view ainda nao retornou a justificativa do estado."

    if discovery_status:
        discovery_status_code = str(discovery_status.get("status_code") or "atencao").lower()
        discovery_status_label = str(discovery_status.get("status_label") or "Sem classificacao")
        discovery_status_reason = str(discovery_status.get("status_reason") or "Sem detalhe adicional.")
        discovery_snapshot_value = str(
            discovery_status.get("ultima_descoberta_de_post_br")
            or format_timestamp_br(discovery_status.get("ultima_descoberta_de_post"))
        )
        discovery_new_posts = format_int(discovery_status.get("novos_posts_24h"))
    else:
        discovery_status_code = "neutral"
        discovery_status_label = "Aguardando view"
        discovery_status_reason = "Worker de descoberta roda a cada 6 horas e ainda precisa de uma view propria."
        discovery_snapshot_value = "--"
        discovery_new_posts = "--"

    if operational_signals:
        operational_status_code = str(operational_signals.get("status_code") or "atencao").lower()
        itens_atrasados_ate_1h = format_int(operational_signals.get("itens_atrasados_ate_1h"))
        itens_atrasados_ate_6h = format_int(operational_signals.get("itens_atrasados_ate_6h"))
        itens_atrasados_ate_24h = format_int(operational_signals.get("itens_atrasados_ate_24h"))
        at_risk_bootstrap = format_int(operational_signals.get("at_risk_bootstrap"))
        at_risk_reason = str(
            operational_signals.get("status_reason")
            or "Leitura de bootstrap nao disponivel."
        )
    else:
        operational_status_code = "neutral"
        itens_atrasados_ate_1h = "--"
        itens_atrasados_ate_6h = "--"
        itens_atrasados_ate_24h = "--"
        at_risk_bootstrap = "--"
        at_risk_reason = "Aguardando a view v_dashboard_post_update_operational_signals."

    panels = [
        worker_panel_html(
            "Integridade da coleta",
            "Leitura executiva separada por worker operacional.",
            [
                worker_stat_html("Atualizacao de posts", status_label, status_reason, raw_status_code),
                worker_stat_html("Descoberta de novos posts", discovery_status_label, discovery_status_reason, discovery_status_code),
            ],
            "#ff8069",
            raw_status_code,
        ),
        worker_panel_html(
            "Evidencia de processamento",
            "Sinais concretos de execucao para cada fluxo.",
            [
                worker_stat_html(
                    "Atualizacao de posts",
                    snapshot_value,
                    f"Tempo de ultima coleta: {delay_minutes} | Posts atualizados 24h: {updated_posts}",
                    raw_status_code,
                ),
                worker_stat_html(
                    "Descoberta de novos posts",
                    discovery_snapshot_value,
                    f"Novos posts 24h: {discovery_new_posts} | {discovery_status_reason}",
                    discovery_status_code,
                ),
            ],
            "#98df96",
            raw_status_code,
        ),
        worker_panel_html(
            "Sinais operacionais",
            "Leitura de atraso e risco de cobertura do worker horario.",
            [
                worker_stat_html(
                    "Ate 1h",
                    itens_atrasados_ate_1h,
                    "",
                    None,
                ),
                worker_stat_html(
                    "Ate 6h",
                    itens_atrasados_ate_6h,
                    "",
                    None,
                ),
                worker_stat_html(
                    "Ate 24h",
                    itens_atrasados_ate_24h,
                    "",
                    None,
                ),
                worker_stat_html(
                    "At risk bootstrap",
                    at_risk_bootstrap,
                    at_risk_reason,
                    operational_status_code,
                ),
            ],
            "#f2c14e",
            operational_status_code,
        ),
    ]
    worker_panel_grid(panels)

    st.write("")
    with st.expander("Passo a passo enxuto de implementacao", expanded=True):
        st.markdown(
            """
1. Consolidar no Supabase uma unica view `v_dashboard_worker_health_status`.
2. Validar apenas os campos do card antes de pensar em tabelas detalhadas.
3. Manter uma leitura por pagina com cache e sem polling automatico.
4. Liberar primeiro os sinais executivos: ultimo snapshot, posts 24h, faixas de atraso e at risk bootstrap.
5. So depois adicionar detalhamento por fila, banda ou erro especifico.

Para economizar tokens nas proximas sessoes:

1. Pedir sempre alteracoes em um unico arquivo por vez quando a mudanca for visual.
2. Trabalhar primeiro com a view consolidada, evitando discutir varias queries em paralelo.
3. Validar o texto e a hierarquia dos cards antes de abrir o detalhamento tecnico.
4. Usar prompts curtos do tipo: `ajuste apenas o bloco Integridade da coleta, sem ler outros arquivos`.
"""
        )


def get_external_intake_mock_state() -> dict[str, Any]:
    defaults = {
        "entity_status": "nao_checada",
        "entity_check_result": None,
        "review_ready": False,
        "published": False,
        "validated": False,
        "creator_ready": False,
    }
    for key, value in defaults.items():
        st.session_state.setdefault(key, value)
    return {key: st.session_state[key] for key in defaults}


def get_mock_entity_bank() -> list[dict[str, str]]:
    return [
        {"display_name": "Auto Mercado Brasil", "normalized_name": "auto mercado brasil", "entity_id": "128"},
        {"display_name": "Canal do Carro Eletrico", "normalized_name": "canal do carro eletrico", "entity_id": "214"},
        {"display_name": "Radar Automotivo", "normalized_name": "radar automotivo", "entity_id": "377"},
    ]


def get_mock_taxonomy_options() -> list[str]:
    return [
        "Mercado automotivo > Analise de mercado",
        "Mercado automotivo > Emplacamentos",
        "Mercado automotivo > Redes de concessionarias",
        "Eletricos > Infraestrutura de recarga",
        "Eletricos > Lancamentos",
        "Performance > Preparacao leve",
        "Manutencao > Revisao preventiva",
    ]


def render_external_intake_page(page_title: str = "Cadastro de Criadores") -> None:
    state = get_external_intake_mock_state()
    mock_entities = get_mock_entity_bank()
    mock_taxonomy_options = get_mock_taxonomy_options()
    page_header(page_title, "Prototipo de metodo sem ligacao com SQL")
    process_banner(
        "Regra obrigatoria de governanca",
        "A UI pode guiar o operador, mas nao pode pular o fluxo: entidade_intake, revisao, publicacao, validacao e so depois cadastro do criador.",
    )

    step_cards = [
        process_step_card(
            "Etapa 1",
            "Entidade",
            "Checar se a entidade ja existe por nome exibido e nome normalizado. Se nao existir, cadastrar via intake em vez de gravar direto em public.entities.",
            "ok-green" if state["entity_status"] == "existente" else "alert-yellow",
            "entidade existente" if state["entity_status"] == "existente" else "cadastrar via intake",
        ),
        process_step_card(
            "Etapa 2",
            "Criador",
            "Cadastrar o criador somente depois da checagem da entidade. O cadastro final continua bloqueado ate review, publicacao e validacao.",
            "ok-green" if state["creator_ready"] else "neutral",
            "liberado" if state["creator_ready"] else "bloqueado",
        ),
        process_step_card(
            "Etapa 3",
            "Associacao de nichos",
            "Subir as opcoes existentes, permitir multiplas associacoes e garantir que o vinculo sera feito para a mesma entidade cadastrada na etapa 1.",
            "neutral",
            "multipla selecao",
        ),
        process_step_card(
            "Etapa 4",
            "Revisao e publicacao",
            "A entidade precisa passar por review, depois publish_entity_intake e por fim validacao de vinculos antes do criador.",
            "ok-green" if state["validated"] else "alert-yellow",
            "validado" if state["validated"] else "aguardando fluxo manual",
        ),
    ]
    process_step_grid(step_cards)

    tab_form, tab_review, tab_rules = st.tabs(
        ["Novo criador de conteudo", "Simulacao de review", "Regras da governanca"]
    )

    with tab_form:
        col_left, col_right = st.columns([1.35, 1])

        with col_left:
            st.markdown("### 1. Cadastrar entidade")
            raw_name = st.text_input("Nome da Entidade", value="Auto Mercado Brasil")
            normalized_name = raw_name.strip().lower()
            creator_type = st.selectbox("Tipo de criador", ["mid-tier", "editorial", "independente"])

            if st.button("Checar entidade no banco", use_container_width=False):
                display_match = next(
                    (row for row in mock_entities if row["display_name"].strip().lower() == raw_name.strip().lower()),
                    None,
                )
                normalized_match = next(
                    (row for row in mock_entities if row["normalized_name"] == normalized_name),
                    None,
                )
                if display_match or normalized_match:
                    st.session_state["entity_status"] = "existente"
                    st.session_state["entity_check_result"] = {
                        "display_match": display_match,
                        "normalized_match": normalized_match,
                    }
                else:
                    st.session_state["entity_status"] = "nova_entity"
                    st.session_state["entity_check_result"] = {
                        "display_match": None,
                        "normalized_match": None,
                    }

            entity_status = st.session_state["entity_status"]
            entity_check_result = st.session_state.get("entity_check_result")

            st.markdown("### 2. Cadastrar criador")
            platform = st.selectbox("Plataforma", ["youtube", "instagram", "tiktok"])
            username = st.text_input("Username", value="@automercadobrasil")
            channel_id = st.text_input("Channel ID", value="UC1234567890ABCDE")
            followers = st.number_input("Followers", min_value=0, value=185000, step=1000)

            st.markdown("### 3. Associar nichos")
            linked_entity_name = raw_name if entity_status == "nova_entity" else (entity_check_result or {}).get("display_match", {}).get("display_name", raw_name)
            st.text_input("Entidade que recebera a associacao", value=linked_entity_name, disabled=True)
            taxonomy_selection = st.multiselect(
                "Nichos e subnichos existentes",
                mock_taxonomy_options,
                default=["Mercado automotivo > Analise de mercado"],
            )
            taxonomy_request = st.text_input("Solicitar novo nicho ou subnicho", value="")

        with col_right:
            st.markdown("### Leitura da UI")
            creator_blocked = entity_status != "nova_entity" or not state["validated"]
            local_warnings = []
            entity_found = entity_status == "existente"
            if entity_status == "nao_checada":
                local_warnings.append("Use o botao para checar o banco antes de cadastrar a entidade.")
            if entity_found:
                local_warnings.append("A entidade ja existe no banco. O cadastro de nova entidade deve ficar bloqueado.")
            if not taxonomy_selection and not taxonomy_request.strip():
                local_warnings.append("A entidade precisa sair desta tela com pelo menos uma associacao de nicho ou uma solicitacao aberta.")
            if taxonomy_request.strip():
                local_warnings.append("Novo nicho ou subnicho deve entrar como solicitacao controlada, nao como cadastro direto.")
            if not channel_id.strip():
                local_warnings.append("Channel ID e obrigatorio para o cadastro final do criador.")
            if entity_status != "nova_entity":
                local_warnings.append("O cadastro final em public.creators depende de uma nova entidade validada nesta jornada.")
            elif creator_blocked:
                local_warnings.append("O cadastro final em public.creators deve continuar bloqueado nesta etapa.")

            chips = [
                dq_chip("Entidade", "existente" if entity_found else "nova", "alert-yellow" if entity_found else "ok-green"),
                dq_chip("Criador", "bloqueado" if creator_blocked else "liberado", "neutral" if creator_blocked else "ok-green"),
                dq_chip("Nichos", str(len(taxonomy_selection)), "ok-green" if taxonomy_selection else "alert-yellow"),
            ]
            st.markdown(
                dq_kpi_card(
                    "Prontidao do cadastro",
                    "Bloqueado" if creator_blocked else "Liberado",
                    "A UI so libera o criador depois do fluxo manual obrigatorio.",
                    "#ff8069" if creator_blocked else "#98df96",
                    chips,
                ),
                unsafe_allow_html=True,
            )

            st.markdown("### Payload que iria para entidade_intake")
            st.json(
                {
                    "raw_name": raw_name,
                    "normalized_name": normalized_name,
                    "tipo_criador": creator_type,
                    "status": "pending",
                }
            )

            st.markdown("### Payload que ficaria retido ate o fim do fluxo")
            st.json(
                {
                    "platform": platform,
                    "username": username,
                    "channel_id": channel_id,
                    "followers": followers,
                }
            )

            st.markdown("### Associacao planejada")
            st.json(
                {
                    "nome_entidade": linked_entity_name,
                    "associacoes_existentes": taxonomy_selection,
                    "solicitacao_taxonomia": taxonomy_request.strip() or None,
                }
            )

            if entity_check_result:
                st.markdown("### Resultado da checagem")
                st.json(entity_check_result)

            if local_warnings:
                st.warning(" | ".join(local_warnings))
            else:
                st.success("A estrutura do rascunho respeita o processo de governanca atual.")

    with tab_review:
        st.markdown("### Simulacao guiada do processo manual")
        flow_col1, flow_col2, flow_col3, flow_col4 = st.columns(4)

        with flow_col1:
            if st.button("Marcar review pronto", use_container_width=True):
                st.session_state["review_ready"] = True
        with flow_col2:
            if st.button("Simular publicacao", use_container_width=True):
                st.session_state["published"] = True
        with flow_col3:
            if st.button("Simular validacao", use_container_width=True):
                st.session_state["validated"] = True
        with flow_col4:
            if st.button("Liberar criador", use_container_width=True):
                st.session_state["creator_ready"] = True

        review_rows = [
            {
                "raw_name": "Auto Mercado Brasil",
                "sub_niche_name": "Analise de mercado",
                "status": "pending" if not st.session_state["published"] else "published",
                "review_result": "READY_TO_INSERT" if st.session_state["review_ready"] else "CHECK_DUPLICATE",
                "existing_entity_id": 128 if st.session_state["entity_status"] == "existente" else None,
                "existing_entity_name": "Auto Mercado Brasil" if st.session_state["entity_status"] == "existente" else None,
                "sub_niche_id": 42,
                "matched_sub_niche_name": "Analise de mercado",
                "notes": "Mock de avaliacao sem SQL.",
            }
        ]
        review_card_grid(review_rows)

        with st.expander("Detalhe tecnico da revisao", expanded=False):
            st.dataframe(pd.DataFrame(review_rows), use_container_width=True, hide_index=True)

        timeline = [
            ("Cadastro em entity_intake", "ok"),
            ("Review via v_entity_intake_review", "ok" if st.session_state["review_ready"] else "atencao"),
            ("Publish via public.publish_entity_intake()", "ok" if st.session_state["published"] else "atencao"),
            ("Validacao de vinculos", "ok" if st.session_state["validated"] else "atencao"),
            ("Cadastro final em public.creators", "ok" if st.session_state["creator_ready"] else "neutral"),
        ]
        st.markdown("### Estado atual do processo")
        st.markdown(
            "".join(dq_chip(label, status.upper(), "ok-green" if status == "ok" else "alert-yellow" if status == "atencao" else "neutral") for label, status in timeline),
            unsafe_allow_html=True,
        )

        if st.button("Reiniciar simulacao", use_container_width=False):
            for key in ["review_ready", "published", "validated", "creator_ready"]:
                st.session_state[key] = False
            st.rerun()

    with tab_rules:
        st.markdown("### O que a UI precisa respeitar")
        st.info(
            "Nunca inserir direto em public.entities ou public.entity_sub_niches. Toda entrada manual continua passando por public.entity_intake."
        )
        st.markdown(
            """
- A busca de entidade vem antes de qualquer tentativa de criar criador.
- O botao de checagem precisa bloquear quando encontrar correspondencia por nome exibido ou nome normalizado.
- Se a entidade nao existir, a UI deve cadastrar via intake e nao gravar na tabela final.
- O criador vem antes da associacao final de nichos nesta jornada.
- Nicho e subnicho precisam subir como opcoes existentes, com selecao multipla, ou entrar como solicitacao controlada.
- Review vem antes de publish, e publish vem antes de validate.
- `platform`, `channel_id` e `followers` podem existir no rascunho da tela, mas nao podem virar criador final antes do fim do fluxo.
- O Streamlit deve funcionar como camada de operacao guiada, nao como editor SQL.
"""
        )


def render_fenabrave_page() -> None:
    page_header("Fenabrave")
    st.write("")


inject_theme()

with st.sidebar:
    st.markdown("## SM Analytics")
    st.caption("Automotivo Americas")
    if "nav_page" not in st.session_state:
        st.session_state["nav_page"] = "Overview"
    if "cadastro_subpage" not in st.session_state:
        st.session_state["cadastro_subpage"] = "Criadores"
    if "cadastro_menu_open" not in st.session_state:
        st.session_state["cadastro_menu_open"] = False

    def sidebar_nav_button(label: str, page_value: str, selected_value: str | None = None) -> None:
        active = st.session_state["nav_page"] == page_value if selected_value is None else st.session_state["cadastro_subpage"] == selected_value
        button_kwargs = {
            "label": label,
            "use_container_width": True,
            "key": f"nav-{page_value}-{selected_value or 'main'}",
            "type": "primary" if active else "secondary",
        }
        if st.button(**button_kwargs):
            if selected_value is None:
                st.session_state["nav_page"] = page_value
                if page_value != "Cadastro":
                    st.session_state["cadastro_menu_open"] = False
            else:
                st.session_state["nav_page"] = page_value
                st.session_state["cadastro_subpage"] = selected_value
                st.session_state["cadastro_menu_open"] = True
            st.rerun()

    sidebar_nav_button("Overview", "Overview")
    sidebar_nav_button("Creators", "Creators")
    sidebar_nav_button("Videos em crescimento", "Videos em crescimento")
    sidebar_nav_button("Hot now", "Hot now")
    sidebar_nav_button("Data quality", "Data quality")

    cadastro_active = st.session_state["nav_page"] == "Cadastro"
    cadastro_open = st.session_state["cadastro_menu_open"] or cadastro_active
    if st.button(
        "Cadastro",
        use_container_width=True,
        key="nav-cadastro-toggle",
        type="primary" if cadastro_open else "secondary",
    ):
        st.session_state["cadastro_menu_open"] = not cadastro_open
        st.session_state["nav_page"] = "Cadastro"
        if st.session_state["cadastro_menu_open"] and st.session_state["cadastro_subpage"] not in {"Criadores", "Fenabrave"}:
            st.session_state["cadastro_subpage"] = "Criadores"
        st.rerun()

    if cadastro_open:
        st.markdown('<div class="sidebar-nav-spacer"></div>', unsafe_allow_html=True)
        child_indent = st.columns([0.12, 0.88])
        with child_indent[0]:
            st.write("")
        with child_indent[1]:
            sidebar_nav_button("Criadores", "Cadastro", "Criadores")
        child_indent = st.columns([0.12, 0.88])
        with child_indent[0]:
            st.write("")
        with child_indent[1]:
            sidebar_nav_button("Fenabrave", "Cadastro", "Fenabrave")

    sidebar_nav_button("Sanitizacao operacional", "Sanitizacao operacional")

page = st.session_state["nav_page"]
cadastro_subpage = st.session_state.get("cadastro_subpage", "Criadores")

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
elif page == "Cadastro":
    if cadastro_subpage == "Criadores":
        render_external_intake_page("Cadastro de Criadores")
    else:
        render_fenabrave_page()
else:
    render_placeholder_page(
        "Sanitizacao operacional",
        "Revisao manual de casos operacionais e confirmacao de sanitizacao.",
    )
