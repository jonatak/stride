CREATE TABLE IF NOT EXISTS conversation_summaries (
  id BIGSERIAL PRIMARY KEY,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),

  -- Last messages.id that is covered by this summary (inclusive).
  up_to_message_id BIGINT NOT NULL,

  -- The summary text (you can treat it as "system memory")
  summary JSONB NOT NULL DEFAULT '{}'::jsonb
);

-- Fast lookup for the latest summary and for "summaries up to X"
CREATE INDEX IF NOT EXISTS conversation_summaries_up_to_message_id_idx
  ON conversation_summaries (up_to_message_id);

CREATE INDEX IF NOT EXISTS conversation_summaries_created_at_idx
  ON conversation_summaries (created_at);
