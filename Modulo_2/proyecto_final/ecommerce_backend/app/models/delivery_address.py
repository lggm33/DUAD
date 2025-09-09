from app.extensions import db
from sqlalchemy import func

class DeliveryAddress(db.Model):
    __tablename__ = "delivery_addresses"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    address = db.Column(db.Text, nullable=False)
    city = db.Column(db.String(100), nullable=False)
    postal_code = db.Column(db.String(20), nullable=False)
    country = db.Column(db.String(100), nullable=False)
    updated_at = db.Column(db.DateTime, nullable=False, server_default=func.now(), onupdate=func.now())
    created_at = db.Column(db.DateTime, nullable=False, server_default=func.now())

    # Relationships
    invoices = db.relationship('Invoice', backref='delivery_address', lazy=True)

    def __repr__(self):
        return f"<DeliveryAddress {self.city}, {self.country}>"
