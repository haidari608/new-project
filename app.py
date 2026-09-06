import json
import os
from datetime import date, datetime, timedelta
from functools import wraps

import requests
from dotenv import load_dotenv
from flask import Flask, abort, flash, redirect, render_template, request, url_for
from flask_login import LoginManager, UserMixin, current_user, login_required, login_user, logout_user
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import inspect, or_, text
from werkzeug.security import check_password_hash, generate_password_hash

load_dotenv()

db = SQLAlchemy()
login_manager = LoginManager()
login_manager.login_view = "login"
login_manager.login_message_category = "info"

application_statuses = [
    "Not Started", "Documents Preparing", "Submitted", "Accepted", "Rejected"]

saved_scholarships = db.Table(
    "saved_scholarships",
    db.Column("user_id", db.Integer, db.ForeignKey(
        "user.id"), primary_key=True),
    db.Column("scholarship_id", db.Integer, db.ForeignKey(
        "scholarship.id"), primary_key=True),
)


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(160), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), default="student", nullable=False)
    applications = db.relationship(
        "Application", backref="student", lazy=True, cascade="all, delete-orphan")
    documents = db.relationship(
        "Document", backref="owner", lazy=True, cascade="all, delete-orphan")
    saved = db.relationship(
        "Scholarship", secondary=saved_scholarships, backref="saved_by")
    profile = db.relationship(
        "StudentProfile", backref="user", uselist=False, cascade="all, delete-orphan")

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class University(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(180), nullable=False)
    country = db.Column(db.String(80), nullable=False)
    city = db.Column(db.String(80), nullable=False)
    description = db.Column(db.Text, default="")
    website = db.Column(db.String(255), default="")
    tuition = db.Column(db.String(80), default="Varies by program")
    scholarships = db.relationship(
        "Scholarship", backref="university", lazy=True, cascade="all, delete-orphan")
    applications = db.relationship(
        "Application", backref="university", lazy=True)


class Scholarship(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(180), nullable=False)
    provider = db.Column(db.String(180), nullable=False)
    degree_level = db.Column(db.String(80), nullable=False)
    field = db.Column(db.String(120), nullable=False)
    funding = db.Column(db.String(80), nullable=False)
    language = db.Column(db.String(80), default="English")
    deadline = db.Column(db.Date, nullable=False)
    amount = db.Column(db.String(120), default="See provider details")
    description = db.Column(db.Text, default="")
    eligibility = db.Column(db.Text, default="")
    gpa_requirement = db.Column(db.Float, default=0)
    ielts_requirement = db.Column(db.Float, default=0)
    application_fee = db.Column(db.String(80), default="No fee")
    verified_status = db.Column(db.String(30), default="Verified")
    open = db.Column(db.Boolean, default=True)
    required_documents = db.Column(
        db.Text, default="Passport, Transcript, CV, Motivation Letter")
    university_id = db.Column(
        db.Integer, db.ForeignKey("university.id"), nullable=True)


class Application(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    program = db.Column(db.String(180), nullable=False)
    status = db.Column(db.String(60), default="Not Started", nullable=False)
    deadline = db.Column(db.Date, nullable=False)
    notes = db.Column(db.Text, default="")
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    university_id = db.Column(db.Integer, db.ForeignKey(
        "university.id"), nullable=False)
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    progress = db.Column(db.Integer, default=0)
    checklist = db.relationship(
        "ApplicationChecklist", backref="application", lazy=True, cascade="all, delete-orphan")


class Document(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(160), nullable=False)
    category = db.Column(db.String(80), default="General")
    status = db.Column(db.String(40), default="Ready")
    expires_on = db.Column(db.Date, nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)


class StudentProfile(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    country = db.Column(db.String(80), default="Afghanistan")
    education_level = db.Column(db.String(80), default="Bachelor's")
    field = db.Column(db.String(120), default="Computer Science")
    gpa = db.Column(db.Float, default=3.0)
    english_score = db.Column(db.Float, default=6.5)
    graduation_year = db.Column(db.Integer, default=2027)
    preferred_countries = db.Column(
        db.String(255), default="Finland, Germany, Canada")
    budget = db.Column(db.String(80), default="Fully funded")
    user_id = db.Column(db.Integer, db.ForeignKey(
        "user.id"), unique=True, nullable=False)


class ApplicationChecklist(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(160), nullable=False)
    complete = db.Column(db.Boolean, default=False)
    application_id = db.Column(db.Integer, db.ForeignKey(
        "application.id"), nullable=False)


class GoogleUpdate(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    link = db.Column(db.String(1000), unique=True, nullable=False)
    snippet = db.Column(db.Text, default="")
    source = db.Column(db.String(255), default="Google Search")
    category = db.Column(db.String(40), nullable=False)
    search_query = db.Column("query", db.String(255), default="")
    fetched_at = db.Column(
        db.DateTime, server_default=db.func.now(), nullable=False)


def upgrade_schema(flask_app):
    """Add new MVP columns to an existing SQLite/MySQL database without data loss."""
    additions = {
        "scholarship": [("gpa_requirement", "FLOAT DEFAULT 0"), ("ielts_requirement", "FLOAT DEFAULT 0"), ("application_fee", "VARCHAR(80) DEFAULT 'No fee'"), ("verified_status", "VARCHAR(30) DEFAULT 'Verified'"), ("open", "BOOLEAN DEFAULT 1"), ("required_documents", "TEXT")],
        "application": [("progress", "INTEGER DEFAULT 0")],
    }
    with flask_app.app_context():
        inspector = inspect(db.engine)
        for table, columns in additions.items():
            existing = {column["name"]
                        for column in inspector.get_columns(table)}
            for name, definition in columns:
                if name not in existing:
                    db.session.execute(
                        text(f"ALTER TABLE {table} ADD COLUMN {name} {definition}"))
        db.session.commit()


def get_profile(user):
    if not user.profile:
        user.profile = StudentProfile(user_id=user.id)
        db.session.commit()
    return user.profile


def match_score(profile, scholarship):
    score = 40
    reasons = []
    if profile.education_level == scholarship.degree_level:
        score += 20
        reasons.append("Degree level aligned")
    if profile.field.lower() in scholarship.field.lower() or scholarship.field == "All fields":
        score += 15
        reasons.append("Field of study aligned")
    if profile.english_score >= (scholarship.ielts_requirement or 0):
        score += 10
        reasons.append("English requirement met")
    if profile.gpa >= (scholarship.gpa_requirement or 0):
        score += 10
        reasons.append("Academic requirement met")
    if scholarship.funding == profile.budget:
        score += 5
        reasons.append("Funding preference aligned")
    return min(score, 99), reasons[:3]


def ensure_checklist(application):
    if application.checklist:
        return
    names = ["Passport", "Transcript", "CV", "Motivation Letter",
             "Recommendation Letter", "Submit Application"]
    db.session.add_all([ApplicationChecklist(
        name=name, application_id=application.id) for name in names])


def google_search_configured():
    return bool(os.getenv("GOOGLE_API_KEY") and os.getenv("GOOGLE_CSE_ID"))


def fetch_google_updates():
    """Fetch and cache public Google results; official pages remain authoritative."""
    if not google_search_configured():
        return 0
    queries = [item.strip() for item in os.getenv(
        "GOOGLE_SEARCH_QUERIES", "scholarships for Afghan students,university admissions international students").split(",") if item.strip()]
    added = 0
    for query in queries[:6]:
        category = "Scholarships" if "scholar" in query.lower() else "Admissions"
        try:
            response = requests.get("https://www.googleapis.com/customsearch/v1", params={
                "key": os.getenv("GOOGLE_API_KEY"), "cx": os.getenv("GOOGLE_CSE_ID"), "q": query, "num": 10,
            }, timeout=10)
            response.raise_for_status()
            payload = response.json()
        except (requests.RequestException, ValueError):
            continue
        for result in payload.get("items", []):
            link = result.get("link")
            if not link or GoogleUpdate.query.filter_by(link=link).first():
                continue
            db.session.add(GoogleUpdate(title=result.get("title", "Untitled update")[:255], link=link, snippet=result.get(
                "snippet", ""), source=result.get("displayLink", "Google Search"), category=category, search_query=query))
            added += 1
    db.session.commit()
    return added


def refresh_google_updates_if_stale():
    latest = GoogleUpdate.query.order_by(
        GoogleUpdate.fetched_at.desc()).first()
    if not latest or not latest.fetched_at or datetime.utcnow() - latest.fetched_at > timedelta(minutes=30):
        fetch_google_updates()


def days_left(deadline):
    return (deadline - date.today()).days


def admin_required(view):
    @wraps(view)
    @login_required
    def wrapped(*args, **kwargs):
        if current_user.role != "admin":
            abort(403)
        return view(*args, **kwargs)
    return wrapped


@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))


def seed_data():
    if User.query.first():
        return
    demo = User(name="Hafiz Rahman", email="hafiz@example.com", role="student")
    demo.set_password("password")
    admin = User(name="ScholarHub Admin",
                 email="admin@example.com", role="admin")
    admin.set_password("password")
    universities = [
        University(name="Aalto University", country="Finland", city="Espoo", tuition="€12,000–€15,000 / year",
                   website="https://www.aalto.fi", description="A leading Nordic university known for technology, design, and business."),
        University(name="University of Toronto", country="Canada", city="Toronto", tuition="CAD 38,000–55,000 / year",
                   website="https://www.utoronto.ca", description="A globally recognized research university with a broad international community."),
        University(name="University of Melbourne", country="Australia", city="Melbourne", tuition="AUD 34,000–48,000 / year",
                   website="https://www.unimelb.edu.au", description="Australia's leading university for ambitious students and interdisciplinary research."),
        University(name="Technical University of Munich", country="Germany", city="Munich", tuition="Low or no tuition",
                   website="https://www.tum.de", description="A high-impact technical university at the heart of Europe's innovation network."),
    ]
    db.session.add_all([demo, admin, *universities])
    db.session.flush()
    today = date.today()
    scholarships = [
        Scholarship(title="Aalto Excellence Scholarship", provider="Aalto University", degree_level="Master's", field="Computer Science", funding="Fully funded", language="English", deadline=today + timedelta(days=18),
                    amount="100% tuition waiver", university_id=universities[0].id, description="For high-achieving students joining Aalto's technology programs.", eligibility="Excellent academic record and admission to an eligible master's program."),
        Scholarship(title="Ontario Graduate Fellowship", provider="University of Toronto", degree_level="Master's", field="All fields", funding="Partial funding", language="English", deadline=today + timedelta(days=34), amount="CAD 15,000",
                    university_id=universities[1].id, description="Competitive support for graduate students pursuing research and professional programs.", eligibility="Full-time graduate enrollment and strong academic standing."),
        Scholarship(title="Melbourne International Undergraduate Scholarship", provider="University of Melbourne", degree_level="Bachelor's", field="All fields", funding="Partial funding", language="English", deadline=today + timedelta(days=49),
                    amount="Up to AUD 100,000", university_id=universities[2].id, description="Rewarding talented international students beginning their undergraduate journey.", eligibility="International student with an outstanding secondary school result."),
        Scholarship(title="TUM Global Scholarship", provider="Technical University of Munich", degree_level="Master's", field="Engineering", funding="Fully funded", language="English / German", deadline=today + timedelta(days=67),
                    amount="€6,000 per year", university_id=universities[3].id, description="Support for talented international students in technical disciplines.", eligibility="Admission to TUM and demonstrated financial need or exceptional merit."),
        Scholarship(title="Nordic Future Leaders Award", provider="Nordic Education Foundation", degree_level="Bachelor's", field="Sustainability", funding="Fully funded", language="English", deadline=today + timedelta(days=12),
                    amount="Tuition and living stipend", description="A leadership award for students creating measurable environmental impact.", eligibility="Portfolio of community work and a clear sustainability study plan."),
    ]
    db.session.add_all(scholarships)
    db.session.flush()
    demo.saved.extend([scholarships[0], scholarships[4]])
    db.session.add_all([
        Application(program="BSc Computer Science", status="Documents Preparing", deadline=today + timedelta(days=11),
                    user_id=demo.id, university_id=universities[0].id, notes="Request recommendation letter from Ms. Khan."),
        Application(program="MSc Data Science", status="Submitted", deadline=today +
                    timedelta(days=28), user_id=demo.id, university_id=universities[3].id),
        Document(name="Passport", category="Identity",
                 status="Ready", user_id=demo.id),
        Document(name="Academic Transcript", category="Academic",
                 status="Ready", user_id=demo.id),
        Document(name="English Certificate", category="Test score", status="Ready",
                 expires_on=today + timedelta(days=320), user_id=demo.id),
        Document(name="Motivation Letter", category="Writing",
                 status="Draft", user_id=demo.id),
    ])
    db.session.commit()


def create_app():
    flask_app = Flask(__name__)
    flask_app.config["SECRET_KEY"] = os.getenv(
        "SECRET_KEY", "dev-secret-change-me")
    flask_app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv(
        "DATABASE_URL", "sqlite:///scholarhub.db")
    flask_app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    db.init_app(flask_app)
    login_manager.init_app(flask_app)
    flask_app.jinja_env.globals["days_left"] = days_left
    with flask_app.app_context():
        db.create_all()
        upgrade_schema(flask_app)
        seed_data()

    @flask_app.route("/")
    def home():
        if current_user.is_authenticated:
            return redirect(url_for("dashboard"))
        return render_template("landing.html")

    @flask_app.route("/register", methods=["GET", "POST"])
    def register():
        if current_user.is_authenticated:
            return redirect(url_for("dashboard"))
        if request.method == "POST":
            name = request.form.get("name", "").strip()
            email = request.form.get("email", "").strip().lower()
            password = request.form.get("password", "")
            if not name or not email or len(password) < 6:
                flash(
                    "Enter your name, a valid email, and a password of at least 6 characters.", "error")
            elif User.query.filter_by(email=email).first():
                flash("An account with that email already exists.", "error")
            else:
                user = User(name=name, email=email)
                user.set_password(password)
                db.session.add(user)
                db.session.commit()
                login_user(user)
                return redirect(url_for("dashboard"))
        return render_template("auth.html", mode="register")

    @flask_app.route("/login", methods=["GET", "POST"])
    def login():
        if current_user.is_authenticated:
            return redirect(url_for("dashboard"))
        if request.method == "POST":
            user = User.query.filter_by(email=request.form.get(
                "email", "").strip().lower()).first()
            if user and user.check_password(request.form.get("password", "")):
                login_user(user, remember=True)
                return redirect(url_for("dashboard"))
            flash("Email or password is incorrect.", "error")
        return render_template("auth.html", mode="login")

    @flask_app.route("/logout")
    @login_required
    def logout():
        logout_user()
        return redirect(url_for("home"))

    @flask_app.route("/dashboard")
    @login_required
    def dashboard():
        applications = Application.query.filter_by(
            user_id=current_user.id).order_by(Application.deadline).all()
        upcoming = sorted([item for item in applications if days_left(
            item.deadline) >= 0], key=lambda item: item.deadline)[:4]
        saved = current_user.saved
        student_profile = get_profile(current_user)
        recommended = sorted([(match_score(student_profile, item)[0], item) for item in Scholarship.query.filter_by(
            open=True).all()], reverse=True, key=lambda item: item[0])[:3]
        attention = sum(1 for item in applications if item.status not in [
                        "Submitted", "Accepted", "Rejected"] and days_left(item.deadline) <= 7)
        return render_template("dashboard.html", applications=applications, upcoming=upcoming, saved=saved, scholarship_count=Scholarship.query.count(), recommended=recommended, attention=attention, profile=student_profile)

    @flask_app.route("/profile", methods=["GET", "POST"])
    @login_required
    def profile():
        student_profile = get_profile(current_user)
        if request.method == "POST":
            student_profile.country = request.form.get(
                "country", "Afghanistan")
            student_profile.education_level = request.form.get(
                "education_level", "Bachelor's")
            student_profile.field = request.form.get(
                "field", "Computer Science")
            student_profile.gpa = float(request.form.get("gpa", 0) or 0)
            student_profile.english_score = float(
                request.form.get("english_score", 0) or 0)
            student_profile.graduation_year = int(
                request.form.get("graduation_year", 2027) or 2027)
            student_profile.preferred_countries = request.form.get(
                "preferred_countries", "")
            student_profile.budget = request.form.get("budget", "Fully funded")
            db.session.commit()
            flash("Your matching profile is updated.", "success")
            return redirect(url_for("profile"))
        return render_template("profile.html", profile=student_profile)

    @flask_app.route("/scholarships")
    @login_required
    def scholarships():
        query = request.args.get("q", "").strip()
        country = request.args.get("country", "")
        degree = request.args.get("degree", "")
        funding = request.args.get("funding", "")
        language = request.args.get("language", "")
        verified = request.args.get("verified", "")
        max_days = request.args.get("max_days", "")
        statement = Scholarship.query.outerjoin(University)
        if query:
            like = f"%{query}%"
            statement = statement.filter(or_(Scholarship.title.ilike(like), Scholarship.provider.ilike(
                like), Scholarship.field.ilike(like), University.name.ilike(like)))
        if country:
            statement = statement.filter(University.country == country)
        if degree:
            statement = statement.filter(Scholarship.degree_level == degree)
        if funding:
            statement = statement.filter(Scholarship.funding == funding)
        if language:
            statement = statement.filter(
                Scholarship.language.ilike(f"%{language}%"))
        if verified:
            statement = statement.filter(
                Scholarship.verified_status == verified)
        if max_days.isdigit():
            statement = statement.filter(
                Scholarship.deadline <= date.today() + timedelta(days=int(max_days)))
        results = statement.order_by(Scholarship.deadline).all()
        countries = [row[0] for row in db.session.query(
            University.country).distinct().order_by(University.country)]
        student_profile = get_profile(current_user)
        matches = {item.id: match_score(student_profile, item)
                   for item in results}
        return render_template("scholarships.html", scholarships=results, countries=countries, filters={"q": query, "country": country, "degree": degree, "funding": funding, "language": language, "verified": verified, "max_days": max_days}, matches=matches)

    @flask_app.route("/scholarships/<int:scholarship_id>/save", methods=["POST"])
    @login_required
    def save_scholarship(scholarship_id):
        scholarship = db.get_or_404(Scholarship, scholarship_id)
        if scholarship in current_user.saved:
            current_user.saved.remove(scholarship)
        else:
            current_user.saved.append(scholarship)
        db.session.commit()
        return redirect(request.referrer or url_for("scholarships"))

    @flask_app.route("/scholarships/<int:scholarship_id>")
    @login_required
    def scholarship_detail(scholarship_id):
        scholarship = db.get_or_404(Scholarship, scholarship_id)
        return render_template("scholarship_detail.html", scholarship=scholarship)

    @flask_app.route("/universities")
    @login_required
    def universities():
        query = request.args.get("q", "").strip()
        statement = University.query
        if query:
            like = f"%{query}%"
            statement = statement.filter(or_(University.name.ilike(
                like), University.country.ilike(like), University.city.ilike(like)))
        return render_template("universities.html", universities=statement.order_by(University.name).all(), query=query)

    @flask_app.route("/applications", methods=["GET", "POST"])
    @login_required
    def applications():
        if request.method == "POST":
            university = db.get_or_404(
                University, int(request.form["university_id"]))
            application = Application(program=request.form["program"].strip(), status=request.form.get("status", "Not Started"), deadline=date.fromisoformat(
                request.form["deadline"]), notes=request.form.get("notes", "").strip(), student=current_user, university=university)
            db.session.add(application)
            db.session.commit()
            ensure_checklist(application)
            db.session.commit()
            flash("Application added to your tracker.", "success")
            return redirect(url_for("applications"))
        applications_list = Application.query.filter_by(
            user_id=current_user.id).order_by(Application.deadline).all()
        for application in applications_list:
            ensure_checklist(application)
        db.session.commit()
        return render_template("applications.html", applications=applications_list, universities=University.query.order_by(University.name).all(), statuses=application_statuses)

    @flask_app.route("/applications/<int:application_id>/status", methods=["POST"])
    @login_required
    def update_application(application_id):
        application = db.get_or_404(Application, application_id)
        if application.user_id != current_user.id:
            abort(403)
        application.status = request.form["status"]
        application.progress = max(
            0, min(100, int(request.form.get("progress", application.progress or 0))))
        db.session.commit()
        return redirect(url_for("applications"))

    @flask_app.route("/applications/<int:application_id>/checklist/<int:item_id>", methods=["POST"])
    @login_required
    def toggle_checklist(application_id, item_id):
        application = db.get_or_404(Application, application_id)
        item = db.get_or_404(ApplicationChecklist, item_id)
        if application.user_id != current_user.id or item.application_id != application.id:
            abort(403)
        item.complete = not item.complete
        items = application.checklist
        application.progress = round(sum(
            1 for checklist_item in items if checklist_item.complete) / len(items) * 100) if items else 0
        db.session.commit()
        return redirect(url_for("applications"))

    @flask_app.route("/documents", methods=["GET", "POST"])
    @login_required
    def documents():
        if request.method == "POST":
            document = Document(name=request.form["name"].strip(), category=request.form.get(
                "category", "General"), status=request.form.get("status", "Ready"), user_id=current_user.id)
            db.session.add(document)
            db.session.commit()
            flash("Document added.", "success")
            return redirect(url_for("documents"))
        return render_template("documents.html", documents=Document.query.filter_by(user_id=current_user.id).order_by(Document.name).all())

    @flask_app.route("/countries")
    @login_required
    def countries():
        grouped = {}
        for university in University.query.order_by(University.country, University.name).all():
            grouped.setdefault(university.country, []).append(university)
        return render_template("countries.html", countries=grouped)

    @flask_app.route("/updates")
    @login_required
    def updates():
        refresh_google_updates_if_stale()
        category = request.args.get("category", "")
        statement = GoogleUpdate.query
        if category in ["Scholarships", "Admissions"]:
            statement = statement.filter_by(category=category)
        return render_template("updates.html", updates=statement.order_by(GoogleUpdate.fetched_at.desc()).limit(80).all(), category=category, configured=google_search_configured())

    @flask_app.route("/calendar")
    @login_required
    def calendar():
        application_events = [{"date": item.deadline, "title": item.university.name, "kind": "Application",
                               "detail": item.program} for item in Application.query.filter_by(user_id=current_user.id).all()]
        scholarship_events = [{"date": item.deadline, "title": item.title,
                               "kind": "Scholarship", "detail": item.provider} for item in current_user.saved]
        events = sorted(application_events + scholarship_events,
                        key=lambda item: item["date"])
        return render_template("calendar.html", events=events)

    @flask_app.route("/compare")
    @login_required
    def compare():
        selected = current_user.saved[:3]
        return render_template("compare.html", scholarships=selected)

    @flask_app.route("/materials")
    @login_required
    def materials():
        materials_list = [("CV", "Keep one strong master CV, then tailor it per program.", "Ready"), ("Motivation letter", "A reusable structure for your story, goals, and fit.", "Draft"), ("Personal statement", "Your academic direction in your own voice.",
                                                                                                                                                                                              "Template"), ("Study plan", "Connect your chosen program to a clear future impact.", "Template"), ("Recommendation request", "A prepared request makes it easier for referees to help.", "Template")]
        return render_template("materials.html", materials=materials_list)

    @flask_app.route("/assistant", methods=["GET", "POST"])
    @login_required
    def assistant():
        question = request.form.get("question", "").strip(
        ) if request.method == "POST" else ""
        student_profile = get_profile(current_user)
        results = Scholarship.query.filter(Scholarship.open.is_(True)).all()
        if question:
            keywords = question.lower().split()
            results = [item for item in results if any(keyword in f"{item.title} {item.field} {item.provider} {item.university.country if item.university else ''}".lower(
            ) for keyword in keywords if len(keyword) > 3)] or results
        recommendations = sorted([(match_score(student_profile, item)[
                                 0], item) for item in results], reverse=True, key=lambda item: item[0])[:4]
        return render_template("assistant.html", question=question, recommendations=recommendations)

    @flask_app.route("/admin")
    @admin_required
    def admin():
        return render_template("admin.html", users=User.query.count(), scholarships=Scholarship.query.count(), universities=University.query.count(), applications=Application.query.count())

    @flask_app.route("/admin/updates/sync", methods=["POST"])
    @admin_required
    def sync_updates():
        if not google_search_configured():
            flash("Google Search is not configured. Add GOOGLE_API_KEY and GOOGLE_CSE_ID to your .env file.", "error")
        else:
            added = fetch_google_updates()
            flash(
                f"Google updates synced. {added} new result(s) added.", "success")
        return redirect(url_for("updates"))

    return flask_app


app = create_app()

if __name__ == "__main__":
    app.run(debug=True)
