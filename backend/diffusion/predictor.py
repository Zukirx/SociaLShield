import math
import re

# Keywords indicating sensationalism, fear, urgency, or health/safety panic
SENSATIONAL_KEYWORDS = {
    "shocking", "urgent", "must watch", "warning", "deadly", "danger",
    "exposed", "secret", "banned", "leaked", "conspiracy", "alert",
    "breaking", "scam", "poison", "death", "attack", "riot", "viral",
    "miracle", "cure", "illegal", "arrested", "government hiding",
    "hoax", "child lifter", "kidnapper", "organ racket", "curfew", "contaminated",
    "blackout", "toxic", "explosion", "emergency", "quarantine", "lockdown",
    # Hindi
    "खुलासा", "सावधान", "खतरा", "वायरल", "चौंकाने", "जहर", "मौत", "अफवाह", "दंगा", "बच्चा चोर",
    # Malayalam
    "മുന്നറിയിപ്പ്", "ഞെട്ടിക്കുന്ന", "വൈറൽ", "രഹസ്യം", "വിഷം", "മരണം", "ഭീതി", "ഹർത്താൽ",
    # Tamil
    "எச்சரிக்கை", "அதிர்ச்சி", "ரகசியம்", "வைரல்", "விஷம்", "மரணங்கள்", "பயங்கரம்", "வதந்தி",
}

# Keywords indicating local/regional/community focus
LOCAL_KEYWORDS = {
    "local", "village", "town", "district", "panchayat", "corporation", "municipality",
    "hospital", "school", "water", "supply", "electricity", "road", "bridge",
    "collector", "mla", "mp", "police station", "bus", "train", "metro", "chowk",
    "market", "temple", "mosque", "church", "festival", "strike", "hartal", "bandh",
    "bureau", "resident", "colony", "taluk", "ward", "ration", "pipeline",
    "kerala", "tamil nadu", "delhi", "mumbai", "bengaluru", "chennai", "kolkata",
    "kochi", "hyderabad", "lucknow", "patna", "punjab", "up", "bihar", "gujarat",
    "maharashtra", "karnataka", "rajasthan", "bhopal", "indore", "surat", "pune",
    "coimbatore", "madurai", "thrissur", "kozhikode", "thiruvananthapuram",
    # Tamil
    "ஊர்", "மாவட்டம்", "மருத்துவமனை", "கிராமம்", "பள்ளி", "தண்ணீர்",
    # Malayalam
    "പഞ്ചായത്ത്", "ജില്ല", "ആശുപത്രി", "നാട്", "സ്കൂൾ", "കുടിവെള്ളം",
    # Hindi
    "जिला", "गाँव", "इलाका", "अस्पताल", "थाना", "पंचायत", "कलेक्टर", "मोहल्ला", "बिजली", "पानी",
}

REGIONAL_AFFINITIES = {
    "Kerala / Malayalam": {"kerala", "kochi", "thrissur", "kozhikode", "thiruvananthapuram", "malayalam", "പഞ്ചായത്ത്", "ജില്ല", "ആശുപത്രി", "നാട്", "ഹർത്താൽ"},
    "Tamil Nadu / Tamil": {"tamil nadu", "chennai", "coimbatore", "madurai", "tamil", "ஊர்", "மாவட்டம்", "மருத்துவமனை", "கிராமம்"},
    "Hindi Belt & North India": {"delhi", "lucknow", "patna", "up", "bihar", "bhopal", "indore", "punjab", "rajasthan", "जिला", "गाँव", "इलाका", "थाना", "मोहल्ला"},
    "Maharashtra & West": {"mumbai", "pune", "gujarat", "surat", "maharashtra"},
    "Karnataka / Bengaluru": {"bengaluru", "karnataka", "mysore"},
}


def analyze_spread_potential(post) -> dict:
    """
    Comprehensive Diffusion & Spread Forecast Engine:
    1. Social virality velocity (likes, shares, views, platform dynamics)
    2. Spillover risk into small & local news (regional portals, WhatsApp groups, local tabloids)
    3. Mainstream broadcast spillover risk (national TV, prime time, national dailies)
    4. Vulnerable local channels, cascade stages, and timeline forecast
    """
    metrics = getattr(post, "metrics", {}) or {}
    likes = metrics.get("likes", 0)
    shares = metrics.get("shares", 0)
    views = metrics.get("views", 0)
    comments = metrics.get("comments", 0)
    raw_platform = getattr(post, "platform", "news") or "news"
    platform = raw_platform.lower()
    if platform in ["x", "tweet", "twitter"]:
        platform = "twitter"

    text = getattr(post, "text_content", "") or ""
    text_lower = text.lower()
    words = re.findall(r"\w+", text_lower)

    # --- 1. Sensationalism & Local Proximity Index ---
    sensational_hits = sum(1 for w in words if w in SENSATIONAL_KEYWORDS)
    local_hits = sum(1 for w in words if w in LOCAL_KEYWORDS)
    has_caps = sum(1 for c in text if c.isupper()) / max(1, len(text)) > 0.30
    has_exclamation = "!" in text or "🚨" in text or "⚠️" in text or "❗" in text

    sensational_score = min(1.0, (sensational_hits * 0.22) + (0.2 if has_caps else 0.0) + (0.15 if has_exclamation else 0.0))
    local_interest_score = min(1.0, 0.15 + (local_hits * 0.25))

    # Identify Regional Affinity
    detected_regions = []
    for region_name, kw_set in REGIONAL_AFFINITIES.items():
        if any(kw in text_lower for kw in kw_set):
            detected_regions.append(region_name)
    primary_region = detected_regions[0] if detected_regions else "National / General"

    # --- 2. Engagement Velocity & Social Platform Multiplier ---
    platform_multipliers = {
        "instagram": 1.30,   # Reels / short-form visual – highest organic virality
        "twitter": 1.30,     # X/Twitter – rapid text + media resharing
        "facebook": 1.20,    # Community groups, shares, Watch videos
        "youtube": 1.20,     # YouTube Shorts treated at Instagram-level virality
        "reddit": 0.95,
        "news": 0.80,
    }
    plat_mult = platform_multipliers.get(platform, 1.0)

    # Base engagement velocity
    if views > 0:
        engagement_velocity = min(1.0, ((likes * 1.0) + (shares * 3.5) + (comments * 2.0)) / views * 10.0)
    else:
        total_eng = likes + (shares * 2.5) + comments
        engagement_velocity = min(1.0, math.log10(max(1, total_eng + 1)) / 5.0)

    # Author influence
    author_meta = getattr(post, "author_meta", {}) or {}
    followers = author_meta.get("followers", 0)
    verified = author_meta.get("verified", False)
    influence_score = min(1.0, math.log10(max(1, followers + 1)) / 7.0)
    if verified:
        influence_score = min(1.0, influence_score + 0.15)

    # Base diffusion risk (0.0 to 1.0)
    base_diffusion = (engagement_velocity * 0.45) + (influence_score * 0.25) + (sensational_score * 0.30)
    overall_diffusion = round(min(1.0, max(0.05, base_diffusion * plat_mult)), 4)

    # --- 3. Small & Local News Spillover Risk ---
    # Small local newsrooms, regional WhatsApp channels, and vernacular YouTube news stringers
    # have minimal fact-checking capacity. Proximity bias causes explosive local community sharing!
    local_spillover_calc = (
        (overall_diffusion * 0.35) +
        (sensational_score * 0.35) +
        (local_interest_score * 0.30)
    )
    if platform in ["facebook", "instagram", "twitter"]:
        local_spillover_calc *= 1.15  # Social platforms feed directly into local news desks
    local_news_risk = round(min(1.0, max(0.10, local_spillover_calc)), 4)

    # Mainstream national media has strict editorial filters and wire requirements:
    mainstream_calc = (overall_diffusion * 0.55) + (influence_score * 0.35) + (0.10 if verified else 0.0)
    # If it is strictly a local civic rumor, big newsrooms often ignore it while local news catches fire!
    if local_hits > 0 and influence_score < 0.30:
        mainstream_calc *= 0.70
    mainstream_risk = round(min(1.0, max(0.05, mainstream_calc)), 4)

    # Ratio of local risk to big news risk
    small_vs_big_ratio = round(local_news_risk / max(0.05, mainstream_risk), 1)

    # Tiers
    if local_news_risk >= 0.70:
        local_tier = "Critical Local Outbreak"
    elif local_news_risk >= 0.45:
        local_tier = "High Regional Uptake"
    elif local_news_risk >= 0.25:
        local_tier = "Moderate Local Spread"
    else:
        local_tier = "Low Local Impact"

    if mainstream_risk >= 0.70:
        mainstream_tier = "Prime-Time Broadcast Risk"
    elif mainstream_risk >= 0.45:
        mainstream_tier = "National Wire Scrutiny"
    elif mainstream_risk >= 0.25:
        mainstream_tier = "Limited National Interest"
    else:
        mainstream_tier = "Filtered by National Desks"

    if overall_diffusion >= 0.70:
        diffusion_tier = "High Virality"
    elif overall_diffusion >= 0.40:
        diffusion_tier = "Moderate Virality"
    else:
        diffusion_tier = "Low Virality"

    # --- 4. Vulnerable Local Channels at Risk ---
    vulnerable_channels = []
    if local_news_risk >= 0.60:
        vulnerable_channels.append("Hyper-local WhatsApp & Telegram Forwarding Clusters (Family & RWA groups)")
        vulnerable_channels.append("District Vernacular News Portals & City Blogs (Low editorial check)")
        vulnerable_channels.append("Local Community Facebook Groups & Citizen Grievance Pages")
        vulnerable_channels.append("Regional Cable TV & Vernacular YouTube News Stringers")
        vulnerable_channels.append("District Print Dailies & Evening Tabloids (District pages)")
    elif local_news_risk >= 0.35:
        vulnerable_channels.append("Regional WhatsApp Community Groups & Neighborhood Chats")
        vulnerable_channels.append("Hyper-local Facebook Community Pages & Local Alert Channels")
        vulnerable_channels.append("Independent District Digital Journalists & City Stringers")
    else:
        vulnerable_channels.append("Limited to Local Peer Forwarding Groups")
        vulnerable_channels.append("Niche Community Discussion Boards")

    # --- 5. Diffusion Cascade Stages ---
    plat_display = "X (Twitter)" if platform == "twitter" else platform.capitalize()
    cascade_stages = [
        {
            "stage": f"{plat_display} Origin",
            "level": round(min(100, max(30, int(overall_diffusion * 100))), 1),
            "status": "Active Seeding",
            "description": f"Direct peer-to-peer engagement, story reshares, and algorithmic feeds on {plat_display}."
        },
        {
            "stage": "WhatsApp & Dark Social Networks",
            "level": round(min(100, max(20, int(local_news_risk * 96))), 1),
            "status": "High Amplification" if local_news_risk > 0.5 else "Moderate Spread",
            "description": "Forwarding across district family groups, resident associations, and dark-social chat loops."
        },
        {
            "stage": "Small & Local News Portals",
            "level": round(min(100, max(15, int(local_news_risk * 88))), 1),
            "status": "Imminent Pickup" if local_news_risk > 0.6 else "Watching",
            "description": "District-level digital media, vernacular aggregators, city blogs, and local stringer journalists."
        },
        {
            "stage": "Mainstream TV & National Press",
            "level": round(min(100, max(5, int(mainstream_risk * 78))), 1),
            "status": "Low Probability" if mainstream_risk < 0.4 else "High Scrutiny",
            "description": "National prime-time broadcasts, state bureaus, and mainstream news fact-checking desks."
        }
    ]

    # --- 6. Timeline Forecast ---
    timeline_forecast = [
        {"window": "0 – 2 Hours", "stage": "Social Echo Chamber", "channels": f"{plat_display} Feeds & Stories", "reach": "Peer Network"},
        {"window": "2 – 6 Hours", "stage": "Dark Social Spread", "channels": "WhatsApp Status & Community Groups", "reach": "District Level"},
        {"window": "6 – 12 Hours", "stage": "Local News Uptake", "channels": "District News Portals & City Blogs", "reach": "Multi-District"},
        {"window": "12 – 24+ Hours", "stage": "Regional Press / TV", "channels": "Local Cable TV & State Dailies", "reach": "State / National"},
    ]

    # --- 7. Key Triggers Detected ---
    triggers = []
    if sensational_hits > 0 or has_exclamation:
        triggers.append(f"Sensational emotional framing detected ({sensational_hits} alert triggers)")
    if local_hits > 0:
        triggers.append(f"High local/community proximity appeal ({local_hits} regional keywords flagged)")
    if platform in ["instagram", "twitter", "facebook"]:
        triggers.append(f"High viral multiplier driven by {plat_display} share-to-view dynamics")
    if shares > 50 or likes > 100:
        triggers.append("Rapid reshare velocity accelerating algorithmic recommendation")
    if not triggers:
        triggers.append("Standard social communication flow without localized emergency triggers")

    # --- 8. Containment Advisory for Local Authorities ---
    if local_news_risk >= 0.60:
        containment_advisory = "CRITICAL: Issue official clarification via District Magistrate / City Police social handles immediately. Alert regional WhatsApp community admins to halt forward loops before evening district tabloids print."
    elif local_news_risk >= 0.35:
        containment_advisory = "MODERATE: Monitor regional community forums and request fact-check tagging on local Facebook pages and city aggregators."
    else:
        containment_advisory = "LOW: Routine monitoring. No emergency local media advisory required."

    return {
        "score": overall_diffusion,
        "tier": diffusion_tier,
        "local_news_risk": local_news_risk,
        "local_news_tier": local_tier,
        "mainstream_news_risk": mainstream_risk,
        "mainstream_news_tier": mainstream_tier,
        "small_vs_big_ratio": small_vs_big_ratio,
        "sensational_score": round(sensational_score, 2),
        "local_interest_score": round(local_interest_score, 2),
        "platform": platform,
        "primary_region": primary_region,
        "vulnerable_channels": vulnerable_channels,
        "cascade_stages": cascade_stages,
        "timeline_forecast": timeline_forecast,
        "key_triggers": triggers,
        "containment_advisory": containment_advisory
    }


def calculate_diffusion_risk(post) -> float:
    """
    Legacy wrapper returning float score for existing ensemble & profiler pipelines.
    """
    analysis = analyze_spread_potential(post)
    return analysis["score"]

