"use client";

import { useEffect } from "react";
import { xvaultWS } from "@/lib/websocket";

export function WSProvider({ children }: { children: React.ReactNode }) {
  useEffect(() => {
    xvaultWS.connect();
    return () => xvaultWS.disconnect();
  }, []);

  return <>{children}</>;
}
