from marshmallow import Schema, fields, validate

class CartProductCreateSchema(Schema):
    cart_id = fields.Int(required=True)
    product_id = fields.Int(required=True)
    quantity = fields.Int(required=True, validate=validate.Range(min=1, max=999))

class CartProductReadSchema(Schema):
    cart_id = fields.Int()
    product_id = fields.Int()
    quantity = fields.Int()
    updated_at = fields.DateTime(dump_only=True)
    # Nested product information
    product = fields.Nested("ProductReadSchema", dump_only=True)
    # Calculated fields
    subtotal = fields.Method("get_subtotal", dump_only=True)
    
    def get_subtotal(self, obj):
        """Calculate subtotal for this cart item"""
        if obj.product and obj.product.price:
            return float(obj.product.price) * obj.quantity
        return 0.0

class CartProductUpdateSchema(Schema):
    quantity = fields.Int(required=True, validate=validate.Range(min=1, max=999))

class CartProductListSchema(Schema):
    cart_id = fields.Int()
    product_id = fields.Int()
    quantity = fields.Int()
    product = fields.Nested("ProductReadSchema", dump_only=True, only=("id", "name", "price", "stock"))
    subtotal = fields.Method("get_subtotal", dump_only=True)
    
    def get_subtotal(self, obj):
        """Calculate subtotal for this cart item"""
        if obj.product and obj.product.price:
            return float(obj.product.price) * obj.quantity
        return 0.0

class AddToCartSchema(Schema):
    """Schema for adding products to cart"""
    product_id = fields.Int(required=True)
    quantity = fields.Int(validate=validate.Range(min=1, max=999), load_default=1)

class UpdateCartProductSchema(Schema):
    """Schema for updating cart product quantity"""
    quantity = fields.Int(required=True, validate=validate.Range(min=0, max=999))  # 0 means remove
