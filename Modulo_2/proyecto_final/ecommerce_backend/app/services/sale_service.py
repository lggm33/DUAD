# app/services/sale_service.py
from typing import Optional, List, Dict, Any
from decimal import Decimal
from datetime import datetime
from app.extensions import db
import app.repos.sale_repo as sale_repo
import app.repos.cart_repo as cart_repo
import app.repos.product_repo as product_repo
import app.repos.delivery_address_repo as delivery_address_repo
import app.services.cart_service as cart_service
from app.models.sale import Sale
from app.models.sale_product import SaleProduct
from app.models.cart import Cart
from app.models.product import Product
from app.utils.exceptions import (
    AppError,
    RepoError,
    SaleNotFoundError,
    CartNotFoundError,
    ProductNotFoundError,
    ForbiddenError,
    EmptyCartError,
    CartNotActiveError,
    InsufficientStockError,
    SaleError,
    DeliveryAddressNotFoundError
)

def get_sale_by_id(sale_id: int, user_id: int = None) -> Sale:
    """Get sale by ID with optional ownership validation"""
    sale = sale_repo.get_by_id(sale_id)
    if not sale:
        raise SaleNotFoundError("Sale not found")
    
    # Validate ownership if user_id provided
    if user_id and sale.user_id != user_id:
        raise ForbiddenError("Access denied: Sale belongs to another user")
    
    return sale

def get_user_sales(user_id: int, start_date: datetime = None, end_date: datetime = None) -> List[Sale]:
    """Get all sales for a user with optional date filtering"""
    try:
        if start_date or end_date:
            return sale_repo.get_sales_by_date_range(user_id, start_date, end_date)
        else:
            return sale_repo.get_by_user_id(user_id)
    except RepoError as e:
        raise SaleError(f"Error retrieving user sales: {str(e)}")

def get_all_sales(user_id: int = None, start_date: datetime = None, end_date: datetime = None) -> List[Sale]:
    """Get all sales with optional filtering (admin function)"""
    try:
        if start_date or end_date or user_id:
            return sale_repo.get_sales_by_date_range(user_id, start_date, end_date)
        else:
            return sale_repo.get_all()
    except RepoError as e:
        raise SaleError(f"Error retrieving sales: {str(e)}")

def create_sale_from_cart(user_id: int, cart_id: int, delivery_address_id: int, 
                         payment_method: str = None, payment_reference: str = None) -> Sale:
    """
    Create a sale from user's cart (checkout process)
    
    This is the main checkout function that:
    1. Validates cart ownership and status
    2. Validates delivery address
    3. Validates cart contents and stock
    4. Creates sale with products
    5. Updates product stock
    6. Converts cart to 'converted' status
    """
    try:
        # Validate cart ownership and get cart
        cart = cart_service.get_cart_by_id(cart_id, user_id)
        
        if cart.status != "active":
            raise CartNotActiveError("Cart is not active")
        
        # Validate delivery address ownership
        delivery_address = delivery_address_repo.get_delivery_address_by_id(delivery_address_id)
        if not delivery_address:
            raise DeliveryAddressNotFoundError("Delivery address not found")
        
        if delivery_address.user_id != user_id:
            raise ForbiddenError("Access denied: Delivery address belongs to another user")
        
        # Validate cart for checkout
        validation_result = cart_service.validate_cart_for_checkout(cart_id)
        if not validation_result['valid']:
            raise SaleError(f"Cart validation failed: {', '.join(validation_result['errors'])}")
        
        # Get cart products
        cart_products = cart_repo.get_cart_products(cart_id)
        if not cart_products:
            raise EmptyCartError("Cart is empty")
        
        # Calculate total and prepare sale products
        total_amount = Decimal('0.00')
        sale_products_data = []
        
        try:
            # Validate stock and prepare sale data
            for cart_product in cart_products:
                product = product_repo.get_by_id(cart_product.product_id)
                if not product:
                    raise ProductNotFoundError(f"Product {cart_product.product_id} not found")
                
                # Final stock check
                if product.stock < cart_product.quantity:
                    raise InsufficientStockError(
                        f"Insufficient stock for {product.name}. Available: {product.stock}, Requested: {cart_product.quantity}"
                    )
                
                # Calculate item total
                item_total = product.price * cart_product.quantity
                total_amount += item_total
                
                sale_products_data.append({
                    'product_id': cart_product.product_id,
                    'quantity': cart_product.quantity,
                    'price': product.price  # Store current price at time of sale
                })
            
            # Create the sale
            sale = sale_repo.create_sale(user_id, total_amount)
            
            # Add products to sale and update stock
            for product_data in sale_products_data:
                # Add product to sale
                sale_repo.add_product_to_sale(
                    sale.id,
                    product_data['product_id'],
                    product_data['quantity'],
                    product_data['price']
                )
                
                # Update product stock
                product = product_repo.get_by_id(product_data['product_id'])
                new_stock = product.stock - product_data['quantity']
                product_repo.update_product(product_data['product_id'], {'stock': new_stock})
            
            # Mark cart as converted
            cart_service.update_cart_status(cart_id, "converted", user_id)
            
            return sale
            
        except Exception as e:
            db.session.rollback()
            raise SaleError(f"Error creating sale: {str(e)}")
        
    except RepoError as e:
        raise SaleError(f"Repository error during checkout: {str(e)}")

def update_sale(sale_id: int, data: dict, user_id: int = None) -> Sale:
    """Update sale information (admin function mainly)"""
    try:
        # Validate ownership if user_id provided
        if user_id:
            get_sale_by_id(sale_id, user_id)
        
        updated_sale = sale_repo.update_sale(sale_id, data)
        if not updated_sale:
            raise SaleNotFoundError("Sale not found")
        
        return updated_sale
    except RepoError as e:
        raise SaleError(f"Error updating sale: {str(e)}")

def get_sale_summary(sale_id: int, user_id: int = None) -> Dict[str, Any]:
    """Get detailed sale summary with products and calculations"""
    try:
        sale = get_sale_by_id(sale_id, user_id)
        sale_products = sale_repo.get_sale_products(sale_id)
        
        # Calculate summary information
        total_items = sum(sp.quantity for sp in sale_products)
        product_count = len(sale_products)
        
        products_detail = []
        for sale_product in sale_products:
            product = product_repo.get_by_id(sale_product.product_id)
            subtotal = sale_product.price * sale_product.quantity
            
            product_detail = {
                'product_id': sale_product.product_id,
                'product_name': product.name if product else 'Product not found',
                'quantity': sale_product.quantity,
                'price_at_sale': float(sale_product.price),
                'subtotal': float(subtotal),
                'current_price': float(product.price) if product else None,
                'price_difference': float(product.price - sale_product.price) if product else None
            }
            products_detail.append(product_detail)
        
        return {
            'sale_id': sale.id,
            'user_id': sale.user_id,
            'sale_date': sale.sale_date,
            'total': float(sale.total),
            'total_items': total_items,
            'product_count': product_count,
            'products': products_detail
        }
    except RepoError as e:
        raise SaleError(f"Error getting sale summary: {str(e)}")

def get_user_sales_summary(user_id: int) -> Dict[str, Any]:
    """Get summary statistics for user's sales"""
    try:
        user_sales = sale_repo.get_by_user_id(user_id)
        
        if not user_sales:
            return {
                'total_sales': 0,
                'total_amount': 0.0,
                'average_order_value': 0.0,
                'first_purchase': None,
                'last_purchase': None
            }
        
        total_amount = sum(float(sale.total) for sale in user_sales)
        total_sales = len(user_sales)
        average_order_value = total_amount / total_sales if total_sales > 0 else 0.0
        
        # Sort by date to get first and last
        sorted_sales = sorted(user_sales, key=lambda x: x.sale_date)
        
        return {
            'total_sales': total_sales,
            'total_amount': total_amount,
            'average_order_value': average_order_value,
            'first_purchase': sorted_sales[0].sale_date,
            'last_purchase': sorted_sales[-1].sale_date
        }
    except RepoError as e:
        raise SaleError(f"Error getting user sales summary: {str(e)}")

def get_sales_analytics(start_date: datetime = None, end_date: datetime = None) -> Dict[str, Any]:
    """Get sales analytics for admin dashboard"""
    try:
        # Get sales in date range
        sales = sale_repo.get_sales_by_date_range(None, start_date, end_date)
        
        if not sales:
            return {
                'total_sales': 0,
                'total_revenue': 0.0,
                'average_order_value': 0.0,
                'total_customers': 0,
                'sales_by_day': {},
                'top_customers': []
            }
        
        # Basic metrics
        total_sales = len(sales)
        total_revenue = sum(float(sale.total) for sale in sales)
        average_order_value = total_revenue / total_sales if total_sales > 0 else 0.0
        
        # Unique customers
        unique_customers = len(set(sale.user_id for sale in sales))
        
        # Sales by day
        sales_by_day = {}
        for sale in sales:
            day = sale.sale_date.date().isoformat()
            if day not in sales_by_day:
                sales_by_day[day] = {'count': 0, 'revenue': 0.0}
            sales_by_day[day]['count'] += 1
            sales_by_day[day]['revenue'] += float(sale.total)
        
        # Top customers by total spent
        customer_totals = {}
        for sale in sales:
            if sale.user_id not in customer_totals:
                customer_totals[sale.user_id] = {'sales_count': 0, 'total_spent': 0.0}
            customer_totals[sale.user_id]['sales_count'] += 1
            customer_totals[sale.user_id]['total_spent'] += float(sale.total)
        
        # Sort customers by total spent
        top_customers = sorted(
            customer_totals.items(),
            key=lambda x: x[1]['total_spent'],
            reverse=True
        )[:10]  # Top 10 customers
        
        return {
            'total_sales': total_sales,
            'total_revenue': total_revenue,
            'average_order_value': average_order_value,
            'total_customers': unique_customers,
            'sales_by_day': sales_by_day,
            'top_customers': [
                {
                    'user_id': user_id,
                    'sales_count': data['sales_count'],
                    'total_spent': data['total_spent']
                }
                for user_id, data in top_customers
            ]
        }
    except RepoError as e:
        raise SaleError(f"Error getting sales analytics: {str(e)}")

def delete_sale(sale_id: int) -> Sale:
    """Delete a sale (admin function only - should be used carefully)"""
    try:
        deleted_sale = sale_repo.delete_sale(sale_id)
        if not deleted_sale:
            raise SaleNotFoundError("Sale not found")
        return deleted_sale
    except RepoError as e:
        raise SaleError(f"Error deleting sale: {str(e)}")
