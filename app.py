from flask import Flask, request, jsonify, render_template, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import (
    LoginManager, UserMixin, login_user, login_required,
    logout_user, current_user
)
from werkzeug.security import generate_password_hash, check_password_hash
import random
import string
from datetime import datetime, timedelta
from sqlalchemy import asc, desc, func

# Initialize Flask app and configure database
app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///reservations.db"
app.config["SECRET_KEY"] = "your_secret_key"
db = SQLAlchemy(app)

# Initialize login manager
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

# Device status constants
STATUS_AVAILABLE = "Available"
STATUS_RESERVED = "Reserved"
STATUS_SHUT_DOWN = "Shut Down"

# Model for Reservations
class Reservation(db.Model):
    __tablename__ = 'reservation'
    id = db.Column(db.Integer, primary_key=True)
    student_number = db.Column(db.String(50), nullable=False)
    name = db.Column(db.String(50), nullable=False)
    school = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(50), nullable=False)
    device = db.Column(db.String(50), nullable=False)
    pin_hash = db.Column(db.String(128), nullable=False)  # Store hashed PIN
    date = db.Column(db.DateTime, default=datetime.now, nullable=False)

    def __repr__(self):
        return (f"<Reservation {self.id} | Student Number: {self.student_number} | "
                f"Name: {self.name} | School: {self.school} | Email: {self.email} | "
                f"Device: {self.device} | Date: {self.date}>")

# Model for Device Status
class DeviceStatus(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    device = db.Column(db.String(50), nullable=False)
    status = db.Column(db.String(50), nullable=False)

    def __repr__(self):
        return f"<DeviceStatus {self.id} | Device: {self.device} | Status: {self.status}>"

# Model for User (Admin) with hashed password
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)

    def __repr__(self):
        return f"<User {self.id} | Username: {self.username}>"

# User loader for login manager
@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))

# Route to handle login
@app.route('/login', methods=['GET', 'POST'])
def login():
    message = None
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()

        # Verify password and login
        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            return redirect(url_for('admin'))
        else:
            message = 'Login failed. Please check your username and password.'

    return render_template('login.html', message=message)

# User registration route
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        hashed_password = generate_password_hash(password, method='pbkdf2:sha256')
        new_user = User(username=username, password_hash=hashed_password)

        # Save the new user to the database
        try:
            db.session.add(new_user)
            db.session.commit()
            flash('Registration successful! You can now log in.')
            return redirect(url_for('login'))
        except:
            db.session.rollback()
            flash('Error: Username already exists.')

    return render_template('register.html')

# Route to handle reservations with hashed PIN
@app.route("/reserve", methods=["POST"])
def reserve():
    data = request.json
    name = data["name"]
    school = data["school"]
    email = data["email"]
    device = data["device"]
    student_number = data["student_number"]
    pin = data.get("pin", "".join(random.choices(string.digits, k=4)))

    # Check if the device is available
    device_status = DeviceStatus.query.filter_by(device=device).first()
    if device_status and device_status.status != STATUS_AVAILABLE:
        return jsonify({"message": f"Device {device} is not available."}), 400

    hashed_pin = generate_password_hash(pin, method='pbkdf2:sha256')

    # Create new reservation
    reservation = Reservation(
        student_number=student_number, name=name, school=school,
        email=email, device=device, pin_hash=hashed_pin
    )
    db.session.add(reservation)
    db.session.commit()

    # Update device status
    if device_status:
        device_status.status = STATUS_RESERVED
    else:
        new_device_status = DeviceStatus(device=device, status=STATUS_RESERVED)
        db.session.add(new_device_status)

    db.session.commit()

    return jsonify({"message": f"Reservation successful! PIN for {device}: {pin}"})

# Route to fetch all reservations (only for logged-in admins)
@app.route("/reservations", methods=["GET"])
@login_required
def reservations():
    reservations_list = Reservation.query.all()

    # Create response data with reservations and their status
    reservation_data = [
        {
            "device": r.device,
            "name": r.name,
            "school": r.school,
            "email": r.email,
            "status": DeviceStatus.query.filter_by(device=r.device).first().status
            if DeviceStatus.query.filter_by(device=r.device).first() else STATUS_AVAILABLE,
            "start_time": r.date.isoformat(),
            "end_time": (r.date + timedelta(hours=1)).isoformat()
        }
        for r in reservations_list
    ]
    return jsonify(reservation_data)

# Route to get device status
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

# Route to update device status
@app.route("/update_status", methods=["POST"])
def update_status():
    data = request.json
    device = data["device"]
    status = data["status"]

    # Find or create device status
    device_status = DeviceStatus.query.filter_by(device=device).first()
    if not device_status:
        device_status = DeviceStatus(device=device, status=status)
        db.session.add(device_status)
    else:
        device_status.status = status

    db.session.commit()
    return jsonify({"message": f"Status for {device} updated to {status}"})

# Device shutdown route (simulated)
@app.route("/shutdown", methods=["POST"])
@login_required
def shutdown():
    data = request.json
    device = data["device"]

    # Simulate shutdown logic (can be replaced with actual logic)
    shutdown_success = True

    if shutdown_success:
        device_status = DeviceStatus.query.filter_by(device=device).first()
        if device_status:
            device_status.status = STATUS_SHUT_DOWN
            db.session.commit()
        return jsonify({"message": f"Shutdown command sent to {device}"}), 200
    else:
        return jsonify({"message": f"Failed to send shutdown command to {device}"}), 500

# Home page route
@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        data = request.form
        name = data["name"]
        school = data["school"]
        email = data["email"]
        device = data["device"]

        # Check if device is available
        device_status = DeviceStatus.query.filter_by(device=device).first()
        if device_status and device_status.status != STATUS_AVAILABLE:
            flash(f"Device {device} is not available.")
            return redirect(url_for("index"))

        pin = "".join(random.choices(string.digits, k=4))
        hashed_pin = generate_password_hash(pin, method='pbkdf2:sha256')

        # Create new reservation
        reservation = Reservation(
            student_number=name, name=name, school=school, email=email, device=device, pin_hash=hashed_pin
        )
        db.session.add(reservation)
        db.session.commit()

        # Update device status
        if device_status:
            device_status.status = STATUS_RESERVED
        else:
            new_device_status = DeviceStatus(device=device, status=STATUS_RESERVED)
            db.session.add(new_device_status)

        db.session.commit()

        flash(f"Reservation successful! PIN for {device}: {pin}")
        return redirect(url_for("index"))

    return render_template("index.html")

# Admin page route for viewing statistics and managing actions
@app.route('/admin', methods=['GET', 'POST'])
@login_required
def admin():
    if request.method == 'POST':
        action = request.form['action']
        device = request.form['device']

        if action == 'Update Status':
            return redirect(url_for('update_status', device=device))
        elif action == 'Shutdown Device':
            return redirect(url_for('shutdown', device=device))

    return render_template('admin.html')

# Logout route
@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.')
    return redirect(url_for('login'))

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(host='192.168.1.57', port=5000, debug=True)
