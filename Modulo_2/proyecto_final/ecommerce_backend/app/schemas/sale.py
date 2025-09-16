from marshmallow import Schema, fields, validate
from decimal import Decimal

class SaleCreateSchema(Schema):
    user_id = fields.Int(required=True)
    total = fields.Decimal(required=True, validate=validate.Range(min=0), places=2)

class SaleReadSchema(Schema):
    id = fields.Int(dump_only=True)
    user_id = fields.Int()
    sale_date = fields.DateTime(dump_only=True)
    total = fields.Decimal(places=2)
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)
    # Nested relationships
    sale_products = fields.Nested("SaleProductReadSchema", many=True, dump_only=True)
    user = fields.Nested("UserReadSchema", dump_only=True, only=("id", "name", "email"))
    invoices = fields.Nested("InvoiceReadSchema", many=True, dump_only=True, exclude=("sale",))
    # Calculated fields
    product_count = fields.Method("get_product_count", dump_only=True)
    total_items = fields.Method("get_total_items", dump_only=True)
    
    def get_product_count(self, obj):
        """Get number of different products in sale"""
        return len(obj.sale_products) if obj.sale_products else 0
    
    def get_total_items(self, obj):
        """Get total quantity of all items in sale"""
        if not obj.sale_products:
            return 0
        return sum(sp.quantity for sp in obj.sale_products)

class SaleUpdateSchema(Schema):
    total = fields.Decimal(required=False, validate=validate.Range(min=0), places=2)

class SaleListSchema(Schema):
    id = fields.Int(dump_only=True)
    user_id = fields.Int()
    sale_date = fields.DateTime(dump_only=True)
    total = fields.Decimal(places=2)
    user = fields.Nested("UserReadSchema", dump_only=True, only=("id", "name", "email"))
    # Summary fields
    product_count = fields.Method("get_product_count", dump_only=True)
    total_items = fields.Method("get_total_items", dump_only=True)
    has_invoice = fields.Method("get_has_invoice", dump_only=True)
    
    def get_product_count(self, obj):
        """Get number of different products in sale"""
        return len(obj.sale_products) if obj.sale_products else 0
    
    def get_total_items(self, obj):
        """Get total quantity of all items in sale"""
        if not obj.sale_products:
            return 0
        return sum(sp.quantity for sp in obj.sale_products)
    
    def get_has_invoice(self, obj):
        """Check if sale has at least one invoice"""
        return len(obj.invoices) > 0 if obj.invoices else False

class SaleFromCartSchema(Schema):
    """Schema for creating a sale from a cart"""
    cart_id = fields.Int(required=True)
    delivery_address_id = fields.Int(required=True)
    # Optional fields for payment processing
    payment_method = fields.Str(required=False, validate=validate.OneOf(["credit_card", "debit_card", "paypal", "cash"]))
    payment_reference = fields.Str(required=False)
    # Optional field for automatic invoice generation
    generate_invoice = fields.Bool(required=False)
