from datetime import datetime, date
from app.extensions import db


class Patient(db.Model):
    """Patient record. Phone is the primary deduplication key."""

    __tablename__ = 'patients'

    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)
    date_of_birth = db.Column(db.Date, nullable=False)
    gender = db.Column(db.String(20), nullable=False)  # male, female, other
    phone = db.Column(db.String(20), unique=True, nullable=False)
    email = db.Column(db.String(255), nullable=True)
    address = db.Column(db.Text, nullable=True)
    emergency_contact = db.Column(db.String(255), nullable=True)
    blood_group = db.Column(db.String(10), nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    appointments = db.relationship('Appointment', back_populates='patient')
    visits = db.relationship('Visit', back_populates='patient')
    billing_records = db.relationship('BillingRecord', back_populates='patient')
    documents = db.relationship('PatientDocument', back_populates='patient')

    def calculate_age(self) -> int:
        """Calculate patient age from date of birth."""
        today = date.today()
        return today.year - self.date_of_birth.year - (
            (today.month, today.day) < 
            (self.date_of_birth.month, self.date_of_birth.day)
        )

    def to_dict(self) -> dict:
        """Serialize patient to dict including calculated age."""
        return {
            'id': self.id,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'full_name': f"{self.first_name} {self.last_name}",
            'date_of_birth': self.date_of_birth.isoformat(),
            'age': self.calculate_age(),
            'gender': self.gender,
            'phone': self.phone,
            'email': self.email,
            'address': self.address,
            'emergency_contact': self.emergency_contact,
            'blood_group': self.blood_group,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat(),
        }