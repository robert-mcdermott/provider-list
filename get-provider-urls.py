"""
Collect all Fred Hutchinson provider profile URLs via the Elastic App Search API
that powers the provider directory. Saves one URL per line to a text file.
"""

import requests
import sys
import time

# Elastic App Search PROD credentials (public search key from clientlib JS)
ELASTIC_ENDPOINT = "https://fredhutch-prod.ent.us-west-2.aws.found.io"
ENGINE_NAME = "www-site-search"
SEARCH_KEY = "search-d4wmid75w6rn9onstbmpampm"
SEARCH_URL = f"{ELASTIC_ENDPOINT}/api/as/v1/engines/{ENGINE_NAME}/search"

BASE_URL = "https://www.fredhutch.org"
OUTPUT_FILE = "provider-urls.txt"
PAGE_SIZE = 100  # max allowed by Elastic App Search is 100


def search_providers(page_num):
    """Query the Elastic App Search API for one page of providers."""
    headers = {
        "Authorization": f"Bearer {SEARCH_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "query": "",
        "page": {"size": PAGE_SIZE, "current": page_num},
        "filters": {
            "all": [
                {"search_result_type": ["Providers"]}
            ]
        },
        "sort": {"provider_last_name": "asc"},
        "result_fields": {
            "url": {"raw": {}},
            "title": {"raw": {}},
            "search_result_type": {"raw": {}},
        },
    }

    resp = requests.post(SEARCH_URL, headers=headers, json=payload, timeout=30)
    resp.raise_for_status()
    return resp.json()


def build_profile_url(raw_url):
    """Normalize a raw URL value to a full https://www.fredhutch.org URL."""
    if not raw_url:
        return None
    url = raw_url.strip()
    if url.startswith("http"):
        return url
    if url.startswith("/"):
        return BASE_URL + url
    return None


def collect_all_providers():
    """Page through the API and collect every provider URL. Returns sorted list."""
    all_urls = []
    page = 1

    print("Querying Elastic App Search API...")

    # First call to get total count
    data = search_providers(page)
    meta = data.get("meta", {})
    total_results = meta.get("page", {}).get("total_results", 0)
    total_pages = meta.get("page", {}).get("total_pages", 1)
    print(f"  Total providers reported by API: {total_results}")
    print(f"  Total pages (size={PAGE_SIZE}): {total_pages}")

    # Process first page
    for result in data.get("results", []):
        raw = result.get("url", {}).get("raw", "")
        url = build_profile_url(raw)
        if url and "/provider-directory/" in url and url.endswith(".html"):
            all_urls.append(url)

    print(f"  Page {page}/{total_pages}: collected {len(all_urls)} URLs so far")

    # Fetch remaining pages
    for page in range(2, total_pages + 1):
        time.sleep(0.3)
        data = search_providers(page)
        for result in data.get("results", []):
            raw = result.get("url", {}).get("raw", "")
            url = build_profile_url(raw)
            if url and "/provider-directory/" in url and url.endswith(".html"):
                all_urls.append(url)
        print(f"  Page {page}/{total_pages}: collected {len(all_urls)} URLs so far")

    return sorted(set(all_urls))


def main():
    print("=" * 60)
    print("Fred Hutchinson Provider Directory URL Collector")
    print("=" * 60)

    provider_urls = collect_all_providers()

    print(f"\nTotal unique provider URLs collected: {len(provider_urls)}")

    if not provider_urls:
        print("ERROR: No provider URLs found.")
        sys.exit(1)

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        for url in provider_urls:
            f.write(url + "\n")

    print(f"Saved to: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
