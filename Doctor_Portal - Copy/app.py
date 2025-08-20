# app.py

import os
from flask import Flask, render_template, request, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

# Initialize the Flask application
app = Flask(__name__)
# Load secret key from environment variable for session management
app.secret_key = os.environ.get('SECRET_KEY')

# =========================================================================
# Database Configuration
# =========================================================================
# Get the PostgreSQL database URL from the environment variable provided by Render.
# The `DATABASE_URL` is automatically configured by Render.
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('postgresql://doctor_dashboard_aij9_user:Nz8lsaHRG9Oj76fAHaW4WEdxB692CKiH@dpg-d2iuahre5dus73be6es0-a/doctor_dashboard_aij9')
# This is a good practice to disable as it saves memory
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize SQLAlchemy with the Flask app
db = SQLAlchemy(app)

# =========================================================================
# Database Models (ORM)
# =========================================================================
# Define the `User` model, which maps to the 'users' table in the database.
# This replaces the need for a separate SQL file to define the table schema.
class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(50), nullable=False) # 'doctor' or 'patient'
    
    # Define relationships with other models.
    # 'lazy=True' means Flask-SQLAlchemy will fetch the data on demand.
    availability_slots = db.relationship('AvailabilitySlot', backref='doctor', lazy=True)
    appointments = db.relationship('Appointment', backref='patient', lazy=True)

# Define the `AvailabilitySlot` model.
class AvailabilitySlot(db.Model):
    __tablename__ = 'availability_slots'
    id = db.Column(db.Integer, primary_key=True)
    start_time = db.Column(db.DateTime, nullable=False)
    end_time = db.Column(db.DateTime, nullable=False)
    
    # Define a foreign key relationship to the `User` model.
    # The 'users.id' specifies the table and column to link to.
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

# Define the `Appointment` model.
class Appointment(db.Model):
    __tablename__ = 'appointments'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    
    # Define a foreign key to the `AvailabilitySlot` model.
    slot_id = db.Column(db.Integer, db.ForeignKey('availability_slots.id'), nullable=False)
    
    # Define a foreign key to the `User` model for the patient.
    patient_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

# =========================================================================
# Routes
# =========================================================================
@app.route('/')
def index():
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # Use SQLAlchemy's `query.filter_by()` to find the user.
        # This replaces the `cur.execute()` call from Flask-MySQLdb.
        user = User.query.filter_by(username=username).first()

        if user and check_password_hash(user.password, password):
            session['logged_in'] = True
            session['user_id'] = user.id
            session['username'] = user.username
            session['role'] = user.role
            return redirect(url_for('dashboard'))

        return "Invalid credentials. Please try again."
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/dashboard')
def dashboard():
    if not session.get('logged_in'):
        return redirect(url_for('login'))

    user_role = session.get('role')
    user_id = session.get('user_id')

    if user_role == 'doctor':
        # Fetch doctor's availability slots
        doctor_slots = AvailabilitySlot.query.filter_by(user_id=user_id).all()
        # Fetch doctor's appointments
        doctor_appointments = Appointment.query.join(AvailabilitySlot).filter(AvailabilitySlot.user_id == user_id).all()
        return render_template('doctor_dashboard.html', slots=doctor_slots, appointments=doctor_appointments)
    
    elif user_role == 'patient':
        # Fetch all available doctor slots
        all_slots = AvailabilitySlot.query.all()
        # Fetch patient's appointments
        patient_appointments = Appointment.query.filter_by(patient_id=user_id).all()
        return render_template('patient_dashboard.html', slots=all_slots, appointments=patient_appointments)

    return "Unknown role."

@app.route('/book_appointment/<int:slot_id>', methods=['POST'])
def book_appointment(slot_id):
    if not session.get('logged_in') or session.get('role') != 'patient':
        return redirect(url_for('login'))

    # Check if the slot is available
    slot = AvailabilitySlot.query.get(slot_id)
    if not slot:
        return "Slot not found.", 404

    # Create a new appointment using the `Appointment` model
    new_appointment = Appointment(
        title=f"Appointment with {session.get('username')}",
        slot_id=slot.id,
        patient_id=session.get('user_id')
    )
    
    # Add the new object to the session and commit the transaction to the database
    db.session.add(new_appointment)
    db.session.commit()
    
    return redirect(url_for('dashboard'))

@app.route('/add_availability', methods=['POST'])
def add_availability():
    if not session.get('logged_in') or session.get('role') != 'doctor':
        return redirect(url_for('login'))
    
    # Parse the form data for start and end times
    start_time_str = request.form['start_time']
    end_time_str = request.form['end_time']
    
    try:
        start_time = datetime.fromisoformat(start_time_str)
        end_time = datetime.fromisoformat(end_time_str)
    except ValueError:
        return "Invalid date format.", 400

    # Create a new availability slot
    new_slot = AvailabilitySlot(
        start_time=start_time,
        end_time=end_time,
        user_id=session.get('user_id')
    )
    
    db.session.add(new_slot)
    db.session.commit()
    
    return redirect(url_for('dashboard'))

# =========================================================================
# Main Entry Point
# =========================================================================
# This block runs when the script is executed.
if __name__ == '__main__':
    # Use `app.app_context()` to ensure we are within the Flask application context.
    with app.app_context():
        # This command creates all the tables defined in your models (`User`, `AvailabilitySlot`, `Appointment`)
        # in the PostgreSQL database. It replaces the need to run an external SQL script.
        db.create_all()
        
        # Optional: Add a few initial users for testing purposes if they don't exist.
        if not User.query.filter_by(username='doctor_a').first():
            hashed_password = generate_password_hash('password123', method='pbkdf2:sha256')
            doctor = User(username='doctor_a', password=hashed_password, role='doctor')
            db.session.add(doctor)
            db.session.commit()
        
        if not User.query.filter_by(username='patient_b').first():
            hashed_password = generate_password_hash('password123', method='pbkdf2:sha256')
            patient = User(username='patient_b', password=hashed_password, role='patient')
            db.session.add(patient)
            db.session.commit()
            
    app.run(debug=True)
