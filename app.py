import sqlite3
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, g

app = Flask(__name__)
DATABASE = "blog.db"


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


@app.before_request
def ensure_db():
    if not hasattr(app, "_db_initialized"):
        init_db()
        app._db_initialized = True


@app.route("/")
def post_list():
    db = get_db()
    posts = db.execute("SELECT * FROM posts ORDER BY created_at DESC").fetchall()
    return render_template("list.html", posts=posts)


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


if __name__ == "__main__":
    app.run(debug=True)
