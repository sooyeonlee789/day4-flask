import sqlite3
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, g

app = Flask(__name__)
DATABASE = "blog.db"
MIN_POST_COUNT = 124


def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(DATABASE)
        g.db.row_factory = sqlite3.Row
    return g.db


@app.teardown_appcontext
def close_db(exc):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def seed_posts(db):
    current_count = db.execute("SELECT COUNT(*) FROM posts").fetchone()[0]
    if current_count >= MIN_POST_COUNT:
        return

    missing = MIN_POST_COUNT - current_count
    rows = [
        (f"샘플 게시글 {current_count + i}", f"자동 생성된 샘플 콘텐츠 {current_count + i}")
        for i in range(1, missing + 1)
    ]
    db.executemany("INSERT INTO posts (title, content) VALUES (?, ?)", rows)
    db.commit()


def init_db():
    db = get_db()
    db.execute(
        """CREATE TABLE IF NOT EXISTS posts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            content TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )"""
    )
    db.commit()
    seed_posts(db)


@app.before_request
def ensure_db():
    if not hasattr(app, "_db_initialized"):
        init_db()
        app._db_initialized = True


@app.route("/")
def post_list():
    db = get_db()
    page = request.args.get("page", default=1, type=int)
    query = request.args.get("q", default="", type=str).strip()
    sort = request.args.get("sort", default="latest", type=str)
    if page < 1:
        page = 1

    sort_orders = {
        "latest": "created_at DESC, id DESC",
        "oldest": "created_at ASC, id ASC",
        "title": "title COLLATE NOCASE ASC, id ASC",
    }
    if sort not in sort_orders:
        sort = "latest"
    order_by = sort_orders[sort]

    per_page = 10
    if query:
        like_query = f"%{query}%"
        total_count = db.execute(
            "SELECT COUNT(*) FROM posts WHERE title LIKE ? OR content LIKE ?",
            (like_query, like_query),
        ).fetchone()[0]
    else:
        total_count = db.execute("SELECT COUNT(*) FROM posts").fetchone()[0]

    total_pages = max(1, (total_count + per_page - 1) // per_page)
    if page > total_pages:
        page = total_pages

    offset = (page - 1) * per_page
    if query:
        like_query = f"%{query}%"
        posts = db.execute(
            f"SELECT * FROM posts WHERE title LIKE ? OR content LIKE ? ORDER BY {order_by} LIMIT ? OFFSET ?",
            (like_query, like_query, per_page, offset),
        ).fetchall()
    else:
        posts = db.execute(
            f"SELECT * FROM posts ORDER BY {order_by} LIMIT ? OFFSET ?",
            (per_page, offset),
        ).fetchall()

    return render_template(
        "list.html",
        posts=posts,
        page=page,
        total_pages=total_pages,
        total_count=total_count,
        query=query,
        sort=sort,
    )


@app.route("/post/<int:post_id>")
def post_detail(post_id):
    db = get_db()
    post = db.execute("SELECT * FROM posts WHERE id = ?", (post_id,)).fetchone()
    if not post:
        return "게시글을 찾을 수 없습니다.", 404
    return render_template("detail.html", post=post)


@app.route("/write", methods=["GET", "POST"])
def post_write():
    if request.method == "POST":
        db = get_db()
        db.execute(
            "INSERT INTO posts (title, content) VALUES (?, ?)",
            (request.form["title"], request.form["content"]),
        )
        db.commit()
        post_id = db.execute("SELECT last_insert_rowid()").fetchone()[0]
        return redirect(url_for("post_detail", post_id=post_id))
    return render_template("write.html")


@app.route("/post/<int:post_id>/edit", methods=["GET", "POST"])
def post_edit(post_id):
    db = get_db()
    post = db.execute("SELECT * FROM posts WHERE id = ?", (post_id,)).fetchone()
    if not post:
        return "게시글을 찾을 수 없습니다.", 404
    if request.method == "POST":
        db.execute(
            "UPDATE posts SET title = ?, content = ? WHERE id = ?",
            (request.form["title"], request.form["content"], post_id),
        )
        db.commit()
        return redirect(url_for("post_detail", post_id=post_id))
    return render_template("write.html", post=post)


@app.route("/post/<int:post_id>/delete", methods=["POST"])
def post_delete(post_id):
    db = get_db()
    db.execute("DELETE FROM posts WHERE id = ?", (post_id,))
    db.commit()
    return redirect(url_for("post_list"))


if __name__ == "__main__":
    app.run(debug=True)
