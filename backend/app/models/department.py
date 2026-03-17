from datetime import datetime
from app.extensions import db


class Department(db.Model):
    """Clinical department. Consultation fee is department-level."""

    __tablename__ = 'departments'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.Text, nullable=True)
    consultation_fee = db.Column(db.Numeric(10, 2), nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    doctors = db.relationship('Doctor', back_populates='department')
    appointments = db.relationship('Appointment', back_populates='department')

    def to_dict(self) -> dict:
        """Serialize department to dict."""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'consultation_fee': float(self.consultation_fee),
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat(),
        }