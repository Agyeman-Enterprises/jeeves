// Voice Service - Core speech recognition and synthesis
export interface VoiceMessage {
  id: string;
  text: string;
  timestamp: Date;
  type: 'user' | 'assistant';
  status: 'pending' | 'acknowledged' | 'processed';
  priority: 'normal' | 'urgent';
}

export interface VoiceServiceConfig {
  wakeWords: string[];
  continuous: boolean;
  interimResults: boolean;
  language: string;
  onMessage: (message: VoiceMessage) => void;
  onStateChange: (state: VoiceState) => void;
}

export type VoiceState = 'idle' | 'listening' | 'processing' | 'speaking';

// eslint-disable-next-line @typescript-eslint/no-explicit-any
type SpeechRecognitionInstance = any;

export class VoiceService {
  private recognition: SpeechRecognitionInstance = null;
  private synthesis: SpeechSynthesis;
  private config: VoiceServiceConfig;
  private state: VoiceState = 'idle';
  private isListening = false;
  private currentTranscript = '';
  private silenceTimer: NodeJS.Timeout | null = null;
  private wakeWordActive = false;

  constructor(config: VoiceServiceConfig) {
    this.config = config;
    this.synthesis = window.speechSynthesis;
    this.initializeRecognition();
  }

  private initializeRecognition() {
    if (!('webkitSpeechRecognition' in window) && !('SpeechRecognition' in window)) {
      console.error('Speech recognition not supported');
      return;
    }

    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    this.recognition = new SpeechRecognition();
    
    this.recognition.continuous = this.config.continuous;
    this.recognition.interimResults = this.config.interimResults;
    this.recognition.lang = this.config.language;
    this.recognition.maxAlternatives = 3;

    this.recognition.onstart = () => {
      this.setState('listening');
      this.isListening = true;
    };

    this.recognition.onresult = (event) => {
      const results = event.results;
      const currentIndex = results.length - 1;
      const transcript = results[currentIndex][0].transcript;
      const isFinal = results[currentIndex].isFinal;

      // Check for wake words
      if (!this.wakeWordActive && this.config.continuous) {
        const lowerTranscript = transcript.toLowerCase();
        const hasWakeWord = this.config.wakeWords.some(word => 
          lowerTranscript.includes(word.toLowerCase())
        );
        
        if (hasWakeWord) {
          this.wakeWordActive = true;
          this.currentTranscript = '';
          // Remove wake word from transcript
          let cleanTranscript = transcript;
          this.config.wakeWords.forEach(word => {
            const regex = new RegExp(word, 'gi');
            cleanTranscript = cleanTranscript.replace(regex, '').trim();
          });
          if (cleanTranscript) {
            this.currentTranscript = cleanTranscript;
          }
          return;
        } else if (!this.wakeWordActive) {
          return; // Ignore non-wake word speech
        }
      }

      if (this.wakeWordActive || !this.config.continuous) {
        this.currentTranscript = transcript;

        // Reset silence timer on new speech
        if (this.silenceTimer) {
          clearTimeout(this.silenceTimer);
        }

        if (isFinal) {
          // Start silence detection after final result
          this.silenceTimer = setTimeout(() => {
            this.processMessage();
          }, 1500); // 1.5 second silence threshold
        }
      }
    };

    this.recognition.onerror = (event) => {
      console.error('Speech recognition error:', event.error);
      if (event.error === 'no-speech') {
        // Reset wake word detection on silence
        if (this.wakeWordActive) {
          this.wakeWordActive = false;
          this.currentTranscript = '';
        }
      }
      if (event.error === 'not-allowed') {
        this.setState('idle');
        this.isListening = false;
      }
    };

    this.recognition.onend = () => {
      this.isListening = false;
      if (this.config.continuous && this.state === 'listening') {
        // Restart for continuous mode
        setTimeout(() => this.start(), 100);
      } else {
        this.setState('idle');
      }
    };
  }

  private setState(state: VoiceState) {
    this.state = state;
    this.config.onStateChange(state);
  }

  private processMessage() {
    if (this.currentTranscript.trim()) {
      const message: VoiceMessage = {
        id: Date.now().toString(),
        text: this.currentTranscript.trim(),
        timestamp: new Date(),
        type: 'user',
        status: 'pending',
        priority: this.detectPriority(this.currentTranscript)
      };

      this.config.onMessage(message);
      this.currentTranscript = '';
      this.wakeWordActive = false;
    }
  }

  private detectPriority(text: string): 'normal' | 'urgent' {
    const urgentKeywords = [
      'urgent', 'immediately', 'stop', 'wait', 'hold on', 
      'actually', 'change that', 'nevermind', 'cancel'
    ];
    const lowerText = text.toLowerCase();
    return urgentKeywords.some(keyword => lowerText.includes(keyword)) ? 'urgent' : 'normal';
  }

  start() {
    if (this.recognition && !this.isListening) {
      this.recognition.start();
    }
  }

  stop() {
    if (this.recognition && this.isListening) {
      this.recognition.stop();
      this.isListening = false;
      this.wakeWordActive = false;
      this.currentTranscript = '';
      if (this.silenceTimer) {
        clearTimeout(this.silenceTimer);
        this.silenceTimer = null;
      }
    }
  }

  speak(text: string, onComplete?: () => void) {
    if (!this.synthesis) return;

    this.setState('speaking');
    const utterance = new SpeechSynthesisUtterance(text);
    utterance.rate = 1.1;
    utterance.pitch = 1.0;
    utterance.volume = 0.9;

    utterance.onend = () => {
      this.setState('idle');
      if (onComplete) onComplete();
    };

    this.synthesis.speak(utterance);
  }

  cancelSpeech() {
    if (this.synthesis) {
      this.synthesis.cancel();
    }
  }

  destroy() {
    this.stop();
    this.cancelSpeech();
    if (this.silenceTimer) {
      clearTimeout(this.silenceTimer);
    }
  }
}

// Browser compatibility types are declared in components/jarvis/VoiceButton.tsx