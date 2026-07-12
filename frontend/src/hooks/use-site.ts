import { useEffect, useState } from 'react';
import { fetchSite } from '../lib/site-api';
import type { SiteData } from '../lib/types';

export function useSite(tenantId: string) {
  const [site, setSite] = useState<SiteData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!tenantId) { setLoading(false); return; }
    fetchSite(tenantId)
      .then(setSite)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, [tenantId]);

  return { site, loading, error };
}
