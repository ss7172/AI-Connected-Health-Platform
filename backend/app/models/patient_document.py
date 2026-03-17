from datetime import datetime
from app.extensions import db


class PatientDocument(db.Model):
    """Digitized patient document. File stored on disk, metadata in DB.
    Patients historically carried paper reports — this system digitizes that."""

    __tablename__ = 'patient_documents'

    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.id'), nullable=False)
    visit_id = db.Column(db.Integer, db.ForeignKey('visits.id'), nullable=True)
    file_name = db.Column(db.String(255), nullable=False)      # original filename
    file_path = db.Column(db.String(500), nullable=False)      # uploads/patients/{id}/{uuid}.ext
    file_type = db.Column(db.String(100), nullable=False)      # MIME type e.g. application/pdf
    file_size_bytes = db.Column(db.Integer, nullable=False)
    document_category = db.Column(db.String(50), nullable=False)  # lab_report/prescription/imaging/discharge_summary/other
    description = db.Column(db.Text, nullable=True)
    uploaded_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    patient = db.relationship('Patient', back_populates='documents')
    visit = db.relationship('Visit', back_populates='documents')
    uploader = db.relationship('User', foreign_keys=[uploaded_by])

    def to_dict(self) -> dict:
        """Serialize document metadata. Never exposes file_path directly."""
        return {
            'id': self.id,
            'patient_id': self.patient_id,
            'visit_id': self.visit_id,
            'file_name': self.file_name,
            'file_type': self.file_type,
            'file_size_bytes': self.file_size_bytes,
            'document_category': self.document_category,
            'description': self.description,
            'uploaded_by': self.uploader.full_name,
            'created_at': self.created_at.isoformat(),
        }