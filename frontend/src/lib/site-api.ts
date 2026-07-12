const API_BASE = import.meta.env.VITE_API_BASE_URL || 'https://web-staffr3-0-snowy.vercel.app';

export async function fetchSite(tenantId: string): Promise<Record<string, unknown>> {
  const res = await fetch(`${API_BASE}/sites/${encodeURIComponent(tenantId)}`);
  if (!res.ok) throw new Error(`Site fetch failed: ${res.status}`);
  return res.json();
}
