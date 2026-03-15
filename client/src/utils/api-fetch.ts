/**
 * Thin fetch wrapper that:
 *  1. Adds the ngrok browser-warning bypass header so API calls work through ngrok tunnels.
 *  2. Fires a 'auth:expired' window event on 401 so the AuthProvider can auto-logout.
 */
export async function apiFetch(url: string, init: RequestInit = {}): Promise<Response> {
    const headers = new Headers(init.headers);
    headers.set('ngrok-skip-browser-warning', '1');

    const res = await fetch(url, { ...init, headers });

    if (res.status === 401) {
        window.dispatchEvent(new Event('auth:expired'));
    }

    return res;
}
