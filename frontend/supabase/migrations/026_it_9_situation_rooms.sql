-- IT-9: Situation Rooms v0
-- nexus_situation_rooms & nexus_situation_widgets

CREATE TABLE IF NOT EXISTS public.nexus_situation_rooms (
  id             uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  workspace_id   uuid NOT NULL,
  user_id        uuid NOT NULL, -- creator / owner
  slug           text NOT NULL,
  name           text NOT NULL,
  description    text,
  is_default     boolean NOT NULL DEFAULT false,
  config         jsonb NOT NULL DEFAULT '{}'::jsonb, -- room-level config (filters, refresh, etc.)
  created_at     timestamptz NOT NULL DEFAULT now(),
  updated_at     timestamptz NOT NULL DEFAULT now()
);

COMMENT ON TABLE public.nexus_situation_rooms IS
  'Operational Situation Rooms built on top of Jarvis GEM events.';

CREATE UNIQUE INDEX IF NOT EXISTS idx_nexus_situation_rooms_workspace_slug
  ON public.nexus_situation_rooms (workspace_id, slug);

ALTER TABLE public.nexus_situation_rooms ENABLE ROW LEVEL SECURITY;

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_policies
    WHERE schemaname = 'public'
      AND tablename = 'nexus_situation_rooms'
      AND policyname = 'nexus_situation_rooms_allow_workspace_members'
  ) THEN
    CREATE POLICY "nexus_situation_rooms_allow_workspace_members"
      ON public.nexus_situation_rooms
      FOR SELECT USING (
        auth.uid() IS NOT NULL AND (
          user_id = auth.uid() OR
          workspace_id IN (
            SELECT workspace_id FROM public.workspaces WHERE owner_id = auth.uid()
          )
        )
      );
  END IF;
END$$;

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_policies
    WHERE schemaname = 'public'
      AND tablename = 'nexus_situation_rooms'
      AND policyname = 'nexus_situation_rooms_allow_workspace_members_mod'
  ) THEN
    CREATE POLICY "nexus_situation_rooms_allow_workspace_members_mod"
      ON public.nexus_situation_rooms
      FOR INSERT WITH CHECK (
        auth.uid() IS NOT NULL AND (
          user_id = auth.uid() OR
          workspace_id IN (
            SELECT workspace_id FROM public.workspaces WHERE owner_id = auth.uid()
          )
        )
      )
      FOR UPDATE USING (
        auth.uid() IS NOT NULL AND (
          user_id = auth.uid() OR
          workspace_id IN (
            SELECT workspace_id FROM public.workspaces WHERE owner_id = auth.uid()
          )
        )
      )
      FOR DELETE USING (
        auth.uid() IS NOT NULL AND (
          user_id = auth.uid() OR
          workspace_id IN (
            SELECT workspace_id FROM public.workspaces WHERE owner_id = auth.uid()
          )
        )
      );
  END IF;
END$$;

-- Widgets

CREATE TABLE IF NOT EXISTS public.nexus_situation_widgets (
  id             uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  room_id        uuid NOT NULL REFERENCES public.nexus_situation_rooms(id) ON DELETE CASCADE,
  workspace_id   uuid NOT NULL,
  user_id        uuid NOT NULL,
  kind           text NOT NULL,   -- e.g., 'event_feed', 'metric_card', 'error_list'
  title          text NOT NULL,
  position       jsonb NOT NULL DEFAULT '{}'::jsonb, -- { x, y, w, h }
  config         jsonb NOT NULL DEFAULT '{}'::jsonb, -- widget-specific config (event filters, etc.)
  created_at     timestamptz NOT NULL DEFAULT now(),
  updated_at     timestamptz NOT NULL DEFAULT now()
);

COMMENT ON TABLE public.nexus_situation_widgets IS
  'Widgets/components that make up a Situation Room dashboard.';

CREATE INDEX IF NOT EXISTS idx_nexus_situation_widgets_room
  ON public.nexus_situation_widgets (room_id);

ALTER TABLE public.nexus_situation_widgets ENABLE ROW LEVEL SECURITY;

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_policies
    WHERE schemaname = 'public'
      AND tablename = 'nexus_situation_widgets'
      AND policyname = 'nexus_situation_widgets_allow_workspace_members'
  ) THEN
    CREATE POLICY "nexus_situation_widgets_allow_workspace_members"
      ON public.nexus_situation_widgets
      FOR SELECT USING (
        auth.uid() IS NOT NULL AND (
          user_id = auth.uid() OR
          workspace_id IN (
            SELECT workspace_id FROM public.workspaces WHERE owner_id = auth.uid()
          )
        )
      );
  END IF;
END$$;

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_policies
    WHERE schemaname = 'public'
      AND tablename = 'nexus_situation_widgets'
      AND policyname = 'nexus_situation_widgets_allow_workspace_members_mod'
  ) THEN
    CREATE POLICY "nexus_situation_widgets_allow_workspace_members_mod"
      ON public.nexus_situation_widgets
      FOR INSERT WITH CHECK (
        auth.uid() IS NOT NULL AND (
          user_id = auth.uid() OR
          workspace_id IN (
            SELECT workspace_id FROM public.workspaces WHERE owner_id = auth.uid()
          )
        )
      )
      FOR UPDATE USING (
        auth.uid() IS NOT NULL AND (
          user_id = auth.uid() OR
          workspace_id IN (
            SELECT workspace_id FROM public.workspaces WHERE owner_id = auth.uid()
          )
        )
      )
      FOR DELETE USING (
        auth.uid() IS NOT NULL AND (
          user_id = auth.uid() OR
          workspace_id IN (
            SELECT workspace_id FROM public.workspaces WHERE owner_id = auth.uid()
          )
        )
      );
  END IF;
END$$;

