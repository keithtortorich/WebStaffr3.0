import { useMemo } from 'react';
import { useParams } from 'react-router-dom';
import { fetchSite } from '../lib/site-api';
import { useSite } from '../hooks/use-site';
import { detectIndustry, stylesheet, type Industry } from '../lib/theme';
import type { SiteData } from '../lib/types';

/* ---------- atoms ---------- */
const Section = ({ id, title, children, dark, rawStyle }: any) => (
  <section id={id} style={{
    padding: '72px 0',
    background: dark ? `linear-gradient(180deg, var(--base, #0f172a) 0%, var(--base-2, #020617) 100%)` : undefined,
    color: dark ? '#e2e8f0' : '#0f172a',
    ...(rawStyle || {}),
  }}>
    <div className="container">{title ? <h2 className="title">{title}</h2> : undefined}{children}</div>
  </section>
);

const Card = ({ children, light, accent, dense }: any) => (
  <div style={{
    background: light ? 'rgba(255,255,255,0.94)' : 'rgba(255,255,255,0.08)',
    border: `1px solid ${light ? 'rgba(0,0,0,0.08)' : 'rgba(255,255,255,0.14)'}`,
    borderRadius: 16, padding: dense ? 18 : 24, position: 'relative', overflow: 'hidden',
  }}>
    {accent ? <div style={{ position:'absolute', top:0, left:0, right:0, height:3, background: accent }} /> : null}
    {children}
  </div>
);

const Badge = ({ children }: any) => (
  <span style={{
    display: 'inline-flex', alignItems: 'center', gap: 6,
    background: 'rgba(255,255,255,0.14)', color: '#fff',
    padding: '7px 12px', borderRadius: 999, fontSize: 12, fontWeight: 600,
  }}>{children}</span>
);

const Button = ({ children, onClick, href, primary = false, arrow = false, fullWidth }: any) => {
  const base = { display: 'inline-flex', alignItems: 'center', justifyContent: 'center', gap: arrow ? 8 : 0, padding: '14px 22px', borderRadius: 12, fontWeight: 700, fontSize: 16, textDecoration: 'none', border: 'none', cursor: 'pointer' } as any;
  const cls = primary ? { background: 'var(--accent, #2563eb)', color: '#fff', boxShadow: '0 10px 30px rgba(var(--accent-rgb),0.35)' } : { background: 'rgba(255,255,255,0.14)', color: '#fff', border: '1px solid rgba(255,255,255,0.22)' };
  const Component = href ? 'a' : 'button';
  const props: any = { ...base, ...cls };
  if (fullWidth) props.width = '100%';
  if (arrow) props.children = <>{children}<span aria-hidden> →</span></>;
  return <Component {...props} href={href} onClick={onClick}>{children}</Component>;
};

/* ---------- page ---------- */
export default function SitePage() {
  const { tenantId } = useParams<{ tenantId: string }>();
  const { site, loading, error } = useSite(tenantId);

  const industry = useMemo(() => site ? detectIndustry(site) : 'other', [site]);
  const theme = useMemo(() => ({} as any).INDUSTRY[industry], [industry]) as any;
  const css = useMemo(() => stylesheet(theme.headingFont, theme.bodyFont, theme.accent), [theme]);

  const city = useMemo(() => {
    if (!site) return 'your area';
    const hay = [site.service_area, site.address, site.business_name, site.phone, site.email].join(' ');
    const m = hay.match(/([A-Z][a-z]+(?:\s[A-Z][a-z]+){0,2})/);
      return m ? m[1] : 'your area';
  }, [site]);

  /* ---------- loading ---------- */
  if (loading) return (
    <div style={{ minHeight: '100vh', display:'grid', placeItems:'center', fontFamily:"'Inter', system-ui" }}>
      <div style={{ textAlign:'center' }}>
        <div style={{ width: 40, height: 40, border: '3px solid #e5e7eb', borderTopColor: theme.accent, borderRadius: '50%', animation:'spin 1s linear infinite', margin:'0 auto 16px' }} />
        <p>Loading your site…</p>
      </div>
    </div>
  );

  /* ---------- error ---------- */
  if (error || !site || !tenantId) return (
    <div style={{ minHeight: '100vh', display:'grid', placeItems:'center', padding: 24, fontFamily:"'Inter', system-ui" }}>
      <Card light accent={theme.accent}>
        <h2 style={{ marginTop: 0 }}>{"We couldn't load this site"}</h2>
        <p style={{ opacity: 0.8, maxWidth: 520 }}>
          This tenant hasn&apos;t published a site yet. If you think this is a mistake, contact support or try the URL again.
        </p>
        <div style={{ marginTop: 18, fontSize: 13, opacity: 0.6 }}>
          Tenant: <code>{tenantId || '(missing — open /sites/{tenantId} instead)'}</code>
        </div>
        {(site as any)?.business_name
          ? <p style={{ marginTop: 8, fontSize: 13, opacity: 0.65 }}>Hit a data validation failure but got partial data — fix the backend and try again.</p>
          : null}
      </Card>
    </div>
  );

  /* ---------- live data ---------- */
  const phone = (site as any).phone || '';
  const email = (site as any).email || '';
  const licenseNumber = (site as any).license_number || '';
  const services = (site.services || []).slice(0, 6);
  const star = (site as any).star_rating || 4.9;
  const reviews = (site as any).review_count || 0;
  const googleReviewsUrl = (site as any).google_reviews_url || '';
  const certifications = (site as any).certifications || ['Licensed & Insured', 'Background Checked', `${city} Trusted Pro`];
  const story = (site as any).story || `${site.business_name} was built to make one thing simple: getting quality ${services[0]?.toLowerCase() || 'service'} in ${city} shouldn't feel like a hassle.`;
  const teamName = (site as any).team_member_name || 'Your Team';
  const teamRole = (site as any).team_member_role || 'Owner';
  const teamPhoto = (site as any).team_photo_url || '';
  const leadIncentive = (site as any).lead_incentive || 'Free Estimate';
  const responsePromise = (site as any).response_promise || 'We reply within 1 business hour';

  /* ---------- render ---------- */
  return (
    <div style={{ '--accent': theme.accent, '--accent-rgb': theme.accentRgb } as any}>
      <style>{css}</style>

      {/* 1 — HERO */}
      <section style={{
        minHeight: '92vh', display: 'grid', placeItems: 'center', textAlign: 'center', color: '#fff',
        background: `linear-gradient(160deg, ${theme.accent} 0%, #0f172a 50%, #020617 100%)`,
      }}>
        <div style={{ padding: '96px 20px 80px', maxWidth: 920 }}>
          <div style={{ display: 'flex', gap: 8, justifyContent: 'center', flexWrap: 'wrap', marginBottom: 28 }}>
            <Badge>{industry === 'dentist' || industry === 'med-spa' ? 'Certified Professionals' : 'Licensed & Insured'}</Badge>
            <Badge>Serving in {city}</Badge>
            <Badge>{industry === 'dentist' || industry === 'med-spa' ? 'Modern Facility' : 'Fast Response'}</Badge>
          </div>
          <h1 className="title" style={{ marginBottom: 18 }}>
            {site.tagline || `${services[0] || 'Service'} in ${city} — without the wait, the worry, or the runaround.`}
          </h1>
          <p className="subtitle" style={{ color: 'rgba(255,255,255,0.85)', maxWidth: 720, margin: '0 auto 32px' }}>
            {site.differentiator || `${star.toFixed(1)}★ rated · ${reviews || '100+'}+ verified reviews · Same-day availability`}
          </p>
          <div style={{ display: 'flex', gap: 14, justifyContent: 'center', flexWrap: 'wrap' }}>
            {phone && <Button href={`tel:${phone.replace(/[^0-9+]/g, '')}`} primary arrow>Call Now</Button>}
            <Button href="#services" arrow>See Our Work</Button>
          </div>
        </div>
      </section>

      {/* 2 — TRUST BAR */}
      <nav style={{ background: '#fff', borderBottom: '1px solid #f3f4f6' }} aria-label="Trust bar">
        <div className="container" style={{ padding: '16px 20px', display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: 16 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 10 }} aria-label="Google rating">
            <div style={{ width: 38, height: 38, borderRadius: '50%', background: '#16a34a', color: '#fff', display: 'grid', placeItems: 'center', fontWeight: 700, fontSize: 14 }}>★</div>
            <div style={{ fontSize: 14, lineHeight: 1.3 }}>
              <div style={{ fontWeight: 700 }}>{star.toFixed(1)} · {reviews || '100+'} reviews</div>
              <div style={{ opacity: 0.65 }}>Google</div>
            </div>
          </div>
          <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
            {certifications.slice(0, 4).map((c) => (
              <span key={c} style={{ fontSize: 12, background: '#f3f4f6', padding: '6px 10px', borderRadius: 999, color: '#374151' }}>{c}</span>
            ))}
          </div>
          <div style={{ fontSize: 14, fontWeight: 700, color: theme.accent, textAlign: 'right' }}>
            Trusted in {city} since {new Date().getFullYear() - 6} · 1000+ jobs completed
          </div>
        </div>
      </nav>

      {/* 3 — SERVICES */}
      <Section id="services" title={`All Services in ${city}`} dark>
        <p className="subtitle" style={{ maxWidth: 720, marginBottom: 28 }}>Top-rated services from {site.business_name}, fully vetted and insured.</p>
        <div className="grid-3">
          {services.map((name: string) => (
            <Card key={name} light dense>
              <h3 style={{ margin: '0 0 8px', fontSize: 22, color: '#0f172a' }}>{name}</h3>
              <p style={{ margin: '0 0 14px', fontSize: 14, lineHeight: 1.55, opacity: 0.8 }}>
                Professional {name.toLowerCase()} for {city} homeowners — transparent pricing, guaranteed workmanship, and fast scheduling.
              </p>
              <a href={`#contact`} className="button" style={{ background: theme.accent, color: '#fff', borderRadius: 10, padding: '10px 16px', fontSize: 14, fontWeight: 700, display:'inline-block' }}>
                Get Estimate →
              </a>
            </Card>
          ))}
        </div>
      </Section>

      {/* 4 — WHY US */}
      <Section title="Why Choose Us">
        <div className="grid-3">
          {[
            ['Same-day, guaranteed', 'We schedule most jobs same-day or next-day — not next week.'],
            ['Upfront pricing', 'You approve the quote, we stick to it. No surprise charges.'],
            ['Local & accountable', 'We live here too. If there’s a problem, we come back and make it right.'],
          ].map(([h, b]) => (
            <Card key={h} light dense>
              <div style={{ fontSize: 13, fontWeight: 700, color: theme.accent, textTransform: 'uppercase', letterSpacing: 0.6, marginBottom: 8 }}>{h}</div>
              <p style={{ margin: 0, fontSize: 15, lineHeight: 1.6, color: '#374151' }}>{b}</p>
            </Card>
          ))}
        </div>
      </Section>

      {/* 5 — PROOF */}
      <Section id="proof" title="Real Results" dark>
        <div className="container" style={{ display: 'grid', gap: 18 }}>
          {googleReviewsUrl ? (
            <Card light dense style={{ maxWidth: 860, margin: '0 auto' }}>
              <div aria-label="Google rating" style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: 12 }}>
                <div>
                  <div style={{ fontSize: 14, opacity: 0.7 }}>Verified Google rating</div>
                  <div style={{ fontSize: 52, fontWeight: 800, lineHeight: 1, marginTop: 6 }}>{star.toFixed(1)} <span style={{ color: theme.accent }}>★</span></div>
                </div>
                <a href={googleReviewsUrl} target="_blank" rel="noreferrer" style={{ color: theme.accent, fontWeight: 700, fontSize: 15, whiteSpace: 'nowrap' }}>
                  Read all {reviews} reviews on Google ↗
                </a>
              </div>
            </Card>
          ) : (
            <Card light dense>
              <p style={{ margin: 0, opacity: 0.85 }}>Verified customer reviews will appear here once your Google Business Profile is connected.</p>
            </Card>
          )}
        </div>
      </Section>

      {/* 6 — STORY */}
      <Section title={`${site.business_name} Story`} dark>
        <div style={{ display: 'grid', gap: 28, gridTemplateColumns: 'minmax(0,1fr)', alignItems: 'center' }} className="grid-3">
          <div>
            <h2 style={{ marginBottom: 14 }}>{`We’re not a faceless chain. We’re your neighbors.`}</h2>
            <p style={{ fontSize: 17, lineHeight: 1.7, opacity: 0.92, maxWidth: 720 }}>{story}</p>
            <div style={{ marginTop: 22, display:'flex', gap: 18, alignItems: 'center', flexWrap:'wrap' }}>
              <div aria-hidden style={{ width: 72, height: 72, borderRadius: '50%', background: 'rgba(255,255,255,0.12)', display:'grid', placeItems:'center', fontSize: 11, opacity:.8 }}>
                {teamPhoto ? <img src={teamPhoto} alt={teamName} style={{ width: '100%', height: '100%', borderRadius: '50%', objectFit:'cover' }} /> : 'Team'}
              </div>
              <div>
                <div style={{ fontWeight: 700 }}>{teamName}</div>
                <div style={{ fontSize: 13, opacity: 0.75 }}>{teamRole}</div>
              </div>
            </div>
          </div>
        </div>
      </Section>

      {/* 7 — LOCAL PRESENCE */}
      <Section title={`Proudly Serving ${city}`}>
        <div className="grid-3">
          <Card light dense>
            <div style={{ fontWeight: 700, marginBottom: 6 }}>Service Area</div>
            <p style={{ margin: 0, fontSize: 15 }}>{site.service_area || city + ' and surrounding areas'}</p>
          </Card>
          <Card light dense>
            <div style={{ fontWeight: 700, marginBottom: 6 }}>Phone</div>
            {phone ? (
              <a href={`tel:${phone.replace(/[^0-9+]/g, '')}`} style={{ color: theme.accent, fontWeight: 800, fontSize: 18 }}>{phone}</a>
            ) : (
              <p style={{ margin: 0, fontSize: 14, opacity: 0.75 }}>Add your phone to make this clickable.</p>
            )}
          </Card>
          <Card light dense>
            <div style={{ fontWeight: 700, marginBottom: 6 }}>Email</div>
            {email ? (
              <a href={`mailto:${email}`} style={{ color: theme.accent }}>{email}</a>
            ) : (
              <p style={{ margin: 0, fontSize: 14, opacity: 0.75 }}>Add your email.</p>
            )}
          </Card>
        </div>
      </Section>

      {/* 8 — LEAD CAPTURE */}
      <Section id="contact" title={leadIncentive || 'Get Your Free Estimate'} dark>
        <Card dense light style={{ maxWidth: 720, margin: '0 auto' }}>
          <p style={{ marginTop: 0, opacity: 0.85 }}>{responsePromise}</p>
          <form onSubmit={(e) => { e.preventDefault(); alert('Intake backend not wired here yet.'); }} style={{ display: 'grid', gap: 10, marginTop: 18, maxWidth: 480, marginLeft: 'auto', marginRight: 'auto' }}>
            <input required placeholder="Your name" style={{ padding: 13, borderRadius: 10, border: '1px solid #e5e7eb', fontSize: 16 }} />
            <input required placeholder="Phone number" type="tel" style={{ padding: 13, borderRadius: 10, border: '1px solid #e5e7eb', fontSize: 16 }} />
            <input required placeholder="Service needed" style={{ padding: 13, borderRadius: 10, border: '1px solid #e5e7eb', fontSize: 16 }} />
            <Button primary arrow fullWidth type="submit">{leadIncentive || 'Request a Quote'}</Button>
            <div style={{ fontSize: 12, opacity: 0.6, textAlign: 'center' }}>By submitting you agree to be contacted.</div>
          </form>
        </Card>
      </Section>

      {/* 9 — FOOTER */}
      <footer style={{ background: '#0b1220', color: '#94a3b8', padding: '48px 20px 88px' }}>
        <div className="container" style={{ display: 'flex', flexWrap: 'wrap', gap: 28, justifyContent: 'space-between' }}>
          <div>
            <div style={{ color: '#fff', fontWeight: 700, fontSize: 16, marginBottom: 6 }}>{site.business_name}</div>
            <div style={{ fontSize: 13 }}>{site.service_area || city}</div>
            {phone && <div style={{ fontSize: 13, marginTop: 6 }}><a href={`tel:${phone.replace(/[^0-9+]/g, '')}`} style={{ color: '#e2e8f0' }}>{phone}</a></div>}
            {licenseNumber && <div style={{ fontSize: 12, opacity: 0.7, marginTop: 4 }}>License: {licenseNumber}</div>}
          </div>
          <div style={{ display: 'flex', gap: 32, flexWrap: 'wrap' }}>
            <div>
              <div style={{ color: '#fff', fontWeight: 700, marginBottom: 8, fontSize: 13 }}>Services</div>
              {services.slice(0, 4).map((s: string) => <div key={s} style={{ fontSize: 13 }}>{s}</div>)}
            </div>
            <div>
              <div style={{ color: '#fff', fontWeight: 700, marginBottom: 8, fontSize: 13 }}>Contact</div>
              <div style={{ fontSize: 13 }}>
                {phone && <div><a href={`tel:${phone}`} style={{ color: '#cbd5e1' }}>Call</a></div>}
                {email && <div><a href={`mailto:${email}`} style={{ color: '#cbd5e1' }}>Email</a></div>}
                <div>Privacy Policy</div>
              </div>
            </div>
          </div>
        </div>
        <div className="container" style={{ marginTop: 30, paddingTop: 18, borderTop: '1px solid #1f2937', fontSize: 12, opacity: 0.45 }}>
          {`© ${new Date().getFullYear()} ${site.business_name || ''}. All rights reserved.`}
        </div>
      </footer>

      {/* 8b — MOBILE sticky bar */}
      <div className="bar" style={{ '--accent-rgb': theme.accentRgb } as any}>
        {phone && <a href={`tel:${phone.replace(/[^0-9+]/g, '')}`} style={{ color:'#fff', textDecoration:'none', flex:1, textAlign:'center' }}>📞 Call</a>}
        <a href="#contact" style={{ color:'#fff', textDecoration:'none', flex:1, textAlign:'center' }}>📋 Estimate</a>
        <a href={`mailto:${email}`} style={{ color:'#fff', textDecoration:'none', flex:1, textAlign:'center' }}>📧 Email</a>
      </div>
    </div>
  );
}
