"""Lunch: a weekly meal planner with a SQLite database and a password login.

Run locally:   LUNCH_PASSWORD=pick-one SECRET_KEY=anything flask --app app run
Other apps can be added later as more blueprints on the same site.
"""
import hmac
import json
import os
import sqlite3
import time
from datetime import timedelta

from flask import (Blueprint, Flask, abort, jsonify, redirect, request,
                   send_from_directory, session, url_for)

BASE = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.environ.get("LUNCH_DB", os.path.join(BASE, "data", "lunch.db"))
MAX_BYTES = 1_000_000

bp = Blueprint("lunch", __name__, url_prefix="/lunch")


def db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    con = sqlite3.connect(DB_PATH)
    con.execute("CREATE TABLE IF NOT EXISTS kv (k TEXT PRIMARY KEY, v TEXT NOT NULL, updated REAL NOT NULL)")
    return con


def read(key):
    con = db()
    try:
        row = con.execute("SELECT v FROM kv WHERE k = ?", (key,)).fetchone()
        return row[0] if row else None
    finally:
        con.close()


def write(key, value):
    con = db()
    try:
        con.execute(
            "INSERT INTO kv (k, v, updated) VALUES (?, ?, ?) "
            "ON CONFLICT(k) DO UPDATE SET v = excluded.v, updated = excluded.updated",
            (key, value, time.time()),
        )
        con.commit()
    finally:
        con.close()


LOGIN = """<!DOCTYPE html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1"><title>Sign in</title>
<style>
:root{color-scheme:light dark;--bg:#f2f5ee;--card:#fff;--ink:#17231c;--line:#d7ded3;--green:#1c7a4a;--bad:#bf3a29}
@media (prefers-color-scheme:dark){:root{--bg:#0f1611;--card:#172019;--ink:#e7eee6;--line:#2b382f;--green:#58c088;--bad:#f08573}}
body{margin:0;min-height:100vh;display:grid;place-items:center;background:var(--bg);color:var(--ink);font:16px/1.4 system-ui,sans-serif}
form{background:var(--card);border:1px solid var(--line);border-radius:14px;padding:22px;width:min(340px,calc(100vw - 32px));display:flex;flex-direction:column;gap:12px}
h1{margin:0;font-size:22px}input,button{font:inherit;padding:11px;border-radius:9px;border:1px solid var(--line);background:var(--bg);color:var(--ink)}
button{background:var(--green);border-color:var(--green);color:#fff;font-weight:600;cursor:pointer}
.e{color:var(--bad);font-size:14px;margin:0}
</style></head><body><form method="post"><h1>Meal Week</h1>
<label for="p">Password</label><input id="p" name="password" type="password" autocomplete="current-password" autofocus required>
{error}<button>Sign in</button></form></body></html>"""


def logged_in():
    return session.get("ok") is True


@bp.get("/")
def index():
    if not logged_in():
        return redirect(url_for("lunch.login"))
    resp = send_from_directory(BASE, "index.html")
    resp.headers["Cache-Control"] = "no-cache"
    return resp


@bp.route("/login", methods=["GET", "POST"])
def login():
    expected = os.environ.get("LUNCH_PASSWORD", "")
    if not expected:
        return LOGIN.replace("{error}", '<p class="e">No password is set on the server yet.</p>'), 500
    if request.method == "POST":
        given = request.form.get("password", "")
        if hmac.compare_digest(given.encode(), expected.encode()):
            session.clear()
            session["ok"] = True
            session.permanent = True
            return redirect(url_for("lunch.index"))
        time.sleep(1)
        return LOGIN.replace("{error}", '<p class="e">That password is not right.</p>'), 401
    return LOGIN.replace("{error}", "")


@bp.get("/logout")
def logout():
    session.clear()
    return redirect(url_for("lunch.login"))


@bp.route("/api/state", methods=["GET", "PUT"])
def state():
    if not logged_in():
        return jsonify(error="sign in"), 401
    if request.method == "GET":
        return (read("state") or "{}"), 200, {"Content-Type": "application/json", "Cache-Control": "no-store"}
    raw = request.get_data()
    if len(raw) > MAX_BYTES:
        abort(413)
    try:
        data = json.loads(raw)
    except ValueError:
        abort(400)
    if not isinstance(data, dict) or "plan" not in data or "pantry" not in data:
        abort(400)
    current = read("state")
    if current:
        write("state_previous", current)
    write("state", json.dumps(data, separators=(",", ":")))
    return jsonify(ok=True)


def create_app():
    app = Flask(__name__)
    app.secret_key = os.environ.get("SECRET_KEY") or os.urandom(32)
    app.config.update(
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE="Lax",
        SESSION_COOKIE_SECURE=os.environ.get("LUNCH_INSECURE_COOKIES") != "1",
        PERMANENT_SESSION_LIFETIME=timedelta(days=90),
        MAX_CONTENT_LENGTH=MAX_BYTES + 1024,
    )
    app.register_blueprint(bp)

    @app.get("/")
    def home():
        return redirect(url_for("lunch.index"))

    return app


app = create_app()
