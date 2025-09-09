from marshmallow import Schema, fields, validate

class RegisterSchema(Schema):
    email = fields.Email(required=True)
    password = fields.Str(required=True, load_only=True, validate=validate.Length(min=8))
    name = fields.Str(required=True)
    phone = fields.Str(required=False, allow_none=True)
    role = fields.Str(required=False, allow_none=True)

class LoginSchema(Schema):
    email = fields.Email(required=True)
    password = fields.Str(required=True, load_only=True)

class UserReadSchema(Schema):
    id = fields.Int(dump_only=True)
    email = fields.Email()
    role = fields.Str()
    is_active = fields.Bool()
    name = fields.Str()
    phone = fields.Str()
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)

class UserUpdateSchema(Schema):
    name = fields.Str(required=False)
    phone = fields.Str(required=False, allow_none=True)
    is_active = fields.Bool(required=False)
