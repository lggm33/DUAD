from marshmallow import Schema, fields, validate

class SaleProductCreateSchema(Schema):
    sale_id = fields.Int(required=True)
    product_id = fields.Int(required=True)
    quantity = fields.Int(required=True, validate=validate.Range(min=1, max=999))
    price = fields.Decimal(required=True, validate=validate.Range(min=0), places=2)

class SaleProductReadSchema(Schema):
    sale_id = fields.Int()
    product_id = fields.Int()
    quantity = fields.Int()
    price = fields.Decimal(places=2)
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)
    # Nested product information
    product = fields.Nested("ProductReadSchema", dump_only=True)
    # Calculated fields
    subtotal = fields.Method("get_subtotal", dump_only=True)
    price_difference = fields.Method("get_price_difference", dump_only=True)
    
    def get_subtotal(self, obj):
        """Calculate subtotal for this sale item"""
        return float(obj.price) * obj.quantity if obj.price else 0.0
    
    def get_price_difference(self, obj):
        """Calculate difference between sale price and current product price"""
        if obj.product and obj.product.price and obj.price:
            return float(obj.product.price) - float(obj.price)
        return 0.0

class SaleProductUpdateSchema(Schema):
    quantity = fields.Int(required=False, validate=validate.Range(min=1, max=999))
    price = fields.Decimal(required=False, validate=validate.Range(min=0), places=2)

class SaleProductListSchema(Schema):
    sale_id = fields.Int()
    product_id = fields.Int()
    quantity = fields.Int()
    price = fields.Decimal(places=2)
    product = fields.Nested("ProductReadSchema", dump_only=True, only=("id", "name", "description"))
    subtotal = fields.Method("get_subtotal", dump_only=True)
    
    def get_subtotal(self, obj):
        """Calculate subtotal for this sale item"""
        return float(obj.price) * obj.quantity if obj.price else 0.0

class SaleProductReturnSchema(Schema):
    """Schema for handling product returns"""
    sale_id = fields.Int(required=True)
    product_id = fields.Int(required=True)
    return_quantity = fields.Int(required=True, validate=validate.Range(min=1))
    return_reason = fields.Str(required=False, validate=validate.Length(max=500))
    
class SaleProductDetailSchema(Schema):
    """Detailed schema for sale products with historical information"""
    sale_id = fields.Int()
    product_id = fields.Int()
    quantity = fields.Int()
    price = fields.Decimal(places=2)
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)
    # Full product information
    product = fields.Nested("ProductReadSchema", dump_only=True)
    # Calculated and comparison fields
    subtotal = fields.Method("get_subtotal", dump_only=True)
    current_product_price = fields.Method("get_current_price", dump_only=True)
    price_difference = fields.Method("get_price_difference", dump_only=True)
    
    def get_subtotal(self, obj):
        """Calculate subtotal for this sale item"""
        return float(obj.price) * obj.quantity if obj.price else 0.0
    
    def get_current_price(self, obj):
        """Get current product price"""
        return float(obj.product.price) if obj.product and obj.product.price else None
    
    def get_price_difference(self, obj):
        """Calculate difference between sale price and current product price"""
        if obj.product and obj.product.price and obj.price:
            return float(obj.product.price) - float(obj.price)
        return 0.0
