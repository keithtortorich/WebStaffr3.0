import { useEffect, useState } from 'react'
import { fetchSite } from './lib/site-api'
import type { SiteData } from './lib/types'

function App() {
  const [site, setSite] = useState<SiteData | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const tenantId = new URLSearchParams(window.location.search).get('tenant') || ''
    if (!tenantId) {
      setLoading(false)
      return
    }
    fetchSite(tenantId)
      .then(setSite)
      .catch((err) => console.error(err))
      .finally(() => setLoading(false))
  }, [])

  if (loading) return <div style={{ padding: 24 }}>Loading...</div>
  if (!site) return <div style={{ padding: 24 }}>No site data.</div>

  return (
    <div style={{ padding: 24, fontFamily: 'system-ui, sans-serif' }}>
      <h1>{String(site.biz_name || 'Your Business')}</h1>
      <p>{String(site.tagline || '')}</p>
      <p>{String(site.differentiator || '')}</p>
      <pre style={{ background: '#f5f5f5', padding: 16, borderRadius: 8 }}>
        {JSON.stringify(site, null, 2)}
      </pre>
    </div>
  )
}

export default App
