# social_media-analytics
social_media-analytics



Schema Inserção de novos dados:
/sql
  /ddl
    001_create_entity_intake.sql
    002_create_entity_intake_review_view.sql
    003_create_publish_entity_intake_function.sql
    004_create_unique_index_entities_normalized_name.sql

  /dml
    publish_entity_intake_manual_run.sql
    review_entity_intake.sql
    intake_normalization_check.sql

  /maintenance
    deduplicate_entities.sql
    validate_entity_links.sql

  /docs
    entity_intake_process.md
