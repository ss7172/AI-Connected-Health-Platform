from datetime import datetime
from app.extensions import db


class Doctor(db.Model):
    """Doctor profile. Linked 1-to-1 with a User account."""

    __tablename__ = 'doctors'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), unique=True, nullable=False)
    department_id = db.Column(db.Integer, db.ForeignKey('departments.id'), nullable=False)
    specialization = db.Column(db.String(200), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    license_number = db.Column(db.String(100), nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = db.relationship('User', back_populates='doctor_profile')
    department = db.relationship('Department', back_populates='doctors')
    appointments = db.relationship('Appointment', back_populates='doctor')
    visits = db.relationship('Visit', back_populates='doctor')

    def to_dict(self) -> dict:
        """Serialize doctor to dict including user and department info."""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'full_name': self.user.full_name,
            'email': self.user.email,
            'department_id': self.department_id,
            'department_name': self.department.name,
            'specialization': self.specialization,
            'phone': self.phone,
            'license_number': self.license_number,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat(),
        }