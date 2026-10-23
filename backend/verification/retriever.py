import time
import feedparser
from ddgs import DDGS
from concurrent.futures import ThreadPoolExecutor, as_completed

# --- Categorized Multi-Outlet RSS Feeds (Global, Indian English, Hindi, Malayalam, Tamil) ---
CATEGORIZED_FEEDS = {
    "Indian English": {
        "The Hindu": "https://www.thehindu.com/news/national/feeder/default.rss",
        "NDTV News": "https://feeds.feedburner.com/ndtvnews-top-stories",
        "Times of India": "https://timesofindia.indiatimes.com/rssfeedstopstories.cms",
        "Indian Express": "https://indianexpress.com/feed/",
        "Hindustan Times": "https://www.hindustantimes.com/feeds/rss/india-news/rssfeed.xml",
        "News18 India": "https://www.news18.com/commonfeeds/v1/eng/rss/india.xml",
    },
    "Hindi (हिन्दी)": {
        "Aaj Tak": "https://www.aajtak.in/rssfeeds/?id=home",
        "BBC Hindi": "https://feeds.bbci.co.uk/hindi/rss.xml",
        "Amar Ujala": "https://www.amarujala.com/rss/breaking-news.xml",
        "Dainik Jagran": "https://rss.jagran.com/rss/news/national.xml",
        "News18 Hindi": "https://hindi.news18.com/rss/khabar/nation/nation.xml",
    },
    "Malayalam (മലയാളം)": {
        "24 News": "https://www.twentyfournews.com/feed",
        "Janmabhumi": "https://www.janmabhumi.in/feed",
        "DoolNews": "https://www.doolnews.com/feed",
        "Oneindia Malayalam": "https://malayalam.oneindia.com/rss/malayalam-news-fb.xml",
    },
    "Tamil (தமிழ்)": {
        "Thanthi TV": "https://www.thanthitv.com/feed",
        "Polimer News": "https://polimernews.com/feed",
        "News7 Tamil": "https://news7tamil.live/feed",
        "BBC Tamil": "https://feeds.bbci.co.uk/tamil/rss.xml",
        "Oneindia Tamil": "https://tamil.oneindia.com/rss/tamil-news-fb.xml",
    },
    "Global": {
        "BBC News": "http://feeds.bbci.co.uk/news/rss.xml",
        "Reuters": "https://feeds.reuters.com/reuters/topNews",
        "The Guardian": "https://www.theguardian.com/world/rss",
        "NPR News": "https://feeds.npr.org/1001/rss.xml",
        "Al Jazeera": "https://www.aljazeera.com/xml/rss/all.xml",
        "Sky News": "https://feeds.skynews.com/feeds/rss/world.xml",
    }
}

# Flattened lookup for all feeds
RSS_FEEDS = {
    name: url
    for cat_feeds in CATEGORIZED_FEEDS.values()
    for name, url in cat_feeds.items()
}

# Category lookup by outlet name
FEED_CATEGORIES = {
    name: cat
    for cat, cat_feeds in CATEGORIZED_FEEDS.items()
    for name in cat_feeds.keys()
}

# Known credible global and Indian domains for verification weighting
CREDIBLE_DOMAINS = {
    # Global top outlets & fact checkers
    "bbc.com", "bbc.co.uk", "reuters.com", "apnews.com", "theguardian.com",
    "npr.org", "aljazeera.com", "cnn.com", "abcnews.go.com", "cbsnews.com",
    "nytimes.com", "washingtonpost.com", "politico.com", "economist.com",
    "ft.com", "bloomberg.com", "time.com", "theatlantic.com", "usatoday.com",
    "latimes.com", "nbcnews.com", "skynews.com", "dw.com", "france24.com",
    "euronews.com", "independent.co.uk", "telegraph.co.uk", "sciencedaily.com",
    "nature.com", "who.int", "cdc.gov", "nih.gov", "nasa.gov",
    "factcheck.org", "snopes.com", "politifact.com", "fullfact.org",
    # Indian Mainstream & TV Outlets
    "thehindu.com", "ndtv.com", "timesofindia.indiatimes.com", "indiatimes.com",
    "indianexpress.com", "hindustantimes.com", "news18.com", "indiatoday.in",
    "deccanherald.com", "tribuneindia.com", "livemint.com", "business-standard.com",
    # Hindi Outlets
    "aajtak.in", "amarujala.com", "jagran.com", "hindi.news18.com", "navbharattimes.indiatimes.com",
    # Malayalam Outlets
    "twentyfournews.com", "janmabhumi.in", "doolnews.com", "malayalam.oneindia.com",
    "mathrubhumi.com", "manoramaonline.com", "asianetnews.com", "mediaonetv.in",
    # Tamil Outlets
    "thanthitv.com", "polimernews.com", "news7tamil.live", "tamil.oneindia.com",
    "dinamalar.com", "dinamani.com", "vikatan.com",
    # Verified Indian Fact Checkers
    "altnews.in", "boomlive.in", "thequint.com", "vishvasnews.com", "factly.in",
    "newsmobile.in", "thip.media",
}


# Categorized source domain sets
FACT_CHECK_DOMAINS = {
    "altnews.in", "boomlive.in", "thequint.com", "vishvasnews.com", "factly.in",
    "newsmobile.in", "thip.media", "factcheck.org", "snopes.com", "politifact.com", "fullfact.org"
}

REGIONAL_LOCAL_DOMAINS = {
    "aajtak.in", "amarujala.com", "jagran.com", "hindi.news18.com", "navbharattimes.indiatimes.com",
    "twentyfournews.com", "janmabhumi.in", "doolnews.com", "malayalam.oneindia.com",
    "mathrubhumi.com", "manoramaonline.com", "asianetnews.com", "mediaonetv.in",
    "thanthitv.com", "polimernews.com", "news7tamil.live", "tamil.oneindia.com",
    "dinamalar.com", "dinamani.com", "vikatan.com", "deccanherald.com", "tribuneindia.com"
}


def _domain_of(url: str) -> str:
    try:
        from urllib.parse import urlparse
        return urlparse(url).netloc.replace("www.", "")
    except Exception:
        return ""


def _source_type_of(url: str, category: str = "") -> str:
    domain = _domain_of(url)
    if any(fcd in domain for fcd in FACT_CHECK_DOMAINS):
        return "Fact-Checking Agency"
    if any(rld in domain for rld in REGIONAL_LOCAL_DOMAINS) or category in ["Hindi (हिन्दी)", "Malayalam (മലയാളം)", "Tamil (தமிழ்)"]:
        return "Regional / Local Press"
    if any(cd in domain for cd in CREDIBLE_DOMAINS):
        return "National / Global Outlet"
    return "Web / Digital Media"


def _credibility_weight(url: str) -> float:
    domain = _domain_of(url)
    if any(cd in domain for cd in CREDIBLE_DOMAINS):
        return 1.0
    low = {"reddit.com", "twitter.com", "x.com", "facebook.com", "instagram.com", "tiktok.com", "quora.com"}
    if any(ld in domain for ld in low):
        return 0.1
    return 0.5


def _fetch_rss(source_name: str, feed_url: str, claim: str, limit: int = 3) -> list:
    results = []
    try:
        feed = feedparser.parse(feed_url)
        keywords = {w.lower() for w in claim.split() if len(w) > 3}
        category = FEED_CATEGORIES.get(source_name, "General")
        for entry in feed.entries:
            title = entry.get("title", "")
            summary = entry.get("summary", entry.get("description", ""))
            link = entry.get("link", "")
            text = (title + " " + summary).lower()
            if not link or not (summary or title):
                continue
            matched = any(kw in text for kw in keywords) if keywords else True
            if matched:
                results.append({
                    "title": title,
                    "snippet": (summary or title)[:500],
                    "link": link,
                    "source": source_name,
                    "category": category,
                    "source_type": _source_type_of(link, category),
                    "credibility_weight": _credibility_weight(link),
                })
            if len(results) >= limit:
                break
    except Exception as e:
        print(f"[RSS] Error fetching {source_name}: {e}")
    return results


def _fetch_ddg_text(claim: str, max_results: int = 8) -> list:
    results = []
    queries = [
        f"{claim} site:altnews.in OR site:boomlive.in OR site:vishvasnews.com OR site:thequint.com OR site:factcheck.org OR site:snopes.com",
        f"{claim} site:reuters.com OR site:apnews.com OR site:thehindu.com OR site:ndtv.com OR site:indianexpress.com OR site:amarujala.com",
        f"{claim} fact check",
        f"{claim} news",
        claim,
    ]
    try:
        ddg = DDGS()
        for q in queries:
            try:
                raw = ddg.text(q, max_results=max_results)
                if raw:
                    for r in raw:
                        snippet = r.get("body", "")
                        link = r.get("href", "")
                        title = r.get("title", "")
                        if len(snippet) > 40 and link:
                            results.append({
                                "title": title,
                                "snippet": snippet[:500],
                                "link": link,
                                "source": "DuckDuckGo Web",
                                "category": "Web Search",
                                "source_type": _source_type_of(link, "Web Search"),
                                "credibility_weight": _credibility_weight(link),
                            })
                    if results:
                        break
            except Exception:
                time.sleep(0.3)
                continue

    except Exception as e:
        print(f"[DDG Web] Error: {e}")
    return results


def _fetch_ddg_news(claim: str, max_results: int = 8) -> list:
    results = []
    try:
        ddg = DDGS()
        raw = ddg.news(claim, max_results=max_results)
        if raw:
            for r in raw:
                snippet = r.get("body", r.get("excerpt", ""))
                link = r.get("url", r.get("href", ""))
                title = r.get("title", "")
                source = r.get("source", "News")
                if (snippet or title) and link:
                    results.append({
                        "title": title,
                        "snippet": (snippet or title)[:500],
                        "link": link,
                        "source": source,
                        "category": "Live News",
                        "source_type": _source_type_of(link, "Live News"),
                        "credibility_weight": _credibility_weight(link),
                    })

    except Exception as e:
        print(f"[DDG News] Error: {e}")
    return results


def retrieve_sources(claim: str, max_results: int = 10) -> list:
    """
    Fetches fact-checking sources from:
      1. DuckDuckGo news search
      2. DuckDuckGo web search (including Indian & global fact checkers)
      3. RSS feeds from major Indian (English, Hindi, Malayalam, Tamil) and Global news outlets
    Results are deduplicated by URL and sorted by domain credibility.
    """
    print(f"[Retriever] Fetching sources for: {claim}")
    all_sources = []
    with ThreadPoolExecutor(max_workers=20) as executor:
        futures = {
            executor.submit(_fetch_ddg_news, claim, 6): "ddg_news",
            executor.submit(_fetch_ddg_text, claim, 6): "ddg_web",
        }
        for name, url in RSS_FEEDS.items():
            futures[executor.submit(_fetch_rss, name, url, claim, 2)] = f"rss_{name}"

        try:
            for future in as_completed(futures, timeout=4.5):
                try:
                    all_sources.extend(future.result())
                except Exception:
                    pass
        except TimeoutError:
            print("[Retriever] Timeout reached, proceeding with collected sources.")

    # Deduplicate by link
    seen = set()
    unique = []
    for s in all_sources:
        if s["link"] and s["link"] not in seen:
            seen.add(s["link"])
            unique.append(s)

    # Sort: credible sources first, longer snippets second
    unique.sort(key=lambda x: (x["credibility_weight"], len(x["snippet"])), reverse=True)

    final = unique[:max_results]
    print(f"[Retriever] Found {len(final)} unique sources (from {len(all_sources)} total).")
    return final
