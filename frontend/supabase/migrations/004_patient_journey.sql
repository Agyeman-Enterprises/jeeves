-- Migration 004: Patient Journey
CREATE TABLE IF NOT EXISTS jarvis_clinical_events (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL,
  workspace_id UUID,
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now()
);

COMMENT ON TABLE jarvis_clinical_events IS 'Clinical events from all sources';

CREATE TABLE IF NOT EXISTS jarvis_patient_state (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL,
  workspace_id UUID,
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now()
);

COMMENT ON TABLE jarvis_patient_state IS 'Current state of patients in journey';

CREATE TABLE IF NOT EXISTS jarvis_patient_pipeline (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL,
  workspace_id UUID,
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now()
);

COMMENT ON TABLE jarvis_patient_pipeline IS 'Patient journey pipeline stages';

CREATE TABLE IF NOT EXISTS jarvis_patient_journey_events (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL,
  workspace_id UUID,
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now()
);

COMMENT ON TABLE jarvis_patient_journey_events IS 'Detailed patient journey event log';

CREATE TABLE IF NOT EXISTS jarvis_chart_prep_packets (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL,
  workspace_id UUID,
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now()
);

COMMENT ON TABLE jarvis_chart_prep_packets IS 'Chart preparation packets for appointments';

ALTER TABLE jarvis_clinical_events ENABLE ROW LEVEL SECURITY;
ALTER TABLE jarvis_patient_state ENABLE ROW LEVEL SECURITY;
ALTER TABLE jarvis_patient_pipeline ENABLE ROW LEVEL SECURITY;
ALTER TABLE jarvis_patient_journey_events ENABLE ROW LEVEL SECURITY;
ALTER TABLE jarvis_chart_prep_packets ENABLE ROW LEVEL SECURITY;

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_policies
    WHERE tablename = 'jarvis_clinical_events'
      AND policyname = 'allow_user'
  ) THEN
    CREATE POLICY "allow_user" ON jarvis_clinical_events
      FOR ALL USING (auth.uid() IS NOT NULL);
  END IF;

  IF NOT EXISTS (
    SELECT 1 FROM pg_policies
    WHERE tablename = 'jarvis_patient_state'
      AND policyname = 'allow_user'
  ) THEN
    CREATE POLICY "allow_user" ON jarvis_patient_state
      FOR ALL USING (auth.uid() IS NOT NULL);
  END IF;

  IF NOT EXISTS (
    SELECT 1 FROM pg_policies
    WHERE tablename = 'jarvis_patient_pipeline'
      AND policyname = 'allow_user'
  ) THEN
    CREATE POLICY "allow_user" ON jarvis_patient_pipeline
      FOR ALL USING (auth.uid() IS NOT NULL);
  END IF;

  IF NOT EXISTS (
    SELECT 1 FROM pg_policies
    WHERE tablename = 'jarvis_patient_journey_events'
      AND policyname = 'allow_user'
  ) THEN
    CREATE POLICY "allow_user" ON jarvis_patient_journey_events
      FOR ALL USING (auth.uid() IS NOT NULL);
  END IF;

  IF NOT EXISTS (
    SELECT 1 FROM pg_policies
    WHERE tablename = 'jarvis_chart_prep_packets'
      AND policyname = 'allow_user'
  ) THEN
    CREATE POLICY "allow_user" ON jarvis_chart_prep_packets
      FOR ALL USING (auth.uid() IS NOT NULL);
  END IF;
END$$;

CREATE INDEX IF NOT EXISTS idx_jarvis_clinical_events_user_id ON jarvis_clinical_events(user_id);
CREATE INDEX IF NOT EXISTS idx_jarvis_patient_state_user_id ON jarvis_patient_state(user_id);
CREATE INDEX IF NOT EXISTS idx_jarvis_patient_pipeline_user_id ON jarvis_patient_pipeline(user_id);
CREATE INDEX IF NOT EXISTS idx_jarvis_patient_journey_events_user_id ON jarvis_patient_journey_events(user_id);
CREATE INDEX IF NOT EXISTS idx_jarvis_chart_prep_packets_user_id ON jarvis_chart_prep_packets(user_id);
