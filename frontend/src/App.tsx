import { useEffect, useState } from 'react'
import { fetchSite } from './lib/site-api'
import type { SiteData } from './lib/types'

const MOCK_SITE_DATA: Record<string, SiteData> = {
  hvac: {
    tenant_id: 'mock-hvac-phoenix',
    biz_name: 'Phoenix Peak HVAC',
    tagline: 'Fast emergency AC service in Phoenix heat.',
    differentiator: 'Same-day service for AC outages. Licensed, insured, and available after hours.',
    services: 'AC repair, installation, maintenance, duct cleaning, heat pumps',
    city: 'Phoenix, AZ',
    contact_name: 'Jake Moralez',
    phone: '(602) 555-0142',
    email: 'service@phoenixpeakhvac.com',
    years_in_business: 14,
    license_number: 'ROC 123456',
    insurance_status: 'insured',
    service_area: 'Phoenix metro and East Valley',
    emergency_service_available: true,
    preferred_trade: 'hvac',
  },
  plumber: {
    tenant_id: 'mock-plumber-phoenix',
    biz_name: 'CopperKey Plumbing',
    tagline: 'Local plumbing when you need it most.',
    differentiator: 'Upfront pricing, clean technicians, and 60-minute response windows.',
    services: 'Drain cleaning, leak repair, water heaters, repiping, sewer camera inspection',
    city: 'Phoenix, AZ',
    contact_name: 'Diana Ruiz',
    phone: '(602) 555-0198',
    email: 'hello@copperkeyplumbing.com',
    years_in_business: 9,
    license_number: 'ROC 908321',
    insurance_status: 'insured',
    service_area: 'Phoenix, Scottsdale, Tempe',
    emergency_service_available: true,
    preferred_trade: 'plumbing',
  },
  roofer: {
    tenant_id: 'mock-roofer-phoenix',
    biz_name: 'Desert Crest Roofing',
    tagline: 'Storm-ready roofing built for Arizona heat.',
    differentiator: 'Free storm inspections and photo-backed repair documentation.',
    services: 'Roof replacements, repair, coatings, storm damage, inspections',
    city: 'Phoenix, AZ',
    contact_name: 'Marco Shen',
    phone: '(602) 555-0177',
    email: 'roofs@desertcrestroofing.com',
    years_in_business: 11,
    license_number: 'ROC 334512',
    insurance_status: 'insured',
    service_area: 'Phoenix, Mesa, Chandler, Gilbert',
    emergency_service_available: false,
    preferred_trade: 'roofing',
  },
  electrician: {
    tenant_id: 'mock-electrician-phoenix',
    biz_name: 'Amp Logic Electric',
    tagline: 'Safe, code-compliant electrical work done right.',
    differentiator: 'Flat-rate diagnostics, same-day troubleshooting, and clean job sites.',
    services: 'Panels, EV chargers, lighting, surges, remodels, inspections',
    city: 'Phoenix, AZ',
    contact_name: 'Priya Nair',
    phone: '(602) 555-0123',
    email: 'info@amplogicelectric.com',
    years_in_business: 7,
    license_number: 'ROC 778901',
    insurance_status: 'insured',
    service_area: 'Phoenix and North Phoenix',
    emergency_service_available: true,
    preferred_trade: 'electrical',
  },
  landscaper: {
    tenant_id: 'mock-landscaper-phoenix',
    biz_name: 'Saguaro Greenscapes',
    tagline: 'Desert-smart landscape design and maintenance.',
    differentiator: 'Low-water designs, irrigation optimization, and seasonal cleanup plans.',
    services: 'Design, irrigation, hardscape, cleanup, tree trimming, xeriscaping',
    city: 'Phoenix, AZ',
    contact_name: 'Omar Diaz',
    phone: '(602) 555-0155',
    email: 'hello@saguarogreenscapes.com',
    years_in_business: 6,
    license_number: 'ROC 556789',
    insurance_status: 'insured',
    service_area: 'Phoenix, Paradise Valley, Cave Creek',
    emergency_service_available: false,
    preferred_trade: 'landscaping',
  },
  handyman: {
    tenant_id: 'mock-handyman-phoenix',
    biz_name: 'FixRight Handyman Services',
    tagline: 'Small jobs done right, on time.',
    differentiator: 'One call covers repairs, installs, punch lists, and preventative fixes.',
    services: 'Drywall, painting, fixtures, shelving, door repair, weatherstripping',
    city: 'Phoenix, AZ',
    contact_name: 'Tom Bridges',
    phone: '(602) 555-0181',
    email: 'book@fixrighthandyman.com',
    years_in_business: 4,
    license_number: 'ROC 112233',
    insurance_status: 'insured',
    service_area: 'Phoenix, Laveen, Goodyear',
    emergency_service_available: false,
    preferred_trade: 'handyman',
  },
}

function App() {
  const [site, setSite] = useState<SiteData | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const params = new URLSearchParams(window.location.search)
    const trade = (params.get('trade') || '').toLowerCase()
    const tenantId = params.get('tenant') || ''
    if (trade && MOCK_SITE_DATA[trade]) {
      setSite(MOCK_SITE_DATA[trade])
      setLoading(false)
      return
    }
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
  if (!site) return <div style={{ padding: 24 }}>No site data. Try <code>?trade=hvac</code> for a demo.</div>

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
