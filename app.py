from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from datetime import datetime

app = Flask(__name__)
app.secret_key = "ntcc-student-skill-exchange-2026"
DB = "database.db"

def get_db():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def init_db():
    conn = get_db()
    conn.executescript("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        department TEXT NOT NULL,
        year INTEGER NOT NULL,
        availability TEXT DEFAULT '',
        bio TEXT DEFAULT '',
        is_admin INTEGER DEFAULT 0,
        is_blocked INTEGER DEFAULT 0,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS skills (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE NOT NULL,
        category TEXT DEFAULT 'Technical'
    );

    CREATE TABLE IF NOT EXISTS user_skills (
        user_id INTEGER NOT NULL,
        skill_id INTEGER NOT NULL,
        skill_type TEXT NOT NULL CHECK(skill_type IN ('teach','learn')),
        PRIMARY KEY(user_id, skill_id, skill_type),
        FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE,
        FOREIGN KEY(skill_id) REFERENCES skills(id) ON DELETE CASCADE
    );

    CREATE TABLE IF NOT EXISTS requests (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        learner_id INTEGER NOT NULL,
        teacher_id INTEGER NOT NULL,
        skill_id INTEGER NOT NULL,
        status TEXT DEFAULT 'Pending',
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(learner_id) REFERENCES users(id) ON DELETE CASCADE,
        FOREIGN KEY(teacher_id) REFERENCES users(id) ON DELETE CASCADE,
        FOREIGN KEY(skill_id) REFERENCES skills(id) ON DELETE CASCADE
    );

    CREATE TABLE IF NOT EXISTS sessions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        request_id INTEGER NOT NULL,
        learner_id INTEGER NOT NULL,
        teacher_id INTEGER NOT NULL,
        skill_id INTEGER NOT NULL,
        session_date TEXT NOT NULL,
        session_time TEXT NOT NULL,
        status TEXT DEFAULT 'Scheduled',
        FOREIGN KEY(request_id) REFERENCES requests(id) ON DELETE CASCADE,
        FOREIGN KEY(learner_id) REFERENCES users(id) ON DELETE CASCADE,
        FOREIGN KEY(teacher_id) REFERENCES users(id) ON DELETE CASCADE,
        FOREIGN KEY(skill_id) REFERENCES skills(id) ON DELETE CASCADE
    );

    CREATE TABLE IF NOT EXISTS reviews (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        session_id INTEGER NOT NULL,
        reviewer_id INTEGER NOT NULL,
        reviewee_id INTEGER NOT NULL,
        rating INTEGER NOT NULL CHECK(rating BETWEEN 1 AND 5),
        comment TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(session_id) REFERENCES sessions(id) ON DELETE CASCADE,
        FOREIGN KEY(reviewer_id) REFERENCES users(id) ON DELETE CASCADE,
        FOREIGN KEY(reviewee_id) REFERENCES users(id) ON DELETE CASCADE
    );
    """)

    skills = [
        ("Python","Programming"),("C","Programming"),("C++","Programming"),
        ("Java","Programming"),("JavaScript","Programming"),("React","Web Development"),
        ("HTML","Web Development"),("CSS","Web Development"),("SQL","Database"),
        ("Data Analysis","Data & Analytics"),("Machine Learning","Data & Analytics"),
        ("Excel","Business"),("Power BI","Business"),("Financial Analysis","Finance"),
        ("Public Speaking","Soft Skills"),("Communication","Soft Skills"),
        ("Leadership","Soft Skills"),("UI/UX","Design"),("Photoshop","Design"),
        ("Video Editing","Creative"),("Git/GitHub","Tools")
    ]
    for name, category in skills:
        conn.execute("INSERT OR IGNORE INTO skills(name,category) VALUES (?,?)",(name,category))

    # Demo students
    demo = [
        ("Shristi Sharma","shristi@gmail.com","CSE",2,"Saturday, Sunday",
         "Computer Science student interested in programming and web development.",
         ["Python","HTML","CSS"],["JavaScript","React"]),
        ("Rahul Verma","rahul@gmail.com","CSE",3,"Saturday, Sunday",
         "Programming enthusiast who enjoys helping juniors learn Python.",
         ["Python","JavaScript"],["Data Analysis"]),
        ("Ananya Singh","ananya@gmail.com","ECE",2,"Sunday",
         "Interested in data, design and communication.",
         ["Power BI","Public Speaking"],["Python","UI/UX"]),
        ("Arjun Mehta","arjun@gmail.com","BBA",3,"Saturday",
         "Business student with an interest in finance and analytics.",
         ["Excel","Financial Analysis"],["Power BI","Python"]),
    ]
    for name,email,dept,year,av,bio,teach,learn in demo:
        existing = conn.execute("SELECT id FROM users WHERE email=?",(email,)).fetchone()
        if not existing:
            cur = conn.execute("""INSERT INTO users(name,email,password,department,year,availability,bio)
                VALUES (?,?,?,?,?,?,?)""",
                (name,email,generate_password_hash("student123"),dept,year,av,bio))
            uid = cur.lastrowid
            for s in teach:
                sid = conn.execute("SELECT id FROM skills WHERE name=?",(s,)).fetchone()["id"]
                conn.execute("INSERT INTO user_skills VALUES (?,?,?)",(uid,sid,"teach"))
            for s in learn:
                sid = conn.execute("SELECT id FROM skills WHERE name=?",(s,)).fetchone()["id"]
                conn.execute("INSERT INTO user_skills VALUES (?,?,?)",(uid,sid,"learn"))

    admin = conn.execute("SELECT id FROM users WHERE email='admin@skillxchange.com'").fetchone()
    if not admin:
        conn.execute("""INSERT INTO users(name,email,password,department,year,is_admin)
                        VALUES (?,?,?,?,?,1)""",
                     ("System Administrator","admin@skillxchange.com",
                      generate_password_hash("admin123"),"Administration",0))
    conn.commit()
    conn.close()

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if "user_id" not in session:
            flash("Please login to continue.", "warning")
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated

def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get("is_admin"):
            flash("Administrator access required.", "danger")
            return redirect(url_for("dashboard"))
        return f(*args, **kwargs)
    return decorated

@app.context_processor
def inject_globals():
    return {"current_year": datetime.now().year}

@app.route("/")
def home():
    return render_template("home.html")

@app.route("/register", methods=["GET","POST"])
def register():
    if request.method == "POST":
        name=request.form["name"].strip()
        email=request.form["email"].strip().lower()
        password=request.form["password"]
        department=request.form["department"]
        year=request.form["year"]
        if not all([name,email,password,department,year]):
            flash("Please fill all required fields.","danger")
            return render_template("register.html")
        conn=get_db()
        try:
            conn.execute("""INSERT INTO users(name,email,password,department,year)
                            VALUES (?,?,?,?,?)""",
                         (name,email,generate_password_hash(password),department,year))
            conn.commit()
            flash("Account created successfully. Please login.","success")
            return redirect(url_for("login"))
        except sqlite3.IntegrityError:
            flash("An account with this email already exists.","danger")
        finally:
            conn.close()
    return render_template("register.html")

@app.route("/login", methods=["GET","POST"])
def login():
    if request.method=="POST":
        email=request.form["email"].strip().lower()
        password=request.form["password"]
        conn=get_db()
        user=conn.execute("SELECT * FROM users WHERE email=?",(email,)).fetchone()
        conn.close()
        if user and check_password_hash(user["password"],password):
            if user["is_blocked"]:
                flash("Your account has been blocked by the administrator.","danger")
                return render_template("login.html")
            session["user_id"]=user["id"]
            session["name"]=user["name"]
            session["is_admin"]=bool(user["is_admin"])
            return redirect(url_for("admin_dashboard" if user["is_admin"] else "dashboard"))
        flash("Invalid email or password.","danger")
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("home"))

@app.route("/dashboard")
@login_required
def dashboard():
    conn=get_db()
    uid=session["user_id"]
    user=conn.execute("SELECT * FROM users WHERE id=?",(uid,)).fetchone()
    teach=conn.execute("""SELECT s.name FROM skills s JOIN user_skills us ON s.id=us.skill_id
                          WHERE us.user_id=? AND us.skill_type='teach' ORDER BY s.name""",(uid,)).fetchall()
    learn=conn.execute("""SELECT s.name FROM skills s JOIN user_skills us ON s.id=us.skill_id
                          WHERE us.user_id=? AND us.skill_type='learn' ORDER BY s.name""",(uid,)).fetchall()
    pending=conn.execute("""SELECT COUNT(*) c FROM requests WHERE teacher_id=? AND status='Pending'""",(uid,)).fetchone()["c"]
    upcoming=conn.execute("""SELECT COUNT(*) c FROM sessions WHERE (teacher_id=? OR learner_id=?) AND status='Scheduled'""",(uid,uid)).fetchone()["c"]
    rating=conn.execute("""SELECT ROUND(AVG(rating),1) r FROM reviews WHERE reviewee_id=?""",(uid,)).fetchone()["r"]
    conn.close()
    return render_template("dashboard.html",user=user,teach=teach,learn=learn,pending=pending,
                           upcoming=upcoming,rating=rating or "—")

@app.route("/profile", methods=["GET","POST"])
@login_required
def profile():
    conn=get_db(); uid=session["user_id"]
    if request.method=="POST":
        conn.execute("""UPDATE users SET name=?,department=?,year=?,availability=?,bio=? WHERE id=?""",
                     (request.form["name"],request.form["department"],request.form["year"],
                      request.form.get("availability",""),request.form.get("bio",""),uid))
        conn.commit()
        session["name"]=request.form["name"]
        flash("Profile updated successfully.","success")
        return redirect(url_for("profile"))
    user=conn.execute("SELECT * FROM users WHERE id=?",(uid,)).fetchone()
    conn.close()
    return render_template("profile.html",user=user)

@app.route("/skills", methods=["GET","POST"])
@login_required
def skills():
    conn=get_db(); uid=session["user_id"]
    if request.method=="POST":
        conn.execute("DELETE FROM user_skills WHERE user_id=?",(uid,))
        for sid in request.form.getlist("teach"):
            conn.execute("INSERT INTO user_skills VALUES (?,?,?)",(uid,int(sid),"teach"))
        for sid in request.form.getlist("learn"):
            conn.execute("INSERT INTO user_skills VALUES (?,?,?)",(uid,int(sid),"learn"))
        conn.commit()
        flash("Skills updated successfully.","success")
        return redirect(url_for("skills"))
    allskills=conn.execute("SELECT * FROM skills ORDER BY category,name").fetchall()
    selected=conn.execute("SELECT skill_id,skill_type FROM user_skills WHERE user_id=?",(uid,)).fetchall()
    teach={r["skill_id"] for r in selected if r["skill_type"]=="teach"}
    learn={r["skill_id"] for r in selected if r["skill_type"]=="learn"}
    conn.close()
    return render_template("skills.html",skills=allskills,teach=teach,learn=learn)

@app.route("/matches")
@login_required
def matches():
    conn=get_db(); uid=session["user_id"]
    # A simple, explainable reciprocal matching algorithm:
    # my learning skill == their teaching skill OR their learning skill == my teaching skill.
    rows=conn.execute("""
        SELECT DISTINCT u.id,u.name,u.department,u.year,u.availability,u.bio,s.name AS skill
        FROM users u
        JOIN user_skills us ON u.id=us.user_id AND us.skill_type='teach'
        JOIN skills s ON s.id=us.skill_id
        WHERE u.id != ? AND u.is_blocked=0
          AND us.skill_id IN (
              SELECT skill_id FROM user_skills WHERE user_id=? AND skill_type='learn'
          )
        ORDER BY u.name
    """,(uid,uid)).fetchall()
    conn.close()
    return render_template("matches.html",matches=rows)

@app.route("/api/skill-id")
@login_required
def skill_id_api():
    name = request.args.get("name","")
    conn=get_db()
    row=conn.execute("SELECT id FROM skills WHERE name=?",(name,)).fetchone()
    conn.close()
    return {"id": row["id"] if row else 0}

@app.route("/request/<int:teacher_id>/<int:skill_id>", methods=["POST"])
@login_required
def send_request(teacher_id,skill_id):
    uid=session["user_id"]
    if uid==teacher_id:
        flash("You cannot send a learning request to yourself.","warning")
        return redirect(url_for("matches"))
    conn=get_db()
    exists=conn.execute("""SELECT id FROM requests WHERE learner_id=? AND teacher_id=? AND skill_id=?
                           AND status IN ('Pending','Accepted')""",(uid,teacher_id,skill_id)).fetchone()
    if not exists:
        conn.execute("INSERT INTO requests(learner_id,teacher_id,skill_id) VALUES (?,?,?)",(uid,teacher_id,skill_id))
        conn.commit()
        flash("Learning request sent successfully.","success")
    else:
        flash("You already have an active request for this skill.","info")
    conn.close()
    return redirect(url_for("matches"))

@app.route("/requests")
@login_required
def requests_page():
    conn=get_db(); uid=session["user_id"]
    incoming=conn.execute("""SELECT r.*,u.name learner,s.name skill FROM requests r
        JOIN users u ON u.id=r.learner_id JOIN skills s ON s.id=r.skill_id
        WHERE r.teacher_id=? ORDER BY r.created_at DESC""",(uid,)).fetchall()
    outgoing=conn.execute("""SELECT r.*,u.name teacher,s.name skill FROM requests r
        JOIN users u ON u.id=r.teacher_id JOIN skills s ON s.id=r.skill_id
        WHERE r.learner_id=? ORDER BY r.created_at DESC""",(uid,)).fetchall()
    conn.close()
    return render_template("requests.html",incoming=incoming,outgoing=outgoing)

@app.route("/request/<int:request_id>/<action>", methods=["POST"])
@login_required
def update_request(request_id,action):
    if action not in ("accept","reject"): return redirect(url_for("requests_page"))
    conn=get_db()
    req=conn.execute("SELECT * FROM requests WHERE id=? AND teacher_id=?",
                     (request_id,session["user_id"])).fetchone()
    if not req:
        conn.close(); flash("Request not found.","danger"); return redirect(url_for("requests_page"))
    status="Accepted" if action=="accept" else "Rejected"
    conn.execute("UPDATE requests SET status=? WHERE id=?",(status,request_id))
    conn.commit(); conn.close()
    flash(f"Request {status.lower()}.","success")
    return redirect(url_for("requests_page"))

@app.route("/sessions", methods=["GET","POST"])
@login_required
def sessions_page():
    conn=get_db(); uid=session["user_id"]
    if request.method=="POST":
        rid=int(request.form["request_id"])
        req=conn.execute("SELECT * FROM requests WHERE id=? AND status='Accepted' AND (learner_id=? OR teacher_id=?)",
                         (rid,uid,uid)).fetchone()
        if req:
            conn.execute("""INSERT INTO sessions(request_id,learner_id,teacher_id,skill_id,session_date,session_time)
                            VALUES (?,?,?,?,?,?)""",
                         (rid,req["learner_id"],req["teacher_id"],req["skill_id"],
                          request.form["session_date"],request.form["session_time"]))
            conn.commit(); flash("Learning session scheduled.","success")
        else:
            flash("You can only schedule an accepted request.","danger")
    accepted=conn.execute("""SELECT r.id,u.name learner,t.name teacher,s.name skill
        FROM requests r JOIN users u ON u.id=r.learner_id JOIN users t ON t.id=r.teacher_id
        JOIN skills s ON s.id=r.skill_id
        WHERE r.status='Accepted' AND (r.learner_id=? OR r.teacher_id=?)""",(uid,uid)).fetchall()
    upcoming=conn.execute("""SELECT ss.*,s.name skill,u.name learner,t.name teacher
        FROM sessions ss JOIN skills s ON s.id=ss.skill_id JOIN users u ON u.id=ss.learner_id
        JOIN users t ON t.id=ss.teacher_id
        WHERE ss.learner_id=? OR ss.teacher_id=? ORDER BY ss.session_date,ss.session_time""",(uid,uid)).fetchall()
    conn.close()
    return render_template("sessions.html",accepted=accepted,upcoming=upcoming)

@app.route("/review/<int:session_id>", methods=["GET","POST"])
@login_required
def review(session_id):
    conn=get_db(); uid=session["user_id"]
    ss=conn.execute("""SELECT ss.*,s.name skill,u.name learner,t.name teacher
        FROM sessions ss JOIN skills s ON s.id=ss.skill_id JOIN users u ON u.id=ss.learner_id
        JOIN users t ON t.id=ss.teacher_id WHERE ss.id=? AND (ss.learner_id=? OR ss.teacher_id=?)""",
        (session_id,uid,uid)).fetchone()
    if not ss:
        conn.close(); flash("Session not found.","danger"); return redirect(url_for("sessions_page"))
    if request.method=="POST":
        reviewee=ss["teacher_id"] if uid==ss["learner_id"] else ss["learner_id"]
        conn.execute("""INSERT INTO reviews(session_id,reviewer_id,reviewee_id,rating,comment)
                        VALUES (?,?,?,?,?)""",
                     (session_id,uid,reviewee,int(request.form["rating"]),request.form.get("comment","")))
        conn.execute("UPDATE sessions SET status='Completed' WHERE id=?",(session_id,))
        conn.commit(); conn.close()
        flash("Thank you! Your review has been submitted.","success")
        return redirect(url_for("sessions_page"))
    conn.close()
    return render_template("review.html",session=ss)

@app.route("/admin")
@admin_required
def admin_dashboard():
    conn=get_db()
    stats={
        "students":conn.execute("SELECT COUNT(*) c FROM users WHERE is_admin=0").fetchone()["c"],
        "active":conn.execute("SELECT COUNT(*) c FROM users WHERE is_admin=0 AND is_blocked=0").fetchone()["c"],
        "skills":conn.execute("SELECT COUNT(*) c FROM skills").fetchone()["c"],
        "requests":conn.execute("SELECT COUNT(*) c FROM requests").fetchone()["c"],
        "completed":conn.execute("SELECT COUNT(*) c FROM sessions WHERE status='Completed'").fetchone()["c"],
    }
    conn.close()
    return render_template("admin/dashboard.html",stats=stats)

@app.route("/admin/students")
@admin_required
def admin_students():
    conn=get_db()
    students=conn.execute("SELECT * FROM users WHERE is_admin=0 ORDER BY created_at DESC").fetchall()
    conn.close()
    return render_template("admin/students.html",students=students)

@app.route("/admin/student/<int:user_id>/<action>", methods=["POST"])
@admin_required
def admin_student_action(user_id,action):
    conn=get_db()
    if action=="block": conn.execute("UPDATE users SET is_blocked=1 WHERE id=?",(user_id,))
    elif action=="unblock": conn.execute("UPDATE users SET is_blocked=0 WHERE id=?",(user_id,))
    elif action=="delete": conn.execute("DELETE FROM users WHERE id=?",(user_id,))
    conn.commit(); conn.close()
    flash("Student record updated.","success")
    return redirect(url_for("admin_students"))

@app.route("/admin/skills")
@admin_required
def admin_skills():
    conn=get_db()
    skills=conn.execute("""SELECT s.*,COUNT(us.user_id) users_count FROM skills s
        LEFT JOIN user_skills us ON s.id=us.skill_id GROUP BY s.id ORDER BY s.category,s.name""").fetchall()
    conn.close()
    return render_template("admin/skills.html",skills=skills)

@app.route("/admin/requests")
@admin_required
def admin_requests():
    conn=get_db()
    rows=conn.execute("""SELECT r.*,l.name learner,t.name teacher,s.name skill
        FROM requests r JOIN users l ON l.id=r.learner_id JOIN users t ON t.id=r.teacher_id
        JOIN skills s ON s.id=r.skill_id ORDER BY r.created_at DESC""").fetchall()
    conn.close()
    return render_template("admin/requests.html",requests=rows)

@app.route("/admin/reviews")
@admin_required
def admin_reviews():
    conn=get_db()
    reviews=conn.execute("""SELECT rv.*,a.name reviewer,b.name reviewee,s.name skill
        FROM reviews rv JOIN users a ON a.id=rv.reviewer_id JOIN users b ON b.id=rv.reviewee_id
        JOIN sessions ss ON ss.id=rv.session_id JOIN skills s ON s.id=ss.skill_id
        ORDER BY rv.created_at DESC""").fetchall()
    conn.close()
    return render_template("admin/reviews.html",reviews=reviews)

if __name__ == "__main__":
    init_db()
    app.run(debug=True)
