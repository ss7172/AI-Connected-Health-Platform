from flask import Blueprint, request
from flask_jwt_extended import jwt_required
from marshmallow import ValidationError
from app.services.patient_service import PatientService
from app.schemas.patient_schema import PatientSchema, PatientUpdateSchema
from app.utils.decorators import role_required
from app.utils.helpers import error_response, success_response, get_pagination_params

patients_bp = Blueprint('patients', __name__)


@patients_bp.route('', methods=['GET'])
@jwt_required()
def get_patients():
    """
    Get paginated list of patients with optional search.
    GET /api/v1/patients?search=&page=&per_page=
    All roles.
    """
    search = request.args.get('search', '').strip() or None
    page, per_page = get_pagination_params()

    result = PatientService.get_patients(search, page, per_page)
    return success_response(result, 200)


@patients_bp.route('/check-phone/<string:phone>', methods=['GET'])
@jwt_required()
@role_required(['front_desk', 'admin'])
def check_phone(phone: str):
    """
    Check if phone number already registered.
    GET /api/v1/patients/check-phone/:phone
    front_desk, admin only.
    """
    exists = PatientService.check_phone_exists(phone)
    return success_response({'exists': exists, 'phone': phone}, 200)


@patients_bp.route('/<int:patient_id>', methods=['GET'])
@jwt_required()
def get_patient(patient_id: int):
    """
    Get single patient by ID.
    GET /api/v1/patients/:id
    All roles.
    """
    try:
        patient = PatientService.get_patient_by_id(patient_id)
        return success_response({'patient': patient.to_dict()}, 200)
    except ValueError as e:
        return error_response(str(e), 404)


@patients_bp.route('', methods=['POST'])
@jwt_required()
@role_required(['front_desk', 'admin'])
def create_patient():
    """
    Create a new patient.
    POST /api/v1/patients
    front_desk, admin only.
    """
    data = request.get_json()

    if not data:
        return error_response("Request body is required", 400)

    try:
        validated = PatientSchema().load(data)
    except ValidationError as e:
        return error_response(str(e.messages), 400)

    try:
        patient = PatientService.create_patient(validated)
        return success_response({'patient': patient.to_dict()}, 201)
    except ValueError as e:
        return error_response(str(e), 409)


@patients_bp.route('/<int:patient_id>', methods=['PUT'])
@jwt_required()
@role_required(['front_desk', 'admin'])
def update_patient(patient_id: int):
    """
    Update existing patient.
    PUT /api/v1/patients/:id
    front_desk, admin only.
    """
    data = request.get_json()

    if not data:
        return error_response("Request body is required", 400)

    try:
        validated = PatientUpdateSchema().load(data)
    except ValidationError as e:
        return error_response(str(e.messages), 400)

    try:
        patient = PatientService.update_patient(patient_id, validated)
        return success_response({'patient': patient.to_dict()}, 200)
    except ValueError as e:
        return error_response(str(e), 404)


@patients_bp.route('/<int:patient_id>', methods=['DELETE'])
@jwt_required()
@role_required(['admin'])
def delete_patient(patient_id: int):
    """
    Soft delete a patient.
    DELETE /api/v1/patients/:id
    admin only.
    """
    try:
        PatientService.delete_patient(patient_id)
        return success_response({'message': 'Patient deactivated successfully'}, 200)
    except ValueError as e:
        return error_response(str(e), 404)


@patients_bp.route('/<int:patient_id>/visits', methods=['GET'])
@jwt_required()
@role_required(['doctor', 'admin'])
def get_patient_visits(patient_id: int):
    """
    Get visit history for a patient.
    GET /api/v1/patients/:id/visits
    doctor, admin only.
    """
    page, per_page = get_pagination_params()

    try:
        result = PatientService.get_patient_visits(patient_id, page, per_page)
        return success_response(result, 200)
    except ValueError as e:
        return error_response(str(e), 404)