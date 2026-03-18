import os
import uuid
from werkzeug.utils import secure_filename

# Absolute path to uploads/ directory at backend root
UPLOAD_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
    'uploads'
)

ALLOWED_EXTENSIONS = {'pdf', 'jpg', 'jpeg', 'png'}


def allowed_file(filename: str) -> bool:
    """
    Check if file extension is allowed.

    Args:
        filename: Original filename from upload

    Returns:
        True if extension is allowed
    """
    return (
        '.' in filename and
        filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS
    )


def save_file(file, patient_id: int) -> tuple[str, int]:
    """
    Save uploaded file to disk.

    Storage pattern: uploads/patients/{patient_id}/{uuid}.{ext}
    UUID filename prevents collisions and path traversal attacks.

    Args:
        file: Werkzeug FileStorage object from request.files
        patient_id: Patient ID for directory organization

    Returns:
        Tuple of (relative_path, file_size_bytes)

    Raises:
        ValueError: If file type not allowed
    """
    if not file or not file.filename:
        raise ValueError("No file provided")

    if not allowed_file(file.filename):
        raise ValueError(
            f"File type not allowed. Allowed types: {ALLOWED_EXTENSIONS}"
        )

    # Get extension from original filename
    ext = file.filename.rsplit('.', 1)[1].lower()

    # Generate UUID filename — never use original filename on disk
    uuid_filename = f"{uuid.uuid4().hex}.{ext}"

    # Create patient directory if needed
    patient_dir = os.path.join(UPLOAD_DIR, 'patients', str(patient_id))
    os.makedirs(patient_dir, exist_ok=True)

    # Save file
    abs_path = os.path.join(patient_dir, uuid_filename)
    file.save(abs_path)

    file_size = os.path.getsize(abs_path)
    relative_path = f"uploads/patients/{patient_id}/{uuid_filename}"

    return relative_path, file_size


def get_absolute_path(relative_path: str) -> str:
    """
    Convert DB-stored relative path to absolute path for serving.

    Args:
        relative_path: Path stored in DB e.g. uploads/patients/1/abc123.pdf

    Returns:
        Absolute filesystem path
    """
    base = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    return os.path.join(base, relative_path)


def delete_file(relative_path: str) -> None:
    """
    Delete file from disk.

    Args:
        relative_path: Path stored in DB
    """
    abs_path = get_absolute_path(relative_path)
    if os.path.exists(abs_path):
        os.remove(abs_path)