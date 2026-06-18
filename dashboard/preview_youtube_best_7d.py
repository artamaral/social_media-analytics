import argparse
import csv
import json
from datetime import datetime
from html import escape
from pathlib import Path


SAMPLE_ROWS = [
    {
        "post_date": "2026-06-15",
        "title": "Tracker diesel 2026: consumo real e o que mudou na pratica",
        "views": 418200,
        "likes": 28400,
        "comments": 1860,
    },
    {
        "post_date": "2026-06-14",
        "title": "BYD Dolphin Mini vs Kwid E-Tech: qual faz mais sentido hoje",
        "views": 392150,
        "likes": 25340,
        "comments": 2195,
    },
    {
        "post_date": "2026-06-13",
        "title": "10 SUVs usados ate 90 mil que ainda valem a compra",
        "views": 355980,
        "likes": 21110,
        "comments": 1498,
    },
    {
        "post_date": "2026-06-12",
        "title": "Nivus GTS: primeiras impressoes, acertos e exageros",
        "views": 332440,
        "likes": 19480,
        "comments": 1331,
    },
    {
        "post_date": "2026-06-11",
        "title": "Corolla Cross 2026: onde ele melhorou e onde ainda decepciona",
        "views": 309700,
        "likes": 17860,
        "comments": 1204,
    },
    {
        "post_date": "2026-06-10",
        "title": "Mercado de usados aqueceu? sinais reais nas lojas e nos anuncios",
        "views": 287920,
        "likes": 16590,
        "comments": 1096,
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
    .kpi-grid {{
      display: grid;
      grid-template-columns: repeat(4, minmax(0, 1fr));
      gap: 12px;
      margin-bottom: 18px;
    }}
    .kpi {{
      background: var(--surface-3);
      color: var(--text-dark);
      border-radius: 16px;
      overflow: hidden;
      border: 1px solid rgba(255,255,255,0.06);
      min-height: 132px;
    }}
    .kpi-head {{
      padding: 12px 14px;
      background: var(--surface-2);
      color: var(--text);
      font-size: 12px;
      font-weight: 800;
      text-transform: uppercase;
    }}
    .kpi-body {{
      padding: 16px;
    }}
    .kpi-value {{
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 12px;
      font-size: 30px;
      font-weight: 800;
      line-height: 1.05;
    }}
    .kpi-icon {{
      width: 42px;
      height: 42px;
      border-radius: 8px;
      background: var(--accent);
      color: white;
      display: inline-flex;
      align-items: center;
      justify-content: center;
      font-size: 13px;
      font-weight: 800;
      flex: 0 0 auto;
    }}
    .kpi-caption {{
      margin-top: 10px;
      font-size: 12px;
      font-weight: 700;
      color: #606774;
      text-transform: uppercase;
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
      vertical-align: top;
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
    .video-title {{
      font-size: 15px;
      font-weight: 700;
      line-height: 1.45;
      margin-bottom: 8px;
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
    .metric-stack {{
      display: grid;
      gap: 4px;
    }}
    .metric-label {{
      font-size: 11px;
      color: var(--muted);
      text-transform: uppercase;
      font-weight: 700;
      letter-spacing: 0.04em;
    }}
    .metric-number {{
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
      .kpi-grid {{ grid-template-columns: repeat(2, minmax(0, 1fr)); }}
    }}
    @media (max-width: 760px) {{
      body {{ padding: 16px; }}
      .kpi-grid {{ grid-template-columns: 1fr; }}
      .panel-head {{ display: grid; }}
      thead {{ display: none; }}
      table, tbody, tr, td {{ display: block; width: 100%; }}
      tbody td {{ padding: 12px 18px; }}
      tbody tr {{ padding: 6px 0; }}
      .metric-stack {{ gap: 2px; }}
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
          <div class="hero-note-title">Dados usados</div>
          <div class="hero-note-copy">`post_date`, `title`, `views`, `likes`, `comments`</div>
        </div>
        <div class="hero-note">
          <div class="hero-note-title">Dado faltante assumido</div>
          <div class="hero-note-copy">Thumbnail ainda nao entra na tela. O mockup nao finge que esse campo ja existe.</div>
        </div>
      </div>
    </section>

    <section class="kpi-grid">
      <article class="kpi">
        <div class="kpi-head">Videos no ranking</div>
        <div class="kpi-body">
          <div class="kpi-value"><span>{videos_total}</span><span class="kpi-icon">VD</span></div>
          <div class="kpi-caption">janela atual do mockup</div>
        </div>
      </article>
      <article class="kpi">
        <div class="kpi-head">Views somadas</div>
        <div class="kpi-body">
          <div class="kpi-value"><span>{views_total}</span><span class="kpi-icon">VW</span></div>
          <div class="kpi-caption">volume observado nos videos listados</div>
        </div>
      </article>
      <article class="kpi">
        <div class="kpi-head">Likes somados</div>
        <div class="kpi-body">
          <div class="kpi-value"><span>{likes_total}</span><span class="kpi-icon">LK</span></div>
          <div class="kpi-caption">apoio social agregado</div>
        </div>
      </article>
      <article class="kpi">
        <div class="kpi-head">Comentarios somados</div>
        <div class="kpi-body">
          <div class="kpi-value"><span>{comments_total}</span><span class="kpi-icon">CM</span></div>
          <div class="kpi-caption">sinal conversacional agregado</div>
        </div>
      </article>
    </section>

    <section class="panel">
      <div class="panel-head">
        <div>
          <div class="panel-title">Ranking editorial dos videos</div>
          <div class="panel-copy">Conceito inspirado na pagina de video stats do template da Windsor, adaptado para a base atual do projeto e sem thumbnail.</div>
        </div>
        <div class="legend-pill">ordenado por views no mockup</div>
      </div>
      <table>
        <thead>
          <tr>
            <th>#</th>
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
        help="CSV opcional com colunas: post_date,title,views,likes,comments",
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


def load_rows(path: Path | None) -> list[dict[str, object]]:
    if path is None:
        return SAMPLE_ROWS
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        rows = []
        for row in reader:
            rows.append(
                {
                    "post_date": str(row.get("post_date") or "").strip(),
                    "title": str(row.get("title") or "").strip(),
                    "views": int(float(row.get("views") or 0)),
                    "likes": int(float(row.get("likes") or 0)),
                    "comments": int(float(row.get("comments") or 0)),
                }
            )
        return rows


def build_table_rows(rows: list[dict[str, object]]) -> str:
    html_rows: list[str] = []
    for index, row in enumerate(sorted(rows, key=lambda item: int(item["views"]), reverse=True), start=1):
        html_rows.append(
            """
            <tr>
              <td><div class="rank">{rank}</div></td>
              <td>
                <div class="video-title">{title}</div>
                <div class="video-meta">
                  <span class="video-badge">sem thumbnail</span>
                  <span class="video-badge">mockup conceitual</span>
                </div>
              </td>
              <td><div class="metric-stack"><div class="metric-label">publicado em</div><div class="metric-number">{post_date}</div></div></td>
              <td><div class="metric-stack"><div class="metric-label">views</div><div class="metric-number">{views}</div></div></td>
              <td><div class="metric-stack"><div class="metric-label">likes</div><div class="metric-number">{likes}</div></div></td>
              <td><div class="metric-stack"><div class="metric-label">comentarios</div><div class="metric-number">{comments}</div></div></td>
            </tr>
            """.format(
                rank=index,
                title=escape(str(row["title"])),
                post_date=escape(format_date(str(row["post_date"]))),
                views=escape(format_int(int(row["views"]))),
                likes=escape(format_int(int(row["likes"]))),
                comments=escape(format_int(int(row["comments"]))),
            ).strip()
        )
    return "\n".join(html_rows)


def render_html(rows: list[dict[str, object]]) -> str:
    rows_sorted = sorted(rows, key=lambda item: int(item["views"]), reverse=True)
    videos_total = format_int(len(rows_sorted))
    views_total = format_int(sum(int(row["views"]) for row in rows_sorted))
    likes_total = format_int(sum(int(row["likes"]) for row in rows_sorted))
    comments_total = format_int(sum(int(row["comments"]) for row in rows_sorted))
    dates = [str(row["post_date"]) for row in rows_sorted if row.get("post_date")]
    window_label = f"{format_date(min(dates))} ate {format_date(max(dates))}" if dates else "Janela sem data"
    return HTML_TEMPLATE.format(
        window_label=escape(window_label),
        videos_total=escape(videos_total),
        views_total=escape(views_total),
        likes_total=escape(likes_total),
        comments_total=escape(comments_total),
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
