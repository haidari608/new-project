import os

from flask import Flask, jsonify, render_template

app = Flask(__name__)

NAV_ITEMS = ["Overview", "Reservations",
             "Rooms & rates", "Housekeeping", "Guests", "Reports"]
KPIS = [
    {"label": "Occupancy", "value": "84.6%",
        "change": "+6.2% vs last week", "detail": "118 / 139 rooms"},
    {"label": "Arrivals", "value": "24",
        "change": "8 due in next 3 hrs", "detail": "6 VIP guests"},
    {"label": "Departures", "value": "19", "change": "3 late checkouts",
        "detail": "Housekeeping ready: 14"},
    {"label": "Revenue today", "value": "$18,420",
        "change": "+12.8% vs forecast", "detail": "ADR $156 · RevPAR $132"},
]
OCCUPANCY = [{"day": day, "occupied": occupied, "forecast": forecast} for day, occupied, forecast in zip(
    ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"], [72, 78, 76, 84, 91, 96, 89], [75, 80, 81, 86, 90, 94, 91])]
REVENUE = [{"name": name, "amount": amount, "percent": percent} for name, amount, percent in [
    ("Rooms", 8420, 100), ("F&B", 4960, 59), ("Spa", 2860, 34), ("Other", 2180, 26)]]
ROOMS = [{"number": number, "type": room_type, "status": status} for number, room_type, status in [("101", "Deluxe King", "Clean"), ("102", "Deluxe King", "Occupied"), ("103", "Twin Room", "Dirty"), ("104", "Garden Suite", "Checkout"), ("201", "Executive Suite", "Occupied"), (
    "202", "Deluxe King", "Clean"), ("203", "Twin Room", "Inspected"), ("204", "Deluxe King", "Maintenance"), ("301", "Garden Suite", "Occupied"), ("302", "Deluxe King", "Clean"), ("303", "Executive Suite", "Occupied"), ("304", "Deluxe King", "Clean")]]
TASKS = [{"room": room, "description": description, "owner": owner} for room, description, owner in [("103", "Turnover · arrival 13:40", "Nora"), (
    "204", "Engineering · AC check", "Marco"), ("104", "Inspect after checkout", "You"), ("302", "Refresh minibar", "Nora")]]


@app.get("/")
def dashboard():
    return render_template("index.html", page_title="LumaStay / Operations", nav_items=NAV_ITEMS, kpis=KPIS, occupancy=OCCUPANCY, revenue=REVENUE, rooms=ROOMS, tasks=TASKS)


@app.get("/health")
def health():
    return jsonify(status="ok")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", "5000")),
            debug=os.environ.get("FLASK_DEBUG", "0") == "1")
