// AdAI Email Notifications via Resend
// Integrates with Ghexit to send critical AdAI alerts

import { Resend } from 'resend';

// ============================================================================
// Types
// ============================================================================

export interface AdAIEmailData {
  to: string;
  subject: string;
  template: string;
  data: {
    workspaceId: string;
    eventType: string;
    timestamp: string;
    [key: string]: unknown;
  };
}

export interface ApprovalRequiredData {
  workspaceId: string;
  decisionId: string;
  entityType: string;
  entityId: string;
  entityName?: string;
  decisionType: string;
  reason: string;
  suggestedAction: Record<string, unknown>;
  approveUrl?: string;
  rejectUrl?: string;
}

export interface SpendAlertData {
  workspaceId: string;
  workspaceName?: string;
  currentSpend: number;
  threshold: number;
  percentOfThreshold: number;
  priorityCompanies: string[];
}

export interface TokenAlertData {
  workspaceId: string;
  platform: string;
  accountId: string;
  accountName?: string;
  expiresAt: string;
  daysUntilExpiry: number;
  renewUrl?: string;
}

export interface AnomalyAlertData {
  workspaceId: string;
  anomalyType: string;
  metric: string;
  currentValue: number;
  expectedValue: number;
  deviation: number;
  severity: 'info' | 'warning' | 'critical';
}

export interface RunFailedData {
  workspaceId: string;
  runId: string;
  runType: string;
  error: string;
  failedAt: string;
}

// ============================================================================
// Email Service
// ============================================================================

class AdAIEmailService {
  private resend: Resend | null = null;
  private fromEmail: string = 'AdAI <adai@notifications.agyeman.enterprises>';

  constructor() {
    const apiKey = process.env.RESEND_API_KEY;
    if (apiKey) {
      this.resend = new Resend(apiKey);
    }
  }

  private get isConfigured(): boolean {
    return this.resend !== null;
  }

  /**
   * Send approval required notification
   */
  async sendApprovalRequired(to: string, data: ApprovalRequiredData): Promise<boolean> {
    const subject = `[AdAI] Approval Required - ${data.decisionType} ${data.entityType}`;

    const html = `
      <div style="font-family: sans-serif; max-width: 600px; margin: 0 auto;">
        <h2 style="color: #f59e0b;">⚠️ Approval Required</h2>

        <p>AdAI has proposed a change that requires your approval before execution.</p>

        <div style="background: #f3f4f6; padding: 16px; border-radius: 8px; margin: 16px 0;">
          <h3 style="margin-top: 0;">Proposed Change</h3>
          <table style="width: 100%; border-collapse: collapse;">
            <tr>
              <td style="padding: 8px 0; color: #6b7280;">Type:</td>
              <td style="padding: 8px 0; font-weight: bold;">${data.decisionType.toUpperCase()}</td>
            </tr>
            <tr>
              <td style="padding: 8px 0; color: #6b7280;">Entity:</td>
              <td style="padding: 8px 0;">${data.entityType} - ${data.entityName || data.entityId}</td>
            </tr>
            <tr>
              <td style="padding: 8px 0; color: #6b7280;">Reason:</td>
              <td style="padding: 8px 0;">${data.reason}</td>
            </tr>
          </table>
        </div>

        <div style="margin: 24px 0;">
          ${data.approveUrl ? `<a href="${data.approveUrl}" style="background: #10b981; color: white; padding: 12px 24px; border-radius: 6px; text-decoration: none; margin-right: 12px;">✓ Approve</a>` : ''}
          ${data.rejectUrl ? `<a href="${data.rejectUrl}" style="background: #ef4444; color: white; padding: 12px 24px; border-radius: 6px; text-decoration: none;">✗ Reject</a>` : ''}
        </div>

        <p style="color: #6b7280; font-size: 12px;">
          Decision ID: ${data.decisionId}<br>
          Workspace: ${data.workspaceId}
        </p>
      </div>
    `;

    return this.send(to, subject, html);
  }

  /**
   * Send monthly spend alert
   */
  async sendSpendAlert(to: string, data: SpendAlertData): Promise<boolean> {
    const subject = `[AdAI] Monthly Spend Alert - $${data.currentSpend.toFixed(2)}`;
    const severity = data.percentOfThreshold >= 100 ? 'critical' : 'warning';
    const color = severity === 'critical' ? '#ef4444' : '#f59e0b';

    const html = `
      <div style="font-family: sans-serif; max-width: 600px; margin: 0 auto;">
        <h2 style="color: ${color};">💰 Monthly Spend Alert</h2>

        <p>Your ad spend has ${data.percentOfThreshold >= 100 ? 'exceeded' : 'reached'} the monthly threshold.</p>

        <div style="background: #f3f4f6; padding: 16px; border-radius: 8px; margin: 16px 0;">
          <h3 style="margin-top: 0;">Spend Summary</h3>
          <table style="width: 100%; border-collapse: collapse;">
            <tr>
              <td style="padding: 8px 0; color: #6b7280;">Current Spend:</td>
              <td style="padding: 8px 0; font-weight: bold; font-size: 24px; color: ${color};">$${data.currentSpend.toFixed(2)}</td>
            </tr>
            <tr>
              <td style="padding: 8px 0; color: #6b7280;">Alert Threshold:</td>
              <td style="padding: 8px 0;">$${data.threshold.toFixed(2)}</td>
            </tr>
            <tr>
              <td style="padding: 8px 0; color: #6b7280;">% of Threshold:</td>
              <td style="padding: 8px 0;">${data.percentOfThreshold.toFixed(0)}%</td>
            </tr>
          </table>
        </div>

        <div style="background: #fef3c7; padding: 16px; border-radius: 8px; margin: 16px 0;">
          <h4 style="margin-top: 0;">📋 Priority Companies</h4>
          <p>Consider prioritizing spend on these companies:</p>
          <ul>
            ${data.priorityCompanies.map(c => `<li>${c}</li>`).join('')}
          </ul>
        </div>

        <p style="color: #6b7280; font-size: 12px;">
          Workspace: ${data.workspaceId}
        </p>
      </div>
    `;

    return this.send(to, subject, html);
  }

  /**
   * Send token expiry alert
   */
  async sendTokenAlert(to: string, data: TokenAlertData, isExpired: boolean = false): Promise<boolean> {
    const subject = isExpired
      ? `[AdAI] Critical - ${data.platform} Token Expired`
      : `[AdAI] Action Required - ${data.platform} Token Expiring`;

    const color = isExpired ? '#ef4444' : '#f59e0b';
    const icon = isExpired ? '🔴' : '⚠️';

    const html = `
      <div style="font-family: sans-serif; max-width: 600px; margin: 0 auto;">
        <h2 style="color: ${color};">${icon} ${isExpired ? 'Token Expired' : 'Token Expiring Soon'}</h2>

        <p>${isExpired
          ? `Your ${data.platform} ad account token has expired. Ad syncing is paused until you reconnect.`
          : `Your ${data.platform} ad account token will expire in ${data.daysUntilExpiry} days.`
        }</p>

        <div style="background: #f3f4f6; padding: 16px; border-radius: 8px; margin: 16px 0;">
          <h3 style="margin-top: 0;">Account Details</h3>
          <table style="width: 100%; border-collapse: collapse;">
            <tr>
              <td style="padding: 8px 0; color: #6b7280;">Platform:</td>
              <td style="padding: 8px 0; font-weight: bold;">${data.platform}</td>
            </tr>
            <tr>
              <td style="padding: 8px 0; color: #6b7280;">Account:</td>
              <td style="padding: 8px 0;">${data.accountName || data.accountId}</td>
            </tr>
            <tr>
              <td style="padding: 8px 0; color: #6b7280;">${isExpired ? 'Expired At' : 'Expires At'}:</td>
              <td style="padding: 8px 0;">${new Date(data.expiresAt).toLocaleDateString()}</td>
            </tr>
          </table>
        </div>

        ${data.renewUrl ? `
          <div style="margin: 24px 0;">
            <a href="${data.renewUrl}" style="background: #3b82f6; color: white; padding: 12px 24px; border-radius: 6px; text-decoration: none;">
              🔗 Reconnect Account
            </a>
          </div>
        ` : ''}

        <p style="color: #6b7280; font-size: 12px;">
          Account ID: ${data.accountId}<br>
          Workspace: ${data.workspaceId}
        </p>
      </div>
    `;

    return this.send(to, subject, html);
  }

  /**
   * Send anomaly alert
   */
  async sendAnomalyAlert(to: string, data: AnomalyAlertData): Promise<boolean> {
    const subject = `[AdAI] ${data.severity === 'critical' ? 'Critical' : 'Alert'} - ${data.anomalyType}`;

    const colors = {
      info: '#3b82f6',
      warning: '#f59e0b',
      critical: '#ef4444',
    };
    const icons = {
      info: 'ℹ️',
      warning: '⚠️',
      critical: '🚨',
    };

    const html = `
      <div style="font-family: sans-serif; max-width: 600px; margin: 0 auto;">
        <h2 style="color: ${colors[data.severity]};">${icons[data.severity]} Anomaly Detected</h2>

        <p>AdAI has detected an unusual pattern in your ad metrics.</p>

        <div style="background: #f3f4f6; padding: 16px; border-radius: 8px; margin: 16px 0;">
          <h3 style="margin-top: 0;">${data.anomalyType}</h3>
          <table style="width: 100%; border-collapse: collapse;">
            <tr>
              <td style="padding: 8px 0; color: #6b7280;">Metric:</td>
              <td style="padding: 8px 0; font-weight: bold;">${data.metric}</td>
            </tr>
            <tr>
              <td style="padding: 8px 0; color: #6b7280;">Current Value:</td>
              <td style="padding: 8px 0; color: ${colors[data.severity]}; font-weight: bold;">${data.currentValue}</td>
            </tr>
            <tr>
              <td style="padding: 8px 0; color: #6b7280;">Expected Value:</td>
              <td style="padding: 8px 0;">${data.expectedValue}</td>
            </tr>
            <tr>
              <td style="padding: 8px 0; color: #6b7280;">Deviation:</td>
              <td style="padding: 8px 0;">${data.deviation > 0 ? '+' : ''}${(data.deviation * 100).toFixed(0)}%</td>
            </tr>
          </table>
        </div>

        <p style="color: #6b7280; font-size: 12px;">
          Workspace: ${data.workspaceId}
        </p>
      </div>
    `;

    return this.send(to, subject, html);
  }

  /**
   * Send run failed alert
   */
  async sendRunFailedAlert(to: string, data: RunFailedData): Promise<boolean> {
    const subject = `[AdAI] Error - ${data.runType} Run Failed`;

    const html = `
      <div style="font-family: sans-serif; max-width: 600px; margin: 0 auto;">
        <h2 style="color: #ef4444;">❌ Optimization Run Failed</h2>

        <p>An AdAI optimization run encountered an error and could not complete.</p>

        <div style="background: #fef2f2; padding: 16px; border-radius: 8px; margin: 16px 0; border-left: 4px solid #ef4444;">
          <h3 style="margin-top: 0;">Error Details</h3>
          <p style="font-family: monospace; color: #b91c1c;">${data.error}</p>
        </div>

        <div style="background: #f3f4f6; padding: 16px; border-radius: 8px; margin: 16px 0;">
          <table style="width: 100%; border-collapse: collapse;">
            <tr>
              <td style="padding: 8px 0; color: #6b7280;">Run Type:</td>
              <td style="padding: 8px 0;">${data.runType}</td>
            </tr>
            <tr>
              <td style="padding: 8px 0; color: #6b7280;">Failed At:</td>
              <td style="padding: 8px 0;">${new Date(data.failedAt).toLocaleString()}</td>
            </tr>
            <tr>
              <td style="padding: 8px 0; color: #6b7280;">Run ID:</td>
              <td style="padding: 8px 0; font-family: monospace; font-size: 12px;">${data.runId}</td>
            </tr>
          </table>
        </div>

        <p style="color: #6b7280; font-size: 12px;">
          Workspace: ${data.workspaceId}
        </p>
      </div>
    `;

    return this.send(to, subject, html);
  }

  /**
   * Generic email send method
   */
  private async send(to: string, subject: string, html: string): Promise<boolean> {
    if (!this.isConfigured) {
      console.warn('[AdAI Email] Resend not configured, email not sent');
      console.log('[AdAI Email] Would send:', { to, subject });
      return false;
    }

    try {
      const { error } = await this.resend!.emails.send({
        from: this.fromEmail,
        to,
        subject,
        html,
      });

      if (error) {
        console.error('[AdAI Email] Send failed:', error);
        return false;
      }

      console.log('[AdAI Email] Sent successfully:', { to, subject });
      return true;
    } catch (err) {
      console.error('[AdAI Email] Error:', err);
      return false;
    }
  }
}

// Export singleton instance
export const adaiEmail = new AdAIEmailService();

// ============================================================================
// Handler Integration
// ============================================================================

/**
 * Process AdAI email notification from GEM event
 */
export async function processAdAIEmailNotification(
  eventType: string,
  payload: Record<string, unknown>
): Promise<boolean> {
  const to = (payload.notifyEmail as string) || process.env.ADAI_DEFAULT_NOTIFY_EMAIL || 'admin@agyeman.enterprises';

  switch (eventType) {
    case 'adai.approval.required':
      return adaiEmail.sendApprovalRequired(to, payload as unknown as ApprovalRequiredData);

    case 'adai.monthly_spend.alert':
      return adaiEmail.sendSpendAlert(to, payload as unknown as SpendAlertData);

    case 'adai.token.expiring':
      return adaiEmail.sendTokenAlert(to, payload as unknown as TokenAlertData, false);

    case 'adai.token.expired':
      return adaiEmail.sendTokenAlert(to, payload as unknown as TokenAlertData, true);

    case 'adai.anomaly.detected':
      return adaiEmail.sendAnomalyAlert(to, payload as unknown as AnomalyAlertData);

    case 'adai.run.failed':
      return adaiEmail.sendRunFailedAlert(to, payload as unknown as RunFailedData);

    default:
      console.warn('[AdAI Email] Unknown event type:', eventType);
      return false;
  }
}
