from app.extensions import db
from sqlalchemy import func

class Cart(db.Model):
    __tablename__ = "carts"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    creation_date = db.Column(db.DateTime, nullable=False, server_default=func.now())
    status = db.Column(db.String(20), nullable=False, default="active")
    updated_at = db.Column(db.DateTime, nullable=False, server_default=func.now(), onupdate=func.now())
    created_at = db.Column(db.DateTime, nullable=False, server_default=func.now())

    # Relationships
    cart_products = db.relationship('CartProduct', backref='cart', lazy=True, cascade='all, delete-orphan')

    def __repr__(self):
        return f"<Cart {self.id} - User: {self.user_id}>"
