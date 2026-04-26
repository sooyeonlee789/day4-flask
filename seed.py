import sqlite3

from crawler import MAX_ITEMS, RSS_URL, fetch_rss, parse_items

DATABASE = "blog.db"


def ensure_posts_table(conn: sqlite3.Connection):
    conn.execute(
        """CREATE TABLE IF NOT EXISTS posts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            content TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )"""
    )


def seed_posts_from_rss(conn: sqlite3.Connection) -> int:
    xml_text = fetch_rss(RSS_URL)
    news_items = parse_items(xml_text, MAX_ITEMS)

    existing_titles = {
        row[0] for row in conn.execute("SELECT title FROM posts").fetchall()
    }

    rows_to_insert = []
    for item in news_items:
        title = item["title"].strip()
        if not title or title in existing_titles:
            continue

        content = item["summary"].strip() if item["summary"] else ""
        rows_to_insert.append((title, content))
        existing_titles.add(title)

    if rows_to_insert:
        conn.executemany(
            "INSERT INTO posts (title, content) VALUES (?, ?)",
            rows_to_insert,
        )
        conn.commit()

    return len(rows_to_insert)


def main():
    with sqlite3.connect(DATABASE) as conn:
        ensure_posts_table(conn)
        added_count = seed_posts_from_rss(conn)
    print(f"{added_count}건 추가됨")


if __name__ == "__main__":
    main()
