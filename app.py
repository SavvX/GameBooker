from flask import Flask, request, jsonify, render_template, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import (
    LoginManager,
    UserMixin,
    login_user,
    login_required,
    logout_user,
    current_user,
)
import random
import string
from datetime import datetime

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///reservations.db"
app.config["SECRET_KEY"] = "your_secret_key"
db = SQLAlchemy(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"


class Reservation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    school = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(50), nullable=False)
    device = db.Column(db.String(50), nullable=False)
    password = db.Column(db.String(50), nullable=False)
    date = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)


class DeviceStatus(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    device = db.Column(db.String(50), nullable=False)
    status = db.Column(db.String(50), nullable=False)


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(50), nullable=False)


@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))


@app.route("/reserve", methods=["POST"])
def reserve():
    data = request.json
    name = data["name"]
    school = data["school"]
    email = data["email"]
    device = data["device"]

    # Check if the device is available
    device_status = DeviceStatus.query.filter_by(device=device).first()

    if device_status and device_status.status != "Available":
        return jsonify({"message": f"Device {device} is not available."}), 400

    password = "".join(random.choices(string.digits, k=4))

    reservation = Reservation(
        name=name, school=school, email=email, device=device, password=password
    )
    db.session.add(reservation)
    db.session.commit()

    # Update device status to 'Reserved'
    if device_status:
        device_status.status = "Reserved"
    else:
        new_device_status = DeviceStatus(device=device, status="Reserved")
        db.session.add(new_device_status)

    db.session.commit()

    return jsonify(
        {"message": f"Reservation successful! Password for {device}: {password}"}
    )


@app.route("/status", methods=["GET"])
def status():
    devices = [
        "PC1",
        "PC2",
        "PC3",
        "PC4",
        "PC5",
        "PC6",
        "PC7",
        "PC8",
        "PC9",
        "PC10",
        "PS5",
        "Switch1",
        "Switch2",
        "RacingSim1",
        "RacingSim2",
    ]
    status = {}
    for device in devices:
        reservation = (
            Reservation.query.filter_by(device=device)
            .order_by(Reservation.id.desc())
            .first()
        )
        status[device] = reservation.password if reservation else "Available"

    return jsonify(status)


@app.route("/update_status", methods=["POST"])
def update_status():
    data = request.json
    device = data["device"]
    status = data["status"]

    device_status = DeviceStatus.query.filter_by(device=device).first()
    if not device_status:
        device_status = DeviceStatus(device=device, status=status)
        db.session.add(device_status)
    else:
        device_status.status = status

    db.session.commit()
    return jsonify({"message": f"Status for {device} updated to {status}"})


@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        data = request.form
        name = data["name"]
        school = data["school"]
        email = data["email"]
        device = data["device"]

        # Check if the device is available
        device_status = DeviceStatus.query.filter_by(device=device).first()

        if device_status and device_status.status != "Available":
            flash(f"Device {device} is not available.")
            return redirect(url_for("index"))

        password = "".join(random.choices(string.digits, k=4))

        reservation = Reservation(
            name=name, school=school, email=email, device=device, password=password
        )
        db.session.add(reservation)
        db.session.commit()

        # Update device status to 'Reserved'
        if device_status:
            device_status.status = "Reserved"
        else:
            new_device_status = DeviceStatus(device=device, status="Reserved")
            db.session.add(new_device_status)

        db.session.commit()

        flash(f"Reservation successful! Password for {device}: {password}")
        return redirect(url_for("index"))

    return render_template("index.html")


@app.route("/admin", methods=["GET", "POST"])
@login_required
def admin():
    action = request.args.get("action", "view_reservations")
    reservations = []
    device_statuses = []

    if action == "view_reservations":
        start_date_str = request.args.get("start_date")
        end_date_str = request.args.get("end_date")

        if start_date_str and end_date_str:
            start_date = datetime.strptime(start_date_str, "%Y-%m-%d")
            end_date = datetime.strptime(end_date_str, "%Y-%m-%d")
            reservations = Reservation.query.filter(Reservation.date.between(start_date, end_date)).all()
        else:
            reservations = Reservation.query.all()

    elif action == "manage_devices":
        device_statuses = DeviceStatus.query.all()

    return render_template(
        "admin.html",
        reservations=reservations,
        device_statuses=device_statuses,
        action=action,
    )


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        user = User.query.filter_by(username=username).first()
        if user and user.password == password:
            login_user(user)
            return redirect(url_for("admin"))
        else:
            flash("Invalid username or password")
    return render_template("login.html")


@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("login"))


if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)