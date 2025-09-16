# app/repos/sale_repo.py
from typing import Optional, List
from decimal import Decimal
from sqlalchemy.exc import SQLAlchemyError
from app.extensions import db
from app.models.sale import Sale
from app.models.sale_product import SaleProduct
from app.utils.exceptions import RepoError
from datetime import datetime

def get_by_id(sale_id: int) -> Optional[Sale]:
    """Get sale by ID"""
    return db.session.get(Sale, sale_id)

def get_by_user_id(user_id: int) -> List[Sale]:
    """Get all sales for a user"""
    return Sale.query.filter_by(user_id=user_id).order_by(Sale.sale_date.desc()).all()

def get_all() -> List[Sale]:
    """Get all sales"""
    return Sale.query.order_by(Sale.sale_date.desc()).all()

def create_sale(user_id: int, total: Decimal) -> Sale:
    """Create a new sale"""
    try:
        sale = Sale(
            user_id=user_id,
            total=total
        )
        db.session.add(sale)
        db.session.commit()
        return sale
    except SQLAlchemyError as e:
        db.session.rollback()
        raise RepoError(f"Error creating sale: {str(e)}")

def update_sale(sale_id: int, data: dict) -> Optional[Sale]:
    """Update sale information"""
    try:
        sale = get_by_id(sale_id)
        if not sale:
            return None
        
        sale.total = data.get("total", sale.total)
        sale.updated_at = datetime.now()
        db.session.commit()
        return sale
    except SQLAlchemyError as e:
        db.session.rollback()
        raise RepoError(f"Error updating sale: {str(e)}")

def delete_sale(sale_id: int) -> Optional[Sale]:
    """Delete a sale and all its products"""
    try:
        sale = get_by_id(sale_id)
        if not sale:
            return None
        
        db.session.delete(sale)
        db.session.commit()
        return sale
    except SQLAlchemyError as e:
        db.session.rollback()
        raise RepoError(f"Error deleting sale: {str(e)}")

def add_product_to_sale(sale_id: int, product_id: int, quantity: int, price: Decimal) -> SaleProduct:
    """Add a product to sale"""
    try:
        sale_product = SaleProduct(
            sale_id=sale_id,
            product_id=product_id,
            quantity=quantity,
            price=price
        )
        db.session.add(sale_product)
        db.session.commit()
        return sale_product
    except SQLAlchemyError as e:
        db.session.rollback()
        raise RepoError(f"Error adding product to sale: {str(e)}")

def update_sale_product(sale_id: int, product_id: int, data: dict) -> Optional[SaleProduct]:
    """Update product in sale"""
    try:
        sale_product = SaleProduct.query.filter_by(
            sale_id=sale_id, 
            product_id=product_id
        ).first()
        
        if not sale_product:
            return None
        
        sale_product.quantity = data.get("quantity", sale_product.quantity)
        sale_product.price = data.get("price", sale_product.price)
        sale_product.updated_at = datetime.now()
        db.session.commit()
        return sale_product
    except SQLAlchemyError as e:
        db.session.rollback()
        raise RepoError(f"Error updating sale product: {str(e)}")

def remove_product_from_sale(sale_id: int, product_id: int) -> Optional[SaleProduct]:
    """Remove a product from sale"""
    try:
        sale_product = SaleProduct.query.filter_by(
            sale_id=sale_id, 
            product_id=product_id
        ).first()
        
        if not sale_product:
            return None
        
        db.session.delete(sale_product)
        db.session.commit()
        return sale_product
    except SQLAlchemyError as e:
        db.session.rollback()
        raise RepoError(f"Error removing product from sale: {str(e)}")

def get_sale_products(sale_id: int) -> List[SaleProduct]:
    """Get all products in a sale"""
    return SaleProduct.query.filter_by(sale_id=sale_id).all()

def get_sales_by_date_range(user_id: int = None, start_date: datetime = None, end_date: datetime = None) -> List[Sale]:
    """Get sales filtered by date range and optionally by user"""
    query = Sale.query
    
    if user_id:
        query = query.filter_by(user_id=user_id)
    
    if start_date:
        query = query.filter(Sale.sale_date >= start_date)
    
    if end_date:
        query = query.filter(Sale.sale_date <= end_date)
    
    return query.order_by(Sale.sale_date.desc()).all()

def get_total_sales_amount(user_id: int = None) -> Decimal:
    """Get total sales amount, optionally filtered by user"""
    query = db.session.query(db.func.sum(Sale.total))
    
    if user_id:
        query = query.filter(Sale.user_id == user_id)
    
    result = query.scalar()
    return result if result is not None else Decimal('0.00')
