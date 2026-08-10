drop view if exists public.v_market_fenabrave_extraction_coverage;
drop view if exists public.v_market_fenabrave_electrified_registrations;
drop view if exists public.v_market_fenabrave_sales_channel_mix;
drop view if exists public.v_market_fenabrave_subsegment_shares;
drop view if exists public.v_market_fenabrave_brand_rankings;
drop view if exists public.v_market_fenabrave_model_rankings;
drop view if exists public.v_market_registration_segment_summary;

create view public.v_market_registration_segment_summary as
with source_context as (
  select
    r.source_file_id,
    date_trunc('month', r.reference_period)::date as reference_period,
    r.segment_code,
    r.segmento,
    r.mes_atual,
    s.source_name,
    f.source_url,
    f.source_page_url,
    f.storage_bucket,
    f.storage_path,
    f.original_filename,
    f.captured_at,
    f.extraction_status
  from public.market_vehicle_registrations_segment r
  join public.market_source_files f
    on f.id = r.source_file_id
  join public.market_data_sources s
    on s.id = f.source_id
  where s.source_name = 'Fenabrave'
    and f.extraction_status = 'validated'
),
enriched as (
  select
    source_file_id,
    reference_period,
    extract(year from reference_period)::int as reference_year,
    extract(month from reference_period)::int as reference_month,
    to_char(reference_period, 'YYYY-MM') as reference_month_label,
    'Brasil'::text as market_scope,
    'emplacamentos'::text as metric_name,
    segment_code,
    segmento,
    mes_atual,
    sum(mes_atual) over (
      partition by segment_code, extract(year from reference_period)
      order by reference_period
      rows between unbounded preceding and current row
    ) as current_year_accumulated_units,
    lag(mes_atual) over (
      partition by segment_code
      order by reference_period
    ) as previous_month_units,
    lag(mes_atual, 12) over (
      partition by segment_code
      order by reference_period
    ) as previous_year_month_units,
    source_name,
    source_url,
    source_page_url,
    storage_bucket,
    storage_path,
    original_filename,
    captured_at,
    extraction_status
  from source_context
)
select
  source_file_id,
  reference_period,
  reference_year,
  reference_month,
  reference_month_label,
  market_scope,
  metric_name,
  segment_code,
  segmento,
  mes_atual,
  current_year_accumulated_units,
  previous_month_units,
  previous_year_month_units,
  case
    when previous_month_units is null or previous_month_units = 0 then null
    else round(((mes_atual::numeric / previous_month_units) - 1) * 100, 2)
  end as month_over_month_pct,
  case
    when previous_year_month_units is null or previous_year_month_units = 0 then null
    else round(((mes_atual::numeric / previous_year_month_units) - 1) * 100, 2)
  end as year_over_year_pct,
  source_name,
  source_url,
  source_page_url,
  storage_bucket,
  storage_path,
  original_filename,
  captured_at,
  extraction_status
from enriched;

create view public.v_market_fenabrave_model_rankings as
select
  r.source_file_id,
  date_trunc('month', r.reference_period)::date as reference_period,
  extract(year from date_trunc('month', r.reference_period))::int as reference_year,
  extract(month from date_trunc('month', r.reference_period))::int as reference_month,
  to_char(date_trunc('month', r.reference_period), 'YYYY-MM') as reference_month_label,
  i.item_code,
  i.item_label,
  i.pdf_page,
  r.published_period_type,
  r.market_scope,
  r.vehicle_category,
  r.sales_channel,
  r.rank_position,
  r.brand_name_raw,
  r.model_name_raw,
  r.model_label_raw,
  r.monthly_units,
  r.market_share_pct,
  s.source_name,
  f.source_url,
  f.source_page_url,
  f.storage_bucket,
  f.storage_path,
  f.original_filename,
  f.captured_at,
  i.status as item_status,
  i.validation_status,
  i.validation_notes
from public.market_vehicle_model_rankings r
join public.market_fenabrave_extraction_items i
  on i.source_file_id = r.source_file_id
 and i.item_code = r.item_code
join public.market_source_files f
  on f.id = r.source_file_id
join public.market_data_sources s
  on s.id = f.source_id
where s.source_name = 'Fenabrave'
  and i.status in ('validated', 'warning_accepted')
order by
  date_trunc('month', r.reference_period)::date,
  i.pdf_page,
  r.vehicle_category,
  r.sales_channel,
  r.rank_position;

create view public.v_market_fenabrave_brand_rankings as
select
  r.source_file_id,
  date_trunc('month', r.reference_period)::date as reference_period,
  extract(year from date_trunc('month', r.reference_period))::int as reference_year,
  extract(month from date_trunc('month', r.reference_period))::int as reference_month,
  to_char(date_trunc('month', r.reference_period), 'YYYY-MM') as reference_month_label,
  i.item_code,
  i.item_label,
  i.pdf_page,
  r.published_period_type,
  r.market_scope,
  r.vehicle_category,
  r.sales_channel,
  r.rank_position,
  r.brand_name_raw,
  r.units,
  r.market_share_pct,
  r.raw_label,
  s.source_name,
  f.source_url,
  f.source_page_url,
  f.storage_bucket,
  f.storage_path,
  f.original_filename,
  f.captured_at,
  i.status as item_status,
  i.validation_status,
  i.validation_notes
from public.market_vehicle_brand_rankings r
join public.market_fenabrave_extraction_items i
  on i.source_file_id = r.source_file_id
 and i.item_code = r.item_code
join public.market_source_files f
  on f.id = r.source_file_id
join public.market_data_sources s
  on s.id = f.source_id
where s.source_name = 'Fenabrave'
  and i.status in ('validated', 'warning_accepted')
order by
  date_trunc('month', r.reference_period)::date,
  i.pdf_page,
  r.vehicle_category,
  r.sales_channel,
  r.rank_position;

create view public.v_market_fenabrave_subsegment_shares as
select
  r.source_file_id,
  date_trunc('month', r.reference_period)::date as reference_period,
  extract(year from date_trunc('month', r.reference_period))::int as reference_year,
  extract(month from date_trunc('month', r.reference_period))::int as reference_month,
  to_char(date_trunc('month', r.reference_period), 'YYYY-MM') as reference_month_label,
  i.item_code,
  i.item_label,
  i.pdf_page,
  r.published_period_type,
  r.market_scope,
  r.vehicle_category,
  r.sales_channel,
  r.subsegment_name,
  r.current_month_share_pct,
  r.current_year_accum_share_pct,
  r.prior_year_accum_share_pct,
  r.raw_label,
  s.source_name,
  f.source_url,
  f.source_page_url,
  f.storage_bucket,
  f.storage_path,
  f.original_filename,
  f.captured_at,
  i.status as item_status,
  i.validation_status,
  i.validation_notes
from public.market_vehicle_subsegment_shares r
join public.market_fenabrave_extraction_items i
  on i.source_file_id = r.source_file_id
 and i.item_code = r.item_code
join public.market_source_files f
  on f.id = r.source_file_id
join public.market_data_sources s
  on s.id = f.source_id
where s.source_name = 'Fenabrave'
  and i.status in ('validated', 'warning_accepted')
order by
  date_trunc('month', r.reference_period)::date,
  r.subsegment_name;

create view public.v_market_fenabrave_sales_channel_mix as
select
  r.source_file_id,
  date_trunc('month', r.reference_period)::date as reference_period,
  extract(year from date_trunc('month', r.reference_period))::int as reference_year,
  extract(month from date_trunc('month', r.reference_period))::int as reference_month,
  to_char(date_trunc('month', r.reference_period), 'YYYY-MM') as reference_month_label,
  i.item_code,
  i.item_label,
  i.pdf_page,
  r.published_period_type,
  r.market_scope,
  r.vehicle_category,
  r.sales_channel,
  r.share_pct,
  r.raw_label,
  s.source_name,
  f.source_url,
  f.source_page_url,
  f.storage_bucket,
  f.storage_path,
  f.original_filename,
  f.captured_at,
  i.status as item_status,
  i.validation_status,
  i.validation_notes
from public.market_vehicle_sales_channel_mix r
join public.market_fenabrave_extraction_items i
  on i.source_file_id = r.source_file_id
 and i.item_code = r.item_code
join public.market_source_files f
  on f.id = r.source_file_id
join public.market_data_sources s
  on s.id = f.source_id
where s.source_name = 'Fenabrave'
  and i.status in ('validated', 'warning_accepted')
order by
  date_trunc('month', r.reference_period)::date,
  i.pdf_page,
  r.vehicle_category,
  r.sales_channel;

create view public.v_market_fenabrave_electrified_registrations as
select
  r.source_file_id,
  date_trunc('month', r.reference_period)::date as reference_period,
  extract(year from date_trunc('month', r.reference_period))::int as reference_year,
  extract(month from date_trunc('month', r.reference_period))::int as reference_month,
  to_char(date_trunc('month', r.reference_period), 'YYYY-MM') as reference_month_label,
  i.item_code,
  i.item_label,
  i.pdf_page,
  r.published_period_type,
  r.market_scope,
  r.aggregation_level,
  r.powertrain_type,
  r.vehicle_category,
  r.rank_position,
  r.brand_name_raw,
  r.model_name_raw,
  r.units,
  r.market_share_pct,
  r.raw_label,
  s.source_name,
  f.source_url,
  f.source_page_url,
  f.storage_bucket,
  f.storage_path,
  f.original_filename,
  f.captured_at,
  i.status as item_status,
  i.validation_status,
  i.validation_notes
from public.market_vehicle_electrified_registrations r
join public.market_fenabrave_extraction_items i
  on i.source_file_id = r.source_file_id
 and i.item_code = r.item_code
join public.market_source_files f
  on f.id = r.source_file_id
join public.market_data_sources s
  on s.id = f.source_id
where s.source_name = 'Fenabrave'
  and i.status in ('validated', 'warning_accepted')
order by
  date_trunc('month', r.reference_period)::date,
  i.pdf_page,
  r.vehicle_category,
  r.aggregation_level,
  r.powertrain_type,
  r.rank_position nulls first,
  r.brand_name_raw nulls first,
  r.model_name_raw nulls first;

create view public.v_market_fenabrave_extraction_coverage as
with expected_items as (
  select *
  from (
    values
      ('fenabrave_item_17_participacao_mercado_marca_mes', 'Participacao de mercado por marca mes', 3, 'monthly'),
      ('fenabrave_item_18_participacao_mercado_marca_acumulado', 'Participacao de mercado por marca acumulado', 4, 'accumulated'),
      ('fenabrave_item_01_ranking_emplacamentos_mes', 'Ranking dos emplacamentos mes', 6, 'monthly'),
      ('fenabrave_item_02_ranking_emplacamentos_acumulado', 'Ranking dos emplacamentos acumulado', 7, 'accumulated'),
      ('fenabrave_item_03_ranking_por_marca_mes', 'Ranking por marca mes', 8, 'monthly'),
      ('fenabrave_item_04_ranking_por_marca_acumulado', 'Ranking por marca acumulado', 9, 'accumulated'),
      ('fenabrave_item_05_emplacamentos_por_subsegmento', 'Emplacamentos por sub segmento', 17, 'mixed'),
      ('fenabrave_item_06_mercado_eletrificados_mes', 'Mercado de eletrificados mes', 20, 'monthly'),
      ('fenabrave_item_07_total_marca_hibrido_mes', 'Total por marca hibrido mes', 20, 'monthly'),
      ('fenabrave_item_08_total_marca_eletrico_mes', 'Total por marca eletrico mes', 20, 'monthly'),
      ('fenabrave_item_11_participacao_venda_direta_varejo_mes', 'Participacao de venda direta e varejo mes', 24, 'monthly'),
      ('fenabrave_item_12_participacao_venda_direta_varejo_acumulado', 'Participacao de venda direta e varejo acumulado', 25, 'accumulated'),
      ('fenabrave_item_13_ranking_marca_emplacamento_varejo_mes', 'Ranking por marca de emplacamento varejo mes', 26, 'monthly'),
      ('fenabrave_item_14_ranking_marca_emplacamento_varejo_acumulado', 'Ranking por marca de emplacamento varejo acumulado', 27, 'accumulated'),
      ('fenabrave_item_15_ranking_marca_emplacamento_direta_mes', 'Ranking por marca de emplacamento direta mes', 28, 'monthly'),
      ('fenabrave_item_16_ranking_marca_emplacamento_direta_acumulado', 'Ranking por marca de emplacamento direta acumulado', 29, 'accumulated'),
      ('fenabrave_item_19_modelos_emplacados_venda_direta_mes', 'Modelos mais emplacados venda direta mes', 30, 'monthly'),
      ('fenabrave_item_20_modelos_emplacados_varejo_mes', 'Modelos mais emplacados venda varejo mes', 31, 'monthly'),
      ('fenabrave_item_21_modelos_emplacados_venda_direta_acumulado', 'Modelos mais emplacados venda direta acumulado', 32, 'accumulated'),
      ('fenabrave_item_22_modelos_emplacados_varejo_acumulado', 'Modelos mais emplacados venda varejo acumulado', 33, 'accumulated')
  ) as t(item_code, item_label, pdf_page, published_period_type)
),
source_files as (
  select
    f.id as source_file_id,
    date_trunc('month', f.reference_period)::date as reference_period,
    extract(year from date_trunc('month', f.reference_period))::int as reference_year,
    extract(month from date_trunc('month', f.reference_period))::int as reference_month,
    to_char(date_trunc('month', f.reference_period), 'YYYY-MM') as reference_month_label,
    s.source_name,
    f.source_url,
    f.source_page_url,
    f.storage_bucket,
    f.storage_path,
    f.original_filename,
    f.captured_at,
    f.extraction_status
  from public.market_source_files f
  join public.market_data_sources s
    on s.id = f.source_id
  where s.source_name = 'Fenabrave'
),
actual_counts as (
  select
    source_file_id,
    item_code,
    count(*) as actual_row_count
  from (
    select source_file_id, item_code from public.market_vehicle_model_rankings
    union all
    select source_file_id, item_code from public.market_vehicle_brand_rankings
    union all
    select source_file_id, item_code from public.market_vehicle_subsegment_shares
    union all
    select source_file_id, item_code from public.market_vehicle_electrified_registrations
    union all
    select source_file_id, item_code from public.market_vehicle_sales_channel_mix
  ) unioned_rows
  group by source_file_id, item_code
)
select
  f.source_file_id,
  f.reference_period,
  f.reference_year,
  f.reference_month,
  f.reference_month_label,
  e.item_code,
  coalesce(i.item_label, e.item_label) as item_label,
  coalesce(i.pdf_page, e.pdf_page) as pdf_page,
  coalesce(i.published_period_type, e.published_period_type) as published_period_type,
  i.market_scope,
  i.status as item_status,
  i.row_count as control_row_count,
  a.actual_row_count,
  i.validation_status,
  i.validation_notes,
  case
    when i.id is null then 'missing_control'
    when i.status in ('validated', 'warning_accepted')
      and i.row_count is not distinct from a.actual_row_count
      then 'covered'
    when i.status in ('pending', 'extracted') then 'pending'
    when i.status = 'failed' then 'failed'
    when i.status = 'skipped' then 'skipped'
    else 'review'
  end as coverage_status,
  f.source_name,
  f.source_url,
  f.source_page_url,
  f.storage_bucket,
  f.storage_path,
  f.original_filename,
  f.captured_at,
  f.extraction_status
from source_files f
cross join expected_items e
left join public.market_fenabrave_extraction_items i
  on i.source_file_id = f.source_file_id
 and i.item_code = e.item_code
left join actual_counts a
  on a.source_file_id = f.source_file_id
 and a.item_code = e.item_code
order by
  f.reference_period,
  coalesce(i.pdf_page, e.pdf_page),
  e.item_code;

grant select on public.v_market_registration_segment_summary to anon;
grant select on public.v_market_registration_segment_summary to authenticated;

grant select on public.v_market_fenabrave_model_rankings to anon;
grant select on public.v_market_fenabrave_model_rankings to authenticated;

grant select on public.v_market_fenabrave_brand_rankings to anon;
grant select on public.v_market_fenabrave_brand_rankings to authenticated;

grant select on public.v_market_fenabrave_subsegment_shares to anon;
grant select on public.v_market_fenabrave_subsegment_shares to authenticated;

grant select on public.v_market_fenabrave_sales_channel_mix to anon;
grant select on public.v_market_fenabrave_sales_channel_mix to authenticated;

grant select on public.v_market_fenabrave_electrified_registrations to anon;
grant select on public.v_market_fenabrave_electrified_registrations to authenticated;

grant select on public.v_market_fenabrave_extraction_coverage to anon;
grant select on public.v_market_fenabrave_extraction_coverage to authenticated;
