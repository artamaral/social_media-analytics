ALTER TABLE public.market_vehicle_brand_rankings
  ALTER COLUMN units DROP NOT NULL;

ALTER TABLE public.market_vehicle_brand_rankings
  DROP CONSTRAINT IF EXISTS market_vehicle_brand_rankings_units_check;

ALTER TABLE public.market_vehicle_brand_rankings
  ADD CONSTRAINT market_vehicle_brand_rankings_units_check CHECK (
    units IS NULL OR units >= 0
  );

ALTER TABLE public.market_vehicle_brand_rankings
  DROP CONSTRAINT IF EXISTS market_vehicle_brand_rankings_value_presence_check;

ALTER TABLE public.market_vehicle_brand_rankings
  ADD CONSTRAINT market_vehicle_brand_rankings_value_presence_check CHECK (
    units IS NOT NULL OR market_share_pct IS NOT NULL
  );
