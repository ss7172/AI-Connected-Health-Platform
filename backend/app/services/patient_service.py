from typing import Optional
from sqlalchemy import or_
from app.extensions import db
from app.models.patient import Patient
from app.utils.helpers import paginate


class PatientService:
    """Handles all patient business logic."""

    @staticmethod
    def get_patients(search: Optional[str], page: int, per_page: int) -> dict:
        """
        Get paginated list of active patients with optional search.

        Args:
            search: Optional search string — matches name or phone
            page: Page number
            per_page: Results per page

        Returns:
            Dict with items, total, page, per_page, pages
        """
        query = Patient.query.filter_by(is_active=True)

        if search:
            search_term = f"%{search}%"
            query = query.filter(
                or_(
                    Patient.first_name.ilike(search_term),
                    Patient.last_name.ilike(search_term),
                    Patient.phone.ilike(search_term),
                )
            )

        query = query.order_by(Patient.last_name, Patient.first_name)
        result = paginate(query, page, per_page)
        result['items'] = [p.to_dict() for p in result['items']]
        return result

    @staticmethod
    def get_patient_by_id(patient_id: int) -> Patient:
        """
        Get single patient by ID.

        Args:
            patient_id: Patient primary key

        Returns:
            Patient object

        Raises:
            ValueError: If patient not found or inactive
        """
        patient = Patient.query.filter_by(
            id=patient_id,
            is_active=True
        ).first()

        if not patient:
            raise ValueError(f"Patient {patient_id} not found")

        return patient

    @staticmethod
    def check_phone_exists(phone: str) -> bool:
        """
        Check if phone number already registered.
        Used for dedup check before registration.

        Args:
            phone: Phone number to check

        Returns:
            True if phone exists, False otherwise
        """
        return Patient.query.filter_by(phone=phone).first() is not None

    @staticmethod
    def create_patient(data: dict) -> Patient:
        """
        Create a new patient record.

        Args:
            data: Validated patient data from schema

        Returns:
            Created Patient object

        Raises:
            ValueError: If phone already exists
        """
        if PatientService.check_phone_exists(data['phone']):
            raise ValueError(f"Phone number {data['phone']} is already registered")

        patient = Patient(**data)
        db.session.add(patient)
        db.session.commit()
        return patient

    @staticmethod
    def update_patient(patient_id: int, data: dict) -> Patient:
        """
        Update existing patient record.

        Args:
            patient_id: Patient primary key
            data: Validated partial update data from schema

        Returns:
            Updated Patient object

        Raises:
            ValueError: If patient not found or phone conflict
        """
        patient = PatientService.get_patient_by_id(patient_id)

        # If phone is being changed, check it isn't taken by another patient
        if 'phone' in data and data['phone'] != patient.phone:
            if PatientService.check_phone_exists(data['phone']):
                raise ValueError(f"Phone number {data['phone']} is already registered")

        for key, value in data.items():
            setattr(patient, key, value)

        db.session.commit()
        return patient

    @staticmethod
    def delete_patient(patient_id: int) -> None:
        """
        Soft delete a patient — sets is_active=False.
        Never hard deletes to preserve medical history.

        Args:
            patient_id: Patient primary key

        Raises:
            ValueError: If patient not found
        """
        patient = PatientService.get_patient_by_id(patient_id)
        patient.is_active = False
        db.session.commit()

    @staticmethod
    def get_patient_visits(patient_id: int, page: int, per_page: int) -> dict:
        """
        Get paginated visit history for a patient.

        Args:
            patient_id: Patient primary key
            page: Page number
            per_page: Results per page

        Returns:
            Dict with paginated visit records

        Raises:
            ValueError: If patient not found
        """
        from app.models.visit import Visit

        # Verify patient exists first
        PatientService.get_patient_by_id(patient_id)

        query = Visit.query.filter_by(
            patient_id=patient_id
        ).order_by(Visit.created_at.desc())

        result = paginate(query, page, per_page)
        result['items'] = [v.to_dict() for v in result['items']]
        return result