from marshmallow import Schema, fields, validate

class ProductCreateSchema(Schema):
    name = fields.Str(required=True, validate=validate.Length(min=1, max=120))
    description = fields.Str(required=False, allow_none=True)
    price = fields.Decimal(required=True, validate=validate.Range(min=0))
    stock = fields.Int(required=True, validate=validate.Range(min=0))

class ProductReadSchema(Schema):
    id = fields.Int(dump_only=True)
    name = fields.Str()
    description = fields.Str()
    price = fields.Decimal()
    stock = fields.Int()
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)

class ProductUpdateSchema(Schema):
    name = fields.Str(required=False, validate=validate.Length(min=1, max=120))
    description = fields.Str(required=False, allow_none=True)
    price = fields.Decimal(required=False, validate=validate.Range(min=0))
    stock = fields.Int(required=False, validate=validate.Range(min=0))

class ProductListSchema(Schema):
    id = fields.Int(dump_only=True)
    name = fields.Str()
    price = fields.Decimal()
    stock = fields.Int()
