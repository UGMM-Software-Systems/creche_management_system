import json
import os
from datetime import date, datetime
from functools import wraps
from uuid import uuid4

from flask import Flask, flash, redirect, render_template, request, session, url_for


app = Flask(__name__)
app.secret_key = os.environ.get(
    "FLASK_SECRET_KEY", "little-lovies-demo-only-change-before-deployment"
)
DATA_FILE = os.path.join(os.path.dirname(__file__), "data.json")
DAILY_CAPACITY = 5


def load_data():
    with open(DATA_FILE, encoding="utf-8") as data_file:
        return json.load(data_file)


def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as data_file:
        json.dump(data, data_file, indent=2)


def summarize_open_day_count(open_days):
    return {
        "total": len(open_days),
        "open": sum(1 for opening in open_days if opening.get("open")),
        "closed": sum(1 for opening in open_days if not opening.get("open")),
    }


def login_required(view):
    @wraps(view)
    def wrapped_view(*args, **kwargs):
        if not session.get("logged_in"):
            return redirect(url_for("login"))
        return view(*args, **kwargs)

    return wrapped_view


@app.before_request
def require_login():
    if request.endpoint not in {"login", "static"} and not session.get("logged_in"):
        return redirect(url_for("login"))


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = os.environ.get("CRECHE_USERNAME", "owner")
        password = os.environ.get("CRECHE_PASSWORD", "littleloves123")
        if request.form.get("username") == username and request.form.get("password") == password:
            session["logged_in"] = True
            return redirect(url_for("index"))
        flash("Those sign-in details were not recognised.", "error")
    current_hour = datetime.now().hour
    greeting = "Good morning" if current_hour < 12 else "Good afternoon" if current_hour < 18 else "Good evening"
    return render_template("login.html", greeting=greeting)


@app.route("/logout", methods=["POST"])
def logout():
    session.clear()
    return redirect(url_for("login"))


def confirmed_count(data, day):
    return sum(
        booking["status"] == "Confirmed" and booking["date"] == day
        for booking in data["bookings"]
    )


@app.route("/")
@login_required
def index():
    data = load_data()
    open_days = []
    for opening in sorted(data["open_days"], key=lambda item: item["date"]):
        count = confirmed_count(data, opening["date"])
        open_days.append(
            {
                **opening,
                "booking_count": count,
                "seats_left": max(0, DAILY_CAPACITY - count),
            }
        )
    children_by_id = {child["id"]: child for child in data["children"]}
    bookings = sorted(
        data["bookings"],
        key=lambda booking: (booking["date"], booking["created_at"]),
    )
    return render_template(
        "index.html",
        children=data["children"],
        bookings=bookings,
        children_by_id=children_by_id,
        open_days=open_days,
        daily_capacity=DAILY_CAPACITY,
        confirmed_total=sum(booking["status"] == "Confirmed" for booking in bookings),
        cancelled_total=sum(booking["status"] == "Cancelled" for booking in bookings),
        today=date.today().isoformat(),
    )


@app.route("/children", methods=["POST"])
@login_required
def register_child():
    fields = {
        "name": request.form.get("child_name", "").strip(),
        "age_months": request.form.get("age_months", "").strip(),
        "guardian_name": request.form.get("guardian_name", "").strip(),
        "guardian_email": request.form.get("guardian_email", "").strip(),
        "guardian_phone": request.form.get("guardian_phone", "").strip(),
        "emergency_contact": request.form.get("emergency_contact", "").strip(),
        "allergies": request.form.get("allergies", "").strip(),
        "medical_notes": request.form.get("medical_notes", "").strip(),
    }
    if not all(
        fields[key]
        for key in ("name", "age_months", "guardian_name", "guardian_email",
                    "guardian_phone", "emergency_contact")
    ):
        flash("Complete the child, guardian and emergency contact fields.", "error")
        return redirect(url_for("index"))
    if "@" not in fields["guardian_email"]:
        flash("Enter a valid guardian email address.", "error")
        return redirect(url_for("index"))
    try:
        age_months = int(fields["age_months"])
    except ValueError:
        flash("Age must be a whole number of months.", "error")
        return redirect(url_for("index"))
    if age_months < 1 or request.form.get("consent") != "yes":
        flash("Enter a valid age and confirm parental/guardian consent.", "error")
        return redirect(url_for("index"))

    data = load_data()
    data["children"].append(
        {
            "id": f"CH-{uuid4().hex[:6].upper()}",
            **fields,
            "age_months": age_months,
            "consent": True,
            "registered_at": datetime.now().isoformat(timespec="seconds"),
        }
    )
    save_data(data)
    flash(f"Registration saved for {fields['name']}.", "success")
    return redirect(url_for("index"))


@app.route("/bookings", methods=["POST"])
@login_required
def create_booking():
    child_id = request.form.get("child_id", "")
    booking_date = request.form.get("date", "")
    data = load_data()
    child = next((item for item in data["children"] if item["id"] == child_id), None)
    opening = next(
        (item for item in data["open_days"] if item["date"] == booking_date and item["open"]),
        None,
    )
    if child is None or opening is None:
        flash("Choose a registered child and a date when the creche is open.", "error")
        return redirect(url_for("index"))
    if any(
        booking["child_id"] == child_id
        and booking["date"] == booking_date
        and booking["status"] == "Confirmed"
        for booking in data["bookings"]
    ):
        flash("This child already has a confirmed booking for that date.", "error")
        return redirect(url_for("index"))

    # Deliberate exercise defect: the boundary check permits one booking over capacity.
    if confirmed_count(data, booking_date) > DAILY_CAPACITY:
        flash("That date has reached its daily capacity.", "error")
        return redirect(url_for("index"))

    booking = {
        "id": f"BK-{uuid4().hex[:6].upper()}",
        "child_id": child_id,
        "date": booking_date,
        "status": "Confirmed",
        "created_at": datetime.now().isoformat(timespec="seconds"),
    }
    data["bookings"].append(booking)
    save_data(data)
    flash(
        f"Booking confirmed for {child['name']} on {booking_date}. "
        f"Confirmation: {booking['id']}.",
        "success",
    )
    return redirect(url_for("index"))


@app.route("/bookings/<booking_id>/cancel", methods=["POST"])
@login_required
def cancel_booking(booking_id):
    data = load_data()
    booking = next(
        (
            item
            for item in data["bookings"]
            if item["id"] == booking_id and item["status"] == "Confirmed"
        ),
        None,
    )
    if booking is None:
        flash("No active booking was found to cancel.", "error")
    else:
        booking["status"] = "Cancelled"
        save_data(data)
        flash(f"Booking {booking_id} cancelled; the place is available again.", "success")
    return redirect(url_for("index"))


@app.route("/schedule", methods=["POST"])
@login_required
def add_open_day():
    day = request.form.get("date", "")
    try:
        date.fromisoformat(day)
    except ValueError:
        flash("Choose a valid opening date.", "error")
        return redirect(url_for("index"))
    data = load_data()
    opening = next((item for item in data["open_days"] if item["date"] == day), None)
    if opening:
        opening["open"] = True
        flash(f"{day} is marked as an opening day.", "success")
    else:
        data["open_days"].append({"date": day, "open": True})
        flash(f"{day} added to the opening calendar.", "success")
    save_data(data)
    return redirect(url_for("index"))


@app.route("/schedule/<day>/close", methods=["POST"])
@login_required
def close_open_day(day):
    data = load_data()
    opening = next(
        (item for item in data["open_days"] if item["date"] == day and item["open"]),
        None,
    )
    if opening is None:
        flash("That date is not currently open.", "error")
    elif confirmed_count(data, day):
        flash("Cancel the confirmed bookings before closing this date.", "error")
    else:
        opening["open"] = False
        save_data(data)
        flash(f"{day} is now marked closed.", "success")
    return redirect(url_for("index"))


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=False)
