from datetime import datetime
from app.extensions import db


class Appointment(db.Model):
    """Appointment record. Unique constraint prevents doctor double-booking."""

    __tablename__ = 'appointments'

    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.id'), nullable=False)
    doctor_id = db.Column(db.Integer, db.ForeignKey('doctors.id'), nullable=False)
    department_id = db.Column(db.Integer, db.ForeignKey('departments.id'), nullable=False)
    appointment_date = db.Column(db.Date, nullable=False)
    appointment_time = db.Column(db.Time, nullable=False)
    status = db.Column(db.String(20), nullable=False, default='scheduled')
    notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Unique constraint — prevents double-booking at DB level
    __table_args__ = (
        db.UniqueConstraint('doctor_id', 'appointment_date', 'appointment_time',
                            name='uq_doctor_date_time'),
    )

    # Relationships
    patient = db.relationship('Patient', back_populates='appointments')
    doctor = db.relationship('Doctor', back_populates='appointments')
    department = db.relationship('Department', back_populates='appointments')
    visit = db.relationship('Visit', back_populates='appointment', uselist=False)

    # Valid status transitions — enforced in service layer
    VALID_TRANSITIONS = {
        'scheduled': ['in_progress', 'cancelled', 'no_show'],
        'in_progress': ['completed'],
        'completed': [],
        'cancelled': [],
        'no_show': [],
    }

    def is_valid_transition(self, new_status: str) -> bool:
        """Check if status transition is allowed."""
        return new_status in self.VALID_TRANSITIONS.get(self.status, [])

    def to_dict(self) -> dict:
        """Serialize appointment to dict with related info."""
        return {
            'id': self.id,
            'patient_id': self.patient_id,
            'patient_name': f"{self.patient.first_name} {self.patient.last_name}",
            'patient_phone': self.patient.phone,
            'doctor_id': self.doctor_id,
            'doctor_name': self.doctor.user.full_name,
            'department_id': self.department_id,
            'department_name': self.department.name,
            'appointment_date': self.appointment_date.isoformat(),
            'appointment_time': self.appointment_time.strftime('%H:%M'),
            'status': self.status,
            'notes': self.notes,
            'created_at': self.created_at.isoformat(),
        }