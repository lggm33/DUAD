from app.extensions import db
from sqlalchemy import func

class CartProduct(db.Model):
    __tablename__ = "cart_products"

    # Composite Primary Key
    cart_id = db.Column(db.Integer, db.ForeignKey('carts.id'), primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), primary_key=True)
    quantity = db.Column(db.Integer, nullable=False, default=1)
    updated_at = db.Column(db.DateTime, nullable=False, server_default=func.now(), onupdate=func.now())

    def __repr__(self):
        return f"<CartProduct Cart: {self.cart_id}, Product: {self.product_id}, Qty: {self.quantity}>"
