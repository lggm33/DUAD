# app/repos/cart_repo.py
from typing import Optional, List
from sqlalchemy.exc import SQLAlchemyError
from app.extensions import db
from app.models.cart import Cart
from app.models.cart_product import CartProduct
from app.utils.exceptions import RepoError
from datetime import datetime

def get_by_id(cart_id: int) -> Optional[Cart]:
    """Get cart by ID"""
    return db.session.get(Cart, cart_id)

def get_by_user_id(user_id: int) -> List[Cart]:
    """Get all carts for a user"""
    return Cart.query.filter_by(user_id=user_id).order_by(Cart.created_at.desc()).all()

def get_active_cart_by_user_id(user_id: int) -> Optional[Cart]:
    """Get the active cart for a user"""
    return Cart.query.filter_by(user_id=user_id, status="active").first()

def get_by_status(status: str) -> List[Cart]:
    """Get all carts by status"""
    return Cart.query.filter_by(status=status).order_by(Cart.created_at.desc()).all()

def create_cart(user_id: int, status: str = "active") -> Cart:
    """Create a new cart"""
    try:
        cart = Cart(
            user_id=user_id,
            status=status
        )
        db.session.add(cart)
        db.session.commit()
        return cart
    except SQLAlchemyError as e:
        db.session.rollback()
        raise RepoError(f"Error creating cart: {str(e)}")

def update_cart_status(cart_id: int, status: str) -> Optional[Cart]:
    """Update cart status"""
    try:
        cart = get_by_id(cart_id)
        if not cart:
            return None
        
        cart.status = status
        cart.updated_at = datetime.now()
        db.session.commit()
        return cart
    except SQLAlchemyError as e:
        db.session.rollback()
        raise RepoError(f"Error updating cart status: {str(e)}")

def delete_cart(cart_id: int) -> Optional[Cart]:
    """Delete a cart and all its products"""
    try:
        cart = get_by_id(cart_id)
        if not cart:
            return None
        
        db.session.delete(cart)
        db.session.commit()
        return cart
    except SQLAlchemyError as e:
        db.session.rollback()
        raise RepoError(f"Error deleting cart: {str(e)}")

def add_product_to_cart(cart_id: int, product_id: int, quantity: int = 1) -> Optional[CartProduct]:
    """Add a product to cart or update quantity if exists"""
    try:
        # Check if product already exists in cart
        cart_product = CartProduct.query.filter_by(
            cart_id=cart_id, 
            product_id=product_id
        ).first()
        
        if cart_product:
            # Update existing quantity
            cart_product.quantity += quantity
            cart_product.updated_at = datetime.now()
        else:
            # Create new cart product
            cart_product = CartProduct(
                cart_id=cart_id,
                product_id=product_id,
                quantity=quantity
            )
            db.session.add(cart_product)
        
        db.session.commit()
        return cart_product
    except SQLAlchemyError as e:
        db.session.rollback()
        raise RepoError(f"Error adding product to cart: {str(e)}")

def update_product_quantity(cart_id: int, product_id: int, quantity: int) -> Optional[CartProduct]:
    """Update product quantity in cart"""
    try:
        cart_product = CartProduct.query.filter_by(
            cart_id=cart_id, 
            product_id=product_id
        ).first()
        
        if not cart_product:
            return None
        
        cart_product.quantity = quantity
        cart_product.updated_at = datetime.now()
        db.session.commit()
        return cart_product
    except SQLAlchemyError as e:
        db.session.rollback()
        raise RepoError(f"Error updating product quantity: {str(e)}")

def remove_product_from_cart(cart_id: int, product_id: int) -> Optional[CartProduct]:
    """Remove a product from cart"""
    try:
        cart_product = CartProduct.query.filter_by(
            cart_id=cart_id, 
            product_id=product_id
        ).first()
        
        if not cart_product:
            return None
        
        db.session.delete(cart_product)
        db.session.commit()
        return cart_product
    except SQLAlchemyError as e:
        db.session.rollback()
        raise RepoError(f"Error removing product from cart: {str(e)}")

def get_cart_products(cart_id: int) -> List[CartProduct]:
    """Get all products in a cart"""
    return CartProduct.query.filter_by(cart_id=cart_id).all()

def clear_cart(cart_id: int) -> bool:
    """Remove all products from cart"""
    try:
        CartProduct.query.filter_by(cart_id=cart_id).delete()
        db.session.commit()
        return True
    except SQLAlchemyError as e:
        db.session.rollback()
        raise RepoError(f"Error clearing cart: {str(e)}")
