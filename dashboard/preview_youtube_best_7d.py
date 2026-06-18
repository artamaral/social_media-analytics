import argparse
import csv
import json
from datetime import datetime
from html import escape
from pathlib import Path


SAMPLE_ROWS = [
    {
        "video_type": "long",
        "post_date": "2026-06-15",
        "channel_name": "Auto Mercado Brasil",
        "title": "Tracker diesel 2026: consumo real e o que mudou na pratica",
        "views": 418200,
        "likes": 28400,
        "comments": 1860,
        "latest_collected_at": "2026-06-18 09:20",
        "snapshot_count": 14,
    },
    {
        "video_type": "short",
        "post_date": "2026-06-14",
        "channel_name": "Carro Chefe",
        "title": "BYD Dolphin Mini vs Kwid E-Tech: qual faz mais sentido hoje",
        "views": 392150,
        "likes": 25340,
        "comments": 2195,
        "latest_collected_at": "2026-06-18 08:45",
        "snapshot_count": 12,
    },
    {
        "video_type": "long",
        "post_date": "2026-06-13",
        "channel_name": "Guia dos Usados",
        "title": "10 SUVs usados ate 90 mil que ainda valem a compra",
        "views": 355980,
        "likes": 21110,
        "comments": 1498,
        "latest_collected_at": "2026-06-18 08:10",
        "snapshot_count": 11,
    },
    {
        "video_type": "long",
        "post_date": "2026-06-12",
        "channel_name": "Pista e Mercado",
        "title": "Nivus GTS: primeiras impressoes, acertos e exageros",
        "views": 332440,
        "likes": 19480,
        "comments": 1331,
        "latest_collected_at": "2026-06-18 07:30",
        "snapshot_count": 10,
    },
    {
        "video_type": "short",
        "post_date": "2026-06-11",
        "channel_name": "Analise Automotiva",
        "title": "Corolla Cross 2026: onde ele melhorou e onde ainda decepciona",
        "views": 309700,
        "likes": 17860,
        "comments": 1204,
        "latest_collected_at": "2026-06-18 06:55",
        "snapshot_count": 9,
    },
    {
        "video_type": "long",
        "post_date": "2026-06-10",
        "channel_name": "Radar dos Carros",
        "title": "Mercado de usados aqueceu? sinais reais nas lojas e nos anuncios",
        "views": 287920,
        "likes": 16590,
        "comments": 1096,
        "latest_collected_at": "2026-06-18 06:20",
        "snapshot_count": 8,
    },
    {
        "video_type": "short",
        "post_date": "2026-06-09",
        "channel_name": "Giro Curto Auto",
        "title": "3 hatches usados que ainda fazem sentido em 2026",
        "views": 245300,
        "likes": 14990,
        "comments": 980,
        "latest_collected_at": "2026-06-17 22:45",
        "snapshot_count": 7,
    },
    {
        "video_type": "long",
        "post_date": "2026-06-08",
        "channel_name": "Compara Motor",
        "title": "Sentra, Corolla ou Civic: comparativo real de uso",
        "views": 233880,
        "likes": 14120,
        "comments": 944,
        "latest_collected_at": "2026-06-17 21:30",
        "snapshot_count": 7,
    },
    {
        "video_type": "short",
        "post_date": "2026-06-07",
        "channel_name": "Auto em 1 Minuto",
        "title": "SUV turbo ou aspirado: qual bebe menos?",
        "views": 221740,
        "likes": 13680,
        "comments": 901,
        "latest_collected_at": "2026-06-17 20:50",
        "snapshot_count": 6,
    },
    {
        "video_type": "long",
        "post_date": "2026-06-06",
        "channel_name": "Planilha Automotiva",
        "title": "Os sedans medios com melhor custo de propriedade hoje",
        "views": 214560,
        "likes": 12940,
        "comments": 855,
        "latest_collected_at": "2026-06-17 20:05",
        "snapshot_count": 6,
    },
]


HTML_TEMPLATE = """<!doctype html>
<html lang="pt-BR">
<head>
  <meta charset="utf-8">
  <title>YouTube Melhores 7d Preview</title>
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <style>
    :root {{
      --bg: #111318;
      --surface: #1b1f27;
      --surface-2: #232833;
      --surface-3: #f4f6f7;
      --text: #f5f7fa;
      --muted: #aeb4bf;
      --text-dark: #232833;
      --accent: #ff8069;
      --accent-soft: rgba(255, 128, 105, 0.16);
      --line: rgba(255,255,255,0.08);
      --shadow: 0 24px 60px rgba(0,0,0,0.26);
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      font-family: Arial, sans-serif;
      background:
        radial-gradient(circle at top left, rgba(255, 128, 105, 0.14), transparent 26%),
        linear-gradient(180deg, #12151c 0%, #0d1016 100%);
      color: var(--text);
      padding: 24px;
    }}
    .page {{
      max-width: 1320px;
      margin: 0 auto;
    }}
    .hero {{
      display: grid;
      grid-template-columns: 1.3fr 0.9fr;
      gap: 18px;
      margin-bottom: 18px;
    }}
    .hero-main, .hero-side {{
      background: linear-gradient(180deg, rgba(34, 39, 49, 0.96), rgba(20, 24, 31, 0.96));
      border: 1px solid var(--line);
      border-radius: 18px;
      box-shadow: var(--shadow);
    }}
    .hero-main {{
      padding: 22px 24px;
    }}
    .eyebrow {{
      display: inline-flex;
      align-items: center;
      gap: 8px;
      font-size: 12px;
      color: var(--muted);
      text-transform: uppercase;
      letter-spacing: 0.08em;
      font-weight: 700;
      margin-bottom: 10px;
    }}
    .eyebrow::before {{
      content: "";
      width: 10px;
      height: 10px;
      border-radius: 999px;
      background: var(--accent);
      box-shadow: 0 0 0 6px var(--accent-soft);
    }}
    h1 {{
      margin: 0;
      font-size: 34px;
      line-height: 1.04;
      letter-spacing: -0.03em;
      max-width: 680px;
    }}
    .subtitle {{
      margin-top: 12px;
      color: var(--muted);
      font-size: 15px;
      line-height: 1.55;
      max-width: 760px;
    }}
    .chips {{
      display: flex;
      flex-wrap: wrap;
      gap: 10px;
      margin-top: 18px;
    }}
    .chip {{
      padding: 8px 12px;
      border-radius: 999px;
      background: rgba(255,255,255,0.05);
      color: var(--text);
      font-size: 12px;
      font-weight: 700;
      border: 1px solid rgba(255,255,255,0.07);
    }}
    .toolbar {{
      display: flex;
      justify-content: flex-end;
      margin-bottom: 14px;
    }}
    .selector {{
      display: inline-flex;
      gap: 8px;
      align-items: center;
      padding: 8px;
      border-radius: 999px;
      background: rgba(255,255,255,0.04);
      border: 1px solid rgba(255,255,255,0.08);
    }}
    .selector-label {{
      font-size: 11px;
      font-weight: 800;
      letter-spacing: 0.06em;
      text-transform: uppercase;
      color: var(--muted);
      padding: 0 6px 0 4px;
    }}
    .selector-button {{
      border: 0;
      border-radius: 999px;
      padding: 8px 12px;
      background: transparent;
      color: var(--muted);
      font-size: 12px;
      font-weight: 800;
      cursor: pointer;
    }}
    .selector-button.active {{
      background: var(--accent);
      color: white;
    }}
    .hero-side {{
      padding: 18px;
      display: grid;
      gap: 12px;
      align-content: start;
    }}
    .hero-note {{
      background: rgba(255,255,255,0.04);
      border: 1px solid rgba(255,255,255,0.06);
      border-radius: 14px;
      padding: 14px;
    }}
    .hero-note-title {{
      font-size: 12px;
      font-weight: 800;
      text-transform: uppercase;
      color: var(--muted);
      margin-bottom: 8px;
    }}
    .hero-note-copy {{
      font-size: 14px;
      line-height: 1.5;
      color: var(--text);
    }}
    .panel {{
      background: linear-gradient(180deg, rgba(31, 36, 45, 0.96), rgba(20, 24, 31, 0.96));
      border: 1px solid var(--line);
      border-radius: 18px;
      box-shadow: var(--shadow);
      overflow: hidden;
    }}
    .panel-head {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      gap: 16px;
      padding: 18px 20px 14px;
    }}
    .panel-title {{
      font-size: 18px;
      font-weight: 800;
    }}
    .panel-copy {{
      color: var(--muted);
      font-size: 13px;
      margin-top: 4px;
      line-height: 1.45;
    }}
    .legend-pill {{
      padding: 8px 12px;
      border-radius: 999px;
      background: rgba(255,255,255,0.05);
      border: 1px solid rgba(255,255,255,0.08);
      font-size: 12px;
      color: var(--muted);
      white-space: nowrap;
    }}
    table {{
      width: 100%;
      border-collapse: collapse;
    }}
    thead th {{
      text-align: left;
      padding: 12px 20px;
      font-size: 11px;
      letter-spacing: 0.06em;
      text-transform: uppercase;
      color: var(--muted);
      border-top: 1px solid var(--line);
      border-bottom: 1px solid var(--line);
    }}
    tbody td {{
      padding: 16px 20px;
      border-bottom: 1px solid rgba(255,255,255,0.06);
      vertical-align: middle;
    }}
    tbody tr:hover {{
      background: rgba(255,255,255,0.03);
    }}
    .rank {{
      font-size: 24px;
      font-weight: 800;
      color: var(--accent);
      line-height: 1;
    }}
    .thumb-shell {{
      width: 112px;
      height: 64px;
      border-radius: 12px;
      border: 1px dashed rgba(255,255,255,0.18);
      background:
        linear-gradient(135deg, rgba(255,255,255,0.05), rgba(255,255,255,0.02)),
        rgba(255,255,255,0.02);
      display: grid;
      place-items: center;
      overflow: hidden;
    }}
    .thumb-placeholder {{
      display: grid;
      gap: 6px;
      justify-items: center;
      color: var(--muted);
      text-transform: uppercase;
      letter-spacing: 0.05em;
      font-size: 10px;
      font-weight: 800;
    }}
    .thumb-icon {{
      width: 34px;
      height: 34px;
      border-radius: 10px;
      border: 1px solid rgba(255,255,255,0.12);
      display: inline-flex;
      align-items: center;
      justify-content: center;
      font-size: 11px;
      color: var(--text);
      background: rgba(255,255,255,0.04);
    }}
    .channel-name {{
      display: inline-flex;
      align-items: center;
      margin-bottom: 8px;
      padding: 4px 0;
      font-size: 12px;
      font-weight: 800;
      letter-spacing: 0.03em;
      text-transform: uppercase;
      color: var(--accent);
    }}
    .video-title {{
      font-size: 15px;
      font-weight: 700;
      line-height: 1.45;
      margin-bottom: 8px;
    }}
    .video-support {{
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
      margin-bottom: 10px;
    }}
    .video-support-item {{
      display: inline-flex;
      align-items: center;
      gap: 6px;
      padding: 5px 8px;
      border-radius: 999px;
      background: rgba(255,255,255,0.05);
      color: var(--muted);
      font-size: 11px;
      font-weight: 700;
    }}
    .video-support-label {{
      text-transform: uppercase;
      letter-spacing: 0.04em;
      color: #8991a0;
    }}
    .video-meta {{
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
    }}
    .video-badge {{
      display: inline-flex;
      align-items: center;
      padding: 5px 8px;
      border-radius: 999px;
      background: rgba(255,255,255,0.05);
      color: var(--muted);
      font-size: 11px;
      font-weight: 700;
    }}
    .metric-number {{
      display: flex;
      align-items: center;
      min-height: 64px;
      font-size: 16px;
      font-weight: 800;
      color: var(--text);
    }}
    .footer-note {{
      margin-top: 12px;
      color: var(--muted);
      font-size: 12px;
      line-height: 1.5;
    }}
    @media (max-width: 1080px) {{
      .hero {{ grid-template-columns: 1fr; }}
    }}
    @media (max-width: 760px) {{
      body {{ padding: 16px; }}
      .panel-head {{ display: grid; }}
      thead {{ display: none; }}
      table, tbody, tr, td {{ display: block; width: 100%; }}
      tbody td {{ padding: 12px 18px; }}
      tbody tr {{ padding: 6px 0; }}
    }}
  </style>
</head>
<body>
  <div class="page">
    <section class="hero">
      <div class="hero-main">
        <div class="eyebrow">Conceito inspirado no Windsor</div>
        <h1>YouTube · Melhores 7d</h1>
        <div class="subtitle">
          Mockup conceitual para a futura tela de ranking semanal. A estrutura prioriza leitura rapida de videos que mais performaram na janela recente, mas usa apenas os campos que ja temos hoje: data de publicacao, titulo, views, likes e comentarios.
        </div>
        <div class="chips">
          <div class="chip">sem thumbnail por enquanto</div>
          <div class="chip">ordenacao editorial por performance</div>
          <div class="chip">foco em tabela forte e leitura executiva</div>
        </div>
      </div>
      <div class="hero-side">
        <div class="hero-note">
          <div class="hero-note-title">Janela usada</div>
          <div class="hero-note-copy">{window_label}</div>
        </div>
        <div class="hero-note">
          <div class="hero-note-title">Semantica de 7d</div>
          <div class="hero-note-copy">Ultimos 7 dias completos fechados, excluindo o dia atual parcial.</div>
        </div>
        <div class="hero-note">
          <div class="hero-note-title">Dados usados</div>
          <div class="hero-note-copy">`video_type`, `channel_name`, `post_date`, `title`, `views`, `likes`, `comments`, `latest_collected_at`, `snapshot_count`</div>
        </div>
        <div class="hero-note">
          <div class="hero-note-title">Dado faltante assumido</div>
          <div class="hero-note-copy">Thumbnail ainda nao entra na tela. O mockup nao finge que esse campo ja existe.</div>
        </div>
      </div>
    </section>

    <div class="toolbar">
      <div class="selector">
        <span class="selector-label">Tipo de video</span>
        <button class="selector-button active" data-filter="todos">Todos</button>
        <button class="selector-button" data-filter="long">Long</button>
        <button class="selector-button" data-filter="short">Short</button>
      </div>
    </div>

    <section class="panel">
      <div class="panel-head">
        <div>
          <div class="panel-title">Ranking editorial dos videos</div>
          <div class="panel-copy">Conceito inspirado na pagina de video stats do template da Windsor, adaptado para a base atual do projeto e sem thumbnail. Cada filtro sempre mostra os 10 melhores videos dentro do universo selecionado.</div>
        </div>
        <div class="legend-pill">top 10 por filtro | ordenado por views no mockup</div>
      </div>
      <table>
        <thead>
          <tr>
            <th>#</th>
            <th>Thumbnail</th>
            <th>Video</th>
            <th>Data da publicacao</th>
            <th>Views</th>
            <th>Likes</th>
            <th>Comentarios</th>
          </tr>
        </thead>
        <tbody>
          {table_rows}
        </tbody>
      </table>
    </section>
    <div class="footer-note">
      Preview local gerado para iterar conceito e hierarquia visual antes da implementacao da pagina real no Streamlit.
    </div>
  </div>
  <script>
    const filterButtons = Array.from(document.querySelectorAll('.selector-button'));
    const tableRows = Array.from(document.querySelectorAll('tbody tr[data-video-type]'));

    function applyFilter(filterValue) {{
      let visibleCount = 0;
      filterButtons.forEach((button) => {{
        button.classList.toggle('active', button.dataset.filter === filterValue);
      }});
      tableRows.forEach((row) => {{
        const rowType = (row.getAttribute('data-video-type') || '').toLowerCase();
        const matchesFilter = filterValue === 'todos' || rowType === filterValue;
        const show = matchesFilter && visibleCount < 10;
        row.style.display = show ? '' : 'none';
        if (show) {{
          visibleCount += 1;
        }}
      }});
    }}

    filterButtons.forEach((button) => {{
      button.addEventListener('click', () => applyFilter(button.dataset.filter || 'todos'));
    }});
    applyFilter('todos');
  </script>
</body>
</html>
"""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Gera um preview local em HTML para o mockup de YouTube > Melhores 7d."
    )
    parser.add_argument(
        "--input",
        type=Path,
        help="CSV opcional com colunas: video_type,channel_name,post_date,title,views,likes,comments,latest_collected_at,snapshot_count",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("dashboard/preview/youtube_best_7d_preview.html"),
        help="Caminho do HTML de saida.",
    )
    return parser.parse_args()


def format_int(value: int) -> str:
    return f"{value:,}".replace(",", ".")


def format_date(value: str) -> str:
    try:
        return datetime.fromisoformat(value).strftime("%d/%m/%Y")
    except ValueError:
        return value


def format_timestamp(value: str) -> str:
    if not value:
        return "--"
    normalized = value.replace("T", " ")
    for fmt in ("%Y-%m-%d %H:%M", "%Y-%m-%d %H:%M:%S"):
        try:
            return datetime.strptime(normalized, fmt).strftime("%d/%m %H:%M")
        except ValueError:
            continue
    return value


def load_rows(path: Path | None) -> list[dict[str, object]]:
    if path is None:
        return SAMPLE_ROWS
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        rows = []
        for row in reader:
            rows.append(
                {
                    "video_type": str(row.get("video_type") or "long").strip().lower(),
                    "channel_name": str(row.get("channel_name") or "").strip(),
                    "post_date": str(row.get("post_date") or "").strip(),
                    "title": str(row.get("title") or "").strip(),
                    "views": int(float(row.get("views") or 0)),
                    "likes": int(float(row.get("likes") or 0)),
                    "comments": int(float(row.get("comments") or 0)),
                    "latest_collected_at": str(row.get("latest_collected_at") or "").strip(),
                    "snapshot_count": int(float(row.get("snapshot_count") or 0)),
                }
            )
        return rows


def build_table_rows(rows: list[dict[str, object]]) -> str:
    html_rows: list[str] = []
    for index, row in enumerate(sorted(rows, key=lambda item: int(item["views"]), reverse=True), start=1):
        html_rows.append(
            """
            <tr data-video-type="{video_type}">
              <td><div class="rank">{rank}</div></td>
              <td>
                <div class="thumb-shell">
                  <div class="thumb-placeholder">
                    <span class="thumb-icon">IMG</span>
                    <span>thumbnail</span>
                  </div>
                </div>
              </td>
              <td>
                <div class="channel-name">{channel_name}</div>
                <div class="video-title">{title}</div>
                <div class="video-support">
                  <span class="video-support-item"><span class="video-support-label">tipo</span><span>{video_type_badge}</span></span>
                  <span class="video-support-item"><span class="video-support-label">ultimo snapshot</span><span>{latest_collected_at}</span></span>
                  <span class="video-support-item"><span class="video-support-label">snapshots</span><span>{snapshot_count}</span></span>
                </div>
                <div class="video-meta">
                  <span class="video-badge">sem thumbnail</span>
                  <span class="video-badge">mockup conceitual</span>
                </div>
              </td>
              <td><div class="metric-number">{post_date}</div></td>
              <td><div class="metric-number">{views}</div></td>
              <td><div class="metric-number">{likes}</div></td>
              <td><div class="metric-number">{comments}</div></td>
            </tr>
            """.format(
                rank=index,
                video_type=escape(str(row.get("video_type") or "long").lower()),
                video_type_badge=escape(str(row.get("video_type") or "long").upper()),
                channel_name=escape(str(row.get("channel_name") or "Canal sem nome")),
                title=escape(str(row["title"])),
                latest_collected_at=escape(format_timestamp(str(row.get("latest_collected_at") or ""))),
                snapshot_count=escape(format_int(int(row.get("snapshot_count") or 0))),
                post_date=escape(format_date(str(row["post_date"]))),
                views=escape(format_int(int(row["views"]))),
                likes=escape(format_int(int(row["likes"]))),
                comments=escape(format_int(int(row["comments"]))),
            ).strip()
        )
    return "\n".join(html_rows)


def render_html(rows: list[dict[str, object]]) -> str:
    rows_sorted = sorted(rows, key=lambda item: int(item["views"]), reverse=True)
    dates = [str(row["post_date"]) for row in rows_sorted if row.get("post_date")]
    window_label = f"{format_date(min(dates))} ate {format_date(max(dates))}" if dates else "Janela sem data"
    return HTML_TEMPLATE.format(
        window_label=escape(window_label),
        table_rows=build_table_rows(rows_sorted),
    )


def main() -> None:
    args = parse_args()
    rows = load_rows(args.input)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(render_html(rows), encoding="utf-8")
    print(json.dumps({"output": str(args.output), "rows": len(rows)}, ensure_ascii=True))


if __name__ == "__main__":
    main()
