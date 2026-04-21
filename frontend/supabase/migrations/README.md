# Supabase Migrations - Jarvis OS

This directory contains all database migrations for the Jarvis OS system. All migrations use proper table prefixes:
- `jarvis_` prefix for Jarvis-related tables
- `nexus_` prefix for financial/analytics tables
- Shared tables (`users`, `workspaces`, `files`) remain unprefixed

## Migration Order

Migrations should be run in this order:

0. **000_jarviscore_identity.sql** - Core identity tables (tenants, workspaces, workspace members)
   - `tenants` - Root organizational containers
   - `workspaces` - Business/project containers
   - `jarvis_workspace_members` - User-workspace relationships

1. **001_agent_architecture.sql** - Core agent and plan tables
   - `jarvis_agents`
   - `jarvis_agent_runs`
   - `jarvis_plans`
   - `jarvis_plan_steps`

2. **002_financial_schema.sql** - Nexus financial tables
   - `nexus_financial_entities`
   - `nexus_financial_transactions`
   - `nexus_financial_snapshots`
   - `nexus_tax_positions`

3. **003_agent_lifecycle.sql** - Agent lifecycle enhancements
   - Updates to `jarvis_agents` and `jarvis_agent_runs`
   - Adds status, heartbeat, retry, streak columns

4. **004_patient_journey.sql** - Patient journey automation
   - `jarvis_patient_state`
   - `jarvis_patient_pipeline`
   - `jarvis_clinical_events`
   - `jarvis_patient_journey_events`
   - `jarvis_chart_prep_packets`

5. **005_briefing_system.sql** - Briefing engine
   - `jarvis_signals`
   - `jarvis_briefings`
   - `jarvis_briefing_preferences`

6. **006_behavioral_models.sql** - Behavioral learning
   - `jarvis_behavior_vectors`
   - `jarvis_decision_logs`
   - `jarvis_communication_examples`
   - `jarvis_preference_rules`
   - `jarvis_behavior_patterns`
   - `jarvis_error_events`
   - `jarvis_root_causes`

7. **007_persona_engine.sql** - Persona system
   - `jarvis_personas`
   - `jarvis_identity_profile`
   - `jarvis_persona_rules`
   - `jarvis_emotional_context`

8. **008_memory_and_journal.sql** - Memory and journal
   - `jarvis_memory_chunks`
   - `jarvis_journal_entries`
   - `jarvis_system_events`

9. **009_action_layer.sql** - Action layer
   - `jarvis_action_policies`
   - `jarvis_action_logs`
   - `jarvis_action_approvals`

10. **010_governance_safety.sql** - Governance and safety
    - `jarvis_agent_permissions`
    - `jarvis_audit_log`
    - `jarvis_kill_switches`
    - Updates to `jarvis_action_policies`

... (migrations 011-033) ...

34. **034_modules_table.sql** - Module metadata table
    - `modules` - Module metadata for workspaces

## Running Migrations

### Using Supabase CLI

```bash
# Apply all migrations
supabase db push

# Or apply specific migration
supabase migration up
```

### Using Supabase Dashboard

1. Go to your Supabase project dashboard
2. Navigate to SQL Editor
3. Run each migration file in order (001 through 010)
4. Verify all tables are created

### Manual SQL Execution

Copy and paste each migration file's contents into the Supabase SQL Editor and execute in order.

## Table Summary

### Identity Tables
- `tenants` - Root organizational containers
- `workspaces` - Business/project containers within tenants
- `jarvis_workspace_members` - User-workspace membership and roles
- `modules` - Module metadata for workspaces

### Jarvis Tables (jarvis_*)
- `jarvis_agents` - Agent registry
- `jarvis_agent_runs` - Agent task queue
- `jarvis_plans` - Execution plans
- `jarvis_plan_steps` - Plan steps
- `jarvis_patient_state` - Patient state tracking
- `jarvis_patient_pipeline` - Patient pipeline history
- `jarvis_clinical_events` - Clinical event stream
- `jarvis_patient_journey_events` - Patient journey events
- `jarvis_chart_prep_packets` - Chart prep data
- `jarvis_signals` - Briefing signals
- `jarvis_briefings` - Generated briefings
- `jarvis_briefing_preferences` - Briefing preferences
- `jarvis_behavior_vectors` - Behavioral embeddings
- `jarvis_decision_logs` - Decision history
- `jarvis_communication_examples` - Communication examples
- `jarvis_preference_rules` - Preference rules
- `jarvis_behavior_patterns` - Behavior patterns
- `jarvis_error_events` - Error tracking
- `jarvis_root_causes` - Root cause analysis
- `jarvis_personas` - Persona profiles
- `jarvis_identity_profile` - Core identity
- `jarvis_persona_rules` - Persona selection rules
- `jarvis_emotional_context` - Emotional context
- `jarvis_memory_chunks` - Memory storage
- `jarvis_journal_entries` - Journal entries
- `jarvis_system_events` - System event stream
- `jarvis_action_policies` - Action policies
- `jarvis_action_logs` - Action execution logs
- `jarvis_action_approvals` - Pending approvals
- `jarvis_agent_permissions` - Agent permission matrix
- `jarvis_audit_log` - Comprehensive audit log
- `jarvis_kill_switches` - Kill switch controls

### Nexus Tables (nexus_*)
- `nexus_financial_entities` - Financial entities
- `nexus_financial_transactions` - Financial transactions
- `nexus_financial_snapshots` - Financial snapshots
- `nexus_tax_positions` - Tax positions

## Row Level Security (RLS)

All tables have RLS enabled with policies that ensure users can only access their own data:
- Policies use `auth.uid() = user_id` for user isolation
- Some tables have additional domain-specific policies

## Indexes

All migrations include appropriate indexes for:
- User-based queries
- Domain-based queries
- Time-based queries
- Foreign key lookups

## Notes

- All migrations use `create table if not exists` to be idempotent
- All migrations include RLS policies
- All migrations include appropriate indexes
- All timestamps use `timestamptz` for timezone-aware dates
- All UUIDs use `gen_random_uuid()` for generation

