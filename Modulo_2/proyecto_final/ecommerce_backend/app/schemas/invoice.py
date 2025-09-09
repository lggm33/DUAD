from marshmallow import Schema, fields, validate

# Invoice statuses for future use (returns, refunds, etc.)
INVOICE_STATUSES = ["issued", "paid", "cancelled", "refunded", "partially_refunded"]

class InvoiceCreateSchema(Schema):
    sale_id = fields.Int(required=True)
    delivery_address_id = fields.Int(required=True)

class InvoiceReadSchema(Schema):
    id = fields.Int(dump_only=True)
    sale_id = fields.Int()
    delivery_address_id = fields.Int()
    issue_date = fields.DateTime(dump_only=True)
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)
    # Nested relationships
    sale = fields.Nested("SaleReadSchema", dump_only=True, exclude=("invoices",))
    delivery_address = fields.Nested("DeliveryAddressReadSchema", dump_only=True)
    # Calculated fields
    invoice_number = fields.Method("get_invoice_number", dump_only=True)
    total_amount = fields.Method("get_total_amount", dump_only=True)
    
    def get_invoice_number(self, obj):
        """Generate a formatted invoice number"""
        return f"INV-{obj.id:06d}"
    
    def get_total_amount(self, obj):
        """Get total amount from related sale"""
        return obj.sale.total if obj.sale else None

class InvoiceUpdateSchema(Schema):
    delivery_address_id = fields.Int(required=False)

class InvoiceListSchema(Schema):
    id = fields.Int(dump_only=True)
    sale_id = fields.Int()
    delivery_address_id = fields.Int()
    issue_date = fields.DateTime(dump_only=True)
    sale = fields.Nested("SaleReadSchema", dump_only=True, only=("id", "total", "sale_date", "user_id"))
    delivery_address = fields.Nested("DeliveryAddressReadSchema", dump_only=True, only=("id", "city", "country", "address"))
    # Summary fields
    invoice_number = fields.Method("get_invoice_number", dump_only=True)
    customer_name = fields.Method("get_customer_name", dump_only=True)
    
    def get_invoice_number(self, obj):
        """Generate a formatted invoice number"""
        return f"INV-{obj.id:06d}"
    
    def get_customer_name(self, obj):
        """Get customer name from sale"""
        return obj.sale.user.name if obj.sale and obj.sale.user else None

class InvoiceSearchSchema(Schema):
    """Schema for searching invoices"""
    invoice_number = fields.Str(required=False)
    user_id = fields.Int(required=False)
    start_date = fields.DateTime(required=False)
    end_date = fields.DateTime(required=False)
    min_amount = fields.Decimal(required=False, validate=validate.Range(min=0))
    max_amount = fields.Decimal(required=False, validate=validate.Range(min=0))

class InvoiceDetailSchema(Schema):
    """Detailed invoice schema with all product information"""
    id = fields.Int(dump_only=True)
    sale_id = fields.Int()
    delivery_address_id = fields.Int()
    issue_date = fields.DateTime(dump_only=True)
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)
    # Full nested relationships
    sale = fields.Nested("SaleReadSchema", dump_only=True, exclude=("invoices",))
    delivery_address = fields.Nested("DeliveryAddressReadSchema", dump_only=True)
    # Formatted fields
    invoice_number = fields.Method("get_invoice_number", dump_only=True)
    
    def get_invoice_number(self, obj):
        """Generate a formatted invoice number"""
        return f"INV-{obj.id:06d}"
