import os
from flask import Blueprint, request, send_file
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.services.document_service import DocumentService
from app.utils.decorators import role_required
from app.utils.helpers import error_response, success_response

documents_bp = Blueprint('documents', __name__)

VALID_CATEGORIES = [
    'lab_report', 'prescription', 'imaging',
    'discharge_summary', 'other'
]


@documents_bp.route('/upload', methods=['POST'])
@jwt_required()
@role_required(['front_desk', 'doctor', 'admin'])
def upload_document():
    """
    Upload a patient document.
    POST /api/v1/documents/upload
    Multipart form: file + patient_id + document_category + visit_id(opt) + description(opt)
    front_desk, doctor, admin only.
    """
    # Validate file present
    if 'file' not in request.files:
        return error_response("No file provided", 400)

    file = request.files['file']
    if not file.filename:
        return error_response("No file selected", 400)

    # Validate required form fields
    patient_id = request.form.get('patient_id', type=int)
    document_category = request.form.get('document_category', '').strip()

    if not patient_id:
        return error_response("patient_id is required", 400)
    if not document_category:
        return error_response("document_category is required", 400)
    if document_category not in VALID_CATEGORIES:
        return error_response(
            f"Invalid category. Must be one of: {VALID_CATEGORIES}", 400
        )

    # Optional fields
    visit_id = request.form.get('visit_id', type=int)
    description = request.form.get('description', '').strip() or None

    # Get uploader ID from token
    user_id = int(get_jwt_identity())

    try:
        document = DocumentService.upload_document(
            file=file,
            patient_id=patient_id,
            document_category=document_category,
            uploaded_by=user_id,
            visit_id=visit_id,
            description=description,
        )
        return success_response({'document': document.to_dict()}, 201)
    except ValueError as e:
        return error_response(str(e), 400)


@documents_bp.route('/<int:document_id>', methods=['GET'])
@jwt_required()
@role_required(['doctor', 'admin'])
def get_document(document_id: int):
    """
    Get document metadata.
    GET /api/v1/documents/:id
    doctor, admin only.
    """
    try:
        document = DocumentService.get_document_by_id(document_id)
        return success_response({'document': document.to_dict()}, 200)
    except ValueError as e:
        return error_response(str(e), 404)


@documents_bp.route('/<int:document_id>/download', methods=['GET'])
@jwt_required()
@role_required(['doctor', 'admin'])
def download_document(document_id: int):
    """
    Download a document file.
    GET /api/v1/documents/:id/download
    doctor, admin only.
    """
    try:
        abs_path, filename = DocumentService.get_file_path(document_id)

        if not os.path.exists(abs_path):
            return error_response("File not found on server", 404)

        return send_file(
            abs_path,
            as_attachment=True,
            download_name=filename,
        )
    except ValueError as e:
        return error_response(str(e), 404)


@documents_bp.route('/<int:document_id>', methods=['DELETE'])
@jwt_required()
@role_required(['admin'])
def delete_document(document_id: int):
    """
    Delete document and file.
    DELETE /api/v1/documents/:id
    admin only.
    """
    try:
        DocumentService.delete_document(document_id)
        return success_response(
            {'message': 'Document deleted successfully'}, 200
        )
    except ValueError as e:
        return error_response(str(e), 404)