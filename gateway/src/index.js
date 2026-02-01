/**
 * API Gateway - Node.js Express server with WebSocket support.
 * Proxies REST requests to Django backend and provides real-time
 * WebSocket connections for agent workflow updates via Redis pub/sub.
 */

const express = require('express');
const http = require('http');
const { WebSocketServer } = require('ws');
const { createProxyMiddleware } = require('http-proxy-middleware');
const cors = require('cors');
const morgan = require('morgan');
const helmet = require('helmet');
const rateLimit = require('express-rate-limit');
const Redis = require('ioredis');

const PORT = parseInt(process.env.PORT || '4052', 10);
const BACKEND_URL = process.env.BACKEND_URL || 'http://backend:8052';
const REDIS_URL = process.env.REDIS_URL || 'redis://redis:6379/0';
const CORS_ORIGIN = process.env.CORS_ORIGIN || 'http://172.168.1.95:3052';

const app = express();
const server = http.createServer(app);

// Middleware
app.use(helmet({ contentSecurityPolicy: false }));
app.use(cors({
  origin: CORS_ORIGIN.split(','),
  credentials: true,
}));
app.use(morgan('combined'));

// Rate limiting
const limiter = rateLimit({
  windowMs: 1 * 60 * 1000,
  max: 200,
  standardHeaders: true,
  legacyHeaders: false,
});
app.use(limiter);

// Health check
app.get('/health', (req, res) => {
  res.json({ status: 'ok', service: 'linkedin-agent-gateway', timestamp: new Date().toISOString() });
});

// A2A discovery endpoint at gateway level
app.get('/.well-known/agent.json', async (req, res) => {
  try {
    const response = await fetch(`${BACKEND_URL}/a2a/agents/`);
    const data = await response.json();
    res.json({
      ...data,
      gateway: {
        url: `http://172.168.1.95:${PORT}`,
        websocket: `ws://172.168.1.95:${PORT}/ws`,
        protocol: 'a2a/1.0',
      },
    });
  } catch (err) {
    res.status(502).json({ error: 'Backend unavailable' });
  }
});

// Proxy API requests to Django backend
app.use('/api', createProxyMiddleware({
  target: BACKEND_URL,
  changeOrigin: true,
  timeout: 300000,
  proxyTimeout: 300000,
  onError: (err, req, res) => {
    console.error('Proxy error:', err.message);
    res.status(502).json({ error: 'Backend service unavailable' });
  },
}));

// Proxy MCP requests
app.use('/mcp', createProxyMiddleware({
  target: BACKEND_URL,
  changeOrigin: true,
  timeout: 300000,
}));

// Proxy A2A requests
app.use('/a2a', createProxyMiddleware({
  target: BACKEND_URL,
  changeOrigin: true,
  timeout: 300000,
}));

// WebSocket Server for real-time agent updates
const wss = new WebSocketServer({ server, path: '/ws' });

// Redis subscriber for agent events
let redisSub;
try {
  redisSub = new Redis(REDIS_URL);
  redisSub.on('error', (err) => {
    console.error('Redis subscriber error:', err.message);
  });
  redisSub.on('connect', () => {
    console.log('Redis subscriber connected');
  });
} catch (err) {
  console.error('Failed to connect to Redis:', err.message);
}

// Track subscriptions per client
const clientSubscriptions = new Map();

wss.on('connection', (ws, req) => {
  const clientId = Math.random().toString(36).substring(7);
  console.log(`WebSocket client connected: ${clientId}`);
  clientSubscriptions.set(clientId, new Set());

  ws.on('message', (data) => {
    try {
      const msg = JSON.parse(data.toString());

      if (msg.type === 'subscribe' && msg.run_id) {
        const channel = `agent_run:${msg.run_id}`;
        const subs = clientSubscriptions.get(clientId);
        if (subs && !subs.has(channel)) {
          subs.add(channel);
          if (redisSub) {
            redisSub.subscribe(channel);
          }
          ws.send(JSON.stringify({ type: 'subscribed', channel, run_id: msg.run_id }));
          console.log(`Client ${clientId} subscribed to ${channel}`);
        }
      }

      if (msg.type === 'unsubscribe' && msg.run_id) {
        const channel = `agent_run:${msg.run_id}`;
        const subs = clientSubscriptions.get(clientId);
        if (subs) {
          subs.delete(channel);
        }
      }

      if (msg.type === 'ping') {
        ws.send(JSON.stringify({ type: 'pong', timestamp: Date.now() }));
      }
    } catch (err) {
      console.error('WebSocket message error:', err.message);
    }
  });

  ws.on('close', () => {
    console.log(`WebSocket client disconnected: ${clientId}`);
    clientSubscriptions.delete(clientId);
  });

  ws.on('error', (err) => {
    console.error(`WebSocket error for ${clientId}:`, err.message);
  });

  // Send welcome message
  ws.send(JSON.stringify({
    type: 'connected',
    clientId,
    timestamp: Date.now(),
  }));
});

// Forward Redis messages to subscribed WebSocket clients
if (redisSub) {
  redisSub.on('message', (channel, message) => {
    wss.clients.forEach((client) => {
      if (client.readyState === 1) { // WebSocket.OPEN
        // Find client ID for this connection
        for (const [cid, subs] of clientSubscriptions.entries()) {
          if (subs.has(channel)) {
            try {
              const parsed = JSON.parse(message);
              client.send(JSON.stringify({
                type: 'agent_event',
                channel,
                data: parsed,
                timestamp: Date.now(),
              }));
            } catch {
              client.send(JSON.stringify({
                type: 'agent_event',
                channel,
                data: message,
                timestamp: Date.now(),
              }));
            }
          }
        }
      }
    });
  });
}

// Start server
server.listen(PORT, '0.0.0.0', () => {
  console.log(`Gateway running on port ${PORT}`);
  console.log(`Backend: ${BACKEND_URL}`);
  console.log(`Redis: ${REDIS_URL}`);
  console.log(`CORS: ${CORS_ORIGIN}`);
});

// Graceful shutdown
process.on('SIGTERM', () => {
  console.log('SIGTERM received, shutting down...');
  wss.close();
  server.close();
  if (redisSub) redisSub.disconnect();
  process.exit(0);
});
