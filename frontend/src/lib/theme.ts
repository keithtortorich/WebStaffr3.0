export type Industry = 'contractor'|'restaurant'|'med-spa'|'dentist'|'plumber'|'electrician'|'real-estate'|'law-firm'|'gym'|'other';

export const INDUSTRY: Record<Industry, {
  headingFont: string;
  bodyFont: string;
  vibe: string;
  accent: string;
  accentRgb: string;
}> = {
  contractor: { headingFont:'Oswald', bodyFont:'Inter', vibe:'industrial', accent:'#0f172a', accentRgb:'15,23,42' },
  restaurant: { headingFont:'Playfair Display', bodyFont:'Inter', vibe:'warm', accent:'#7c2d12', accentRgb:'124,45,18' },
  'med-spa': { headingFont:'Cormorant Garamond', bodyFont:'Inter', vibe:'luxury', accent:'#581c87', accentRgb:'88,28,135' },
  dentist: { headingFont:'Outfit', bodyFont:'Inter', vibe:'modern', accent:'#0e7490', accentRgb:'14,116,144' },
  plumber: { headingFont:'Archivo Black', bodyFont:'Inter', vibe:'urgent', accent:'#1d4ed8', accentRgb:'29,78,216' },
  electrician: { headingFont:'Sora', bodyFont:'Inter', vibe:'energetic', accent:'#b45309', accentRgb:'180,83,9' },
  'real-estate': { headingFont:'DM Serif Display', bodyFont:'Inter', vibe:'premium', accent:'#15803d', accentRgb:'21,128,61' },
  'law-firm': { headingFont:'Lora', bodyFont:'Inter', vibe:'serious', accent:'#1e3a8a', accentRgb:'30,58,138' },
  gym: { headingFont:'Bebas Neue', bodyFont:'Inter', vibe:'aggressive', accent:'#991b1b', accentRgb:'153,27,27' },
  other: { headingFont:'Space Grotesk', bodyFont:'Inter', vibe:'modern', accent:'#2563eb', accentRgb:'37,99,235' },
};

export function detectIndustry(site: any): Industry {
  const s = [site?.industry, site?.biz_name, site?.tagline, (site?.services||[]).join(' ')].join(' ').toLowerCase();
  if (/restaurant|food|catering|kitchen|dining/.test(s)) return 'restaurant';
  if (/spa|medspa|med\s*spa|aesthetic|botox|filler|laser/.test(s)) return 'med-spa';
  if (/dentist|dental|orthodont|teeth/.test(s)) return 'dentist';
  if (/plumb|drain|water\s*heater|toilet|pipes/.test(s)) return 'plumber';
  if (/electric|wiring|panel|sparky|EV charger/.test(s)) return 'electrician';
  if (/real\s*estate|realtor|listing|property|broker/.test(s)) return 'real-estate';
  if (/law|attorney|legal|lawyer/.test(s)) return 'law-firm';
  if (/contractor|construction|remodel|roof|hvac|carpenter|handyman/.test(s)) return 'contractor';
  if (/gym|fitness|crossfit|training/.test(s)) return 'gym';
  return 'other';
}

export function stylesheet(hf: string, bf: string, accent: string) {
  const css = `
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    @import url('https://fonts.googleapis.com/css2?family=Oswald:wght@500;700&family=${encodeURIComponent(hf)}:wght@400;500;600;700&family=Inter:wght@400;500;600;700&display=swap');
    *, *::before, *::after { box-sizing: border-box; }
    body { margin: 0; font-family: ${bf}, system-ui, sans-serif; }
    h1,h2,h3,h4 { font-family: ${hf}, ${bf}, sans-serif; }
    a { text-decoration: none; color: inherit; }
    .container { max-width: 1160px; margin: 0 auto; padding: 0 20px; }
    .section { padding: 64px 20px; }
    .title { font-size: clamp(28px, 4vw, 44px); line-height: 1.1; }
    .subtitle { font-size: 18px; line-height: 1.55; opacity: 0.85; margin-top: 12px; }
    .grid-3 { display: grid; gap: 20px; }
    @media (min-width: 760px){ .grid-3 { grid-template-columns: repeat(3, 1fr); } }
    .card { background: rgba(255,255,255,0.08); border: 1px solid rgba(255,255,255,0.14); border-radius: 14px; padding: 20px; }
    .button { display:inline-block; padding: 14px 22px; border-radius: 10px; font-weight: 700; text-decoration: none; }
    .button-primary { background: ${accent}; color: #fff; }
    .button-secondary { background: rgba(255,255,255,0.12); color: #fff; border: 1px solid rgba(255,255,255,0.25); }
    .bar { position: fixed; bottom: 0; left: 0; right: 0; background: rgb(var(--accent-rgb, 15, 23, 42)); color: #fff; display: flex; justify-content: space-around; padding: 12px; z-index: 60; }
    @media (min-width: 768px){ .bar { display: none; } }
  `;
  return css;
}
