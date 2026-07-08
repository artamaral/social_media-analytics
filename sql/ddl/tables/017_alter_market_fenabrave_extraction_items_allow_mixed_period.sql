-- 017_alter_market_fenabrave_extraction_items_allow_mixed_period.sql

ALTER TABLE public.market_fenabrave_extraction_items
  DROP CONSTRAINT IF EXISTS market_fenabrave_extraction_items_period_type_check;

ALTER TABLE public.market_fenabrave_extraction_items
  ADD CONSTRAINT market_fenabrave_extraction_items_period_type_check CHECK (
    published_period_type IN ('monthly', 'accumulated', 'mixed')
  );
