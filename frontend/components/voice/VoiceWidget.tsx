'use client';

import React, { useState, useEffect, useRef } from 'react';
import { useVoiceInterface } from '@/hooks/useVoiceInterface';
import { Mic, MicOff, X, Minimize2, Maximize2, MessageSquare } from 'lucide-react';

interface Position {
  x: number;
  y: number;
}

export function VoiceWidget() {
  const [isMinimized, setIsMinimized] = useState(false);
  const [isDragging, setIsDragging] = useState(false);
  const [position, setPosition] = useState<Position>({ x: 20, y: 20 });
  const [dragStart, setDragStart] = useState<Position>({ x: 0, y: 0 });
  const [showMessages, setShowMessages] = useState(false);
  const widgetRef = useRef<HTMLDivElement>(null);

  const voice = useVoiceInterface({
    continuous: true,
    autoSpeak: false,
    maxMessages: 20,
    wakeWords: ['Claude', 'Hey Claude', 'Computer'],
    onMessage: () => {
      // Flash widget on new message
      if (widgetRef.current) {
        widgetRef.current.classList.add('animate-bounce');
        setTimeout(() => {
          widgetRef.current?.classList.remove('animate-bounce');
        }, 1000);
      }
    },
    onUrgentMessage: () => {
      // Auto-expand on urgent message
      setIsMinimized(false);
      setShowMessages(true);
    }
  });

  // Handle drag
  useEffect(() => {
    const handleMouseMove = (e: MouseEvent) => {
      if (isDragging) {
        setPosition({
          x: e.clientX - dragStart.x,
          y: e.clientY - dragStart.y
        });
      }
    };

    const handleMouseUp = () => {
      setIsDragging(false);
    };

    if (isDragging) {
      document.addEventListener('mousemove', handleMouseMove);
      document.addEventListener('mouseup', handleMouseUp);
    }

    return () => {
      document.removeEventListener('mousemove', handleMouseMove);
      document.removeEventListener('mouseup', handleMouseUp);
    };
  }, [isDragging, dragStart]);

  const handleMouseDown = (e: React.MouseEvent) => {
    const rect = widgetRef.current?.getBoundingClientRect();
    if (rect) {
      setIsDragging(true);
      setDragStart({
        x: e.clientX - rect.left,
        y: e.clientY - rect.top
      });
    }
  };

  if (!voice.isSupported) {
    return null;
  }

  // Minimized view - just the mic button
  if (isMinimized) {
    return (
      <div
        ref={widgetRef}
        className="fixed z-40 group"
        style={{ left: `${position.x}px`, top: `${position.y}px` }}
      >
        <button
          onClick={() => setIsMinimized(false)}
          onMouseDown={handleMouseDown}
          className={`w-14 h-14 rounded-full shadow-lg transition-all duration-200 ${
            voice.isListening 
              ? 'bg-green-500 hover:bg-green-600' 
              : 'bg-slate-800 hover:bg-slate-700'
          } ${isDragging ? 'cursor-move' : 'cursor-pointer'}`}
        >
          <div className="relative w-full h-full flex items-center justify-center">
            {voice.isListening ? (
              <>
                <Mic className="w-6 h-6 text-white" />
                <div className="absolute inset-0 rounded-full animate-ping bg-green-400 opacity-30" />
              </>
            ) : (
              <MicOff className="w-6 h-6 text-slate-400" />
            )}
          </div>
        </button>
        {voice.pendingMessages.length > 0 && (
          <div className="absolute -top-1 -right-1 w-5 h-5 bg-red-500 text-white text-xs rounded-full flex items-center justify-center">
            {voice.pendingMessages.length}
          </div>
        )}
      </div>
    );
  }

  // Expanded view
  return (
    <div
      ref={widgetRef}
      className="fixed z-40 bg-slate-900 border border-slate-700 rounded-lg shadow-2xl"
      style={{ 
        left: `${position.x}px`, 
        top: `${position.y}px`,
        width: '320px'
      }}
    >
      {/* Header */}
      <div
        className="flex items-center justify-between p-3 border-b border-slate-800 cursor-move"
        onMouseDown={handleMouseDown}
      >
        <div className="flex items-center space-x-2">
          <div className={`w-8 h-8 rounded-full flex items-center justify-center ${
            voice.isListening ? 'bg-green-500' : 'bg-slate-700'
          }`}>
            {voice.isListening ? <Mic className="w-4 h-4 text-white" /> : <MicOff className="w-4 h-4 text-slate-400" />}
          </div>
          <span className="text-sm font-medium text-slate-100">
            {voice.isEnabled ? 'Voice Active' : 'Voice Inactive'}
          </span>
        </div>
        <div className="flex items-center space-x-1">
          <button
            onClick={() => setShowMessages(!showMessages)}
            className="p-1.5 hover:bg-slate-800 rounded transition-colors"
          >
            <MessageSquare className="w-4 h-4 text-slate-400" />
          </button>
          <button
            onClick={() => setIsMinimized(true)}
            className="p-1.5 hover:bg-slate-800 rounded transition-colors"
          >
            <Minimize2 className="w-4 h-4 text-slate-400" />
          </button>
          <button
            onClick={() => voice.isEnabled ? voice.disable() : voice.enable()}
            className="p-1.5 hover:bg-slate-800 rounded transition-colors"
          >
            <X className="w-4 h-4 text-slate-400" />
          </button>
        </div>
      </div>

      {/* Status */}
      <div className="px-3 py-2 border-b border-slate-800">
        <div className="flex items-center justify-between">
          <span className="text-xs text-slate-500">
            {voice.voiceState === 'listening' ? 'Listening...' : 
             voice.voiceState === 'processing' ? 'Processing...' :
             voice.voiceState === 'speaking' ? 'Speaking...' :
             'Say "Hey Claude"'}
          </span>
          {voice.pendingMessages.length > 0 && (
            <span className="text-xs text-amber-400">
              {voice.pendingMessages.length} pending
            </span>
          )}
        </div>
      </div>

      {/* Recent Messages (collapsible) */}
      {showMessages && (
        <div className="max-h-48 overflow-y-auto p-3 space-y-2 border-b border-slate-800">
          {voice.messages.slice(-5).map((message) => (
            <div
              key={message.id}
              className={`text-xs p-2 rounded ${
                message.type === 'assistant' 
                  ? 'bg-slate-800 text-slate-300'
                  : message.priority === 'urgent'
                  ? 'bg-red-900/50 text-red-200'
                  : 'bg-blue-900/50 text-blue-200'
              }`}
            >
              <p className="break-words">{message.text}</p>
              <div className="flex items-center justify-between mt-1">
                <span className="text-[10px] opacity-60">
                  {new Date(message.timestamp).toLocaleTimeString()}
                </span>
                {message.status !== 'pending' && (
                  <span className="text-[10px]">
                    {message.status === 'acknowledged' ? '✓' : '✓✓'}
                  </span>
                )}
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Quick Actions */}
      <div className="p-3 flex justify-center space-x-2">
        <button
          onClick={() => voice.isEnabled ? voice.disable() : voice.enable()}
          className={`px-4 py-2 text-xs rounded transition-colors ${
            voice.isEnabled 
              ? 'bg-green-600 hover:bg-green-700 text-white' 
              : 'bg-slate-700 hover:bg-slate-600 text-slate-300'
          }`}
        >
          {voice.isEnabled ? 'Disable Voice' : 'Enable Voice'}
        </button>
        <button
          onClick={() => voice.clearMessages()}
          className="px-4 py-2 text-xs bg-slate-700 hover:bg-slate-600 text-slate-300 rounded transition-colors"
        >
          Clear
        </button>
      </div>
    </div>
  );
}