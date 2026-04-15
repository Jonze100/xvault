"use client";

import { useState, useEffect } from "react";
import { xvaultWS } from "@/lib/websocket";

export function useWSConnection() {
  const [isConnected, setIsConnected] = useState(false);

  useEffect(() => {
    const checkInterval = setInterval(() => {
      setIsConnected(xvaultWS.isConnected);
    }, 2000);
    return () => clearInterval(checkInterval);
  }, []);

  return {
    isConnected,
    reconnect: () => xvaultWS.connect(),
  };
}
