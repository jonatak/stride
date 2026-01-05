

-- Core extensions
CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- Enums
DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'message_role') THEN
    CREATE TYPE message_role AS ENUM ('system', 'user', 'assistant', 'tool');
  END IF;
END $$;

-- Conversations
CREATE TABLE IF NOT EXISTS conversations (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  meta JSONB NOT NULL DEFAULT '{}'::jsonb
);

-- Messages
CREATE TABLE IF NOT EXISTS conversation_messages (
  id BIGSERIAL PRIMARY KEY,
  conversation_id UUID NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
  role message_role NOT NULL,
  content TEXT NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),

  metadata JSONB NOT NULL DEFAULT '{}'::jsonb
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_conversation_messages_conversation_id
  ON conversation_messages (conversation_id);

CREATE INDEX IF NOT EXISTS idx_conversation_messages_created_at
  ON conversation_messages (created_at);

CREATE INDEX IF NOT EXISTS idx_conversation_messages_conversation_id_created_at
  ON conversation_messages (conversation_id, created_at);

-- Keep conversations.updated_at fresh when new messages arrive
CREATE OR REPLACE FUNCTION touch_conversation_updated_at()
RETURNS TRIGGER AS $$
BEGIN
  UPDATE conversations
  SET updated_at = now()
  WHERE id = NEW.conversation_id;
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_touch_conversation_updated_at ON conversation_messages;
CREATE TRIGGER trg_touch_conversation_updated_at
AFTER INSERT ON conversation_messages
FOR EACH ROW
EXECUTE FUNCTION touch_conversation_updated_at();
