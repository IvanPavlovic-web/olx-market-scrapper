"use client";
import { useEffect, useRef, useState } from "react";
import Cookies from "js-cookie";
import { WS_URL } from "@/lib/api";

export function useWS() {
  const [messages, setMessages] = useState<any[]>([]);
  const [connected, setConnected] = useState(false);
  const wsRef = useRef<WebSocket | null>(null);

  useEffect(() => {
    const token = Cookies.get("token");
    if (!token) return;

    const ws = new WebSocket(`${WS_URL}?token=${token}`);
    wsRef.current = ws;

    ws.onopen = () => {
      setConnected(true);
      ws.send("ping");
    };
    ws.onmessage = (ev) => {
      if (ev.data === "pong") return;
      try {
        const data = JSON.parse(ev.data);
        setMessages((prev) => [data, ...prev].slice(0, 200));
      } catch {}
    };
    ws.onclose = () => setConnected(false);

    const pingInterval = setInterval(() => {
      if (ws.readyState === WebSocket.OPEN) ws.send("ping");
    }, 25000);

    return () => {
      clearInterval(pingInterval);
      ws.close();
    };
  }, []);

  return { messages, connected };
}
