import { createReadStream, existsSync, readFileSync, statSync } from 'node:fs';
import { createServer } from 'node:http';
import { extname, join, normalize, resolve, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';

const root = resolve(dirname(fileURLToPath(import.meta.url)), '..');

function loadEnvFile(filePath) {
  if (!existsSync(filePath)) return;
  const text = readFileSync(filePath, 'utf8');
  for (const line of text.split(/\r?\n/)) {
    const trimmed = line.trim();
    if (!trimmed || trimmed.startsWith('#')) continue;
    const eq = trimmed.indexOf('=');
    if (eq <= 0) continue;
    const key = trimmed.slice(0, eq).trim();
    const value = trimmed.slice(eq + 1).trim();
    if (!(key in process.env)) process.env[key] = value;
  }
}

loadEnvFile(resolve(root, '.env'));
loadEnvFile(resolve(root, '.env.example'));

const PORT = Number.parseInt(process.env.PORT || '4200', 10);

function getDistDir() {
  const candidate1 = resolve(root, 'dist/frontend-angular-scada/browser');
  if (existsSync(candidate1)) return candidate1;
  const candidate2 = resolve(root, 'dist/frontend-angular-scada');
  if (existsSync(candidate2)) return candidate2;
  const candidate3 = resolve(root, 'dist/frontend-angular-crud/browser');
  if (existsSync(candidate3)) return candidate3;
  const candidate4 = resolve(root, 'dist/browser');
  if (existsSync(candidate4)) return candidate4;
  return resolve(root, 'dist');
}

const DIST = getDistDir();

const MIME = {
  '.html': 'text/html; charset=utf-8',
  '.js': 'text/javascript; charset=utf-8',
  '.css': 'text/css; charset=utf-8',
  '.json': 'application/json; charset=utf-8',
  '.svg': 'image/svg+xml',
  '.ico': 'image/x-icon',
  '.png': 'image/png',
  '.woff2': 'font/woff2',
  '.map': 'application/json; charset=utf-8',
};

function sendHealth(res) {
  const body = JSON.stringify({
    status: 'ok',
    service: 'frontend-angular-scada',
    framework: 'angular',
    scope: 'frontend',
    timestamp: new Date().toISOString(),
  });
  res.writeHead(200, {
    'Content-Type': 'application/json; charset=utf-8',
    'Cache-Control': 'no-store',
    'Content-Length': Buffer.byteLength(body),
  });
  res.end(body);
}

function safeJoin(base, requestPath) {
  const decoded = decodeURIComponent(requestPath.split('?')[0]);
  const target = normalize(join(base, decoded));
  if (!target.startsWith(base)) return null;
  return target;
}

const server = createServer((req, res) => {
  const url = req.url?.split('?')[0] || '/';

  if (req.method === 'GET' && (url === '/health' || url === '/health/')) {
    sendHealth(res);
    return;
  }

  let filePath = safeJoin(DIST, url === '/' ? '/index.html' : url);
  if (!filePath) {
    res.writeHead(400);
    res.end('Bad request');
    return;
  }

  if (!existsSync(filePath) || statSync(filePath).isDirectory()) {
    filePath = join(DIST, 'index.html');
  }

  const type = MIME[extname(filePath)] || 'application/octet-stream';
  res.writeHead(200, { 'Content-Type': type });
  createReadStream(filePath).pipe(res);
});

server.listen(PORT, '0.0.0.0', () => {
  console.log(`Frontend Angular SCADA escuchando en el puerto ${PORT}`);
});
