import os
import sys

# Add backend/ to path so we can import app
sys.path.insert(0, os.path.dirname(__file__))

from app import create_app
from app.extensions import db

from app.models import (
    User, Department, Doctor, Patient,
    Appointment, Visit, BillingRecord, BillingItem, PatientDocument
)
from datetime import date, time
from decimal import Decimal


def seed_departments() -> dict:
    """Create 4 departments with consultation fees. Returns name→object map."""
    departments_data = [
        {'name': 'Cardiology', 'description': 'Heart and cardiovascular care', 'consultation_fee': 500},
        {'name': 'Gastroenterology', 'description': 'Digestive system care', 'consultation_fee': 500},
        {'name': 'Hepatology', 'description': 'Liver and biliary care', 'consultation_fee': 600},
        {'name': 'General Medicine', 'description': 'General outpatient care', 'consultation_fee': 300},
    ]

    departments = {}
    for data in departments_data:
        dept = Department(**data)
        db.session.add(dept)
        departments[data['name']] = dept
        print(f"  Created department: {data['name']} (fee: ₹{data['consultation_fee']})")

    return departments


def seed_users() -> dict:
    """Create admin, 2 doctors, 1 front desk. Returns email→object map."""
    users_data = [
        {'email': 'admin', 'full_name': 'Admin User', 'role': 'admin', 'password': 'admin123'},
        {'email': 'dr.mohanty', 'full_name': 'Dr. Rajesh Mohanty', 'role': 'doctor', 'password': 'doctor123'},
        {'email': 'dr.patel', 'full_name': 'Dr. Priya Patel', 'role': 'doctor', 'password': 'doctor123'},
        {'email': 'frontdesk1', 'full_name': 'Anita Das', 'role': 'front_desk', 'password': 'front123'},
    ]

    users = {}
    for data in users_data:
        user = User(
            email=data['email'],
            full_name=data['full_name'],
            role=data['role'],
        )
        user.set_password(data['password'])
        db.session.add(user)
        users[data['email']] = user
        print(f"  Created user: {data['full_name']} ({data['role']})")

    return users


def seed_doctors(users: dict, departments: dict) -> None:
    """Create 2 doctor profiles linked to user accounts."""
    doctors_data = [
        {
            'user': users['dr.mohanty'],
            'department': departments['Cardiology'],
            'specialization': 'Interventional Cardiology',
            'phone': '9876543201',
            'license_number': 'OD-12345',
        },
        {
            'user': users['dr.patel'],
            'department': departments['Gastroenterology'],
            'specialization': 'Gastroenterology',
            'phone': '9876543202',
            'license_number': 'OD-12346',
        },
    ]

    for data in doctors_data:
        doctor = Doctor(
            user=data['user'],
            department=data['department'],
            specialization=data['specialization'],
            phone=data['phone'],
            license_number=data['license_number'],
        )
        db.session.add(doctor)
        print(f"  Created doctor: {data['user'].full_name} → {data['department'].name}")



def seed_patients() -> dict:
    """Create 3 demo patients. Returns phone→object map."""
    patients_data = [
        {
            'first_name': 'Ramesh', 'last_name': 'Nayak',
            'date_of_birth': date(1975, 4, 12), 'gender': 'male',
            'phone': '9437001001', 'blood_group': 'B+',
            'address': 'MG Road, Cuttack', 'emergency_contact': 'Sunita Nayak - 9437001002',
        },
        {
            'first_name': 'Priya', 'last_name': 'Sahoo',
            'date_of_birth': date(1990, 8, 22), 'gender': 'female',
            'phone': '9437002001', 'blood_group': 'O+',
            'address': 'Badambadi, Cuttack', 'emergency_contact': 'Suresh Sahoo - 9437002002',
        },
        {
            'first_name': 'Bikram', 'last_name': 'Das',
            'date_of_birth': date(1965, 1, 5), 'gender': 'male',
            'phone': '9437003001', 'blood_group': 'A+',
            'address': 'College Square, Cuttack', 'emergency_contact': 'Mita Das - 9437003002',
        },
    ]

    patients = {}
    for data in patients_data:
        patient = Patient(**data)
        db.session.add(patient)
        patients[data['phone']] = patient
        print(f"  Created patient: {data['first_name']} {data['last_name']}")

    return patients


def seed_appointments(patients: dict, doctors: list, departments: dict) -> list:
    """Create 3 demo appointments — one per patient."""
    dr_mohanty = doctors[0]
    dr_patel = doctors[1]

    appointments_data = [
        {
            'patient': patients['9437001001'],
            'doctor': dr_mohanty,
            'department': departments['Cardiology'],
            'appointment_date': date.today(),
            'appointment_time': time(9, 0),
            'status': 'completed',
            'notes': 'Routine cardiac checkup',
        },
        {
            'patient': patients['9437002001'],
            'doctor': dr_patel,
            'department': departments['Gastroenterology'],
            'appointment_date': date.today(),
            'appointment_time': time(10, 0),
            'status': 'scheduled',
            'notes': 'Follow-up visit',
        },
        {
            'patient': patients['9437003001'],
            'doctor': dr_mohanty,
            'department': departments['Cardiology'],
            'appointment_date': date.today(),
            'appointment_time': time(11, 0),
            'status': 'scheduled',
            'notes': 'First consultation',
        },
    ]

    appointments = []
    for data in appointments_data:
        appointment = Appointment(**data)
        db.session.add(appointment)
        appointments.append(appointment)
        print(f"  Created appointment: {data['patient'].first_name} → {data['doctor'].user.full_name} at {data['appointment_time']}")

    return appointments


def seed_visits(appointments: list, departments: dict) -> None:
    """Create a visit and billing record for Ramesh's completed appointment."""
    completed_appointment = appointments[0]  # Ramesh, Cardiology, status=completed
    cardiology = departments['Cardiology']

    visit = Visit(
        appointment_id=completed_appointment.id,
        patient_id=completed_appointment.patient_id,
        doctor_id=completed_appointment.doctor_id,
        symptoms="Chest pain and shortness of breath",
        diagnosis="Stable angina — recommend stress test and medication adjustment",
        diagnosis_code="I20.9",
        prescription="Tab. Metoprolol 25mg BD, Tab. Aspirin 75mg OD",
        follow_up_notes="Review after stress test results",
        follow_up_date=date.today().replace(day=date.today().day + 14)
        if date.today().day <= 14
        else date.today(),
    )
    db.session.add(visit)
    db.session.flush()

    billing_record = BillingRecord(
        visit_id=visit.id,
        patient_id=completed_appointment.patient_id,
        total_amount=Decimal('700.00'),
        status='paid',
        payment_method='cash',
        payment_date=date.today(),
    )
    db.session.add(billing_record)
    db.session.flush()

    # Consultation fee line item
    consultation_item = BillingItem(
        billing_record_id=billing_record.id,
        description='Cardiology Consultation',
        category='consultation',
        amount=Decimal('500.00'),
    )

    # Additional test line item
    ecg_item = BillingItem(
        billing_record_id=billing_record.id,
        description='ECG',
        category='test',
        amount=Decimal('200.00'),
    )

    db.session.add(consultation_item)
    db.session.add(ecg_item)
    print(f"  Created visit + billing record for Ramesh Nayak (paid ₹700)")


def run_seed() -> None:
    """Main seed function. Clears existing data and reseeds."""
    app = create_app('development')

    with app.app_context():
        print("\nClearing existing data...")
        # Delete in reverse dependency order to avoid FK violations
        BillingItem.query.delete()
        BillingRecord.query.delete()
        PatientDocument.query.delete()
        Visit.query.delete()
        Appointment.query.delete()
        Doctor.query.delete()
        User.query.delete()
        Department.query.delete()
        Patient.query.delete()
        db.session.commit()

        print("\nSeeding departments...")
        departments = seed_departments()
        db.session.flush()

        print("\nSeeding users...")
        users = seed_users()
        db.session.flush()

        print("\nSeeding doctors...")
        seed_doctors(users, departments)
        db.session.flush()

        # Get doctor objects for appointments
        doctors = Doctor.query.all()

        print("\nSeeding patients...")
        patients = seed_patients()
        db.session.flush()

        print("\nSeeding appointments...")
        seed_appointments(patients, doctors, departments)

        print("\nSeeding visits and billing...")
        appointments = Appointment.query.all()
        seed_visits(appointments, departments)


        db.session.commit()
        print("\nSeed complete.")



if __name__ == '__main__':
    run_seed()