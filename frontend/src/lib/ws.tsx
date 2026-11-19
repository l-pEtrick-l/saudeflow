import { useEffect, useRef, useState } from "react";
import { wsUrl } from "./api";

export type RealtimeStatus = "connecting" | "online" | "offline";

/**
 * Conecta ao WebSocket e cai para "offline" (o componente deve fazer polling).
 * O backend transmite eventos por canal: request:<id>, unit:<id>, alert:<id>, user:<id>.
 */
export function useRealtime(
  channels: string[],
  onEvent: (message: { type: string; data: unknown }) => void
) {
  const [status, setStatus] = useState<RealtimeStatus>("connecting");
  const socketRef = useRef<WebSocket | null>(null);
  const handlersRef = useRef(onEvent);
  handlersRef.current = onEvent;

  useEffect(() => {
    let closed = false;
    let reconnectTimer: number | undefined;
    let attempts = 0;

    const connect = () => {
      if (closed) return;
      setStatus("connecting");
      const socket = new WebSocket(wsUrl(channels));
      socketRef.current = socket;

      socket.onopen = () => {
        attempts = 0;
        setStatus("online");
      };
      socket.onmessage = (event) => {
        try {
          handlersRef.current(JSON.parse(event.data));
        } catch {
          /* mensagem inválida: ignorar */
        }
      };
      socket.onclose = () => {
        if (closed) return;
        setStatus("offline");
        attempts += 1;
        const delay = Math.min(15000, 1000 * attempts);
        reconnectTimer = window.setTimeout(connect, delay);
      };
      socket.onerror = () => socket.close();
    };

    connect();
    return () => {
      closed = true;
      if (reconnectTimer) window.clearTimeout(reconnectTimer);
      socketRef.current?.close();
    };
  }, [channels.join("|")]);

  return { status };
}

export function RealtimeBadge({ status }: { status: RealtimeStatus }) {
  const styles: Record<RealtimeStatus, string> = {
    online: "bg-mint-100 text-mint-700",
    connecting: "bg-amber-100 text-amber-700",
    offline: "bg-red-100 text-red-700",
  };
  const labels: Record<RealtimeStatus, string> = {
    online: "Tempo real conectado",
    connecting: "Conectando...",
    offline: "Tempo real indisponível — atualizando por consulta",
  };
  return <span className={`badge ${styles[status]}`}>{labels[status]}</span>;
}
