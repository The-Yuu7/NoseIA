import { spawn } from 'node:child_process';
import { existsSync, readFileSync } from 'node:fs';
import { dirname, resolve } from 'node:path';
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
    if (!(key in process.env)) {
      process.env[key] = value;
    }
  }
}

loadEnvFile(resolve(root, '.env'));
loadEnvFile(resolve(root, '.env.example'));

const port = process.env.PORT || '4200';
const ng = spawn(
  'npx',
  ['ng', 'serve', '--host', '0.0.0.0', '--port', String(port)],
  { cwd: root, stdio: 'inherit', shell: true },
);

ng.on('exit', (code) => process.exit(code ?? 0));
