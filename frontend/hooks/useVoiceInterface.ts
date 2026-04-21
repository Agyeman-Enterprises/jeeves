// Voice Interface Hook - Manages voice interactions and message queue
import { useState, useEffect, useCallback, useRef } from 'react';
import { VoiceService, VoiceMessage, VoiceState } from '@/lib/voice/VoiceService';
import { MessageQueue, QueuedMessage } from '@/lib/voice/MessageQueue';

export interface UseVoiceInterfaceConfig {
  wakeWords?: string[];
  continuous?: boolean;
  maxMessages?: number;
  autoSpeak?: boolean;
  onMessage?: (message: QueuedMessage) => void;
  onUrgentMessage?: (message: QueuedMessage) => void;
}

export interface VoiceInterfaceState {
  isListening: boolean;
  voiceState: VoiceState;
  messages: QueuedMessage[];
  pendingMessages: QueuedMessage[];
  isEnabled: boolean;
}

export function useVoiceInterface(config: UseVoiceInterfaceConfig = {}) {
  const [state, setState] = useState<VoiceInterfaceState>({
    isListening: false,
    voiceState: 'idle',
    messages: [],
    pendingMessages: [],
    isEnabled: false
  });

  const voiceServiceRef = useRef<VoiceService | null>(null);
  const messageQueueRef = useRef<MessageQueue | null>(null);
  const apiEndpointRef = useRef<string>('/api/proxy/query');

  // Initialize services
  useEffect(() => {
    if (!state.isEnabled) return;

    // Create message queue
    messageQueueRef.current = new MessageQueue({
      maxMessages: config.maxMessages || 50,
      onNewMessage: (message) => {
        setState(prev => ({
          ...prev,
          messages: [...prev.messages, message],
          pendingMessages: [...prev.pendingMessages, message]
        }));
        
        // Process message with JARVIS API
        processMessageWithJARVIS(message);
        
        if (config.onMessage) {
          config.onMessage(message);
        }
      },
      onMessageUpdate: (message) => {
        setState(prev => ({
          ...prev,
          messages: prev.messages.map(m => 
            m.id === message.id ? message : m
          ),
          pendingMessages: prev.pendingMessages.filter(m => 
            m.id !== message.id || m.status === 'pending'
          )
        }));
      },
      onUrgentMessage: config.onUrgentMessage
    });

    // Create voice service
    voiceServiceRef.current = new VoiceService({
      wakeWords: config.wakeWords || ['Claude', 'Hey Claude', 'OK Claude', 'Jarvis', 'Hey Jarvis'],
      continuous: config.continuous !== false,
      interimResults: true,
      language: 'en-US',
      onMessage: (voiceMessage) => {
        if (messageQueueRef.current) {
          messageQueueRef.current.addMessage({
            text: voiceMessage.text,
            priority: voiceMessage.priority
          }, 'voice');
        }
      },
      onStateChange: (voiceState) => {
        setState(prev => ({ 
          ...prev, 
          voiceState,
          isListening: voiceState === 'listening'
        }));
      }
    });

    // Start listening if continuous mode
    if (config.continuous !== false) {
      voiceServiceRef.current.start();
    }

    return () => {
      if (voiceServiceRef.current) {
        voiceServiceRef.current.destroy();
      }
    };
  }, [state.isEnabled, config.continuous]);

  // Process message with JARVIS API
  const processMessageWithJARVIS = async (message: QueuedMessage) => {
    try {
      // Acknowledge message
      messageQueueRef.current?.acknowledgeMessage(message.id, '✓ Processing');

      // Send to JARVIS query endpoint
      const response = await fetch(apiEndpointRef.current, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          query: message.text,
          context: {
            source: 'voice',
            priority: message.priority,
            timestamp: message.timestamp
          }
        })
      });

      if (response.ok) {
        const data = await response.json();
        
        // Mark as processed
        messageQueueRef.current?.processMessage(message.id);
        
        // Extract response text from JARVIS format
        const responseText = data.content || data.messages?.[1]?.text || 'I processed your request.';
        
        // Add assistant response to queue
        if (responseText && messageQueueRef.current) {
          const assistantMessage = messageQueueRef.current.addMessage({
            text: responseText,
            type: 'assistant',
            priority: 'normal'
          }, 'text');

          // Speak response if enabled
          if (config.autoSpeak && voiceServiceRef.current) {
            // Use JARVIS TTS endpoint
            try {
              const ttsResponse = await fetch('/api/proxy/api/voice/speak', {
                method: 'POST',
                headers: {
                  'Content-Type': 'application/json',
                },
                body: JSON.stringify({ text: responseText })
              });

              if (ttsResponse.ok) {
                const audioBlob = await ttsResponse.blob();
                const audioUrl = URL.createObjectURL(audioBlob);
                const audio = new Audio(audioUrl);
                audio.play();
                
                // Cleanup
                audio.addEventListener('ended', () => {
                  URL.revokeObjectURL(audioUrl);
                });
              }
            } catch (ttsError) {
              console.error('TTS failed:', ttsError);
              // Fall back to browser TTS
              voiceServiceRef.current.speak(responseText);
            }
          }
        }
      }
    } catch (error) {
      console.error('Failed to process message:', error);
      messageQueueRef.current?.acknowledgeMessage(message.id, '⚠️ Error');
    }
  };

  // Control functions
  const enable = useCallback(() => {
    setState(prev => ({ ...prev, isEnabled: true }));
  }, []);

  const disable = useCallback(() => {
    if (voiceServiceRef.current) {
      voiceServiceRef.current.stop();
    }
    setState(prev => ({ ...prev, isEnabled: false }));
  }, []);

  const startListening = useCallback(() => {
    if (voiceServiceRef.current) {
      voiceServiceRef.current.start();
    }
  }, []);

  const stopListening = useCallback(() => {
    if (voiceServiceRef.current) {
      voiceServiceRef.current.stop();
    }
  }, []);

  const speak = useCallback((text: string, onComplete?: () => void) => {
    if (voiceServiceRef.current) {
      voiceServiceRef.current.speak(text, onComplete);
    }
  }, []);

  const addTextMessage = useCallback((text: string, priority?: 'normal' | 'urgent') => {
    if (messageQueueRef.current) {
      return messageQueueRef.current.addMessage({
        text,
        priority: priority || 'normal'
      }, 'text');
    }
    return null;
  }, []);

  const clearMessages = useCallback(() => {
    if (messageQueueRef.current) {
      messageQueueRef.current.clear();
      setState(prev => ({
        ...prev,
        messages: [],
        pendingMessages: []
      }));
    }
  }, []);

  const acknowledgeMessage = useCallback((messageId: string, acknowledgment?: string) => {
    if (messageQueueRef.current) {
      messageQueueRef.current.acknowledgeMessage(messageId, acknowledgment);
    }
  }, []);

  const processMessage = useCallback((messageId: string) => {
    if (messageQueueRef.current) {
      messageQueueRef.current.processMessage(messageId);
    }
  }, []);

  return {
    // State
    ...state,
    
    // Control functions
    enable,
    disable,
    startListening,
    stopListening,
    speak,
    
    // Message functions
    addTextMessage,
    clearMessages,
    acknowledgeMessage,
    processMessage,
    
    // Utility
    isSupported: typeof window !== 'undefined' && 
      ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window)
  };
}