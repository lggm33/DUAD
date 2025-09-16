# app/services/invoice_service.py
from typing import Optional, List, Dict, Any
from datetime import datetime
from app.extensions import db
import app.repos.invoice_repo as invoice_repo
import app.repos.sale_repo as sale_repo
import app.repos.delivery_address_repo as delivery_address_repo
from app.models.invoice import Invoice
from app.models.sale import Sale
from app.utils.exceptions import (
    AppError,
    RepoError,
    InvoiceNotFoundError,
    SaleNotFoundError,
    DeliveryAddressNotFoundError,
    ForbiddenError,
    InvoiceError
)

def get_invoice_by_id(invoice_id: int, user_id: int = None) -> Invoice:
    """Get invoice by ID with optional ownership validation"""
    invoice = invoice_repo.get_by_id(invoice_id)
    if not invoice:
        raise InvoiceNotFoundError("Invoice not found")
    
    # Validate ownership if user_id provided
    if user_id and invoice.sale.user_id != user_id:
        raise ForbiddenError("Access denied: Invoice belongs to another user")
    
    return invoice

def get_invoice_with_details(invoice_id: int, user_id: int = None) -> Invoice:
    """Get invoice with full details including sale products and delivery address"""
    invoice = invoice_repo.get_invoice_with_full_details(invoice_id)
    if not invoice:
        raise InvoiceNotFoundError("Invoice not found")
    
    # Validate ownership if user_id provided
    if user_id and invoice.sale.user_id != user_id:
        raise ForbiddenError("Access denied: Invoice belongs to another user")
    
    return invoice

def get_user_invoices(user_id: int, start_date: datetime = None, end_date: datetime = None) -> List[Invoice]:
    """Get all invoices for a user with optional date filtering"""
    try:
        if start_date or end_date:
            return invoice_repo.get_invoices_by_date_range(start_date, end_date, user_id)
        else:
            return invoice_repo.get_by_user_id(user_id)
    except RepoError as e:
        raise InvoiceError(f"Error retrieving user invoices: {str(e)}")

def get_invoices_for_sale(sale_id: int, user_id: int = None) -> List[Invoice]:
    """Get all invoices for a specific sale"""
    # Validate sale exists and ownership if user_id provided
    sale = sale_repo.get_by_id(sale_id)
    if not sale:
        raise SaleNotFoundError("Sale not found")
    
    if user_id and sale.user_id != user_id:
        raise ForbiddenError("Access denied: Sale belongs to another user")
    
    try:
        return invoice_repo.get_by_sale_id(sale_id)
    except RepoError as e:
        raise InvoiceError(f"Error retrieving sale invoices: {str(e)}")

def create_invoice(sale_id: int, delivery_address_id: int, user_id: int = None) -> Invoice:
    """
    Create a new invoice for a sale
    
    Args:
        sale_id: ID of the sale to invoice
        delivery_address_id: ID of the delivery address
        user_id: Optional user ID for ownership validation
    
    Returns:
        Created invoice
    
    Raises:
        SaleNotFoundError: If sale doesn't exist
        DeliveryAddressNotFoundError: If delivery address doesn't exist
        ForbiddenError: If user doesn't own the sale or delivery address
        InvoiceError: If invoice creation fails
    """
    # Validate sale exists
    sale = sale_repo.get_by_id(sale_id)
    if not sale:
        raise SaleNotFoundError("Sale not found")
    
    # Validate ownership if user_id provided
    if user_id and sale.user_id != user_id:
        raise ForbiddenError("Access denied: Sale belongs to another user")
    
    # Validate delivery address exists
    delivery_address = delivery_address_repo.get_delivery_address_by_id(delivery_address_id)
    if not delivery_address:
        raise DeliveryAddressNotFoundError("Delivery address not found")
    
    # Validate delivery address ownership if user_id provided
    if user_id and delivery_address.user_id != user_id:
        raise ForbiddenError("Access denied: Delivery address belongs to another user")
    
    try:
        return invoice_repo.create_invoice(sale_id, delivery_address_id)
    except RepoError as e:
        raise InvoiceError(f"Error creating invoice: {str(e)}")

def update_invoice(invoice_id: int, data: dict, user_id: int = None) -> Invoice:
    """Update invoice information"""
    # Validate invoice exists and ownership
    invoice = get_invoice_by_id(invoice_id, user_id)
    
    # If updating delivery address, validate it exists and ownership
    if 'delivery_address_id' in data:
        delivery_address = delivery_address_repo.get_delivery_address_by_id(data['delivery_address_id'])
        if not delivery_address:
            raise DeliveryAddressNotFoundError("Delivery address not found")
        
        if user_id and delivery_address.user_id != user_id:
            raise ForbiddenError("Access denied: Delivery address belongs to another user")
    
    try:
        return invoice_repo.update_invoice(invoice_id, data)
    except RepoError as e:
        raise InvoiceError(f"Error updating invoice: {str(e)}")

def delete_invoice(invoice_id: int, user_id: int = None) -> Invoice:
    """Delete an invoice"""
    # Validate invoice exists and ownership
    invoice = get_invoice_by_id(invoice_id, user_id)
    
    try:
        return invoice_repo.delete_invoice(invoice_id)
    except RepoError as e:
        raise InvoiceError(f"Error deleting invoice: {str(e)}")

def get_all_invoices(start_date: datetime = None, end_date: datetime = None, 
                    user_id: int = None) -> List[Invoice]:
    """Get all invoices with optional filtering (Admin only typically)"""
    try:
        return invoice_repo.get_invoices_by_date_range(start_date, end_date, user_id)
    except RepoError as e:
        raise InvoiceError(f"Error retrieving invoices: {str(e)}")

def search_invoices(min_total: float = None, max_total: float = None) -> List[Invoice]:
    """Search invoices by sale total amount (Admin only typically)"""
    try:
        return invoice_repo.search_invoices_by_sale_total(min_total, max_total)
    except RepoError as e:
        raise InvoiceError(f"Error searching invoices: {str(e)}")

def generate_invoice_summary(invoice_id: int, user_id: int = None) -> Dict[str, Any]:
    """Generate a comprehensive invoice summary with all details"""
    invoice = get_invoice_with_details(invoice_id, user_id)
    
    # Calculate summary information
    sale = invoice.sale
    sale_products = sale.sale_products
    
    # Product details
    products_summary = []
    total_items = 0
    
    for sale_product in sale_products:
        product_info = {
            'product_id': sale_product.product_id,
            'product_name': sale_product.product.name if sale_product.product else 'Unknown Product',
            'quantity': sale_product.quantity,
            'unit_price': float(sale_product.price),
            'total_price': float(sale_product.price * sale_product.quantity)
        }
        products_summary.append(product_info)
        total_items += sale_product.quantity
    
    # Customer information
    customer_info = {
        'user_id': sale.user_id,
        'name': sale.user.name if sale.user else 'Unknown Customer',
        'email': sale.user.email if sale.user else 'Unknown Email'
    }
    
    # Delivery information
    delivery_info = {
        'address_id': invoice.delivery_address_id,
        'address': invoice.delivery_address.address if invoice.delivery_address else 'Unknown Address',
        'city': invoice.delivery_address.city if invoice.delivery_address else 'Unknown City',
        'country': invoice.delivery_address.country if invoice.delivery_address else 'Unknown Country',
        'postal_code': invoice.delivery_address.postal_code if invoice.delivery_address else 'Unknown Postal Code'
    }
    
    return {
        'invoice_number': f"INV-{invoice.id:06d}",
        'invoice_id': invoice.id,
        'sale_id': invoice.sale_id,
        'issue_date': invoice.issue_date.isoformat(),
        'customer': customer_info,
        'delivery_address': delivery_info,
        'products': products_summary,
        'summary': {
            'total_products': len(products_summary),
            'total_items': total_items,
            'subtotal': float(sale.total),
            'total_amount': float(sale.total)
        }
    }

def get_user_invoices_summary(user_id: int) -> Dict[str, Any]:
    """Get summary statistics for user's invoices"""
    try:
        invoices = invoice_repo.get_by_user_id(user_id)
        
        if not invoices:
            return {
                'total_invoices': 0,
                'total_amount': 0.0,
                'date_range': None
            }
        
        total_amount = sum(float(invoice.sale.total) for invoice in invoices)
        oldest_invoice = min(invoices, key=lambda x: x.issue_date)
        newest_invoice = max(invoices, key=lambda x: x.issue_date)
        
        return {
            'total_invoices': len(invoices),
            'total_amount': total_amount,
            'average_amount': total_amount / len(invoices),
            'date_range': {
                'from': oldest_invoice.issue_date.isoformat(),
                'to': newest_invoice.issue_date.isoformat()
            }
        }
    except RepoError as e:
        raise InvoiceError(f"Error generating user invoices summary: {str(e)}")

def get_invoices_analytics(start_date: datetime = None, end_date: datetime = None) -> Dict[str, Any]:
    """Get analytics for invoices in a date range (Admin only typically)"""
    try:
        invoices = invoice_repo.get_invoices_by_date_range(start_date, end_date)
        
        if not invoices:
            return {
                'total_invoices': 0,
                'total_revenue': 0.0,
                'analytics': {}
            }
        
        total_revenue = sum(float(invoice.sale.total) for invoice in invoices)
        unique_customers = len(set(invoice.sale.user_id for invoice in invoices))
        
        # Monthly breakdown if date range spans multiple months
        monthly_data = {}
        for invoice in invoices:
            month_key = invoice.issue_date.strftime('%Y-%m')
            if month_key not in monthly_data:
                monthly_data[month_key] = {'count': 0, 'revenue': 0.0}
            monthly_data[month_key]['count'] += 1
            monthly_data[month_key]['revenue'] += float(invoice.sale.total)
        
        return {
            'total_invoices': len(invoices),
            'total_revenue': total_revenue,
            'unique_customers': unique_customers,
            'average_invoice_amount': total_revenue / len(invoices),
            'monthly_breakdown': monthly_data,
            'date_range': {
                'from': start_date.isoformat() if start_date else None,
                'to': end_date.isoformat() if end_date else None
            }
        }
    except RepoError as e:
        raise InvoiceError(f"Error generating invoices analytics: {str(e)}")
