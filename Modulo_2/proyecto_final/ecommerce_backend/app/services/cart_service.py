# app/services/cart_service.py
from typing import Optional, List, Dict, Any
from decimal import Decimal
from app.extensions import db
import app.repos.cart_repo as cart_repo
import app.repos.product_repo as product_repo
from app.models.cart import Cart
from app.models.cart_product import CartProduct
from app.models.product import Product
from app.utils.exceptions import (
    AppError,
    RepoError,
    ProductNotFoundError,
    ForbiddenError,
    CartNotFoundError,
    InsufficientStockError,
    CartError,
    EmptyCartError,
    CartNotActiveError
)

def get_or_create_active_cart(user_id: int) -> Cart:
    """Get user's active cart or create a new one if none exists"""
    try:
        # Try to get existing active cart
        active_cart = cart_repo.get_active_cart_by_user_id(user_id)
        
        if not active_cart:
            # Create new active cart
            active_cart = cart_repo.create_cart(user_id, status="active")
        
        return active_cart
    except RepoError as e:
        raise CartError(f"Error managing cart: {str(e)}")

def get_cart_by_id(cart_id: int, user_id: int = None) -> Cart:
    """Get cart by ID, optionally validating ownership"""
    cart = cart_repo.get_by_id(cart_id)
    if not cart:
        raise CartNotFoundError("Cart not found")
    
    # Validate ownership if user_id provided
    if user_id and cart.user_id != user_id:
        raise ForbiddenError("Access denied: Cart belongs to another user")
    
    return cart

def get_user_carts(user_id: int, status: str = None) -> List[Cart]:
    """Get all carts for a user, optionally filtered by status"""
    try:
        if status:
            # Get carts by status for user
            all_carts = cart_repo.get_by_status(status)
            return [cart for cart in all_carts if cart.user_id == user_id]
        else:
            return cart_repo.get_by_user_id(user_id)
    except RepoError as e:
        raise CartError(f"Error retrieving carts: {str(e)}")

def add_product_to_cart(user_id: int, product_id: int, quantity: int = 1) -> CartProduct:
    """Add a product to user's active cart with stock validation"""
    try:
        # Get or create active cart
        cart = get_or_create_active_cart(user_id)
        
        # Validate product exists and has sufficient stock
        product = product_repo.get_by_id(product_id)
        if not product:
            raise ProductNotFoundError("Product not found")
        
        # Check if product already exists in cart
        existing_cart_product = None
        for cp in cart.cart_products:
            if cp.product_id == product_id:
                existing_cart_product = cp
                break
        
        # Calculate total quantity needed
        current_quantity = existing_cart_product.quantity if existing_cart_product else 0
        total_quantity = current_quantity + quantity
        
        # Validate stock availability
        if product.stock < total_quantity:
            raise InsufficientStockError(
                f"Insufficient stock. Available: {product.stock}, Requested: {total_quantity}"
            )
        
        # Add or update product in cart
        cart_product = cart_repo.add_product_to_cart(cart.id, product_id, quantity)
        
        return cart_product
    except RepoError as e:
        raise CartError(f"Error adding product to cart: {str(e)}")

def update_product_quantity(user_id: int, product_id: int, quantity: int) -> Optional[CartProduct]:
    """Update product quantity in user's active cart"""
    try:
        # Get active cart
        cart = get_or_create_active_cart(user_id)
        
        # If quantity is 0, remove product
        if quantity == 0:
            return remove_product_from_cart(user_id, product_id)
        
        # Validate product exists and has sufficient stock
        product = product_repo.get_by_id(product_id)
        if not product:
            raise ProductNotFoundError("Product not found")
        
        if product.stock < quantity:
            raise InsufficientStockError(
                f"Insufficient stock. Available: {product.stock}, Requested: {quantity}"
            )
        
        # Update quantity
        cart_product = cart_repo.update_product_quantity(cart.id, product_id, quantity)
        if not cart_product:
            raise CartError("Product not found in cart")
        
        return cart_product
    except RepoError as e:
        raise CartError(f"Error updating product quantity: {str(e)}")

def remove_product_from_cart(user_id: int, product_id: int) -> Optional[CartProduct]:
    """Remove a product from user's active cart"""
    try:
        cart = get_or_create_active_cart(user_id)
        cart_product = cart_repo.remove_product_from_cart(cart.id, product_id)
        
        if not cart_product:
            raise CartError("Product not found in cart")
        
        return cart_product
    except RepoError as e:
        raise CartError(f"Error removing product from cart: {str(e)}")

def clear_cart(user_id: int) -> bool:
    """Remove all products from user's active cart"""
    try:
        cart = get_or_create_active_cart(user_id)
        return cart_repo.clear_cart(cart.id)
    except RepoError as e:
        raise CartError(f"Error clearing cart: {str(e)}")

def calculate_cart_total(cart_id: int) -> Dict[str, Any]:
    """Calculate cart totals and summary information"""
    try:
        cart = cart_repo.get_by_id(cart_id)
        if not cart:
            raise CartNotFoundError("Cart not found")
        
        cart_products = cart_repo.get_cart_products(cart_id)
        
        subtotal = Decimal('0.00')
        total_items = 0
        product_count = len(cart_products)
        
        items_detail = []
        
        for cart_product in cart_products:
            product = product_repo.get_by_id(cart_product.product_id)
            if product:
                item_subtotal = product.price * cart_product.quantity
                subtotal += item_subtotal
                total_items += cart_product.quantity
                
                items_detail.append({
                    'product_id': product.id,
                    'product_name': product.name,
                    'price': float(product.price),
                    'quantity': cart_product.quantity,
                    'subtotal': float(item_subtotal)
                })
        
        return {
            'cart_id': cart_id,
            'subtotal': float(subtotal),
            'total_items': total_items,
            'product_count': product_count,
            'items': items_detail
        }
    except RepoError as e:
        raise CartError(f"Error calculating cart total: {str(e)}")

def update_cart_status(cart_id: int, status: str, user_id: int = None) -> Cart:
    """Update cart status with optional ownership validation"""
    try:
        # Validate ownership if user_id provided
        if user_id:
            cart = get_cart_by_id(cart_id, user_id)
        
        # Valid statuses from schema
        valid_statuses = ["active", "abandoned", "converted", "expired"]
        if status not in valid_statuses:
            raise CartError(f"Invalid status. Must be one of: {valid_statuses}")
        
        updated_cart = cart_repo.update_cart_status(cart_id, status)
        if not updated_cart:
            raise CartNotFoundError("Cart not found")
        
        return updated_cart
    except RepoError as e:
        raise CartError(f"Error updating cart status: {str(e)}")

def validate_cart_for_checkout(cart_id: int) -> Dict[str, Any]:
    """Validate cart is ready for checkout and return validation results"""
    try:
        cart = cart_repo.get_by_id(cart_id)
        if not cart:
            raise CartNotFoundError("Cart not found")
        
        if cart.status != "active":
            raise CartNotActiveError("Cart is not active")
        
        cart_products = cart_repo.get_cart_products(cart_id)
        if not cart_products:
            raise EmptyCartError("Cart is empty")
        
        validation_results = {
            'valid': True,
            'errors': [],
            'warnings': [],
            'total_amount': Decimal('0.00'),
            'items': []
        }
        
        for cart_product in cart_products:
            product = product_repo.get_by_id(cart_product.product_id)
            
            item_result = {
                'product_id': cart_product.product_id,
                'requested_quantity': cart_product.quantity,
                'available_stock': product.stock if product else 0,
                'valid': True,
                'issues': []
            }
            
            if not product:
                item_result['valid'] = False
                item_result['issues'].append('Product no longer exists')
                validation_results['errors'].append(f"Product {cart_product.product_id} no longer exists")
                validation_results['valid'] = False
            else:
                # Check stock availability
                if product.stock < cart_product.quantity:
                    item_result['valid'] = False
                    item_result['issues'].append(f'Insufficient stock (available: {product.stock})')
                    validation_results['errors'].append(
                        f"Insufficient stock for {product.name}. Available: {product.stock}, Requested: {cart_product.quantity}"
                    )
                    validation_results['valid'] = False
                elif product.stock < cart_product.quantity * 2:  # Warning if stock is low
                    validation_results['warnings'].append(f"Low stock for {product.name}")
                
                # Calculate total
                if item_result['valid']:
                    validation_results['total_amount'] += product.price * cart_product.quantity
            
            validation_results['items'].append(item_result)
        
        validation_results['total_amount'] = float(validation_results['total_amount'])
        return validation_results
        
    except RepoError as e:
        raise CartError(f"Error validating cart: {str(e)}")

def abandon_old_carts(days_old: int = 7) -> int:
    """Mark old active carts as abandoned (utility function for cleanup)"""
    try:
        from datetime import datetime, timedelta
        
        # This would need to be implemented in the repository
        # For now, return 0 as placeholder
        # TODO: Implement in cart_repo
        return 0
    except RepoError as e:
        raise CartError(f"Error abandoning old carts: {str(e)}")
