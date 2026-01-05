

-- Drop trigger + function first
DROP TRIGGER IF EXISTS trg_touch_conversation_updated_at ON conversation_messages;
DROP FUNCTION IF EXISTS touch_conversation_updated_at();

-- Drop tables
DROP TABLE IF EXISTS conversation_messages;
DROP TABLE IF EXISTS conversations;

-- Drop enum
DO $$
BEGIN
  IF EXISTS (SELECT 1 FROM pg_type WHERE typname = 'message_role') THEN
    DROP TYPE message_role;
  END IF;
END $$;

-- (Optional) keep extension installed; comment out if you want it removed on down
-- DROP EXTENSION IF EXISTS pgcrypto;
