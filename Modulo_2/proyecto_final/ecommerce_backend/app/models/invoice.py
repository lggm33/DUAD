from app.extensions import db
from sqlalchemy import func

class Invoice(db.Model):
    __tablename__ = "invoices"

    id = db.Column(db.Integer, primary_key=True)
    sale_id = db.Column(db.Integer, db.ForeignKey('sales.id'), nullable=False, index=True)
    delivery_address_id = db.Column(db.Integer, db.ForeignKey('delivery_addresses.id'), nullable=False, index=True)
    issue_date = db.Column(db.DateTime, nullable=False, server_default=func.now())
    created_at = db.Column(db.DateTime, nullable=False, server_default=func.now())
    updated_at = db.Column(db.DateTime, nullable=False, server_default=func.now(), onupdate=func.now())

    # Relationships
    sale = db.relationship('Sale', back_populates='invoices', lazy=True)

    def __repr__(self):
        return f"<Invoice {self.id} - Sale: {self.sale_id}>"
