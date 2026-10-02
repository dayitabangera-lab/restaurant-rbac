from flask import Flask, render_template, request, redirect, session, url_for, g
import sqlite3
from pathlib import Path

app = Flask(__name__)
app.secret_key = "replace_this_with_any_random_string"

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "rbac.db"

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    cur = conn.cursor()

    cur.executescript('''
    CREATE TABLE IF NOT EXISTS Role (
        RoleId INTEGER PRIMARY KEY AUTOINCREMENT,
        RoleName TEXT NOT NULL UNIQUE
    );

    CREATE TABLE IF NOT EXISTS "User" (
        UserId INTEGER PRIMARY KEY AUTOINCREMENT,
        UserName TEXT NOT NULL,
        LoginId TEXT NOT NULL UNIQUE,
        Pwd TEXT NOT NULL,
        RoleId INTEGER NOT NULL,
        FOREIGN KEY (RoleId) REFERENCES Role(RoleId)
    );

    CREATE TABLE IF NOT EXISTS Activity (
        ActivityId INTEGER PRIMARY KEY AUTOINCREMENT,
        ActivityName TEXT NOT NULL UNIQUE,
        ParentActivityId INTEGER NULL,
        AccessDetail TEXT NOT NULL,
        FOREIGN KEY (ParentActivityId) REFERENCES Activity(ActivityId)
    );

    CREATE TABLE IF NOT EXISTS Responsibility (
        RoleId INTEGER NOT NULL,
        ActivityId INTEGER NOT NULL,
        PRIMARY KEY (RoleId, ActivityId),
        FOREIGN KEY (RoleId) REFERENCES Role(RoleId),
        FOREIGN KEY (ActivityId) REFERENCES Activity(ActivityId)
    );
    ''')

    role_count = cur.execute("SELECT COUNT(*) AS c FROM Role").fetchone()["c"]
    if role_count == 0:
        cur.execute("INSERT INTO Role (RoleName) VALUES (?)", ("Restaurant Owner",))
        role_id = cur.lastrowid

        cur.execute('''
            INSERT INTO "User" (UserName, LoginId, Pwd, RoleId)
            VALUES (?, ?, ?, ?)
        ''', ("Restaurant Owner One", "owner1", "owner123", role_id))

        activities = [
            ("Dashboard", None, "Main landing page after login"),
            ("Manage Profile", 1, "Update restaurant profile information"),
            ("Manage Menu", 1, "Add, edit, and remove menu items"),
            
        ]

        for name, parent_id, detail in activities:
            cur.execute(
                "INSERT INTO Activity (ActivityName, ParentActivityId, AccessDetail) VALUES (?, ?, ?)",
                (name, parent_id, detail),
            )

        activity_ids = [row["ActivityId"] for row in cur.execute("SELECT ActivityId FROM Activity").fetchall()]
        for aid in activity_ids:
            cur.execute("INSERT OR IGNORE INTO Responsibility (RoleId, ActivityId) VALUES (?, ?)", (role_id, aid))

    conn.commit()
    conn.close()

@app.before_request
def before_request():
    g.db = get_db()

@app.teardown_request
def teardown_request(exception):
    db = getattr(g, "db", None)
    if db is not None:
        db.close()

@app.route("/", methods=["GET", "POST"])
def login():
    error = None
    if request.method == "POST":
        login_id = request.form["login_id"].strip()
        pwd = request.form["pwd"].strip()

        user = g.db.execute('''
            SELECT UserId, UserName, RoleId
            FROM "User"
            WHERE LoginId = ? AND Pwd = ?
        ''', (login_id, pwd)).fetchone()

        if user:
            session["user_id"] = user["UserId"]
            session["user_name"] = user["UserName"]
            session["role_id"] = user["RoleId"]
            return redirect(url_for("dashboard"))
        else:
            error = "Invalid Login ID or Password"

    return render_template("login.html", error=error)

@app.route("/dashboard")
def dashboard():
    if "user_id" not in session:
        return redirect(url_for("login"))

    role = g.db.execute("SELECT RoleName FROM Role WHERE RoleId = ?", (session["role_id"],)).fetchone()
    activities = g.db.execute('''
        SELECT a.ActivityId, a.ActivityName, a.AccessDetail
        FROM Activity a
        JOIN Responsibility r ON r.ActivityId = a.ActivityId
        WHERE r.RoleId = ?
        ORDER BY a.ActivityId
    ''', (session["role_id"],)).fetchall()

    return render_template(
        "dashboard.html",
        user_name=session["user_name"],
        role_name=role["RoleName"] if role else "Unknown",
        activities=activities
    )

@app.route("/activity/<int:activity_id>")
def activity_page(activity_id):
    if "user_id" not in session:
        return redirect(url_for("login"))

    activity = g.db.execute("SELECT * FROM Activity WHERE ActivityId = ?", (activity_id,)).fetchone()
    if not activity:
        return "Activity not found", 404

    allowed = g.db.execute('''
        SELECT 1
        FROM Responsibility
        WHERE RoleId = ? AND ActivityId = ?
    ''', (session["role_id"], activity_id)).fetchone()

    if not allowed:
        return render_template("activity.html", denied=True, activity_name=activity["ActivityName"])

    return render_template(
        "activity.html",
        denied=False,
        activity_name=activity["ActivityName"],
        access_detail=activity["AccessDetail"],
    )

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

if __name__ == "__main__":
    init_db()
    app.run(debug=True)
