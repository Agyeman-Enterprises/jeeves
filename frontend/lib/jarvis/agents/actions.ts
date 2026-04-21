import { AgentAction } from './types';

export async function executeAgentAction(
  action: AgentAction
): Promise<{ status: 'success' | 'failed'; detail?: any }> {
  try {
    switch (action.type) {
      case 'adjustRouting':
        // Stub — integrate with Ghexit routing engine later
        console.log('[AgentAction] adjustRouting', action);
        return { status: 'success' };

      case 'notify':
        // For now, print. Later pipe into IT-11 alert system or Ghexit deliverer.
        console.log('[AgentAction] notify', action);
        return { status: 'success' };

      case 'invokeInternalAPI': {
        const res = await fetch(action.url, {
          method: action.method,
          headers: { 'Content-Type': 'application/json' },
          body: action.body ? JSON.stringify(action.body) : undefined
        });
        return {
          status: res.ok ? 'success' : 'failed',
          detail: await res.json().catch(() => ({}))
        };
      }

      case 'runNexusTask':
        // Stub: produce GEM event or log.
        console.log('[AgentAction] runNexusTask', action);
        return { status: 'success' };

      default:
        console.warn('[AgentAction] Unknown action type:', action);
        return { status: 'failed', detail: 'Unknown action type' };
    }
  } catch (err: any) {
    console.error('[AgentAction] execution error:', err);
    return { status: 'failed', detail: err.message };
  }
}

