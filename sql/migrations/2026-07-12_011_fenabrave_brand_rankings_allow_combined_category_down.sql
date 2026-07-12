ALTER TABLE public.market_vehicle_brand_rankings
  DROP CONSTRAINT IF EXISTS market_vehicle_brand_rankings_category_check;

ALTER TABLE public.market_vehicle_brand_rankings
  ADD CONSTRAINT market_vehicle_brand_rankings_category_check CHECK (
    vehicle_category IN ('automoveis', 'comerciais_leves')
  );
