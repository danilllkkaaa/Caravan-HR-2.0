const DEFAULT_API_BASE_URL = 'http://localhost:8000';
const LOCAL_HOSTS = new Set(['localhost', '127.0.0.1', '0.0.0.0', '::1']);

function withoutTrailingSlash(value: string): string {
  return value.replace(/\/+$/, '');
}

export function resolveApiBaseUrl(configuredBaseUrl?: string): string {
  const rawBaseUrl = withoutTrailingSlash(
    configuredBaseUrl ?? process.env.NEXT_PUBLIC_API_URL ?? DEFAULT_API_BASE_URL
  );

  if (typeof window === 'undefined') {
    return rawBaseUrl;
  }

  try {
    const apiUrl = new URL(rawBaseUrl);
    const pageHostname = window.location.hostname;

    // When served via tunnel/CDN (not localhost), adopt the page's origin
    // so API requests don't try to reach localhost:PORT which is unreachable externally
    if (LOCAL_HOSTS.has(apiUrl.hostname) && !LOCAL_HOSTS.has(pageHostname)) {
      apiUrl.hostname = pageHostname;
      apiUrl.protocol = window.location.protocol;
      apiUrl.port = window.location.port; // '' for standard 80/443
    }

    return withoutTrailingSlash(apiUrl.toString());
  } catch {
    return rawBaseUrl;
  }
}
