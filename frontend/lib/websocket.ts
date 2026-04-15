// =============================================================================
// XVault WebSocket Connection Manager
// Real-time agent events, decisions, and treasury updates
// =============================================================================

import type { WSEvent, WSEventType } from "./types";

type EventHandler<T = unknown> = (data: T) => void;

class XVaultWebSocket {
  private ws: WebSocket | null = null;
  private url: string;
  private handlers: Map<WSEventType, Set<EventHandler>> = new Map();
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 10;
  private reconnectDelay = 1000;
  private pingInterval: ReturnType<typeof setInterval> | null = null;
  private isIntentionallyClosed = false;

  constructor(url: string) {
    this.url = url;
  }

  connect(): void {
    if (this.ws?.readyState === WebSocket.OPEN) return;

    this.isIntentionallyClosed = false;
    this.ws = new WebSocket(this.url);

    this.ws.onopen = () => {
      console.log("[XVault WS] Connected");
      this.reconnectAttempts = 0;
      this.reconnectDelay = 1000;
      this.startPing();
    };

    this.ws.onmessage = (event: MessageEvent) => {
      try {
        const message: WSEvent = JSON.parse(event.data as string);
        this.dispatch(message.event, message.data);
      } catch (err) {
        console.error("[XVault WS] Parse error:", err);
      }
    };

    this.ws.onclose = () => {
      this.stopPing();
      if (!this.isIntentionallyClosed) {
        this.scheduleReconnect();
      }
    };

    this.ws.onerror = (err) => {
      console.error("[XVault WS] Error:", err);
    };
  }

  disconnect(): void {
    this.isIntentionallyClosed = true;
    this.stopPing();
    this.ws?.close();
    this.ws = null;
  }

  on<T = unknown>(event: WSEventType, handler: EventHandler<T>): () => void {
    if (!this.handlers.has(event)) {
      this.handlers.set(event, new Set());
    }
    this.handlers.get(event)!.add(handler as EventHandler);

    // Return unsubscribe function
    return () => {
      this.handlers.get(event)?.delete(handler as EventHandler);
    };
  }

  send(data: unknown): void {
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(data));
    }
  }

  /** Emit an event directly to all local subscribers — used by demo simulation */
  emit(event: WSEventType, data: unknown): void {
    this.dispatch(event, data);
  }

  get isConnected(): boolean {
    return this.ws?.readyState === WebSocket.OPEN;
  }

  dispatch(event: WSEventType, data: unknown): void {
    this.handlers.get(event)?.forEach((handler) => handler(data));
  }

  private startPing(): void {
    this.pingInterval = setInterval(() => {
      this.send({ type: "ping" });
    }, 30_000);
  }

  private stopPing(): void {
    if (this.pingInterval) {
      clearInterval(this.pingInterval);
      this.pingInterval = null;
    }
  }

  private scheduleReconnect(): void {
    if (this.reconnectAttempts >= this.maxReconnectAttempts) {
      console.error("[XVault WS] Max reconnect attempts reached");
      return;
    }

    console.log(`[XVault WS] Reconnecting in ${this.reconnectDelay}ms...`);
    setTimeout(() => {
      this.reconnectAttempts++;
      this.reconnectDelay = Math.min(this.reconnectDelay * 1.5, 30_000);
      this.connect();
    }, this.reconnectDelay);
  }
}

// Singleton instance
const WS_URL =
  (typeof window !== "undefined" && process.env.NEXT_PUBLIC_WS_URL) ||
  "ws://localhost:8000/ws";

export const xvaultWS = new XVaultWebSocket(WS_URL);
export type { WSEvent, WSEventType };
