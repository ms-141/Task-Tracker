from datetime import date
from functools import wraps

from flask import Flask, session, render_template, request, redirect
from flask_bcrypt import Bcrypt





from core import (
    # users
    get_user_by_login, create_user,
    # daily context
    upsert_daily_context, get_daily_context,
    # planning
    generate_daily_plan, apply_plan_progress,
    # tasks
    create_task, list_active_tasks
)

app = Flask(__name__)
app.secret_key = "tralalala_secret_key"  
bcrypt = Bcrypt(app)


# #############################################
# SEE DATABASE CONTENTS AT "http://127.0.0.1:5000/debug/all"
from core import query_all

@app.route("/debug/all")
def debug_all():
    output = []

    tables = query_all(
        "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';"
    )

    for t in tables:
        table_name = t["name"]
        output.append(f"=== {table_name} ===")

        rows = query_all(f"SELECT * FROM {table_name}")
        if rows:
            for r in rows:
                output.append(str(dict(r)))
        else:
            output.append("(empty)")

        output.append("")

    return "<pre>" + "\n".join(output) + "</pre>"

# #############################################

#  Authentication helpers
def hash_password(password: str) -> str:
    return bcrypt.generate_password_hash(password).decode("utf-8")

def verify_password(password: str, stored_hash: str) -> bool:
    return bcrypt.check_password_hash(stored_hash, password)

def login_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if "user_id" not in session:
            return redirect("/login")
        return fn(*args, **kwargs)
    return wrapper


@app.route("/", methods=["GET"])
def index():
    
    # Routes people based on login status
    if "user_id" in session:
        return redirect("/plan")
    return render_template("index.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        login_name = request.form.get("login_name", "").strip()
        password = request.form.get("password", "")

        if not login_name or not password:
            return "Missing username or password", 400

        if get_user_by_login(login_name):
            return "User already exists. Use /login.", 400

        pw_hash = hash_password(password)
        create_user(login_name, pw_hash)

        user = get_user_by_login(login_name)
        session["user_id"] = int(user["id"])

        return redirect("/daily")

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        login_name = request.form.get("login_name", "").strip()
        password = request.form.get("password", "")

        user = get_user_by_login(login_name)
        if not user:
            return "Invalid credentials", 401

        if not verify_password(password, user["password_hash"]):
            return "Invalid credentials", 401

        session["user_id"] = int(user["id"])
        return redirect("/daily")

    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")


@app.route("/daily", methods=["GET", "POST"])
@login_required
def daily():
    user_id = int(session["user_id"])
    today = date.today().strftime("%Y-%m-%d")

    if request.method == "POST":
        available = int(request.form.get("available_minutes", 0) or 0)
        buffer_mins = int(request.form.get("buffer_minutes", 0) or 0)
        energy_raw = request.form.get("energy_level")
        energy = int(energy_raw) if energy_raw not in (None, "", "null") else None

        upsert_daily_context(
            user_id=user_id,
            entry_date=today,
            available_minutes=available,
            energy_level=energy,
            buffer_minutes=buffer_mins
        )
        return redirect("/plan")

    ctx = get_daily_context(user_id, today)
    return render_template("daily.html", ctx=ctx, entry_date=today)


@app.route("/plan", methods=["GET", "POST"])
@login_required
def plan():
    user_id = int(session["user_id"])
    today = date.today().strftime("%Y-%m-%d")

    if request.method == "POST":
        multiplier = float(request.form.get("minutes_multiplier", "1.0") or 1.0)

        plan_data = generate_daily_plan(user_id, today)
        allocations = plan_data.get("allocations", [])
        apply_plan_progress(user_id, allocations, minutes_multiplier=multiplier)

        return redirect("/plan")

    plan_data = generate_daily_plan(user_id, today)
    return render_template("dashboard.html", plan=plan_data, entry_date=today)


@app.route("/tasks", methods=["GET", "POST"])
@login_required
def tasks():
    user_id = int(session["user_id"])

    if request.method == "POST":
        title = request.form.get("title", "").strip()
        course = request.form.get("course", "").strip() or None
        due_date = request.form.get("due_date", "").strip()
        difficulty = int(request.form.get("difficulty", 2))
        importance = int(request.form.get("importance", 2))
        remaining_minutes = int(request.form.get("remaining_minutes", 0))

        if not title or not due_date:
            return "Missing title or due date", 400

    
        difficulty = max(1, min(3, difficulty))
        importance = max(1, min(3, importance))
        remaining_minutes = max(0, remaining_minutes)

        create_task(
            user_id=user_id,
            title=title,
            course=course,
            due_date=due_date,
            difficulty=difficulty,
            importance=importance,
            remaining_minutes=remaining_minutes
        )

        return redirect("/tasks")

    tasks = list_active_tasks(user_id)
    return render_template("tasks.html", tasks=tasks)

if __name__ == "__main__":
    app.run(debug=True)
