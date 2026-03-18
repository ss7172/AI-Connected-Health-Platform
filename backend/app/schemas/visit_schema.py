from marshmallow import Schema, fields, validate


class VisitSchema(Schema):
    """Validates visit create requests."""

    appointment_id = fields.Int(required=True)
    symptoms = fields.Str(required=False, load_default=None)
    diagnosis = fields.Str(required=True, validate=validate.Length(min=1))
    diagnosis_code = fields.Str(required=False, load_default=None)
    prescription = fields.Str(required=False, load_default=None)
    follow_up_notes = fields.Str(required=False, load_default=None)
    follow_up_date = fields.Date(required=False, load_default=None)


class VisitUpdateSchema(Schema):
    """Validates visit update requests — all fields optional."""

    symptoms = fields.Str(required=False)
    diagnosis = fields.Str(required=False, validate=validate.Length(min=1))
    diagnosis_code = fields.Str(required=False)
    prescription = fields.Str(required=False)
    follow_up_notes = fields.Str(required=False)
    follow_up_date = fields.Date(required=False)