import sqlite3
from datetime import datetime, date


DB_PATH = "database.db"

# Helpers

def get_connection():
    
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    cursor = connection.cursor()
    cursor.execute("PRAGMA foreign_keys = ON;")
    
    return connection

def query_one(sql, params=()):
    
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(sql, params)
    row = cursor.fetchone()
    conn.close()
    
    return row

def query_all(sql, params=()):
    
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(sql, params)
    rows = cursor.fetchall()
    conn.close()
    
    return rows

def execute(sql, params=()):
    
    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute(sql, params)
    connection.commit()
    last_id = cursor.lastrowid
    connection.close()
    
    return last_id




# Users
 
def create_user(login_name, password_hash, user_email=None):
    
    return execute(
        """
        INSERT OR IGNORE INTO users (login_name, password_hash, user_email)
        VALUES (?, ?, ?)
        """,
        (login_name, password_hash, user_email)
    )

def get_user_by_login(login_name):
    
    return query_one(
        "SELECT * FROM users WHERE login_name = ?",
        (login_name,)   
    )

def get_user_by_id(id):
    
    return query_one(
        "SELECT * FROM users WHERE id = ?",
        (id,)   
    )

def get_or_create_user(login_name, password_hash, user_email=None):
    create_user(login_name, password_hash, user_email)
    user = get_user_by_login(login_name)
    return user["id"]



# Tasks

def create_task(user_id, title, course, due_date, difficulty, importance, remaining_minutes):
    
    return execute(
        """
        INSERT OR IGNORE INTO tasks (user_id, title, course, due_date, difficulty, importance, remaining_minutes)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (user_id, title, course, due_date, difficulty, importance, remaining_minutes)
    )

def list_active_tasks(user_id):
    
    return query_all(
        """
        SELECT * FROM tasks
        WHERE user_id = ? AND status = 'active'
        ORDER BY due_date ASC, importance DESC, difficulty DESC
        """,
        (user_id,)
    )

def update_task_remaining_minutes(task_id, remaining_minutes):
    
    execute(
        """
        UPDATE tasks
        SET remaining_minutes = ?
        WHERE id = ?;
        """,
        (remaining_minutes, task_id)
    )




# Daily

def upsert_daily_context(user_id, entry_date, available_minutes, energy_level=None, buffer_minutes=0):
    
    execute("""
            
        INSERT INTO daily_context (user_id, entry_date, available_minutes, energy_level, buffer_minutes) 
        VALUES (?, ?, ?, ?, ?)
        ON CONFLICT(user_id, entry_date)
        DO UPDATE SET
            available_minutes = excluded.available_minutes,
            energy_level = excluded.energy_level,
            buffer_minutes = excluded.buffer_minutes;
        """,
        (user_id, entry_date, available_minutes, energy_level, buffer_minutes)
    )

def get_daily_context(user_id, entry_date):
    
    return query_one("""
            
        SELECT available_minutes, energy_level, buffer_minutes 
        FROM daily_context
        WHERE user_id = ? AND entry_date = ?;
        """,
        (user_id, entry_date)
    )



# Planning Helpers

def date_yyyy_mm_dd(s: str) -> date:
    
    return datetime.strptime(s, "%Y-%m-%d").date()

def days_left_including_today(today: date, due: date) -> int:
    
    return max(1, (due - today).days + 1)

def score_need(entry_date, due_date_str, remaining_minutes, difficulty_score, importance_score):
    difficulty = {1: 1.0, 2: 1.2, 3: 1.4}
    importance  = {1: 0.9, 2: 1.0, 3: 1.2}

    today = date_yyyy_mm_dd(entry_date)
    due_date = date_yyyy_mm_dd(due_date_str)
    days_left = days_left_including_today(today, due_date)

    base_daily_need = remaining_minutes / days_left

    return base_daily_need * difficulty.get(difficulty_score, 1.0) * importance.get(importance_score, 1.0)

def compute_usable_minutes(daily_context):
    
    available = int(daily_context["available_minutes"])
    buffer_minutes = int(daily_context["buffer_minutes"] or 0)
    usable_minutes = max(0, available - buffer_minutes)
    
    return available, buffer_minutes, usable_minutes

def build_scored_tasks(tasks, entry_date):
    
    scored_tasks = []
    total_score = 0.0

    for t in tasks:
        remaining = int(t["remaining_minutes"])
        if remaining <= 0:
            continue

        need = score_need(
            entry_date=entry_date,
            due_date_str=t["due_date"],
            remaining_minutes=remaining,
            difficulty_score=int(t["difficulty"]),
            importance_score=int(t["importance"])
        )

        scored_tasks.append({
            "task_id": t["id"],
            "title": t["title"],
            "due_date": t["due_date"],
            "remaining_minutes": remaining,
            "score": need
        })
        total_score += need

    return scored_tasks, total_score

def allocate_minutes(scored_tasks, total_score, usable_minutes):
    
    allocations = []

    for st in scored_tasks:
        if total_score > 0:
            share = (st["score"] / total_score)
        else: 
            share = 0.0
        
        minutes = int(round(share * usable_minutes))
        minutes = min(minutes, st["remaining_minutes"])
        lo = int(round(minutes * 0.8))
        hi = int(round(minutes * 1.2))


        allocations.append({
            "task_id": st["task_id"],
            "title": st["title"],
            "due_date": st["due_date"],
            "minutes": minutes,
            "minutes_range": f"{lo}-{hi}"
        })

    return allocations

def fix_rounding_drift(allocations, scored_tasks, usable_minutes):
    
    planned_total = sum(a["minutes"] for a in allocations)
    drift = usable_minutes - planned_total

    # earliest first
    allocations.sort(key=lambda a: a["due_date"])  

    i = 0
    while drift != 0 and allocations:
        idx = i % len(allocations)
        task_id = allocations[idx]["task_id"]
        remaining = next(st["remaining_minutes"] for st in scored_tasks if st["task_id"] == task_id)

        if drift > 0:
            if allocations[idx]["minutes"] < remaining:
                allocations[idx]["minutes"] += 1
                drift -= 1
        else:
            if allocations[idx]["minutes"] > 0:
                allocations[idx]["minutes"] -= 1
                drift += 1
        i += 1

    planned_total = sum(a["minutes"] for a in allocations)
    
    return allocations, planned_total

def compute_overloaded(tasks, entry_date, usable_minutes):
    
    today_date = date_yyyy_mm_dd(entry_date)
    min_needed = 0.0

    for t in tasks:
        remaining = int(t["remaining_minutes"])
        if remaining <= 0:
            continue

        due = date_yyyy_mm_dd(t["due_date"])
        days_left = days_left_including_today(today_date, due)
        min_needed += (remaining / days_left)

    return min_needed > usable_minutes

def build_plan_messages(overloaded):
    
    if overloaded:
        return [
            "Today is overloaded: required prep exceeds your usable time.",
            "This reflects constraints, not effort. The plan prioritizes urgent work."
        ]
    return ["Plan generated based on remaining work, deadlines, difficulty, and importance."]

# Main Planning Function

def generate_daily_plan(user_id, entry_date):
    
    daily_context = get_daily_context(user_id, entry_date)
    if daily_context is None:
        return {
            "overloaded": False,
            "allocations": [],
            "messages": ["No daily context found. Please enter today's available time first."]
        }

    tasks = list_active_tasks(user_id)
    if not tasks:
        available, buffer_minutes, usable_minutes = compute_usable_minutes(daily_context)
        return {
            "available_minutes": available,
            "buffer_minutes": buffer_minutes,
            "usable_minutes": usable_minutes,
            "overloaded": False,
            "allocations": [],
            "messages": ["No active tasks found. Add at least one exam/task first."]
        }

    available, buffer_minutes, usable_minutes = compute_usable_minutes(daily_context)
    if usable_minutes == 0:
        return {
            "available_minutes": available,
            "buffer_minutes": buffer_minutes,
            "usable_minutes": usable_minutes,
            "overloaded": True,
            "allocations": [],
            "messages": [
                "There is no usable time today after accounting for buffer time.",
                "Consider increasing your available time or reducing buffer time."
            ]
        }

    scored_tasks, total_score = build_scored_tasks(tasks, entry_date)
    if not scored_tasks:
        return {
            "available_minutes": available,
            "buffer_minutes": buffer_minutes,
            "usable_minutes": usable_minutes,
            "overloaded": False,
            "allocations": [],
            "messages": ["All active tasks have 0 remaining minutes."]
        }

    allocations = allocate_minutes(scored_tasks, total_score, usable_minutes)
    allocations, planned_total = fix_rounding_drift(allocations, scored_tasks, usable_minutes)

    overloaded = compute_overloaded(tasks, entry_date, usable_minutes)
    messages = build_plan_messages(overloaded)

    return {
        "available_minutes": available,
        "buffer_minutes": buffer_minutes,
        "usable_minutes": usable_minutes,
        "overloaded": overloaded,
        "planned_minutes_total": planned_total,
        "allocations": allocations,
        "messages": messages
    }


def apply_plan_progress(user_id, allocations, minutes_multiplier=1.0):
    
    for a in allocations:
        task_id = a["task_id"]
        worked = int(round(a["minutes"] * minutes_multiplier))
        if worked <= 0:
            continue

        # fetch current remaining
        row = query_one("""
                        SELECT remaining_minutes FROM tasks WHERE id = ? AND user_id = ?
                        """, 
                        (task_id, user_id)
                        )
        if row is None:
            continue

        remaining_now = int(row["remaining_minutes"])
        new_remaining = max(0, remaining_now - worked)
        update_task_remaining_minutes(task_id, new_remaining)

        # optionally mark done if finished
        if new_remaining == 0:
            execute("""
                    UPDATE tasks SET status = 'done' WHERE id = ? AND user_id = ?
                    """,
                    (task_id, user_id)
                    )

#Lust testing
if __name__ == "__main__":
    
    # 1) Create/get a test user
    login = "test_user"
    user_id = get_or_create_user(login, "hashed_password", "test@example.com")

    # 2) Add a couple tasks (use realistic dates and remaining minutes)
    # Note: due_date must be YYYY-MM-DD
    create_task(user_id, "MATH 1203 Midterm Prep", "MATH 1203", "2026-02-10", 3, 3, 600)
    create_task(user_id, "COMP 2633 Hackathon Post", "COMP 2633", "2026-02-04", 2, 3, 180)
    create_task(user_id, "Email prof / admin", "General", "2026-02-03", 1, 2, 30)

    # 3) Set today's context
    entry_date = date.today().strftime("%Y-%m-%d")
    upsert_daily_context(user_id, entry_date, available_minutes=180, energy_level=2, buffer_minutes=30)

    # 4) Generate and print the plan
    plan = generate_daily_plan(user_id, entry_date)

    print("\n=== DAILY PLAN ===")
    for msg in plan.get("messages", []):
        print("-", msg)

    print("\nTime:")
    print("Available:", plan.get("available_minutes"))
    print("Buffer:", plan.get("buffer_minutes"))
    print("Usable:", plan.get("usable_minutes"))
    print("Overloaded:", plan.get("overloaded"))
    print("Planned total:", plan.get("planned_minutes_total"))

    print("\nAllocations:")
    for a in plan.get("allocations", []):
        print(f"- {a['title']} (due {a['due_date']}): {a['minutes']} min (range {a['minutes_range']})")






