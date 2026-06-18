# Streamlit dashboard

Dashboard interno para estudos de mercado automotivo.

## Deploy inicial

Configuracao recomendada no Streamlit Community Cloud:

```text
Repository: social_media-analytics
Branch: codex/dashboard-streamlit-mvp
Main file path: dashboard/streamlit_app.py
```

## Rodar localmente

Executar a partir da raiz do repositorio:

```powershell
streamlit run dashboard/streamlit_app.py
```

## Preview local do grafico da overview

Para iterar no bloco de atividade recente sem depender de deploy no Streamlit:

```powershell
python dashboard/preview_overview_recent_activity.py
```

Isso gera um HTML local em:

```text
dashboard/preview/overview_recent_activity_preview.html
```

Tambem e possivel usar um CSV proprio:

```powershell
python dashboard/preview_overview_recent_activity.py --input C:\caminho\overview_recent_activity.csv
```

## Preview local do mockup YouTube > Melhores 7d

Para iterar no conceito visual da futura tela de ranking semanal com os campos
ja disponiveis hoje:

```powershell
python dashboard/preview_youtube_best_7d.py
```

Isso gera um HTML local em:

```text
dashboard/preview/youtube_best_7d_preview.html
```

Tambem e possivel usar um CSV proprio com colunas `post_date`, `title`,
`views`, `likes` e `comments`:

```powershell
python dashboard/preview_youtube_best_7d.py --input C:\caminho\youtube_best_7d.csv
```

## Seguranca

- Nao versionar secrets reais.
- Nao usar `SUPABASE_SERVICE_ROLE_KEY` no app.
- Guardar credenciais em `.streamlit/secrets.toml` localmente ou em Secrets no Streamlit Community Cloud.
- A primeira conexao real deve carregar `v_dashboard_data_quality_status` antes dos rankings.

## Secrets esperados

Configurar localmente em `.streamlit/secrets.toml` ou no painel do Streamlit Community Cloud:

```toml
SUPABASE_URL = "https://your-project.supabase.co"
SUPABASE_ANON_KEY = "your-anon-key"
```

O app usa apenas leitura das views do dashboard. A service role key nao deve ser usada.
