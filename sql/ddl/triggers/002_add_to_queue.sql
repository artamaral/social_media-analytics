BEGIN
  INSERT INTO post_update_queue (
    post_id,
    priority_score,
    last_checked,
    next_check,
    needs_update
  )
  VALUES (
    NEW.post_id,
    COALESCE(NEW.views, 0) * 1 +
    COALESCE(NEW.likes, 0) * 10 +
    COALESCE(NEW.comments, 0) * 20,
    NULL,
    NOW(),
    TRUE
  )
  ON CONFLICT (post_id) DO NOTHING;

  RETURN NEW;
END;