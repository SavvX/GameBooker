from flask import Flask, request, jsonify, render_template, url_for
from flask_sqlalchemy import SQLAlchemy
import random
import string

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///reservations.db"
db = SQLAlchemy(app)


class Reservation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    school = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(50), nullable=False)
    device = db.Column(db.String(50), nullable=False)
    password = db.Column(db.String(50), nullable=False)


@app.route("/reserve", methods=["POST"])
def reserve():
    data = request.get_json()
    name = data["name"]
    school = data["school"]
    email = data["email"]
    device = data["device"]
    password = "".join(random.choices(string.digits, k=4))

    reservation = Reservation(
        name=name, school=school, email=email, device=device, password=password
    )
    db.session.add(reservation)
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


@app.route("/", methods=["GET", "POST"])
def index():
    return render_template("index.html")


if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)
