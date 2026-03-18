from decimal import Decimal
from app.extensions import db
from app.models.visit import Visit
from app.models.appointment import Appointment
from app.models.billing import BillingRecord, BillingItem


class VisitService:
    """
    Handles visit creation with auto-billing.
    Creating a visit automatically creates a billing record
    with the department consultation fee as the first line item.
    """

    @staticmethod
    def get_visits(
        patient_id: int = None,
        doctor_id: int = None,
        date_from: str = None,
        date_to: str = None,
    ) -> list:
        """
        Get filtered list of visits.

        Args:
            patient_id: Filter by patient
            doctor_id: Filter by doctor
            date_from: Filter visits from this date (YYYY-MM-DD)
            date_to: Filter visits to this date (YYYY-MM-DD)

        Returns:
            List of visit dicts ordered by created_at DESC
        """
        from datetime import datetime

        query = Visit.query

        if patient_id:
            query = query.filter_by(patient_id=patient_id)
        if doctor_id:
            query = query.filter_by(doctor_id=doctor_id)
        if date_from:
            try:
                date_from_obj = datetime.strptime(date_from, '%Y-%m-%d')
                query = query.filter(Visit.created_at >= date_from_obj)
            except ValueError:
                raise ValueError("Invalid date_from format. Use YYYY-MM-DD")
        if date_to:
            try:
                date_to_obj = datetime.strptime(date_to, '%Y-%m-%d')
                query = query.filter(Visit.created_at <= date_to_obj)
            except ValueError:
                raise ValueError("Invalid date_to format. Use YYYY-MM-DD")

        visits = query.order_by(Visit.created_at.desc()).all()
        return [v.to_dict() for v in visits]

    @staticmethod
    def get_visit_by_id(visit_id: int) -> Visit:
        """
        Get single visit by ID.

        Args:
            visit_id: Visit primary key

        Returns:
            Visit object

        Raises:
            ValueError: If visit not found
        """
        visit = Visit.query.get(visit_id)
        if not visit:
            raise ValueError(f"Visit {visit_id} not found")
        return visit

    @staticmethod
    def create_visit(
        appointment_id: int,
        symptoms: str = None,
        diagnosis: str = None,
        diagnosis_code: str = None,
        prescription: str = None,
        follow_up_notes: str = None,
        follow_up_date=None,
    ) -> Visit:
        """
        Create a visit and auto-generate billing record.

        Flow:
        1. Verify appointment exists and is in_progress
        2. Create Visit record
        3. Update appointment status to completed
        4. Get department consultation fee
        5. Create BillingRecord
        6. Create BillingItem for consultation fee
        7. Commit all in single transaction

        Args:
            appointment_id: Must be in_progress status
            symptoms: Patient reported symptoms
            diagnosis: Doctor's diagnosis (required)
            diagnosis_code: ICD-10 code
            prescription: Free text prescription
            follow_up_notes: Follow-up instructions
            follow_up_date: Follow-up appointment date

        Returns:
            Created Visit object

        Raises:
            ValueError: If appointment not found, wrong status, or visit exists
        """
        # Verify appointment exists
        appointment = Appointment.query.get(appointment_id)
        if not appointment:
            raise ValueError(f"Appointment {appointment_id} not found")

        # Appointment must be in_progress
        if appointment.status != 'in_progress':
            raise ValueError(
                f"Appointment must be 'in_progress' to create a visit. "
                f"Current status: '{appointment.status}'"
            )

        # Check visit doesn't already exist
        existing_visit = Visit.query.filter_by(
            appointment_id=appointment_id
        ).first()
        if existing_visit:
            raise ValueError(
                f"Visit already exists for appointment {appointment_id}"
            )

        # Create visit
        visit = Visit(
            appointment_id=appointment_id,
            patient_id=appointment.patient_id,
            doctor_id=appointment.doctor_id,
            symptoms=symptoms,
            diagnosis=diagnosis,
            diagnosis_code=diagnosis_code,
            prescription=prescription,
            follow_up_notes=follow_up_notes,
            follow_up_date=follow_up_date,
        )
        db.session.add(visit)

        # Update appointment to completed
        appointment.status = 'completed'

        # Flush to get visit.id
        db.session.flush()

        # Get department consultation fee
        department = appointment.department
        consultation_fee = Decimal(str(department.consultation_fee))

        # Create billing record
        billing_record = BillingRecord(
            visit_id=visit.id,
            patient_id=appointment.patient_id,
            total_amount=consultation_fee,
            status='pending',
        )
        db.session.add(billing_record)
        db.session.flush()

        # Create consultation fee line item
        consultation_item = BillingItem(
            billing_record_id=billing_record.id,
            description=f"{department.name} Consultation",
            category='consultation',
            amount=consultation_fee,
        )
        db.session.add(consultation_item)

        # Commit everything in one transaction
        db.session.commit()

        return visit

    @staticmethod
    def update_visit(visit_id: int, data: dict) -> Visit:
        """
        Update visit notes and clinical details.

        Args:
            visit_id: Visit primary key
            data: Fields to update

        Returns:
            Updated Visit object

        Raises:
            ValueError: If visit not found
        """
        visit = VisitService.get_visit_by_id(visit_id)

        for key, value in data.items():
            setattr(visit, key, value)

        db.session.commit()
        return visit