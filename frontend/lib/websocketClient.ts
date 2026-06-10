export interface ActionItem {
  owner: string;
  task: string;
  deadline: string;
  quote: string;
  confidence: number;
  review_status: "pending" | "accepted" | "rejected";
}

export interface Decision {
  decision: string;
  timestamp: string;
  quote: string;
  confidence: number;
}

export interface Risk {
  description: string;
  timestamp: string;
  quote: string;
  confidence: number;
}

export interface WSClientOptions {
  url: string;
  meetingId: string;
  onTranscript: (data: { timestamp: string; speaker: string; text: string }) => void;
  onInsights: (data: { action_items: ActionItem[]; decisions: Decision[]; risks: Risk[]; summary: string }) => void;
  onStatus: (status: string) => void;
  onDroppedFrame: () => void;
  onError: (error: string) => void;
}

export class MeetingWebSocketClient {
  private ws: WebSocket | null = null;
  private options: WSClientOptions;
  
  private sequence: number = 0;
  private isConnecting: boolean = false;
  private intentionallyClosed: boolean = false;
  
  private reconnectAttempts: number = 0;
  private maxReconnectAttempts: number = 5;
  private reconnectDelays = [1000, 2000, 4000, 8000, 10000];
  
  private heartbeatInterval: NodeJS.Timeout | null = null;
  private pongTimeout: NodeJS.Timeout | null = null;
  private pendingUtterances: Array<{ buffer: ArrayBuffer; speechStartMs: number; speechEndMs: number }> = [];

  constructor(options: WSClientOptions) {
    this.options = options;
  }

  public connect() {
    if (this.ws && (this.ws.readyState === WebSocket.OPEN || this.ws.readyState === WebSocket.CONNECTING)) {
      return;
    }

    this.isConnecting = true;
    this.intentionallyClosed = false;
    this.options.onStatus('connecting');

    try {
      this.ws = new WebSocket(this.options.url);
      
      this.ws.onopen = this.handleOpen.bind(this);
      this.ws.onmessage = this.handleMessage.bind(this);
      this.ws.onclose = this.handleClose.bind(this);
      this.ws.onerror = this.handleError.bind(this);
    } catch (err) {
      console.error('WebSocket connection error:', err);
      this.options.onError('Failed to connect to server');
      this.scheduleReconnect();
    }
  }

  private handleOpen() {
    this.isConnecting = false;
    this.reconnectAttempts = 0;
    this.options.onStatus('connected');
    
    // Start session
    this.sendControlMessage('start');
    
    // Setup heartbeat
    this.startHeartbeat();
    
    // Send any pending utterances that were queued while disconnected
    this.flushPendingUtterances();
  }

  private handleMessage(event: MessageEvent) {
    try {
      const data = JSON.parse(event.data);
      
      if (data.type === 'transcript' && data.data) {
        this.options.onTranscript(data.data);
      } else if (data.type === 'insights' && data.data) {
        this.options.onInsights(data.data);
      } else if (data.type === 'status' && data.status) {
        this.options.onStatus(data.status);
      } else if (data.type === 'error' && data.message) {
        this.options.onError(data.message);
      } else if (data.type === 'pong') {
        // Clear the pong timeout — connection is alive
        if (this.pongTimeout) {
          clearTimeout(this.pongTimeout);
          this.pongTimeout = null;
        }
      }
    } catch (e) {
      console.error('Failed to parse WebSocket message:', e);
    }
  }

  private handleClose(event: CloseEvent) {
    this.stopHeartbeat();
    this.ws = null;
    
    if (this.intentionallyClosed) {
      this.options.onStatus('disconnected');
    } else {
      this.options.onStatus('reconnecting');
      this.scheduleReconnect();
    }
  }

  private handleError(event: Event) {
    console.error('WebSocket error event:', event);
    // Onclose will fire after onerror, handling reconnection
  }

  private scheduleReconnect() {
    if (this.intentionallyClosed) return;
    
    if (this.reconnectAttempts < this.maxReconnectAttempts) {
      const delay = this.reconnectDelays[this.reconnectAttempts];
      this.reconnectAttempts++;
      
      console.log(`Reconnecting in ${delay}ms (Attempt ${this.reconnectAttempts})`);
      setTimeout(() => {
        this.connect();
      }, delay);
    } else {
      this.options.onError('Connection lost. Please refresh the page.');
      this.options.onStatus('disconnected');
    }
  }

  private startHeartbeat() {
    this.stopHeartbeat();
    this.heartbeatInterval = setInterval(() => {
      if (this.ws?.readyState === WebSocket.OPEN) {
        this.sendControlMessage('ping');
        // Trigger reconnect if no pong arrives within 30s
        this.pongTimeout = setTimeout(() => {
          console.warn('Pong timeout — connection appears hung, reconnecting');
          this.ws?.close();
        }, 30000);
      }
    }, 15000);
  }

  private stopHeartbeat() {
    if (this.heartbeatInterval) {
      clearInterval(this.heartbeatInterval);
      this.heartbeatInterval = null;
    }
    if (this.pongTimeout) {
      clearTimeout(this.pongTimeout);
      this.pongTimeout = null;
    }
  }

  public sendControlMessage(type: string) {
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify({
        type,
        meeting_id: this.options.meetingId
      }));
    }
  }

  public sendUtterance(wavBuffer: ArrayBuffer, speechStartMs: number, speechEndMs: number) {
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.sequence++;

      // 1. Send metadata frame
      this.ws.send(JSON.stringify({
        type: 'audio',
        meeting_id: this.options.meetingId,
        sequence: this.sequence,
        speech_start_ms: speechStartMs,
        speech_end_ms: speechEndMs
      }));

      // 2. Send binary audio frame
      this.ws.send(wavBuffer);
    } else {
      // Queue it if we're disconnected
      this.pendingUtterances.push({ buffer: wavBuffer, speechStartMs, speechEndMs });

      // L-2: Notify caller when oldest frames are silently dropped so the UI can warn
      if (this.pendingUtterances.length > 20) {
        this.pendingUtterances.shift();
        this.options.onDroppedFrame();
      }
    }
  }
  
  public requestAnalysis() {
    this.sendControlMessage('analyze_now');
  }

  private flushPendingUtterances() {
    if (this.pendingUtterances.length > 0 && this.ws?.readyState === WebSocket.OPEN) {
      console.log(`Flushing ${this.pendingUtterances.length} pending utterances`);
      
      // Send them sequentially with slight delay to avoid overwhelming the socket
      const queue = [...this.pendingUtterances];
      this.pendingUtterances = [];
      
      const processNext = () => {
        if (queue.length === 0) return;
        
        const item = queue.shift();
        if (item && this.ws?.readyState === WebSocket.OPEN) {
          this.sequence++;
          
          this.ws.send(JSON.stringify({
            type: 'audio',
            meeting_id: this.options.meetingId,
            sequence: this.sequence,
            speech_start_ms: item.speechStartMs,
            speech_end_ms: item.speechEndMs
          }));
          
          this.ws.send(item.buffer);
          
          setTimeout(processNext, 100);
        }
      };
      
      processNext();
    }
  }

  public disconnect() {
    this.intentionallyClosed = true;
    this.stopHeartbeat();
    
    if (this.ws) {
      this.sendControlMessage('stop');
      this.ws.close();
      this.ws = null;
    }
  }
}
