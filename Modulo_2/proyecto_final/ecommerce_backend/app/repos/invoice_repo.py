# app/repos/invoice_repo.py
from typing import Optional, List
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import joinedload
from app.extensions import db
from app.models.invoice import Invoice
from app.models.sale import Sale
from app.models.sale_product import SaleProduct
from app.models.product import Product
from app.models.delivery_address import DeliveryAddress
from app.utils.exceptions import RepoError
from datetime import datetime

def get_by_id(invoice_id: int) -> Optional[Invoice]:
    """Get invoice by ID"""
    return db.session.get(Invoice, invoice_id)

def get_by_sale_id(sale_id: int) -> List[Invoice]:
    """Get all invoices for a sale"""
    return Invoice.query.filter_by(sale_id=sale_id).order_by(Invoice.issue_date.desc()).all()

def get_by_user_id(user_id: int) -> List[Invoice]:
    """Get all invoices for a user through sales relationship"""
    return Invoice.query.join(Invoice.sale).filter_by(user_id=user_id).order_by(Invoice.issue_date.desc()).all()

def get_all() -> List[Invoice]:
    """Get all invoices"""
    return Invoice.query.order_by(Invoice.issue_date.desc()).all()

def create_invoice(sale_id: int, delivery_address_id: int) -> Invoice:
    """Create a new invoice"""
    try:
        invoice = Invoice(
            sale_id=sale_id,
            delivery_address_id=delivery_address_id
        )
        db.session.add(invoice)
        db.session.commit()
        return invoice
    except SQLAlchemyError as e:
        db.session.rollback()
        raise RepoError(f"Error creating invoice: {str(e)}")

def update_invoice(invoice_id: int, data: dict) -> Optional[Invoice]:
    """Update invoice information"""
    try:
        invoice = get_by_id(invoice_id)
        if not invoice:
            return None
        
        invoice.delivery_address_id = data.get("delivery_address_id", invoice.delivery_address_id)
        invoice.updated_at = datetime.now()
        db.session.commit()
        return invoice
    except SQLAlchemyError as e:
        db.session.rollback()
        raise RepoError(f"Error updating invoice: {str(e)}")

def delete_invoice(invoice_id: int) -> Optional[Invoice]:
    """Delete an invoice"""
    try:
        invoice = get_by_id(invoice_id)
        if not invoice:
            return None
        
        db.session.delete(invoice)
        db.session.commit()
        return invoice
    except SQLAlchemyError as e:
        db.session.rollback()
        raise RepoError(f"Error deleting invoice: {str(e)}")

def get_invoices_by_date_range(start_date: datetime = None, end_date: datetime = None, user_id: int = None) -> List[Invoice]:
    """Get invoices filtered by date range and optionally by user"""
    query = Invoice.query
    
    if user_id:
        query = query.join(Invoice.sale).filter_by(user_id=user_id)
    
    if start_date:
        query = query.filter(Invoice.issue_date >= start_date)
    
    if end_date:
        query = query.filter(Invoice.issue_date <= end_date)
    
    return query.order_by(Invoice.issue_date.desc()).all()

def search_invoices_by_sale_total(min_total: float = None, max_total: float = None) -> List[Invoice]:
    """Search invoices by sale total amount"""
    query = Invoice.query.join(Invoice.sale)
    
    if min_total is not None:
        query = query.filter(Invoice.sale.has(total__gte=min_total))
    
    if max_total is not None:
        query = query.filter(Invoice.sale.has(total__lte=max_total))
    
    return query.order_by(Invoice.issue_date.desc()).all()

def get_invoice_with_full_details(invoice_id: int) -> Optional[Invoice]:
    """Get invoice with all related data (sale, products, delivery address)"""
    return Invoice.query.options(
        joinedload(Invoice.sale).joinedload(Sale.sale_products).joinedload(SaleProduct.product),
        joinedload(Invoice.delivery_address)
    ).filter_by(id=invoice_id).first()
