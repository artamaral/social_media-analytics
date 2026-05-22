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

        .creator-kpi-grid {
            display: grid;
            grid-template-columns: repeat(6, minmax(0, 1fr));
            gap: 0.75rem;
            margin-top: 0.75rem;
            margin-bottom: 1.1rem;
        }

        .creator-kpi-section-title {
            color: var(--text);
            font-size: 1.12rem;
            font-weight: 900;
            line-height: 1.1;
            text-transform: uppercase;
            letter-spacing: 0;
            margin-top: 0.95rem;
            margin-bottom: 0.2rem;
        }

        .creator-kpi-section-subtitle {
            color: var(--muted);
            font-size: 0.9rem;
            font-weight: 700;
            line-height: 1.25;
            margin-bottom: 0.35rem;
        }

        .creator-kpi-grid .metric-card {
            min-height: 126px;
        }

        .creator-kpi-grid .metric-card-header {
            display: flex;
            align-items: center;
            min-height: 2.15rem;
            padding: 0.55rem 0.7rem;
            font-size: 0.92rem;
            line-height: 1.05;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: clip;
        }

        .creator-kpi-grid .metric-card-body {
            padding: 0.8rem 0.85rem;
        }

        .creator-kpi-grid .metric-value {
            font-size: 1.3rem;
            gap: 0.6rem;
        }

        .creator-kpi-grid .metric-picto {
            width: 38px;
            height: 38px;
            font-size: 0.9rem;
        }

        .creator-kpi-grid .metric-caption {
            font-size: 0.69rem;
            margin-top: 0.55rem;
        }

        .creator-kpi-grid.weekly-grid {
            margin-top: 0.25rem;
        }

        @media (max-width: 1320px) {
            .creator-kpi-grid {
                grid-template-columns: repeat(3, minmax(0, 1fr));
            }
        }

        @media (max-width: 900px) {
            .creator-kpi-grid {
                grid-template-columns: repeat(2, minmax(0, 1fr));
            }
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

        .creator-layout {
            display: grid;
            grid-template-columns: minmax(0, 1.7fr) minmax(320px, 0.95fr);
            gap: 1rem;
            margin-top: 1rem;
        }

        .creator-panel {
            background: var(--card-dark);
            color: var(--text);
            border-radius: 8px;
            border: 1px solid rgba(255, 255, 255, 0.06);
            padding: 1rem 1.05rem;
        }

        .creator-panel-title {
            color: var(--text);
            font-size: 1.08rem;
            font-weight: 900;
            line-height: 1.15;
        }

        .creator-panel-subtitle {
            color: var(--muted);
            font-size: 0.88rem;
            line-height: 1.35;
            margin-top: 0.35rem;
        }

        .creator-ranking-list {
            display: grid;
            gap: 0.75rem;
            margin-top: 1rem;
        }

        .creator-ranking-item {
            display: grid;
            grid-template-columns: minmax(0, 2fr) minmax(120px, 0.9fr) minmax(120px, 0.9fr) minmax(110px, 0.75fr);
            gap: 0.85rem;
            align-items: center;
            background: rgba(255, 255, 255, 0.03);
            border: 1px solid rgba(255, 255, 255, 0.06);
            border-radius: 8px;
            padding: 0.85rem 0.9rem;
        }

        .creator-ranking-main {
            min-width: 0;
        }

        .creator-ranking-title {
            color: var(--text);
            font-size: 1rem;
            font-weight: 900;
            line-height: 1.15;
            overflow-wrap: anywhere;
        }

        .creator-ranking-meta {
            color: var(--muted);
            font-size: 0.82rem;
            margin-top: 0.25rem;
            line-height: 1.3;
            overflow-wrap: anywhere;
        }

        .creator-stat-label {
            color: var(--muted);
            font-size: 0.72rem;
            font-weight: 800;
            text-transform: uppercase;
        }

        .creator-stat-value {
            color: var(--text);
            font-size: 1rem;
            font-weight: 900;
            margin-top: 0.18rem;
            line-height: 1.1;
        }

        .creator-detail-grid {
            display: grid;
            grid-template-columns: repeat(2, minmax(0, 1fr));
            gap: 0.75rem;
            margin-top: 1rem;
        }

        .creator-detail-card {
            background: rgba(255, 255, 255, 0.03);
            border: 1px solid rgba(255, 255, 255, 0.06);
            border-radius: 8px;
            padding: 0.75rem 0.8rem;
            min-height: 78px;
        }

        .creator-detail-label {
            color: var(--muted);
            font-size: 0.72rem;
            font-weight: 800;
            text-transform: uppercase;
        }

        .creator-detail-value {
            color: var(--text);
            font-size: 0.9rem;
            font-weight: 800;
            margin-top: 0.25rem;
            overflow-wrap: anywhere;
        }

        .creator-gap-list {
            display: grid;
            gap: 0.55rem;
            margin-top: 1rem;
        }

        .creator-gap-item {
            background: rgba(255, 255, 255, 0.03);
            border: 1px solid rgba(255, 255, 255, 0.06);
            border-radius: 8px;
            padding: 0.75rem 0.8rem;
        }

        .creator-gap-item strong {
            color: var(--text);
            display: block;
            font-size: 0.88rem;
            line-height: 1.2;
        }

        .creator-gap-item span {
            color: var(--muted);
            display: block;
            font-size: 0.82rem;
            line-height: 1.35;
            margin-top: 0.25rem;
        }

        .creator-videos-toolbar {
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 1rem;
            flex-wrap: wrap;
            margin: 0.35rem 0 0.7rem;
        }

        .creator-videos-toolbar .stCheckbox {
            margin-bottom: 0;
        }

        .creator-reference-note {
            background: rgba(255, 128, 105, 0.08);
            border: 1px solid rgba(255, 128, 105, 0.24);
            border-radius: 8px;
            color: var(--text);
            padding: 0.85rem 0.95rem;
            margin-top: 0.85rem;
            margin-bottom: 1rem;
        }

        .creator-reference-note strong {
            display: block;
            font-size: 0.9rem;
            margin-bottom: 0.2rem;
        }

        .creator-section-title {
            color: var(--text);
            font-size: 1.05rem;
            font-weight: 900;
            margin: 0 0 0.2rem;
        }

        .creator-section-subtitle {
            color: var(--muted);
            font-size: 0.84rem;
            line-height: 1.35;
            margin-bottom: 0.7rem;
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


def metric_card_html(
    title: str,
    value: str,
    caption: str,
    picto: str,
    accent_color: str | None = None,
    caption_color: str | None = None,
) -> str:
    picto_style = f' style="color: {accent_color};"' if accent_color else ""
    caption_style = f' style="color: {caption_color};"' if caption and caption_color else ""
    caption_html = f'<div class="metric-caption"{caption_style}>{escape(caption)}</div>' if caption else ""
    return (
        '<div class="metric-card">'
        f'<div class="metric-card-header">{escape(title)}</div>'
        '<div class="metric-card-body">'
        '<div class="metric-value">'
        f"<span>{escape(value)}</span>"
        f'<span class="metric-picto"{picto_style}>{escape(picto)}</span>'
        "</div>"
        f"{caption_html}"
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


@st.cache_data(ttl=300, show_spinner=False)
def load_filtered_rows(
    source_name: str,
    filters: tuple[tuple[str, Any], ...] = (),
    order_by: str | None = None,
    order_desc: bool = False,
    limit: int | None = None,
) -> list[dict[str, Any]]:
    client = get_supabase_client()
    if client is None:
        return []

    query = client.table(source_name).select("*")
    for column_name, column_value in filters:
        query = query.eq(column_name, column_value)
    if order_by:
        query = query.order(order_by, desc=order_desc)
    if limit is not None:
        query = query.limit(limit)
    response = query.execute()
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


def get_filtered_rows(
    source_name: str,
    filters: tuple[tuple[str, Any], ...] = (),
    order_by: str | None = None,
    order_desc: bool = False,
    limit: int | None = None,
) -> tuple[list[dict[str, Any]], str | None]:
    if not is_supabase_configured():
        return [], "Supabase ainda nao configurado. Adicione SUPABASE_URL e SUPABASE_ANON_KEY nos secrets."

    try:
        return load_filtered_rows(source_name, filters, order_by, order_desc, limit), None
    except Exception as exc:
        return [], f"Falha ao consultar {source_name}: {exc}"


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


def get_fenabrave_mock_state() -> dict[str, Any]:
    defaults = {
        "fenabrave_source_confirmed": False,
        "fenabrave_metadata_registered": False,
        "fenabrave_preview_ready": False,
        "fenabrave_validated": False,
    }
    for key, value in defaults.items():
        st.session_state.setdefault(key, value)
    return {key: st.session_state[key] for key in defaults}


def get_creator_mock_rows() -> list[dict[str, Any]]:
    return [
        {
            "entity_id": 128,
            "entity_name": "Auto Mercado Brasil",
            "niche": "Mercado automotivo",
            "creator_type": "editorial",
            "creator_id": 12,
            "platform": "youtube",
            "username": "@automercadobrasil",
            "channel_id": "UC1234567890ABCDE",
            "followers": 185000,
            "post_count": 142,
            "total_views": 12850000,
            "total_likes": 418000,
            "total_comments": 29600,
            "engagement_rate_pct": 3.48,
            "latest_post_date": "2026-05-19",
            "latest_collected_at": "2026-05-22 08:00",
            "is_active": True,
            "sub_niche_display": "Analise de mercado",
            "followers_delta_30d": None,
            "avg_views_per_post": 90493,
        },
        {
            "entity_id": 214,
            "entity_name": "Radar de Concessionarias",
            "niche": "Mercado automotivo",
            "creator_type": "editorial",
            "creator_id": 24,
            "platform": "youtube",
            "username": "@radardeconcessionarias",
            "channel_id": "UCZYX987654321",
            "followers": 94200,
            "post_count": 88,
            "total_views": 6840000,
            "total_likes": 214500,
            "total_comments": 18400,
            "engagement_rate_pct": 3.40,
            "latest_post_date": "2026-05-18",
            "latest_collected_at": "2026-05-22 08:00",
            "is_active": True,
            "sub_niche_display": "Rede e varejo automotivo",
            "followers_delta_30d": None,
            "avg_views_per_post": 77727,
        },
        {
            "entity_id": 377,
            "entity_name": "Electric Garage Brasil",
            "niche": "Eletricos",
            "creator_type": "personal",
            "creator_id": 31,
            "platform": "youtube",
            "username": "@electricgaragebr",
            "channel_id": "UCFLEET1234567",
            "followers": 65300,
            "post_count": 64,
            "total_views": 4920000,
            "total_likes": 189000,
            "total_comments": 12100,
            "engagement_rate_pct": 4.09,
            "latest_post_date": "2026-05-21",
            "latest_collected_at": "2026-05-22 08:00",
            "is_active": True,
            "sub_niche_display": "Infraestrutura de recarga",
            "followers_delta_30d": None,
            "avg_views_per_post": 76875,
        },
    ]


def get_creator_monthly_series(entity_name: str) -> pd.DataFrame:
    monthly_map = {
        "Auto Mercado Brasil": [
            ("jan/2026", 1820000, 52100),
            ("fev/2026", 1940000, 54800),
            ("mar/2026", 2085000, 59300),
            ("abr/2026", 2170000, 61400),
            ("mai/2026", 2035000, 57600),
            ("jun/2026", 2280000, 64800),
        ],
        "Radar de Concessionarias": [
            ("jan/2026", 960000, 28400),
            ("fev/2026", 1025000, 30100),
            ("mar/2026", 1145000, 32900),
            ("abr/2026", 1100000, 31700),
            ("mai/2026", 1215000, 33800),
            ("jun/2026", 1295000, 35100),
        ],
        "Electric Garage Brasil": [
            ("jan/2026", 640000, 20100),
            ("fev/2026", 685000, 21400),
            ("mar/2026", 742000, 22900),
            ("abr/2026", 801000, 24700),
            ("mai/2026", 862000, 26100),
            ("jun/2026", 918000, 27600),
        ],
    }
    data = monthly_map.get(entity_name, monthly_map["Auto Mercado Brasil"])
    return pd.DataFrame(data, columns=["mes", "views_totais", "likes_totais"])


def get_creator_weekly_mock_rows(entity_name: str) -> list[dict[str, Any]]:
    weekly_map = {
        "Auto Mercado Brasil": [
            ("2026-04-13", "2026-04-19", "13/04/2026-19/04/2026", 1840000, 125000, 6.79, 52100, 3900, 8400, 610, 38),
            ("2026-04-20", "2026-04-26", "20/04/2026-26/04/2026", 1915000, 75000, 4.08, 54800, 2700, 8920, 520, 41),
            ("2026-04-27", "2026-05-03", "27/04/2026-03/05/2026", 2050000, 135000, 7.05, 58900, 4100, 9610, 690, 44),
            ("2026-05-04", "2026-05-10", "04/05/2026-10/05/2026", 2135000, 85000, 4.15, 61100, 2200, 10040, 430, 40),
            ("2026-05-11", "2026-05-17", "11/05/2026-17/05/2026", 2260000, 125000, 5.85, 64400, 3300, 10780, 740, 46),
        ],
        "Radar de Concessionarias": [
            ("2026-04-13", "2026-04-19", "13/04/2026-19/04/2026", 1010000, 52000, 5.43, 30100, 1800, 5020, 310, 24),
            ("2026-04-20", "2026-04-26", "20/04/2026-26/04/2026", 1085000, 75000, 7.43, 31900, 1800, 5360, 340, 28),
            ("2026-04-27", "2026-05-03", "27/04/2026-03/05/2026", 1120000, 35000, 3.23, 33000, 1100, 5580, 220, 26),
            ("2026-05-04", "2026-05-10", "04/05/2026-10/05/2026", 1200000, 80000, 7.14, 34700, 1700, 5910, 330, 31),
            ("2026-05-11", "2026-05-17", "11/05/2026-17/05/2026", 1265000, 65000, 5.42, 36100, 1400, 6140, 230, 29),
        ],
        "Electric Garage Brasil": [
            ("2026-04-13", "2026-04-19", "13/04/2026-19/04/2026", 705000, 41000, 6.18, 21400, 1400, 4380, 180, 18),
            ("2026-04-20", "2026-04-26", "20/04/2026-26/04/2026", 744000, 39000, 5.53, 22600, 1200, 4570, 190, 20),
            ("2026-04-27", "2026-05-03", "27/04/2026-03/05/2026", 802000, 58000, 7.80, 24400, 1800, 4860, 290, 23),
            ("2026-05-04", "2026-05-10", "04/05/2026-10/05/2026", 854000, 52000, 6.48, 25900, 1500, 5110, 250, 24),
            ("2026-05-11", "2026-05-17", "11/05/2026-17/05/2026", 903000, 49000, 5.74, 27300, 1400, 5320, 210, 22),
        ],
    }
    data = weekly_map.get(entity_name, weekly_map["Auto Mercado Brasil"])
    rows = []
    previous_active_posts = None
    for week_start, week_end, week_label, views_week_end, views_delta, views_growth_pct, likes_week_end, likes_delta, comments_week_end, comments_delta, active_posts_in_week in data:
        active_posts_delta = None if previous_active_posts is None else active_posts_in_week - previous_active_posts
        rows.append(
            {
                "week_start": week_start,
                "week_end": week_end,
                "week_label": week_label,
                "views_week_end": views_week_end,
                "views_delta_vs_prev_week": views_delta,
                "views_growth_pct_vs_prev_week": views_growth_pct,
                "likes_week_end": likes_week_end,
                "likes_delta_vs_prev_week": likes_delta,
                "comments_week_end": comments_week_end,
                "comments_delta_vs_prev_week": comments_delta,
                "active_posts_in_week": active_posts_in_week,
                "active_posts_delta_vs_prev_week": active_posts_delta,
            }
        )
        previous_active_posts = active_posts_in_week
    return rows


def get_creator_top_videos(entity_name: str) -> pd.DataFrame:
    top_video_map = {
        "Auto Mercado Brasil": [
            ("Novo reajuste das montadoras no 2o trimestre", "2026-05-19", 268000, 8400, 760, "long"),
            ("SUVs compactos: preco real nas concessionarias", "2026-05-16", 241000, 7900, 640, "long"),
            ("Financiamento em 2026: o que mudou", "2026-05-12", 218000, 6850, 590, "long"),
            ("Sedas medios que mais perderam valor", "2026-05-08", 191000, 6210, 552, "long"),
            ("Ranking de estoque parado por modelo", "2026-05-03", 177000, 5980, 488, "long"),
            ("Mercado direto para locadoras em abril", "2026-04-28", 166000, 5440, 451, "short"),
        ],
        "Radar de Concessionarias": [
            ("Mapa das concessionarias com maior giro", "2026-05-18", 151000, 5210, 404, "long"),
            ("Margem real no varejo de usados", "2026-05-15", 144000, 4980, 382, "long"),
            ("Aberturas e fechamentos de lojas no mes", "2026-05-10", 133000, 4560, 340, "long"),
            ("Como esta a aprovacao de credito", "2026-05-05", 126000, 4310, 301, "short"),
            ("Ranking por capital", "2026-04-29", 119000, 4080, 276, "short"),
            ("Comerciais leves: pressao de estoque", "2026-04-24", 111000, 3890, 250, "long"),
        ],
        "Electric Garage Brasil": [
            ("Custo real para carregar em viagem", "2026-05-21", 122000, 6120, 318, "long"),
            ("Recarga rapida: quando faz sentido", "2026-05-17", 118000, 5940, 294, "long"),
            ("Sedas eletricos mais vendidos", "2026-05-12", 109000, 5510, 272, "long"),
            ("Wallbox em condominio: o que verificar", "2026-05-08", 101000, 5230, 241, "short"),
            ("Autonomia no uso urbano real", "2026-05-02", 94000, 4870, 219, "short"),
            ("Infraestrutura publica em 2026", "2026-04-26", 89000, 4590, 204, "long"),
        ],
    }
    data = top_video_map.get(entity_name, top_video_map["Auto Mercado Brasil"])
    df = pd.DataFrame(
        data,
        columns=["titulo", "post_date", "views", "likes", "comments", "video_type"],
    )
    df["post_date"] = pd.to_datetime(df["post_date"])
    return df


def get_creator_cadence_matrix(entity_name: str) -> pd.DataFrame:
    cadence_map = {
        "Auto Mercado Brasil": [
            ("Seg", 3, 2, 1, 0, 0, 0),
            ("Ter", 2, 4, 2, 1, 0, 0),
            ("Qua", 1, 3, 4, 2, 0, 0),
            ("Qui", 0, 2, 5, 3, 1, 0),
            ("Sex", 0, 1, 3, 4, 2, 1),
            ("Sab", 0, 0, 1, 2, 1, 0),
            ("Dom", 0, 0, 0, 1, 0, 0),
        ],
        "Radar de Concessionarias": [
            ("Seg", 2, 2, 1, 0, 0, 0),
            ("Ter", 1, 3, 2, 1, 0, 0),
            ("Qua", 1, 2, 3, 2, 1, 0),
            ("Qui", 0, 2, 4, 2, 1, 0),
            ("Sex", 0, 1, 3, 3, 1, 1),
            ("Sab", 0, 0, 1, 1, 1, 0),
            ("Dom", 0, 0, 0, 0, 0, 0),
        ],
        "Electric Garage Brasil": [
            ("Seg", 1, 1, 1, 0, 0, 0),
            ("Ter", 1, 2, 2, 1, 0, 0),
            ("Qua", 0, 2, 3, 2, 1, 0),
            ("Qui", 0, 1, 4, 2, 1, 0),
            ("Sex", 0, 1, 2, 3, 2, 0),
            ("Sab", 0, 0, 1, 2, 1, 1),
            ("Dom", 0, 0, 0, 1, 1, 0),
        ],
    }
    columns = ["dia_semana", "sem_1", "sem_2", "sem_3", "sem_4", "sem_5", "extra"]
    return pd.DataFrame(cadence_map.get(entity_name, cadence_map["Auto Mercado Brasil"]), columns=columns)


def get_engagement_rank(rows: list[dict[str, Any]], entity_name: str) -> tuple[int, int]:
    ranked_rows = sorted(rows, key=lambda row: float(row["engagement_rate_pct"]), reverse=True)
    total = len(ranked_rows)
    for index, row in enumerate(ranked_rows, start=1):
        if row["entity_name"] == entity_name:
            return index, total
    return total, total


def get_delta_color(delta_value: float | int | None) -> str:
    if delta_value is None:
        return "#aeb4bf"
    if delta_value > 0:
        return "#98df96"
    if delta_value < 0:
        return "#ff6f61"
    return "#f2c14e"


def format_growth_caption(delta_value: float | int | None, pct_value: float | None, fallback: str = "Sem base semanal") -> tuple[str, str]:
    if delta_value is None or pct_value is None:
        return fallback, "#aeb4bf"
    signed_pct = f"{pct_value:+.2f}%".replace(".", ",")
    return f"{signed_pct} vs ultima semana", get_delta_color(delta_value)


def calculate_delta_pct(current_value: int | None, delta_value: int | None) -> float | None:
    if current_value is None or delta_value is None:
        return None
    previous_value = current_value - delta_value
    if previous_value <= 0:
        return None
    return round((delta_value / previous_value) * 100, 2)


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


def render_creator_detail_page() -> None:
    summary_rows, summary_error = get_view_rows("v_dashboard_creator_summary")
    rows = summary_rows or get_creator_mock_rows()
    selected_name = st.session_state.get("creator_selected_name", rows[0]["entity_name"])
    selected_default = next((row for row in rows if row["entity_name"] == selected_name), rows[0])

    page_header("Criador individual")

    filter_col1, filter_col2, filter_col3 = st.columns([1.5, 1.15, 1.0])
    with filter_col1:
        selected_creator_name = st.selectbox(
            "Criador em foco",
            [row["entity_name"] for row in rows],
            index=[row["entity_name"] for row in rows].index(selected_default["entity_name"]),
        )
    with filter_col2:
        selected_platform = st.selectbox("Plataforma", ["todas", "youtube", "instagram", "tiktok"], index=1)

    st.session_state["creator_selected_name"] = selected_creator_name
    working_rows = rows
    if selected_platform != "todas":
        working_rows = [row for row in working_rows if row["platform"] == selected_platform]
    working_rows = sorted(working_rows, key=lambda row: int(row["total_views"]), reverse=True)

    selected_row = next((row for row in working_rows if row["entity_name"] == selected_creator_name), working_rows[0] if working_rows else rows[0])

    weekly_rows, weekly_error = get_filtered_rows(
        "v_dashboard_creator_weekly_timeseries",
        filters=(("creator_id", selected_row["creator_id"]),),
        order_by="week_start",
        order_desc=False,
    )
    if not weekly_rows:
        weekly_rows = get_creator_weekly_mock_rows(selected_row["entity_name"])

    period_options = [str(row["week_label"]) for row in reversed(weekly_rows)]
    latest_period_label = period_options[0] if period_options else "Sem base semanal"
    with filter_col3:
        selected_period_label = st.selectbox("Periodo", period_options or [latest_period_label], index=0)

    selected_week_row = next(
        (row for row in weekly_rows if str(row["week_label"]) == selected_period_label),
        weekly_rows[-1] if weekly_rows else {},
    )
    selected_week_index = next(
        (index for index, row in enumerate(weekly_rows) if str(row["week_label"]) == selected_period_label),
        len(weekly_rows) - 1,
    )
    previous_week_row = weekly_rows[selected_week_index - 1] if selected_week_index > 0 else None
    if selected_week_row and "active_posts_delta_vs_prev_week" not in selected_week_row:
        previous_active_posts = int(previous_week_row.get("active_posts_in_week") or 0) if previous_week_row else None
        current_active_posts = int(selected_week_row.get("active_posts_in_week") or 0)
        selected_week_row["active_posts_delta_vs_prev_week"] = (
            None if previous_active_posts is None else current_active_posts - previous_active_posts
        )

    chart_rows = [row for row in weekly_rows if str(row["week_start"]) <= str(selected_week_row.get("week_start", ""))]
    chart_rows = chart_rows[-8:]
    weekly_df = pd.DataFrame(chart_rows)

    top_videos_rows, top_videos_error = get_filtered_rows(
        "posts",
        filters=(("creator_id", selected_row["creator_id"]),),
        order_by="views",
        order_desc=True,
        limit=10,
    )
    if not top_videos_rows:
        top_videos_df = get_creator_top_videos(selected_row["entity_name"])
    else:
        top_videos_df = pd.DataFrame(top_videos_rows)

    engagement_rank, engagement_total = get_engagement_rank(working_rows or rows, selected_row["entity_name"])
    likes_growth_pct = calculate_delta_pct(
        int(selected_week_row.get("likes_week_end") or 0),
        int(selected_week_row.get("likes_delta_vs_prev_week")) if selected_week_row.get("likes_delta_vs_prev_week") is not None else None,
    )
    comments_growth_pct = calculate_delta_pct(
        int(selected_week_row.get("comments_week_end") or 0),
        int(selected_week_row.get("comments_delta_vs_prev_week")) if selected_week_row.get("comments_delta_vs_prev_week") is not None else None,
    )
    active_posts_growth_pct = calculate_delta_pct(
        int(selected_week_row.get("active_posts_in_week") or 0),
        int(selected_week_row.get("active_posts_delta_vs_prev_week")) if selected_week_row.get("active_posts_delta_vs_prev_week") is not None else None,
    )

    st.markdown(
        '<div class="creator-kpi-section-title">Bloco total do criador</div>',
        unsafe_allow_html=True,
    )
    metric_card_grid(
        [
            metric_card_html("Seguidores", format_int(selected_row["followers"]), "", "SG"),
            metric_card_html("Engajamento", f"{engagement_rank} de {engagement_total}", "", "RK"),
            metric_card_html("Videos", format_int(selected_row["post_count"]), "", "VD"),
            metric_card_html("Views", format_int(selected_row["total_views"]), "", "VW"),
            metric_card_html("Likes", format_int(selected_row["total_likes"]), "", "LK"),
            metric_card_html("Comentarios", format_int(selected_row["total_comments"]), "", "CM"),
        ],
        class_name="creator-kpi-grid",
    )

    donut_df = pd.DataFrame(
        {
            "metrica": ["Likes", "Comentarios"],
            "valor": [int(selected_row["total_likes"]), int(selected_row["total_comments"])],
        }
    )
    donut_fig = px.pie(
        donut_df,
        names="metrica",
        values="valor",
        hole=0.62,
        color="metrica",
        color_discrete_map={"Likes": "#ff8069", "Comentarios": "#f2c14e"},
    )
    donut_fig.update_traces(textinfo="percent", hovertemplate="%{label}: %{value:,}<extra></extra>")
    apply_plotly_theme(donut_fig, legend_title="Metrica")

    weekly_fig = px.bar(
        weekly_df,
        x="week_label",
        y="views_delta_vs_prev_week",
        color_discrete_sequence=["#ff8069"],
    )
    weekly_fig.add_scatter(
        x=weekly_df["week_label"],
        y=weekly_df["views_growth_pct_vs_prev_week"],
        mode="lines+markers",
        name="% views",
        line=dict(color="#f2c14e", width=2),
        yaxis="y2",
    )
    weekly_fig.update_layout(
        yaxis_title="Delta de views",
        yaxis2=dict(title="% vs semana anterior", overlaying="y", side="right", showgrid=False),
    )
    apply_plotly_theme(weekly_fig, legend_title="Serie")

    engagement_display = f"{float(selected_row['engagement_rate_pct']):.2f}%"
    selected_sub_niche = str(selected_row.get("sub_niche_display") or selected_row.get("niche") or "Sem classificacao fina")
    selected_creator_type = str(selected_row.get("creator_type") or "--")
    selected_latest_collected_at = format_timestamp_br(selected_row.get("latest_collected_at"))
    selected_latest_post_date = format_timestamp_br(selected_row.get("latest_post_date"))
    selected_status = "ativo" if bool(selected_row.get("is_active")) else "inativo"

    selected_week_label = str(selected_week_row.get("week_label") or "Sem base semanal")
    weekly_followers_caption, weekly_followers_caption_color = "Acumulado ate a semana selecionada", "#aeb4bf"
    weekly_engagement_caption, weekly_engagement_caption_color = "Acumulado ate a semana selecionada", "#aeb4bf"
    weekly_videos_caption, weekly_videos_caption_color = format_growth_caption(
        selected_week_row.get("active_posts_delta_vs_prev_week"),
        active_posts_growth_pct,
    )
    weekly_views_caption, weekly_views_caption_color = format_growth_caption(
        selected_week_row.get("views_delta_vs_prev_week"),
        float(selected_week_row.get("views_growth_pct_vs_prev_week")) if selected_week_row.get("views_growth_pct_vs_prev_week") is not None else None,
    )
    weekly_likes_caption, weekly_likes_caption_color = format_growth_caption(
        selected_week_row.get("likes_delta_vs_prev_week"),
        likes_growth_pct,
    )
    weekly_comments_caption, weekly_comments_caption_color = format_growth_caption(
        selected_week_row.get("comments_delta_vs_prev_week"),
        comments_growth_pct,
    )

    st.markdown(
        f'<div class="creator-kpi-section-title">Semana selecionada: {escape(selected_week_label)}</div>',
        unsafe_allow_html=True,
    )
    st.caption("Os valores desta faixa representam o acumulado ate o fim da semana selecionada; a linha de baixo mostra a variacao vs a semana anterior completa.")
    metric_card_grid(
        [
            metric_card_html("Seguidores", format_int(selected_row["followers"]), weekly_followers_caption, "SG", caption_color=weekly_followers_caption_color),
            metric_card_html("Engajamento", f"{engagement_rank} de {engagement_total}", weekly_engagement_caption, "RK", caption_color=weekly_engagement_caption_color),
            metric_card_html("Videos", format_int(selected_week_row.get("active_posts_in_week")), weekly_videos_caption, "VD", caption_color=weekly_videos_caption_color),
            metric_card_html("Views", format_int(selected_week_row.get("views_week_end")), weekly_views_caption, "VW", caption_color=weekly_views_caption_color),
            metric_card_html("Likes", format_int(selected_week_row.get("likes_week_end")), weekly_likes_caption, "LK", caption_color=weekly_likes_caption_color),
            metric_card_html("Comentarios", format_int(selected_week_row.get("comments_week_end")), weekly_comments_caption, "CM", caption_color=weekly_comments_caption_color),
        ],
        class_name="creator-kpi-grid weekly-grid",
    )

    left_col, right_col = st.columns([1.35, 1])
    with left_col:
        chart_left, chart_right = st.columns([0.95, 1.05])
        with chart_left:
            st.markdown("#### Distribuicao de engajamento")
            st.caption("Dados usados: total_likes e total_comments do criador em v_dashboard_creator_summary.")
            st.plotly_chart(donut_fig, use_container_width=True)
        with chart_right:
            st.markdown("#### Crescimento semanal")
            st.caption("Dados usados: v_dashboard_creator_weekly_timeseries, apenas semanas completas.")
            st.plotly_chart(weekly_fig, use_container_width=True)

    with right_col:
        if summary_error or weekly_error or top_videos_error:
            active_errors = [error for error in [summary_error, weekly_error, top_videos_error] if error]
            st.warning(" | ".join(active_errors))

    video_scope_weekly = st.checkbox("Mostrar videos da semana selecionada", value=False)
    videos_source_df = top_videos_df.copy()
    if video_scope_weekly and "post_date" in videos_source_df.columns:
        videos_source_df["post_date"] = pd.to_datetime(videos_source_df["post_date"], errors="coerce")
        week_start = pd.to_datetime(selected_week_row.get("week_start"), errors="coerce")
        week_end = pd.to_datetime(selected_week_row.get("week_end"), errors="coerce")
        if pd.notna(week_start) and pd.notna(week_end):
            videos_source_df = videos_source_df[
                (videos_source_df["post_date"] >= week_start) & (videos_source_df["post_date"] <= week_end)
            ]
    videos_source_df = videos_source_df.sort_values(by="views", ascending=False, na_position="last") if "views" in videos_source_df.columns else videos_source_df
    top_videos_display = videos_source_df.copy()
    drop_video_columns = [
        column
        for column in top_videos_display.columns
        if "id" in str(column).lower() or "date" in str(column).lower()
    ]
    if drop_video_columns:
        top_videos_display = top_videos_display.drop(columns=drop_video_columns, errors="ignore")
    if "views" in top_videos_display.columns:
        top_videos_display["views"] = top_videos_display["views"].apply(format_int)
    if "likes" in top_videos_display.columns:
        top_videos_display["likes"] = top_videos_display["likes"].apply(format_int)
    if "comments" in top_videos_display.columns:
        top_videos_display["comments"] = top_videos_display["comments"].apply(format_int)
    top_videos_display = top_videos_display.rename(
        columns={
            "titulo": "Titulo",
            "title": "Titulo",
            "views": "Views",
            "likes": "Likes",
            "comments": "Comentarios",
            "video_type": "Tipo",
        }
    )
    top_videos_display = top_videos_display[[column for column in ["Titulo", "Views", "Likes", "Comentarios", "Tipo"] if column in top_videos_display.columns]]

    st.markdown("#### Videos")
    st.caption("Desmarcado exibe o historico completo; marcado exibe apenas os videos da semana selecionada.")
    st.dataframe(top_videos_display, use_container_width=True, hide_index=True)

    st.markdown("#### Leitura do criador em foco")
    st.markdown(
        (
            '<div class="creator-panel">'
            f'<div class="creator-panel-title">{escape(str(selected_row["entity_name"]))}</div>'
            f'<div class="creator-panel-subtitle">{escape(selected_sub_niche)} | {escape(selected_creator_type)} | ultima coleta {escape(selected_latest_collected_at)}</div>'
            '<div class="creator-detail-grid">'
            f'<div class="creator-detail-card"><div class="creator-detail-label">Plataforma</div><div class="creator-detail-value">{escape(str(selected_row["platform"]))}</div></div>'
            f'<div class="creator-detail-card"><div class="creator-detail-label">Canal</div><div class="creator-detail-value">{escape(str(selected_row["channel_id"]))}</div></div>'
            f'<div class="creator-detail-card"><div class="creator-detail-label">Posts monitorados</div><div class="creator-detail-value">{escape(format_int(selected_row["post_count"]))}</div></div>'
            f'<div class="creator-detail-card"><div class="creator-detail-label">Engajamento</div><div class="creator-detail-value">{escape(engagement_display)}</div></div>'
            f'<div class="creator-detail-card"><div class="creator-detail-label">Likes totais</div><div class="creator-detail-value">{escape(format_int(selected_row["total_likes"]))}</div></div>'
            f'<div class="creator-detail-card"><div class="creator-detail-label">Comentarios totais</div><div class="creator-detail-value">{escape(format_int(selected_row["total_comments"]))}</div></div>'
            f'<div class="creator-detail-card"><div class="creator-detail-label">Ultimo post</div><div class="creator-detail-value">{escape(selected_latest_post_date)}</div></div>'
            f'<div class="creator-detail-card"><div class="creator-detail-label">Status</div><div class="creator-detail-value">{escape(selected_status)}</div></div>'
            "</div>"
            '<div class="dq-chip-row">'
            f'{dq_chip("Subnicho", selected_sub_niche, "ok-green")}'
            f'{dq_chip("Curva followers", "pendente", "alert-yellow")}'
            f'{dq_chip("URL do post", "pendente", "alert-yellow")}'
            "</div>"
            '<div class="creator-gap-list">'
            '<div class="creator-gap-item"><strong>Campo faltante: subnichos reais</strong><span>A view atual ainda nao sobe a associacao real de entity_sub_niches. O mockup mostra a necessidade, mas nao finge que o dado ja existe.</span></div>'
            '<div class="creator-gap-item"><strong>Campo faltante: delta de audiencia</strong><span>A imagem sugere comparacoes temporais mais fortes. Para isso, precisamos de followers_delta_7d ou followers_delta_30d, alem da data da ultima coleta de audiencia.</span></div>'
            '<div class="creator-gap-item"><strong>Campo faltante: URL e resumo editorial</strong><span>Conseguimos montar a tabela de top videos com titulo, data, views, likes e comentarios. Ainda faltam URL publica e agregados editoriais mais ricos.</span></div>'
            "</div>"
            "</div>"
        ),
        unsafe_allow_html=True,
    )

    with st.expander("Campos usados no mockup", expanded=False):
        st.dataframe(
            pd.DataFrame(
                [
                    {"campo": "entity_name", "origem": "v_dashboard_creator_summary", "uso": "titulo e ranking"},
                    {"campo": "niche", "origem": "v_dashboard_creator_summary", "uso": "filtro"},
                    {"campo": "creator_type", "origem": "v_dashboard_creator_summary", "uso": "painel lateral"},
                    {"campo": "platform", "origem": "v_dashboard_creator_summary", "uso": "filtro e detalhe"},
                    {"campo": "username", "origem": "v_dashboard_creator_summary", "uso": "identificacao"},
                    {"campo": "channel_id", "origem": "v_dashboard_creator_summary", "uso": "identificacao tecnica"},
                    {"campo": "followers", "origem": "v_dashboard_creator_summary", "uso": "kpi e ranking"},
                    {"campo": "post_count", "origem": "v_dashboard_creator_summary", "uso": "kpi e ranking"},
                    {"campo": "total_views", "origem": "v_dashboard_creator_summary", "uso": "kpi e ranking"},
                    {"campo": "total_likes", "origem": "v_dashboard_creator_summary", "uso": "painel lateral"},
                    {"campo": "total_comments", "origem": "v_dashboard_creator_summary", "uso": "painel lateral"},
                    {"campo": "engagement_rate_pct", "origem": "v_dashboard_creator_summary", "uso": "kpi e ranking"},
                    {"campo": "latest_post_date", "origem": "v_dashboard_creator_summary", "uso": "detalhe"},
                    {"campo": "latest_collected_at", "origem": "v_dashboard_creator_summary", "uso": "detalhe operacional"},
                    {"campo": "is_active", "origem": "v_dashboard_creator_summary", "uso": "status"},
                    {"campo": "week_label", "origem": "v_dashboard_creator_weekly_timeseries", "uso": "periodo semanal selecionado"},
                    {"campo": "week_end", "origem": "v_dashboard_creator_weekly_timeseries", "uso": "ordem e semana completa"},
                    {"campo": "views_delta_vs_prev_week", "origem": "v_dashboard_creator_weekly_timeseries", "uso": "serie principal e subtitulo do KPI"},
                    {"campo": "views_growth_pct_vs_prev_week", "origem": "v_dashboard_creator_weekly_timeseries", "uso": "intensidade relativa semanal"},
                    {"campo": "likes_delta_vs_prev_week", "origem": "v_dashboard_creator_weekly_timeseries", "uso": "subtitulo semanal"},
                    {"campo": "comments_delta_vs_prev_week", "origem": "v_dashboard_creator_weekly_timeseries", "uso": "subtitulo semanal"},
                    {"campo": "active_posts_in_week", "origem": "v_dashboard_creator_weekly_timeseries", "uso": "comparacao semanal de videos ativos"},
                    {"campo": "title", "origem": "public.posts", "uso": "tabela de top videos"},
                    {"campo": "post_date", "origem": "public.posts", "uso": "tabela e serie temporal"},
                    {"campo": "views", "origem": "public.posts", "uso": "tabela de top videos e serie temporal"},
                    {"campo": "likes", "origem": "public.posts", "uso": "distribuicao e serie temporal"},
                    {"campo": "comments", "origem": "public.posts", "uso": "distribuicao e tabela"},
                    {"campo": "video_type", "origem": "public.posts", "uso": "classificacao visual dos top videos"},
                ]
            ),
            use_container_width=True,
            hide_index=True,
        )


def render_creator_overview_page() -> None:
    rows = get_creator_mock_rows()
    page_header("Visao geral de criadores", "Leitura comparativa da base monitorada")
    process_banner(
        "Papel desta view",
        "Esta tela resume a carteira monitorada. Ela responde quem esta maior, quem engaja melhor e quem concentra mais volume, sem entrar ainda no detalhe editorial profundo de um unico criador.",
    )

    selected_platform = st.selectbox("Plataforma", ["todas", "youtube", "instagram", "tiktok"], index=1)
    working_rows = rows if selected_platform == "todas" else [row for row in rows if row["platform"] == selected_platform]
    working_rows = sorted(working_rows, key=lambda row: int(row["total_views"]), reverse=True)

    total_followers = sum(int(row["followers"]) for row in working_rows)
    total_posts = sum(int(row["post_count"]) for row in working_rows)
    total_views = sum(int(row["total_views"]) for row in working_rows)
    total_likes = sum(int(row["total_likes"]) for row in working_rows)
    total_comments = sum(int(row["total_comments"]) for row in working_rows)
    avg_engagement = round(sum(float(row["engagement_rate_pct"]) for row in working_rows) / max(len(working_rows), 1), 2)

    metric_card_grid(
        [
            metric_card_html("Criadores ativos", format_int(len(working_rows)), "Base atual filtrada", "CR"),
            metric_card_html("Seguidores monitorados", format_int(total_followers), "Soma dos criadores filtrados", "SG"),
            metric_card_html("Total de videos", format_int(total_posts), "Posts monitorados na base", "VD"),
            metric_card_html("Total de views", format_int(total_views), "Volume acumulado da carteira", "VW"),
            metric_card_html("Total de likes", format_int(total_likes), "Interacoes acumuladas", "LK"),
            metric_card_html("Total de comentarios", format_int(total_comments), "Interacoes acumuladas", "CM"),
        ],
        class_name="fenabrave-card-grid",
    )

    st.markdown("#### Ranking comparativo")
    st.caption(f"Base filtrada em {selected_platform}. Engajamento medio atual da carteira: {avg_engagement:.2f}%.")
    ranking_items = []
    for row in working_rows:
        engagement_label = f"{float(row['engagement_rate_pct']):.2f}%"
        ranking_items.append(
            (
                '<div class="creator-ranking-item">'
                '<div class="creator-ranking-main">'
                f'<div class="creator-ranking-title">{escape(str(row["entity_name"]))}</div>'
                f'<div class="creator-ranking-meta">{escape(str(row["niche"]))} | {escape(str(row["platform"]))} | @{escape(str(row["username"]).lstrip("@"))}</div>'
                '</div>'
                '<div>'
                '<div class="creator-stat-label">Seguidores</div>'
                f'<div class="creator-stat-value">{escape(format_int(row["followers"]))}</div>'
                '</div>'
                '<div>'
                '<div class="creator-stat-label">Views totais</div>'
                f'<div class="creator-stat-value">{escape(format_int(row["total_views"]))}</div>'
                '</div>'
                '<div>'
                '<div class="creator-stat-label">Engajamento</div>'
                f'<div class="creator-stat-value">{escape(engagement_label)}</div>'
                '</div>'
                '</div>'
            )
        )
    st.markdown(
        '<div class="creator-panel">'
        '<div class="creator-panel-title">Comparativo dos criadores filtrados</div>'
        '<div class="creator-panel-subtitle">Esta e a view geral. O detalhe temporal e editorial completo fica reservado para a tela de criador individual.</div>'
        f'<div class="creator-ranking-list">{"".join(ranking_items)}</div>'
        '</div>',
        unsafe_allow_html=True,
    )


def render_fenabrave_page() -> None:
    state = get_fenabrave_mock_state()
    page_header("Cadastro Fenabrave", "Mockup da rotina mensal de inclusao de dados")
    process_banner(
        "Regra obrigatoria de governanca",
        "A rotina mensal continua manual no ponto certo: confirmar a publicacao, preservar o PDF no bucket privado, registrar metadados, revisar preview, validar e so depois liberar consumo.",
    )

    step_cards = [
        process_step_card(
            "Etapa 1",
            "Confirmar a fonte",
            "A rotina so comeca depois do 5o dia util e sempre para o mes anterior, usando a URL oficial da Fenabrave.",
            "ok-green" if state["fenabrave_source_confirmed"] else "alert-yellow",
            "fonte confirmada" if state["fenabrave_source_confirmed"] else "pendente",
        ),
        process_step_card(
            "Etapa 2",
            "Carregar PDF",
            "O PDF mensal pode ser carregado no Streamlit para apoio operacional, mas a versao oficial deve ser preservada no bucket privado market-source-files.",
            "ok-green",
            "pdf manual",
        ),
        process_step_card(
            "Etapa 3",
            "Registrar metadados",
            "A UI prepara os dados de market_source_files com periodo, source_url, storage_path, extraction_status e metodo de extracao.",
            "ok-green" if state["fenabrave_metadata_registered"] else "alert-yellow",
            "metadados prontos" if state["fenabrave_metadata_registered"] else "pendente",
        ),
        process_step_card(
            "Etapa 4",
            "Preview e validacao",
            "O fluxo so libera a view depois de preview humano, checks estruturais e aprovacao do periodo.",
            "ok-green" if state["fenabrave_validated"] else "alert-yellow",
            "validado" if state["fenabrave_validated"] else "aguardando checks",
        ),
    ]
    process_step_grid(step_cards)

    tab_monthly, tab_review, tab_rules = st.tabs(
        ["Rotina mensal", "Simulacao de status", "Regras da governanca"]
    )

    with tab_monthly:
        left, right = st.columns([1.35, 1])

        with left:
            st.markdown("### 1. Confirmar publicacao do mes anterior")
            reference_period = st.date_input(
                "Periodo de referencia",
                value=pd.Timestamp("2026-04-01").date(),
                format="DD/MM/YYYY",
            )
            source_url = st.text_input(
                "URL oficial do PDF",
                value="https://www.fenabrave.org.br/portal/files/2026_04_02.pdf",
            )
            source_page_url = st.text_input(
                "Pagina oficial de origem",
                value="https://www.fenabrave.org.br/portalv2/Conteudo/Emplacamentos%20",
            )
            if st.button("Confirmar fonte mensal", use_container_width=False):
                st.session_state["fenabrave_source_confirmed"] = True
                st.rerun()

            st.markdown("### 2. Carregar PDF do mes")
            uploaded_pdf = st.file_uploader(
                "PDF Fenabrave",
                type=["pdf"],
                help="O upload no Streamlit e viavel para apoio operacional. A versao oficial ainda deve ser enviada ao bucket privado.",
            )

            st.markdown("### 3. Registrar metadados")
            storage_bucket = st.text_input("Storage bucket", value="market-source-files")
            storage_path = st.text_input("Storage path", value="fenabrave/2026/04/2026_04_02.pdf")
            original_filename = st.text_input("Nome original do arquivo", value="2026_04_02.pdf")
            extraction_status = st.selectbox(
                "Status de extracao",
                ["stored", "extracted", "normalized", "validated", "failed"],
                index=0,
            )
            extraction_method = st.text_input("Metodo de extracao", value="pdf_table_extraction")
            if st.button("Preparar metadados do arquivo", use_container_width=False):
                st.session_state["fenabrave_metadata_registered"] = True
                st.rerun()

            st.markdown("### 4. Preview operacional")
            preview_rows = [
                {"segment_code": "autos", "segmento": "Autos", "mes_atual": 187313},
                {"segment_code": "comerciais_leves", "segmento": "Comerciais Leves", "mes_atual": 49943},
                {"segment_code": "autos_comerciais_leves", "segmento": "Autos + Comerciais Leves", "mes_atual": 237256},
            ]
            st.dataframe(pd.DataFrame(preview_rows), use_container_width=True, hide_index=True)
            if st.button("Marcar preview como revisado", use_container_width=False):
                st.session_state["fenabrave_preview_ready"] = True
                st.rerun()

        with right:
            st.markdown("### Leitura da rotina")
            uploaded_name = uploaded_pdf.name if uploaded_pdf is not None else None
            uploaded_size = uploaded_pdf.size if uploaded_pdf is not None else None
            can_validate = (
                st.session_state["fenabrave_source_confirmed"]
                and st.session_state["fenabrave_metadata_registered"]
                and st.session_state["fenabrave_preview_ready"]
            )
            warnings = []
            if not st.session_state["fenabrave_source_confirmed"]:
                warnings.append("A fonte oficial do mes anterior ainda nao foi confirmada.")
            if uploaded_pdf is None:
                warnings.append("O PDF ainda nao foi carregado para apoio operacional na tela.")
            if not st.session_state["fenabrave_metadata_registered"]:
                warnings.append("Os metadados de market_source_files ainda nao foram preparados.")
            if not st.session_state["fenabrave_preview_ready"]:
                warnings.append("O preview operacional ainda precisa de revisao humana.")
            if not can_validate:
                warnings.append("A liberacao da view deve ficar bloqueada ate a rotina mensal ficar completa.")

            chips = [
                dq_chip("Fonte", "ok" if st.session_state["fenabrave_source_confirmed"] else "pendente", "ok-green" if st.session_state["fenabrave_source_confirmed"] else "alert-yellow"),
                dq_chip("PDF", "carregado" if uploaded_pdf is not None else "ausente", "ok-green" if uploaded_pdf is not None else "alert-yellow"),
                dq_chip("Preview", "revisado" if st.session_state["fenabrave_preview_ready"] else "pendente", "ok-green" if st.session_state["fenabrave_preview_ready"] else "alert-yellow"),
                dq_chip("Liberacao", "pronta" if can_validate else "bloqueada", "ok-green" if can_validate else "neutral"),
            ]
            st.markdown(
                dq_kpi_card(
                    "Prontidao da carga mensal",
                    "Pronta" if can_validate else "Em andamento",
                    "A rotina continua manual nos pontos de controle, mesmo com apoio visual no Streamlit.",
                    "#98df96" if can_validate else "#ff8069",
                    chips,
                ),
                unsafe_allow_html=True,
            )

            st.markdown("### Metadados preparados")
            st.json(
                {
                    "source_name": "Fenabrave",
                    "reference_period": pd.Timestamp(reference_period).strftime("%d/%m/%Y"),
                    "source_url": source_url,
                    "source_page_url": source_page_url,
                    "storage_bucket": storage_bucket,
                    "storage_path": storage_path,
                    "original_filename": original_filename,
                    "extraction_status": extraction_status,
                    "extraction_method": extraction_method,
                }
            )

            st.markdown("### Avaliacao do PDF no Streamlit")
            st.json(
                {
                    "pdf_upload_viavel": True,
                    "nome_arquivo": uploaded_name,
                    "tamanho_bytes": uploaded_size,
                    "uso_recomendado": "apoio operacional e checagem de consistencia antes do envio oficial ao bucket privado",
                    "restricao": "nao expor service role nem usar o Streamlit publico como destino final de armazenamento",
                }
            )

            if warnings:
                st.warning(" | ".join(warnings))
            else:
                st.success("A rotina mockada esta completa e pronta para seguir para validacao final.")

    with tab_review:
        st.markdown("### Simulacao da rotina operacional")
        flow_col1, flow_col2, flow_col3, flow_col4 = st.columns(4)

        with flow_col1:
            if st.button("Confirmar fonte", use_container_width=True):
                st.session_state["fenabrave_source_confirmed"] = True
        with flow_col2:
            if st.button("Registrar metadados", use_container_width=True):
                st.session_state["fenabrave_metadata_registered"] = True
        with flow_col3:
            if st.button("Validar preview", use_container_width=True):
                st.session_state["fenabrave_preview_ready"] = True
        with flow_col4:
            if st.button("Aprovar periodo", use_container_width=True):
                st.session_state["fenabrave_validated"] = True

        review_rows = [
            {
                "periodo": "01/04/2026",
                "fonte": "Fenabrave",
                "arquivo": "2026_04_02.pdf",
                "storage_path": "fenabrave/2026/04/2026_04_02.pdf",
                "status_arquivo": "validated" if st.session_state["fenabrave_validated"] else "stored",
                "preview_operacional": "revisado" if st.session_state["fenabrave_preview_ready"] else "pendente",
                "resultado_validacao": "OK" if st.session_state["fenabrave_validated"] else "AGUARDANDO",
                "observacao": "Liberar view somente depois da aprovacao humana.",
            }
        ]
        review_card_grid(
            [
                {
                    "raw_name": row["arquivo"],
                    "sub_niche_name": row["periodo"],
                    "status": row["status_arquivo"],
                    "review_result": row["resultado_validacao"],
                    "existing_entity_id": row["fonte"],
                    "existing_entity_name": row["storage_path"],
                    "sub_niche_id": row["preview_operacional"],
                    "matched_sub_niche_name": "Rotina mensal Fenabrave",
                    "notes": row["observacao"],
                }
                for row in review_rows
            ]
        )

        timeline = [
            ("Fonte oficial confirmada", "ok" if st.session_state["fenabrave_source_confirmed"] else "atencao"),
            ("PDF preservado e registrado", "ok" if st.session_state["fenabrave_metadata_registered"] else "atencao"),
            ("Preview operacional revisado", "ok" if st.session_state["fenabrave_preview_ready"] else "atencao"),
            ("Periodo validado", "ok" if st.session_state["fenabrave_validated"] else "neutral"),
        ]
        st.markdown("### Estado atual do processo")
        st.markdown(
            "".join(dq_chip(label, status.upper(), "ok-green" if status == "ok" else "alert-yellow" if status == "atencao" else "neutral") for label, status in timeline),
            unsafe_allow_html=True,
        )

        if st.button("Reiniciar simulacao Fenabrave", use_container_width=False):
            for key in [
                "fenabrave_source_confirmed",
                "fenabrave_metadata_registered",
                "fenabrave_preview_ready",
                "fenabrave_validated",
            ]:
                st.session_state[key] = False
            st.rerun()

    with tab_rules:
        st.markdown("### O que a UI precisa respeitar")
        st.info(
            "O PDF pode ser carregado no Streamlit, mas o arquivo oficial precisa continuar no bucket privado market-source-files com registro em market_source_files."
        )
        st.markdown(
            """
- A rotina mensal so roda apos o 5o dia util e sempre para o mes anterior.
- O upload do PDF pelo Streamlit e viavel como apoio operacional e pode simplificar a conferenca do arquivo.
- O app nao deve usar o navegador como destino final do PDF nem expor credenciais privilegiadas.
- A persistencia oficial continua em bucket privado, com storage_path, source_url, hash, tamanho e extraction_status.
- O preview operacional vem antes da carga analitica.
- A view so deve ser liberada depois dos checks e da aprovacao humana do periodo.
"""
        )


inject_theme()

with st.sidebar:
    st.markdown("## SM Analytics")
    st.caption("Automotivo Americas")
    if "nav_page" not in st.session_state:
        st.session_state["nav_page"] = "Overview"
    if "creators_subpage" not in st.session_state:
        st.session_state["creators_subpage"] = "Visao geral"
    if "creators_menu_open" not in st.session_state:
        st.session_state["creators_menu_open"] = False
    if "cadastro_subpage" not in st.session_state:
        st.session_state["cadastro_subpage"] = "Criadores"
    if "cadastro_menu_open" not in st.session_state:
        st.session_state["cadastro_menu_open"] = False

    def sidebar_nav_button(label: str, page_value: str, selected_value: str | None = None) -> None:
        if selected_value is None:
            active = st.session_state["nav_page"] == page_value
        elif page_value == "Creators":
            active = st.session_state["nav_page"] == "Creators" and st.session_state["creators_subpage"] == selected_value
        else:
            active = st.session_state["nav_page"] == "Cadastro" and st.session_state["cadastro_subpage"] == selected_value
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
                if page_value != "Creators":
                    st.session_state["creators_menu_open"] = False
            else:
                st.session_state["nav_page"] = page_value
                if page_value == "Creators":
                    st.session_state["creators_subpage"] = selected_value
                    st.session_state["creators_menu_open"] = True
                else:
                    st.session_state["cadastro_subpage"] = selected_value
                    st.session_state["cadastro_menu_open"] = True
            st.rerun()

    sidebar_nav_button("Overview", "Overview")
    sidebar_nav_button("Videos em crescimento", "Videos em crescimento")
    sidebar_nav_button("Hot now", "Hot now")
    sidebar_nav_button("Data quality", "Data quality")

    creators_active = st.session_state["nav_page"] == "Creators"
    creators_open = st.session_state["creators_menu_open"] or creators_active
    if st.button(
        "Criadores",
        use_container_width=True,
        key="nav-creators-toggle",
        type="primary" if creators_open else "secondary",
    ):
        st.session_state["creators_menu_open"] = not creators_open
        st.session_state["nav_page"] = "Creators"
        if st.session_state["creators_menu_open"] and st.session_state["creators_subpage"] not in {"Visao geral", "Criador individual"}:
            st.session_state["creators_subpage"] = "Visao geral"
        st.rerun()

    if creators_open:
        st.markdown('<div class="sidebar-nav-spacer"></div>', unsafe_allow_html=True)
        child_indent = st.columns([0.12, 0.88])
        with child_indent[0]:
            st.write("")
        with child_indent[1]:
            sidebar_nav_button("Visao geral", "Creators", "Visao geral")
        child_indent = st.columns([0.12, 0.88])
        with child_indent[0]:
            st.write("")
        with child_indent[1]:
            sidebar_nav_button("Criador individual", "Creators", "Criador individual")

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
creators_subpage = st.session_state.get("creators_subpage", "Visao geral")
cadastro_subpage = st.session_state.get("cadastro_subpage", "Criadores")

if page == "Overview":
    render_overview()
elif page == "Creators":
    if creators_subpage == "Criador individual":
        render_creator_detail_page()
    else:
        render_creator_overview_page()
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
