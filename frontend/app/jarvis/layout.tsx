'use client';

import React from 'react';
import dynamic from 'next/dynamic';

const VoicePanel = dynamic(
  () => import('@/components/voice/VoicePanel').then((m) => m.VoicePanel),
  { ssr: false }
);
const VoiceWidget = dynamic(
  () => import('@/components/voice/VoiceWidget').then((m) => m.VoiceWidget),
  { ssr: false }
);

export default function JarvisLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <>
      {children}
      <VoicePanel />
      <VoiceWidget />
    </>
  );
}
