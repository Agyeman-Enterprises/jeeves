// Message Queue - Manages live conversation flow
import { VoiceMessage } from './VoiceService';

export interface QueuedMessage extends VoiceMessage {
  source: 'voice' | 'text';
  processed?: boolean;
  acknowledgment?: string;
}

export interface MessageQueueConfig {
  maxMessages: number;
  onNewMessage: (message: QueuedMessage) => void;
  onMessageUpdate: (message: QueuedMessage) => void;
  onUrgentMessage?: (message: QueuedMessage) => void;
}

export class MessageQueue {
  private messages: QueuedMessage[] = [];
  private config: MessageQueueConfig;
  private processingQueue: QueuedMessage[] = [];
  private currentProcessingId: string | null = null;

  constructor(config: MessageQueueConfig) {
    this.config = config;
  }

  addMessage(message: Pick<QueuedMessage, 'text'> & Partial<Omit<QueuedMessage, 'id' | 'text'>>, source: 'voice' | 'text' = 'voice'): QueuedMessage {
    const queuedMessage: QueuedMessage = {
      ...message,
      id: Date.now().toString(),
      source,
      processed: false,
      type: 'user',
      status: 'pending',
      timestamp: new Date(),
      priority: message.priority || 'normal'
    };

    this.messages.push(queuedMessage);
    
    // Keep only maxMessages
    if (this.messages.length > this.config.maxMessages) {
      this.messages = this.messages.slice(-this.config.maxMessages);
    }

    // Add to processing queue
    this.processingQueue.push(queuedMessage);

    // Notify listeners
    this.config.onNewMessage(queuedMessage);

    // Handle urgent messages
    if (queuedMessage.priority === 'urgent' && this.config.onUrgentMessage) {
      this.config.onUrgentMessage(queuedMessage);
    }

    return queuedMessage;
  }

  acknowledgeMessage(messageId: string, acknowledgment?: string) {
    const message = this.messages.find(m => m.id === messageId);
    if (message) {
      message.status = 'acknowledged';
      message.acknowledgment = acknowledgment;
      this.config.onMessageUpdate(message);
    }
  }

  processMessage(messageId: string) {
    const message = this.messages.find(m => m.id === messageId);
    if (message) {
      message.status = 'processed';
      message.processed = true;
      this.currentProcessingId = messageId;
      this.config.onMessageUpdate(message);
    }
  }

  completeProcessing(messageId: string) {
    if (this.currentProcessingId === messageId) {
      this.currentProcessingId = null;
    }
    // Remove from processing queue
    this.processingQueue = this.processingQueue.filter(m => m.id !== messageId);
  }

  getMessages(): QueuedMessage[] {
    return [...this.messages];
  }

  getPendingMessages(): QueuedMessage[] {
    return this.messages.filter(m => m.status === 'pending');
  }

  getUrgentMessages(): QueuedMessage[] {
    return this.processingQueue.filter(m => m.priority === 'urgent' && !m.processed);
  }

  getCurrentProcessing(): QueuedMessage | null {
    return this.messages.find(m => m.id === this.currentProcessingId) || null;
  }

  clearProcessed() {
    this.messages = this.messages.filter(m => !m.processed || m.status !== 'processed');
  }

  clear() {
    this.messages = [];
    this.processingQueue = [];
    this.currentProcessingId = null;
  }
}