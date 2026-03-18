from app.extensions import db
from app.models.patient_document import PatientDocument
from app.models.patient import Patient
from app.utils.file_storage import save_file, delete_file, get_absolute_path


class DocumentService:
    """Handles patient document upload, retrieval, and deletion."""

    @staticmethod
    def upload_document(
        file,
        patient_id: int,
        document_category: str,
        uploaded_by: int,
        visit_id: int = None,
        description: str = None,
    ) -> PatientDocument:
        """
        Save file to disk and create metadata record in DB.

        Args:
            file: Werkzeug FileStorage from request.files
            patient_id: Patient primary key
            document_category: lab_report/prescription/imaging/discharge_summary/other
            uploaded_by: User ID of uploader
            visit_id: Optional visit to link document to
            description: Optional note about the document

        Returns:
            Created PatientDocument object

        Raises:
            ValueError: If patient not found or file type invalid
        """
        # Verify patient exists
        patient = Patient.query.filter_by(
            id=patient_id, is_active=True
        ).first()
        if not patient:
            raise ValueError(f"Patient {patient_id} not found")

        # Save file to disk
        file_path, file_size = save_file(file, patient_id)

        # Store metadata in DB
        document = PatientDocument(
            patient_id=patient_id,
            visit_id=visit_id,
            file_name=file.filename,
            file_path=file_path,
            file_type=file.content_type,
            file_size_bytes=file_size,
            document_category=document_category,
            description=description,
            uploaded_by=uploaded_by,
        )
        db.session.add(document)
        db.session.commit()
        return document

    @staticmethod
    def get_document_by_id(document_id: int) -> PatientDocument:
        """
        Get document metadata by ID.

        Args:
            document_id: PatientDocument primary key

        Returns:
            PatientDocument object

        Raises:
            ValueError: If document not found
        """
        document = PatientDocument.query.get(document_id)
        if not document:
            raise ValueError(f"Document {document_id} not found")
        return document

    @staticmethod
    def get_patient_documents(patient_id: int) -> list:
        """
        Get all documents for a patient ordered by newest first.

        Args:
            patient_id: Patient primary key

        Returns:
            List of document metadata dicts
        """
        documents = PatientDocument.query.filter_by(
            patient_id=patient_id
        ).order_by(PatientDocument.created_at.desc()).all()
        return [d.to_dict() for d in documents]

    @staticmethod
    def get_file_path(document_id: int) -> tuple[str, str]:
        """
        Get absolute file path and original filename for serving.

        Args:
            document_id: PatientDocument primary key

        Returns:
            Tuple of (absolute_path, original_filename)

        Raises:
            ValueError: If document not found
        """
        document = DocumentService.get_document_by_id(document_id)
        abs_path = get_absolute_path(document.file_path)
        return abs_path, document.file_name

    @staticmethod
    def delete_document(document_id: int) -> None:
        """
        Delete file from disk and remove metadata from DB.

        Args:
            document_id: PatientDocument primary key

        Raises:
            ValueError: If document not found
        """
        document = DocumentService.get_document_by_id(document_id)

        # Delete file from disk first
        delete_file(document.file_path)

        # Then remove DB record
        db.session.delete(document)
        db.session.commit()