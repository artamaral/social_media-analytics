import hashlib
import importlib.util
from html import escape
from datetime import date
from pathlib import Path
import time
from typing import Any
import unicodedata
import re

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import requests
import streamlit as st


CREATOR_WEEKLY_ACTIVITY_CUTOFF = pd.Timestamp("2026-05-04")
OVERVIEW_RECENT_ACTIVITY_WINDOW_WEEKS = 8


def trace_startup(message: str) -> None:
    print(f"[streamlit-startup] {message}", flush=True)


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
            --positive: #2f9e62;
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
            border-radius: 6px;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            background: var(--accent);
            color: #ffffff;
            font-size: 0;
            font-weight: 900;
            flex: 0 0 auto;
            box-shadow: inset 0 0 0 1px rgba(0, 0, 0, 0.12);
        }

        .metric-picto svg {
            width: 68%;
            height: 68%;
            display: block;
            fill: none;
            stroke: currentColor;
            stroke-width: 2.4;
            stroke-linecap: round;
            stroke-linejoin: round;
        }

        .metric-picto .icon-fill {
            fill: currentColor;
            stroke: none;
        }

        .metric-picto-text {
            font-size: 1.25rem;
            line-height: 1;
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
            font-size: 1.16rem;
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
            min-height: 136px;
        }

        .creator-kpi-grid .metric-card-header {
            display: flex;
            align-items: center;
            min-height: 2.25rem;
            padding: 0.55rem 0.7rem;
            font-size: 1rem;
            line-height: 1.05;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: clip;
        }

        .creator-kpi-grid .metric-card-body {
            padding: 0.9rem 0.6rem;
        }

        .creator-kpi-grid .metric-value {
            font-size: clamp(2rem, 2.05vw, 2.9rem);
            gap: 0.6rem;
            min-width: 0;
        }

        .creator-kpi-grid .metric-value span:first-child {
            min-width: 0;
            overflow-wrap: anywhere;
            white-space: nowrap;
        }

        .creator-overview-kpi-grid {
            display: grid;
            grid-template-columns: repeat(3, minmax(0, 1fr));
            gap: 1rem;
            margin-top: 0.75rem;
            margin-bottom: 1.25rem;
        }

        .creator-overview-kpi-grid .metric-card {
            min-height: 118px;
        }

        .creator-overview-kpi-grid .metric-card-header {
            font-size: 1.05rem;
            padding: 0.72rem 0.82rem;
            line-height: 1.05;
        }

        .creator-overview-kpi-grid .metric-card-body {
            padding: 0.95rem 1rem;
        }

        .creator-overview-kpi-grid .metric-caption {
            display: none;
        }

        .creator-kpi-grid .metric-picto {
            width: 46px;
            height: 46px;
            font-size: 0.92rem;
        }

        .creator-kpi-grid .metric-caption {
            font-size: 0.71rem;
            margin-top: 0.55rem;
        }

        .creator-kpi-grid.weekly-grid {
            margin-top: 0.25rem;
        }

        .overview-recent-head {
            display: flex;
            align-items: flex-end;
            justify-content: space-between;
            gap: 1rem;
            margin-top: 0.9rem;
            margin-bottom: 0.25rem;
        }

        .overview-recent-copy {
            min-width: 0;
        }

        .overview-recent-subtitle {
            color: var(--muted);
            font-size: 0.9rem;
            font-weight: 700;
            line-height: 1.25;
            margin-bottom: 0.55rem;
        }

        .overview-recent-kpi-grid {
            grid-template-columns: 1fr;
            gap: 0.85rem;
            margin-top: 0;
            margin-bottom: 0;
        }

        .overview-recent-kpi-grid .metric-card {
            min-height: 140px;
        }

        .overview-fenabrave-grid {
            display: grid;
            grid-template-columns: repeat(5, minmax(0, 1fr));
            gap: 0.75rem;
            margin-top: 0.75rem;
            margin-bottom: 0.25rem;
        }

        .overview-fenabrave-grid .metric-card {
            min-height: 126px;
        }

        .overview-fenabrave-grid .metric-card-header {
            font-size: 0.74rem;
            padding: 0.65rem 0.75rem;
        }

        .overview-fenabrave-grid .metric-card-body {
            padding: 0.85rem 0.9rem;
        }

        .overview-fenabrave-grid .metric-value {
            font-size: clamp(1.45rem, 1.55vw, 2rem);
            gap: 0.5rem;
        }

        .overview-fenabrave-grid .metric-picto {
            width: 40px;
            height: 40px;
        }

        .overview-fenabrave-grid .metric-caption {
            font-size: 0.68rem;
            margin-top: 0.45rem;
        }

        @media (max-width: 1320px) {
            .creator-kpi-grid {
                grid-template-columns: repeat(3, minmax(0, 1fr));
            }

            .dq-kpi-grid.dq-kpi-grid-third {
                grid-template-columns: repeat(2, minmax(0, 1fr));
            }

            .overview-fenabrave-grid {
                grid-template-columns: repeat(3, minmax(0, 1fr));
            }
        }

        @media (max-width: 900px) {
            .creator-kpi-grid {
                grid-template-columns: repeat(2, minmax(0, 1fr));
            }

            .dq-kpi-grid,
            .dq-kpi-grid.dq-kpi-grid-third {
                grid-template-columns: repeat(1, minmax(0, 1fr));
            }

            .overview-recent-head {
                display: block;
            }

            .overview-fenabrave-grid {
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

        .dq-kpi-grid.dq-kpi-grid-third {
            grid-template-columns: repeat(3, minmax(0, 1fr));
        }

        .dq-kpi-card {
            background: var(--card-dark);
            color: var(--text);
            border-radius: 8px;
            border: 1px solid rgba(255, 255, 255, 0.06);
            border-top: 4px solid var(--accent);
            padding: 0.85rem 0.9rem 0.9rem;
            min-height: 220px;
            overflow: hidden;
        }

        .dq-kpi-title {
            font-size: 1.28rem;
            font-weight: 900;
            text-transform: uppercase;
            letter-spacing: 0;
            line-height: 1.1;
            white-space: normal;
            overflow-wrap: anywhere;
            min-height: 2.55rem;
        }

        .dq-kpi-value {
            font-size: 2.1rem;
            line-height: 1.05;
            font-weight: 900;
            margin-top: 0.35rem;
        }

        .dq-kpi-subtitle {
            margin-top: 0.3rem;
            color: var(--muted);
            font-size: 0.88rem;
            font-weight: 700;
            line-height: 1.2;
            overflow-wrap: anywhere;
        }

        .dq-chip-row {
            display: flex;
            flex-wrap: wrap;
            gap: 0.45rem;
            margin-top: 0.7rem;
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

        .creator-ranking-toolbar {
            display: flex;
            align-items: center;
            gap: 0.6rem;
            margin-top: 0.75rem;
            margin-bottom: 0.15rem;
            flex-wrap: wrap;
        }

        .creator-ranking-toolbar-label {
            color: var(--muted);
            font-size: 0.82rem;
            font-weight: 800;
            text-transform: uppercase;
        }

        .creator-ranking-item {
            display: grid;
            grid-template-columns: minmax(0, 2fr) minmax(110px, 0.7fr) minmax(120px, 0.85fr) minmax(120px, 0.9fr) minmax(110px, 0.75fr);
            gap: 0.85rem;
            align-items: center;
            background: rgba(255, 255, 255, 0.03);
            border: 1px solid rgba(255, 255, 255, 0.06);
            border-radius: 8px;
            padding: 0.85rem 0.9rem;
        }

        .creator-ranking-main {
            display: grid;
            grid-template-columns: 52px minmax(0, 1fr);
            gap: 0.85rem;
            align-items: center;
            min-width: 0;
        }

        .creator-ranking-avatar {
            width: 52px;
            height: 52px;
            border-radius: 999px;
            overflow: hidden;
            background: linear-gradient(135deg, rgba(255, 128, 105, 0.28), rgba(255, 255, 255, 0.05));
            border: 1px solid rgba(255, 255, 255, 0.08);
            display: inline-flex;
            align-items: center;
            justify-content: center;
            color: var(--text);
            font-size: 1rem;
            font-weight: 900;
            text-transform: uppercase;
            flex: 0 0 auto;
        }

        .creator-ranking-avatar img {
            width: 100%;
            height: 100%;
            object-fit: cover;
            display: block;
        }

        .creator-ranking-avatar-link {
            display: inline-flex;
            border-radius: 999px;
            text-decoration: none;
            flex: 0 0 auto;
        }

        .creator-ranking-avatar-link:hover .creator-ranking-avatar {
            border-color: rgba(255, 128, 105, 0.55);
            box-shadow: 0 0 0 3px rgba(255, 128, 105, 0.14);
        }

        .creator-ranking-copy {
            min-width: 0;
        }

        .creator-ranking-title {
            color: var(--text);
            font-size: 1rem;
            font-weight: 900;
            line-height: 1.15;
            overflow-wrap: anywhere;
        }

        .creator-ranking-title-link {
            color: inherit;
            text-decoration: none;
        }

        .creator-ranking-title-link:hover {
            text-decoration: underline;
            text-decoration-color: var(--accent);
            text-underline-offset: 0.14em;
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


def metric_picto_html(picto: str) -> str:
    icons = {
        "CR": (
            '<svg viewBox="0 0 24 24" aria-hidden="true">'
            '<circle class="icon-fill" cx="9" cy="8" r="4"/>'
            '<path class="icon-fill" d="M2.8 20c.7-4.2 3.1-6.3 6.2-6.3s5.5 2.1 6.2 6.3z"/>'
            '<circle class="icon-fill" cx="17" cy="10" r="3"/>'
            '<path class="icon-fill" d="M14.6 20c.3-2.4 1.5-4.1 3.6-4.1 1.7 0 3 1.3 3.5 4.1z"/>'
            "</svg>"
        ),
        "SG": (
            '<svg viewBox="0 0 24 24" aria-hidden="true">'
            '<circle class="icon-fill" cx="9" cy="8" r="4"/>'
            '<path class="icon-fill" d="M2.8 20c.7-4.2 3.1-6.3 6.2-6.3s5.5 2.1 6.2 6.3z"/>'
            '<circle class="icon-fill" cx="17" cy="10" r="3"/>'
            '<path class="icon-fill" d="M14.6 20c.3-2.4 1.5-4.1 3.6-4.1 1.7 0 3 1.3 3.5 4.1z"/>'
            "</svg>"
        ),
        "RK": (
            '<svg viewBox="0 0 24 24" aria-hidden="true">'
            '<path d="M3 13h4l2.2-5 4 9 2.2-4H21"/>'
            '<circle class="icon-fill" cx="7" cy="13" r="1.8"/>'
            '<circle class="icon-fill" cx="13.2" cy="17" r="1.8"/>'
            '<circle class="icon-fill" cx="17.2" cy="13" r="1.8"/>'
            "</svg>"
        ),
        "VD": (
            '<svg viewBox="0 0 24 24" aria-hidden="true">'
            '<rect x="3" y="6" width="18" height="12" rx="2.2"/>'
            '<path class="icon-fill" d="M10 9.1v5.8l5-2.9z"/>'
            "</svg>"
        ),
        "VW": (
            '<svg viewBox="0 0 24 24" aria-hidden="true">'
            '<rect x="4" y="3" width="16" height="18" rx="2"/>'
            '<path d="M8 3v18M16 3v18M4 8h16M4 16h16"/>'
            "</svg>"
        ),
        "LK": (
            '<svg viewBox="0 0 24 24" aria-hidden="true">'
            '<path class="icon-fill" d="M8.2 20H5a2 2 0 0 1-2-2v-6a2 2 0 0 1 2-2h3.2z"/>'
            '<path class="icon-fill" d="M9.6 20h7.6c1 0 1.8-.7 2-1.6l1.5-6.1c.3-1.2-.6-2.3-1.9-2.3h-4.4l.7-3.4c.2-1.2-.7-2.3-1.9-2.3h-.5L8.2 10v9c.3.6.8 1 1.4 1z"/>'
            "</svg>"
        ),
        "CM": (
            '<svg viewBox="0 0 24 24" aria-hidden="true">'
            '<path class="icon-fill" d="M4 5h13a3 3 0 0 1 3 3v5a3 3 0 0 1-3 3h-5l-5 4v-4H4a3 3 0 0 1-3-3V8a3 3 0 0 1 3-3z"/>'
            '<path class="icon-fill" d="M8 3h10a3 3 0 0 1 3 3v6.2c-.6-1-1.7-1.7-3-1.7H8z" opacity=".72"/>'
            "</svg>"
        ),
        "SH": (
            '<svg viewBox="0 0 24 24" aria-hidden="true">'
            '<circle class="icon-fill" cx="6" cy="12" r="3"/>'
            '<circle class="icon-fill" cx="18" cy="6" r="3"/>'
            '<circle class="icon-fill" cx="18" cy="18" r="3"/>'
            '<path d="M8.8 10.8l6.4-3.6M8.8 13.2l6.4 3.6"/>'
            "</svg>"
        ),
        "AV": (
            '<svg viewBox="0 0 24 24" aria-hidden="true">'
            '<path class="icon-fill" d="M4 20h3V9H4zM10.5 20h3V4h-3zM17 20h3v-8h-3z"/>'
            "</svg>"
        ),
        "SC": (
            '<svg viewBox="0 0 24 24" aria-hidden="true">'
            '<path d="M4 16h4l3-5 3.2 6 2.2-4H20"/>'
            '<path class="icon-fill" d="M18.2 4.4l.8 1.7 1.8.2-1.3 1.2.3 1.8-1.6-.9-1.6.9.3-1.8-1.3-1.2 1.8-.2z"/>'
            '<circle class="icon-fill" cx="8" cy="16" r="1.6"/>'
            '<circle class="icon-fill" cx="14.2" cy="17" r="1.6"/>'
            "</svg>"
        ),
        "VA": (
            '<svg viewBox="0 0 24 24" aria-hidden="true">'
            '<path d="M5 16a7 7 0 0 1 14 0"/>'
            '<path d="M12 16l4.8-4.8"/>'
            '<circle class="icon-fill" cx="12" cy="16" r="1.9"/>'
            '<path d="M8 12.4h.01M12 10h.01M16 12.4h.01"/>'
            "</svg>"
        ),
        "VP": (
            '<svg viewBox="0 0 24 24" aria-hidden="true">'
            '<path d="M5 16a7 7 0 0 1 14 0"/>'
            '<path d="M12 16l-3.8-2.6"/>'
            '<circle class="icon-fill" cx="12" cy="16" r="1.9"/>'
            '<path d="M7.2 10.9l1.2 1.2M16.8 10.9l-1.2 1.2" opacity=".65"/>'
            "</svg>"
        ),
        "AC": (
            '<svg viewBox="0 0 24 24" aria-hidden="true">'
            '<path class="icon-fill" d="M4 20h3v-5H4zM10 20h3v-8H10zM16 20h3v-11h-3z"/>'
            '<path d="M5.5 10.5 10 8l3.3 2.2L20 4.5"/>'
            '<path d="M16.8 4.5H20v3.2"/>'
            "</svg>"
        ),
        "DV": (
            '<svg viewBox="0 0 24 24" aria-hidden="true">'
            '<path d="M2.5 12s3.6-5.5 9.5-5.5 9.5 5.5 9.5 5.5-3.6 5.5-9.5 5.5S2.5 12 2.5 12z"/>'
            '<circle class="icon-fill" cx="12" cy="12" r="2.3"/>'
            '<path d="M18.5 5.5v5M16 8h5"/>'
            "</svg>"
        ),
    }
    return icons.get(picto, f'<span class="metric-picto-text">{escape(picto)}</span>')


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
    picto_html = metric_picto_html(picto)
    return (
        '<div class="metric-card">'
        f'<div class="metric-card-header">{escape(title)}</div>'
        '<div class="metric-card-body">'
        '<div class="metric-value">'
        f"<span>{escape(value)}</span>"
        f'<span class="metric-picto"{picto_style}>{picto_html}</span>'
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


def header_pill_icon_html(picto: str, label: str) -> str:
    return (
        f'<span class="youtube-best-head-icon" title="{escape(label)}" aria-label="{escape(label)}">'
        f"{metric_picto_html(picto)}"
        "</span>"
    )


def calendar_header_icon_html(label: str) -> str:
    return (
        f'<span class="youtube-best-head-icon" title="{escape(label)}" aria-label="{escape(label)}">'
        '<svg viewBox="0 0 24 24" aria-hidden="true">'
        '<rect x="3" y="5" width="18" height="16" rx="2"></rect>'
        '<path d="M8 3v4M16 3v4M3 9h18"></path>'
        '<path class="icon-fill" d="M7 12h3v3H7z"></path>'
        "</svg>"
        "</span>"
    )


def metric_card_grid(cards: list[str], class_name: str = "fenabrave-card-grid") -> None:
    st.markdown(
        f'<div class="{escape(class_name)}">' + "".join(cards) + "</div>",
        unsafe_allow_html=True,
    )


def dq_kpi_card(
    title: str,
    value: str,
    subtitle: str,
    accent_color: str,
    chips: list[str],
    footer_html: str = "",
) -> str:
    chip_html = "".join(chips)
    return (
        f'<div class="dq-kpi-card" style="border-top-color: {escape(accent_color)};">'
        f'<div class="dq-kpi-title">{escape(title)}</div>'
        f'<div class="dq-kpi-value">{escape(value)}</div>'
        f'<div class="dq-kpi-subtitle">{escape(subtitle)}</div>'
        f'<div class="dq-chip-row">{chip_html}</div>'
        f"{footer_html}"
        "</div>"
    )


def dq_chip(label: str, amount: str, tone: str = "neutral") -> str:
    return f'<span class="dq-chip {escape(tone)}">{escape(label)} <strong>{escape(amount)}</strong></span>'


def humanize_queue_band(value: Any) -> str:
    text = str(value or "--").strip()
    if not text or text == "--":
        return "--"
    return text.replace("_", " ").title()


def queue_band_sort_value(value: Any) -> tuple[int, str]:
    text = str(value or "").strip()
    try:
        return (0, f"{int(text):04d}")
    except ValueError:
        return (1, text.lower())


def queue_band_title(value: Any) -> str:
    text = str(value or "--").strip()
    if not text or text == "--":
        return "Banda --"
    return f"Banda {text}"


def queue_staleness_tone(value: float) -> str:
    if value < 3:
        return "ok-green"
    if value < 4:
        return "alert-yellow"
    return "alert-red"


def queue_overdue_label(overdue_count: int, total_posts: int) -> str:
    pct = (overdue_count / total_posts * 100) if total_posts else 0.0
    return f"{format_int(overdue_count)} | {int(round(pct))}%"


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


def combine_worker_status(*status_codes: str) -> str:
    normalized = [str(code or "neutral").lower() for code in status_codes]
    if any(code in {"nok", "danger"} for code in normalized):
        return "nok"
    if any(code in {"atencao", "warning"} for code in normalized):
        return "atencao"
    if any(code == "ok" for code in normalized):
        return "ok"
    return "neutral"


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


def normalize_fenabrave_reference_period(value: Any) -> date:
    timestamp = pd.Timestamp(value)
    first_day_of_month = timestamp.to_period("M").to_timestamp().date()
    return first_day_of_month


def get_default_fenabrave_reference_period() -> date:
    today = pd.Timestamp.today().normalize()
    return (today.to_period("M").to_timestamp() - pd.offsets.MonthBegin(1)).date()


def is_supabase_configured() -> bool:
    return bool(get_secret("SUPABASE_URL") and get_secret("SUPABASE_ANON_KEY"))


def is_supabase_upload_configured() -> bool:
    return bool(get_secret("SUPABASE_URL") and get_secret("SUPABASE_SERVICE_ROLE_KEY"))


def is_creator_onboarding_configured() -> bool:
    return bool(get_secret("CREATOR_ONBOARDING_WORKER_URL") and get_secret("ONBOARDING_WORKER_TOKEN"))


def get_supabase_client():
    from supabase import create_client

    supabase_url = get_secret("SUPABASE_URL")
    supabase_anon_key = get_secret("SUPABASE_ANON_KEY")
    if not supabase_url or not supabase_anon_key:
        return None
    return create_client(supabase_url, supabase_anon_key)


def get_supabase_upload_client():
    from supabase import create_client

    supabase_url = get_secret("SUPABASE_URL")
    supabase_service_role_key = get_secret("SUPABASE_SERVICE_ROLE_KEY")
    if not supabase_url or not supabase_service_role_key:
        return None
    return create_client(supabase_url, supabase_service_role_key)


@st.cache_resource(show_spinner=False)
def load_fenabrave_ingestion_module():
    module_path = Path(__file__).resolve().parents[1] / "scripts" / "fenabrave_ingestion" / "ingest_fenabrave_phase1.py"
    spec = importlib.util.spec_from_file_location("fenabrave_phase1_module", module_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Nao foi possivel carregar o modulo Fenabrave em {module_path}.")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


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
        trace_startup(f"load_view_rows skipped: {view_name} (no client)")
        return []

    started_at = time.perf_counter()
    trace_startup(f"load_view_rows start: {view_name}")
    response = client.table(view_name).select("*").execute()
    rows = response.data or []
    trace_startup(f"load_view_rows end: {view_name} rows={len(rows)} elapsed={time.perf_counter() - started_at:.2f}s")
    return rows


@st.cache_data(ttl=300, show_spinner=False)
def load_filtered_rows(
    source_name: str,
    filters: tuple[tuple[str, Any], ...] = (),
    order_by: str | None = None,
    order_desc: bool = False,
    order_nulls_first: bool | None = None,
    limit: int | None = None,
) -> list[dict[str, Any]]:
    client = get_supabase_client()
    if client is None:
        trace_startup(f"load_filtered_rows skipped: {source_name} (no client)")
        return []

    started_at = time.perf_counter()
    trace_startup(
        f"load_filtered_rows start: {source_name} filters={len(filters)} order_by={order_by} limit={limit}"
    )
    query = client.table(source_name).select("*")
    for column_name, column_value in filters:
        query = query.eq(column_name, column_value)
    if order_by:
        order_kwargs: dict[str, Any] = {"desc": order_desc}
        if order_nulls_first is not None:
            order_kwargs["nullsfirst"] = order_nulls_first
        query = query.order(order_by, **order_kwargs)
    if limit is not None:
        query = query.limit(limit)
    response = query.execute()
    rows = response.data or []
    trace_startup(f"load_filtered_rows end: {source_name} rows={len(rows)} elapsed={time.perf_counter() - started_at:.2f}s")
    return rows


def get_single_row_view(view_name: str) -> tuple[dict[str, Any] | None, str | None]:
    if not is_supabase_configured():
        trace_startup(f"get_single_row_view skipped: {view_name} (not configured)")
        return None, "Supabase ainda nao configurado. Adicione SUPABASE_URL e SUPABASE_ANON_KEY nos secrets."

    try:
        trace_startup(f"get_single_row_view start: {view_name}")
        row = load_single_row_view(view_name)
        trace_startup(f"get_single_row_view end: {view_name} found={row is not None}")
        return row, None
    except Exception as exc:
        return None, f"Falha ao consultar {view_name}: {exc}"


def get_view_rows(view_name: str) -> tuple[list[dict[str, Any]], str | None]:
    if not is_supabase_configured():
        trace_startup(f"get_view_rows skipped: {view_name} (not configured)")
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
    order_nulls_first: bool | None = None,
    limit: int | None = None,
) -> tuple[list[dict[str, Any]], str | None]:
    if not is_supabase_configured():
        trace_startup(f"get_filtered_rows skipped: {source_name} (not configured)")
        return [], "Supabase ainda nao configurado. Adicione SUPABASE_URL e SUPABASE_ANON_KEY nos secrets."

    try:
        return load_filtered_rows(source_name, filters, order_by, order_desc, order_nulls_first, limit), None
    except Exception as exc:
        return [], f"Falha ao consultar {source_name}: {exc}"


@st.cache_data(ttl=300, show_spinner=False)
def load_creator_posts_rollup(
    creator_ids: tuple[int, ...],
    video_type: str,
) -> dict[int, dict[str, Any]]:
    client = get_supabase_client()
    if client is None or not creator_ids:
        return {}

    page_size = 1000
    creator_batch_size = 25
    rollup: dict[int, dict[str, Any]] = {}

    for start in range(0, len(creator_ids), creator_batch_size):
        creator_batch = list(creator_ids[start:start + creator_batch_size])
        offset = 0

        while True:
            query = (
                client.table("posts")
                .select("creator_id,views,likes,comments")
                .in_("creator_id", creator_batch)
                .eq("video_type", video_type)
                .range(offset, offset + page_size - 1)
            )
            response = query.execute()
            rows = response.data or []

            for row in rows:
                creator_id = nullable_int(row.get("creator_id"))
                if creator_id is None:
                    continue
                current = rollup.setdefault(
                    creator_id,
                    {
                        "post_count": 0,
                        "total_views": 0,
                        "total_likes": 0,
                        "total_comments": 0,
                    },
                )
                current["post_count"] += 1
                current["total_views"] += nullable_int(row.get("views")) or 0
                current["total_likes"] += nullable_int(row.get("likes")) or 0
                current["total_comments"] += nullable_int(row.get("comments")) or 0

            if len(rows) < page_size:
                break

            offset += page_size

    for current in rollup.values():
        total_views = current["total_views"]
        total_likes = current["total_likes"]
        total_comments = current["total_comments"]
        current["engagement_rate_pct"] = round(((total_likes + total_comments) / total_views) * 100, 4) if total_views > 0 else 0.0

    return rollup


def get_creator_posts_rollup(
    creator_ids: list[int],
    video_type: str,
) -> tuple[dict[int, dict[str, Any]], str | None]:
    if video_type not in {"long", "short"}:
        return {}, None

    try:
        normalized_ids = tuple(sorted({creator_id for creator_id in creator_ids if creator_id}))
        return load_creator_posts_rollup(normalized_ids, video_type), None
    except Exception as exc:
        return {}, f"Falha ao segmentar posts por tipo de video: {exc}"


def normalize_name_for_intake(value: str) -> str:
    without_accents = unicodedata.normalize("NFKD", value.strip())
    ascii_value = "".join(char for char in without_accents if not unicodedata.combining(char))
    return ascii_value.lower().strip()


def clear_supabase_data_cache() -> None:
    load_single_row_view.clear()
    load_view_rows.clear()
    load_filtered_rows.clear()
    load_sub_niches_for_intake.clear()
    load_fenabrave_preview_from_storage.clear()


CREATOR_INTAKE_FORM_DEFAULTS: dict[str, Any] = {
    "creator_intake_raw_name": "Auto Mercado Brasil",
    "creator_intake_creator_type": "mid-tier",
    "creator_intake_platform": "youtube",
    "creator_intake_username": "@automercadobrasil",
    "creator_intake_channel_id": "UC1234567890ABCDE",
    "creator_intake_followers": 185000,
    "creator_intake_niche": "automotivo",
    "creator_intake_selected_sub_niches": [],
    "creator_intake_taxonomy_request": "",
    "creator_intake_notes": "",
}


def ensure_creator_intake_form_defaults(sub_niche_names: list[str]) -> None:
    for key, default_value in CREATOR_INTAKE_FORM_DEFAULTS.items():
        if key not in st.session_state:
            st.session_state[key] = list(default_value) if isinstance(default_value, list) else default_value
    if not st.session_state.get("creator_intake_selected_sub_niches") and sub_niche_names:
        st.session_state["creator_intake_selected_sub_niches"] = [sub_niche_names[0]]


def apply_creator_intake_form_reset(sub_niche_names: list[str]) -> None:
    st.session_state["creator_intake_raw_name"] = ""
    st.session_state["creator_intake_creator_type"] = "mid-tier"
    st.session_state["creator_intake_platform"] = "youtube"
    st.session_state["creator_intake_username"] = ""
    st.session_state["creator_intake_channel_id"] = ""
    st.session_state["creator_intake_followers"] = 0
    st.session_state["creator_intake_niche"] = "automotivo"
    st.session_state["creator_intake_selected_sub_niches"] = []
    st.session_state["creator_intake_taxonomy_request"] = ""
    st.session_state["creator_intake_notes"] = ""

    for key in [
        "creator_intake_entity_matches",
        "creator_intake_entity_error",
        "creator_intake_entity_checked_name",
        "creator_intake_channel_matches",
        "creator_intake_channel_error",
        "creator_intake_channel_checked_value",
        "creator_intake_last_rows",
    ]:
        st.session_state[key] = [] if key.endswith("_matches") or key.endswith("_rows") else None

    st.session_state["creator_intake_reset_pending"] = False


def schedule_creator_intake_form_reset() -> None:
    st.session_state["creator_intake_reset_pending"] = True


def build_creator_created_summary(
    creator_row: dict[str, Any],
    resolved_entity: dict[str, Any] | None,
    selected_sub_niches: list[str],
) -> dict[str, Any]:
    creator_id = int(creator_row.get("creator_id") or 0)
    entity_id = int(creator_row.get("entity_id") or resolved_entity.get("entity_id") or 0) if resolved_entity else int(creator_row.get("entity_id") or 0)
    return {
        "creator_id": creator_id,
        "entity_id": entity_id,
        "entity_name": str(creator_row.get("entity_name") or (resolved_entity or {}).get("entity_name") or "--"),
        "platform": str(creator_row.get("platform") or "--"),
        "username": str(creator_row.get("username") or "--"),
        "channel_id": str(creator_row.get("channel_id") or "--"),
        "followers": int(creator_row.get("followers") or 0),
        "creator_type": str(creator_row.get("creator_type") or "--"),
        "sub_niches": ", ".join(selected_sub_niches) if selected_sub_niches else "--",
    }


def call_supabase_rpc(function_name: str, params: dict[str, Any] | None = None) -> tuple[list[dict[str, Any]], str | None]:
    if not is_supabase_configured():
        return [], "Supabase ainda nao configurado. Adicione SUPABASE_URL e SUPABASE_ANON_KEY nos secrets."

    client = get_supabase_client()
    if client is None:
        return [], "Cliente Supabase indisponivel."

    try:
        response = client.rpc(function_name, params or {}).execute()
        return response.data or [], None
    except Exception as exc:
        return [], f"Falha ao executar {function_name}: {exc}"


def list_fenabrave_source_files(limit: int = 12) -> tuple[list[dict[str, Any]], str | None]:
    return call_supabase_rpc("list_fenabrave_source_files", {"p_limit": limit})


def upsert_fenabrave_source_file(payload: dict[str, Any]) -> tuple[dict[str, Any] | None, str | None]:
    rows, error = call_supabase_rpc("upsert_fenabrave_source_file", payload)
    if error:
        return None, error
    if not rows:
        return None, "Nenhum registro retornado por upsert_fenabrave_source_file."
    clear_supabase_data_cache()
    return rows[0], None


def build_fenabrave_upsert_payload(
    record: dict[str, Any],
    extraction_status: str,
    extraction_notes: str | None = None,
) -> dict[str, Any]:
    normalized_reference_period = normalize_fenabrave_reference_period(record.get("reference_period"))
    return {
        "p_reference_period": pd.Timestamp(normalized_reference_period).strftime("%Y-%m-%d"),
        "p_source_url": str(record.get("source_url") or ""),
        "p_source_page_url": str(record.get("source_page_url") or ""),
        "p_storage_bucket": str(record.get("storage_bucket") or ""),
        "p_storage_path": str(record.get("storage_path") or ""),
        "p_original_filename": str(record.get("original_filename") or ""),
        "p_file_size_bytes": nullable_int(record.get("file_size_bytes")),
        "p_sha256": str(record.get("sha256") or "") or None,
        "p_extraction_status": extraction_status,
        "p_extraction_method": str(record.get("extraction_method") or "pdf_table_extraction"),
        "p_extraction_notes": extraction_notes if extraction_notes is not None else record.get("extraction_notes"),
    }


def normalize_fenabrave_filename(filename: str | None, reference_period: date) -> str:
    raw_name = str(filename or "").strip()
    base_name = raw_name.replace("\\", "/").split("/")[-1]
    safe_name = re.sub(r"[^A-Za-z0-9._-]+", "_", base_name).strip("._")
    if safe_name.lower().endswith(".pdf"):
        return safe_name
    if safe_name:
        return f"{safe_name}.pdf"
    return pd.Timestamp(reference_period).strftime("%Y_%m_fenabrave.pdf")


def build_fenabrave_storage_path(reference_period: date, filename: str | None) -> str:
    period_prefix = pd.Timestamp(reference_period).strftime("%Y/%m")
    normalized_filename = normalize_fenabrave_filename(filename, reference_period)
    return f"fenabrave/{period_prefix}/{normalized_filename}"


def upload_fenabrave_pdf_to_storage(
    bucket: str,
    storage_path: str,
    pdf_bytes: bytes,
) -> tuple[dict[str, Any] | None, str | None]:
    if not is_supabase_upload_configured():
        return None, (
            "Upload ao Storage ainda nao configurado. "
            "Adicione SUPABASE_URL e SUPABASE_SERVICE_ROLE_KEY nos secrets do Streamlit."
        )

    client = get_supabase_upload_client()
    if client is None:
        return None, "Cliente Supabase de upload indisponivel."

    try:
        response = client.storage.from_(bucket).upload(
            storage_path,
            pdf_bytes,
            {"content-type": "application/pdf", "upsert": "true"},
        )
        payload = {"storage_path": storage_path, "bucket": bucket}
        if isinstance(response, dict):
            payload.update(response)
        elif hasattr(response, "model_dump"):
            payload.update(response.model_dump())
        elif hasattr(response, "dict"):
            payload.update(response.dict())
        elif hasattr(response, "json"):
            try:
                response_payload = response.json()
                if isinstance(response_payload, dict):
                    payload.update(response_payload)
            except Exception:
                pass
        elif hasattr(response, "__dict__"):
            payload.update(
                {
                    key: value
                    for key, value in vars(response).items()
                    if not key.startswith("_")
                }
            )
        clear_supabase_data_cache()
        return payload, None
    except Exception as exc:
        return None, f"Falha ao enviar PDF para o Storage: {exc}"


def create_fenabrave_signed_url(
    bucket: str,
    storage_path: str,
    expires_in_seconds: int = 1800,
) -> tuple[str | None, str | None]:
    if not is_supabase_upload_configured():
        return None, (
            "Abertura segura do PDF ainda nao configurada. "
            "Adicione SUPABASE_URL e SUPABASE_SERVICE_ROLE_KEY nos secrets do Streamlit."
        )

    client = get_supabase_upload_client()
    if client is None:
        return None, "Cliente Supabase de upload indisponivel."

    try:
        response = client.storage.from_(bucket).create_signed_url(storage_path, expires_in_seconds)
        signed_url = response.get("signedURL") or response.get("signed_url")
        if not signed_url:
            return None, "Nao foi possivel gerar a signed URL do PDF."
        return str(signed_url), None
    except Exception as exc:
        return None, f"Falha ao gerar link seguro do PDF: {exc}"


@st.cache_data(ttl=300, show_spinner=False)
def load_fenabrave_preview_from_storage(
    source_file_id: int,
    reference_period_label: str,
    storage_bucket: str,
    storage_path: str,
) -> dict[str, Any]:
    if not is_supabase_upload_configured():
        raise RuntimeError(
            "Preview operacional indisponivel: adicione SUPABASE_URL e SUPABASE_SERVICE_ROLE_KEY nos secrets do Streamlit."
        )

    module = load_fenabrave_ingestion_module()
    base_url = module.normalize_supabase_url(get_secret("SUPABASE_URL"))
    supabase_service_role_key = get_secret("SUPABASE_SERVICE_ROLE_KEY")
    if not base_url or not supabase_service_role_key:
        raise RuntimeError("Credenciais de upload/preview indisponiveis.")

    pdf_bytes = module.download_pdf_from_storage(base_url, supabase_service_role_key, storage_bucket, storage_path)
    raw_rows = module.extract_first_page_table(pdf_bytes)
    normalized_rows = module.normalize_rows(raw_rows, source_file_id, reference_period_label)
    checks = module.validate_normalized_rows(normalized_rows)
    item1_raw_rows = module.extract_item1_model_rankings(pdf_bytes)
    item1_rows = module.normalize_item1_rows(item1_raw_rows, source_file_id, reference_period_label)
    item1_checks = module.validate_item1_rows(item1_rows, normalized_rows)
    item2_raw_rows = module.extract_item2_model_rankings(pdf_bytes)
    item2_rows = module.normalize_item2_rows(item2_raw_rows, source_file_id, reference_period_label)
    item2_checks = module.validate_item2_rows(item2_rows, item1_rows)
    item3_raw_rows = module.extract_item3_brand_rankings(pdf_bytes)
    item3_rows = module.normalize_item3_rows(item3_raw_rows, source_file_id, reference_period_label)
    item3_checks = module.validate_item3_rows(item3_rows)
    item4_raw_rows = module.extract_item4_brand_rankings(pdf_bytes)
    item4_rows = module.normalize_item4_rows(item4_raw_rows, source_file_id, reference_period_label)
    item4_checks = module.validate_item4_rows(item4_rows, item3_rows)
    item5_raw_rows = module.extract_item5_subsegment_shares(pdf_bytes)
    item5_rows = module.normalize_item5_rows(item5_raw_rows, source_file_id, reference_period_label)
    item5_checks = module.validate_item5_rows(item5_rows, item5_raw_rows)
    item6_raw_rows = module.extract_item6_electrified_market(pdf_bytes)
    item6_rows = module.normalize_item6_rows(item6_raw_rows, source_file_id, reference_period_label)
    item6_checks = module.validate_item6_rows(item6_rows)
    item7_raw_rows = module.extract_item7_electrified_hybrid_brands(pdf_bytes)
    item7_rows = module.normalize_item7_rows(item7_raw_rows, source_file_id, reference_period_label)
    item7_checks = module.validate_item7_rows(item7_rows, item6_rows)
    item8_raw_rows = module.extract_item8_electrified_electric_brands(pdf_bytes)
    item8_rows = module.normalize_item8_rows(item8_raw_rows, source_file_id, reference_period_label)
    item8_checks = module.validate_item8_rows(item8_rows, item6_rows)
    item11_raw_rows = module.extract_item11_sales_channel_mix(pdf_bytes)
    item11_rows = module.normalize_item11_rows(item11_raw_rows, source_file_id, reference_period_label)
    item11_checks = module.validate_item11_rows(item11_rows)
    item12_raw_rows = module.extract_item12_sales_channel_mix(pdf_bytes)
    item12_rows = module.normalize_item12_rows(item12_raw_rows, source_file_id, reference_period_label)
    item12_checks = module.validate_item12_rows(item12_rows)
    item13_raw_rows = module.extract_item13_brand_share_rankings(pdf_bytes)
    item13_rows = module.normalize_item13_rows(item13_raw_rows, source_file_id, reference_period_label)
    item13_checks = module.validate_item13_rows(item13_rows)
    item14_raw_rows = module.extract_item14_brand_share_rankings(pdf_bytes)
    item14_rows = module.normalize_item14_rows(item14_raw_rows, source_file_id, reference_period_label)
    item14_checks = module.validate_item14_rows(item14_rows, item13_rows)
    item15_raw_rows = module.extract_item15_brand_share_rankings(pdf_bytes)
    item15_rows = module.normalize_item15_rows(item15_raw_rows, source_file_id, reference_period_label)
    item15_checks = module.validate_item15_rows(item15_rows)
    item16_raw_rows = module.extract_item16_brand_share_rankings(pdf_bytes)
    item16_rows = module.normalize_item16_rows(item16_raw_rows, source_file_id, reference_period_label)
    item16_checks = module.validate_item16_rows(item16_rows, item15_rows)
    item17_raw_rows = module.extract_item17_brand_share_rankings(pdf_bytes)
    item17_rows = module.normalize_item17_rows(item17_raw_rows, source_file_id, reference_period_label)
    item17_checks = module.validate_item17_rows(item17_rows)
    item18_raw_rows = module.extract_item18_brand_share_rankings(pdf_bytes)
    item18_rows = module.normalize_item18_rows(item18_raw_rows, source_file_id, reference_period_label)
    item18_checks = module.validate_item18_rows(item18_rows, item17_rows)
    item19_raw_rows = module.extract_item19_model_rankings(pdf_bytes)
    item19_rows = module.normalize_item19_rows(item19_raw_rows, source_file_id, reference_period_label)
    item19_checks = module.validate_item19_rows(item19_rows, normalized_rows)
    item20_raw_rows = module.extract_item20_model_rankings(pdf_bytes)
    item20_rows = module.normalize_item20_rows(item20_raw_rows, source_file_id, reference_period_label)
    item20_checks = module.validate_item20_rows(item20_rows, normalized_rows)
    item21_raw_rows = module.extract_item21_model_rankings(pdf_bytes)
    item21_rows = module.normalize_item21_rows(item21_raw_rows, source_file_id, reference_period_label)
    item21_checks = module.validate_item21_rows(item21_rows, item19_rows)
    item22_raw_rows = module.extract_item22_model_rankings(pdf_bytes)
    item22_rows = module.normalize_item22_rows(item22_raw_rows, source_file_id, reference_period_label)
    item22_checks = module.validate_item22_rows(item22_rows, item20_rows)
    return {
        "pdf_size_bytes": len(pdf_bytes),
        "pdf_sha256": hashlib.sha256(pdf_bytes).hexdigest(),
        "raw_rows": raw_rows,
        "normalized_rows": normalized_rows,
        "checks": checks,
        "item1_raw_rows": item1_raw_rows,
        "item1_rows": item1_rows,
        "item1_checks": item1_checks,
        "item2_raw_rows": item2_raw_rows,
        "item2_rows": item2_rows,
        "item2_checks": item2_checks,
        "item3_raw_rows": item3_raw_rows,
        "item3_rows": item3_rows,
        "item3_checks": item3_checks,
        "item4_raw_rows": item4_raw_rows,
        "item4_rows": item4_rows,
        "item4_checks": item4_checks,
        "item5_raw_rows": item5_raw_rows,
        "item5_rows": item5_rows,
        "item5_checks": item5_checks,
        "item6_raw_rows": item6_raw_rows,
        "item6_rows": item6_rows,
        "item6_checks": item6_checks,
        "item7_raw_rows": item7_raw_rows,
        "item7_rows": item7_rows,
        "item7_checks": item7_checks,
        "item8_raw_rows": item8_raw_rows,
        "item8_rows": item8_rows,
        "item8_checks": item8_checks,
        "item11_raw_rows": item11_raw_rows,
        "item11_rows": item11_rows,
        "item11_checks": item11_checks,
        "item12_raw_rows": item12_raw_rows,
        "item12_rows": item12_rows,
        "item12_checks": item12_checks,
        "item13_raw_rows": item13_raw_rows,
        "item13_rows": item13_rows,
        "item13_checks": item13_checks,
        "item14_raw_rows": item14_raw_rows,
        "item14_rows": item14_rows,
        "item14_checks": item14_checks,
        "item15_raw_rows": item15_raw_rows,
        "item15_rows": item15_rows,
        "item15_checks": item15_checks,
        "item16_raw_rows": item16_raw_rows,
        "item16_rows": item16_rows,
        "item16_checks": item16_checks,
        "item17_raw_rows": item17_raw_rows,
        "item17_rows": item17_rows,
        "item17_checks": item17_checks,
        "item18_raw_rows": item18_raw_rows,
        "item18_rows": item18_rows,
        "item18_checks": item18_checks,
        "item19_raw_rows": item19_raw_rows,
        "item19_rows": item19_rows,
        "item19_checks": item19_checks,
        "item20_raw_rows": item20_raw_rows,
        "item20_rows": item20_rows,
        "item20_checks": item20_checks,
        "item21_raw_rows": item21_raw_rows,
        "item21_rows": item21_rows,
        "item21_checks": item21_checks,
        "item22_raw_rows": item22_raw_rows,
        "item22_rows": item22_rows,
        "item22_checks": item22_checks,
    }


def get_fenabrave_preview_from_storage(record: dict[str, Any] | None) -> tuple[dict[str, Any] | None, str | None]:
    if record is None:
        return None, "Selecione ou registre um periodo Fenabrave antes de gerar o preview."

    source_file_id = nullable_int(record.get("source_file_id"))
    reference_period = record.get("reference_period")
    storage_bucket = str(record.get("storage_bucket") or "").strip()
    storage_path = str(record.get("storage_path") or "").strip()

    if source_file_id is None:
        return None, "Registro Fenabrave sem source_file_id."
    if not reference_period:
        return None, "Registro Fenabrave sem reference_period."
    if not storage_bucket or not storage_path:
        return None, "Registro Fenabrave sem bucket/path do PDF."

    try:
        reference_period_label = pd.Timestamp(normalize_fenabrave_reference_period(reference_period)).strftime("%Y-%m-%d")
        payload = load_fenabrave_preview_from_storage(
            source_file_id,
            reference_period_label,
            storage_bucket,
            storage_path,
        )
        return payload, None
    except Exception as exc:
        return None, f"Falha ao gerar preview operacional: {exc}"


def trigger_creator_onboarding(creator_id: int) -> tuple[dict[str, Any] | None, str | None]:
    worker_url = get_secret("CREATOR_ONBOARDING_WORKER_URL")
    worker_token = get_secret("ONBOARDING_WORKER_TOKEN")

    if not worker_url or not worker_token:
        return None, (
            "Worker de discovery inicial nao configurado. "
            "Adicione CREATOR_ONBOARDING_WORKER_URL e ONBOARDING_WORKER_TOKEN nos secrets."
        )

    try:
        response = requests.post(
            worker_url,
            headers={"x-worker-token": worker_token},
            json={"creator_id": creator_id},
            timeout=90,
        )
    except requests.RequestException as exc:
        return None, f"Falha ao chamar worker de discovery inicial: {exc}"

    try:
        payload = response.json()
    except ValueError:
        payload = {
            "status": "error",
            "error": response.text,
        }

    if response.status_code >= 400:
        return payload, (
            "Worker de discovery inicial retornou erro "
            f"{response.status_code}: {payload}"
        )

    return payload, None


@st.cache_data(ttl=300, show_spinner=False)
def load_sub_niches_for_intake() -> list[dict[str, Any]]:
    client = get_supabase_client()
    if client is None:
        return []

    response = client.rpc("list_sub_niches_for_intake").execute()
    return response.data or []


def get_sub_niches_for_intake() -> tuple[list[dict[str, Any]], str | None]:
    if not is_supabase_configured():
        return [], "Supabase ainda nao configurado. Adicione SUPABASE_URL e SUPABASE_ANON_KEY nos secrets."

    try:
        return load_sub_niches_for_intake(), None
    except Exception as exc:
        return [], f"Falha ao consultar subnichos para intake: {exc}"


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


def aggregate_queue_bottleneck_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[str, dict[str, Any]] = {}

    for row in rows:
        check_band = str(row.get("check_band") or "").strip().lower()
        video_age_bucket = str(row.get("video_age_bucket") or "").strip().lower()
        if check_band == "needs_coverage" and video_age_bucket in {"new_0_3d", "recent_4_7d"}:
            continue

        priority_band = str(row.get("priority_band") or "sem_banda").strip().lower()
        current = grouped.setdefault(
            priority_band,
            {
                "priority_band": priority_band,
                "total_posts": 0,
                "media_checagens_sum": 0.0,
                "media_checagens_count": 0,
                "max_staleness_days": 0.0,
                "posts_vencidos": 0,
                "posts_no_batch_atual": 0,
            },
        )

        current["total_posts"] += int(row.get("total_posts") or 0)
        if row.get("media_checagens") is not None:
            current["media_checagens_sum"] += float(row.get("media_checagens") or 0)
            current["media_checagens_count"] += 1
        current["max_staleness_days"] = max(
            float(current.get("max_staleness_days") or 0),
            float(row.get("max_staleness_days") or 0),
        )
        current["posts_vencidos"] += int(row.get("posts_vencidos") or 0)
        current["posts_no_batch_atual"] += int(row.get("posts_no_batch_atual") or 0)

    aggregated_rows: list[dict[str, Any]] = []
    for current in grouped.values():
        count = int(current.get("media_checagens_count") or 0)
        avg_checks = (float(current.get("media_checagens_sum") or 0) / count) if count else 0.0
        aggregated_rows.append(
            {
                "priority_band": current["priority_band"],
                "total_posts": int(current["total_posts"]),
                "media_checagens_media": avg_checks,
                "max_staleness_days": float(current["max_staleness_days"]),
                "posts_vencidos": int(current["posts_vencidos"]),
                "posts_no_batch_atual": int(current["posts_no_batch_atual"]),
            }
        )

    def sort_key(row: dict[str, Any]) -> tuple[int, int, str]:
        is_text, normalized = queue_band_sort_value(row.get("priority_band"))
        if is_text == 0:
            return (0, -int(normalized), normalized)
        return (1, 0, normalized)

    return sorted(aggregated_rows, key=sort_key)


def render_queue_bottleneck_section(queue_rows: list[dict[str, Any]], queue_error: str | None) -> None:
    st.write("")
    st.markdown("### Gargalo da fila por banda")

    if queue_error:
        st.warning(queue_error)

    aggregated_rows = aggregate_queue_bottleneck_rows(queue_rows)
    if not aggregated_rows:
        st.markdown(
            '<div class="dq-kpi-grid dq-kpi-grid-third">'
            + dq_kpi_card(
                "Sem dados da fila",
                "--",
                "View v_dashboard_queue_bottleneck_status indisponivel ou vazia.",
                "#f2c14e",
                [
                    dq_chip("Posts", "--"),
                    dq_chip("Média checagens", "--"),
                    dq_chip("Pior atraso", "--"),
                    dq_chip("Vencidos", "--"),
                    dq_chip("Próximo batch", "--"),
                ],
            )
            + "</div>",
            unsafe_allow_html=True,
        )
        return

    cards: list[str] = []
    for row in aggregated_rows:
        avg_checks = float(row.get("media_checagens_media") or 0)
        max_staleness_days = float(row.get("max_staleness_days") or 0)
        overdue_count = int(row.get("posts_vencidos") or 0)
        next_batch_count = int(row.get("posts_no_batch_atual") or 0)
        staleness_tone = queue_staleness_tone(max_staleness_days)
        cards.append(
            dq_kpi_card(
                queue_band_title(row.get("priority_band")),
                format_int(row.get("total_posts")),
                "Posts monitorados na banda",
                "#ff8069",
                [
                    dq_chip("Média checagens", f"{avg_checks:.1f}".replace(".", ",")),
                    dq_chip("Pior atraso", f"{max_staleness_days:.1f}d".replace(".", ","), staleness_tone),
                    dq_chip("Vencidos", queue_overdue_label(overdue_count, int(row.get("total_posts") or 0)), "ok-green"),
                    dq_chip("Próximo batch", format_int(next_batch_count), "ok-green" if next_batch_count > 0 else "neutral"),
                ],
            )
        )

    st.markdown(
        '<div class="dq-kpi-grid dq-kpi-grid-third">' + "".join(cards) + "</div>",
        unsafe_allow_html=True,
    )
    st.caption("Buckets new e recent com check band needs coverage ficam fora deste bloco porque ja pertencem ao KPI de cobertura.")


def load_data_quality_context() -> tuple[
    list[dict[str, Any]],
    dict[str, Any] | None,
    list[dict[str, Any]],
    str | None,
    list[str],
]:
    guardrail_rows, guardrail_error = get_view_rows("v_dashboard_guardrail_coverage_status")
    dead_posts, dead_posts_error = get_single_row_view("v_dashboard_dead_post_validation_status")
    queue_rows, queue_error = get_view_rows("v_dashboard_queue_bottleneck_status")
    errors = [error for error in [guardrail_error, dead_posts_error] if error]
    return guardrail_rows, dead_posts, queue_rows, queue_error, errors


def render_data_quality_raw_tables(
    guardrail_rows: list[dict[str, Any]],
    dead_posts: dict[str, Any] | None,
    queue_rows: list[dict[str, Any]],
) -> None:
    trace_startup("render_data_quality_raw_tables start")
    with st.expander("Detalhamento tecnico", expanded=False):
        should_render_tables = st.checkbox(
            "Carregar tabelas tecnicas",
            value=True,
            key="data_quality_render_raw_tables",
        )
        if not should_render_tables:
            st.caption("As tabelas tecnicas ficam sob demanda para manter a abertura da pagina leve.")
            trace_startup("render_data_quality_raw_tables skipped")
            return

        trace_startup("render_data_quality_raw_tables rendering")
        if guardrail_rows:
            guardrail_rows = sorted(
                guardrail_rows,
                key=lambda row: (int(row.get("bucket_sort") or 0), int(row.get("total_checagens") or 0)),
            )
            st.markdown("### Legado guardrail")
            trace_startup("render_data_quality_raw_tables guardrail before")
            st.dataframe(
                guardrail_rows,
                width="stretch",
                hide_index=True,
                column_order=["intervalo_video", "total_checagens", "total_posts"],
                column_config={
                    "intervalo_video": "Intervalo do video",
                    "total_checagens": "Total de checagens",
                    "total_posts": "Total de posts",
                },
            )
            trace_startup("render_data_quality_raw_tables guardrail after")
        if dead_posts:
            st.write("")
            st.markdown("### Posts mortos e validacao humana")
            trace_startup("render_data_quality_raw_tables dead_posts before")
            st.dataframe([dead_posts], width="stretch")
            trace_startup("render_data_quality_raw_tables dead_posts after")
        if queue_rows:
            st.write("")
            st.markdown("### Gargalo da fila por banda")
            trace_startup("render_data_quality_raw_tables queue before")
            st.dataframe(queue_rows, width="stretch", hide_index=True)
            trace_startup("render_data_quality_raw_tables queue after")
    trace_startup("render_data_quality_raw_tables end")


def render_overview() -> None:
    trace_startup("render_overview start")
    creator_rows, creator_error = get_view_rows("v_dashboard_creator_summary")
    weekly_rows, weekly_error = get_filtered_rows(
        "v_dashboard_creator_weekly_activity",
        filters=(("video_type", "todos"),),
    )
    fenabrave_rows, fenabrave_error = get_view_rows("v_dashboard_fenabrave_monthly_segments")
    errors = [error for error in [creator_error, weekly_error, fenabrave_error] if error]
    base_summary = summarize_overview_creator_base(creator_rows)
    recent_summary = summarize_overview_recent_activity(creator_rows, weekly_rows)
    recent_chart_df = build_overview_recent_activity_frame(weekly_rows)
    fenabrave_summary = summarize_overview_fenabrave(fenabrave_rows)

    page_header(
        "Social Media Analytics",
        "Dashboard interno para estudos de mercado automotivo",
        "Overview",
    )
    page_subtitle("Leitura macro da base monitorada, sem aprofundamento analitico pesado.")

    if errors:
        st.warning(" | ".join(errors))

    st.write("")
    overview_cols = st.columns(4)
    with overview_cols[0]:
        metric_card(
            "Creators monitorados",
            format_int(base_summary["creators_monitorados"]),
            "Base ativa acompanhada pelo dashboard",
            "CR",
        )
    with overview_cols[1]:
        metric_card(
            "Posts monitorados",
            format_int(base_summary["posts_monitorados"]),
            "Volume atual dentro da base observada",
            "VD",
        )
    with overview_cols[2]:
        metric_card(
            "Plataformas cobertas",
            format_int(base_summary["plataformas_cobertas"]),
            base_summary["plataformas_legenda"],
            "SH",
        )
    with overview_cols[3]:
        metric_card(
            "Nichos cobertos",
            format_int(base_summary["nichos_cobertos"]),
            base_summary["nichos_legenda"],
            "RK",
        )

    st.markdown("### Atividade recente")
    st.markdown(
        '<div class="overview-recent-subtitle">Serie macro da base monitorada por semanas fechadas. O grafico resume novos posts e interacoes.</div>',
        unsafe_allow_html=True,
    )
    available_weeks = len(recent_chart_df.index) if recent_chart_df is not None and not recent_chart_df.empty else 0
    default_window_weeks = (
        max(min(OVERVIEW_RECENT_ACTIVITY_WINDOW_WEEKS, available_weeks), 2 if available_weeks >= 2 else 1)
        if available_weeks > 0
        else OVERVIEW_RECENT_ACTIVITY_WINDOW_WEEKS
    )
    selected_week_label = None
    recent_chart_filtered = filter_overview_recent_activity_frame(
        recent_chart_df,
        selected_week_label=selected_week_label,
        trailing_weeks=default_window_weeks,
    )
    recent_focus = summarize_overview_recent_focus(recent_chart_filtered, recent_summary)
    recent_left, recent_right = st.columns([1.8, 1])
    with recent_left:
        slider_col, _ = st.columns([0.55, 0.45])
        with slider_col:
            if available_weeks > 0:
                week_options = recent_chart_df.sort_values("week_end")["week_label"].dropna().astype(str).tolist()
                selected_week_label = st.select_slider(
                    "Semana fechada",
                    options=week_options,
                    value=week_options[-1],
                    key="overview_recent_week_slider",
                )
            else:
                st.select_slider(
                    "Semana fechada",
                    options=["Sem semana fechada"],
                    value="Sem semana fechada",
                    key="overview_recent_week_slider_empty",
                    disabled=True,
                )
        recent_chart_filtered = filter_overview_recent_activity_frame(
            recent_chart_df,
            selected_week_label=selected_week_label,
            trailing_weeks=default_window_weeks,
        )
        recent_focus = summarize_overview_recent_focus(recent_chart_filtered, recent_summary)
        recent_fig = build_overview_recent_activity_chart(recent_chart_filtered)
        if recent_fig is not None:
            trace_startup("render_overview recent_chart before")
            st.plotly_chart(recent_fig, width="stretch", config={"displayModeBar": False})
            trace_startup("render_overview recent_chart after")
        else:
            placeholder_card(
                "Atividade recente",
                "Aguardando semanas fechadas com dados suficientes para montar a serie macro da base.",
            )
    with recent_right:
        metric_card_grid(
            [
                metric_card_html(
                    "Novos posts",
                    format_int(recent_focus["posts_publicados_semana"]),
                    recent_focus["posts_caption"],
                    "VD",
                    caption_color=recent_focus["posts_caption_color"],
                ),
                metric_card_html(
                    "Interacoes",
                    format_int(recent_focus["interacoes_semana"]),
                    recent_focus["interacoes_caption"],
                    "VW",
                    caption_color=recent_focus["interacoes_caption_color"],
                ),
                metric_card_html(
                    "Criadores ativos",
                    format_int(recent_focus["creators_ativos_semana"]),
                    recent_focus["creators_caption"],
                    "CR",
                    caption_color=recent_focus["creators_caption_color"],
                ),
            ],
            class_name="creator-kpi-grid weekly-grid overview-recent-kpi-grid",
        )

    st.write("")
    left, right = st.columns([1.6, 0.45])
    with left:
        process_banner(
            "Estado macro da base",
            (
                f"Ultima coleta observada em {base_summary['ultima_coleta_legenda']}. "
                f"Ultimo post observado em {base_summary['ultimo_post_legenda']}. "
                f"A janela semanal mais recente fechada e {recent_summary['semana_legenda_curta']}."
            ),
        )
    with right:
        if st.button("Ver Data Quality", use_container_width=True):
            st.session_state["nav_page"] = "Data quality"
            st.rerun()

    st.write("")
    st.markdown("### Fenabrave")
    st.caption(fenabrave_summary["periodo"])
    if fenabrave_summary["cards"]:
        metric_card_grid(
            fenabrave_summary["cards"],
            class_name="overview-fenabrave-grid",
        )
    else:
        placeholder_card(
            "Fenabrave",
            "Aguardando a view v_dashboard_fenabrave_monthly_segments retornar dados validos.",
        )

    st.caption(
        "Os numeros desta tela descrevem a base monitorada e o estado geral do monitoramento, nao o universo completo de videos de cada creator."
    )
    trace_startup("render_overview end")


def render_placeholder_page(title: str, description: str) -> None:
    st.title(title)
    placeholder_card(title, description)


def render_youtube_best_7d_page() -> None:
    trace_startup("render_youtube_best_7d start")
    page_header("Ranking semanal de crescimento")

    st.markdown(
        """
        <style>
        .youtube-best-toolbar {
            display: flex;
            align-items: center;
            gap: 0.85rem;
            margin: 0.15rem 0 0.75rem;
        }
        .youtube-best-toolbar-label {
            color: var(--text);
            font-size: 1.7rem;
            font-weight: 800;
            line-height: 1;
            white-space: nowrap;
        }
        .youtube-best-table {
            border: none;
            border-radius: 0;
            overflow: visible;
            background: transparent;
            box-shadow: none;
        }
        .youtube-best-scroll {
            max-height: 72vh;
            overflow-y: auto;
            overflow-x: hidden;
            padding-right: 0.2rem;
        }
        .youtube-best-header,
        .youtube-best-row {
            display: grid;
            grid-template-columns: minmax(610px, 4.9fr) 0.54fr 0.28fr 0.26fr 0.26fr 0.28fr;
            gap: 0;
        }
        .youtube-best-header {
            position: sticky;
            top: 0;
            z-index: 4;
            background: transparent;
            border-bottom: 1px solid rgba(255, 255, 255, 0.08);
            backdrop-filter: blur(10px);
        }
        .youtube-best-head-cell {
            min-height: 58px;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 0.72rem 0.25rem;
            color: var(--muted);
            font-size: 0.72rem;
            font-weight: 800;
            letter-spacing: 0.02em;
            text-transform: uppercase;
            text-align: center;
        }
        .youtube-best-head-cell.video {
            display: grid;
            grid-template-columns: 48px 140px minmax(0, 1fr);
            gap: 0.95rem;
            align-items: center;
            justify-content: initial;
            text-align: left;
            padding-left: 1rem;
        }
        .youtube-best-head-hash {
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 1.45rem;
            font-weight: 800;
            line-height: 1;
            color: var(--text);
        }
        .youtube-best-head-video-label {
            grid-column: 3;
            display: inline-flex;
            align-items: center;
        }
        .youtube-best-head-icon {
            width: 28px;
            height: 28px;
            border-radius: 6px;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            background: var(--accent);
            color: #ffffff;
            font-size: 0;
            box-sizing: border-box;
            flex: 0 0 auto;
            box-shadow: inset 0 0 0 1px rgba(0, 0, 0, 0.12);
        }
        .youtube-best-head-icon svg {
            width: 68%;
            height: 68%;
            display: block;
            stroke: currentColor;
            fill: none;
            stroke-width: 2.4;
            stroke-linecap: round;
            stroke-linejoin: round;
        }
        .youtube-best-head-icon .icon-fill {
            fill: currentColor;
            stroke: none;
        }
        .youtube-best-row + .youtube-best-row {
            border-top: 1px solid rgba(255, 255, 255, 0.08);
        }
        .youtube-best-main {
            display: grid;
            grid-template-columns: 48px 140px minmax(0, 1fr);
            gap: 0.95rem;
            align-items: center;
            padding: 1rem;
        }
        .youtube-best-rank {
            font-size: 1.6rem;
            font-weight: 800;
            color: var(--text);
            text-align: center;
            line-height: 1;
        }
        .youtube-best-thumb {
            width: 140px;
            aspect-ratio: 16 / 9;
            border-radius: 14px;
            border: 1px dashed rgba(255, 255, 255, 0.18);
            background:
                linear-gradient(135deg, rgba(255, 128, 105, 0.28), rgba(255, 255, 255, 0.02)),
                rgba(255, 255, 255, 0.03);
            display: flex;
            align-items: center;
            justify-content: center;
            color: var(--muted);
            font-size: 0.74rem;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.04em;
        }
        .youtube-best-thumb-link {
            display: block;
            width: 140px;
            text-decoration: none;
        }
        .youtube-best-thumb-image {
            width: 140px;
            aspect-ratio: 16 / 9;
            object-fit: cover;
            display: block;
            border-radius: 14px;
            border: 1px solid rgba(255, 255, 255, 0.12);
            background: rgba(255, 255, 255, 0.04);
        }
        .youtube-best-copy {
            min-width: 0;
            display: flex;
            flex-direction: column;
            justify-content: center;
            min-height: 78px;
        }
        .youtube-best-channel {
            color: var(--accent);
            font-size: 0.82rem;
            font-weight: 700;
            margin-bottom: 0.28rem;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }
        .youtube-best-title {
            color: var(--text);
            font-size: 1.28rem;
            font-weight: 700;
            line-height: 1.22;
            margin-bottom: 0.48rem;
            word-break: break-word;
        }
        .youtube-best-title-link {
            color: inherit;
            text-decoration: none;
        }
        .youtube-best-title-link:hover {
            text-decoration: underline;
        }
        .youtube-best-meta {
            display: flex;
            flex-wrap: nowrap;
            gap: 0.38rem;
            align-items: center;
            overflow: hidden;
        }
        .youtube-best-chip {
            border-radius: 999px;
            padding: 0.26rem 0.58rem;
            font-size: 0.68rem;
            font-weight: 700;
            background: rgba(255, 255, 255, 0.06);
            color: var(--muted);
            border: 1px solid rgba(255, 255, 255, 0.08);
            white-space: nowrap;
        }
        .youtube-best-chip.type {
            color: white;
            background: rgba(255, 128, 105, 0.22);
            border-color: rgba(255, 128, 105, 0.34);
        }
        .youtube-best-cell {
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 1rem 0.28rem;
            color: var(--text);
            font-size: 0.92rem;
            font-weight: 700;
            text-align: center;
        }
        @media (max-width: 1100px) {
            .youtube-best-header {
                display: none;
            }
            .youtube-best-row {
                grid-template-columns: 1fr;
            }
            .youtube-best-main {
                grid-template-columns: 40px 118px minmax(0, 1fr);
            }
            .youtube-best-thumb {
                width: 118px;
            }
            .youtube-best-thumb-link {
                width: 118px;
            }
            .youtube-best-thumb-image {
                width: 118px;
            }
            .youtube-best-cell {
                justify-content: space-between;
                border-top: 1px solid rgba(255, 255, 255, 0.06);
                padding: 0.85rem 1rem;
            }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    selector_cols = st.columns([0.19, 0.81])
    with selector_cols[0]:
        st.markdown('<div class="youtube-best-toolbar"><div class="youtube-best-toolbar-label">Tipo de video</div></div>', unsafe_allow_html=True)
    with selector_cols[1]:
        selected_filter = st.radio(
            "Tipo de video",
            ["Todos", "Long", "Short"],
            horizontal=True,
            key="youtube_best_7d_filter",
            label_visibility="collapsed",
        )

    filters: list[tuple[str, Any]] = [("platform", "youtube")]
    if selected_filter == "Long":
        filters.append(("video_type", "long"))
    elif selected_filter == "Short":
        filters.append(("video_type", "short"))

    rows, error = get_filtered_rows(
        "v_dashboard_post_growth_7d",
        filters=tuple(filters),
        order_by="views_growth_pct_7d",
        order_desc=True,
        order_nulls_first=False,
        limit=10,
    )
    if error:
        render_connection_notice(error)

    if error and not rows:
        placeholder_card(
            "View indisponivel",
            "A pagina esta pronta, mas a consulta a v_dashboard_post_growth_7d ainda nao retornou dados neste ambiente.",
        )
        return

    if not rows:
        placeholder_card(
            "Sem dados para ranking semanal",
            "Nenhum video com crescimento na janela atual de 7 dias completos fechados foi retornado.",
        )
        return

    df = pd.DataFrame(rows)

    def optional_series(column_name: str, default_value: Any = None) -> pd.Series:
        if column_name in df.columns:
            return df[column_name]
        return pd.Series([default_value] * len(df), index=df.index)

    df["views_delta_7d_num"] = pd.to_numeric(optional_series("views_delta_7d", 0), errors="coerce").fillna(0)
    df["likes_delta_7d_num"] = pd.to_numeric(optional_series("likes_delta_7d", 0), errors="coerce").fillna(0)
    df["comments_delta_7d_num"] = pd.to_numeric(optional_series("comments_delta_7d", 0), errors="coerce").fillna(0)
    df["views_num"] = pd.to_numeric(optional_series("views", 0), errors="coerce").fillna(0)
    df["likes_num"] = pd.to_numeric(optional_series("likes", 0), errors="coerce").fillna(0)
    df["comments_num"] = pd.to_numeric(optional_series("comments", 0), errors="coerce").fillna(0)
    df["snapshot_count_num"] = pd.to_numeric(optional_series("snapshot_count", 0), errors="coerce").fillna(0)
    df["views_growth_pct_7d_num"] = pd.to_numeric(optional_series("views_growth_pct_7d"), errors="coerce")
    df["post_date_dt"] = pd.to_datetime(optional_series("post_date"), errors="coerce")
    df["latest_collected_at_dt"] = pd.to_datetime(optional_series("latest_collected_at"), errors="coerce", utc=True)

    df["channel_name"] = df.get("username", pd.Series(dtype="object")).fillna("").astype(str).str.strip()
    entity_series = df.get("entity_name", pd.Series(dtype="object")).fillna("").astype(str).str.strip()
    df.loc[df["channel_name"] == "", "channel_name"] = entity_series[df["channel_name"] == ""]
    df.loc[df["channel_name"] == "", "channel_name"] = "Canal sem nome"
    df["title_display"] = df.get("title", pd.Series(dtype="object")).fillna("").astype(str).str.strip()
    df.loc[df["title_display"] == "", "title_display"] = "Video sem titulo"
    df["video_type_normalized"] = (
        df.get("video_type", pd.Series(dtype="object")).fillna("outro").astype(str).str.strip().str.lower()
    )
    df["video_type_label"] = df["video_type_normalized"].map({"long": "Long", "short": "Short"}).fillna("Todos")

    if df.empty:
        placeholder_card(
            "Sem videos neste filtro",
            f"Nao houve retorno do Supabase para o filtro {selected_filter} dentro da janela de 7 dias completos fechados.",
        )
        return

    date_header_icon = calendar_header_icon_html("Publicado em")
    growth_header_icon = header_pill_icon_html("RK", "Crescimento")
    video_header_icon = header_pill_icon_html("VD", "Video")
    views_header_icon = header_pill_icon_html("VW", "Views")
    likes_header_icon = header_pill_icon_html("LK", "Likes")
    comments_header_icon = header_pill_icon_html("CM", "Comentarios")
    row_blocks: list[str] = []
    table_html = (
        '<div class="youtube-best-table">'
        '<div class="youtube-best-scroll">'
        '<div class="youtube-best-header">'
        f'<div class="youtube-best-head-cell video"><span class="youtube-best-head-hash">#</span><span class="youtube-best-head-video-label">{video_header_icon}</span></div>'
        f'<div class="youtube-best-head-cell">{date_header_icon}</div>'
        f'<div class="youtube-best-head-cell">{growth_header_icon}</div>'
        f'<div class="youtube-best-head-cell">{views_header_icon}</div>'
        f'<div class="youtube-best-head-cell">{likes_header_icon}</div>'
        f'<div class="youtube-best-head-cell">{comments_header_icon}</div>'
        "</div>"
    )

    for rank, row in enumerate(df.to_dict("records"), start=1):
        latest_snapshot = format_timestamp_br(row.get("latest_collected_at_dt"))
        snapshot_count = row.get("snapshot_count_num")
        snapshot_label = format_int(snapshot_count) if snapshot_count not in (None, "", 0) else "n/d"
        post_date_label = pd.Timestamp(row["post_date_dt"]).strftime("%d/%m/%Y") if pd.notna(row.get("post_date_dt")) else "--"
        growth_label = format_pct(row.get("views_growth_pct_7d_num"))
        video_id = str(row.get("post_id") or "").strip()
        video_url = f"https://www.youtube.com/watch?v={video_id}" if video_id else ""
        thumbnail_url = f"https://i.ytimg.com/vi/{video_id}/mqdefault.jpg" if video_id else ""
        if video_url:
            thumb_html = (
                f'<a class="youtube-best-thumb-link" href="{escape(video_url)}" target="_blank" rel="noopener noreferrer">'
                f'<img class="youtube-best-thumb-image" src="{escape(thumbnail_url)}" alt="{escape(str(row.get("title_display") or "Thumbnail do video"))}" loading="lazy" />'
                "</a>"
            )
            title_html = (
                f'<a class="youtube-best-title-link" href="{escape(video_url)}" target="_blank" rel="noopener noreferrer">'
                f'{escape(str(row.get("title_display") or "Video sem titulo"))}'
                "</a>"
            )
        else:
            thumb_html = '<div class="youtube-best-thumb">thumbnail</div>'
            title_html = escape(str(row.get("title_display") or "Video sem titulo"))
        row_html = (
            '<div class="youtube-best-row">'
            '<div class="youtube-best-main">'
            f'<div class="youtube-best-rank">{rank}</div>'
            f"{thumb_html}"
            '<div class="youtube-best-copy">'
            f'<div class="youtube-best-channel">{escape(str(row.get("channel_name") or "Canal sem nome"))}</div>'
            f'<div class="youtube-best-title">{title_html}</div>'
            '<div class="youtube-best-meta">'
            f'<span class="youtube-best-chip type">{escape(str(row.get("video_type_label") or "Todos"))}</span>'
            f'<span class="youtube-best-chip">Ultimo snapshot {escape(latest_snapshot)}</span>'
            f'<span class="youtube-best-chip">Snapshots {escape(snapshot_label)}</span>'
            "</div>"
            "</div>"
            "</div>"
            f'<div class="youtube-best-cell">{escape(post_date_label)}</div>'
            f'<div class="youtube-best-cell">{escape(growth_label)}</div>'
            f'<div class="youtube-best-cell">{escape(format_compact_number(row.get("views_num")))}</div>'
            f'<div class="youtube-best-cell">{escape(format_compact_number(row.get("likes_num")))}</div>'
            f'<div class="youtube-best-cell">{escape(format_compact_number(row.get("comments_num")))}</div>'
            "</div>"
        )
        row_blocks.append(row_html)

    st.markdown(table_html + "".join(row_blocks) + "</div></div>", unsafe_allow_html=True)
    st.caption("O video entra no ranking pelo crescimento de views em 7 dias, enquanto views, likes e comentarios mostram os totais atuais do post.")


def render_youtube_hot_now_page() -> None:
    trace_startup("render_youtube_hot_now start")
    page_header("Hot now", "Videos ganhando tracao agora por velocidade recente e aceleracao")

    st.markdown(
        """
        <style>
        .hot-now-toolbar {
            display: flex;
            align-items: center;
            gap: 0.85rem;
            margin: 0.15rem 0 0.75rem;
        }
        .hot-now-toolbar-label {
            color: var(--text);
            font-size: 1.7rem;
            font-weight: 800;
            line-height: 1;
            white-space: nowrap;
        }
        .hot-now-note {
            color: var(--muted);
            font-size: 0.86rem;
            margin: 0 0 1rem;
        }
        .hot-now-table {
            border: none;
            border-radius: 0;
            overflow: visible;
            background: transparent;
            box-shadow: none;
        }
        .hot-now-scroll {
            max-height: 72vh;
            overflow-y: auto;
            overflow-x: hidden;
            padding-right: 0.2rem;
        }
        .hot-now-header,
        .hot-now-row {
            display: grid;
            grid-template-columns: minmax(560px, 4.45fr) 0.36fr 0.4fr 0.33fr 0.33fr 0.33fr 0.33fr;
            gap: 0;
        }
        .hot-now-header {
            position: sticky;
            top: 0;
            z-index: 4;
            background: transparent;
            border-bottom: 1px solid rgba(255, 255, 255, 0.08);
            backdrop-filter: blur(10px);
        }
        .hot-now-head-cell {
            min-height: 58px;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 0.72rem 0.25rem;
            color: var(--muted);
            font-size: 0.72rem;
            font-weight: 800;
            letter-spacing: 0.02em;
            text-transform: uppercase;
            text-align: center;
        }
        .hot-now-head-cell.video {
            display: grid;
            grid-template-columns: 48px 140px minmax(0, 1fr);
            gap: 0.95rem;
            align-items: center;
            justify-content: initial;
            text-align: left;
            padding-left: 1rem;
        }
        .hot-now-head-hash {
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 1.45rem;
            font-weight: 800;
            line-height: 1;
            color: var(--text);
        }
        .hot-now-head-video-label {
            grid-column: 3;
            display: inline-flex;
            align-items: center;
        }
        .youtube-best-head-icon {
            width: 28px;
            height: 28px;
            border-radius: 6px;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            background: var(--accent);
            color: #ffffff;
            font-size: 0;
            box-sizing: border-box;
            flex: 0 0 auto;
            box-shadow: inset 0 0 0 1px rgba(0, 0, 0, 0.12);
        }
        .youtube-best-head-icon svg {
            width: 68%;
            height: 68%;
            display: block;
            stroke: currentColor;
            fill: none;
            stroke-width: 2.4;
            stroke-linecap: round;
            stroke-linejoin: round;
        }
        .youtube-best-head-icon .icon-fill {
            fill: currentColor;
            stroke: none;
        }
        .hot-now-row + .hot-now-row {
            border-top: 1px solid rgba(255, 255, 255, 0.08);
        }
        .hot-now-main {
            display: grid;
            grid-template-columns: 48px 140px minmax(0, 1fr);
            gap: 0.95rem;
            align-items: center;
            padding: 1rem;
        }
        .hot-now-rank {
            font-size: 1.6rem;
            font-weight: 800;
            color: var(--text);
            text-align: center;
            line-height: 1;
        }
        .hot-now-thumb-link {
            display: block;
            width: 140px;
            text-decoration: none;
        }
        .hot-now-thumb-image {
            width: 140px;
            aspect-ratio: 16 / 9;
            object-fit: cover;
            display: block;
            border-radius: 14px;
            border: 1px solid rgba(255, 255, 255, 0.12);
            background: rgba(255, 255, 255, 0.04);
        }
        .hot-now-thumb {
            width: 140px;
            aspect-ratio: 16 / 9;
            border-radius: 14px;
            border: 1px dashed rgba(255, 255, 255, 0.18);
            background:
                linear-gradient(135deg, rgba(255, 128, 105, 0.28), rgba(255, 255, 255, 0.02)),
                rgba(255, 255, 255, 0.03);
            display: flex;
            align-items: center;
            justify-content: center;
            color: var(--muted);
            font-size: 0.74rem;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.04em;
        }
        .hot-now-copy {
            min-width: 0;
            display: flex;
            flex-direction: column;
            justify-content: center;
            min-height: 78px;
        }
        .hot-now-channel {
            color: var(--accent);
            font-size: 0.82rem;
            font-weight: 700;
            margin-bottom: 0.28rem;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }
        .hot-now-title {
            color: var(--text);
            font-size: 1.28rem;
            font-weight: 700;
            line-height: 1.22;
            margin-bottom: 0.48rem;
            word-break: break-word;
        }
        .hot-now-title-link {
            color: inherit;
            text-decoration: none;
        }
        .hot-now-title-link:hover {
            text-decoration: underline;
        }
        .hot-now-meta {
            display: flex;
            flex-wrap: nowrap;
            gap: 0.38rem;
            align-items: center;
            overflow: hidden;
        }
        .hot-now-chip {
            border-radius: 999px;
            padding: 0.26rem 0.58rem;
            font-size: 0.68rem;
            font-weight: 700;
            background: rgba(255, 255, 255, 0.06);
            color: var(--muted);
            border: 1px solid rgba(255, 255, 255, 0.08);
            white-space: nowrap;
        }
        .hot-now-chip.type {
            color: white;
            background: rgba(255, 128, 105, 0.22);
            border-color: rgba(255, 128, 105, 0.34);
        }
        .hot-now-cell {
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 1rem 0.28rem;
            color: var(--text);
            font-size: 0.92rem;
            font-weight: 700;
            text-align: center;
        }
        .hot-now-cell.positive {
            color: #66d99a;
        }
        .hot-now-cell.negative {
            color: #ff9f91;
        }
        @media (max-width: 1100px) {
            .hot-now-header {
                display: none;
            }
            .hot-now-row {
                grid-template-columns: 1fr;
            }
            .hot-now-main {
                grid-template-columns: 40px 118px minmax(0, 1fr);
            }
            .hot-now-thumb,
            .hot-now-thumb-link,
            .hot-now-thumb-image {
                width: 118px;
            }
            .hot-now-cell {
                justify-content: space-between;
                border-top: 1px solid rgba(255, 255, 255, 0.06);
                padding: 0.85rem 1rem;
            }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    selector_cols = st.columns([0.19, 0.81])
    with selector_cols[0]:
        st.markdown('<div class="hot-now-toolbar"><div class="hot-now-toolbar-label">Tipo de video</div></div>', unsafe_allow_html=True)
    with selector_cols[1]:
        selected_filter = st.radio(
            "Tipo de video",
            ["Todos", "Long", "Short"],
            horizontal=True,
            key="youtube_hot_now_filter",
            label_visibility="collapsed",
        )

    st.markdown(
        '<div class="hot-now-note">Ranking exploratorio com snapshot atual ate 12h, baseline de 6h entre 6h e 8h, e baseline anterior entre 18h e 30h.</div>',
        unsafe_allow_html=True,
    )

    filters: list[tuple[str, Any]] = [("is_hot_now_eligible", True)]
    if selected_filter == "Long":
        filters.append(("video_type", "long"))
    elif selected_filter == "Short":
        filters.append(("video_type", "short"))

    rows, error = get_filtered_rows(
        "v_dashboard_hot_now",
        filters=tuple(filters),
        order_by="hot_now_rank_score",
        order_desc=True,
        order_nulls_first=False,
        limit=10,
    )
    if error:
        render_connection_notice(error)

    if error and not rows:
        placeholder_card(
            "View indisponivel",
            "A pagina esta pronta, mas a consulta a v_dashboard_hot_now ainda nao retornou dados neste ambiente.",
        )
        return

    if not rows:
        placeholder_card(
            "Sem videos elegiveis para Hot now",
            f"Nenhum video do filtro {selected_filter} tem ao menos 3 snapshots validos com frescor de ate 24h agora.",
        )
        return

    df = pd.DataFrame(rows)

    def optional_series(column_name: str, default_value: Any = None) -> pd.Series:
        if column_name in df.columns:
            return df[column_name]
        return pd.Series([default_value] * len(df), index=df.index)

    df["hot_now_rank_score_num"] = pd.to_numeric(optional_series("hot_now_rank_score", 0), errors="coerce").fillna(0)
    df["velocity_6h_num"] = pd.to_numeric(optional_series("velocity_6h", 0), errors="coerce").fillna(0)
    df["previous_velocity_num"] = pd.to_numeric(optional_series("previous_velocity", 0), errors="coerce").fillna(0)
    df["acceleration_num"] = pd.to_numeric(optional_series("acceleration", 0), errors="coerce").fillna(0)
    df["views_delta_recent_num"] = pd.to_numeric(optional_series("views_delta_recent", 0), errors="coerce").fillna(0)
    df["views_latest_num"] = pd.to_numeric(optional_series("views_latest", 0), errors="coerce").fillna(0)
    df["snapshot_count_num"] = pd.to_numeric(optional_series("snapshot_count", 0), errors="coerce").fillna(0)
    df["likes_delta_recent_num"] = pd.to_numeric(optional_series("likes_delta_recent", 0), errors="coerce").fillna(0)
    df["comments_delta_recent_num"] = pd.to_numeric(optional_series("comments_delta_recent", 0), errors="coerce").fillna(0)
    df["latest_collected_at_dt"] = pd.to_datetime(optional_series("latest_collected_at"), errors="coerce", utc=True)
    df["published_at_dt"] = pd.to_datetime(optional_series("published_at"), errors="coerce")

    df["channel_name"] = optional_series("creator_name", "").fillna("").astype(str).str.strip()
    username_series = optional_series("username", "").fillna("").astype(str).str.strip()
    df.loc[df["channel_name"] == "", "channel_name"] = username_series[df["channel_name"] == ""]
    df.loc[df["channel_name"] == "", "channel_name"] = "Canal sem nome"
    df["title_display"] = optional_series("title", "").fillna("").astype(str).str.strip()
    df.loc[df["title_display"] == "", "title_display"] = "Video sem titulo"
    df["video_type_normalized"] = optional_series("video_type", "outro").fillna("outro").astype(str).str.strip().str.lower()
    df["video_type_label"] = df["video_type_normalized"].map({"long": "Long", "short": "Short"}).fillna("Todos")

    def format_rate(value: Any) -> str:
        try:
            numeric_value = float(value)
            if pd.isna(numeric_value):
                return "--"
            return f"{int(round(numeric_value))}/h"
        except (TypeError, ValueError):
            return "--"

    def format_score(value: Any) -> str:
        try:
            numeric_value = float(value)
            if pd.isna(numeric_value):
                return "--"
            return format_int(round(numeric_value))
        except (TypeError, ValueError):
            return "--"

    def value_class(value: Any) -> str:
        try:
            numeric_value = float(value)
        except (TypeError, ValueError):
            return ""
        if numeric_value > 0:
            return " positive"
        if numeric_value < 0:
            return " negative"
        return ""

    video_header_icon = header_pill_icon_html("VD", "Video")
    total_views_header_icon = header_pill_icon_html("VW", "Views totais")
    score_header_icon = header_pill_icon_html("SC", "Score")
    velocity_header_icon = header_pill_icon_html("VA", "Velocidade atual")
    previous_header_icon = header_pill_icon_html("VP", "Velocidade anterior")
    acceleration_header_icon = header_pill_icon_html("AC", "Aceleracao")
    delta_header_icon = header_pill_icon_html("DV", "Delta views")
    row_blocks: list[str] = []
    table_html = (
        '<div class="hot-now-table">'
        '<div class="hot-now-scroll">'
        '<div class="hot-now-header">'
        f'<div class="hot-now-head-cell video"><span class="hot-now-head-hash">#</span><span class="hot-now-head-video-label">{video_header_icon}</span></div>'
        f'<div class="hot-now-head-cell">{total_views_header_icon}</div>'
        f'<div class="hot-now-head-cell">{score_header_icon}</div>'
        f'<div class="hot-now-head-cell">{velocity_header_icon}</div>'
        f'<div class="hot-now-head-cell">{previous_header_icon}</div>'
        f'<div class="hot-now-head-cell">{acceleration_header_icon}</div>'
        f'<div class="hot-now-head-cell">{delta_header_icon}</div>'
        "</div>"
    )

    for rank, row in enumerate(df.to_dict("records"), start=1):
        video_id = str(row.get("post_id") or "").strip()
        video_url = f"https://www.youtube.com/watch?v={video_id}" if video_id else ""
        thumbnail_url = f"https://i.ytimg.com/vi/{video_id}/mqdefault.jpg" if video_id else ""
        latest_snapshot = format_timestamp_br(row.get("latest_collected_at_dt"))
        published_label = pd.Timestamp(row["published_at_dt"]).strftime("%d/%m/%Y") if pd.notna(row.get("published_at_dt")) else "--"
        snapshot_count = row.get("snapshot_count_num")
        snapshot_count_label = format_int(snapshot_count) if snapshot_count not in (None, "", 0) else "n/d"
        if video_url:
            thumb_html = (
                f'<a class="hot-now-thumb-link" href="{escape(video_url)}" target="_blank" rel="noopener noreferrer">'
                f'<img class="hot-now-thumb-image" src="{escape(thumbnail_url)}" alt="{escape(str(row.get("title_display") or "Thumbnail do video"))}" loading="lazy" />'
                "</a>"
            )
            title_html = (
                f'<a class="hot-now-title-link" href="{escape(video_url)}" target="_blank" rel="noopener noreferrer">'
                f'{escape(str(row.get("title_display") or "Video sem titulo"))}'
                "</a>"
            )
        else:
            thumb_html = '<div class="hot-now-thumb">thumbnail</div>'
            title_html = escape(str(row.get("title_display") or "Video sem titulo"))

        acceleration_class = value_class(row.get("acceleration_num"))
        row_html = (
            '<div class="hot-now-row">'
            '<div class="hot-now-main">'
            f'<div class="hot-now-rank">{rank}</div>'
            f"{thumb_html}"
            '<div class="hot-now-copy">'
            f'<div class="hot-now-channel">{escape(str(row.get("channel_name") or "Canal sem nome"))}</div>'
            f'<div class="hot-now-title">{title_html}</div>'
            '<div class="hot-now-meta">'
            f'<span class="hot-now-chip type">{escape(str(row.get("video_type_label") or "Todos"))}</span>'
            f'<span class="hot-now-chip">Publicado {escape(published_label)}</span>'
            f'<span class="hot-now-chip">Snapshot {escape(latest_snapshot)}</span>'
            f'<span class="hot-now-chip">Snapshots {escape(snapshot_count_label)}</span>'
            "</div>"
            "</div>"
            "</div>"
            f'<div class="hot-now-cell">{escape(format_compact_number(row.get("views_latest_num")))}</div>'
            f'<div class="hot-now-cell">{escape(format_score(row.get("hot_now_rank_score_num")))}</div>'
            f'<div class="hot-now-cell">{escape(format_rate(row.get("velocity_6h_num")))}</div>'
            f'<div class="hot-now-cell">{escape(format_rate(row.get("previous_velocity_num")))}</div>'
            f'<div class="hot-now-cell{acceleration_class}">{escape(format_rate(row.get("acceleration_num")))}</div>'
            f'<div class="hot-now-cell">{escape(format_compact_number(row.get("views_delta_recent_num")))}</div>'
            "</div>"
        )
        row_blocks.append(row_html)

    st.markdown(table_html + "".join(row_blocks) + "</div></div>", unsafe_allow_html=True)
    st.caption("Hot now 24h usa o ultimo snapshot, o snapshot anterior e o penultimo disponivel. VA representa a velocidade atual entre os dois snapshots mais recentes; VP representa a velocidade imediatamente anterior; o score soma VA com bonus apenas para aceleracao positiva.")


def render_data_quality_page() -> None:
    trace_startup("render_data_quality start")
    guardrail_rows, dead_posts, queue_rows, queue_error, errors = load_data_quality_context()
    trace_startup("render_data_quality context loaded")
    page_header("Data quality", "Confiabilidade operacional antes das análises")
    render_connection_notice(errors[0] if errors else None)
    trace_startup("render_data_quality cards start")
    render_data_quality_cards(guardrail_rows, dead_posts, errors)
    trace_startup("render_data_quality queue start")
    render_queue_bottleneck_section(queue_rows, queue_error)
    trace_startup("render_data_quality collection start")
    render_collection_integrity_section()
    trace_startup("render_data_quality raw tables start")
    render_data_quality_raw_tables(guardrail_rows, dead_posts, queue_rows)
    trace_startup("render_data_quality end")


def format_int(value: Any) -> str:
    try:
        return f"{int(value):,}".replace(",", ".")
    except (TypeError, ValueError):
        return "--"


def format_compact_number(value: Any) -> str:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return "--"
    abs_number = abs(number)
    if abs_number >= 1_000_000_000:
        compact_value = number / 1_000_000_000
        suffix = "B"
    elif abs_number >= 1_000_000:
        compact_value = number / 1_000_000
        suffix = "M"
    elif abs_number >= 1_000:
        compact_value = number / 1_000
        suffix = "K"
    else:
        return str(int(number)) if number.is_integer() else f"{number:.1f}".rstrip("0").rstrip(".")
    formatted = f"{compact_value:.1f}".rstrip("0").rstrip(".")
    return f"{formatted}{suffix}"


def format_pct(value: Any) -> str:
    try:
        numeric_value = float(value)
        if pd.isna(numeric_value):
            return "--"
        return f"{round(numeric_value):.0f}%".replace(".", ",")
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
    timestamp = pd.Timestamp(value)
    if timestamp.tzinfo is None:
        timestamp = timestamp.tz_localize("UTC")
    return timestamp.tz_convert("America/Sao_Paulo").strftime("%d/%m/%Y %H:%M")


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


def summarize_overview_creator_base(rows: list[dict[str, Any]]) -> dict[str, Any]:
    if not rows:
        return {
            "creators_monitorados": 0,
            "posts_monitorados": 0,
            "plataformas_cobertas": 0,
            "nichos_cobertos": 0,
            "plataformas_legenda": "Sem plataformas carregadas",
            "nichos_legenda": "Sem nichos carregados",
            "ultima_coleta_legenda": "--",
            "ultimo_post_legenda": "--",
        }

    df = pd.DataFrame(rows)
    posts_monitorados = int(pd.to_numeric(df.get("post_count"), errors="coerce").fillna(0).sum())

    platforms = sorted(
        {
            str(value).strip()
            for value in df.get("platform", pd.Series(dtype="object")).tolist()
            if str(value).strip() and str(value).strip().lower() != "nan"
        }
    )
    niches = sorted(
        {
            str(value).strip()
            for value in df.get("niche", pd.Series(dtype="object")).tolist()
            if str(value).strip() and str(value).strip().lower() != "nan"
        }
    )

    latest_collected = pd.to_datetime(df.get("latest_collected_at"), errors="coerce", utc=True)
    latest_post = pd.to_datetime(df.get("latest_post_date"), errors="coerce", utc=True)

    return {
        "creators_monitorados": int(len(df)),
        "posts_monitorados": posts_monitorados,
        "plataformas_cobertas": len(platforms),
        "nichos_cobertos": len(niches),
        "plataformas_legenda": humanize_overview_list(platforms, "plataforma"),
        "nichos_legenda": humanize_overview_list(niches, "nicho"),
        "ultima_coleta_legenda": format_overview_date(latest_collected.max()),
        "ultimo_post_legenda": format_overview_date(latest_post.max()),
    }


def summarize_overview_recent_activity(
    creator_rows: list[dict[str, Any]],
    weekly_rows: list[dict[str, Any]],
) -> dict[str, Any]:
    recent_collectors = 0
    if creator_rows:
        creator_df = pd.DataFrame(creator_rows)
        latest_collected = pd.to_datetime(
            creator_df.get("latest_collected_at"),
            errors="coerce",
            utc=True,
        )
        cutoff = pd.Timestamp.now(tz="UTC") - pd.to_timedelta(7, unit="D")
        recent_collectors = int((latest_collected >= cutoff).fillna(False).sum())

    if not weekly_rows:
        return {
            "creators_ativos_semana": 0,
            "posts_publicados_semana": 0,
            "interacoes_semana": 0,
            "semana_legenda": "Sem janela semanal carregada",
            "semana_legenda_curta": "--",
            "creators_coleta_recente": recent_collectors,
        }

    weekly_df = pd.DataFrame(weekly_rows)
    weekly_df["week_end"] = pd.to_datetime(weekly_df.get("week_end"), errors="coerce", utc=True)
    weekly_df["views_novas"] = pd.to_numeric(weekly_df.get("views_novas"), errors="coerce").fillna(0)
    weekly_df["likes_novos"] = pd.to_numeric(weekly_df.get("likes_novos"), errors="coerce").fillna(0)
    weekly_df["comentarios_novos"] = pd.to_numeric(weekly_df.get("comentarios_novos"), errors="coerce").fillna(0)
    latest_week_end = weekly_df["week_end"].max()
    latest_week_rows = weekly_df[weekly_df["week_end"] == latest_week_end].copy()

    creators_ativos = int(
        latest_week_rows.loc[
            pd.to_numeric(latest_week_rows.get("videos_publicados"), errors="coerce").fillna(0) > 0,
            "creator_id",
        ].nunique()
    )
    posts_publicados = int(
        pd.to_numeric(latest_week_rows.get("videos_publicados"), errors="coerce").fillna(0).sum()
    )
    interacoes_semana = int(
        (latest_week_rows["views_novas"] + latest_week_rows["likes_novos"] + latest_week_rows["comentarios_novos"]).sum()
    )
    week_label = str(latest_week_rows["week_label"].dropna().iloc[0]) if not latest_week_rows.empty else "Sem semana fechada"

    return {
        "creators_ativos_semana": creators_ativos,
        "posts_publicados_semana": posts_publicados,
        "interacoes_semana": interacoes_semana,
        "semana_legenda": f"Janela fechada: {week_label}",
        "semana_legenda_curta": week_label,
        "creators_coleta_recente": recent_collectors,
    }


def build_overview_recent_activity_frame(weekly_rows: list[dict[str, Any]]) -> pd.DataFrame:
    if not weekly_rows:
        return pd.DataFrame()

    weekly_df = pd.DataFrame(weekly_rows).copy()
    if weekly_df.empty:
        return pd.DataFrame()

    weekly_df["week_end"] = pd.to_datetime(weekly_df.get("week_end"), errors="coerce", utc=True)
    weekly_df["week_start"] = pd.to_datetime(weekly_df.get("week_start"), errors="coerce", utc=True)
    weekly_df["videos_publicados"] = pd.to_numeric(weekly_df.get("videos_publicados"), errors="coerce").fillna(0)
    weekly_df["views_novas"] = pd.to_numeric(weekly_df.get("views_novas"), errors="coerce").fillna(0)
    weekly_df["likes_novos"] = pd.to_numeric(weekly_df.get("likes_novos"), errors="coerce").fillna(0)
    weekly_df["comentarios_novos"] = pd.to_numeric(weekly_df.get("comentarios_novos"), errors="coerce").fillna(0)
    weekly_df["interacoes"] = (
        weekly_df["views_novas"] + weekly_df["likes_novos"] + weekly_df["comentarios_novos"]
    )

    grouped = (
        weekly_df.groupby(["week_start", "week_end", "week_label"], dropna=False)
        .agg(
            posts_publicados=("videos_publicados", "sum"),
            interacoes=("interacoes", "sum"),
            creators_ativos=("creator_id", lambda values: pd.Series(values)[pd.Series(values).notna()].nunique()),
        )
        .reset_index()
        .sort_values("week_end")
    )

    if grouped.empty:
        return grouped

    grouped_week_start = pd.to_datetime(grouped["week_start"], errors="coerce", utc=True).dt.tz_localize(None)
    grouped = grouped[grouped_week_start >= CREATOR_WEEKLY_ACTIVITY_CUTOFF].copy()
    if grouped.empty:
        return grouped

    grouped["week_label_short"] = grouped["week_label"].fillna("--")
    grouped["creators_ativos"] = grouped["creators_ativos"].astype(int)
    grouped["posts_publicados"] = grouped["posts_publicados"].astype(int)
    grouped["interacoes"] = grouped["interacoes"].astype(int)
    return grouped


def filter_overview_recent_activity_frame(
    chart_df: pd.DataFrame,
    selected_week_label: str | None,
    trailing_weeks: int = OVERVIEW_RECENT_ACTIVITY_WINDOW_WEEKS,
) -> pd.DataFrame:
    if chart_df is None or chart_df.empty:
        return pd.DataFrame()
    ordered = chart_df.sort_values("week_end").reset_index(drop=True)
    if selected_week_label:
        matched = ordered.index[ordered["week_label"].astype(str) == str(selected_week_label)].tolist()
        if matched:
            return ordered.iloc[: matched[-1] + 1].tail(trailing_weeks).copy()
    return ordered.tail(trailing_weeks).copy()


def summarize_overview_recent_focus(
    chart_df: pd.DataFrame,
    fallback_summary: dict[str, Any],
) -> dict[str, Any]:
    if chart_df is None or chart_df.empty:
        return {
            "posts_publicados_semana": int(fallback_summary.get("posts_publicados_semana") or 0),
            "interacoes_semana": int(fallback_summary.get("interacoes_semana") or 0),
            "creators_ativos_semana": int(fallback_summary.get("creators_ativos_semana") or 0),
            "semana_legenda": str(fallback_summary.get("semana_legenda") or "Sem semana fechada"),
            "posts_caption": "Sem semana anterior",
            "posts_caption_color": "#aeb4bf",
            "interacoes_caption": "Sem semana anterior",
            "interacoes_caption_color": "#aeb4bf",
            "creators_caption": "Sem semana anterior",
            "creators_caption_color": "#aeb4bf",
        }

    ordered = chart_df.sort_values("week_end").reset_index(drop=True)
    latest_row = ordered.iloc[-1]
    previous_row = ordered.iloc[-2] if len(ordered.index) > 1 else None

    latest_posts = int(latest_row.get("posts_publicados") or 0)
    latest_interacoes = int(latest_row.get("interacoes") or 0)
    latest_creators = int(latest_row.get("creators_ativos") or 0)
    previous_posts = int(previous_row.get("posts_publicados") or 0) if previous_row is not None else None
    previous_interacoes = int(previous_row.get("interacoes") or 0) if previous_row is not None else None
    previous_creators = int(previous_row.get("creators_ativos") or 0) if previous_row is not None else None

    posts_caption, posts_caption_color = growth_caption_from_values(latest_posts, previous_posts)
    interacoes_caption, interacoes_caption_color = weekly_growth_caption(latest_interacoes, previous_interacoes)
    creators_caption, creators_caption_color = growth_caption_from_values(latest_creators, previous_creators)
    return {
        "posts_publicados_semana": latest_posts,
        "interacoes_semana": latest_interacoes,
        "creators_ativos_semana": latest_creators,
        "semana_legenda": f"Janela fechada: {latest_row.get('week_label') or '--'}",
        "posts_caption": posts_caption,
        "posts_caption_color": posts_caption_color,
        "interacoes_caption": interacoes_caption,
        "interacoes_caption_color": interacoes_caption_color,
        "creators_caption": creators_caption,
        "creators_caption_color": creators_caption_color,
    }


def build_overview_recent_activity_chart(chart_df: pd.DataFrame) -> Any:
    if chart_df is None or chart_df.empty:
        return None

    tick_values = []
    tick_text = []
    week_labels = chart_df["week_label_short"].tolist()
    if week_labels:
        tick_values = [week_labels[0]]
        tick_text = [week_labels[0]]
        if len(week_labels) > 1 and week_labels[-1] != week_labels[0]:
            tick_values.append(week_labels[-1])
            tick_text.append(week_labels[-1])

    fig = go.Figure()
    fig.add_scatter(
        x=chart_df["week_label_short"],
        y=chart_df["interacoes"],
        name="Interacoes",
        mode="lines",
        line=dict(color="#ff8069", width=3),
        hovertemplate="Semana %{x}<br>Interacoes: %{y}<extra></extra>",
    )
    fig.add_scatter(
        x=chart_df["week_label_short"],
        y=chart_df["posts_publicados"],
        name="Novos posts",
        mode="lines",
        line=dict(color="#f2c14e", width=3),
        fill="tozeroy",
        fillcolor="rgba(242, 193, 78, 0.24)",
        yaxis="y2",
        hovertemplate="Semana %{x}<br>Novos posts: %{y}<extra></extra>",
    )
    fig.update_layout(
        xaxis_title=None,
        yaxis_title=None,
        yaxis2=dict(
            title=None,
            overlaying="y",
            side="right",
            showgrid=False,
            zeroline=False,
            range=[0, 1000],
        ),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="left",
            x=0,
        ),
        margin=dict(l=16, r=64, t=24, b=16),
        hovermode="x unified",
        xaxis=dict(
            tickmode="array" if tick_values else "auto",
            tickvals=tick_values,
            ticktext=tick_text,
            tickangle=0,
            showgrid=False,
            zeroline=False,
        ),
        yaxis=dict(
            title=None,
            showgrid=False,
            zeroline=False,
        ),
    )
    apply_plotly_theme(fig, legend_title="Serie")
    fig.update_layout(
        paper_bgcolor="#15171c",
        plot_bgcolor="#15171c",
    )
    fig.update_xaxes(showgrid=False, zeroline=False)
    fig.update_yaxes(showgrid=False, zeroline=False)
    return fig


def summarize_overview_fenabrave(rows: list[dict[str, Any]]) -> dict[str, Any]:
    if not rows:
        return {
            "periodo": "Fenabrave sem dados carregados",
            "cards": [],
        }

    df = pd.DataFrame(rows)
    df["reference_period"] = pd.to_datetime(df.get("reference_period"), errors="coerce")
    if "segment_code" in df.columns:
        df["segment_code"] = df["segment_code"].astype(str)
    else:
        df["segment_code"] = ""
    latest_period = df["reference_period"].max()
    latest_df = df[
        (df["reference_period"] == latest_period)
        & (df["segment_code"].str.lower() != "implementos_rodoviarios")
    ].copy()

    if latest_df.empty or pd.isna(latest_period):
        return {
            "periodo": "Fenabrave sem periodo valido",
            "cards": [],
        }

    latest_df["monthly_units"] = pd.to_numeric(latest_df.get("monthly_units"), errors="coerce").fillna(0)
    latest_df["current_year_accumulated_units"] = pd.to_numeric(
        latest_df.get("current_year_accumulated_units"),
        errors="coerce",
    ).fillna(0)
    latest_df["segment_sort"] = pd.to_numeric(latest_df.get("segment_sort"), errors="coerce").fillna(999).astype(int)
    latest_df = latest_df.sort_values(["segment_sort", "segment_label"]).copy()

    cards = []
    for _, row in latest_df.iterrows():
        picto = FENABRAVE_PICTOS.get(str(row.get("picto_code") or ""), str(row.get("picto_code") or "AV"))
        cards.append(
            metric_card_html(
                str(row.get("segment_short_label") or row.get("segment_label") or "--"),
                format_int(row.get("monthly_units") or 0),
                f"Acumulado ano: {format_int(row.get('current_year_accumulated_units') or 0)}",
                picto,
                str(row.get("color_hex") or "#ff8069"),
            )
        )

    return {
        "periodo": f"Referencia {format_month_label(pd.Timestamp(latest_period))}",
        "cards": cards,
    }


def humanize_overview_list(values: list[str], singular_label: str) -> str:
    if not values:
        return f"Sem {singular_label}s carregados"
    if len(values) == 1:
        return values[0].title()
    if len(values) == 2:
        return f"{values[0].title()} e {values[1].title()}"
    return f"{values[0].title()} + {len(values) - 1} outros"


def format_overview_date(value: Any) -> str:
    if value is None or value == "" or pd.isna(value):
        return "--"
    timestamp = pd.Timestamp(value)
    if timestamp.tzinfo is None:
        timestamp = timestamp.tz_localize("UTC")
    return timestamp.tz_convert("America/Sao_Paulo").strftime("%d/%m/%Y")


def render_fenabrave_dashboard_page() -> None:
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

    chart_df = df.sort_values(["reference_period", "segment_sort"])
    category_colors = {
        row["segment_label"]: row["color_hex"]
        for _, row in df.drop_duplicates("segment_label").iterrows()
    }

    fig = px.bar(
        chart_df,
        x="month_display",
        y="monthly_units",
        color="segment_label",
        barmode="group",
        category_orders={"month_display": month_order},
        color_discrete_map=category_colors,
        labels={
            "month_display": "Mes",
            "monthly_units": "Emplacamentos",
            "segment_label": "Categoria",
        },
    )
    apply_plotly_theme(fig)
    trace_startup("render_fenabrave_monthly bar_chart before")
    st.plotly_chart(fig, width="stretch")
    trace_startup("render_fenabrave_monthly bar_chart after")

    st.write("")
    st.markdown("### Evolucao mensal por categoria")

    line_fig = px.line(
        chart_df,
        x="month_display",
        y="monthly_units",
        color="segment_label",
        markers=True,
        category_orders={"month_display": month_order},
        color_discrete_map=category_colors,
        labels={
            "month_display": "Mes",
            "monthly_units": "Emplacamentos",
            "segment_label": "Categoria",
        },
    )
    apply_plotly_theme(line_fig)
    line_fig.update_traces(line_width=3, marker_size=8)
    trace_startup("render_fenabrave_monthly line_chart before")
    st.plotly_chart(line_fig, width="stretch")
    trace_startup("render_fenabrave_monthly line_chart after")


def render_collection_integrity_section() -> None:
    trace_startup("render_collection_integrity start")
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
        discovery_execution_timestamp = discovery_status.get("ultima_execucao_discovery")
        discovery_post_timestamp = discovery_status.get("ultima_descoberta_de_post")
        discovery_evidence_timestamp = discovery_status.get("ultima_evidencia_discovery")
        discovery_snapshot_value = str(
            discovery_status.get("ultima_evidencia_discovery_br")
            or (format_timestamp_br(discovery_evidence_timestamp) if discovery_evidence_timestamp else None)
            or discovery_status.get("ultima_execucao_discovery_br")
            or (format_timestamp_br(discovery_execution_timestamp) if discovery_execution_timestamp else None)
            or discovery_status.get("ultima_descoberta_de_post_br")
            or (format_timestamp_br(discovery_post_timestamp) if discovery_post_timestamp else None)
            or "--"
        )
        discovery_latest_post = str(
            discovery_status.get("ultima_descoberta_de_post_br")
            or (format_timestamp_br(discovery_post_timestamp) if discovery_post_timestamp else None)
            or "--"
        )
        discovery_evidence_source = str(discovery_status.get("fonte_ultima_evidencia") or "--")
        discovery_checked_creators = format_int(discovery_status.get("creators_avaliados_24h"))
        discovery_new_posts = format_int(discovery_status.get("novos_posts_24h"))
        discovery_new_posts_6h = format_int(discovery_status.get("novos_posts_6h"))
    else:
        discovery_status_code = "neutral"
        discovery_status_label = "Aguardando view"
        discovery_status_reason = "Worker de descoberta roda a cada 3 horas e ainda precisa de uma view propria."
        discovery_snapshot_value = "--"
        discovery_latest_post = "--"
        discovery_evidence_source = "--"
        discovery_checked_creators = "--"
        discovery_new_posts = "--"
        discovery_new_posts_6h = "--"

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

    collection_status_code = combine_worker_status(raw_status_code, discovery_status_code)

    panels = [
        worker_panel_html(
            "Integridade da coleta",
            "Leitura executiva separada por worker operacional.",
            [
                worker_stat_html("Atualizacao de posts", status_label, status_reason, raw_status_code),
                worker_stat_html("Descoberta de novos posts", discovery_status_label, discovery_status_reason, discovery_status_code),
            ],
            "#ff8069",
            collection_status_code,
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
                    (
                        f"Fonte: {discovery_evidence_source} | "
                        f"Snapshots canal 24h: {discovery_checked_creators} | "
                        f"Novos posts 6h: {discovery_new_posts_6h} | "
                        f"Novos posts 24h: {discovery_new_posts} | "
                        f"Ultima descoberta: {discovery_latest_post}"
                    ),
                    discovery_status_code,
                ),
            ],
            "#98df96",
            collection_status_code,
        ),
        worker_panel_html(
            "Sinais operacionais",
            "Leitura de atraso e risco de cobertura do worker de metricas.",
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
    with st.expander("Passo a passo enxuto de implementacao", expanded=False):
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
    trace_startup("render_collection_integrity end")


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
        "fenabrave_pdf_uploaded": False,
        "fenabrave_metadata_registered": False,
        "fenabrave_preview_ready": False,
        "fenabrave_validated": False,
    }
    for key, value in defaults.items():
        st.session_state.setdefault(key, value)
    return {key: st.session_state[key] for key in defaults}


def get_fenabrave_record_for_period(
    records: list[dict[str, Any]],
    reference_period: date,
) -> dict[str, Any] | None:
    target_label = pd.Timestamp(normalize_fenabrave_reference_period(reference_period)).strftime("%Y-%m-%d")
    normalized_candidates: list[dict[str, Any]] = []
    for row in records:
        row_period_raw = row.get("reference_period")
        if row_period_raw in (None, ""):
            continue
        try:
            row_period_timestamp = pd.Timestamp(row_period_raw)
        except Exception:
            continue
        row_period_exact = row_period_timestamp.strftime("%Y-%m-%d")
        if row_period_exact == target_label:
            return row
        row_period_normalized = row_period_timestamp.to_period("M").to_timestamp().strftime("%Y-%m-%d")
        if row_period_normalized == target_label:
            normalized_candidates.append(row)
    return normalized_candidates[0] if normalized_candidates else None


def get_fenabrave_preview_rows(reference_period: date) -> list[dict[str, Any]]:
    period_label = pd.Timestamp(normalize_fenabrave_reference_period(reference_period)).strftime("%Y-%m-%d")
    rows, error = get_filtered_rows(
        "v_dashboard_fenabrave_monthly_segments",
        filters=(("reference_period", period_label),),
        order_by="segment_sort",
    )
    if error:
        return []
    return rows


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


def build_creator_channel_url(row: dict[str, Any]) -> str:
    platform = str(row.get("platform") or "").strip().lower()
    if platform != "youtube":
        return ""

    channel_id = str(row.get("channel_id") or "").strip()
    if channel_id:
        if channel_id.startswith(("http://", "https://")):
            return channel_id
        return f"https://www.youtube.com/channel/{channel_id}"

    username_value = str(row.get("username") or "").strip().lstrip("@")
    if username_value:
        return f"https://www.youtube.com/@{username_value}"

    return ""


def format_ordinal_rank(position: int) -> str:
    return f"{position}º"


def get_delta_color(delta_value: float | int | None) -> str:
    if delta_value is None:
        return "#aeb4bf"
    if delta_value > 0:
        return "#2f9e62"
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


def sum_numeric_column(df: pd.DataFrame, column_name: str) -> int:
    if column_name not in df.columns or df.empty:
        return 0
    return int(pd.to_numeric(df[column_name], errors="coerce").fillna(0).sum())


def engagement_rate_from_totals(views: int, likes: int, comments: int) -> float:
    if views <= 0:
        return 0.0
    return round(((likes + comments) / views) * 100, 2)


def engagement_weighted_components(views: int, likes: int, comments: int) -> pd.DataFrame:
    return pd.DataFrame(
        {
            "metrica": ["Views x1", "Likes x10", "Comentarios x20"],
            "valor": [
                max(views, 0) * 1,
                max(likes, 0) * 10,
                max(comments, 0) * 20,
            ],
        }
    )


def growth_caption_from_values(current_value: int, previous_value: int | None) -> tuple[str, str]:
    if previous_value is None:
        return "Sem semana anterior", "#aeb4bf"
    delta_value = current_value - previous_value
    if previous_value <= 0:
        return "Sem base anterior", get_delta_color(delta_value)
    pct_value = round((delta_value / previous_value) * 100, 2)
    return format_growth_caption(delta_value, pct_value)


def nullable_int(value: Any) -> int | None:
    if value in (None, ""):
        return None
    try:
        if pd.isna(value):
            return None
        return int(value)
    except (TypeError, ValueError):
        return None


def weekly_row_has_metric_base(row: dict[str, Any]) -> bool:
    if bool(row.get("semana_tem_base")):
        return True
    return (nullable_int(row.get("posts_com_base_para_delta")) or 0) > 0


def weekly_growth_caption(current_value: int | None, previous_value: int | None) -> tuple[str, str]:
    if current_value is None:
        return "Sem base semanal", "#aeb4bf"
    return growth_caption_from_values(current_value, previous_value)


def weekly_audience_caption(status: Any) -> tuple[str, str]:
    status_key = str(status or "").strip().lower()
    if status_key == "cresceu":
        return "Cresceu vs semana anterior", "#7ddc8e"
    if status_key == "caiu":
        return "Caiu vs semana anterior", "#ff7b6f"
    if status_key == "estavel":
        return "Estavel vs semana anterior", "#f4c453"
    return "Sem base semanal", "#aeb4bf"


def render_external_intake_page(page_title: str = "Cadastro de Criadores") -> None:
    page_header(page_title, "Intake controlado ligado ao Supabase")
    process_banner(
        "Regra obrigatoria de governanca",
        "A UI guia o cadastro, mas a entidade e os vinculos de subnicho continuam passando por entity_intake e revisao antes de virarem base final.",
    )

    connection_error = None if is_supabase_configured() else "Supabase ainda nao configurado. Adicione SUPABASE_URL e SUPABASE_ANON_KEY nos secrets."
    render_connection_notice(connection_error)

    entity_matches = st.session_state.get("creator_intake_entity_matches", [])
    channel_matches = st.session_state.get("creator_intake_channel_matches", [])
    last_intake_rows = st.session_state.get("creator_intake_last_rows", [])
    creator_created = st.session_state.get("creator_intake_creator_row")
    entity_exact_match = any(row.get("match_type") in {"display_name", "normalized_name"} for row in entity_matches)

    step_cards = [
        process_step_card(
            "Etapa 1",
            "Entidade",
            "Checar nome exibido e nome normalizado. Se nao existir, enviar solicitacao para public.entity_intake.",
            "ok-green" if entity_exact_match else "alert-yellow",
            "resolvida" if entity_exact_match else "intake",
        ),
        process_step_card(
            "Etapa 2",
            "Criador",
            "Cadastrar em public.creators apenas com entity_id resolvido, platform valido e channel_id sem duplicidade.",
            "ok-green" if creator_created else "neutral",
            "cadastrado" if creator_created else "pendente",
        ),
        process_step_card(
            "Etapa 3",
            "Associacao de nichos",
            "Selecionar subnichos existentes ou registrar solicitacao controlada para revisao.",
            "ok-green" if last_intake_rows else "neutral",
            "registrada" if last_intake_rows else "aguardando",
        ),
        process_step_card(
            "Etapa 4",
            "Revisao e publicacao",
            "Publicar uma linha de intake por vez via RPC controlada e resolver o entity_id sem sair do Streamlit.",
            "ok-green" if any(row.get("status") == "published" for row in last_intake_rows) else "alert-yellow",
            "acompanhar",
        ),
    ]
    process_step_grid(step_cards)

    tab_form, tab_review, tab_rules = st.tabs(["Novo criador de conteudo", "Revisao de intake", "Regras da governanca"])

    with tab_form:
        sub_niche_rows, sub_niche_error = get_sub_niches_for_intake()
        sub_niche_names = [str(row["sub_niche_name"]) for row in sub_niche_rows if row.get("sub_niche_name")]
        if st.session_state.get("creator_intake_reset_pending"):
            apply_creator_intake_form_reset(sub_niche_names)
        ensure_creator_intake_form_defaults(sub_niche_names)

        if sub_niche_error:
            st.warning(sub_niche_error)

        success_message = st.session_state.get("creator_intake_success_message")
        if success_message:
            st.success(success_message)

        col_left, col_right = st.columns([1.35, 1])

        with col_left:
            st.markdown("### 1. Cadastrar entidade")
            raw_name = st.text_input("Nome da Entidade", key="creator_intake_raw_name")
            normalized_name = normalize_name_for_intake(raw_name)
            creator_type = st.selectbox("Tipo de criador", ["mid-tier", "editorial", "independente"], key="creator_intake_creator_type")
            st.caption(f"Nome normalizado sugerido: {normalized_name or '--'}")

            if st.button("Checar entidade no banco", use_container_width=False, disabled=bool(connection_error)):
                matches, error = call_supabase_rpc("search_entities_for_intake", {"p_raw_name": raw_name})
                st.session_state["creator_intake_entity_matches"] = matches
                st.session_state["creator_intake_entity_error"] = error
                st.session_state["creator_intake_entity_checked_name"] = raw_name
                st.session_state["creator_intake_last_rows"] = []
                st.session_state["creator_intake_creator_row"] = None
                st.session_state["creator_intake_onboarding_result"] = None
                st.session_state["creator_intake_onboarding_error"] = None
                if error:
                    st.warning(error)
                else:
                    st.success("Checagem concluida.")

            entity_matches = st.session_state.get("creator_intake_entity_matches", [])
            entity_error = st.session_state.get("creator_intake_entity_error")
            if st.session_state.get("creator_intake_entity_checked_name") != raw_name:
                entity_matches = []
                entity_error = None
            if entity_error:
                st.warning(entity_error)

            resolved_entity = None
            if entity_matches:
                match_labels = [
                    f'{row["entity_name"]} | id {row["entity_id"]} | {row["match_type"]}'
                    for row in entity_matches
                ]
                selected_match_label = st.selectbox("Entidades encontradas", match_labels)
                resolved_entity = entity_matches[match_labels.index(selected_match_label)]
                exact_matches = [row for row in entity_matches if row.get("match_type") in {"display_name", "normalized_name"}]
                if exact_matches:
                    st.info("Entidade existente encontrada. O cadastro de nova entidade fica bloqueado; use a entidade resolvida para o criador.")
                else:
                    st.warning("Foram encontradas correspondencias parciais. Revise antes de cadastrar uma nova entidade.")
            else:
                st.info("Entidade nao encontrada nesta sessao. Para entidade nova, envie para entity_intake e publique pela propria tela.")

            st.markdown("### 2. Cadastrar criador")
            platform = st.selectbox("Plataforma", ["youtube", "instagram", "tiktok"], key="creator_intake_platform")
            username = st.text_input("Username", key="creator_intake_username")
            channel_id = st.text_input("Channel ID", key="creator_intake_channel_id")
            followers = st.number_input("Followers", min_value=0, step=1000, key="creator_intake_followers")

            if st.button("Checar canal no banco", use_container_width=False, disabled=bool(connection_error) or not channel_id.strip()):
                matches, error = call_supabase_rpc(
                    "search_creators_for_intake",
                    {"p_platform": platform, "p_channel_id": channel_id},
                )
                st.session_state["creator_intake_channel_matches"] = matches
                st.session_state["creator_intake_channel_error"] = error
                st.session_state["creator_intake_channel_checked_value"] = f"{platform}:{channel_id}"
                st.session_state["creator_intake_onboarding_result"] = None
                st.session_state["creator_intake_onboarding_error"] = None
                if error:
                    st.warning(error)
                elif matches:
                    st.warning("Canal ja existe na base. O cadastro final deve ficar bloqueado.")
                else:
                    st.success("Canal nao encontrado em public.creators.")

            channel_matches = st.session_state.get("creator_intake_channel_matches", [])
            channel_error = st.session_state.get("creator_intake_channel_error")
            if st.session_state.get("creator_intake_channel_checked_value") != f"{platform}:{channel_id}":
                channel_matches = []
                channel_error = None
            if channel_error:
                st.warning(channel_error)
            if channel_matches:
                trace_startup("render_creator_intake channel_matches_dataframe before")
                st.dataframe(pd.DataFrame(channel_matches), width="stretch", hide_index=True)
                trace_startup("render_creator_intake channel_matches_dataframe after")

            st.markdown("### 3. Associar nichos")
            linked_entity_name = str(resolved_entity["entity_name"]) if resolved_entity else raw_name
            st.text_input("Entidade que recebera a associacao", value=linked_entity_name, disabled=True)
            niche = st.selectbox("Nicho", ["automotivo"], index=0, key="creator_intake_niche")
            selected_sub_niches = st.multiselect(
                "Subnichos existentes",
                sub_niche_names,
                key="creator_intake_selected_sub_niches",
            )
            taxonomy_request = st.text_input("Solicitar novo subnicho para revisao", key="creator_intake_taxonomy_request")
            intake_notes = st.text_area("Observacao da solicitacao", height=88, key="creator_intake_notes")

            st.markdown("### Acoes")
            intake_targets = selected_sub_niches + ([taxonomy_request.strip()] if taxonomy_request.strip() else [])
            can_send_intake = bool(raw_name.strip()) and bool(intake_targets) and not connection_error
            if st.button("Enviar para entity_intake", use_container_width=True, disabled=not can_send_intake):
                created_rows: list[dict[str, Any]] = []
                errors: list[str] = []
                for sub_niche_name in intake_targets:
                    rows, error = call_supabase_rpc(
                        "create_entity_intake_entry",
                        {
                            "p_raw_name": raw_name,
                            "p_sub_niche_name": sub_niche_name,
                            "p_niche": niche,
                            "p_creator_type": creator_type,
                            "p_notes": intake_notes,
                        },
                    )
                    if error:
                        errors.append(error)
                    else:
                        created_rows.extend(rows)
                if created_rows:
                    clear_supabase_data_cache()
                    st.session_state["creator_intake_last_rows"] = created_rows
                    st.session_state["creator_intake_onboarding_result"] = None
                    st.session_state["creator_intake_onboarding_error"] = None
                    last_intake_rows = created_rows
                    st.success(f"{len(created_rows)} registro(s) enviado(s) para entity_intake.")
                if errors:
                    st.warning(" | ".join(errors))

            publishable_intake_rows = [
                row
                for row in last_intake_rows
                if row.get("id")
                and row.get("status") != "published"
                and row.get("sub_niche_id")
                and row.get("review_result") in {"READY_TO_INSERT", "ENTITY_ALREADY_EXISTS"}
            ]
            if publishable_intake_rows:
                if st.button("Publicar intake e resolver entidade", use_container_width=True, disabled=bool(connection_error)):
                    published_rows: list[dict[str, Any]] = []
                    publish_errors: list[str] = []
                    for intake_row in publishable_intake_rows:
                        rows, error = call_supabase_rpc(
                            "publish_entity_intake_entry",
                            {"p_intake_id": int(intake_row["id"])},
                        )
                        if error:
                            publish_errors.append(error)
                        else:
                            published_rows.extend(rows)
                    if published_rows:
                        clear_supabase_data_cache()
                        st.session_state["creator_intake_last_rows"] = published_rows
                        last_intake_rows = published_rows
                        refreshed_matches, refresh_error = call_supabase_rpc(
                            "search_entities_for_intake",
                            {"p_raw_name": raw_name},
                        )
                        st.session_state["creator_intake_entity_matches"] = refreshed_matches
                        st.session_state["creator_intake_entity_checked_name"] = raw_name
                        st.session_state["creator_intake_entity_error"] = refresh_error
                        entity_matches = refreshed_matches
                        resolved_entity = next(
                            (row for row in entity_matches if row.get("match_type") in {"display_name", "normalized_name"}),
                            entity_matches[0] if entity_matches else None,
                        )
                        if refresh_error:
                            st.warning(refresh_error)
                        else:
                            st.success("Intake publicado e entidade resolvida. Revise a selecao de entidade antes de cadastrar o criador.")
                    if publish_errors:
                        st.warning(" | ".join(publish_errors))

            creator_disabled_reason = []
            if connection_error:
                creator_disabled_reason.append("configure Supabase")
            if not resolved_entity:
                creator_disabled_reason.append("resolva ou publique a entidade")
            if not selected_sub_niches:
                creator_disabled_reason.append("selecione pelo menos um subnicho existente")
            if taxonomy_request.strip():
                creator_disabled_reason.append("novo subnicho precisa de revisao antes do creator")
            if not channel_id.strip():
                creator_disabled_reason.append("informe channel_id")
            if channel_matches:
                creator_disabled_reason.append("channel_id ja cadastrado")
            can_create_creator = not creator_disabled_reason
            if st.button("Cadastrar criador no Supabase", use_container_width=True, disabled=not can_create_creator):
                rows, error = call_supabase_rpc(
                    "create_creator_from_resolved_entity",
                    {
                        "p_entity_id": int(resolved_entity["entity_id"]),
                        "p_platform": platform,
                        "p_username": username,
                        "p_channel_id": channel_id,
                        "p_followers": int(followers),
                    },
                )
                if error:
                    st.warning(error)
                elif rows:
                    clear_supabase_data_cache()
                    creator_summary = build_creator_created_summary(rows[0], resolved_entity, selected_sub_niches)
                    st.session_state["creator_intake_creator_row"] = creator_summary
                    creator_created = creator_summary
                    creator_id = int(creator_summary["creator_id"])

                    if platform == "youtube":
                        with st.spinner("Executando discovery inicial do novo creator..."):
                            onboarding_result, onboarding_error = trigger_creator_onboarding(creator_id)
                    else:
                        onboarding_result = {
                            "status": "skipped",
                            "reason": "platform_not_youtube",
                            "creator_id": creator_id,
                        }
                        onboarding_error = None

                    st.session_state["creator_intake_onboarding_result"] = onboarding_result
                    st.session_state["creator_intake_onboarding_error"] = onboarding_error
                    st.session_state["creator_intake_success_message"] = (
                        "Criador cadastrado com sucesso. "
                        f"Creator ID {creator_summary['creator_id']} | "
                        f"Entidade {creator_summary['entity_name']} (ID {creator_summary['entity_id']}) | "
                        f"Plataforma {creator_summary['platform']} | "
                        f"Username {creator_summary['username']} | "
                        f"Channel ID {creator_summary['channel_id']} | "
                        f"Followers {format_int(creator_summary['followers'])} | "
                        f"Subnichos {creator_summary['sub_niches']}."
                    )
                    schedule_creator_intake_form_reset()
                    st.rerun()

        with col_right:
            st.markdown("### Leitura da UI")
            exact_entity = bool(resolved_entity and resolved_entity.get("match_type") in {"display_name", "normalized_name"})
            partial_entity = bool(resolved_entity and resolved_entity.get("match_type") == "partial_name")
            local_warnings = []
            if not entity_matches:
                local_warnings.append("Entidade ainda nao resolvida. Para uma entidade nova, envie para intake e publique pela propria tela.")
            if partial_entity:
                local_warnings.append("Ha apenas correspondencia parcial. Revise antes de seguir.")
            if not selected_sub_niches and not taxonomy_request.strip():
                local_warnings.append("Escolha um subnicho existente ou registre uma solicitacao para revisao.")
            if taxonomy_request.strip():
                local_warnings.append("Novo nicho ou subnicho deve entrar como solicitacao controlada, nao como cadastro direto.")
            if not channel_id.strip():
                local_warnings.append("Channel ID e obrigatorio para o cadastro final do criador.")
            if creator_disabled_reason:
                local_warnings.append("Cadastro final bloqueado: " + ", ".join(creator_disabled_reason) + ".")

            chips = [
                dq_chip("Entidade", "resolvida" if exact_entity else "revisar", "ok-green" if exact_entity else "alert-yellow"),
                dq_chip("Canal", "duplicado" if channel_matches else "ok", "alert-yellow" if channel_matches else "ok-green"),
                dq_chip("Subnichos", str(len(selected_sub_niches)), "ok-green" if selected_sub_niches else "alert-yellow"),
            ]
            st.markdown(
                dq_kpi_card(
                    "Prontidao do cadastro",
                    "Liberado" if can_create_creator else "Bloqueado",
                    "O creator so e gravado por RPC quando entity_id, canal e classificacao estao resolvidos.",
                    "#98df96" if can_create_creator else "#ff8069",
                    chips,
                ),
                unsafe_allow_html=True,
            )

            st.markdown("### Payload para entity_intake")
            st.json(
                {
                    "raw_name": raw_name,
                    "normalized_name": normalized_name,
                    "niche": niche,
                    "creator_type": creator_type,
                    "sub_niche_names": intake_targets,
                    "notes": intake_notes or None,
                    "status": "pending",
                }
            )

            st.markdown("### Payload para public.creators")
            st.json(
                {
                    "entity_id": resolved_entity.get("entity_id") if resolved_entity else None,
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
                    "associacoes_existentes": selected_sub_niches,
                    "solicitacao_taxonomia": taxonomy_request.strip() or None,
                }
            )

            if last_intake_rows:
                st.markdown("### Ultimo envio para review")
                review_card_grid(last_intake_rows)

            if creator_created:
                st.markdown("### Criador cadastrado")
                trace_startup("render_creator_intake created_creator_dataframe before")
                st.dataframe(
                    pd.DataFrame(
                        [
                            {
                                "Creator ID": creator_created.get("creator_id"),
                                "Entity ID": creator_created.get("entity_id"),
                                "Entidade": creator_created.get("entity_name"),
                                "Plataforma": creator_created.get("platform"),
                                "Username": creator_created.get("username"),
                                "Channel ID": creator_created.get("channel_id"),
                                "Followers": format_int(creator_created.get("followers")),
                                "Tipo": creator_created.get("creator_type"),
                                "Subnichos": creator_created.get("sub_niches"),
                            }
                        ]
                    ),
                    width="stretch",
                    hide_index=True,
                )
                trace_startup("render_creator_intake created_creator_dataframe after")

            onboarding_result = st.session_state.get("creator_intake_onboarding_result")
            onboarding_error = st.session_state.get("creator_intake_onboarding_error")
            if onboarding_result or onboarding_error:
                st.markdown("### Discovery inicial")
                if onboarding_error:
                    st.warning(onboarding_error)
                if onboarding_result:
                    if onboarding_result.get("status") == "processed":
                        st.success(
                            "Discovery inicial concluido: "
                            f"{int(onboarding_result.get('processed_posts') or 0)} posts processados."
                        )
                    elif onboarding_result.get("status") == "skipped":
                        reason = onboarding_result.get("reason")
                        if reason == "platform_not_youtube":
                            st.info("Discovery inicial ignorado: worker de onboarding e exclusivo para YouTube.")
                        else:
                            st.info("Discovery inicial ignorado: creator ja possui posts.")
                    else:
                        st.info(f"Discovery inicial retornou status: {onboarding_result.get('status')}.")
                    st.json(onboarding_result)
            elif not is_creator_onboarding_configured():
                st.markdown("### Discovery inicial")
                st.info("Configure CREATOR_ONBOARDING_WORKER_URL e ONBOARDING_WORKER_TOKEN para acionar o worker apos o cadastro.")

            if local_warnings:
                st.warning(" | ".join(local_warnings))
            else:
                st.success("O cadastro esta pronto para a acao permitida nesta etapa.")

    with tab_review:
        st.markdown("### Revisao v_entity_intake_review")
        refresh_col, _ = st.columns([0.25, 0.75])
        with refresh_col:
            if st.button("Atualizar revisao", use_container_width=True):
                clear_supabase_data_cache()
                st.rerun()

        review_rows, review_error = get_view_rows("v_entity_intake_review")
        if review_error:
            st.warning(review_error)
        elif review_rows:
            sorted_review_rows = sorted(review_rows, key=lambda row: str(row.get("created_at") or ""), reverse=True)
            review_card_grid(sorted_review_rows[:12])
            with st.expander("Detalhe tecnico da revisao", expanded=False):
                trace_startup("render_creator_intake review_dataframe before")
                st.dataframe(pd.DataFrame(sorted_review_rows), width="stretch", hide_index=True)
                trace_startup("render_creator_intake review_dataframe after")
        else:
            st.info("Nenhum registro encontrado em v_entity_intake_review.")

        onboarding_result = st.session_state.get("creator_intake_onboarding_result")
        onboarding_error = st.session_state.get("creator_intake_onboarding_error")
        if onboarding_error:
            onboarding_status = "atencao"
        elif onboarding_result and onboarding_result.get("status") in {"processed", "skipped"}:
            onboarding_status = "ok"
        else:
            onboarding_status = "neutral"

        timeline = [
            ("Cadastro em entity_intake", "ok" if last_intake_rows else "atencao"),
            ("Review via v_entity_intake_review", "ok" if review_rows and not review_error else "atencao"),
            ("Publish via public.publish_entity_intake_entry()", "ok" if any(row.get("status") == "published" for row in last_intake_rows) else "atencao"),
            ("Cadastro final em public.creators", "ok" if creator_created else "neutral"),
            ("Discovery inicial via Cloud Run", onboarding_status),
        ]
        st.markdown("### Estado atual do processo")
        st.markdown(
            "".join(dq_chip(label, status.upper(), "ok-green" if status == "ok" else "alert-yellow" if status == "atencao" else "neutral") for label, status in timeline),
            unsafe_allow_html=True,
        )

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
- Review vem antes de publish, e publish usa `public.publish_entity_intake_entry()` para uma linha por vez.
- `platform`, `channel_id` e `followers` viram creator somente por RPC controlada e com `entity_id` resolvido.
- O Streamlit deve funcionar como camada de operacao guiada, nao como editor SQL.
"""
        )


def render_creator_detail_page() -> None:
    trace_startup("render_creator_detail start")
    summary_rows, summary_error = get_view_rows("v_dashboard_creator_summary")
    rows = summary_rows or get_creator_mock_rows()
    selected_name = st.session_state.get("creator_selected_name", rows[0]["entity_name"])
    page_header("Criador individual")

    filter_col1, filter_col2, filter_col3, filter_col4 = st.columns([1.45, 1.05, 0.95, 1.0])
    with filter_col2:
        selected_platform = st.selectbox("Plataforma", ["todas", "youtube", "instagram", "tiktok"], index=1)
    working_rows = rows
    if selected_platform != "todas":
        working_rows = [
            row
            for row in working_rows
            if str(row.get("platform") or "").strip().lower() == selected_platform
        ]
    working_rows = sorted(working_rows, key=lambda row: float(row["engagement_rate_pct"]), reverse=True)

    if not working_rows:
        with filter_col1:
            st.selectbox("Criador em foco", ["Sem criador para a plataforma"], index=0, disabled=True)
        with filter_col3:
            st.selectbox("Tipo de video", ["todos", "long", "short"], index=0, disabled=True)
        with filter_col4:
            st.selectbox("Semana fechada", ["Sem base semanal"], index=0, disabled=True)
        st.info(f"Nenhum criador da view v_dashboard_creator_summary corresponde ao filtro de plataforma {selected_platform}.")
        trace_startup("render_creator_detail end: no creators for platform")
        return

    creator_options = working_rows
    selected_default = next((row for row in creator_options if row["entity_name"] == selected_name), creator_options[0])
    creator_option_names = [row["entity_name"] for row in creator_options]
    with filter_col1:
        selected_creator_name = st.selectbox(
            "Criador em foco",
            creator_option_names,
            index=creator_option_names.index(selected_default["entity_name"]),
        )
    with filter_col3:
        selected_video_type = st.selectbox("Tipo de video", ["todos", "long", "short"], index=0)

    st.session_state["creator_selected_name"] = selected_creator_name
    selected_row = next((row for row in working_rows if row["entity_name"] == selected_creator_name), working_rows[0])

    weekly_filters = [("creator_id", selected_row["creator_id"])]
    weekly_rows, weekly_error = get_filtered_rows(
        "v_dashboard_creator_weekly_activity",
        filters=tuple(weekly_filters),
        order_by="week_start",
        order_desc=False,
    )
    if not weekly_rows:
        weekly_rows = []
    weekly_rows = [
        row
        for row in weekly_rows
        if pd.to_datetime(row.get("week_start"), errors="coerce") >= CREATOR_WEEKLY_ACTIVITY_CUTOFF
    ]
    weekly_audience_rows, weekly_audience_error = get_filtered_rows(
        "v_dashboard_creator_weekly_audience",
        filters=tuple(weekly_filters),
        order_by="week_start",
        order_desc=False,
    )
    if not weekly_audience_rows:
        weekly_audience_rows = []
    weekly_audience_rows = [
        row
        for row in weekly_audience_rows
        if pd.to_datetime(row.get("week_start"), errors="coerce") >= CREATOR_WEEKLY_ACTIVITY_CUTOFF
    ]
    weekly_total_rows = [
        row
        for row in weekly_rows
        if str(row.get("video_type") or "").strip().lower() == "todos"
    ]

    period_options = [str(row["week_label"]) for row in reversed(weekly_total_rows)]
    latest_period_label = period_options[0] if period_options else "Sem base semanal"
    with filter_col4:
        selected_period_label = st.selectbox("Semana fechada", period_options or [latest_period_label], index=0)

    selected_week_row = next(
        (row for row in weekly_total_rows if str(row["week_label"]) == selected_period_label),
        weekly_total_rows[-1] if weekly_total_rows else {},
    )
    selected_week_audience_row = next(
        (row for row in weekly_audience_rows if str(row.get("week_label")) == selected_period_label),
        {},
    )
    selected_week_start = str(selected_week_row.get("week_start") or "")
    weekly_selected_type_rows = (
        [
            row
            for row in weekly_rows
            if str(row.get("video_type") or "").strip().lower() == selected_video_type
        ]
        if selected_video_type != "todos"
        else weekly_total_rows
    )
    selected_week_metric_row = next(
        (row for row in weekly_selected_type_rows if str(row.get("week_label")) == selected_period_label),
        selected_week_row if selected_video_type == "todos" else {},
    )
    post_filters = [("creator_id", selected_row["creator_id"])]
    if selected_video_type != "todos":
        post_filters.append(("video_type", selected_video_type))
    filtered_post_rows, top_videos_error = get_filtered_rows(
        "posts",
        filters=tuple(post_filters),
        order_by="views",
        order_desc=True,
    )
    if top_videos_error:
        filtered_posts_df = get_creator_top_videos(selected_row["entity_name"])
    else:
        filtered_posts_df = pd.DataFrame(filtered_post_rows)
    if selected_video_type != "todos" and "video_type" in filtered_posts_df.columns:
        filtered_posts_df = filtered_posts_df[
            filtered_posts_df["video_type"].astype(str).str.lower() == selected_video_type
        ]
    top_videos_df = (
        filtered_posts_df.sort_values(by="views", ascending=False, na_position="last").head(10)
        if "views" in filtered_posts_df.columns
        else filtered_posts_df.head(10)
    )

    total_videos_filtered = len(filtered_posts_df)
    total_views_filtered = sum_numeric_column(filtered_posts_df, "views")
    total_likes_filtered = sum_numeric_column(filtered_posts_df, "likes")
    total_comments_filtered = sum_numeric_column(filtered_posts_df, "comments")
    engagement_rank, engagement_total = get_engagement_rank(working_rows or rows, selected_row["entity_name"])
    engagement_rank_display = format_ordinal_rank(engagement_rank)

    selected_week_index = next(
        (index for index, row in enumerate(weekly_selected_type_rows) if str(row.get("week_label")) == selected_period_label),
        None,
    )
    previous_week_row = weekly_selected_type_rows[selected_week_index - 1] if selected_week_index is not None and selected_week_index > 0 else None

    selected_week_has_metric_base = weekly_row_has_metric_base(selected_week_metric_row)
    previous_week_has_metric_base = weekly_row_has_metric_base(previous_week_row or {})

    weekly_videos_value = int(selected_week_metric_row.get("videos_publicados") or 0)
    weekly_views_value = nullable_int(selected_week_metric_row.get("views_novas")) if selected_week_has_metric_base else None
    weekly_likes_value = nullable_int(selected_week_metric_row.get("likes_novos")) if selected_week_has_metric_base else None
    weekly_comments_value = nullable_int(selected_week_metric_row.get("comentarios_novos")) if selected_week_has_metric_base else None
    previous_week_videos_value = int(previous_week_row.get("videos_publicados") or 0) if previous_week_row else None
    previous_week_views_value = nullable_int(previous_week_row.get("views_novas")) if previous_week_has_metric_base else None
    previous_week_likes_value = nullable_int(previous_week_row.get("likes_novos")) if previous_week_has_metric_base else None
    previous_week_comments_value = nullable_int(previous_week_row.get("comentarios_novos")) if previous_week_has_metric_base else None
    weekly_followers_value = nullable_int(selected_week_audience_row.get("followers_delta_vs_prev_week")) if selected_week_audience_row else None
    weekly_followers_status = str(selected_week_audience_row.get("followers_weekly_status") or "") if selected_week_audience_row else ""
    weekly_followers_caption, weekly_followers_caption_color = weekly_audience_caption(weekly_followers_status)
    weekly_followers_display = format_compact_number(weekly_followers_value) if weekly_followers_value is not None else "--"

    chart_rows = []
    for row in [row for row in weekly_selected_type_rows if str(row["week_start"]) <= str(selected_week_row.get("week_start", ""))][-8:]:
        if not weekly_row_has_metric_base(row):
            continue
        chart_rows.append(
            {
                "week_label": str(row.get("week_label") or ""),
                "views_novas": nullable_int(row.get("views_novas")) or 0,
                "likes_novos": nullable_int(row.get("likes_novos")) or 0,
                "comentarios_novos": nullable_int(row.get("comentarios_novos")) or 0,
                "views_growth_pct_vs_prev_week": row.get("views_growth_pct_vs_prev_week"),
            }
        )
    weekly_df = pd.DataFrame(chart_rows, columns=["week_label", "views_novas", "likes_novos", "comentarios_novos", "views_growth_pct_vs_prev_week"])

    weekly_videos_caption, weekly_videos_caption_color = growth_caption_from_values(
        weekly_videos_value,
        previous_week_videos_value,
    )
    weekly_views_caption, weekly_views_caption_color = weekly_growth_caption(
        weekly_views_value,
        previous_week_views_value,
    )
    weekly_likes_caption, weekly_likes_caption_color = weekly_growth_caption(
        weekly_likes_value,
        previous_week_likes_value,
    )
    weekly_comments_caption, weekly_comments_caption_color = weekly_growth_caption(
        weekly_comments_value,
        previous_week_comments_value,
    )

    st.markdown(
        '<div class="creator-kpi-section-title">Bloco total do criador</div>',
        unsafe_allow_html=True,
    )
    metric_card_grid(
        [
            metric_card_html("Seguidores", format_compact_number(selected_row["followers"]), "", "SG"),
            metric_card_html("Engajamento", engagement_rank_display, "", "RK"),
            metric_card_html("Videos", format_compact_number(total_videos_filtered), "", "VD"),
            metric_card_html("Views", format_compact_number(total_views_filtered), "", "VW"),
            metric_card_html("Likes", format_compact_number(total_likes_filtered), "", "LK"),
            metric_card_html("Comentarios", format_compact_number(total_comments_filtered), "", "CM"),
        ],
        class_name="creator-kpi-grid",
    )

    engagement_distribution_df = engagement_weighted_components(
        total_views_filtered,
        total_likes_filtered,
        total_comments_filtered,
    )
    donut_fig = px.pie(
        engagement_distribution_df,
        names="metrica",
        values="valor",
        hole=0.62,
        color="metrica",
        color_discrete_map={"Views x1": "#ff8069", "Likes x10": "#ff9b87", "Comentarios x20": "#ffc0b4"},
    )
    donut_fig.update_traces(
        textinfo="percent",
        textposition="inside",
        insidetextorientation="radial",
        hovertemplate="%{label}: %{percent}<extra></extra>",
    )
    donut_fig.update_layout(uniformtext_minsize=10, uniformtext_mode="hide")
    apply_plotly_theme(donut_fig, legend_title="Metrica")

    weekly_fig = px.bar(
        weekly_df,
        x="week_label",
        y="views_novas",
        color_discrete_sequence=["#ff8069"],
    )
    weekly_fig.add_scatter(
        x=weekly_df["week_label"],
        y=weekly_df["likes_novos"],
        mode="lines+markers",
        name="Likes",
        line=dict(color="#ff9b87", width=2),
        yaxis="y2",
    )
    weekly_fig.add_scatter(
        x=weekly_df["week_label"],
        y=weekly_df["comentarios_novos"],
        mode="lines+markers",
        name="Comentarios",
        line=dict(color="#ffc0b4", width=2),
        yaxis="y2",
    )
    weekly_fig.update_layout(
        yaxis_title="Views",
        yaxis2=dict(title="Interacoes", overlaying="y", side="right", showgrid=False),
    )
    apply_plotly_theme(weekly_fig, legend_title="Serie")
    weekly_fig.update_layout(
        xaxis_title=None,
        legend=dict(x=1.08, y=0.88, xanchor="left", yanchor="top"),
        margin=dict(l=16, r=112, t=28, b=16),
    )

    engagement_display = engagement_rank_display
    selected_sub_niche = str(selected_row.get("sub_niche_display") or selected_row.get("niche") or "Sem classificacao fina")
    selected_creator_type = str(selected_row.get("creator_type") or "--")
    selected_latest_collected_at = format_timestamp_br(selected_row.get("latest_collected_at"))
    selected_latest_post_date = format_timestamp_br(selected_row.get("latest_post_date"))
    selected_status = "ativo" if bool(selected_row.get("is_active")) else "inativo"

    selected_week_label = str(selected_week_row.get("week_label") or "Sem base semanal")
    selected_video_type_label = selected_video_type.title() if selected_video_type != "todos" else "Todos"
    weekly_engagement_caption, weekly_engagement_caption_color = "Sem serie semanal", "#aeb4bf"
    st.markdown(
        f'<div class="creator-kpi-section-title">Semana selecionada: {escape(selected_week_label)} | {escape(selected_video_type_label)}</div>',
        unsafe_allow_html=True,
    )
    st.caption("Videos por data de publicacao; views, likes e comentarios por movimento observado em snapshots da semana; seguidores por fechamento semanal contra a semana anterior.")
    metric_card_grid(
        [
            metric_card_html("Seguidores", weekly_followers_display, weekly_followers_caption, "SG", caption_color=weekly_followers_caption_color),
            metric_card_html("Engajamento", "--", weekly_engagement_caption, "RK", caption_color=weekly_engagement_caption_color),
            metric_card_html("Videos", format_compact_number(weekly_videos_value), weekly_videos_caption, "VD", caption_color=weekly_videos_caption_color),
            metric_card_html("Views", format_compact_number(weekly_views_value), weekly_views_caption, "VW", caption_color=weekly_views_caption_color),
            metric_card_html("Likes", format_compact_number(weekly_likes_value), weekly_likes_caption, "LK", caption_color=weekly_likes_caption_color),
            metric_card_html("Comentarios", format_compact_number(weekly_comments_value), weekly_comments_caption, "CM", caption_color=weekly_comments_caption_color),
        ],
        class_name="creator-kpi-grid weekly-grid",
    )

    if summary_error or weekly_error or weekly_audience_error or top_videos_error:
        active_errors = [error for error in [summary_error, weekly_error, weekly_audience_error, top_videos_error] if error]
        st.warning(" | ".join(active_errors))

    show_interactive_creator_charts = st.checkbox(
        "Mostrar graficos interativos do criador",
        value=True,
        help="Religado em teste controlado. Se houver instabilidade no Streamlit Cloud, desligue para manter o fallback HTML.",
    )
    if show_interactive_creator_charts:
        trace_startup("render_creator_detail charts start")
        chart_left, chart_right = st.columns(2)
        with chart_left:
            st.markdown(f"#### Distribuicao de engajamento | {selected_video_type_label}")
            st.caption("Participacao normalizada pelo score: views x1, likes x10 e comentarios x20, respeitando o tipo de video escolhido.")
            trace_startup("render_creator_detail donut_chart before")
            st.plotly_chart(donut_fig, width="stretch", config={"displayModeBar": False})
            trace_startup("render_creator_detail donut_chart after")
        with chart_right:
            st.markdown(f"#### Crescimento semanal | {selected_video_type_label}")
            st.caption("Views em barras; likes e comentarios em linhas com base em snapshots semanais. Semanas sem base suficiente nao entram no grafico.")
            trace_startup("render_creator_detail weekly_chart before")
            st.plotly_chart(weekly_fig, width="stretch", config={"displayModeBar": False})
            trace_startup("render_creator_detail weekly_chart after")
        trace_startup("render_creator_detail charts end")
    else:
        st.info("Graficos interativos desativados nesta sessao. O restante da pagina segue em fallback HTML estavel.")

    video_scope_weekly = st.checkbox("Mostrar videos da semana selecionada", value=False)
    videos_source_df = filtered_posts_df.copy() if video_scope_weekly else top_videos_df.copy()
    if video_scope_weekly and "post_date" in videos_source_df.columns:
        videos_source_df["post_date"] = pd.to_datetime(videos_source_df["post_date"], errors="coerce")
        week_start = pd.to_datetime(selected_week_row.get("week_start"), errors="coerce")
        week_end = pd.to_datetime(selected_week_row.get("week_end"), errors="coerce")
        if pd.notna(week_start) and pd.notna(week_end):
            videos_source_df = videos_source_df[
                (videos_source_df["post_date"] >= week_start)
                & (videos_source_df["post_date"] < (week_end + pd.to_timedelta(1, unit="D")))
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
    if top_videos_display.empty:
        st.info("Sem videos para o filtro selecionado.")
    else:
        video_cards_html = ['<div class="creator-gap-list">']
        for _, video_row in top_videos_display.head(10).iterrows():
            title = str(video_row.get("Titulo") or "Video sem titulo")
            views = str(video_row.get("Views") or "--")
            likes = str(video_row.get("Likes") or "--")
            comments = str(video_row.get("Comentarios") or "--")
            video_type = str(video_row.get("Tipo") or "--")
            video_cards_html.append(
                (
                    '<div class="creator-gap-item">'
                    f'<strong>{escape(title)}</strong>'
                    f'<span>Views: {escape(views)} | Likes: {escape(likes)} | Comentarios: {escape(comments)} | Tipo: {escape(video_type)}</span>'
                    "</div>"
                )
            )
        video_cards_html.append("</div>")
        st.markdown("".join(video_cards_html), unsafe_allow_html=True)
        show_creator_video_dataframe = st.checkbox(
            "Mostrar tabela interativa de videos",
            value=True,
            help="Reintroducao controlada do st.dataframe para isolar o incidente de Segmentation fault no Streamlit Cloud.",
        )
        if show_creator_video_dataframe:
            trace_startup("render_creator_detail video_dataframe before")
            st.dataframe(top_videos_display, width="stretch", hide_index=True)
            trace_startup("render_creator_detail video_dataframe after")

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
            f'{dq_chip("Curva followers", weekly_followers_caption.replace(" vs semana anterior", ""), "ok-green" if weekly_followers_status == "cresceu" else "alert-red" if weekly_followers_status == "caiu" else "alert-yellow" if weekly_followers_status == "estavel" else "neutral")}'
            f'{dq_chip("URL do post", "pendente", "alert-yellow")}'
            "</div>"
            '<div class="creator-gap-list">'
            '<div class="creator-gap-item"><strong>Campo faltante: subnichos reais</strong><span>A view atual ainda nao sobe a associacao real de entity_sub_niches. O mockup mostra a necessidade, mas nao finge que o dado ja existe.</span></div>'
            '<div class="creator-gap-item"><strong>Serie de audiencia semanal</strong><span>A leitura executiva de seguidores agora usa o fechamento da semana contra a semana anterior, com base em creator_metrics_history e na nova view semanal de audiencia.</span></div>'
            '<div class="creator-gap-item"><strong>Campo faltante: URL e resumo editorial</strong><span>Conseguimos montar a tabela de top videos com titulo, data, views, likes e comentarios. Ainda faltam URL publica e agregados editoriais mais ricos.</span></div>'
            "</div>"
            "</div>"
        ),
        unsafe_allow_html=True,
    )

    with st.expander("Campos usados no mockup", expanded=False):
        creator_mockup_fields_df = pd.DataFrame(
            [
                {"campo": "entity_name", "origem": "v_dashboard_creator_summary", "uso": "titulo e ranking"},
                {"campo": "niche", "origem": "v_dashboard_creator_summary", "uso": "filtro"},
                {"campo": "creator_type", "origem": "v_dashboard_creator_summary", "uso": "painel lateral"},
                {"campo": "platform", "origem": "v_dashboard_creator_summary", "uso": "filtro e detalhe"},
                {"campo": "username", "origem": "v_dashboard_creator_summary", "uso": "identificacao"},
                {"campo": "channel_id", "origem": "v_dashboard_creator_summary", "uso": "identificacao tecnica"},
                {"campo": "followers", "origem": "v_dashboard_creator_summary", "uso": "kpi e ranking"},
                {"campo": "post_count", "origem": "v_dashboard_creator_summary", "uso": "ranking e fallback"},
                {"campo": "total_views", "origem": "v_dashboard_creator_summary", "uso": "ranking e fallback"},
                {"campo": "total_likes", "origem": "v_dashboard_creator_summary", "uso": "ranking e fallback"},
                {"campo": "total_comments", "origem": "v_dashboard_creator_summary", "uso": "ranking e fallback"},
                {"campo": "engagement_rate_pct", "origem": "v_dashboard_creator_summary", "uso": "ranking e fallback"},
                {"campo": "latest_post_date", "origem": "v_dashboard_creator_summary", "uso": "detalhe"},
                {"campo": "latest_collected_at", "origem": "v_dashboard_creator_summary", "uso": "detalhe operacional"},
                {"campo": "is_active", "origem": "v_dashboard_creator_summary", "uso": "status"},
                {"campo": "followers_delta_vs_prev_week", "origem": "v_dashboard_creator_weekly_audience", "uso": "card semanal de seguidores"},
                {"campo": "followers_weekly_status", "origem": "v_dashboard_creator_weekly_audience", "uso": "status executivo da audiencia"},
                {"campo": "week_label", "origem": "v_dashboard_creator_weekly_activity", "uso": "periodo semanal selecionado"},
                {"campo": "video_type", "origem": "v_dashboard_creator_weekly_activity", "uso": "cards e graficos semanais conforme tipo selecionado"},
                {"campo": "views_novas", "origem": "v_dashboard_creator_weekly_activity", "uso": "card e grafico semanal de views"},
                {"campo": "likes_novos", "origem": "v_dashboard_creator_weekly_activity", "uso": "card semanal de likes"},
                {"campo": "comentarios_novos", "origem": "v_dashboard_creator_weekly_activity", "uso": "card semanal de comentarios"},
                {"campo": "title", "origem": "public.posts", "uso": "tabela de top videos"},
                {"campo": "views", "origem": "public.posts", "uso": "cards totais filtrados e tabela de top videos"},
                {"campo": "likes", "origem": "public.posts", "uso": "cards totais filtrados e distribuicao"},
                {"campo": "comments", "origem": "public.posts", "uso": "cards filtrados, distribuicao e tabela"},
            ]
        )
        trace_startup("render_creator_detail mockup_fields_dataframe before")
        st.dataframe(creator_mockup_fields_df, width="stretch", hide_index=True)
        trace_startup("render_creator_detail mockup_fields_dataframe after")


def render_creator_overview_page() -> None:
    trace_startup("render_creator_overview start")
    rows, connection_error = get_view_rows("v_dashboard_creator_summary")
    page_header("Visao geral de criadores")

    if not rows:
        placeholder_card(
            "Visao geral de criadores",
            connection_error or "Aguardando a view v_dashboard_creator_summary retornar base valida para montar o comparativo da carteira monitorada.",
        )
        return

    def row_int(row: dict[str, Any], field_name: str) -> int:
        return nullable_int(row.get(field_name)) or 0

    def row_float(row: dict[str, Any], field_name: str) -> float:
        try:
            value = row.get(field_name)
            if value in (None, "") or pd.isna(value):
                return 0.0
            return float(value)
        except (TypeError, ValueError):
            return 0.0

    cards_container = st.container()

    st.markdown("#### Ranking comparativo")
    control_col1, control_col2, control_col3 = st.columns([1.0, 1.0, 1.0])
    with control_col1:
        selected_platform = st.selectbox("Plataforma", ["todas", "youtube", "instagram", "tiktok"], index=1, key="creator_overview_platform")
    with control_col2:
        selected_video_type = st.selectbox("Tipo de video", ["todos", "long", "short"], index=0, key="creator_overview_video_type")
    with control_col3:
        sort_label = st.selectbox("Ordenar por", ["Engajamento", "Seguidores", "Views"], index=0, key="creator_overview_sort_select")
    sort_key = {"Engajamento": "engagement", "Seguidores": "followers", "Views": "views"}.get(sort_label, "engagement")

    working_rows = rows if selected_platform == "todas" else [row for row in rows if row["platform"] == selected_platform]
    working_rows = sorted(working_rows, key=lambda row: row_float(row, "engagement_rate_pct"), reverse=True)

    if not working_rows:
        placeholder_card(
            "Sem criadores neste filtro",
            f"Nenhum criador da view v_dashboard_creator_summary corresponde ao filtro de plataforma {selected_platform}.",
        )
        return

    if selected_video_type in {"long", "short"}:
        creator_ids = [row_int(row, "creator_id") for row in working_rows]
        segmented_rollup, segmented_error = get_creator_posts_rollup(creator_ids, selected_video_type)
        if segmented_error:
            render_connection_notice(segmented_error)
            placeholder_card(
                "Segmentacao indisponivel",
                f"Nao foi possivel carregar a segmentacao {selected_video_type} a partir de public.posts neste ambiente.",
            )
            return

        segmented_rows = []
        for row in working_rows:
            creator_id = row_int(row, "creator_id")
            creator_rollup = segmented_rollup.get(creator_id)
            if not creator_rollup or (creator_rollup.get("post_count") or 0) <= 0:
                continue
            updated_row = dict(row)
            updated_row["post_count"] = creator_rollup["post_count"]
            updated_row["total_views"] = creator_rollup["total_views"]
            updated_row["total_likes"] = creator_rollup["total_likes"]
            updated_row["total_comments"] = creator_rollup["total_comments"]
            updated_row["engagement_rate_pct"] = creator_rollup["engagement_rate_pct"]
            segmented_rows.append(updated_row)
        working_rows = segmented_rows

        if not working_rows:
            placeholder_card(
                "Sem criadores neste filtro",
                f"Nenhum criador possui videos {selected_video_type} monitorados dentro da carteira selecionada.",
            )
            return

    total_followers = sum(row_int(row, "followers") for row in working_rows)
    total_posts = sum(row_int(row, "post_count") for row in working_rows)
    total_views = sum(row_int(row, "total_views") for row in working_rows)
    total_likes = sum(row_int(row, "total_likes") for row in working_rows)
    total_comments = sum(row_int(row, "total_comments") for row in working_rows)
    avg_engagement = round(sum(row_float(row, "engagement_rate_pct") for row in working_rows) / max(len(working_rows), 1), 2)

    with cards_container:
        metric_card_grid(
            [
                metric_card_html("Criadores ativos", format_int(len(working_rows)), "", "CR"),
                metric_card_html("Seguidores monitorados", format_int(total_followers), "", "SG"),
                metric_card_html("Total de videos", format_int(total_posts), "", "VD"),
                metric_card_html("Total de views", format_int(total_views), "", "VW"),
                metric_card_html("Total de likes", format_int(total_likes), "", "LK"),
                metric_card_html("Total de comentarios", format_int(total_comments), "", "CM"),
            ],
            class_name="creator-overview-kpi-grid",
        )

    if sort_key == "followers":
        working_rows = sorted(working_rows, key=lambda row: row_int(row, "followers"), reverse=True)
    elif sort_key == "views":
        working_rows = sorted(working_rows, key=lambda row: row_int(row, "total_views"), reverse=True)
    else:
        working_rows = sorted(working_rows, key=lambda row: row_float(row, "engagement_rate_pct"), reverse=True)

    ranking_items = []
    for row in working_rows:
        engagement_label = f"{row_float(row, 'engagement_rate_pct'):.2f}%"
        entity_name = str(row.get("entity_name") or "Criador sem nome")
        niche_name = str(row.get("niche") or "Nicho nao informado")
        platform_name = str(row.get("platform") or "plataforma")
        username_value = str(row.get("username") or "sem_username").lstrip("@")
        avatar_url = str(row.get("avatar_url") or "").strip()
        avatar_fallback = escape((entity_name[:1] or "C").upper())
        avatar_core_html = (
            f'<div class="creator-ranking-avatar"><img src="{escape(avatar_url)}" alt="{escape(entity_name)}" loading="lazy" /></div>'
            if avatar_url
            else f'<div class="creator-ranking-avatar">{avatar_fallback}</div>'
        )
        creator_channel_url = build_creator_channel_url(row)
        creator_link_attrs = (
            f' href="{escape(creator_channel_url)}" target="_blank" rel="noopener noreferrer" aria-label="Abrir canal de {escape(entity_name)}"'
            if creator_channel_url
            else ""
        )
        avatar_html = (
            f'<a class="creator-ranking-avatar-link"{creator_link_attrs}>{avatar_core_html}</a>'
            if creator_channel_url
            else avatar_core_html
        )
        title_html = (
            f'<a class="creator-ranking-title-link"{creator_link_attrs}>{escape(entity_name)}</a>'
            if creator_channel_url
            else f'<div class="creator-ranking-title">{escape(entity_name)}</div>'
        )
        ranking_items.append(
            (
                '<div class="creator-ranking-item">'
                '<div class="creator-ranking-main">'
                f'{avatar_html}'
                '<div class="creator-ranking-copy">'
                f'{title_html}'
                f'<div class="creator-ranking-meta">{escape(niche_name)} | {escape(platform_name)} | @{escape(username_value)}</div>'
                '</div>'
                '</div>'
                '<div>'
                '<div class="creator-stat-label">Videos monitorados</div>'
                f'<div class="creator-stat-value">{escape(format_int(row_int(row, "post_count")))}</div>'
                '</div>'
                '<div>'
                '<div class="creator-stat-label">Seguidores</div>'
                f'<div class="creator-stat-value">{escape(format_int(row_int(row, "followers")))}</div>'
                '</div>'
                '<div>'
                '<div class="creator-stat-label">Views totais</div>'
                f'<div class="creator-stat-value">{escape(format_int(row_int(row, "total_views")))}</div>'
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


def render_fenabrave_intake_page() -> None:
    state = get_fenabrave_mock_state()
    page_header("Cadastro Fenabrave", "Apoio operacional da rotina mensal de inclusao de dados")
    process_banner(
        "Regra obrigatoria de governanca",
        "A rotina mensal continua manual no ponto certo: confirmar a publicacao, preservar o PDF no bucket privado, registrar metadados, revisar preview, validar e so depois liberar consumo.",
    )

    connection_error = None if is_supabase_configured() else "Supabase ainda nao configurado. Adicione SUPABASE_URL e SUPABASE_ANON_KEY nos secrets."
    recent_records, recent_records_error = list_fenabrave_source_files(limit=12) if connection_error is None else ([], None)
    data_error = connection_error or recent_records_error
    latest_record = recent_records[0] if recent_records else None
    if latest_record is not None:
        st.session_state["fenabrave_source_confirmed"] = True
        if latest_record.get("storage_path"):
            st.session_state["fenabrave_pdf_uploaded"] = True
        st.session_state["fenabrave_metadata_registered"] = True
        if str(latest_record.get("extraction_status")) in {"extracted", "normalized", "validated"}:
            st.session_state["fenabrave_preview_ready"] = True
        if str(latest_record.get("extraction_status")) == "validated":
            st.session_state["fenabrave_validated"] = True
        state = get_fenabrave_mock_state()

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
        ["Rotina mensal", "Validador de status", "Regras da governanca"]
    )

    with tab_monthly:
        left, right = st.columns([1.35, 1])

        with left:
            st.markdown("### 1. Confirmar publicacao do mes anterior")
            default_reference_period = get_default_fenabrave_reference_period()
            reference_period = st.date_input(
                "Periodo de referencia",
                value=default_reference_period,
                format="DD/MM/YYYY",
            )
            reference_period = normalize_fenabrave_reference_period(reference_period)
            current_record = get_fenabrave_record_for_period(recent_records, reference_period)
            fallback_pdf_name = pd.Timestamp(reference_period).strftime("%Y_%m_02.pdf")
            default_source_url = str(current_record.get("source_url")) if current_record else f"https://www.fenabrave.org.br/portal/files/{fallback_pdf_name}"
            default_source_page_url = str(current_record.get("source_page_url")) if current_record and current_record.get("source_page_url") else "https://www.fenabrave.org.br/portalv2/Conteudo/Emplacamentos%20"
            source_url = st.text_input(
                "URL oficial do PDF",
                value=default_source_url,
            )
            source_page_url = st.text_input(
                "Pagina oficial de origem",
                value=default_source_page_url,
            )
            if st.button("Confirmar fonte mensal", use_container_width=False):
                st.session_state["fenabrave_source_confirmed"] = True
                st.rerun()

            current_record = get_fenabrave_record_for_period(recent_records, reference_period)
            signed_pdf_url = None
            signed_pdf_url_error = None
            if current_record and current_record.get("storage_bucket") and current_record.get("storage_path"):
                signed_pdf_url, signed_pdf_url_error = create_fenabrave_signed_url(
                    str(current_record.get("storage_bucket")),
                    str(current_record.get("storage_path")),
                )

            st.markdown("### 2. Carregar PDF do mes")
            uploaded_pdf = st.file_uploader(
                "PDF Fenabrave",
                type=["pdf"],
                help="O PDF pode ser enviado direto ao bucket privado pela propria tela, mantendo o caminho padrao por ano e mes.",
            )

            st.markdown("### 3. Registrar metadados")
            default_filename = uploaded_pdf.name if uploaded_pdf is not None else fallback_pdf_name
            normalized_filename = normalize_fenabrave_filename(default_filename, reference_period)
            storage_bucket = st.text_input("Storage bucket", value=str(current_record.get("storage_bucket")) if current_record and current_record.get("storage_bucket") else "market-source-files")
            original_filename = st.text_input("Nome original do arquivo", value=normalized_filename)
            storage_path = build_fenabrave_storage_path(reference_period, original_filename)
            expected_storage_prefix = pd.Timestamp(reference_period).strftime("fenabrave/%Y/%m/")
            st.caption(f"Pasta obrigatoria do periodo selecionado: `{expected_storage_prefix}`")
            st.code(storage_path)
            status_options = ["stored", "extracted", "normalized", "validated", "failed"]
            current_status = str(current_record.get("extraction_status")) if current_record and current_record.get("extraction_status") in status_options else "stored"
            extraction_status = st.selectbox(
                "Status de extracao",
                status_options,
                index=status_options.index(current_status),
            )
            extraction_method = st.text_input("Metodo de extracao", value=str(current_record.get("extraction_method")) if current_record and current_record.get("extraction_method") else "pdf_table_extraction")
            if st.button("Carregar PDF no bucket privado", use_container_width=False):
                if uploaded_pdf is None:
                    st.error("Selecione um PDF antes de enviar para o Storage.")
                elif not storage_path.startswith(expected_storage_prefix):
                    st.error(f"O storage_path precisa comecar com {expected_storage_prefix}.")
                else:
                    upload_payload, upload_error = upload_fenabrave_pdf_to_storage(
                        storage_bucket,
                        storage_path,
                        uploaded_pdf.getvalue(),
                    )
                    if upload_error:
                        st.error(upload_error)
                    else:
                        st.session_state["fenabrave_pdf_uploaded"] = True
                        st.success(
                            "PDF enviado ao bucket privado em "
                            f"`{storage_bucket}/{storage_path}`."
                        )
                        st.json(upload_payload)
            if st.button("Preparar metadados do arquivo", use_container_width=False):
                metadata_payload = {
                    "p_reference_period": pd.Timestamp(reference_period).strftime("%Y-%m-%d"),
                    "p_source_url": source_url,
                    "p_source_page_url": source_page_url,
                    "p_storage_bucket": storage_bucket,
                    "p_storage_path": storage_path,
                    "p_original_filename": original_filename,
                    "p_file_size_bytes": uploaded_pdf.size if uploaded_pdf is not None else None,
                    "p_sha256": hashlib.sha256(uploaded_pdf.getvalue()).hexdigest() if uploaded_pdf is not None else None,
                    "p_extraction_status": extraction_status,
                    "p_extraction_method": extraction_method,
                    "p_extraction_notes": "Metadados preparados via Cadastro Fenabrave no Streamlit.",
                }
                saved_row, save_error = upsert_fenabrave_source_file(metadata_payload)
                if save_error:
                    st.error(save_error)
                else:
                    st.session_state["fenabrave_metadata_registered"] = True
                    st.session_state["fenabrave_source_confirmed"] = True
                    st.success(
                        "Metadados reais registrados em market_source_files para o periodo "
                        f"{pd.Timestamp(reference_period).strftime('%m/%Y')}."
                    )
                    st.json(saved_row)
                    st.rerun()

            preview_source_file_id = nullable_int(current_record.get("source_file_id")) if current_record else -1
            preview_record = {
                "source_file_id": preview_source_file_id if preview_source_file_id is not None else -1,
                "reference_period": reference_period,
                "source_url": source_url,
                "source_page_url": source_page_url,
                "storage_bucket": storage_bucket,
                "storage_path": storage_path,
                "original_filename": original_filename,
                "extraction_method": extraction_method,
            }

            st.markdown("### 4. Preview operacional")
            if preview_record is not None:
                compare_col, action_col = st.columns([1.15, 1])
                with compare_col:
                    preview_signed_pdf_url = None
                    preview_signed_pdf_url_error = None
                    if storage_bucket and storage_path:
                        preview_signed_pdf_url, preview_signed_pdf_url_error = create_fenabrave_signed_url(
                            storage_bucket,
                            storage_path,
                        )
                    if preview_signed_pdf_url:
                        st.link_button("Abrir PDF real para comparativo", preview_signed_pdf_url, use_container_width=False)
                        st.caption("Link temporario do arquivo real salvo no bucket privado.")
                    elif preview_signed_pdf_url_error:
                        st.warning(preview_signed_pdf_url_error)
                with action_col:
                    if current_record:
                        current_status_label = str(current_record.get("extraction_status") or "stored")
                        st.caption(f"Status real atual do periodo: `{current_status_label}`")

            preview_payload, preview_error = get_fenabrave_preview_from_storage(preview_record)

            if preview_payload and preview_payload.get("normalized_rows"):
                normalized_df = pd.DataFrame(preview_payload["normalized_rows"])
                normalized_df = normalized_df.rename(
                    columns={
                        "segmento": "segment_label",
                        "mes_atual": "monthly_units",
                    }
                )
                preview_columns = [
                    column
                    for column in ["segment_code", "segment_label", "monthly_units"]
                    if column in normalized_df.columns
                ]
                trace_startup("render_fenabrave_preview normalized_dataframe before")
                st.dataframe(normalized_df[preview_columns], width="stretch", hide_index=True)
                trace_startup("render_fenabrave_preview normalized_dataframe after")

                if preview_payload.get("checks"):
                    checks_df = pd.DataFrame(preview_payload["checks"]).rename(
                        columns={
                            "check_name": "check",
                            "calculated_value": "calculated",
                            "expected_value": "expected",
                            "difference": "difference",
                            "passed": "passed",
                            "severity": "severity",
                            "notes": "notes",
                        }
                    )
                    st.markdown("#### Checks estruturais")
                    trace_startup("render_fenabrave_preview checks_dataframe before")
                    st.dataframe(checks_df, width="stretch", hide_index=True)
                    trace_startup("render_fenabrave_preview checks_dataframe after")

                    item1_rows = preview_payload.get("item1_rows") or []
                    item1_checks = preview_payload.get("item1_checks") or []
                    item2_rows = preview_payload.get("item2_rows") or []
                    item2_checks = preview_payload.get("item2_checks") or []
                    item3_rows = preview_payload.get("item3_rows") or []
                    item3_checks = preview_payload.get("item3_checks") or []
                    item4_rows = preview_payload.get("item4_rows") or []
                    item4_checks = preview_payload.get("item4_checks") or []
                    item5_rows = preview_payload.get("item5_rows") or []
                    item5_checks = preview_payload.get("item5_checks") or []
                    item6_rows = preview_payload.get("item6_rows") or []
                    item6_checks = preview_payload.get("item6_checks") or []
                    item7_rows = preview_payload.get("item7_rows") or []
                    item7_checks = preview_payload.get("item7_checks") or []
                    item8_rows = preview_payload.get("item8_rows") or []
                    item8_checks = preview_payload.get("item8_checks") or []
                    item11_rows = preview_payload.get("item11_rows") or []
                    item11_checks = preview_payload.get("item11_checks") or []
                    item12_rows = preview_payload.get("item12_rows") or []
                    item12_checks = preview_payload.get("item12_checks") or []
                    item13_rows = preview_payload.get("item13_rows") or []
                    item13_checks = preview_payload.get("item13_checks") or []
                    item14_rows = preview_payload.get("item14_rows") or []
                    item14_checks = preview_payload.get("item14_checks") or []
                    item15_rows = preview_payload.get("item15_rows") or []
                    item15_checks = preview_payload.get("item15_checks") or []
                    item16_rows = preview_payload.get("item16_rows") or []
                    item16_checks = preview_payload.get("item16_checks") or []
                    item17_rows = preview_payload.get("item17_rows") or []
                    item17_checks = preview_payload.get("item17_checks") or []
                    item18_rows = preview_payload.get("item18_rows") or []
                    item18_checks = preview_payload.get("item18_checks") or []
                    item19_rows = preview_payload.get("item19_rows") or []
                    item19_checks = preview_payload.get("item19_checks") or []
                    item20_rows = preview_payload.get("item20_rows") or []
                    item20_checks = preview_payload.get("item20_checks") or []
                    item21_rows = preview_payload.get("item21_rows") or []
                    item21_checks = preview_payload.get("item21_checks") or []
                    item22_rows = preview_payload.get("item22_rows") or []
                    item22_checks = preview_payload.get("item22_checks") or []
                    trace_startup("render_fenabrave_preview items_1_8 start")
                    if item1_rows:
                        st.markdown("#### Item 1 fase 2 - Ranking dos emplacamentos mes")
                        item1_df = pd.DataFrame(item1_rows)
                        item1_preview_columns = [
                            column
                            for column in ["vehicle_category", "rank_position", "model_label_raw", "monthly_units"]
                            if column in item1_df.columns
                        ]
                        st.dataframe(
                            item1_df[item1_preview_columns].head(20),
                            width="stretch",
                            hide_index=True,
                        )
                    if item1_checks:
                        st.markdown("#### Checks item 1 fase 2")
                        st.dataframe(
                            pd.DataFrame(item1_checks),
                            width="stretch",
                            hide_index=True,
                        )
                    if item2_rows:
                        st.markdown("#### Item 2 fase 2 - Ranking dos emplacamentos acumulado")
                        item2_df = pd.DataFrame(item2_rows)
                        item2_preview_columns = [
                            column
                            for column in ["vehicle_category", "rank_position", "model_label_raw", "monthly_units"]
                            if column in item2_df.columns
                        ]
                        st.dataframe(
                            item2_df[item2_preview_columns].head(20),
                            width="stretch",
                            hide_index=True,
                        )
                    if item2_checks:
                        st.markdown("#### Checks item 2 fase 2")
                        st.dataframe(
                            pd.DataFrame(item2_checks),
                            width="stretch",
                            hide_index=True,
                        )
                    if item3_rows:
                        st.markdown("#### Item 3 fase 2 - Ranking por marca mes")
                        item3_df = pd.DataFrame(item3_rows)
                        item3_preview_columns = [
                            column
                            for column in ["vehicle_category", "rank_position", "brand_name_raw", "units", "market_share_pct"]
                            if column in item3_df.columns
                        ]
                        st.dataframe(
                            item3_df[item3_preview_columns].head(25),
                            width="stretch",
                            hide_index=True,
                        )
                    if item3_checks:
                        st.markdown("#### Checks item 3 fase 2")
                        st.dataframe(
                            pd.DataFrame(item3_checks),
                            width="stretch",
                            hide_index=True,
                        )
                    if item4_rows:
                        st.markdown("#### Item 4 fase 2 - Ranking por marca acumulado")
                        item4_df = pd.DataFrame(item4_rows)
                        item4_preview_columns = [
                            column
                            for column in ["vehicle_category", "rank_position", "brand_name_raw", "units", "market_share_pct"]
                            if column in item4_df.columns
                        ]
                        st.dataframe(
                            item4_df[item4_preview_columns].head(25),
                            width="stretch",
                            hide_index=True,
                        )
                    if item4_checks:
                        st.markdown("#### Checks item 4 fase 2")
                        st.dataframe(
                            pd.DataFrame(item4_checks),
                            width="stretch",
                            hide_index=True,
                        )
                    if item5_rows:
                        st.markdown("#### Item 5 fase 2 - Emplacamentos por sub segmento")
                        item5_df = pd.DataFrame(item5_rows)
                        item5_preview_columns = [
                            column
                            for column in [
                                "subsegment_name",
                                "current_month_share_pct",
                                "current_year_accum_share_pct",
                                "prior_year_accum_share_pct",
                            ]
                            if column in item5_df.columns
                        ]
                        st.dataframe(
                            item5_df[item5_preview_columns],
                            width="stretch",
                            hide_index=True,
                        )
                    if item5_checks:
                        st.markdown("#### Checks item 5 fase 2")
                        st.dataframe(
                            pd.DataFrame(item5_checks),
                            width="stretch",
                            hide_index=True,
                        )
                    if item6_rows:
                        st.markdown("#### Item 6 fase 2 - Mercado de eletrificados mes")
                        st.caption("Preview operacional das paginas 20 e 21. Nesta etapa a UI mostra parser e checks; a persistencia dos itens 6, 7 e 8 ainda nao entra na gravacao automatica deste botao.")
                        item6_df = pd.DataFrame(item6_rows)
                        item6_preview_columns = [
                            column
                            for column in ["vehicle_category", "powertrain_type", "units"]
                            if column in item6_df.columns
                        ]
                        st.dataframe(
                            item6_df[item6_preview_columns],
                            width="stretch",
                            hide_index=True,
                        )
                    if item6_checks:
                        st.markdown("#### Checks item 6 fase 2")
                        st.dataframe(
                            pd.DataFrame(item6_checks),
                            width="stretch",
                            hide_index=True,
                        )
                    if item7_rows:
                        st.markdown("#### Item 7 fase 2 - Total por marca hibrido mes")
                        item7_df = pd.DataFrame(item7_rows)
                        item7_preview_columns = [
                            column
                            for column in ["vehicle_category", "rank_position", "brand_name_raw", "units", "market_share_pct"]
                            if column in item7_df.columns
                        ]
                        st.dataframe(
                            item7_df[item7_preview_columns].head(30),
                            width="stretch",
                            hide_index=True,
                        )
                    if item7_checks:
                        st.markdown("#### Checks item 7 fase 2")
                        st.dataframe(
                            pd.DataFrame(item7_checks),
                            width="stretch",
                            hide_index=True,
                        )
                    if item8_rows:
                        st.markdown("#### Item 8 fase 2 - Total por marca eletrico mes")
                        item8_df = pd.DataFrame(item8_rows)
                        item8_preview_columns = [
                            column
                            for column in ["vehicle_category", "rank_position", "brand_name_raw", "units", "market_share_pct"]
                            if column in item8_df.columns
                        ]
                        st.dataframe(
                            item8_df[item8_preview_columns].head(30),
                            width="stretch",
                            hide_index=True,
                        )
                    if item8_checks:
                        st.markdown("#### Checks item 8 fase 2")
                        st.dataframe(
                            pd.DataFrame(item8_checks),
                            width="stretch",
                            hide_index=True,
                        )
                    trace_startup("render_fenabrave_preview items_1_8 end")
                    trace_startup("render_fenabrave_preview items_11_22 start")
                    if item11_rows:
                        st.markdown("#### Item 11 fase 2 - Participacao venda direta e varejo mes")
                        item11_df = pd.DataFrame(item11_rows)
                        item11_preview_columns = [
                            column
                            for column in ["vehicle_category", "sales_channel", "share_pct"]
                            if column in item11_df.columns
                        ]
                        st.dataframe(
                            item11_df[item11_preview_columns],
                            width="stretch",
                            hide_index=True,
                        )
                    if item11_checks:
                        st.markdown("#### Checks item 11 fase 2")
                        st.dataframe(
                            pd.DataFrame(item11_checks),
                            width="stretch",
                            hide_index=True,
                        )
                    if item12_rows:
                        st.markdown("#### Item 12 fase 2 - Participacao venda direta e varejo acumulado")
                        item12_df = pd.DataFrame(item12_rows)
                        item12_preview_columns = [
                            column
                            for column in ["vehicle_category", "sales_channel", "share_pct"]
                            if column in item12_df.columns
                        ]
                        st.dataframe(
                            item12_df[item12_preview_columns],
                            width="stretch",
                            hide_index=True,
                        )
                    if item12_checks:
                        st.markdown("#### Checks item 12 fase 2")
                        st.dataframe(
                            pd.DataFrame(item12_checks),
                            width="stretch",
                            hide_index=True,
                        )
                    if item13_rows:
                        st.markdown("#### Item 13 fase 2 - Ranking por marca de emplacamento varejo mes")
                        st.caption("Parser posicional com persistencia pronta para ranking por share sem unidades.")
                        item13_df = pd.DataFrame(item13_rows)
                        item13_preview_columns = [
                            column
                            for column in [
                                "vehicle_category",
                                "rank_position",
                                "brand_name_raw",
                                "market_share_pct",
                                "reversed_text_fixed",
                                "brand_x_center",
                                "share_x_center",
                            ]
                            if column in item13_df.columns
                        ]
                        st.dataframe(
                            item13_df[item13_preview_columns].head(40),
                            width="stretch",
                            hide_index=True,
                        )
                    if item13_checks:
                        st.markdown("#### Checks item 13 fase 2")
                        item13_checks_df = pd.DataFrame(item13_checks)
                        st.dataframe(
                            item13_checks_df,
                            width="stretch",
                            hide_index=True,
                        )
                        item13_errors = item13_checks_df[
                            (~item13_checks_df["passed"]) & (item13_checks_df["severity"] == "error")
                        ]
                        if not item13_errors.empty:
                            first_error = item13_errors.iloc[0]
                            st.error(
                                "Falha na extracao do item Fenabrave. O parser identificou inconsistencias de layout, alinhamento ou texto invertido e a persistencia foi bloqueada para este item. "
                                f"item_code=fenabrave_item_13 pagina=26 erro={first_error['check_name']}"
                            )
                    if item14_rows:
                        st.markdown("#### Item 14 fase 2 - Ranking por marca de emplacamento varejo acumulado")
                        st.caption("Parser posicional com persistencia pronta para ranking por share sem unidades.")
                        item14_df = pd.DataFrame(item14_rows)
                        item14_preview_columns = [
                            column
                            for column in [
                                "vehicle_category",
                                "rank_position",
                                "brand_name_raw",
                                "market_share_pct",
                                "reversed_text_fixed",
                                "brand_x_center",
                                "share_x_center",
                            ]
                            if column in item14_df.columns
                        ]
                        st.dataframe(
                            item14_df[item14_preview_columns].head(40),
                            width="stretch",
                            hide_index=True,
                        )
                    if item14_checks:
                        st.markdown("#### Checks item 14 fase 2")
                        item14_checks_df = pd.DataFrame(item14_checks)
                        st.dataframe(
                            item14_checks_df,
                            width="stretch",
                            hide_index=True,
                        )
                        item14_errors = item14_checks_df[
                            (~item14_checks_df["passed"]) & (item14_checks_df["severity"] == "error")
                        ]
                        if not item14_errors.empty:
                            first_error = item14_errors.iloc[0]
                            st.error(
                                "Falha na extracao do item Fenabrave. O parser identificou inconsistencias de layout, alinhamento ou texto invertido e a persistencia foi bloqueada para este item. "
                                f"item_code=fenabrave_item_14 pagina=27 erro={first_error['check_name']}"
                            )
                    if item15_rows:
                        st.markdown("#### Item 15 fase 2 - Ranking por marca de emplacamento direta mes")
                        st.caption("Parser posicional com persistencia pronta para ranking por share sem unidades.")
                        item15_df = pd.DataFrame(item15_rows)
                        item15_preview_columns = [
                            column
                            for column in [
                                "vehicle_category",
                                "rank_position",
                                "brand_name_raw",
                                "market_share_pct",
                                "reversed_text_fixed",
                                "brand_x_center",
                                "share_x_center",
                            ]
                            if column in item15_df.columns
                        ]
                        st.dataframe(
                            item15_df[item15_preview_columns].head(40),
                            width="stretch",
                            hide_index=True,
                        )
                    if item15_checks:
                        st.markdown("#### Checks item 15 fase 2")
                        item15_checks_df = pd.DataFrame(item15_checks)
                        st.dataframe(
                            item15_checks_df,
                            width="stretch",
                            hide_index=True,
                        )
                        item15_errors = item15_checks_df[
                            (~item15_checks_df["passed"]) & (item15_checks_df["severity"] == "error")
                        ]
                        if not item15_errors.empty:
                            first_error = item15_errors.iloc[0]
                            st.error(
                                "Falha na extracao do item Fenabrave. O parser identificou inconsistencias de layout, alinhamento ou texto invertido e a persistencia foi bloqueada para este item. "
                                f"item_code=fenabrave_item_15 pagina=28 erro={first_error['check_name']}"
                            )
                    if item16_rows:
                        st.markdown("#### Item 16 fase 2 - Ranking por marca de emplacamento direta acumulado")
                        st.caption("Parser posicional com persistencia pronta para ranking por share sem unidades.")
                        item16_df = pd.DataFrame(item16_rows)
                        item16_preview_columns = [
                            column
                            for column in [
                                "vehicle_category",
                                "rank_position",
                                "brand_name_raw",
                                "market_share_pct",
                                "reversed_text_fixed",
                                "brand_x_center",
                                "share_x_center",
                            ]
                            if column in item16_df.columns
                        ]
                        st.dataframe(
                            item16_df[item16_preview_columns].head(40),
                            width="stretch",
                            hide_index=True,
                        )
                    if item16_checks:
                        st.markdown("#### Checks item 16 fase 2")
                        item16_checks_df = pd.DataFrame(item16_checks)
                        st.dataframe(
                            item16_checks_df,
                            width="stretch",
                            hide_index=True,
                        )
                        item16_errors = item16_checks_df[
                            (~item16_checks_df["passed"]) & (item16_checks_df["severity"] == "error")
                        ]
                        if not item16_errors.empty:
                            first_error = item16_errors.iloc[0]
                            st.error(
                                "Falha na extracao do item Fenabrave. O parser identificou inconsistencias de layout, alinhamento ou texto invertido e a persistencia foi bloqueada para este item. "
                                f"item_code=fenabrave_item_16 pagina=29 erro={first_error['check_name']}"
                            )
                    if item17_rows:
                        st.markdown("#### Item 17 fase 2 - Participacao de mercado por marca mes")
                        st.caption("Parser posicional do consolidado total por marca com persistencia pronta em ranking por share.")
                        item17_df = pd.DataFrame(item17_rows)
                        item17_preview_columns = [
                            column
                            for column in [
                                "vehicle_category",
                                "rank_position",
                                "brand_name_raw",
                                "market_share_pct",
                                "reversed_text_fixed",
                                "brand_x_center",
                                "share_x_center",
                            ]
                            if column in item17_df.columns
                        ]
                        st.dataframe(
                            item17_df[item17_preview_columns].head(40),
                            width="stretch",
                            hide_index=True,
                        )
                    if item17_checks:
                        st.markdown("#### Checks item 17 fase 2")
                        item17_checks_df = pd.DataFrame(item17_checks)
                        st.dataframe(
                            item17_checks_df,
                            width="stretch",
                            hide_index=True,
                        )
                        item17_errors = item17_checks_df[
                            (~item17_checks_df["passed"]) & (item17_checks_df["severity"] == "error")
                        ]
                        if not item17_errors.empty:
                            first_error = item17_errors.iloc[0]
                            st.error(
                                "Falha na extracao do item Fenabrave. O parser identificou inconsistencias de layout, alinhamento ou texto invertido e a persistencia foi bloqueada para este item. "
                                f"item_code=fenabrave_item_17 pagina=3 erro={first_error['check_name']}"
                            )
                    if item18_rows:
                        st.markdown("#### Item 18 fase 2 - Participacao de mercado por marca acumulado")
                        st.caption("Parser posicional do consolidado total por marca com persistencia pronta em ranking por share.")
                        item18_df = pd.DataFrame(item18_rows)
                        item18_preview_columns = [
                            column
                            for column in [
                                "vehicle_category",
                                "rank_position",
                                "brand_name_raw",
                                "market_share_pct",
                                "reversed_text_fixed",
                                "brand_x_center",
                                "share_x_center",
                            ]
                            if column in item18_df.columns
                        ]
                        st.dataframe(
                            item18_df[item18_preview_columns].head(40),
                            width="stretch",
                            hide_index=True,
                        )
                    if item18_checks:
                        st.markdown("#### Checks item 18 fase 2")
                        item18_checks_df = pd.DataFrame(item18_checks)
                        st.dataframe(
                            item18_checks_df,
                            width="stretch",
                            hide_index=True,
                        )
                        item18_errors = item18_checks_df[
                            (~item18_checks_df["passed"]) & (item18_checks_df["severity"] == "error")
                        ]
                        if not item18_errors.empty:
                            first_error = item18_errors.iloc[0]
                            st.error(
                                "Falha na extracao do item Fenabrave. O parser identificou inconsistencias de layout, alinhamento ou texto invertido e a persistencia foi bloqueada para este item. "
                                f"item_code=fenabrave_item_18 pagina=4 erro={first_error['check_name']}"
                            )
                    if item19_rows:
                        st.markdown("#### Item 19 fase 2 - Modelos mais emplacados venda direta mes")
                        item19_df = pd.DataFrame(item19_rows)
                        item19_preview_columns = [
                            column
                            for column in ["vehicle_category", "rank_position", "model_label_raw", "monthly_units"]
                            if column in item19_df.columns
                        ]
                        st.dataframe(
                            item19_df[item19_preview_columns].head(20),
                            width="stretch",
                            hide_index=True,
                        )
                    if item19_checks:
                        st.markdown("#### Checks item 19 fase 2")
                        st.dataframe(
                            pd.DataFrame(item19_checks),
                            width="stretch",
                            hide_index=True,
                        )
                    if item20_rows:
                        st.markdown("#### Item 20 fase 2 - Modelos mais emplacados venda varejo mes")
                        item20_df = pd.DataFrame(item20_rows)
                        item20_preview_columns = [
                            column
                            for column in ["vehicle_category", "rank_position", "model_label_raw", "monthly_units"]
                            if column in item20_df.columns
                        ]
                        st.dataframe(
                            item20_df[item20_preview_columns].head(20),
                            width="stretch",
                            hide_index=True,
                        )
                    if item20_checks:
                        st.markdown("#### Checks item 20 fase 2")
                        st.dataframe(
                            pd.DataFrame(item20_checks),
                            width="stretch",
                            hide_index=True,
                        )
                    if item21_rows:
                        st.markdown("#### Item 21 fase 2 - Modelos mais emplacados venda direta acumulado")
                        item21_df = pd.DataFrame(item21_rows)
                        item21_preview_columns = [
                            column
                            for column in ["vehicle_category", "rank_position", "model_label_raw", "monthly_units"]
                            if column in item21_df.columns
                        ]
                        st.dataframe(
                            item21_df[item21_preview_columns].head(20),
                            width="stretch",
                            hide_index=True,
                        )
                    if item21_checks:
                        st.markdown("#### Checks item 21 fase 2")
                        st.dataframe(
                            pd.DataFrame(item21_checks),
                            width="stretch",
                            hide_index=True,
                        )
                    if item22_rows:
                        st.markdown("#### Item 22 fase 2 - Modelos mais emplacados venda varejo acumulado")
                        item22_df = pd.DataFrame(item22_rows)
                        item22_preview_columns = [
                            column
                            for column in ["vehicle_category", "rank_position", "model_label_raw", "monthly_units"]
                            if column in item22_df.columns
                        ]
                        st.dataframe(
                            item22_df[item22_preview_columns].head(20),
                            width="stretch",
                            hide_index=True,
                        )
                    if item22_checks:
                        st.markdown("#### Checks item 22 fase 2")
                        st.dataframe(
                            pd.DataFrame(item22_checks),
                            width="stretch",
                            hide_index=True,
                        )
                    trace_startup("render_fenabrave_preview items_11_22 end")
                    if item13_rows or item14_rows or item15_rows or item16_rows or item17_rows or item18_rows:
                        st.info(
                            "Itens 13 a 18 agora usam a mesma modelagem de ranking por marca, com suporte a linhas publicadas apenas com share."
                        )

                if current_record is not None and st.button("Marcar preview real como revisado", use_container_width=False):
                    notes = (
                        "Preview operacional revisado via Cadastro Fenabrave no Streamlit. "
                        f"PDF={preview_payload.get('pdf_sha256')}."
                    )
                    saved_row, save_error = upsert_fenabrave_source_file(
                        build_fenabrave_upsert_payload(current_record, "extracted", notes)
                    )
                    if save_error:
                        st.error(save_error)
                    else:
                        st.session_state["fenabrave_preview_ready"] = True
                        st.success("Status real do periodo atualizado para extracted apos revisao do preview.")
                        st.json(saved_row)
                        st.rerun()
                if current_record is not None and st.button("Gravar dados analiticos no Supabase", use_container_width=False):
                    module = load_fenabrave_ingestion_module()
                    base_url = module.normalize_supabase_url(get_secret("SUPABASE_URL"))
                    supabase_service_role_key = get_secret("SUPABASE_SERVICE_ROLE_KEY")
                    if not base_url or not supabase_service_role_key:
                        st.error("Adicione SUPABASE_URL e SUPABASE_SERVICE_ROLE_KEY nos secrets do Streamlit.")
                    else:
                        try:
                            headers = module.build_headers(supabase_service_role_key)
                            module.write_results(
                                base_url,
                                headers,
                                int(current_record["source_file_id"]),
                                preview_payload["normalized_rows"],
                                preview_payload["checks"],
                                True,
                                item1_rows=preview_payload.get("item1_rows"),
                                item1_checks=preview_payload.get("item1_checks"),
                                item2_rows=preview_payload.get("item2_rows"),
                                item2_checks=preview_payload.get("item2_checks"),
                                item3_rows=preview_payload.get("item3_rows"),
                                item3_checks=preview_payload.get("item3_checks"),
                                item4_rows=preview_payload.get("item4_rows"),
                                item4_checks=preview_payload.get("item4_checks"),
                                item5_rows=preview_payload.get("item5_rows"),
                                item5_checks=preview_payload.get("item5_checks"),
                                item6_rows=preview_payload.get("item6_rows"),
                                item6_checks=preview_payload.get("item6_checks"),
                                item7_rows=preview_payload.get("item7_rows"),
                                item7_checks=preview_payload.get("item7_checks"),
                                item8_rows=preview_payload.get("item8_rows"),
                                item8_checks=preview_payload.get("item8_checks"),
                                item11_rows=preview_payload.get("item11_rows"),
                                item11_checks=preview_payload.get("item11_checks"),
                                item12_rows=preview_payload.get("item12_rows"),
                                item12_checks=preview_payload.get("item12_checks"),
                                item13_rows=preview_payload.get("item13_rows"),
                                item13_checks=preview_payload.get("item13_checks"),
                                item14_rows=preview_payload.get("item14_rows"),
                                item14_checks=preview_payload.get("item14_checks"),
                                item15_rows=preview_payload.get("item15_rows"),
                                item15_checks=preview_payload.get("item15_checks"),
                                item16_rows=preview_payload.get("item16_rows"),
                                item16_checks=preview_payload.get("item16_checks"),
                                item17_rows=preview_payload.get("item17_rows"),
                                item17_checks=preview_payload.get("item17_checks"),
                                item18_rows=preview_payload.get("item18_rows"),
                                item18_checks=preview_payload.get("item18_checks"),
                                item19_rows=preview_payload.get("item19_rows"),
                                item19_checks=preview_payload.get("item19_checks"),
                                item20_rows=preview_payload.get("item20_rows"),
                                item20_checks=preview_payload.get("item20_checks"),
                                item21_rows=preview_payload.get("item21_rows"),
                                item21_checks=preview_payload.get("item21_checks"),
                                item22_rows=preview_payload.get("item22_rows"),
                                item22_checks=preview_payload.get("item22_checks"),
                            )
                        except Exception as exc:
                            st.error(f"Falha ao gravar os dados analiticos: {exc}")
                        else:
                            st.session_state["fenabrave_preview_ready"] = True
                            st.session_state["fenabrave_validated"] = True
                            st.success(
                                "Dados analiticos gravados em market_vehicle_registrations_segment "
                                "e itens 1, 2, 3, 4, 5, 6, 7, 8, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21 e 22 da fase 2 gravados nas tabelas Fenabrave."
                            )
                            st.rerun()
            elif preview_error:
                st.warning(preview_error)
            else:
                    st.info("Ainda nao foi possivel gerar o preview operacional real a partir do PDF salvo.")

            preview_rows = get_fenabrave_preview_rows(reference_period)
            if preview_rows:
                persisted_df = pd.DataFrame(preview_rows)
                persisted_columns = [
                    column
                    for column in ["segment_code", "segment_label", "monthly_units", "current_year_accumulated_units"]
                    if column in persisted_df.columns
                ]
                st.markdown("#### Dados persistidos da view analitica")
                trace_startup("render_fenabrave_persisted_dataframe before")
                st.dataframe(persisted_df[persisted_columns], width="stretch", hide_index=True)
                trace_startup("render_fenabrave_persisted_dataframe after")

        with right:
            st.markdown("### Leitura da rotina")
            uploaded_name = uploaded_pdf.name if uploaded_pdf is not None else None
            uploaded_size = uploaded_pdf.size if uploaded_pdf is not None else None
            pdf_uploaded_real = bool(current_record and current_record.get("storage_path")) or st.session_state["fenabrave_pdf_uploaded"]
            metadata_registered_real = current_record is not None
            preview_ready_real = bool(current_record and str(current_record.get("extraction_status")) in {"extracted", "normalized", "validated"})
            validated_real = bool(current_record and str(current_record.get("extraction_status")) == "validated")
            source_confirmed_real = bool(current_record) or st.session_state["fenabrave_source_confirmed"]
            can_validate = (
                source_confirmed_real
                and pdf_uploaded_real
                and metadata_registered_real
                and (preview_ready_real or st.session_state["fenabrave_preview_ready"])
            )
            warnings = []
            if data_error:
                warnings.append(data_error)
            if not source_confirmed_real:
                warnings.append("A fonte oficial do mes anterior ainda nao foi confirmada.")
            if not pdf_uploaded_real:
                warnings.append("O PDF ainda nao foi enviado ao bucket privado para o periodo selecionado.")
            if not metadata_registered_real:
                warnings.append("Ainda nao existe registro real de market_source_files para o periodo selecionado.")
            if not (preview_ready_real or st.session_state["fenabrave_preview_ready"]):
                warnings.append("O preview operacional ainda precisa de revisao humana ou status real de extracao.")
            if not can_validate:
                warnings.append("A liberacao da view deve ficar bloqueada ate a rotina mensal ficar completa.")

            chips = [
                dq_chip("Fonte", "ok" if source_confirmed_real else "pendente", "ok-green" if source_confirmed_real else "alert-yellow"),
                dq_chip("PDF", "enviado" if pdf_uploaded_real else "ausente", "ok-green" if pdf_uploaded_real else "alert-yellow"),
                dq_chip("Metadados", "reais" if metadata_registered_real else "pendente", "ok-green" if metadata_registered_real else "alert-yellow"),
                dq_chip("Preview", "revisado" if (preview_ready_real or st.session_state["fenabrave_preview_ready"]) else "pendente", "ok-green" if (preview_ready_real or st.session_state["fenabrave_preview_ready"]) else "alert-yellow"),
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
                    "registro_real_encontrado": metadata_registered_real,
                }
            )

            if current_record is not None:
                st.markdown("### Registro real do periodo")
                st.json(current_record)

            st.markdown("### Avaliacao do PDF no Streamlit")
            st.json(
                {
                    "pdf_upload_viavel": True,
                    "nome_arquivo": uploaded_name,
                    "tamanho_bytes": uploaded_size,
                    "pdf_sha256_preview": preview_payload.get("pdf_sha256") if preview_payload else None,
                    "pdf_size_preview_bytes": preview_payload.get("pdf_size_bytes") if preview_payload else None,
                    "storage_path_gerado": storage_path,
                    "pasta_obrigatoria": expected_storage_prefix,
                    "uso_recomendado": "carga historica e carga mensal via Streamlit com persistencia oficial no bucket privado",
                    "restricao": "o upload precisa rodar no servidor do Streamlit com SUPABASE_SERVICE_ROLE_KEY em secrets, sem expor a chave ao navegador",
                }
            )

            if warnings:
                st.warning(" | ".join(warnings))
            else:
                st.success("A rotina operacional do periodo esta completa e pronta para seguir para validacao final.")

    with tab_review:
        st.markdown("### Validador operacional do periodo")
        flow_col1, flow_col2, flow_col3, flow_col4 = st.columns(4)

        with flow_col1:
            if st.button("Marcar stored", use_container_width=True, disabled=current_record is None):
                if current_record is not None:
                    saved_row, save_error = upsert_fenabrave_source_file(
                        build_fenabrave_upsert_payload(
                            current_record,
                            "stored",
                            "Status atualizado via validador operacional no Streamlit.",
                        )
                    )
                    if save_error:
                        st.error(save_error)
                    else:
                        st.success("Periodo atualizado para stored.")
                        st.json(saved_row)
                        st.rerun()
        with flow_col2:
            if st.button("Marcar extracted", use_container_width=True, disabled=current_record is None):
                if current_record is not None:
                    saved_row, save_error = upsert_fenabrave_source_file(
                        build_fenabrave_upsert_payload(
                            current_record,
                            "extracted",
                            "Preview operacional revisado via validador no Streamlit.",
                        )
                    )
                    if save_error:
                        st.error(save_error)
                    else:
                        st.success("Periodo atualizado para extracted.")
                        st.json(saved_row)
                        st.rerun()
        with flow_col3:
            if st.button("Marcar normalized", use_container_width=True, disabled=current_record is None):
                if current_record is not None:
                    saved_row, save_error = upsert_fenabrave_source_file(
                        build_fenabrave_upsert_payload(
                            current_record,
                            "normalized",
                            "Carga analitica sinalizada via validador no Streamlit.",
                        )
                    )
                    if save_error:
                        st.error(save_error)
                    else:
                        st.success("Periodo atualizado para normalized.")
                        st.json(saved_row)
                        st.rerun()
        with flow_col4:
            if st.button("Marcar validated", use_container_width=True, disabled=current_record is None):
                if current_record is not None:
                    saved_row, save_error = upsert_fenabrave_source_file(
                        build_fenabrave_upsert_payload(
                            current_record,
                            "validated",
                            "Periodo aprovado via validador operacional no Streamlit.",
                        )
                    )
                    if save_error:
                        st.error(save_error)
                    else:
                        st.success("Periodo atualizado para validated.")
                        st.json(saved_row)
                        st.rerun()

        if current_record is not None:
            st.markdown("### Registro real do periodo selecionado")
            st.json(current_record)

        if recent_records:
            review_card_grid(
                [
                    {
                        "raw_name": str(row.get("original_filename") or "--"),
                        "sub_niche_name": pd.Timestamp(row.get("reference_period")).strftime("%d/%m/%Y") if row.get("reference_period") else "--",
                        "status": str(row.get("extraction_status") or "--"),
                        "review_result": "OK" if str(row.get("extraction_status")) == "validated" else "AGUARDANDO",
                        "existing_entity_id": str(row.get("source_name") or "Fenabrave"),
                        "existing_entity_name": str(row.get("storage_path") or "--"),
                        "sub_niche_id": str(row.get("extraction_method") or "--"),
                        "matched_sub_niche_name": "Rotina mensal Fenabrave",
                        "notes": str(row.get("extraction_notes") or "Registro operacional real do periodo."),
                    }
                    for row in recent_records[:12]
                ]
            )
        elif data_error:
            st.error(data_error)
        else:
            st.info("Nenhum periodo Fenabrave encontrado em market_source_files.")

        timeline = [
            ("Fonte oficial confirmada", "ok" if st.session_state["fenabrave_source_confirmed"] else "atencao"),
            ("PDF preservado e registrado", "ok" if (recent_records or st.session_state["fenabrave_pdf_uploaded"]) else "atencao"),
            ("Preview operacional revisado", "ok" if any(str(row.get("extraction_status")) in {"extracted", "normalized", "validated"} for row in recent_records) or st.session_state["fenabrave_preview_ready"] else "atencao"),
            ("Periodo validado", "ok" if any(str(row.get("extraction_status")) == "validated" for row in recent_records) or st.session_state["fenabrave_validated"] else "neutral"),
        ]
        st.markdown("### Estado atual do processo")
        st.markdown(
            "".join(dq_chip(label, status.upper(), "ok-green" if status == "ok" else "alert-yellow" if status == "atencao" else "neutral") for label, status in timeline),
            unsafe_allow_html=True,
        )

        if st.button("Reiniciar simulacao Fenabrave", use_container_width=False):
            for key in [
                "fenabrave_source_confirmed",
                "fenabrave_pdf_uploaded",
                "fenabrave_metadata_registered",
                "fenabrave_preview_ready",
                "fenabrave_validated",
            ]:
                st.session_state[key] = False
            st.rerun()

    with tab_rules:
        st.markdown("### O que a UI precisa respeitar")
        st.info(
            "O PDF deve ser carregado pelo Streamlit direto no bucket privado market-source-files, sempre em `fenabrave/AAAA/MM/arquivo.pdf`, com registro correspondente em market_source_files."
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
    if "youtube_subpage" not in st.session_state:
        st.session_state["youtube_subpage"] = "Melhores videos 7d"
    if "youtube_menu_open" not in st.session_state:
        st.session_state["youtube_menu_open"] = False
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
        elif page_value == "YouTube":
            active = st.session_state["nav_page"] == "YouTube" and st.session_state["youtube_subpage"] == selected_value
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
                if page_value != "YouTube":
                    st.session_state["youtube_menu_open"] = False
            else:
                st.session_state["nav_page"] = page_value
                if page_value == "YouTube":
                    st.session_state["youtube_subpage"] = selected_value
                    st.session_state["youtube_menu_open"] = True
                elif page_value == "Creators":
                    st.session_state["creators_subpage"] = selected_value
                    st.session_state["creators_menu_open"] = True
                else:
                    st.session_state["cadastro_subpage"] = selected_value
                    st.session_state["cadastro_menu_open"] = True
            st.rerun()

    sidebar_nav_button("Overview", "Overview")
    sidebar_nav_button("Data quality", "Data quality")
    sidebar_nav_button("Fenabrave", "Fenabrave")

    youtube_active = st.session_state["nav_page"] == "YouTube"
    youtube_open = st.session_state["youtube_menu_open"] or youtube_active
    if st.button(
        "YouTube",
        use_container_width=True,
        key="nav-youtube-toggle",
        type="primary" if youtube_open else "secondary",
    ):
        st.session_state["youtube_menu_open"] = not youtube_open
        st.session_state["nav_page"] = "YouTube"
        if st.session_state["youtube_menu_open"] and st.session_state["youtube_subpage"] not in {"Melhores videos 7d", "Hot now"}:
            st.session_state["youtube_subpage"] = "Melhores videos 7d"
        st.rerun()

    if youtube_open:
        st.markdown('<div class="sidebar-nav-spacer"></div>', unsafe_allow_html=True)
        child_indent = st.columns([0.12, 0.88])
        with child_indent[0]:
            st.write("")
        with child_indent[1]:
            sidebar_nav_button("Melhores videos 7d", "YouTube", "Melhores videos 7d")
        child_indent = st.columns([0.12, 0.88])
        with child_indent[0]:
            st.write("")
        with child_indent[1]:
            sidebar_nav_button("Hot now", "YouTube", "Hot now")

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
youtube_subpage = st.session_state.get("youtube_subpage", "Melhores videos 7d")
creators_subpage = st.session_state.get("creators_subpage", "Visao geral")
cadastro_subpage = st.session_state.get("cadastro_subpage", "Criadores")

trace_startup(
    f"dispatch page={page} youtube={youtube_subpage} creators={creators_subpage} cadastro={cadastro_subpage}"
)

if page == "Overview":
    render_overview()
elif page == "YouTube":
    if youtube_subpage == "Hot now":
        render_youtube_hot_now_page()
    else:
        render_youtube_best_7d_page()
elif page == "Creators":
    if creators_subpage == "Criador individual":
        render_creator_detail_page()
    else:
        render_creator_overview_page()
elif page == "Data quality":
    render_data_quality_page()
elif page == "Fenabrave":
    render_fenabrave_dashboard_page()
elif page == "Cadastro":
    if cadastro_subpage == "Criadores":
        render_external_intake_page("Cadastro de Criadores")
    else:
        render_fenabrave_intake_page()
else:
    render_placeholder_page(
        "Sanitizacao operacional",
        "Revisao manual de casos operacionais e confirmacao de sanitizacao.",
    )
