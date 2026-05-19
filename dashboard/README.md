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

## Seguranca

- Nao versionar secrets reais.
- Nao usar `SUPABASE_SERVICE_ROLE_KEY` no app.
- Guardar credenciais em `.streamlit/secrets.toml` localmente ou em Secrets no Streamlit Community Cloud.
- A primeira conexao real deve carregar `v_dashboard_data_quality_status` antes dos rankings.
