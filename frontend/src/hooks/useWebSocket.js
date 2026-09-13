import { useEffect, useRef, useState, useCallback } from 'react';

/**
 * Custom hook for WebSocket connection to the backend.
 * Handles auto-reconnect, message parsing, and state synchronization.
 */
export function useWebSocket(url) {
  const [isConnected, setIsConnected] = useState(false);
  const [inventory, setInventory] = useState([]);
  const [suppliers, setSuppliers] = useState([]);
  const [emails, setEmails] = useState([]);
  const [telemetryLogs, setTelemetryLogs] = useState([]);
  const wsRef = useRef(null);
  const reconnectTimer = useRef(null);
  const logIdCounter = useRef(0);

  const connect = useCallback(() => {
    try {
      const ws = new WebSocket(url);
      wsRef.current = ws;

      ws.onopen = () => {
        setIsConnected(true);
        console.log('[WS] Connected to backend');
      };

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);

          switch (data.type) {
            case 'inventory_update':
              setInventory(data.data);
              break;
            case 'supplier_update':
              setSuppliers(data.data);
              break;
            case 'email_update':
              setEmails(data.data);
              break;
            case 'telemetry':
              setTelemetryLogs(prev => {
                const newLog = {
                  ...data,
                  id: logIdCounter.current++,
                };
                // Keep last 200 log entries
                const updated = [...prev, newLog];
                return updated.slice(-200);
              });
              break;
            case 'pong':
              break;
            default:
              console.log('[WS] Unknown message type:', data.type);
          }
        } catch (err) {
          console.error('[WS] Parse error:', err);
        }
      };

      ws.onclose = () => {
        setIsConnected(false);
        console.log('[WS] Disconnected. Reconnecting in 3s...');
        reconnectTimer.current = setTimeout(connect, 3000);
      };

      ws.onerror = (err) => {
        console.error('[WS] Error:', err);
        ws.close();
      };
    } catch (err) {
      console.error('[WS] Connection failed:', err);
      reconnectTimer.current = setTimeout(connect, 3000);
    }
  }, [url]);

  useEffect(() => {
    connect();
    return () => {
      if (wsRef.current) wsRef.current.close();
      if (reconnectTimer.current) clearTimeout(reconnectTimer.current);
    };
  }, [connect]);

  // Heartbeat every 30s
  useEffect(() => {
    const interval = setInterval(() => {
      if (wsRef.current?.readyState === WebSocket.OPEN) {
        wsRef.current.send(JSON.stringify({ type: 'ping' }));
      }
    }, 30000);
    return () => clearInterval(interval);
  }, []);

  return {
    isConnected,
    inventory,
    suppliers,
    emails,
    telemetryLogs,
  };
}
