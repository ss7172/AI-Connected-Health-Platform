from datetime import datetime
from app.extensions import db


class BillingRecord(db.Model):
    """Invoice header. One per visit. Total is sum of all line items."""

    __tablename__ = 'billing_records'

    id = db.Column(db.Integer, primary_key=True)
    visit_id = db.Column(db.Integer, db.ForeignKey('visits.id'), unique=True, nullable=False)
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.id'), nullable=False)
    total_amount = db.Column(db.Numeric(10, 2), nullable=False)
    status = db.Column(db.String(20), nullable=False, default='pending')  # pending/paid/partially_paid/waived
    payment_method = db.Column(db.String(50), nullable=True)  # cash/card/upi/insurance
    payment_date = db.Column(db.DateTime, nullable=True)
    notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    visit = db.relationship('Visit', back_populates='billing_record')
    patient = db.relationship('Patient', back_populates='billing_records')
    items = db.relationship('BillingItem', back_populates='billing_record',
                            cascade='all, delete-orphan')

    def to_dict(self) -> dict:
        """Serialize billing record with all line items."""
        return {
            'id': self.id,
            'visit_id': self.visit_id,
            'patient_id': self.patient_id,
            'patient_name': f"{self.patient.first_name} {self.patient.last_name}",
            'total_amount': float(self.total_amount),
            'status': self.status,
            'payment_method': self.payment_method,
            'payment_date': self.payment_date.isoformat() if self.payment_date else None,
            'notes': self.notes,
            'items': [item.to_dict() for item in self.items],
            'created_at': self.created_at.isoformat(),
        }


class BillingItem(db.Model):
    """Invoice line item. First item is always consultation fee (auto-created).
    Additional items are tests/procedures added by front desk."""

    __tablename__ = 'billing_items'

    id = db.Column(db.Integer, primary_key=True)
    billing_record_id = db.Column(db.Integer, db.ForeignKey('billing_records.id'), nullable=False)
    description = db.Column(db.String(255), nullable=False)  # e.g. 'Cardiology Consultation', 'ECG'
    category = db.Column(db.String(50), nullable=False)  # consultation/test/procedure/other
    amount = db.Column(db.Numeric(10, 2), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    billing_record = db.relationship('BillingRecord', back_populates='items')

    def to_dict(self) -> dict:
        """Serialize billing item to dict."""
        return {
            'id': self.id,
            'billing_record_id': self.billing_record_id,
            'description': self.description,
            'category': self.category,
            'amount': float(self.amount),
            'created_at': self.created_at.isoformat(),
        }