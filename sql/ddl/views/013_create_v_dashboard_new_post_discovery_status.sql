drop view if exists public.v_dashboard_new_post_discovery_status;

create view public.v_dashboard_new_post_discovery_status as
with latest_discovery as (
  select
    max(created_at) as ultima_descoberta_de_post,
    count(*) filter (where created_at >= now() - interval '24 hours') as novos_posts_24h
  from public.posts
),
classified as (
  select
    now() as checked_at,
    ultima_descoberta_de_post,
    novos_posts_24h,
    case
      when ultima_descoberta_de_post is null then null
      else floor(extract(epoch from (now() - ultima_descoberta_de_post)) / 60)::int
    end as idade_da_ultima_descoberta_minutos
  from latest_discovery
)
select
  checked_at,
  to_char(checked_at - interval '3 hours', 'DD/MM/YYYY HH24:MI') as checked_at_br,
  ultima_descoberta_de_post,
  to_char(ultima_descoberta_de_post - interval '3 hours', 'DD/MM/YYYY HH24:MI') as ultima_descoberta_de_post_br,
  idade_da_ultima_descoberta_minutos,
  novos_posts_24h,
  case
    when ultima_descoberta_de_post is null then 'nok'
    when idade_da_ultima_descoberta_minutos <= 360 then 'ok'
    when idade_da_ultima_descoberta_minutos <= 720 then 'atencao'
    else 'nok'
  end as status_code,
  case
    when ultima_descoberta_de_post is null then 'Descoberta sem evidencia'
    when idade_da_ultima_descoberta_minutos <= 360 then 'Descoberta em dia'
    when idade_da_ultima_descoberta_minutos <= 720 then 'Descoberta com atraso'
    else 'Descoberta sem evidencia recente'
  end as status_label,
  case
    when ultima_descoberta_de_post is null then 'Nenhum post novo encontrado na tabela posts.'
    when idade_da_ultima_descoberta_minutos <= 360 then 'Ultima descoberta dentro da janela esperada de 6 horas.'
    when idade_da_ultima_descoberta_minutos <= 720 then 'Ultima descoberta acima da janela ideal, mas ainda dentro do limite de atencao.'
    else 'Ultima descoberta acima do limite tolerado para o worker de 6 horas.'
  end as status_reason
from classified;

grant select on public.v_dashboard_new_post_discovery_status to anon;
grant select on public.v_dashboard_new_post_discovery_status to authenticated;
