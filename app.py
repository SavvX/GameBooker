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
from datetime import datetime, timedelta

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


@app.route("/shutdown", methods=["POST"])
@login_required
def shutdown():
    data = request.json
    device = data["device"]

    # Send the shutdown signal to the specific device (you can use an internal API or other mechanism)
    # For now, let's assume a successful shutdown command is sent
    shutdown_success = True  # Replace this with actual shutdown logic

    if shutdown_success:
        # Update device status to 'Shut Down'
        device_status = DeviceStatus.query.filter_by(device=device).first()
        if device_status:
            device_status.status = "Shut Down"
            db.session.commit()
        return jsonify({"message": f"Shutdown command sent to {device}"}), 200
    else:
        return jsonify({"message": f"Failed to send shutdown command to {device}"}), 500

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

@app.route('/admin', methods=['GET', 'POST'])
def admin():
    action = request.args.get('action')
    frequency = request.args.get('frequency', 'daily')
    time_range = request.args.get('time_range', 'all_time')

    # Calculate start_date and end_date based on time_range
    end_date = datetime.now()
    if time_range == 'last_24_hours':
        start_date = end_date - timedelta(days=1)
    elif time_range == 'last_7_days':
        start_date = end_date - timedelta(days=7)
    elif time_range == 'last_month':
        start_date = end_date - timedelta(days=30)
    elif time_range == 'last_6_months':
        start_date = end_date - timedelta(days=180)
    elif time_range == 'last_year':
        start_date = end_date - timedelta(days=365)
    else:  # 'all_time'
        start_date = datetime(2000, 1, 1)  # Or some reasonable historical start date

    start_date_str = start_date.strftime('%Y-%m-%d')
    end_date_str = end_date.strftime('%Y-%m-%d')

    statistics_data = {
        'labels': [],
        'values': []
    }

    if action == 'statistics':
        if frequency == 'hourly':
            statistics_data = get_hourly_data(start_date, end_date)
        elif frequency == 'daily':
            statistics_data = get_daily_data(start_date, end_date)
        elif frequency == 'weekly':
            statistics_data = get_weekly_data(start_date, end_date)
        elif frequency == 'monthly':
            statistics_data = get_monthly_data(start_date, end_date)
        elif frequency == 'yearly':
            statistics_data = get_yearly_data(start_date, end_date)

    return render_template('admin.html', action=action, statistics_data=statistics_data)

def get_hourly_data(start_date, end_date):
    data = db.session.query(
        db.func.strftime('%Y-%m-%d %H:00:00', Reservation.date).label('hour'),
        db.func.count().label('count')
    ).filter(
        Reservation.date.between(start_date, end_date)
    ).group_by('hour').all()

    labels = [row.hour for row in data]
    values = [row.count for row in data]
    return {'labels': labels, 'values': values}


def get_daily_data(start_date, end_date):
    data = db.session.query(
        db.func.strftime('%Y-%m-%d', Reservation.date).label('day'),
        db.func.count().label('count')
    ).filter(
        Reservation.date.between(start_date, end_date)
    ).group_by('day').all()

    labels = [row.day for row in data]
    values = [row.count for row in data]
    return {'labels': labels, 'values': values}

def get_weekly_data(start_date, end_date):
    data = db.session.query(
        db.func.strftime('%Y-%W', Reservation.date).label('week'),
        db.func.count().label('count')
    ).filter(
        Reservation.date.between(start_date, end_date)
    ).group_by('week').all()

    labels = [row.week for row in data]
    values = [row.count for row in data]
    return {'labels': labels, 'values': values}

def get_monthly_data(start_date, end_date):
    data = db.session.query(
        db.func.strftime('%Y-%m', Reservation.date).label('month'),
        db.func.count().label('count')
    ).filter(
        Reservation.date.between(start_date, end_date)
    ).group_by('month').all()

    labels = [row.month for row in data]
    values = [row.count for row in data]
    return {'labels': labels, 'values': values}

def get_yearly_data(start_date, end_date):
    data = db.session.query(
        db.func.strftime('%Y', Reservation.date).label('year'),
        db.func.count().label('count')
    ).filter(
        Reservation.date.between(start_date, end_date)
    ).group_by('year').all()

    labels = [row.year for row in data]
    values = [row.count for row in data]
    return {'labels': labels, 'values': values}

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
