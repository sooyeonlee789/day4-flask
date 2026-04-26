import sys
import xml.etree.ElementTree as ET

import requests
from bs4 import BeautifulSoup

RSS_URL = "https://news.google.com/rss?hl=ko&gl=KR&ceid=KR:ko"
MAX_ITEMS = 10


def configure_stdout_encoding():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")


def fetch_rss(url: str) -> str:
    response = requests.get(url, timeout=10)
    response.raise_for_status()
    return response.text


def parse_items(xml_text: str, limit: int = MAX_ITEMS):
    root = ET.fromstring(xml_text)
    items = []

    for item in root.findall("./channel/item")[:limit]:
        title = item.findtext("title", default="N/A").strip() or "N/A"
        summary_raw = item.findtext("description", default="N/A")
        summary = BeautifulSoup(summary_raw, "html.parser").get_text(" ", strip=True) if summary_raw else "N/A"
        link = item.findtext("link", default="N/A").strip() or "N/A"
        pub_date = item.findtext("pubDate", default="N/A").strip() or "N/A"

        items.append(
            {
                "title": title,
                "summary": summary,
                "link": link,
                "pub_date": pub_date,
            }
        )

    return items


def print_items(items):
    if not items:
        print("가져온 뉴스가 없습니다.")
        return

    print(f"구글 뉴스 한국어 RSS 상위 {len(items)}건")
    print("=" * 80)

    for idx, news in enumerate(items, start=1):
        print(f"[{idx}] {news['title']}")
        print(f"요약: {news['summary']}")
        print(f"링크: {news['link']}")
        print(f"발행시간: {news['pub_date']}")
        print("-" * 80)


def main():
    configure_stdout_encoding()
    try:
        xml_text = fetch_rss(RSS_URL)
        items = parse_items(xml_text, MAX_ITEMS)
        print_items(items)
    except requests.RequestException as e:
        print(f"RSS 요청 중 오류가 발생했습니다: {e}")
    except ET.ParseError as e:
        print(f"RSS 파싱 중 오류가 발생했습니다: {e}")


if __name__ == "__main__":
    main()
