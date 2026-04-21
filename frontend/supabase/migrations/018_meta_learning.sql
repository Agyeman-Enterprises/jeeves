-- Migration 018: Meta-Learning
CREATE TABLE IF NOT EXISTS jarvis_decision_outcomes (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL,
  workspace_id UUID,
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now()
);

COMMENT ON TABLE jarvis_decision_outcomes IS 'Decision quality tracking over time';

CREATE TABLE IF NOT EXISTS jarvis_preference_learning (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL,
  workspace_id UUID,
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now()
);

COMMENT ON TABLE jarvis_preference_learning IS 'Learned user preferences';

CREATE TABLE IF NOT EXISTS jarvis_agent_performance (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL,
  workspace_id UUID,
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now()
);

COMMENT ON TABLE jarvis_agent_performance IS 'Agent performance tracking';

CREATE TABLE IF NOT EXISTS jarvis_forecast_accuracy (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL,
  workspace_id UUID,
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now()
);

COMMENT ON TABLE jarvis_forecast_accuracy IS 'Forecast accuracy tracking';

CREATE TABLE IF NOT EXISTS jarvis_notification_effectiveness (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL,
  workspace_id UUID,
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now()
);

COMMENT ON TABLE jarvis_notification_effectiveness IS 'Notification effectiveness tracking';

CREATE TABLE IF NOT EXISTS jarvis_meta_insights (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL,
  workspace_id UUID,
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now()
);

COMMENT ON TABLE jarvis_meta_insights IS 'Meta-learning insights';

CREATE TABLE IF NOT EXISTS jarvis_meta_learning_config (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL,
  workspace_id UUID,
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now()
);

COMMENT ON TABLE jarvis_meta_learning_config IS 'Meta-learning configuration';

ALTER TABLE jarvis_decision_outcomes ENABLE ROW LEVEL SECURITY;
ALTER TABLE jarvis_preference_learning ENABLE ROW LEVEL SECURITY;
ALTER TABLE jarvis_agent_performance ENABLE ROW LEVEL SECURITY;
ALTER TABLE jarvis_forecast_accuracy ENABLE ROW LEVEL SECURITY;
ALTER TABLE jarvis_notification_effectiveness ENABLE ROW LEVEL SECURITY;
ALTER TABLE jarvis_meta_insights ENABLE ROW LEVEL SECURITY;
ALTER TABLE jarvis_meta_learning_config ENABLE ROW LEVEL SECURITY;

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_policies
    WHERE tablename = 'jarvis_decision_outcomes'
      AND policyname = 'allow_user'
  ) THEN
    CREATE POLICY "allow_user" ON jarvis_decision_outcomes
      FOR ALL USING (auth.uid() IS NOT NULL);
  END IF;

  IF NOT EXISTS (
    SELECT 1 FROM pg_policies
    WHERE tablename = 'jarvis_preference_learning'
      AND policyname = 'allow_user'
  ) THEN
    CREATE POLICY "allow_user" ON jarvis_preference_learning
      FOR ALL USING (auth.uid() IS NOT NULL);
  END IF;

  IF NOT EXISTS (
    SELECT 1 FROM pg_policies
    WHERE tablename = 'jarvis_agent_performance'
      AND policyname = 'allow_user'
  ) THEN
    CREATE POLICY "allow_user" ON jarvis_agent_performance
      FOR ALL USING (auth.uid() IS NOT NULL);
  END IF;

  IF NOT EXISTS (
    SELECT 1 FROM pg_policies
    WHERE tablename = 'jarvis_forecast_accuracy'
      AND policyname = 'allow_user'
  ) THEN
    CREATE POLICY "allow_user" ON jarvis_forecast_accuracy
      FOR ALL USING (auth.uid() IS NOT NULL);
  END IF;

  IF NOT EXISTS (
    SELECT 1 FROM pg_policies
    WHERE tablename = 'jarvis_notification_effectiveness'
      AND policyname = 'allow_user'
  ) THEN
    CREATE POLICY "allow_user" ON jarvis_notification_effectiveness
      FOR ALL USING (auth.uid() IS NOT NULL);
  END IF;

  IF NOT EXISTS (
    SELECT 1 FROM pg_policies
    WHERE tablename = 'jarvis_meta_insights'
      AND policyname = 'allow_user'
  ) THEN
    CREATE POLICY "allow_user" ON jarvis_meta_insights
      FOR ALL USING (auth.uid() IS NOT NULL);
  END IF;

  IF NOT EXISTS (
    SELECT 1 FROM pg_policies
    WHERE tablename = 'jarvis_meta_learning_config'
      AND policyname = 'allow_user'
  ) THEN
    CREATE POLICY "allow_user" ON jarvis_meta_learning_config
      FOR ALL USING (auth.uid() IS NOT NULL);
  END IF;
END$$;

CREATE INDEX IF NOT EXISTS idx_jarvis_decision_outcomes_user_id ON jarvis_decision_outcomes(user_id);
CREATE INDEX IF NOT EXISTS idx_jarvis_preference_learning_user_id ON jarvis_preference_learning(user_id);
CREATE INDEX IF NOT EXISTS idx_jarvis_agent_performance_user_id ON jarvis_agent_performance(user_id);
CREATE INDEX IF NOT EXISTS idx_jarvis_forecast_accuracy_user_id ON jarvis_forecast_accuracy(user_id);
CREATE INDEX IF NOT EXISTS idx_jarvis_notification_effectiveness_user_id ON jarvis_notification_effectiveness(user_id);
CREATE INDEX IF NOT EXISTS idx_jarvis_meta_insights_user_id ON jarvis_meta_insights(user_id);
CREATE INDEX IF NOT EXISTS idx_jarvis_meta_learning_config_user_id ON jarvis_meta_learning_config(user_id);
