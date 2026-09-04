import os
import sqlite3
from datetime import date, datetime, timedelta
from pathlib import Path

from flask import Flask, jsonify, render_template, request

app = Flask(__name__)
DATABASE_PATH = Path(os.environ.get(
    "DATABASE_PATH", Path(__file__).with_name("hotel.db")))


def connect_db():
    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def rows_to_dicts(rows):
    return [dict(row) for row in rows]


def seed_database():
    with connect_db() as db:
        db.executescript(
            """
            CREATE TABLE IF NOT EXISTS rooms (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                number TEXT UNIQUE NOT NULL,
                room_type TEXT NOT NULL,
                floor INTEGER NOT NULL,
                rate REAL NOT NULL,
                status TEXT NOT NULL DEFAULT 'Clean',
                notes TEXT DEFAULT ''
            );
            CREATE TABLE IF NOT EXISTS guests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                first_name TEXT NOT NULL,
                last_name TEXT NOT NULL,
                email TEXT DEFAULT '',
                phone TEXT DEFAULT '',
                vip INTEGER NOT NULL DEFAULT 0,
                notes TEXT DEFAULT '',
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS reservations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                confirmation_code TEXT UNIQUE NOT NULL,
                guest_id INTEGER NOT NULL REFERENCES guests(id),
                room_id INTEGER REFERENCES rooms(id),
                check_in TEXT NOT NULL,
                check_out TEXT NOT NULL,
                adults INTEGER NOT NULL DEFAULT 1,
                children INTEGER NOT NULL DEFAULT 0,
                total_amount REAL NOT NULL DEFAULT 0,
                payment_status TEXT NOT NULL DEFAULT 'Due',
                status TEXT NOT NULL DEFAULT 'Confirmed',
                source TEXT NOT NULL DEFAULT 'Direct',
                notes TEXT DEFAULT '',
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                room_id INTEGER REFERENCES rooms(id),
                task_type TEXT NOT NULL,
                description TEXT NOT NULL,
                assignee TEXT NOT NULL DEFAULT 'Unassigned',
                priority TEXT NOT NULL DEFAULT 'Normal',
                status TEXT NOT NULL DEFAULT 'Open',
                due_time TEXT DEFAULT '',
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
            """
        )
        if db.execute("SELECT COUNT(*) FROM rooms").fetchone()[0] == 0:
            room_rows = [
                ("101", "Deluxe King", 1, 156, "Clean"), ("102",
                                                          "Deluxe King", 1, 156, "Occupied"),
                ("103", "Twin Room", 1, 132, "Dirty"), ("104",
                                                        "Garden Suite", 1, 240, "Checkout"),
                ("201", "Executive Suite", 2, 310,
                 "Occupied"), ("202", "Deluxe King", 2, 156, "Clean"),
                ("203", "Twin Room", 2, 132, "Inspected"), ("204",
                                                            "Deluxe King", 2, 156, "Maintenance"),
                ("301", "Garden Suite", 3, 240, "Occupied"), ("302",
                                                              "Deluxe King", 3, 156, "Clean"),
                ("303", "Executive Suite", 3, 310,
                 "Occupied"), ("304", "Deluxe King", 3, 156, "Clean"),
            ]
            db.executemany(
                "INSERT INTO rooms (number, room_type, floor, rate, status) VALUES (?, ?, ?, ?, ?)", room_rows)
            guests = [
                ("Maya", "Chen", "maya.chen@example.com", "+1 555 0182", 1),
                ("Oliver", "Grant", "oliver.grant@example.com", "+1 555 0183", 0),
                ("Sofia", "Alvarez", "sofia.alvarez@example.com", "+1 555 0184", 0),
                ("Liam", "Brooks", "liam.brooks@example.com", "+1 555 0185", 0),
                ("Amelia", "James", "amelia.james@example.com", "+1 555 0186", 0),
                ("Noah", "Wilson", "noah.wilson@example.com", "+1 555 0187", 0),
                ("Emma", "Davis", "emma.davis@example.com", "+1 555 0188", 1),
            ]
            db.executemany(
                "INSERT INTO guests (first_name, last_name, email, phone, vip) VALUES (?, ?, ?, ?, ?)", guests)
            today = date.today()
            reservation_rows = [
                ("LS-2401", 1, 1, today.isoformat(), (today + timedelta(days=2)
                                                      ).isoformat(), 2, 0, 312, "Paid", "Arriving", "Direct"),
                ("LS-2402", 2, 4, today.isoformat(), (today + timedelta(days=4)
                                                      ).isoformat(), 2, 1, 960, "Due", "Arriving", "Booking.com"),
                ("LS-2403", 3, 3, today.isoformat(), (today + timedelta(days=1)
                                                      ).isoformat(), 1, 0, 132, "Paid", "Arriving", "Direct"),
                ("LS-2404", 4, 5, today.isoformat(), (today + timedelta(days=3)
                                                      ).isoformat(), 2, 0, 930, "Paid", "Arriving", "Corporate"),
                ("LS-2392", 5, 4, (today - timedelta(days=2)).isoformat(),
                 today.isoformat(), 2, 0, 480, "Paid", "Departing", "Direct"),
                ("LS-2393", 6, 6, (today - timedelta(days=3)).isoformat(),
                 today.isoformat(), 1, 0, 468, "Paid", "Departing", "Direct"),
                ("LS-2394", 7, 9, (today - timedelta(days=1)).isoformat(),
                 today.isoformat(), 2, 0, 620, "Paid", "Departed", "Direct"),
            ]
            db.executemany("""INSERT INTO reservations
                (confirmation_code, guest_id, room_id, check_in, check_out, adults, children, total_amount, payment_status, status, source)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""", reservation_rows)
            tasks = [
                (3, "Turnover", "Turnover · arrival 13:40",
                 "Nora", "Urgent", "Open", "13:40"),
                (8, "Engineering", "Engineering · AC check",
                 "Marco", "High", "Open", "14:00"),
                (4, "Inspection", "Inspect after checkout",
                 "You", "High", "Open", "11:30"),
                (10, "Refresh", "Refresh minibar", "Nora",
                 "Normal", "In progress", "15:00"),
            ]
            db.executemany("""INSERT INTO tasks
                (room_id, task_type, description, assignee, priority, status, due_time)
                VALUES (?, ?, ?, ?, ?, ?, ?)""", tasks)


def reservation_query(db, where="", params=()):
    return rows_to_dicts(db.execute(f"""SELECT r.*, g.first_name || ' ' || g.last_name AS guest_name,
        g.email, g.phone, g.vip, rm.number AS room_number, rm.room_type
        FROM reservations r JOIN guests g ON g.id = r.guest_id
        LEFT JOIN rooms rm ON rm.id = r.room_id {where}
        ORDER BY r.check_in, r.id""", params).fetchall())


def build_summary(db):
    today = date.today().isoformat()
    total_rooms = db.execute("SELECT COUNT(*) FROM rooms").fetchone()[0]
    occupied = db.execute(
        "SELECT COUNT(*) FROM rooms WHERE status = 'Occupied'").fetchone()[0]
    arrivals = db.execute(
        "SELECT COUNT(*) FROM reservations WHERE check_in = ? AND status = 'Arriving'", (today,)).fetchone()[0]
    departures = db.execute(
        "SELECT COUNT(*) FROM reservations WHERE check_out = ? AND status IN ('Departing', 'Checked in')", (today,)).fetchone()[0]
    revenue = db.execute(
        "SELECT COALESCE(SUM(total_amount), 0) FROM reservations WHERE check_in <= ? AND check_out > ? AND status != 'Cancelled'", (today, today)).fetchone()[0]
    room_revenue = db.execute(
        "SELECT COALESCE(SUM(total_amount), 0) FROM reservations WHERE check_in = ? AND status != 'Cancelled'", (today,)).fetchone()[0]
    return {
        "occupancy": round(occupied / total_rooms * 100, 1) if total_rooms else 0,
        "occupied_rooms": occupied, "total_rooms": total_rooms, "arrivals": arrivals,
        "departures": departures, "revenue": round(revenue), "room_revenue": round(room_revenue),
        "rooms_ready": db.execute("SELECT COUNT(*) FROM rooms WHERE status IN ('Clean', 'Inspected')").fetchone()[0],
        "open_tasks": db.execute("SELECT COUNT(*) FROM tasks WHERE status != 'Complete'").fetchone()[0],
    }


@app.get("/")
def dashboard():
    return render_template("index.html", page_title="LumaStay / Operations")


@app.get("/health")
def health():
    with connect_db() as db:
        db.execute("SELECT 1")
    return jsonify(status="ok", database="connected")


@app.get("/api/summary")
def summary():
    with connect_db() as db:
        return jsonify(summary=build_summary(db))


@app.get("/api/reservations")
def reservations():
    status = request.args.get("status")
    search = request.args.get("search", "").strip()
    clauses, params = [], []
    if status and status != "all":
        clauses.append("r.status = ?")
        params.append(status)
    if search:
        clauses.append(
            "(g.first_name || ' ' || g.last_name LIKE ? OR r.confirmation_code LIKE ? OR rm.number LIKE ?)")
        params.extend([f"%{search}%"] * 3)
    where = "WHERE " + " AND ".join(clauses) if clauses else ""
    with connect_db() as db:
        return jsonify(reservations=reservation_query(db, where, params))


@app.post("/api/reservations")
def create_reservation():
    payload = request.get_json(silent=True) or {}
    required = ["first_name", "last_name", "check_in", "check_out"]
    if any(not payload.get(field) for field in required):
        return jsonify(error="First name, last name, check-in and check-out are required."), 400
    if payload["check_out"] <= payload["check_in"]:
        return jsonify(error="Check-out must be after check-in."), 400
    with connect_db() as db:
        guest = db.execute("SELECT id FROM guests WHERE email = ? AND email != ''",
                           (payload.get("email", ""),)).fetchone()
        guest_id = guest["id"] if guest else db.execute(
            "INSERT INTO guests (first_name, last_name, email, phone) VALUES (?, ?, ?, ?)",
            (payload["first_name"], payload["last_name"], payload.get("email", ""), payload.get("phone", ""))).lastrowid
        room_id = payload.get("room_id") or None
        if room_id:
            conflict = db.execute("""SELECT 1 FROM reservations WHERE room_id = ? AND status NOT IN ('Cancelled', 'Departed')
                AND check_in < ? AND check_out > ?""", (room_id, payload["check_out"], payload["check_in"])).fetchone()
            if conflict:
                return jsonify(error="That room is already reserved for part of these dates."), 409
        code = f"LS-{datetime.now().strftime('%y%m%d%H%M%S')}"
        db.execute("""INSERT INTO reservations
            (confirmation_code, guest_id, room_id, check_in, check_out, adults, children, total_amount, payment_status, status, source, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'Confirmed', ?, ?)""", (code, guest_id, room_id, payload["check_in"], payload["check_out"],
                                                                       payload.get("adults", 1), payload.get("children", 0), payload.get(
                                                                           "total_amount", 0), payload.get("payment_status", "Due"),
                                                                       payload.get("source", "Direct"), payload.get("notes", "")))
        return jsonify(message="Reservation created", confirmation_code=code), 201


@app.patch("/api/reservations/<int:reservation_id>/status")
def update_reservation_status(reservation_id):
    new_status = (request.get_json(silent=True) or {}).get("status")
    allowed = {"Arriving", "Checked in", "Departing",
               "Departed", "Cancelled", "Confirmed"}
    if new_status not in allowed:
        return jsonify(error="Unsupported reservation status."), 400
    with connect_db() as db:
        reservation = db.execute(
            "SELECT room_id FROM reservations WHERE id = ?", (reservation_id,)).fetchone()
        if not reservation:
            return jsonify(error="Reservation not found."), 404
        db.execute("UPDATE reservations SET status = ? WHERE id = ?",
                   (new_status, reservation_id))
        if reservation["room_id"]:
            room_status = {"Checked in": "Occupied",
                           "Departed": "Dirty", "Cancelled": "Clean"}.get(new_status)
            if room_status:
                db.execute("UPDATE rooms SET status = ? WHERE id = ?",
                           (room_status, reservation["room_id"]))
    return jsonify(message=f"Reservation marked {new_status.lower()}.")


@app.get("/api/rooms")
def rooms():
    with connect_db() as db:
        return jsonify(rooms=rows_to_dicts(db.execute("SELECT * FROM rooms ORDER BY floor, number").fetchall()))


@app.patch("/api/rooms/<int:room_id>")
def update_room(room_id):
    status = (request.get_json(silent=True) or {}).get("status")
    if status not in {"Clean", "Occupied", "Dirty", "Inspected", "Checkout", "Maintenance"}:
        return jsonify(error="Unsupported room status."), 400
    with connect_db() as db:
        cursor = db.execute(
            "UPDATE rooms SET status = ? WHERE id = ?", (status, room_id))
        if cursor.rowcount == 0:
            return jsonify(error="Room not found."), 404
    return jsonify(message=f"Room marked {status.lower()}.")


@app.get("/api/tasks")
def tasks():
    with connect_db() as db:
        result = db.execute("""SELECT t.*, r.number AS room_number FROM tasks t
            LEFT JOIN rooms r ON r.id = t.room_id WHERE t.status != 'Complete' ORDER BY t.priority DESC, t.id""").fetchall()
        return jsonify(tasks=rows_to_dicts(result))


@app.patch("/api/tasks/<int:task_id>")
def update_task(task_id):
    status = (request.get_json(silent=True) or {}).get("status")
    if status not in {"Open", "In progress", "Complete"}:
        return jsonify(error="Unsupported task status."), 400
    with connect_db() as db:
        cursor = db.execute(
            "UPDATE tasks SET status = ? WHERE id = ?", (status, task_id))
        if cursor.rowcount == 0:
            return jsonify(error="Task not found."), 404
    return jsonify(message="Task updated.")


@app.get("/api/guests")
def guests():
    search = request.args.get("search", "").strip()
    with connect_db() as db:
        if search:
            result = db.execute("""SELECT g.*, COUNT(r.id) AS stays, MAX(r.check_out) AS last_stay
                FROM guests g LEFT JOIN reservations r ON r.guest_id = g.id
                WHERE g.first_name || ' ' || g.last_name LIKE ? OR g.email LIKE ?
                GROUP BY g.id ORDER BY g.last_name""", (f"%{search}%", f"%{search}%")).fetchall()
        else:
            result = db.execute("""SELECT g.*, COUNT(r.id) AS stays, MAX(r.check_out) AS last_stay
                FROM guests g LEFT JOIN reservations r ON r.guest_id = g.id
                GROUP BY g.id ORDER BY g.last_name""").fetchall()
        return jsonify(guests=rows_to_dicts(result))


seed_database()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", "5000")),
            debug=os.environ.get("FLASK_DEBUG", "0") == "1")
