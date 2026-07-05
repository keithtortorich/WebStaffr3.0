"""Per-trade presentation hints for the intake form.

Presentation-layer only -- none of this affects the intake_submissions
schema (webstaffr/migrations/0003_intake_submissions.sql), which is the
same for every industry. What varies per trade is: example/placeholder
text shown while filling out the form, and which field-service-management
software options are offered.

Ported from the legacy webstaff repo's intake/intake.html (TRADE_HINTS,
INDUSTRY_SOFTWARE) and builder/site_generator.py (INDUSTRY_PRESETS'
default_services) -- see the CLAUDE.md session addendum for provenance.
Values are illustrative placeholder copy, not real business data.
"""

from __future__ import annotations

from typing import Optional, TypedDict


class TradeHint(TypedDict):
    biz: str
    tagline: str
    differentiator: str
    services: list[str]
    license: str
    keywords: str
    certifications: str


class TradeSoftware(TypedDict):
    label: str
    options: list[str]
    booking_placeholder: str


SUPPORTED_INDUSTRIES: list[str] = [
    "HVAC",
    "Plumber",
    "Electrician",
    "Roofing",
    "Contractor",
    "Restaurant",
    "Med Spa",
    "Dentist",
    "Salon",
    "Other",
]

# Industries that don't map 1:1 to a canonical key above (mirrors
# INDUSTRY_NORMALIZE in the legacy site_generator.py).
INDUSTRY_ALIASES: dict[str, str] = {
    "Plumbing": "Plumber",
    "Electrical": "Electrician",
    "General Contractor": "Contractor",
    "Dental": "Dentist",
    "Salon / Beauty": "Salon",
}

TRADE_HINTS: dict[str, TradeHint] = {
    "HVAC": {
        "biz": "Desert Air HVAC",
        "tagline": "Phoenix's fastest HVAC - same-day service, always.",
        "differentiator": "We're the only HVAC company in Phoenix that guarantees same-day service in writing. No call center, no runaround.",
        "services": ["AC Repair", "AC Installation", "Furnace Repair", "Air Quality / Duct Cleaning", "Emergency HVAC"],
        "license": "ROC 123456 - NATE Certified",
        "keywords": "hvac repair phoenix, ac not cooling, emergency ac repair scottsdale, furnace replacement phoenix, air conditioning tune-up",
        "certifications": "BBB A+, NATE Certified, ACCA Member, EPA 608",
    },
    "Plumber": {
        "biz": "Desert Flow Plumbing",
        "tagline": "Phoenix plumbers on call 24/7 - we fix it right the first time.",
        "differentiator": "Upfront flat-rate pricing before we start any work. No surprise invoices, ever.",
        "services": ["Leak Detection & Repair", "Water Heater Replacement", "Drain Cleaning", "Sewer Line Inspection", "Emergency Plumbing"],
        "license": "ROC 234567",
        "keywords": "plumber phoenix, emergency plumber, water heater replacement scottsdale, drain cleaning phoenix, leak repair",
        "certifications": "Licensed & Bonded, BBB A+, HomeAdvisor Top Rated",
    },
    "Electrician": {
        "biz": "Bright Force Electric",
        "tagline": "Licensed electricians in Phoenix - panel upgrades, rewires, same-day.",
        "differentiator": "Every job is inspected and code-certified before we leave. No shortcuts.",
        "services": ["Panel Upgrades & Replacements", "EV Charger Installation", "Outlet & Switch Repair", "Whole-Home Rewire", "Emergency Electrical"],
        "license": "ROC 345678 - State License CR-11",
        "keywords": "electrician phoenix, panel upgrade scottsdale, ev charger installation, electrical repair phoenix, licensed electrician",
        "certifications": "Licensed & Bonded, BBB A+, NABCEP Certified",
    },
    "Roofing": {
        "biz": "Peak Roofing Solutions",
        "tagline": "Phoenix roofers trusted by 1,200+ homeowners - free inspection, lifetime workmanship.",
        "differentiator": "We're one of the only roofers in the Valley that documents every inspection with photos and a written report - before we quote anything.",
        "services": ["Roof Replacement", "Roof Repair", "Storm Damage Inspection", "Flat Roof Systems", "New Construction Roofing"],
        "license": "ROC 456789 - Licensed & Bonded",
        "keywords": "roofing contractor phoenix, roof replacement scottsdale, storm damage roof repair, flat roof phoenix, free roof inspection",
        "certifications": "Owens Corning Preferred, GAF Master Elite, BBB A+",
    },
    "Contractor": {
        "biz": "Premier Home Solutions",
        "tagline": "Phoenix general contractor - remodels, additions, and repairs done right.",
        "differentiator": "Every project has a dedicated site supervisor on-site daily. You always know who's in charge.",
        "services": ["Kitchen Remodeling", "Bathroom Renovation", "Home Additions", "Deck & Patio Build", "Handyman & Repairs"],
        "license": "ROC 567890 - General Contractor",
        "keywords": "general contractor phoenix, kitchen remodel scottsdale, bathroom renovation, home addition phoenix, contractor near me",
        "certifications": "Licensed ROC, BBB A+, EPA Lead-Safe Certified",
    },
    "Restaurant": {
        "biz": "Mesa Grille & Bar",
        "tagline": "Fresh, local ingredients - great food without the pretense.",
        "differentiator": "Every dish is made to order from scratch. We don't have a freezer full of shortcuts.",
        "services": ["Dine-In", "Takeout & Curbside", "Private Events & Catering", "Happy Hour", "Weekend Brunch"],
        "license": "AZ Food Service License #12345",
        "keywords": "restaurant mesa az, best burgers mesa, happy hour scottsdale, private event catering phoenix, brunch near me",
        "certifications": "Health Dept A Rating, OpenTable Top Pick, Yelp Top Rated",
    },
    "Med Spa": {
        "biz": "Radiance Medical Aesthetics",
        "tagline": "Natural-looking results - expert injectors, zero pressure.",
        "differentiator": "Every treatment plan is designed by a board-certified provider, not a sales coordinator.",
        "services": ["Botox & Dysport", "Dermal Fillers", "Laser Skin Resurfacing", "Hydrafacial", "Body Contouring"],
        "license": "AZ Medical Aesthetics License",
        "keywords": "med spa scottsdale, botox phoenix, lip filler scottsdale, laser hair removal phoenix, hydrafacial near me",
        "certifications": "AACS Member, RealSelf Top Doctor, Board Certified Providers",
    },
    "Dentist": {
        "biz": "Sunrise Family Dentistry",
        "tagline": "Comfortable, modern dental care for the whole family - no wait, no judgment.",
        "differentiator": "We offer same-day emergency appointments and accept most insurance plans.",
        "services": ["Preventive Cleanings", "Teeth Whitening", "Dental Implants", "Invisalign", "Emergency Dental Care"],
        "license": "AZ Dental License #98765",
        "keywords": "dentist phoenix, family dentist scottsdale, teeth whitening phoenix, dental implants, emergency dentist near me",
        "certifications": "ADA Member, BBB A+, Google 4.9 Stars",
    },
    "Salon": {
        "biz": "Luxe Hair Studio",
        "tagline": "Color, cuts, and blowouts - book online, walk out obsessed.",
        "differentiator": "Every stylist is a senior colorist with 10+ years of experience. No junior stylists, ever.",
        "services": ["Haircut & Blowout", "Color & Highlights", "Balayage & Ombre", "Keratin Treatment", "Bridal Party Packages"],
        "license": "AZ Cosmetology License",
        "keywords": "hair salon scottsdale, balayage phoenix, highlights near me, bridal hair scottsdale, best colorist phoenix",
        "certifications": "Redken Elite Salon, NAHA Nominee, Yelp Top Rated",
    },
    "Other": {
        "biz": "Your Business Name",
        "tagline": "Your city's most trusted [service] - [your differentiator here].",
        "differentiator": "Describe the #1 reason a customer should choose you over anyone else in your market.",
        "services": ["Your Top Service", "Your Second Service", "Your Third Service"],
        "license": "License # / Bond # / Certification",
        "keywords": "your service your city, [service] near me, best [service] [city]",
        "certifications": "Your Key Certifications, Awards, Affiliations",
    },
}

TRADE_SOFTWARE: dict[str, TradeSoftware] = {
    "HVAC": {"label": "Do you use a field service management system?", "options": ["ServiceTitan", "Jobber", "Housecall Pro", "ServiceFusion", "Other", "None"], "booking_placeholder": "e.g. ServiceTitan, Calendly, or none"},
    "Plumber": {"label": "Do you use a field service management system?", "options": ["ServiceTitan", "Jobber", "Housecall Pro", "ServiceFusion", "Other", "None"], "booking_placeholder": "e.g. Jobber, ServiceTitan, or none"},
    "Electrician": {"label": "Do you use a field service management system?", "options": ["ServiceTitan", "Jobber", "Housecall Pro", "ServiceFusion", "Other", "None"], "booking_placeholder": "e.g. Jobber, ServiceTitan, or none"},
    "Roofing": {"label": "Do you use a field service management system?", "options": ["JobNimbus", "AccuLynx", "Jobber", "Roofr", "Other", "None"], "booking_placeholder": "e.g. JobNimbus, AccuLynx, or none"},
    "Contractor": {"label": "Do you use a project management system?", "options": ["BuilderTrend", "CoConstruct", "Jobber", "Procore", "Other", "None"], "booking_placeholder": "e.g. BuilderTrend, Jobber, or none"},
    "Salon": {"label": "Do you use a salon booking or management system?", "options": ["Vagaro", "Mindbody", "Fresha", "Booksy", "Square Appointments", "GlossGenius", "Acuity", "Other", "None"], "booking_placeholder": "e.g. Vagaro, Mindbody, Fresha, or none"},
    "Med Spa": {"label": "Do you use a booking or practice management system?", "options": ["Vagaro", "Mindbody", "Patientnow", "Aesthetix", "Square Appointments", "Other", "None"], "booking_placeholder": "e.g. Vagaro, Mindbody, or none"},
    "Restaurant": {"label": "Do you use a POS or reservation system?", "options": ["Toast", "Square for Restaurants", "OpenTable", "Yelp Reservations", "Other", "None"], "booking_placeholder": "e.g. Toast, OpenTable, or none"},
    "Dentist": {"label": "Do you use a practice management system?", "options": ["Dentrix", "Eaglesoft", "Open Dental", "Carestream", "Other", "None"], "booking_placeholder": "e.g. Dentrix, Eaglesoft, or none"},
    "Other": {"label": "Do you use any scheduling or management software?", "options": ["Other", "None"], "booking_placeholder": "e.g. Calendly, or none"},
}


def normalize_industry(industry: str) -> str:
    """Map a free-text/alias industry value to its canonical preset key.
    Unknown industries fall back to 'Other' rather than raising -- intake
    should never hard-fail just because a business picked a trade we don't
    have bespoke copy for yet."""
    canonical = INDUSTRY_ALIASES.get(industry, industry)
    return canonical if canonical in TRADE_HINTS else "Other"


def get_preset(industry: str) -> dict:
    """Returns the combined hint + software preset for an industry, always
    resolvable (falls back to 'Other'). Used by GET /intake/presets/{industry}
    so the Lovable-generated form can adapt placeholder copy and FSM options
    per trade without this backend owning any UI itself."""
    key = normalize_industry(industry)
    return {
        "industry": key,
        "hints": TRADE_HINTS[key],
        "software": TRADE_SOFTWARE.get(key, TRADE_SOFTWARE["Other"]),
    }
