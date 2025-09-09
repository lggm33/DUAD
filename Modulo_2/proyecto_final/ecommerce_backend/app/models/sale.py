from app.extensions import db
from sqlalchemy import func

class Sale(db.Model):
    __tablename__ = "sales"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    sale_date = db.Column(db.DateTime, nullable=False, server_default=func.now())
    total = db.Column(db.Numeric(10, 2), nullable=False)
    updated_at = db.Column(db.DateTime, nullable=False, server_default=func.now(), onupdate=func.now())
    created_at = db.Column(db.DateTime, nullable=False, server_default=func.now())

    # Relationships
    sale_products = db.relationship('SaleProduct', backref='sale', lazy=True, cascade='all, delete-orphan')
    invoices = db.relationship('Invoice', back_populates='sale', lazy=True, cascade='all, delete-orphan')

    def __repr__(self):
        return f"<Sale {self.id} - User: {self.user_id}, Total: {self.total}>"
