import { useState, useEffect, useRef, useCallback } from 'react';
import { useWebSocket } from './hooks/useWebSocket';

// ─── API Helpers ─────────────────────────────────────────────
const API_BASE = '';

async function apiPost(path, body = {}) {
  const res = await fetch(`${API_BASE}${path}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
  return res.json();
}

// ─── Determine WebSocket URL ─────────────────────────────────
function getWsUrl() {
  const proto = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
  return `${proto}//${window.location.host}/ws`;
}

// ═══════════════════════════════════════════════════════════════
// MAIN APP
// ═══════════════════════════════════════════════════════════════

export default function App() {
  const { isConnected, inventory, suppliers, emails, telemetryLogs } = useWebSocket(getWsUrl());
  const [chaosMode, setChaosMode] = useState(false);
  const [expandedEmail, setExpandedEmail] = useState(null);

  const toggleChaos = async () => {
    const newState = !chaosMode;
    setChaosMode(newState);
    await apiPost('/api/chaos', { enabled: newState });
  };

  return (
    <div className="min-h-screen bg-surface-900 p-4 lg:p-6">
      {/* ── Top Bar ──────────────────────────────────── */}
      <header className="flex flex-wrap items-center justify-between gap-4 mb-6">
        <div className="flex items-center gap-4">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-accent-cyan to-accent-violet flex items-center justify-center text-lg font-bold text-surface-900">
            AR
          </div>
          <div>
            <h1 className="text-lg font-bold tracking-tight text-text-primary">
              Autonomous Restocker Dashboard
            </h1>
            <p className="text-xs text-text-muted mt-0.5">
              Multi-Agent Inventory Intelligence Platform
            </p>
          </div>
        </div>

        <div className="flex items-center gap-6">
          {/* Connection Status */}
          <div className="flex items-center gap-2">
            <span className={`status-dot ${isConnected ? 'online' : 'offline'}`} />
            <span className="text-xs text-text-secondary">
              {isConnected ? 'Connected' : 'Reconnecting...'}
            </span>
          </div>

          {/* Chaos Mode */}
          <div className="flex items-center gap-3">
            <span className="text-xs font-semibold text-text-secondary tracking-wide uppercase">
              Chaos Mode
            </span>
            <button
              id="chaos-toggle"
              className={`chaos-toggle ${chaosMode ? 'active' : ''}`}
              onClick={toggleChaos}
              aria-label="Toggle Chaos Mode"
            >
              <div className="toggle-knob" />
            </button>
            {chaosMode && (
              <span className="text-xs font-bold text-accent-rose animate-pulse">
                ⚡ ACTIVE
              </span>
            )}
          </div>
        </div>
      </header>

      {/* ── Dashboard Grid ───────────────────────────── */}
      <div className="dashboard-grid grid grid-cols-1 xl:grid-cols-[1fr_1fr] gap-5">
        {/* Left Column */}
        <div className="flex flex-col gap-5">
          <InventoryModule inventory={inventory} />
          <SupplierModule suppliers={suppliers} />
        </div>

        {/* Right Column */}
        <div className="flex flex-col gap-5">
          <TelemetryStream logs={telemetryLogs} />
          <EmailOutbox
            emails={emails}
            expandedEmail={expandedEmail}
            setExpandedEmail={setExpandedEmail}
          />
        </div>
      </div>
    </div>
  );
}


// ═══════════════════════════════════════════════════════════════
// INVENTORY MODULE
// ═══════════════════════════════════════════════════════════════

function InventoryModule({ inventory }) {
  const handleStockChange = useCallback(async (productId, newStock) => {
    await apiPost('/api/inventory/update', {
      product_id: productId,
      new_stock: newStock,
    });
  }, []);

  return (
    <section className="glass-panel animate-fade-in" id="inventory-module">
      <div className="module-header">
        <div className="flex items-center gap-3">
          <div className="module-icon bg-gradient-to-br from-emerald-500/20 to-emerald-600/10 text-accent-emerald">
            🛒
          </div>
          <div>
            <div className="module-title text-text-primary">Shopify Live Inventory</div>
            <div className="module-subtitle">Real-time stock tracking · {inventory.length} products</div>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <span className="badge badge-economy">LIVE</span>
        </div>
      </div>

      <div className="overflow-x-auto" style={{ maxHeight: '380px', overflowY: 'auto' }}>
        <table className="data-table">
          <thead>
            <tr>
              <th>Product</th>
              <th>SKU</th>
              <th>Category</th>
              <th>Price</th>
              <th>Current Stock</th>
              <th>Status</th>
            </tr>
          </thead>
          <tbody>
            {inventory.map((item) => (
              <InventoryRow
                key={item.id}
                item={item}
                onStockChange={handleStockChange}
              />
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}

function InventoryRow({ item, onStockChange }) {
  const [localStock, setLocalStock] = useState(item.stock);
  const debounceRef = useRef(null);

  useEffect(() => {
    setLocalStock(item.stock);
  }, [item.stock]);

  const updateStock = (newVal) => {
    const clamped = Math.max(0, newVal);
    setLocalStock(clamped);

    if (debounceRef.current) clearTimeout(debounceRef.current);
    debounceRef.current = setTimeout(() => {
      onStockChange(item.id, clamped);
    }, 400);
  };

  const stockStatus = localStock < 5 ? 'critical' : localStock < 10 ? 'low' : 'ok';
  const stockStatusLabel = localStock < 5 ? 'Critical' : localStock < 10 ? 'Low' : 'In Stock';

  return (
    <tr>
      <td className="font-medium text-text-primary">{item.product}</td>
      <td>
        <code className="text-xs font-mono bg-surface-700 px-2 py-0.5 rounded text-accent-cyan">
          {item.sku}
        </code>
      </td>
      <td className="text-xs">{item.category}</td>
      <td className="font-mono text-xs">${item.price.toFixed(2)}</td>
      <td>
        <div className="stock-stepper">
          <button onClick={() => updateStock(localStock - 1)} aria-label="Decrease stock">−</button>
          <input
            type="number"
            className="stock-value"
            value={localStock}
            onChange={(e) => updateStock(parseInt(e.target.value) || 0)}
            min="0"
            aria-label={`Stock for ${item.product}`}
          />
          <button onClick={() => updateStock(localStock + 1)} aria-label="Increase stock">+</button>
        </div>
      </td>
      <td>
        <span className={`badge ${
          stockStatus === 'critical' ? 'email-status-failed' :
          stockStatus === 'low' ? 'badge-luxury' : 'badge-economy'
        }`}>
          {stockStatusLabel}
        </span>
      </td>
    </tr>
  );
}


// ═══════════════════════════════════════════════════════════════
// SUPPLIER MODULE
// ═══════════════════════════════════════════════════════════════

function SupplierModule({ suppliers }) {
  const handleSever = async (supplierId) => {
    await apiPost(`/api/suppliers/sever/${supplierId}`);
  };

  const handleRestore = async (supplierId) => {
    await apiPost(`/api/suppliers/restore/${supplierId}`);
  };

  return (
    <section className="glass-panel animate-fade-in" id="supplier-module" style={{ animationDelay: '0.1s' }}>
      <div className="module-header">
        <div className="flex items-center gap-3">
          <div className="module-icon bg-gradient-to-br from-violet-500/20 to-violet-600/10 text-accent-violet">
            📋
          </div>
          <div>
            <div className="module-title text-text-primary">Airtable Supplier Records</div>
            <div className="module-subtitle">Global vendor directory · {suppliers.length} suppliers</div>
          </div>
        </div>
      </div>

      <div className="overflow-x-auto" style={{ maxHeight: '340px', overflowY: 'auto' }}>
        <table className="data-table">
          <thead>
            <tr>
              <th>Supplier</th>
              <th>Region</th>
              <th>Price Tier</th>
              <th>$/Unit</th>
              <th>Lead Time</th>
              <th>Contact</th>
              <th>Action</th>
            </tr>
          </thead>
          <tbody>
            {suppliers.map((s) => (
              <tr key={s.id}>
                <td className="font-medium text-text-primary text-sm">{s.name}</td>
                <td className="text-xs">{s.region}</td>
                <td>
                  <span className={`badge badge-${s.price_tier.toLowerCase()}`}>
                    {s.price_tier}
                  </span>
                </td>
                <td className="font-mono text-xs">${s.price_per_unit.toFixed(2)}</td>
                <td className="text-xs">{s.lead_time_days}d</td>
                <td>
                  {s.email ? (
                    <span className="text-xs text-accent-cyan truncate max-w-[160px] inline-block">
                      {s.email}
                    </span>
                  ) : (
                    <span className="text-xs text-accent-rose font-semibold">⚠ SEVERED</span>
                  )}
                </td>
                <td>
                  {s.email ? (
                    <button
                      className="btn-danger"
                      onClick={() => handleSever(s.id)}
                      id={`sever-btn-${s.id}`}
                    >
                      ✂ Sever
                    </button>
                  ) : (
                    <button
                      className="btn-restore"
                      onClick={() => handleRestore(s.id)}
                      id={`restore-btn-${s.id}`}
                    >
                      🔗 Restore
                    </button>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}


// ═══════════════════════════════════════════════════════════════
// TELEMETRY STREAM
// ═══════════════════════════════════════════════════════════════

function TelemetryStream({ logs }) {
  const scrollRef = useRef(null);
  const [autoScroll, setAutoScroll] = useState(true);

  useEffect(() => {
    if (autoScroll && scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [logs, autoScroll]);

  const handleScroll = (e) => {
    const el = e.target;
    const isNearBottom = el.scrollHeight - el.scrollTop - el.clientHeight < 60;
    setAutoScroll(isNearBottom);
  };

  const agentColors = {
    'Agent 1 — Auditor': 'text-accent-cyan',
    'Agent 2 — Strategist': 'text-accent-violet',
    'Agent 3 — Comms': 'text-accent-emerald',
    'SYSTEM': 'text-accent-amber',
  };

  return (
    <section className="glass-panel animate-fade-in" id="telemetry-module" style={{ animationDelay: '0.15s' }}>
      <div className="module-header">
        <div className="flex items-center gap-3">
          <div className="module-icon bg-gradient-to-br from-cyan-500/20 to-cyan-600/10 text-accent-cyan">
            📡
          </div>
          <div>
            <div className="module-title text-text-primary">Live Agent Telemetry Stream</div>
            <div className="module-subtitle">Real-time orchestration logs · {logs.length} entries</div>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <span className={`status-dot ${logs.length > 0 ? 'online' : 'warning'}`} />
          <span className="text-xs text-text-muted">
            {autoScroll ? 'Auto-scroll ON' : 'Scroll paused'}
          </span>
        </div>
      </div>

      <div className="terminal">
        <div className="terminal-header">
          <div className="terminal-dot" style={{ background: '#ff5f57' }} />
          <div className="terminal-dot" style={{ background: '#febc2e' }} />
          <div className="terminal-dot" style={{ background: '#28c840' }} />
          <span className="text-xs text-text-muted ml-3 font-mono">agent-telemetry — bash</span>
        </div>

        <div
          className="terminal-body"
          ref={scrollRef}
          onScroll={handleScroll}
          style={{ minHeight: '200px', maxHeight: '300px' }}
        >
          {logs.length === 0 ? (
            <div className="text-text-muted text-center py-8">
              <p className="text-sm">Waiting for agent activity...</p>
              <p className="text-xs mt-1">Lower any product stock below 10 to trigger the agent chain</p>
            </div>
          ) : (
            logs.map((log) => (
              <div
                key={log.id}
                className={`terminal-line level-${log.level}`}
                style={{ animationDelay: `${(log.id % 10) * 0.02}s` }}
              >
                <span className="timestamp">[{log.timestamp}]</span>
                <span className={`agent-tag ${agentColors[log.agent] || 'text-text-secondary'}`}>
                  [{log.agent}]:
                </span>
                <span>{log.message}</span>
              </div>
            ))
          )}
          <span className="terminal-cursor" />
        </div>
      </div>
    </section>
  );
}


// ═══════════════════════════════════════════════════════════════
// EMAIL OUTBOX
// ═══════════════════════════════════════════════════════════════

function EmailOutbox({ emails, expandedEmail, setExpandedEmail }) {
  return (
    <section className="glass-panel animate-fade-in" id="email-module" style={{ animationDelay: '0.2s' }}>
      <div className="module-header">
        <div className="flex items-center gap-3">
          <div className="module-icon bg-gradient-to-br from-rose-500/20 to-rose-600/10 text-accent-rose">
            ✉️
          </div>
          <div>
            <div className="module-title text-text-primary">Gmail Outbound Outbox</div>
            <div className="module-subtitle">Generated PO templates · {emails.length} emails</div>
          </div>
        </div>
      </div>

      <div style={{ maxHeight: '360px', overflowY: 'auto' }}>
        {emails.length === 0 ? (
          <div className="text-text-muted text-center py-10">
            <p className="text-2xl mb-2">📭</p>
            <p className="text-sm">No outbound emails yet</p>
            <p className="text-xs mt-1">Purchase orders will appear here when agents complete procurement</p>
          </div>
        ) : (
          emails.map((email) => (
            <div
              key={email.id}
              className="email-card"
              onClick={() => setExpandedEmail(expandedEmail === email.id ? null : email.id)}
            >
              <div className="flex items-start justify-between gap-3">
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-1">
                    <span className={`badge text-[10px] px-1.5 py-0.5 ${
                      email.status === 'SENT' ? 'email-status-sent' : 'email-status-failed'
                    }`}>
                      {email.status}
                    </span>
                    <span className="text-xs font-semibold text-text-primary truncate">
                      {email.subject}
                    </span>
                  </div>
                  <div className="flex items-center gap-3 text-xs text-text-muted">
                    <span>To: {email.to}</span>
                    <span>·</span>
                    <span>{new Date(email.timestamp).toLocaleTimeString()}</span>
                  </div>
                </div>
              </div>

              {expandedEmail === email.id && (
                <div className="mt-3 p-3 glass-panel-inner animate-fade-in">
                  <pre className="text-xs text-text-secondary whitespace-pre-wrap font-mono leading-relaxed">
                    {email.body}
                  </pre>
                </div>
              )}
            </div>
          ))
        )}
      </div>
    </section>
  );
}
