from marshmallow import Schema, fields, validate

class DeliveryAddressCreateSchema(Schema):
    user_id = fields.Int(required=True)
    address = fields.Str(required=True, validate=validate.Length(min=1))
    city = fields.Str(required=True, validate=validate.Length(min=1, max=100))
    postal_code = fields.Str(required=True, validate=validate.Length(min=1, max=20))
    country = fields.Str(required=True, validate=validate.Length(min=1, max=100))

class DeliveryAddressReadSchema(Schema):
    id = fields.Int(dump_only=True)
    user_id = fields.Int()
    address = fields.Str()
    city = fields.Str()
    postal_code = fields.Str()
    country = fields.Str()
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)

class DeliveryAddressUpdateSchema(Schema):
    address = fields.Str(required=False, validate=validate.Length(min=1))
    city = fields.Str(required=False, validate=validate.Length(min=1, max=100))
    postal_code = fields.Str(required=False, validate=validate.Length(min=1, max=20))
    country = fields.Str(required=False, validate=validate.Length(min=1, max=100))
