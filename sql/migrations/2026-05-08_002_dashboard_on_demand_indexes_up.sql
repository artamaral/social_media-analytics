CREATE INDEX IF NOT EXISTS idx_post_metrics_history_post_id_collected_at
ON public.post_metrics_history (post_id, collected_at DESC);

CREATE INDEX IF NOT EXISTS idx_posts_creator_id_post_date
ON public.posts (creator_id, post_date DESC);

CREATE INDEX IF NOT EXISTS idx_posts_collected_at
ON public.posts (collected_at);
