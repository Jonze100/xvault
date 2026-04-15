// =============================================================================
// useWSEvents — Subscribe to a specific WebSocket event type
// =============================================================================

"use client";

import { useEffect } from "react";
import { xvaultWS } from "@/lib/websocket";
import type { WSEventType } from "@/lib/types";

export function useWSEvents<T = unknown>(
  event: WSEventType,
  handler: (data: T) => void
): void {
  useEffect(() => {
    const unsubscribe = xvaultWS.on<T>(event, handler);
    return unsubscribe;
  }, [event, handler]);
}
