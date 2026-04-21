import React from 'react';
import { BaseWidgetProps } from './types';

// Existing widgets
import { EventFeedWidget } from '@/components/nexus/situations/widgets/EventFeedWidget';
import { ErrorListWidget } from '@/components/nexus/situations/widgets/ErrorListWidget';
import { MetricCardWidget } from '@/components/nexus/situations/widgets/MetricCardWidget';

// Prediction widgets
import { LatencyForecastWidget } from '@/components/widgets/predictions/LatencyForecastWidget';
import { CarrierStabilityWidget } from '@/components/widgets/predictions/CarrierStabilityWidget';
import { RoutingScoreWidget } from '@/components/widgets/predictions/RoutingScoreWidget';
import { SpendForecastWidget } from '@/components/widgets/predictions/SpendForecastWidget';
import { DeliveryCurveWidget } from '@/components/widgets/predictions/DeliveryCurveWidget';
import { OutageRadarWidget } from '@/components/widgets/predictions/OutageRadarWidget';

export type WidgetComponent = React.ComponentType<BaseWidgetProps & { config?: Record<string, unknown> }>;

export const widgetRegistry: Record<string, WidgetComponent> = {
  // Existing widgets
  event_feed: EventFeedWidget,
  error_list: ErrorListWidget,
  metric_card: MetricCardWidget,

  // Prediction widgets
  latencyForecast: LatencyForecastWidget,
  carrierStability: CarrierStabilityWidget,
  routingScore: RoutingScoreWidget,
  spendForecast: SpendForecastWidget,
  deliveryCurve: DeliveryCurveWidget,
  outageRadar: OutageRadarWidget,
};

export function getWidgetComponent(kind: string): WidgetComponent | undefined {
  return widgetRegistry[kind];
}

