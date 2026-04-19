import requests
from bs4 import BeautifulSoup
import random
from time import sleep
import json
from urllib.parse import urlencode, urljoin
from datetime import datetime

ALL_ARTICLES_LINKS = []

# ─── Shared Headers ───────────────────────────────────────────────────────────
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:137.0) Gecko/20100101 Firefox/137.0",
    "Content-Type": "application/json"
}

# ─── 1. UPSTOX ────────────────────────────────────────────────────────────────
def scrape_upstox():
    print("Processing Upstox Started")
    found = False
    page = 1
    while not found:
        url = f"https://service.upstox.com/content/open/v5/news/sub-category/news/list/market-news/stocks?page=1&pageSize=100"
        response = requests.get(url, headers=headers)
        data = response.json()
        if not data.get('data'):
            break
        for item in data['data']:
            if 'stocks to watch' in item['headline'].lower():
                print(item['headline'])
                print(item['contentUrl'])
                found = True
                ALL_ARTICLES_LINKS.append(item['contentUrl'])
                break
        page += 1
    print("Processing Upstox Done")


# ─── 2. MINT ──────────────────────────────────────────────────────────────────
def scrape_mint():
    print("Processing Mint Started")
    page = 0
    found = False
    base_url = "https://www.livemint.com"
    url_template = "https://www.livemint.com/listing/subsection/market~stock-market-news/{}"
    mint_headers = {"User-Agent": "Mozilla/5.0"}

    while not found:
        url = url_template.format(page)
        response = requests.get(url, headers=mint_headers)

        if response.status_code != 200:
            print(f"Error fetching page {page}: {response.status_code}")
            break

        soup = BeautifulSoup(response.text, "html.parser")
        articles = soup.select("div.impression-candidate")

        if not articles:
            print("No more articles found.")
            break

        for article in articles:
            headline_tag = article.select_one("h2.headline a")
            headline = headline_tag.get_text(strip=True) if headline_tag else "N/A"

            time_tag = article.select_one('span[id^="tListBox_"]')
            updated_datetime = time_tag.get("data-updatedtime") if time_tag else "N/A"
            expanded_datetime = time_tag.get("data-expandedtime") if time_tag else "N/A"

            meta_url_tag = article.select_one('meta[itemprop="url"]')
            main_url = meta_url_tag.get("content") if meta_url_tag else "N/A"

            if main_url == "N/A" and headline_tag:
                href = headline_tag.get("href")
                if href:
                    main_url = base_url + href if href.startswith("/") else href

            if "stocks to watch" in headline.lower():
                print("Headline:", headline)
                print("DateTime (ISO):", updated_datetime)
                print("DateTime (Readable):", expanded_datetime)
                print("Main URL:", main_url)
                ALL_ARTICLES_LINKS.append(main_url)
                print("-" * 100)
                found = True
                break

        page += 1
    print("Processing Mint Done")


# ─── 3. MONEYCONTROL ──────────────────────────────────────────────────────────
def scrape_moneycontrol():
    print("Processing Moneycontrol Started")
    scrape_token = "f4044f874fe94c23b94c2c27bd9bfd7272df77600aa"

    for i in range(1, 5):
        try:
            print(f"\nFetching page {i} via Scrape.do...")
            target_url = f"https://www.moneycontrol.com/news/business/markets/page-{i}/"
            from urllib.parse import quote
            encoded_url = quote(target_url)

            api_url = (
                f"http://api.scrape.do/?url={encoded_url}"
                f"&token={scrape_token}"
                f"&super=true&regionalGeoCode=asia"
            )

            response = requests.get(api_url, timeout=15)
            print(f"Page Status Code: {response.status_code}")

            if response.status_code != 200:
                print("Failed to fetch page:", response.status_code)
                break

            soup = BeautifulSoup(response.text, 'html.parser')
            news_items = soup.select('ul#cagetory li.clearfix[id^="newslist-"]')

            found_result = False

            for item in news_items:
                heading_element = item.find('h2')
                if not heading_element:
                    continue

                heading = heading_element.get_text(strip=True)
                time_element = item.find('span', class_=lambda x: x and 'time' in x.lower())
                time_text = time_element.get_text(strip=True) if time_element else 'Today'

                link_tag = item.find('a', href=True)
                full_url = link_tag['href'] if link_tag else target_url

                if 'stocks to watch' in heading.lower():
                    found_result = True
                    print("Found matching news:")
                    print("Headline:", heading)
                    print("Time:", time_text)
                    print("URL:", full_url)
                    ALL_ARTICLES_LINKS.append(full_url)
                    print("-" * 100)
                    break

            if found_result:
                break

            sleep(1)

        except Exception as e:
            print("Error:", e)

    print("Processing Moneycontrol Done")


# ─── 4. CNBCTV18 ──────────────────────────────────────────────────────────────
def scrape_cnbctv18():
    print("Processing CNBCTV18 Started")
    base_url = 'https://www.cnbctv18.com'
    url = 'https://api-en.cnbctv18.com/nodeapi/v1/cne/get-article-list?count=15&offset=0&fields=story_id,display_headline,post_type,timetoread,weburl_r,created_at,updated_at,images,categories&filter={%22tags.slug%22:%22stocks-to-watch%22}&sortOrder=desc&sortBy=updated_at'
    response = requests.get(url, headers={'Accept': 'application/json'})
    i = response.json()['data'][0]
    print(i['created_at'])
    print(i['display_headline'])
    final_url = base_url + i['weburl_r']
    print(final_url)
    ALL_ARTICLES_LINKS.append(final_url)
    print("Processing CNBCTV18 Done")


# ─── 5. BUSINESS STANDARD ─────────────────────────────────────────────────────
def scrape_business_standard():
    print("Processing Business Standard Started")

    bs_headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:149.0) Gecko/20100101 Firefox/149.0",
        "Referer": "https://www.business-standard.com/",
    }

    def get_url(api_page=1):
        ALPHA = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
        block = (api_page - 1) // 4
        token2 = f"9{ALPHA[(3 + block) % 26]}"
        cycle = [23, 25, 1, 3]
        pos = min((api_page - 1), 3)
        token63 = f"9{ALPHA[cycle[pos]]}"
        ld = (f"9W{token2}9B9X5I935K545B5M5O5W5Z5G5q5Z5M545B5Q5W5V5w5L"
              f"939F939W9V9B9V9W939R935X545O5M939F9V9R935T5Q5U5Q5B939F"
              f"9X9W9R935W5N5N5A5M5B939F{token63}9V855J5A9X9A9A5h")
        return f"https://apibs.business-standard.com/article/list?listData={ld}"

    all_matches = []

    for page in range(1, 6):
        print(f"Checking page {page}...")
        try:
            resp = requests.get(get_url(api_page=page), headers=bs_headers, timeout=10)
            if resp.status_code != 200:
                print(f"Status {resp.status_code} — skipping")
                continue
            rows = resp.json()['data']['rows']
            matches = [r for r in rows if 'stocks to watch' in r['heading1'].lower()]
            print(f"Found {len(matches)} match(es) on page {page}")
            all_matches.extend(matches)
        except Exception as e:
            print(f"Error: {e}")

    if all_matches:
        latest = max(all_matches, key=lambda x: x['published_date'])
        print(f"\nLatest 'Stocks to Watch' article:")
        print(f"{datetime.fromtimestamp(latest['published_date']).strftime('%d %b %Y %I:%M %p')}")
        print(f"{latest['heading1']}")
        bs_url = f"https://www.business-standard.com{latest['article_url']}"
        print(bs_url)
        ALL_ARTICLES_LINKS.append(bs_url)
    else:
        print("Not found in 5 pages")

    print("Processing Business Standard Done")


# ─── 6. NDTV PROFIT ───────────────────────────────────────────────────────────
def scrape_ndtv_profit():
    print("Processing NDTV Profit Started")

    BASE_URL = "https://www.ndtvprofit.com/profit/article-load-more/page/{page}/category/market-news"
    START_PAGE = 0
    END_PAGE = 5
    link_list_ndtv = []

    ndtv_headers = {
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Encoding": "gzip, deflate, br, zstd",
        "Accept-Language": "en-US,en;q=0.9",
        "Alt-Used": "www.ndtvprofit.com",
        "Connection": "keep-alive",
        "Host": "www.ndtvprofit.com",
        "Referer": "https://www.ndtvprofit.com/",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "same-origin",
        "Sec-Fetch-User": "?1",
        "Upgrade-Insecure-Requests": "1",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:149.0) Gecko/20100101 Firefox/149.0"
    }

    def scrape_page(page_num):
        url = BASE_URL.format(page=page_num)
        response = requests.get(url, headers=ndtv_headers, timeout=30)
        print(f"Page {page_num} → Status: {response.status_code}")

        if response.status_code != 200:
            print(f"Skipping page {page_num}")
            return []

        soup = BeautifulSoup(response.text, "html.parser")
        articles = soup.find_all("li", class_="NwsLstPg-a-li")

        results = []
        for article in articles:
            title_tag = article.find("a", class_="NwsLstPg_ttl")
            title = title_tag.get_text(strip=True) if title_tag else "N/A"
            url = title_tag["href"] if title_tag and title_tag.has_attr("href") else "N/A"

            desc_tag = article.find("p", class_="NwsLstPg_txt")
            description = desc_tag.get_text(strip=True) if desc_tag else "N/A"

            img_tag = article.find("img", class_="NwsLstPg_img-full")
            image_url = img_tag["src"] if img_tag and img_tag.has_attr("src") else "N/A"

            meta_items = article.find_all("li", class_="NwsLstPg_pst_li")
            date = meta_items[0].get_text(strip=True) if len(meta_items) > 0 else "N/A"
            author = meta_items[1].get_text(strip=True) if len(meta_items) > 1 else "N/A"

            results.append({
                "title": title,
                "url": url,
                "description": description,
                "date": date,
                "author": author,
                "image_url": image_url,
                "page": page_num,
            })

        return results

    all_articles = []
    for page in range(START_PAGE, END_PAGE + 1):
        articles = scrape_page(page)
        all_articles.extend(articles)
        print(f"  → {len(articles)} articles found")

    print(f"\nTotal articles scraped: {len(all_articles)}")

    keywords = ["stocks to watch", "stocks to buy"]
    filtered = [a for a in all_articles if any(kw in a["title"].lower() for kw in keywords)]

    print(f"Found {len(filtered)} articles:\n")
    for i, a in enumerate(filtered, 1):
        print(f"{i}. {a['title']}")
        print(f"   Date: {a['date']} | Author: {a['author']}")
        print(f"   URL : {a['url']}\n")
        link_list_ndtv.append(a['url'])

    ALL_ARTICLES_LINKS.extend(link_list_ndtv)
    print("Processing NDTV Profit Done")


# ─── 7. BUSINESS TODAY ────────────────────────────────────────────────────────
def scrape_business_today():
    print("Processing Business Today Started")

    DATE_START = ""
    DATE_END = ""
    DATE_RANGE = ""

    QUERIES = [
        "stocks to buy",
        "stocks to watch",
        "stocks in news",
    ]

    LANG = "en"
    SITE = "bt"
    CTYPE = "all"
    RTYPE = "undefined"
    SORT_BY = "createddatetime"
    SORT_ORDER = "desc"
    SIZE = 10
    FROM = 0
    TEMPLATE = "output_bt_company"
    bt_links = []

    bt_headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:149.0) Gecko/20100101 Firefox/149.0",
        "Accept": "application/json, text/html, */*",
        "Accept-Language": "en-US,en;q=0.9",
        "Accept-Encoding": "gzip, deflate, br",
        "Referer": "https://www.businesstoday.in/",
        "Connection": "keep-alive",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "same-origin",
        "Upgrade-Insecure-Requests": "1",
    }

    BASE_URL = "https://www.businesstoday.in/api/loadmoredata"

    def is_target_article(article, query):
        title = article.get("title_short", "").strip().lower()
        return query.lower() in title

    def fetch_articles(query):
        inner_params = {
            "q": query,
            "lang": LANG,
            "site": SITE,
            "ctype": CTYPE,
            "rtype": RTYPE,
            "datestart": DATE_START,
            "dateend": DATE_END,
            "daterange": DATE_RANGE,
            "sr": SORT_BY,
            "sro": SORT_ORDER,
            "size": SIZE,
            "template": TEMPLATE,
        }
        api_route = "groupsearchlist?" + urlencode(inner_params)
        outer_params = {
            "apiRoute": api_route,
            "size": SIZE,
            "isFrom": "true",
            "from": FROM,
        }
        response = requests.get(BASE_URL, params=outer_params, headers=bt_headers, timeout=30)
        response.raise_for_status()
        return response.json()

    def extract_filtered_articles(data, query):
        articles = data.get("data", {}).get("content", [])
        return [article for article in articles if is_target_article(article, query)]

    def get_latest_date(all_results):
        all_dates = []
        for articles in all_results.values():
            for article in articles:
                dt = article.get("datetime_published", "").strip()
                if dt:
                    all_dates.append(dt.split(" ")[0])
        return max(all_dates) if all_dates else None

    def filter_latest_date_articles(all_results, latest_date):
        latest_results = {}
        for query, articles in all_results.items():
            latest_results[query] = [
                article for article in articles
                if article.get("datetime_published", "").split(" ")[0] == latest_date
            ]
        return latest_results

    all_results = {}

    for query in QUERIES:
        try:
            data = fetch_articles(query)
            filtered_articles = extract_filtered_articles(data, query)
            all_results[query] = filtered_articles
        except requests.RequestException as e:
            print(f"Request failed for query '{query}': {e}")
            all_results[query] = []
        except json.JSONDecodeError:
            print(f"Response is not valid JSON for query '{query}'.")
            all_results[query] = []

    latest_date = get_latest_date(all_results)

    if not latest_date:
        print("No articles found.")
        print("Processing Business Today Done")
        return

    print(f"\nLATEST DATE FOUND: {latest_date}")

    latest_results = filter_latest_date_articles(all_results, latest_date)

    for query in QUERIES:
        filtered_articles = latest_results.get(query, [])
        print(f"\nQUERY: {query}")
        if not filtered_articles:
            print("No matching latest-date articles found.")
            continue
        for i, article in enumerate(filtered_articles, 1):
            title = article.get("title_short", "N/A")
            url = article.get("share_link_url", "N/A")
            date = article.get("datetime_published", "N/A")
            print(f"{i}. [{date}] {title}")
            print(f"   URL: {url}\n")
            bt_links.append(url)

    ALL_ARTICLES_LINKS.extend(bt_links)
    print("Processing Business Today Done")


# ─── 8. ECONOMIC TIMES ────────────────────────────────────────────────────────
def scrape_economic_times():
    print("Processing Economic Times Started")

    url_template = "https://economictimes.indiatimes.com/lazyloadlistnew.cms?msid=2146843&curpg={}&img=0"
    max_pages = 10
    et_base_url = "https://economictimes.indiatimes.com"

    user_agents = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0"
    ]

    def get_headers():
        return {
            "User-Agent": random.choice(user_agents),
            "Accept-Language": "en-US,en;q=0.5",
            "Referer": "https://economictimes.indiatimes.com/"
        }

    def get_article_content(article_url):
        try:
            sleep(random.uniform(1, 2))
            response = requests.get(article_url, headers=get_headers(), timeout=20)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, "html.parser")

            content_selectors = [
                "div.artText",
                "div.Normal",
                "div.article_wrap",
                "div.content1",
                "div.story_content",
                "div[data-articlebody='1']"
            ]

            content_div = None
            for selector in content_selectors:
                content_div = soup.select_one(selector)
                if content_div:
                    break

            if content_div:
                paragraphs = content_div.find_all("p")
            else:
                paragraphs = soup.find_all("p")

            article_text = []
            for p in paragraphs:
                text = p.get_text(" ", strip=True)
                if text and len(text) > 30:
                    article_text.append(text)

            return "\n".join(article_text) if article_text else "No content found"

        except Exception as e:
            return f"Error extracting article content: {e}"

    found_any = False

    for page in range(0, max_pages + 1):
        try:
            sleep(random.uniform(1, 3))
            url = url_template.format(page)
            response = requests.get(url, headers=get_headers(), timeout=15)
            response.raise_for_status()

            if "text/html" not in response.headers.get("Content-Type", ""):
                continue

            soup = BeautifulSoup(response.content, "html.parser")
            story_divs = (
                soup.find_all("div", class_="eachStory")
                or soup.find_all("div", class_=lambda x: x and "story" in x.lower())
            )

            if not story_divs:
                print(f"No articles found on page {page}")
                break

            for story in story_divs:
                h3 = story.find("h3") or story.find("h2") or story.find("h4")
                if not h3:
                    continue

                h3_text = h3.get_text(strip=True)

                time_tag = (
                    story.find("time", class_="date-format")
                    or story.find("time", class_=lambda x: x and "date" in x.lower())
                    or story.find("span", class_=lambda x: x and "date" in x.lower())
                )

                datetime_value = (
                    time_tag["data-time"] if time_tag and time_tag.has_attr("data-time")
                    else time_tag.get_text(strip=True) if time_tag
                    else "Today"
                )

                if any(
                    phrase in h3_text.lower()
                    for phrase in ["stocks in news", "stocks to watch", "stocks in focus", "shares to watch"]
                ):
                    found_any = True

                    a_tag = story.find("a", href=True)
                    article_url = urljoin(et_base_url, a_tag["href"]) if a_tag else None

                    print("=" * 120)
                    print("DATE:", datetime_value)
                    print("TITLE:", h3_text)
                    print("URL:", article_url)
                    ALL_ARTICLES_LINKS.append(article_url)

                    if article_url:
                        content = get_article_content(article_url)
                        print("\nCONTENT:\n")
                        print(content)
                    else:
                        print("\nNo article URL found")

                    print("=" * 120)
                    break

            if found_any:
                break

        except requests.exceptions.RequestException as e:
            print(f"Error fetching page {page}: {str(e)[:100]}...")
            continue
        except Exception as e:
            print(f"Unexpected error on page {page}: {str(e)[:100]}...")
            continue

    if not found_any:
        print(f"No article found with target phrases after {max_pages} pages")

    print("Processing Economic Times Done")


# ─── MAIN FUNCTION ────────────────────────────────────────────────────────────
def run_all_scrapers():
    global ALL_ARTICLES_LINKS
    ALL_ARTICLES_LINKS = []

    scrape_upstox()
    scrape_mint()
    scrape_moneycontrol()
    scrape_cnbctv18()
    scrape_business_standard()
    scrape_ndtv_profit()
    scrape_business_today()
    scrape_economic_times()

    print("\n" + "=" * 60)
    print(f"Total links collected: {len(ALL_ARTICLES_LINKS)}")
    for idx, link in enumerate(ALL_ARTICLES_LINKS, 1):
        print(f"{idx}. {link}")
    print("=" * 60)

    return ALL_ARTICLES_LINKS
