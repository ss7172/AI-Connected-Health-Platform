from marshmallow import Schema, fields, validate, validates, ValidationError


class PatientSchema(Schema):
    """Validates patient create/update requests."""

    first_name = fields.Str(required=True, validate=validate.Length(min=1, max=100))
    last_name = fields.Str(required=True, validate=validate.Length(min=1, max=100))
    date_of_birth = fields.Date(required=True)
    gender = fields.Str(required=True, validate=validate.OneOf(['male', 'female', 'other']))
    phone = fields.Str(required=True, validate=validate.Length(min=10, max=20))
    email = fields.Email(required=False, load_default=None)
    address = fields.Str(required=False, load_default=None)
    emergency_contact = fields.Str(required=False, load_default=None)
    blood_group = fields.Str(
        required=False,
        load_default=None,
        validate=validate.OneOf(['A+', 'A-', 'B+', 'B-', 'O+', 'O-', 'AB+', 'AB-'])
    )

    @validates('phone')
    def validate_phone(self, value: str) -> None:
        """Ensure phone contains only digits and optional leading +."""
        cleaned = value.replace(' ', '').replace('-', '')
        if not cleaned.lstrip('+').isdigit():
            raise ValidationError("Phone must contain only digits")


class PatientUpdateSchema(Schema):
    """Same as PatientSchema but all fields optional for partial updates."""

    first_name = fields.Str(required=False, validate=validate.Length(min=1, max=100))
    last_name = fields.Str(required=False, validate=validate.Length(min=1, max=100))
    date_of_birth = fields.Date(required=False)
    gender = fields.Str(required=False, validate=validate.OneOf(['male', 'female', 'other']))
    phone = fields.Str(required=False, validate=validate.Length(min=10, max=20))
    email = fields.Email(required=False)
    address = fields.Str(required=False)
    emergency_contact = fields.Str(required=False)
    blood_group = fields.Str(
        required=False,
        validate=validate.OneOf(['A+', 'A-', 'B+', 'B-', 'O+', 'O-', 'AB+', 'AB-'])
    )