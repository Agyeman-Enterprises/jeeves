export interface BaseWidgetProps {
  workspaceId: string;
  config?: Record<string, unknown>;
}

export interface PredictionWidgetProps extends BaseWidgetProps {
  provider?: string;
  channel?: string;
}

