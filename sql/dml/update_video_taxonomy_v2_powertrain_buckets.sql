-- update_video_taxonomy_v2_powertrain_buckets.sql

-- Consolida a leitura operacional de motorizacao em dois buckets:
-- powertrain__eletrificados e powertrain__ice.
-- Rotas antigas de eletrico/hibrido/combustao ficam inativas para preservar
-- integridade historica, mas deixam de ser retornadas pelo harness.

BEGIN;

WITH tv AS (
  SELECT id
  FROM public.video_taxonomy_versions
  WHERE taxonomy_version = 'taxonomia_video_v2'
),
upsert_topic_paths AS (
  INSERT INTO public.video_taxonomy_topic_paths (
    taxonomy_version_id, topic_path_code, label_pt, parent_code, level,
    automotive_domain, default_activity_type, description, example_signals,
    allowed_in_pilot, requires_technical_context, allows_secondary_topic,
    is_active, source_row, updated_at
  )
  SELECT
    tv.id,
    v.topic_path_code,
    v.label_pt,
    v.parent_code,
    v.level,
    v.automotive_domain,
    v.default_activity_type,
    v.description,
    v.example_signals,
    v.allowed_in_pilot,
    v.requires_technical_context,
    v.allows_secondary_topic,
    true,
    v.source_row,
    now()
  FROM tv
  CROSS JOIN (
    VALUES
      (
        'powertrain__eletrificados',
        'Eletrificados',
        'powertrain',
        2,
        'powertrain',
        'analise_mercado',
        'Bucket operacional para eletricos, hibridos, plug-in, MHEV e demais eletrificados.',
        'eletrico; hibrido; plug-in; PHEV; MHEV; bateria; recarga; autonomia',
        true,
        true,
        true,
        '{"topic_path_code":"powertrain__eletrificados","label_pt":"Eletrificados","parent_code":"powertrain","level":"2","automotive_domain":"powertrain","default_activity_type":"analise_mercado","description":"Bucket operacional para eletricos, hibridos, plug-in, MHEV e demais eletrificados.","example_signals":"eletrico; hibrido; plug-in; PHEV; MHEV; bateria; recarga; autonomia","allowed_in_pilot":"true","requires_technical_context":"true","allows_secondary_topic":"true"}'::jsonb
      ),
      (
        'powertrain__ice',
        'ICE',
        'powertrain',
        2,
        'powertrain',
        'analise_mercado',
        'Bucket operacional para combustao interna, incluindo gasolina, etanol, flex, diesel, aspirado ou turbo.',
        'combustao; gasolina; etanol; flex; diesel; aspirado; turbo',
        true,
        true,
        true,
        '{"topic_path_code":"powertrain__ice","label_pt":"ICE","parent_code":"powertrain","level":"2","automotive_domain":"powertrain","default_activity_type":"analise_mercado","description":"Bucket operacional para combustao interna, incluindo gasolina, etanol, flex, diesel, aspirado ou turbo.","example_signals":"combustao; gasolina; etanol; flex; diesel; aspirado; turbo","allowed_in_pilot":"true","requires_technical_context":"true","allows_secondary_topic":"true"}'::jsonb
      )
  ) AS v (
    topic_path_code, label_pt, parent_code, level, automotive_domain,
    default_activity_type, description, example_signals, allowed_in_pilot,
    requires_technical_context, allows_secondary_topic, source_row
  )
  ON CONFLICT (taxonomy_version_id, topic_path_code) DO UPDATE SET
    label_pt = EXCLUDED.label_pt,
    parent_code = EXCLUDED.parent_code,
    level = EXCLUDED.level,
    automotive_domain = EXCLUDED.automotive_domain,
    default_activity_type = EXCLUDED.default_activity_type,
    description = EXCLUDED.description,
    example_signals = EXCLUDED.example_signals,
    allowed_in_pilot = EXCLUDED.allowed_in_pilot,
    requires_technical_context = EXCLUDED.requires_technical_context,
    allows_secondary_topic = EXCLUDED.allows_secondary_topic,
    is_active = true,
    source_row = EXCLUDED.source_row,
    updated_at = now()
  RETURNING topic_path_code
)
UPDATE public.video_taxonomy_topic_paths tp
SET
  is_active = false,
  updated_at = now()
FROM tv
WHERE tp.taxonomy_version_id = tv.id
  AND tp.topic_path_code IN (
    'powertrain__eletrico',
    'powertrain__eletrico__autonomia',
    'powertrain__eletrico__bateria_tracao',
    'powertrain__eletrico__garantia_bateria',
    'powertrain__eletrico__recarga',
    'powertrain__eletrico__regeneracao',
    'powertrain__hibrido',
    'powertrain__hibrido__hibrido_flex',
    'powertrain__hibrido__plug_in',
    'powertrain__hibrido__sistema_hibrido',
    'powertrain__combustao',
    'powertrain__combustao__aspirado',
    'powertrain__combustao__diesel',
    'powertrain__combustao__flex',
    'powertrain__combustao__turbo'
  );

WITH tv AS (
  SELECT id
  FROM public.video_taxonomy_versions
  WHERE taxonomy_version = 'taxonomia_video_v2'
),
compatibility_values AS (
  SELECT *
  FROM (
    VALUES
      ('cmp_027', 'powertrain__eletrificados', 'powertrain', 'bateria_tracao', NULL, 'allowed_with_evidence', 'Conteudo cujo foco principal e eletrificacao, bateria ou motorizacao eletrificada.', 'eletrico; hibrido; plug-in; PHEV; MHEV; bateria; autonomia; recarga', 'Eletricos e hibridos sobem para o bucket operacional Eletrificados.', true, '{"compatibility_id":"cmp_027","topic_path_code":"powertrain__eletrificados","automotive_system":"powertrain","component":"bateria_tracao","problem":"","compatibility_status":"allowed_with_evidence","required_evidence":"Conteudo cujo foco principal e eletrificacao, bateria ou motorizacao eletrificada.","example_signals":"eletrico; hibrido; plug-in; PHEV; MHEV; bateria; autonomia; recarga","validation_rule":"Eletricos e hibridos sobem para o bucket operacional Eletrificados.","allowed_in_pilot":"true"}'::jsonb),
      ('cmp_028', 'powertrain__eletrificados', 'powertrain', NULL, NULL, 'allowed_with_evidence', 'Conteudo cujo foco principal e eletrificacao sem componente tecnico especifico.', 'hibrido; eletrico; eletrificado; super hibrido; economico', 'Usar bucket Eletrificados; nao repetir sistema_hibrido como componente pleonastico.', true, '{"compatibility_id":"cmp_028","topic_path_code":"powertrain__eletrificados","automotive_system":"powertrain","component":"","problem":"","compatibility_status":"allowed_with_evidence","required_evidence":"Conteudo cujo foco principal e eletrificacao sem componente tecnico especifico.","example_signals":"hibrido; eletrico; eletrificado; super hibrido; economico","validation_rule":"Usar bucket Eletrificados; nao repetir sistema_hibrido como componente pleonastico.","allowed_in_pilot":"true"}'::jsonb),
      ('cmp_029', 'powertrain__ice', 'powertrain', 'motor_flex', NULL, 'allowed', 'Conteudo cujo foco principal e motor flex ou combustao interna.', 'flex; etanol; gasolina; combustao', 'Flex pertence ao bucket operacional ICE.', true, '{"compatibility_id":"cmp_029","topic_path_code":"powertrain__ice","automotive_system":"powertrain","component":"motor_flex","problem":"","compatibility_status":"allowed","required_evidence":"Conteudo cujo foco principal e motor flex ou combustao interna.","example_signals":"flex; etanol; gasolina; combustao","validation_rule":"Flex pertence ao bucket operacional ICE.","allowed_in_pilot":"true"}'::jsonb),
      ('cmp_030', 'powertrain__ice', 'powertrain', 'motor_diesel', NULL, 'allowed', 'Conteudo cujo foco principal e motor diesel ou combustao interna.', 'diesel; torque; consumo; combustao', 'Diesel pertence ao bucket operacional ICE.', true, '{"compatibility_id":"cmp_030","topic_path_code":"powertrain__ice","automotive_system":"powertrain","component":"motor_diesel","problem":"","compatibility_status":"allowed","required_evidence":"Conteudo cujo foco principal e motor diesel ou combustao interna.","example_signals":"diesel; torque; consumo; combustao","validation_rule":"Diesel pertence ao bucket operacional ICE.","allowed_in_pilot":"true"}'::jsonb),
      ('cmp_057', 'powertrain__eletrificados', 'powertrain', 'sistema_hibrido_plug_in', NULL, 'allowed_with_evidence', 'Veiculo hibrido plug-in como powertrain.', 'hibrido plug-in; PHEV; motorizacao hibrida', 'Hibrido plug-in pertence ao bucket operacional Eletrificados.', true, '{"compatibility_id":"cmp_057","topic_path_code":"powertrain__eletrificados","automotive_system":"powertrain","component":"sistema_hibrido_plug_in","problem":"","compatibility_status":"allowed_with_evidence","required_evidence":"Veiculo hibrido plug-in como powertrain.","example_signals":"hibrido plug-in; PHEV; motorizacao hibrida","validation_rule":"Hibrido plug-in pertence ao bucket operacional Eletrificados.","allowed_in_pilot":"true"}'::jsonb),
      ('cmp_103', 'powertrain__ice', 'motor', 'turbo', NULL, 'allowed_with_evidence', 'Conteudo de powertrain cita motor turbo como foco ou atributo forte.', 'motor turbo; turbo; desempenho; torque', 'Turbo entra como componente/feature de ICE, sem problem e sem virar rotulo solto.', true, '{"compatibility_id":"cmp_103","topic_path_code":"powertrain__ice","automotive_system":"motor","component":"turbo","problem":"","compatibility_status":"allowed_with_evidence","required_evidence":"Conteudo de powertrain cita motor turbo como foco ou atributo forte.","example_signals":"motor turbo; turbo; desempenho; torque","validation_rule":"Turbo entra como componente/feature de ICE, sem problem e sem virar rotulo solto.","allowed_in_pilot":"true"}'::jsonb)
  ) AS v (
    compatibility_id, topic_path_code, automotive_system, component, problem,
    compatibility_status, required_evidence, example_signals, validation_rule,
    allowed_in_pilot, source_row
  )
)
UPDATE public.video_taxonomy_technical_compatibility c
SET
  topic_path_code = v.topic_path_code,
  automotive_system = v.automotive_system,
  component = v.component,
  problem = v.problem,
  compatibility_status = v.compatibility_status,
  required_evidence = v.required_evidence,
  example_signals = v.example_signals,
  validation_rule = v.validation_rule,
  allowed_in_pilot = v.allowed_in_pilot,
  is_active = true,
  source_row = v.source_row,
  updated_at = now()
FROM tv
JOIN compatibility_values v ON true
WHERE c.taxonomy_version_id = tv.id
  AND c.compatibility_id = v.compatibility_id;

UPDATE public.video_taxonomy_versions
SET
  source_topic_paths_sha256 = 'BD5520AC830A74D7E0F821AA86B4A31899CAE787D4E9A4C96F3DFC383FAF6C0B',
  source_compatibility_sha256 = 'B59E4E128FB2482D37327E451E4119621652489437CE32198E262C4442CD1952',
  notes = 'Taxonomia Video V2 operacional com 93 topic_paths e 112 regras; motorizacao consolidada em Eletrificados vs ICE.'
WHERE taxonomy_version = 'taxonomia_video_v2';

COMMIT;
