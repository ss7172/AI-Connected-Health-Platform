from flask import Blueprint, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from marshmallow import ValidationError
from app.services.visit_service import VisitService
from app.schemas.visit_schema import VisitSchema, VisitUpdateSchema
from app.utils.decorators import role_required
from app.utils.helpers import error_response, success_response

visits_bp = Blueprint('visits', __name__)


@visits_bp.route('', methods=['GET'])
@jwt_required()
@role_required(['doctor', 'admin'])
def get_visits():
    """
    Get filtered list of visits.
    GET /api/v1/visits?patient_id=&doctor_id=&date_from=&date_to=
    doctor, admin only.
    """
    try:
        visits = VisitService.get_visits(
            patient_id=request.args.get('patient_id', type=int),
            doctor_id=request.args.get('doctor_id', type=int),
            date_from=request.args.get('date_from'),
            date_to=request.args.get('date_to'),
        )
        return success_response({'visits': visits}, 200)
    except ValueError as e:
        return error_response(str(e), 400)


@visits_bp.route('/<int:visit_id>', methods=['GET'])
@jwt_required()
@role_required(['doctor', 'admin'])
def get_visit(visit_id: int):
    """
    Get single visit detail.
    GET /api/v1/visits/:id
    doctor, admin only.
    """
    try:
        visit = VisitService.get_visit_by_id(visit_id)
        return success_response({'visit': visit.to_dict()}, 200)
    except ValueError as e:
        return error_response(str(e), 404)


@visits_bp.route('', methods=['POST'])
@jwt_required()
@role_required(['doctor'])
def create_visit():
    """
    Create visit and auto-generate billing record.
    POST /api/v1/visits
    doctor only.
    """
    data = request.get_json()

    if not data:
        return error_response("Request body is required", 400)

    try:
        validated = VisitSchema().load(data)
    except ValidationError as e:
        return error_response(str(e.messages), 400)

    try:
        visit = VisitService.create_visit(**validated)
        return success_response({'visit': visit.to_dict()}, 201)
    except ValueError as e:
        return error_response(str(e), 400)


@visits_bp.route('/<int:visit_id>', methods=['PUT'])
@jwt_required()
@role_required(['doctor'])
def update_visit(visit_id: int):
    """
    Update visit clinical notes.
    PUT /api/v1/visits/:id
    doctor only.
    """
    data = request.get_json()

    if not data:
        return error_response("Request body is required", 400)

    try:
        validated = VisitUpdateSchema().load(data)
    except ValidationError as e:
        return error_response(str(e.messages), 400)

    try:
        visit = VisitService.update_visit(visit_id, validated)
        return success_response({'visit': visit.to_dict()}, 200)
    except ValueError as e:
        return error_response(str(e), 404)