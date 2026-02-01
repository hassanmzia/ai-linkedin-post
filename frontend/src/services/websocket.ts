import type { AgentEvent } from '../types';

const WS_URL = import.meta.env.VITE_WS_URL || 'ws://172.168.1.95:4052';

type EventHandler = (event: AgentEvent) => void;

class WebSocketService {
  private ws: WebSocket | null = null;
  private handlers = new Map<string, Set<EventHandler>>();
  private reconnectAttempts = 0;
  private maxReconnects = 10;
  private reconnectTimeout: ReturnType<typeof setTimeout> | null = null;

  connect() {
    if (this.ws?.readyState === WebSocket.OPEN) return;

    try {
      this.ws = new WebSocket(`${WS_URL}/ws`);

      this.ws.onopen = () => {
        console.log('WebSocket connected');
        this.reconnectAttempts = 0;
      };

      this.ws.onmessage = (event) => {
        try {
          const data: AgentEvent = JSON.parse(event.data);
          this.emit('message', data);

          if (data.type === 'agent_event' && data.data) {
            const runId = data.data.run_id;
            if (runId) {
              this.emit(`run:${runId}`, data);
            }
            const projectId = data.data.project_id;
            if (projectId) {
              this.emit(`project:${projectId}`, data);
            }
          }
        } catch {
          // ignore parse errors
        }
      };

      this.ws.onclose = () => {
        console.log('WebSocket disconnected');
        this.tryReconnect();
      };

      this.ws.onerror = () => {
        // onclose will fire after this
      };
    } catch {
      this.tryReconnect();
    }
  }

  private tryReconnect() {
    if (this.reconnectAttempts >= this.maxReconnects) return;
    this.reconnectAttempts++;
    const delay = Math.min(1000 * Math.pow(2, this.reconnectAttempts), 30000);
    this.reconnectTimeout = setTimeout(() => this.connect(), delay);
  }

  disconnect() {
    if (this.reconnectTimeout) clearTimeout(this.reconnectTimeout);
    this.ws?.close();
    this.ws = null;
  }

  subscribe(runId: string) {
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify({ type: 'subscribe', run_id: runId }));
    }
  }

  unsubscribe(runId: string) {
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify({ type: 'unsubscribe', run_id: runId }));
    }
  }

  on(event: string, handler: EventHandler) {
    if (!this.handlers.has(event)) {
      this.handlers.set(event, new Set());
    }
    this.handlers.get(event)!.add(handler);
    return () => this.off(event, handler);
  }

  off(event: string, handler: EventHandler) {
    this.handlers.get(event)?.delete(handler);
  }

  private emit(event: string, data: AgentEvent) {
    this.handlers.get(event)?.forEach((handler) => handler(data));
  }
}

export const wsService = new WebSocketService();
