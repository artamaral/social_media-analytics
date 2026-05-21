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


def worker_stat_html(label: str, value: str, caption: str, tone: str = "neutral") -> str:
    chip_class = {
        "ok": "ok-green",
        "atencao": "alert-yellow",
        "warning": "alert-yellow",
        "nok": "alert-red",
        "danger": "alert-red",
        "neutral": "neutral",
    }.get(tone, "neutral")
    return (
        '<div class="worker-stat">'
        f'<div class="worker-stat-label">{escape(label)}</div>'
        f'<div class="worker-stat-value">{escape(value)}</div>'
        f'<div class="worker-stat-caption">{escape(caption)}</div>'
        f'<div class="dq-chip-row"><span class="dq-chip {escape(chip_class)}">{escape(tone)}</span></div>'
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
    st.write("")
    st.markdown("### Integridade da coleta")

    if error:
        st.warning(error)

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

    discovery_status_code = "neutral"
    discovery_status_label = "Aguardando view"
    discovery_status_reason = "Worker de descoberta roda a cada 6 horas e ainda precisa de uma view propria."
    discovery_snapshot_value = "--"
    discovery_new_posts = "--"

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
            "Heartbeat operacional",
            "Leitura de fila e sinais de degradacao recente.",
            [
                worker_stat_html("Fila com movimento", queue_ready, "Itens prontos para processamento na fila."),
                worker_stat_html(
                    "Falhas recentes",
                    recent_failures,
                    "Eventos recentes que merecem acompanhamento.",
                ),
                worker_stat_html(
                    "Fila atrasada",
                    queue_delayed,
                    "Itens ja vencidos ou sem giro esperado.",
                ),
            ],
            "#f2c14e",
            raw_status_code,
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
4. Liberar primeiro os sinais executivos: ultimo snapshot, posts 24h, fila com movimento, atraso e falhas recentes.
5. So depois adicionar detalhamento por fila, banda ou erro especifico.

Para economizar tokens nas proximas sessoes:

1. Pedir sempre alteracoes em um unico arquivo por vez quando a mudanca for visual.
2. Trabalhar primeiro com a view consolidada, evitando discutir varias queries em paralelo.
3. Validar o texto e a hierarquia dos cards antes de abrir o detalhamento tecnico.
4. Usar prompts curtos do tipo: `ajuste apenas o bloco Integridade da coleta, sem ler outros arquivos`.
"""
        )


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
            "Sanitizacao operacional",
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
    render_placeholder_page(
        "Sanitizacao operacional",
        "Revisao manual de casos operacionais e confirmacao de sanitizacao.",
    )
