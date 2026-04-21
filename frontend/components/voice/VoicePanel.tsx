'use client';

import React, { useState, useEffect, useRef } from 'react';
import { useVoiceInterface } from '@/hooks/useVoiceInterface';
import { Mic, MicOff, Volume2, Send, X, ChevronDown, ChevronUp, Zap } from 'lucide-react';

export function VoicePanel() {
  const [isExpanded, setIsExpanded] = useState(true);
  const [textInput, setTextInput] = useState('');
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const messagesContainerRef = useRef<HTMLDivElement>(null);
  
  const voice = useVoiceInterface({
    continuous: true,
    autoSpeak: false,
    maxMessages: 100,
    onUrgentMessage: (message) => {
      // Flash the panel for urgent messages
      const panel = document.getElementById('voice-panel');
      if (panel) {
        panel.classList.add('ring-2', 'ring-red-500', 'animate-pulse');
        setTimeout(() => {
          panel.classList.remove('ring-2', 'ring-red-500', 'animate-pulse');
        }, 2000);
      }
    }
  });

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    if (messagesEndRef.current && messagesContainerRef.current) {
      // Check if user is near bottom (within 100px)
      const container = messagesContainerRef.current;
      const isNearBottom = container.scrollHeight - container.scrollTop - container.clientHeight < 100;
      
      // Only auto-scroll if user is already near bottom
      if (isNearBottom) {
        messagesEndRef.current.scrollIntoView({ behavior: 'smooth' });
      }
    }
  }, [voice.messages]);

  const handleSendText = () => {
    if (textInput.trim()) {
      const isUrgent = textInput.toLowerCase().includes('urgent') || 
                      textInput.toLowerCase().includes('stop');
      voice.addTextMessage(textInput.trim(), isUrgent ? 'urgent' : 'normal');
      setTextInput('');
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendText();
    }
  };

  if (!voice.isSupported) {
    return null;
  }

  return (
    <div
      id="voice-panel"
      className="fixed bottom-4 right-4 w-96 bg-slate-900 border border-slate-800 rounded-lg shadow-2xl transition-all duration-300 z-40"
      style={{ maxWidth: '90vw' }} // Prevent panel from being wider than viewport
    >
      {/* Header */}
      <div className="flex items-center justify-between p-4 border-b border-slate-800">
        <div className="flex items-center space-x-3">
          <div className="relative">
            <div className={`w-10 h-10 rounded-full flex items-center justify-center transition-colors ${
              voice.isListening ? 'bg-green-500' : 'bg-slate-700'
            }`}>
              {voice.isListening ? <Mic className="w-5 h-5 text-white" /> : <MicOff className="w-5 h-5 text-slate-400" />}
            </div>
            {voice.voiceState === 'listening' && (
              <div className="absolute inset-0 animate-ping w-10 h-10 rounded-full bg-green-500 opacity-50" />
            )}
          </div>
          <div>
            <h3 className="text-sm font-semibold text-slate-100">Voice Assistant</h3>
            <p className="text-xs text-slate-400">
              {voice.isEnabled ? (
                voice.isListening ? 'Listening...' : 'Say "Hey Claude"'
              ) : 'Click to enable'}
            </p>
          </div>
        </div>
        <div className="flex items-center space-x-2">
          <button
            onClick={() => setIsExpanded(!isExpanded)}
            className="p-1 hover:bg-slate-800 rounded transition-colors"
          >
            {isExpanded ? <ChevronDown className="w-4 h-4" /> : <ChevronUp className="w-4 h-4" />}
          </button>
          <button
            onClick={() => voice.isEnabled ? voice.disable() : voice.enable()}
            className={`px-3 py-1 text-xs rounded transition-colors ${
              voice.isEnabled 
                ? 'bg-green-500 hover:bg-green-600 text-white' 
                : 'bg-slate-700 hover:bg-slate-600 text-slate-300'
            }`}
          >
            {voice.isEnabled ? 'ON' : 'OFF'}
          </button>
        </div>
      </div>

      {/* Expanded Content */}
      {isExpanded && (
        <>
          {/* Message Feed with fixed height and scroll */}
          <div 
            ref={messagesContainerRef}
            className="h-64 overflow-y-auto p-4 space-y-3 scroll-smooth voice-scroll"
          >
            {voice.messages.length === 0 ? (
              <div className="text-center py-8 text-slate-500 text-sm">
                <p>Start speaking or type a message</p>
                <p className="text-xs mt-2">Say "Hey Claude" to begin voice mode</p>
              </div>
            ) : (
              <>
                {voice.messages.map((message, index) => (
                  <div
                    key={message.id}
                    className={`flex ${message.type === 'assistant' ? 'justify-start' : 'justify-end'} animate-fade-in`}
                  >
                    <div
                      className={`max-w-[80%] px-3 py-2 rounded-lg ${
                        message.type === 'assistant'
                          ? 'bg-slate-800 text-slate-100'
                          : message.priority === 'urgent'
                          ? 'bg-red-900 text-red-100'
                          : 'bg-blue-900 text-blue-100'
                      }`}
                    >
                      <div className="flex items-start space-x-2">
                        {/* Fixed text size with voice-message-text class */}
                        <p className="flex-1 voice-message-text break-words whitespace-pre-wrap">{message.text}</p>
                        {message.priority === 'urgent' && (
                          <Zap className="w-4 h-4 text-yellow-400 flex-shrink-0 mt-0.5" />
                        )}
                      </div>
                      <div className="flex items-center justify-between mt-1">
                        <span className="text-xs opacity-60">
                          {new Date(message.timestamp).toLocaleTimeString()}
                        </span>
                        {message.status !== 'pending' && (
                          <span className="text-xs">
                            {message.status === 'acknowledged' ? '✓' : '✓✓'}
                          </span>
                        )}
                      </div>
                      {message.source === 'voice' && (
                        <Volume2 className="w-3 h-3 inline ml-1 opacity-50" />
                      )}
                    </div>
                  </div>
                ))}
                {/* Invisible element to scroll to */}
                <div ref={messagesEndRef} />
              </>
            )}
          </div>

          {/* Input Area */}
          <div className="p-4 border-t border-slate-800">
            <div className="flex space-x-2">
              <input
                type="text"
                value={textInput}
                onChange={(e) => setTextInput(e.target.value)}
                onKeyPress={handleKeyPress}
                placeholder="Type a message or addition..."
                className="flex-1 px-3 py-2 bg-slate-800 border border-slate-700 rounded-lg text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:border-blue-500"
              />
              <button
                onClick={handleSendText}
                disabled={!textInput.trim()}
                className="px-3 py-2 bg-blue-600 hover:bg-blue-700 disabled:bg-slate-700 disabled:opacity-50 text-white rounded-lg transition-colors"
              >
                <Send className="w-4 h-4" />
              </button>
            </div>
            <div className="mt-2 flex items-center space-x-4 text-xs text-slate-500">
              <span>• Say "urgent" for priority</span>
              <span>• Voice: {voice.pendingMessages.length} pending</span>
            </div>
          </div>
        </>
      )}
    </div>
  );
}