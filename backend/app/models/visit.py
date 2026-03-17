from datetime import datetime
from app.extensions import db


class Visit(db.Model):
    """Clinical visit record. Created by doctor after appointment is in_progress.
    Auto-creates a billing record on creation."""

    __tablename__ = 'visits'

    id = db.Column(db.Integer, primary_key=True)
    appointment_id = db.Column(db.Integer, db.ForeignKey('appointments.id'), unique=True, nullable=False)
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.id'), nullable=False)
    doctor_id = db.Column(db.Integer, db.ForeignKey('doctors.id'), nullable=False)
    symptoms = db.Column(db.Text, nullable=True)
    diagnosis = db.Column(db.Text, nullable=False)
    diagnosis_code = db.Column(db.String(20), nullable=True)  # ICD-10
    prescription = db.Column(db.Text, nullable=True)
    follow_up_notes = db.Column(db.Text, nullable=True)
    follow_up_date = db.Column(db.Date, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    appointment = db.relationship('Appointment', back_populates='visit')
    patient = db.relationship('Patient', back_populates='visits')
    doctor = db.relationship('Doctor', back_populates='visits')
    billing_record = db.relationship('BillingRecord', back_populates='visit', uselist=False)
    documents = db.relationship('PatientDocument', back_populates='visit')

    def to_dict(self) -> dict:
        """Serialize visit to dict with related info."""
        return {
            'id': self.id,
            'appointment_id': self.appointment_id,
            'patient_id': self.patient_id,
            'patient_name': f"{self.patient.first_name} {self.patient.last_name}",
            'doctor_id': self.doctor_id,
            'doctor_name': self.doctor.user.full_name,
            'department_name': self.doctor.department.name,
            'symptoms': self.symptoms,
            'diagnosis': self.diagnosis,
            'diagnosis_code': self.diagnosis_code,
            'prescription': self.prescription,
            'follow_up_notes': self.follow_up_notes,
            'follow_up_date': self.follow_up_date.isoformat() if self.follow_up_date else None,
            'created_at': self.created_at.isoformat(),
        }