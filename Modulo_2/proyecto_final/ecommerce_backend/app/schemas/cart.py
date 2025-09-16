from marshmallow import Schema, fields, validate

# Valid cart statuses
CART_STATUSES = ["active", "abandoned", "converted", "expired"]

class CartCreateSchema(Schema):
    user_id = fields.Int(required=True)
    status = fields.Str(required=False, validate=validate.OneOf(CART_STATUSES), load_default="active")

class CartReadSchema(Schema):
    id = fields.Int(dump_only=True)
    user_id = fields.Int()
    creation_date = fields.DateTime(dump_only=True)
    status = fields.Str()
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)
    # Nested relationship for cart products
    cart_products = fields.Nested("CartProductReadSchema", many=True, dump_only=True)

class CartUpdateSchema(Schema):
    status = fields.Str(required=False, validate=validate.OneOf(CART_STATUSES))

class CartListSchema(Schema):
    id = fields.Int(dump_only=True)
    user_id = fields.Int()
    creation_date = fields.DateTime(dump_only=True)
    status = fields.Str()
    # Count of products in cart
    product_count = fields.Method("get_product_count", dump_only=True)
    
    def get_product_count(self, obj):
        """Calculate total number of products in cart"""
        return len(obj.cart_products) if obj.cart_products else 0
