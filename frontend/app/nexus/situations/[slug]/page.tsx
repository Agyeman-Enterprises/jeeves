// src/app/nexus/situations/[slug]/page.tsx
import React from 'react';
import { getSituationRoomBySlug } from '@/lib/nexus/situations/service';
import { getWidgetComponent } from '@/lib/jarvis/widgets/registry';

interface PageProps {
  params: Promise<{ slug: string }>;
  searchParams: Promise<{ workspaceId?: string }>;
}

export default async function SituationRoomPage({ params, searchParams }: PageProps) {
  const { slug } = await params;
  const { workspaceId } = await searchParams;

  if (!workspaceId) {
    return (
      <div className="p-6">
        <p className="text-red-500">workspaceId is required</p>
      </div>
    );
  }

  const { room, widgets } = await getSituationRoomBySlug(workspaceId, slug);

  if (!room) {
    return (
      <div className="p-6">
        <p className="text-red-500">Situation room not found</p>
      </div>
    );
  }

  const refreshMs = (room.config as any)?.refreshMs ?? 5000;

  return (
    <div className="p-6">
      <div className="mb-4">
        <h1 className="text-2xl font-semibold">{room.name}</h1>
        {room.description && (
          <p className="text-gray-600 mt-1">{room.description}</p>
        )}
        <p className="text-xs text-gray-500 mt-1">
          Live mode: Auto-refreshing every {refreshMs / 1000}s
        </p>
      </div>
      <div className="grid grid-cols-12 gap-4">
        {widgets.map((w) => {
          const Component = getWidgetComponent(w.kind);
          if (!Component) {
            return (
              <div key={w.id} className="col-span-12 p-4 border rounded text-red-500">
                Unknown widget type: {w.kind}
              </div>
            );
          }

          const wPos = w.position.w || 4;
          const hPos = w.position.h || 3;

          return (
            <div
              key={w.id}
              className={`col-span-${wPos}`}
              style={{ gridRow: `span ${hPos}` }}
            >
              <Component config={w.config} workspaceId={workspaceId} />
            </div>
          );
        })}
        {widgets.length === 0 && (
          <div className="col-span-12 p-4 border rounded text-gray-500">
            No widgets configured for this room.
          </div>
        )}
      </div>
    </div>
  );
}
