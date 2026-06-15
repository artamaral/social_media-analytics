-- Migration: 2026-06-15_005_dashboard_queue_batch_timezone_down
-- Remove a view de dashboard com conversao explicita de timezone da fila.

drop view if exists public.v_dashboard_post_update_queue_batch;
