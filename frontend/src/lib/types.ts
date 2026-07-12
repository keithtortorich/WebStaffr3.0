export interface SiteData {
  tenant_id: string;
  business_name: string;
  tagline: string;
  differentiator: string;
  services: string[];
  service_area: string;
  phone: string;
  email: string;
  license_number?: string;
  website_url?: string;
  google_place_id?: string;
  google_reviews_url?: string;
  review_count?: number;
  star_rating?: number;
  certifications?: string[];
  story?: string;
  team_member_name?: string;
  team_member_role?: string;
  team_photo_url?: string;
  competitor_names?: string[];
  lead_incentive?: string;
  response_promise?: string;
}
