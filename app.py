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
from sqlalchemy.orm import aliased
from sqlalchemy.sql import literal_column
import logging

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
        
        # Redirect based on the selected action
        if action == 'view_reservations':
            return redirect(url_for('view_reservations'))  # Example route for viewing reservations
        elif action == 'manage_devices':
            return redirect(url_for('manage_devices'))  # Route for managing devices
        elif action == 'add_admin':
            return redirect(url_for('add_admin'))  # Route for adding admin
        elif action == 'check_statistics':
            return redirect(url_for('check_statistics'))  # Route for checking statistics

    return render_template('admin.html')

@app.route('/view_reservations', methods=['GET'])
@login_required
def view_reservations():
    # Get filter values from the request
    rows = request.args.get('rows', default='10')  # Treat 'rows' as a string to handle "all"
    order_by = request.args.get('order', default='date', type=str)
    direction = request.args.get('direction', default='desc', type=str)
    
    # Determine sort direction (ascending/descending)
    if direction == 'desc':
        order_clause = desc(order_by)
    else:
        order_clause = asc(order_by)
        
    # Fetch reservations based on rows value
    if rows == 'all':
        # Fetch all reservations without limit
        reservations = Reservation.query.order_by(order_clause).all()
    else:
        # Convert rows to int and apply a limit
        rows_per_page = int(rows)
        reservations = Reservation.query.order_by(order_clause).limit(rows_per_page).all()


    # Fetch device statuses
    device_statuses = DeviceStatus.query.all()
    statuses = {status.device: status.status for status in device_statuses}

    # Pass reservations and statuses to the template
    return render_template('view_reservations.html', reservations=reservations, statuses=statuses)

@app.route('/manage_devices', methods=['GET'])
@login_required
def manage_devices():
    # Alias for the Reservation table
    ReservationAlias = aliased(Reservation)
    
    # Subquery for ranking reservations by device and date
    ranked_reservations = db.session.query(
        Reservation.device,
        Reservation.date.label('last_date'),
        Reservation.name,
        Reservation.pin_hash,
        func.row_number().over(
            partition_by=Reservation.device,
            order_by=Reservation.date.desc()
        ).label('row_num')
    ).subquery()

    # Main query to get the most recent reservations per device
    latest_reservations = db.session.query(
        ranked_reservations.c.device,
        ranked_reservations.c.last_date,
        ranked_reservations.c.name,
        ranked_reservations.c.pin_hash
    ).filter(ranked_reservations.c.row_num == 1).all()

    # Fetch device statuses
    devices = DeviceStatus.query.all()

    # Create a list to store device info with the latest reservation
    device_info = []
    
    # Combine the devices and the latest reservations
    for device in devices:
        last_reservation = next(
            (res for res in latest_reservations if res.device == device.device), None
        )

        device_info.append({
            'device': device.device,
            'status': device.status,
            'last_reservation': {
                'name': last_reservation.name if last_reservation else 'N/A',
                'date': last_reservation.last_date.strftime('%Y-%m-%d %H:%M') if last_reservation else 'N/A',
            }
        })

    # Pass the device info to the template
    return render_template('manage_devices.html', devices=device_info)

# Add user route
@app.route('/add_admin', methods=['GET', 'POST'])
@login_required
def add_admin():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        hashed_password = generate_password_hash(password, method='pbkdf2:sha256')
        new_user = User(username=username, password_hash=hashed_password)
        db.session.add(new_user)
        db.session.commit()
        flash(f"User {username} added successfully!")
        return redirect(url_for('admin'))
    return render_template('add_admin.html')


# Route to check statistics
@app.route('/check_statistics', methods=['GET'])
@login_required
def check_statistics():
    # Get total number of reservations
    total_reservations = Reservation.query.count()
    
    # Get device statuses
    device_statuses = DeviceStatus.query.all()
    
    # Count reserved and available devices
    reserved_count = sum(1 for status in device_statuses if status.status == STATUS_RESERVED)
    available_count = sum(1 for status in device_statuses if status.status == STATUS_AVAILABLE)
    shut_down_count = sum(1 for status in device_statuses if status.status == STATUS_SHUT_DOWN)
    
    # Pass statistics to the template
    return render_template('check_statistics.html', 
                           total_reservations=total_reservations,
                           reserved_count=reserved_count,
                           available_count=available_count,
                           shut_down_count=shut_down_count)

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
    app.run(host='localhost', port=5000, debug=True)
