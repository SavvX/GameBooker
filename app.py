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
from werkzeug.security import generate_password_hash, check_password_hash
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

# Constants for device status
STATUS_AVAILABLE = "Available"
STATUS_RESERVED = "Reserved"
STATUS_SHUT_DOWN = "Shut Down"

# Models
class Reservation(db.Model):
    __tablename__ = 'reservation'  # Ensure this matches the actual table name in the DB
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    school = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(50), nullable=False)
    device = db.Column(db.String(50), nullable=False)
    pin_hash = db.Column(db.String(128), nullable=False)  # Hashed PIN
    date = db.Column(db.DateTime, default=datetime.now, nullable=False)

    def __repr__(self):
        return (f"<Reservation {self.id} | Name: {self.name} | School: {self.school} | "
                f"Email: {self.email} | Device: {self.device} | Date: {self.date}>")

class DeviceStatus(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    device = db.Column(db.String(50), nullable=False)
    status = db.Column(db.String(50), nullable=False)

    def __repr__(self):
        return f"<DeviceStatus {self.id} | Device: {self.device} | Status: {self.status}>"

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)  # Hashed password

    def __repr__(self):
        return f"<User {self.id} | Username: {self.username}>"

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))

# Route to handle login form submission
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()

        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            return redirect(url_for('admin'))
        else:
            flash('Login failed. Please check your username and password.')

    return render_template('login.html')

# User registration route (for simplicity)
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        hashed_password = generate_password_hash(password, method='pbkdf2:sha256')
        new_user = User(username=username, password_hash=hashed_password)

        try:
            db.session.add(new_user)
            db.session.commit()
            flash('Registration successful! You can now log in.')
            return redirect(url_for('login'))
        except:
            db.session.rollback()
            flash('Error: Username already exists.')

    return render_template('register.html')

# Reservation endpoint with hashed pin storage
@app.route("/reserve", methods=["POST"])
def reserve():
    data = request.json
    name = data["name"]
    school = data["school"]
    email = data["email"]
    device = data["device"]
    pin = data.get("pin", "".join(random.choices(string.digits, k=4)))

    device_status = DeviceStatus.query.filter_by(device=device).first()

    if device_status and device_status.status != STATUS_AVAILABLE:
        return jsonify({"message": f"Device {device} is not available."}), 400

    hashed_pin = generate_password_hash(pin, method='pbkdf2:sha256')

    reservation = Reservation(
        name=name, school=school, email=email, device=device, pin_hash=hashed_pin
    )
    db.session.add(reservation)
    db.session.commit()

    if device_status:
        device_status.status = STATUS_RESERVED
    else:
        new_device_status = DeviceStatus(device=device, status=STATUS_RESERVED)
        db.session.add(new_device_status)

    db.session.commit()

    return jsonify({"message": f"Reservation successful! PIN for {device}: {pin}"})

# Status route
@app.route("/status", methods=["GET"])
def status():
    devices = [
        "PC1", "PC2", "PC3", "PC4", "PC5", "PC6", "PC7", "PC8", "PC9", "PC10",
        "PS5", "Switch1", "Switch2", "RacingSim1", "RacingSim2",
    ]
    status = {}
    for device in devices:
        reservation = (
            Reservation.query.filter_by(device=device)
            .order_by(Reservation.id.desc())
            .first()
        )
        status[device] = "Reserved" if reservation else STATUS_AVAILABLE

    return jsonify(status)

# Device status update route
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

# Device shutdown simulation
@app.route("/shutdown", methods=["POST"])
@login_required
def shutdown():
    data = request.json
    device = data["device"]

    # Simulate shutdown logic
    shutdown_success = True  # Replace this with actual shutdown logic

    if shutdown_success:
        device_status = DeviceStatus.query.filter_by(device=device).first()
        if device_status:
            device_status.status = STATUS_SHUT_DOWN
            db.session.commit()
        return jsonify({"message": f"Shutdown command sent to {device}"}), 200
    else:
        return jsonify({"message": f"Failed to send shutdown command to {device}"}), 500

# Index route
@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        data = request.form
        name = data["name"]
        school = data["school"]
        email = data["email"]
        device = data["device"]

        device_status = DeviceStatus.query.filter_by(device=device).first()

        if device_status and device_status.status != STATUS_AVAILABLE:
            flash(f"Device {device} is not available.")
            return redirect(url_for("index"))

        pin = "".join(random.choices(string.digits, k=4))

        hashed_pin = generate_password_hash(pin, method='pbkdf2:sha256')

        reservation = Reservation(
            name=name, school=school, email=email, device=device, pin_hash=hashed_pin
        )
        db.session.add(reservation)
        db.session.commit()

        if device_status:
            device_status.status = STATUS_RESERVED
        else:
            new_device_status = DeviceStatus(device=device, status=STATUS_RESERVED)
            db.session.add(new_device_status)

        db.session.commit()

        flash(f"Reservation successful! PIN for {device}: {pin}")
        return redirect(url_for("index"))

    return render_template("index.html")

# Admin route to view statistics
@app.route('/admin', methods=['GET', 'POST'])
@login_required
def admin():
    action = request.args.get('action')
    frequency = request.args.get('frequency', 'daily')
    time_range = request.args.get('time_range', 'all_time')

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
        start_date = datetime(2020, 1, 1) 

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

# Utility functions for fetching statistics
def get_hourly_data(start_date, end_date):
    data = db.session.query(
        db.func.strftime('%Y-%m-%d %H:00:00', Reservation.date).label('hour'),
        db.func.count().label('count')
    ).filter(
        Reservation.date >= start_date,
        Reservation.date <= end_date
    ).group_by('hour').all()

    labels = [row.hour for row in data]
    values = [row.count for row in data]
    return {'labels': labels, 'values': values}

def get_daily_data(start_date, end_date):
    data = db.session.query(
        db.func.strftime('%Y-%m-%d', Reservation.date).label('day'),
        db.func.count().label('count')
    ).filter(
        Reservation.date >= start_date,
        Reservation.date <= end_date
    ).group_by('day').all()

    labels = [row.day for row in data]
    values = [row.count for row in data]
    return {'labels': labels, 'values': values}

def get_weekly_data(start_date, end_date):
    data = db.session.query(
        db.func.strftime('%Y-%W', Reservation.date).label('week'),
        db.func.count().label('count')
    ).filter(
        Reservation.date >= start_date,
        Reservation.date <= end_date
    ).group_by('week').all()

    labels = [row.week for row in data]
    values = [row.count for row in data]
    return {'labels': labels, 'values': values}

def get_monthly_data(start_date, end_date):
    data = db.session.query(
        db.func.strftime('%Y-%m', Reservation.date).label('month'),
        db.func.count().label('count')
    ).filter(
        Reservation.date >= start_date,
        Reservation.date <= end_date
    ).group_by('month').all()

    labels = [row.month for row in data]
    values = [row.count for row in data]
    return {'labels': labels, 'values': values}

def get_yearly_data(start_date, end_date):
    data = db.session.query(
        db.func.strftime('%Y', Reservation.date).label('year'),
        db.func.count().label('count')
    ).filter(
        Reservation.date >= start_date,
        Reservation.date <= end_date
    ).group_by('year').all()

    labels = [row.year for row in data]
    values = [row.count for row in data]
    return {'labels': labels, 'values': values}

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(host="192.168.1.57", port=5000, debug=True)
