from flask import Blueprint, request
from flask_jwt_extended import jwt_required
from marshmallow import ValidationError
from app.services.billing_service import BillingService
from app.schemas.billing_schema import (
    BillingItemSchema, BillingItemUpdateSchema, BillingPaymentSchema
)
from app.utils.decorators import role_required
from app.utils.helpers import error_response, success_response

billing_bp = Blueprint('billing', __name__)


# @billing_bp.route('', methods=['GET'])
# @jwt_required()
# @role_required(['front_desk', 'admin'])
# def get_billing_records():
#     """
#     Get filtered list of billing records.
#     GET /api/v1/billing?status=&date_from=&date_to=
#     front_desk, admin only.
#     """
#     try:
#         records = BillingService.get_billing_records(
#             status=request.args.get('status'),
#             date_from=request.args.get('date_from'),
#             date_to=request.args.get('date_to'),
#         )
#         return success_response({'billing_records': records}, 200)
#     except ValueError as e:
#         return error_response(str(e), 400)


@billing_bp.route('', methods=['GET'])
@jwt_required()
@role_required(['front_desk', 'admin'])
def get_billing_records():
    """
    GET /api/v1/billing?status=&date_from=&date_to=&page=&per_page=
    """
    from app.utils.helpers import get_pagination_params
    page, per_page = get_pagination_params()

    try:
        result = BillingService.get_billing_records(
            status=request.args.get('status'),
            date_from=request.args.get('date_from'),
            date_to=request.args.get('date_to'),
            page=page,
            per_page=per_page,
        )
        return success_response(result, 200)
    except ValueError as e:
        return error_response(str(e), 400)


@billing_bp.route('/<int:billing_id>/items', methods=['POST'])
@jwt_required()
@role_required(['front_desk', 'admin'])
def add_line_item(billing_id: int):
    """
    Add a line item to an invoice.
    POST /api/v1/billing/:id/items
    front_desk, admin only.
    """
    data = request.get_json()

    if not data:
        return error_response("Request body is required", 400)

    try:
        validated = BillingItemSchema().load(data)
    except ValidationError as e:
        return error_response(str(e.messages), 400)

    try:
        record = BillingService.add_line_item(
            billing_id=billing_id,
            description=validated['description'],
            category=validated['category'],
            amount=validated['amount'],
        )
        return success_response({'billing_record': record.to_dict()}, 201)
    except ValueError as e:
        return error_response(str(e), 400)


@billing_bp.route('/<int:billing_id>/items/<int:item_id>', methods=['PUT'])
@jwt_required()
@role_required(['front_desk', 'admin'])
def update_line_item(billing_id: int, item_id: int):
    """
    Update a line item.
    PUT /api/v1/billing/:id/items/:item_id
    front_desk, admin only.
    """
    data = request.get_json()

    if not data:
        return error_response("Request body is required", 400)

    try:
        validated = BillingItemUpdateSchema().load(data)
    except ValidationError as e:
        return error_response(str(e.messages), 400)

    try:
        record = BillingService.update_line_item(billing_id, item_id, validated)
        return success_response({'billing_record': record.to_dict()}, 200)
    except ValueError as e:
        return error_response(str(e), 400)


@billing_bp.route('/<int:billing_id>/items/<int:item_id>', methods=['DELETE'])
@jwt_required()
@role_required(['front_desk', 'admin'])
def remove_line_item(billing_id: int, item_id: int):
    """
    Remove a line item — cannot remove consultation fee.
    DELETE /api/v1/billing/:id/items/:item_id
    front_desk, admin only.
    """
    try:
        record = BillingService.remove_line_item(billing_id, item_id)
        return success_response({'billing_record': record.to_dict()}, 200)
    except ValueError as e:
        return error_response(str(e), 400)


@billing_bp.route('/<int:billing_id>/pay', methods=['PATCH'])
@jwt_required()
@role_required(['front_desk', 'admin'])
def process_payment(billing_id: int):
    """
    Mark invoice as paid.
    PATCH /api/v1/billing/:id/pay
    front_desk, admin only.
    """
    data = request.get_json()

    if not data:
        return error_response("Request body is required", 400)

    try:
        validated = BillingPaymentSchema().load(data)
    except ValidationError as e:
        return error_response(str(e.messages), 400)

    try:
        record = BillingService.process_payment(
            billing_id=billing_id,
            payment_method=validated['payment_method'],
            notes=validated.get('notes'),
        )
        return success_response({'billing_record': record.to_dict()}, 200)
    except ValueError as e:
        return error_response(str(e), 400)