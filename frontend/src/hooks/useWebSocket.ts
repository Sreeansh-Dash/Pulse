import { useEffect, useRef, useState } from 'react';

export function useWebSocket(url: string, onMessage: (data: Record<string, unknown>) => void) {
  const [connected, setConnected] = useState(false);
  const ws = useRef<WebSocket | null>(null);
  const reconnectTimeout = useRef<number | null>(null);
  const reconnectAttempt = useRef(0);

  useEffect(() => {
    function connect() {
      // Connect using current host + WS protocol
      const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
      // In dev we proxy via Vite, so we use the same host.
      const wsUrl = `${protocol}//${window.location.host}${url}`;
      
      ws.current = new WebSocket(wsUrl);

      ws.current.onopen = () => {
        console.log('WebSocket connected');
        setConnected(true);
        reconnectAttempt.current = 0;
      };

      ws.current.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          onMessage(data);
        } catch (e) {
          console.error("WS Parse error", e);
        }
      };

      ws.current.onclose = () => {
        console.log('WebSocket disconnected');
        setConnected(false);
        // Exponential backoff reconnect
        const timeout = Math.min(1000 * Math.pow(2, reconnectAttempt.current), 30000);
        reconnectAttempt.current++;
        reconnectTimeout.current = window.setTimeout(connect, timeout);
      };
      
      ws.current.onerror = (err) => {
        console.error("WebSocket error", err);
      }
    }

    connect();

    return () => {
      if (reconnectTimeout.current) window.clearTimeout(reconnectTimeout.current);
      if (ws.current) {
        ws.current.onclose = null; // Prevent reconnect on unmount
        ws.current.close();
      }
    };
  }, [url]);

  return connected;
}
