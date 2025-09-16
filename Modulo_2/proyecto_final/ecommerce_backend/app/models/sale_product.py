from app.extensions import db
from sqlalchemy import func

class SaleProduct(db.Model):
    __tablename__ = "sale_products"

    # Composite Primary Key
    sale_id = db.Column(db.Integer, db.ForeignKey('sales.id'), primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), primary_key=True)
    quantity = db.Column(db.Integer, nullable=False, default=1)
    price = db.Column(db.Numeric(10, 2), nullable=False)  # Price at time of sale
    updated_at = db.Column(db.DateTime, nullable=False, server_default=func.now(), onupdate=func.now())
    created_at = db.Column(db.DateTime, nullable=False, server_default=func.now())
    
    def __repr__(self):
        return f"<SaleProduct Sale: {self.sale_id}, Product: {self.product_id}, Qty: {self.quantity}>"
