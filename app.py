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
from sqlalchemy import asc, desc

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
    __tablename__ = 'reservation'
    id = db.Column(db.Integer, primary_key=True)
    student_number = db.Column(db.String(50), nullable=False)
    name = db.Column(db.String(50), nullable=False)
    school = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(50), nullable=False)
    device = db.Column(db.String(50), nullable=False)
    pin_hash = db.Column(db.String(128), nullable=False)  # Hashed PIN
    date = db.Column(db.DateTime, default=datetime.now, nullable=False)

    def __repr__(self):
        return (f"<Reservation {self.id} | Student Number: {self.student_number} | "
                f"Name: {self.name} | School: {self.school} | Email: {self.email} | "
                f"Device: {self.device} | Date: {self.date}>")

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
    message = None
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()

        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            return redirect(url_for('admin'))
        else:
            message = 'Login failed. Please check your username and password.'

    return render_template('login.html', message=message)


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
    student_number = data["student_number"]
    pin = data.get("pin", "".join(random.choices(string.digits, k=4)))

    device_status = DeviceStatus.query.filter_by(device=device).first()

    if device_status and device_status.status != STATUS_AVAILABLE:
        return jsonify({"message": f"Device {device} is not available."}), 400

    hashed_pin = generate_password_hash(pin, method='pbkdf2:sha256')

    reservation = Reservation(
        student_number=student_number, name=name, school=school, email=email, device=device, pin_hash=hashed_pin
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

# New reservations endpoint
@app.route("/reservations", methods=["GET"])
@login_required
def reservations():
    reservations_list = Reservation.query.all()
    reservation_data = [
        {
            "device": r.device,
            "name": r.name,
            "school": r.school,
            "email": r.email,
            "status": DeviceStatus.query.filter_by(device=r.device).first().status if DeviceStatus.query.filter_by(device=r.device).first() else STATUS_AVAILABLE,
            "start_time": r.date.isoformat(),
            "end_time": (r.date + timedelta(hours=1)).isoformat()
        }
        for r in reservations_list
    ]
    return jsonify(reservation_data)

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
            student_number=name, name=name, school=school, email=email, device=device, pin_hash=hashed_pin
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
    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'view_reservations':
            return redirect(url_for('view_reservations'))
        elif action == 'manage_devices':
            return redirect(url_for('manage_devices'))
        elif action == 'add_user':
            return redirect(url_for('add_user'))
        elif action == 'statistics':
            return redirect(url_for('admin'))  # Ensure 'admin' is the correct page for stats

    action = request.args.get('action')
    frequency = request.args.get('frequency', 'daily')
    time_range = request.args.get('time_range', 'past_week')
    
    end_date = datetime.now()
    start_date = end_date - timedelta(weeks=1)  # Default to the past week

    if time_range == 'past_month':
        start_date = end_date - timedelta(weeks=4)
    elif time_range == 'past_year':
        start_date = end_date - timedelta(weeks=52)
    elif time_range == 'custom':
        start_date = datetime.strptime(request.args.get('start_date'), '%Y-%m-%d')
        end_date = datetime.strptime(request.args.get('end_date'), '%Y-%m-%d')

    reservation_stats = db.session.query(
        db.func.strftime(f"%{'%Y-%m-%d' if frequency == 'daily' else '%Y-%W' if frequency == 'weekly' else '%Y-%m'}", Reservation.date),
        db.func.count(Reservation.id)
    ).filter(Reservation.date.between(start_date, end_date)).group_by(
        db.func.strftime(f"%{'%Y-%m-%d' if frequency == 'daily' else '%Y-%W' if frequency == 'weekly' else '%Y-%m'}", Reservation.date)
    ).all()

    return render_template('admin.html', reservation_stats=reservation_stats)


# View Reservations with sorting and filters
@app.route('/view_reservations', methods=['GET'])
@login_required
def view_reservations():
    # Get filter values from the request
    rows_per_page = request.args.get('rows', default=10, type=int)
    order_by = request.args.get('order', default='student_number', type=str)
    direction = request.args.get('direction', default='asc', type=str)

    # Determine sort direction (ascending/descending)
    if direction == 'desc':
        order_clause = desc(order_by)
    else:
        order_clause = asc(order_by)

    # Query the reservations from the database with the specified order and limit
    reservations = Reservation.query.order_by(order_clause).limit(rows_per_page).all()

    # Check if reservations are empty and print them for debugging
    if not reservations:
        print("No reservations found.")
    else:
        print(f"Reservations: {reservations}")

    # Fetch device statuses
    device_statuses = DeviceStatus.query.all()
    statuses = {status.device: status.status for status in device_statuses}

    # Pass reservations and statuses to the template
    return render_template('view_reservations.html', reservations=reservations, statuses=statuses)

@app.route('/manage_devices', methods=['GET'])
@login_required
def manage_devices():
    # Fetch all devices with their current status
    devices = DeviceStatus.query.all()
    
    # Create a list to store device info with the last reservation
    device_info = []
    
    # For each device, get the most recent reservation
    for device in devices:
        last_reservation = db.session.query(Reservation)\
            .filter_by(device=device.device)\
            .order_by(Reservation.date.desc())\
            .first()  # Fetch the most recent reservation based on the date

        # Append device info and last reservation (if any) to the list
        device_info.append({
            'device': device.device,
            'status': device.status,
            'last_reservation': {
                'name': last_reservation.name if last_reservation else 'N/A',
                'email': last_reservation.email if last_reservation else 'N/A',
                'school': last_reservation.school if last_reservation else 'N/A',
                'date': last_reservation.date.strftime('%Y-%m-%d %H:%M') if last_reservation else 'N/A',
            }
        })

    # Pass the device info to the template
    return render_template('manage_devices.html', devices=device_info)



# Add user route
@app.route('/add_user', methods=['GET', 'POST'])
@login_required
def add_user():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        hashed_password = generate_password_hash(password, method='pbkdf2:sha256')

        new_user = User(username=username, password_hash=hashed_password)
        db.session.add(new_user)
        db.session.commit()

        flash(f"User {username} added successfully!")
        return redirect(url_for('admin'))

    return render_template('add_user.html')


if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(host='192.168.1.57', port=5000, debug=True)
