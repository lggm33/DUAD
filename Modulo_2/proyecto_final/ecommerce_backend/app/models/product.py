from app.extensions import db
from sqlalchemy import func

class Product(db.Model):
    __tablename__ = "products"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False, unique=True, index=True)
    description = db.Column(db.Text, nullable=True)
    price = db.Column(db.Numeric(10, 2), nullable=False, index=True)
    stock = db.Column(db.Integer, nullable=False, default=0)

    created_at = db.Column(db.DateTime, nullable=False, server_default=func.now())
    updated_at = db.Column(db.DateTime, nullable=False, server_default=func.now(), onupdate=func.now())

    # Relationships
    cart_products = db.relationship('CartProduct', backref='product', lazy=True, cascade='all, delete-orphan')
    sale_products = db.relationship('SaleProduct', backref='product', lazy=True, cascade='all, delete-orphan')

    def update(self, data: dict):
        """Update product fields from dictionary"""
        for key, value in data.items():
            if hasattr(self, key) and key != 'id':
                setattr(self, key, value)
    
    def __repr__(self):
        return f"<Product {self.name}>"
