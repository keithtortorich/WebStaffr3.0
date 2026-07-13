/**
 * Mirrors webstaffr/site_data.py's build_public_site_data() exactly -- that
 * function is the single source of truth for this shape. Don't add a field
 * here that isn't in that function's `data`/`optional_fields`, and don't
 * rename one without checking there first (business_name/biz_name and
 * star_rating/rating_value mismatches here previously broke every
 * generated site's rendering silently -- see CLAUDE.md's 2026-07-13
 * addendum).
 */
export interface SiteData {
  tenant_id: string;
  biz_name: string;
  industry: string;
  service_area: string;
  tagline: string;
  differentiator: string;
  services: string[];
  plan: string;
  phone: string;
  email: string;
  years_in_biz?: number;
  emergency_service?: string;
  gbp_url?: string;
  google_review_link?: string;
  tone?: string;
  pricing_shown?: string;
  promos?: string;
  rating_value?: number;
  review_count?: number;
  certifications?: string[];
  has_before_after?: string;
  testimonials?: string;
  facebook_url?: string;
  instagram_url?: string;
  keywords?: string;
  /**
   * Not sent by the backend today (no source field in
   * intake_submissions/site_data.py) -- referenced defensively in
   * SitePage.tsx with a generic fallback, never real data. Kept optional
   * rather than removed so that copy doesn't need another edit if/when
   * these get real backend support; flagged in CLAUDE.md as a design
   * question (perfect-site principle says omit rather than always show
   * placeholder copy for a field that can never be populated).
   */
  story?: string;
  team_member_name?: string;
  team_member_role?: string;
  team_photo_url?: string;
  lead_incentive?: string;
  response_promise?: string;
}
