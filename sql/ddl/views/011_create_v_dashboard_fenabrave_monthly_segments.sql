drop view if exists public.v_dashboard_fenabrave_monthly_segments;

create view public.v_dashboard_fenabrave_monthly_segments as
with segment_dictionary as (
  select *
  from (
    values
      ('autos', 'Autos', 'Autos', 'CAR', '#4f6fd7', 1),
      ('comerciais_leves', 'Comerciais leves', 'Com. leves', 'VAN', '#9b3f72', 2),
      ('caminhoes', 'Caminhoes', 'Caminhoes', 'TRK', '#77b95f', 3),
      ('onibus', 'Onibus', 'Onibus', 'BUS', '#3d8aa3', 4),
      ('motos', 'Motos', 'Motos', 'MOTO', '#de4b45', 5),
      ('implementos_rodoviarios', 'Implementos rodoviarios', 'Impl. rod.', 'TRL', '#f0b51f', 6)
  ) as t(segment_code, segment_label, segment_short_label, picto_code, color_hex, segment_sort)
),
base as (
  select
    r.reference_period,
    r.segment_code,
    d.segment_label,
    d.segment_short_label,
    d.picto_code,
    d.color_hex,
    d.segment_sort,
    r.mes_atual as monthly_units
  from public.market_vehicle_registrations_segment r
  join segment_dictionary d
    on d.segment_code = r.segment_code
)
select
  reference_period,
  extract(year from reference_period)::int as reference_year,
  extract(month from reference_period)::int as reference_month,
  to_char(reference_period, 'YYYY-MM') as reference_month_label,
  segment_code,
  segment_label,
  segment_short_label,
  picto_code,
  color_hex,
  segment_sort,
  monthly_units,
  sum(monthly_units) over (
    partition by segment_code, extract(year from reference_period)
    order by reference_period
    rows between unbounded preceding and current row
  ) as current_year_accumulated_units
from base
order by
  reference_period,
  segment_sort;

grant select on public.v_dashboard_fenabrave_monthly_segments to anon;
grant select on public.v_dashboard_fenabrave_monthly_segments to authenticated;
