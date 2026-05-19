import { createReadStream, existsSync, statSync } from 'node:fs';
import { stat } from 'node:fs/promises';
import { createServer, request as httpRequest } from 'node:http';
import { extname, join, normalize, resolve } from 'node:path';

const root = resolve('apps/web/out');
const port = Number(process.env.PUBLIC_PROXY_PORT ?? 3100);
const apiTarget = new URL(process.env.API_TARGET ?? 'http://127.0.0.1:8001');
const storageTarget = new URL(process.env.STORAGE_TARGET ?? 'http://127.0.0.1:9000');
const storageBuckets = (
  process.env.STORAGE_BUCKETS ??
  'sick-leave-documents,personal-data-documents,portal-avatars,portal-documents'
)
  .split(',')
  .map((bucket) => bucket.trim())
  .filter(Boolean);

const contentTypes = {
  '.css': 'text/css; charset=utf-8',
  '.html': 'text/html; charset=utf-8',
  '.ico': 'image/x-icon',
  '.js': 'application/javascript; charset=utf-8',
  '.json': 'application/json; charset=utf-8',
  '.png': 'image/png',
  '.svg': 'image/svg+xml',
  '.txt': 'text/plain; charset=utf-8',
  '.webmanifest': 'application/manifest+json',
};

function sendFile(res, filePath) {
  const type = contentTypes[extname(filePath)] ?? 'application/octet-stream';
  res.writeHead(200, {
    'content-type': type,
    'cache-control': filePath.endsWith('.html') ? 'no-cache' : 'public, max-age=3600',
  });
  createReadStream(filePath).pipe(res);
}

function resolveStaticPath(pathname) {
  const clean = normalize(decodeURIComponent(pathname)).replace(/^(\.\.[/\\])+/, '');
  const absolute = resolve(join(root, clean));
  if (!absolute.startsWith(root)) return null;

  const candidates = [
    absolute,
    join(absolute, 'index.html'),
    join(root, pathname.replace(/^\/+/, ''), 'index.html'),
    join(root, '404.html'),
  ];

  return (
    candidates.find((candidate) => {
      try {
        return existsSync(candidate) && statSync(candidate).isFile();
      } catch {
        return false;
      }
    }) ?? null
  );
}

function proxyApi(req, res) {
  const target = new URL(req.url ?? '/', apiTarget);
  const proxyReq = httpRequest(
    {
      hostname: target.hostname,
      port: target.port,
      path: target.pathname + target.search,
      method: req.method,
      headers: {
        ...req.headers,
        host: apiTarget.host,
        origin: `${apiTarget.protocol}//${apiTarget.host}`,
      },
    },
    (proxyRes) => {
      res.writeHead(proxyRes.statusCode ?? 502, proxyRes.headers);
      proxyRes.pipe(res);
    }
  );

  proxyReq.on('error', () => {
    res.writeHead(502, { 'content-type': 'application/json; charset=utf-8' });
    res.end(JSON.stringify({ error: 'API proxy unavailable' }));
  });

  req.pipe(proxyReq);
}

function proxyStorage(req, res) {
  const target = new URL(req.url ?? '/', storageTarget);
  const proxyReq = httpRequest(
    {
      hostname: target.hostname,
      port: target.port,
      path: target.pathname + target.search,
      method: req.method,
      headers: {
        ...req.headers,
        host: req.headers.host,
      },
    },
    (proxyRes) => {
      res.writeHead(proxyRes.statusCode ?? 502, proxyRes.headers);
      proxyRes.pipe(res);
    }
  );

  proxyReq.on('error', () => {
    res.writeHead(502, { 'content-type': 'application/json; charset=utf-8' });
    res.end(JSON.stringify({ error: 'Storage proxy unavailable' }));
  });

  req.pipe(proxyReq);
}

createServer(async (req, res) => {
  const url = new URL(req.url ?? '/', `http://${req.headers.host ?? 'localhost'}`);

  if (url.pathname.startsWith('/api/')) {
    proxyApi(req, res);
    return;
  }

  if (storageBuckets.some((bucket) => url.pathname.startsWith(`/${bucket}/`))) {
    proxyStorage(req, res);
    return;
  }

  const filePath = resolveStaticPath(url.pathname);
  if (!filePath) {
    res.writeHead(404, { 'content-type': 'text/plain; charset=utf-8' });
    res.end('Not found');
    return;
  }

  try {
    const fileStat = await stat(filePath);
    if (!fileStat.isFile()) throw new Error('not a file');
    sendFile(res, filePath);
  } catch {
    res.writeHead(404, { 'content-type': 'text/plain; charset=utf-8' });
    res.end('Not found');
  }
}).listen(port, '0.0.0.0', () => {
  console.log(`Public proxy listening on http://localhost:${port}`);
  console.log(`API proxy target ${apiTarget.href}`);
  console.log(`Storage proxy target ${storageTarget.href}`);
});
