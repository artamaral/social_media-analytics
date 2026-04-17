BEGIN
  UPDATE posts
  SET
    views = NEW.views,
    likes = NEW.likes,
    comments = NEW.comments,
    collected_at = NEW.collected_at
  WHERE post_id = NEW.post_id;

  RETURN NEW;
END;