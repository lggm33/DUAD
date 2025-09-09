from flask import Blueprint, jsonify, request
from datetime import datetime
from app.schemas.cart import CartCreateSchema, CartReadSchema, CartUpdateSchema, CartListSchema
from app.schemas.cart_product import AddToCartSchema, UpdateCartProductSchema, CartProductReadSchema
from app.schemas.sale import SaleCreateSchema, SaleReadSchema, SaleUpdateSchema, SaleListSchema, SaleFromCartSchema
from app.schemas.invoice import InvoiceCreateSchema, InvoiceReadSchema, InvoiceUpdateSchema, InvoiceListSchema, InvoiceDetailSchema
from app.services import cart_service, sale_service, invoice_service
from app.utils.decorators import handle_errors
from app.utils.cache_decorators import cached_response
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.security.decorators import cart_owner_required, customer_only, admin_only, roles_required

bp = Blueprint("sales", __name__, url_prefix="/sales")

# ===== CART ENDPOINTS =====

@bp.get("/cart")
@jwt_required()
@handle_errors("getting active cart")
def get_active_cart():
    """
    Get or create user's active cart
    """
    user_id = int(get_jwt_identity())
    cart = cart_service.get_or_create_active_cart(user_id)
    return jsonify(CartReadSchema().dump(cart)), 200

@bp.get("/cart/<int:cart_id>")
@jwt_required()
@cart_owner_required()
@handle_errors("getting cart")
def get_cart(cart_id: int):
    """
    Get specific cart by ID
    
    Authentication: JWT token required (customer only)
    Authorization: User can only access their own carts
    """
    from flask import g
    cart = g.cart  # Cart is already validated and loaded by the decorator
    return jsonify(CartReadSchema().dump(cart)), 200

@bp.get("/carts")
@jwt_required()
@handle_errors("getting user carts")
def get_user_carts():
    """
    Get all carts for the current user
    """
    user_id = int(get_jwt_identity())
    status = request.args.get('status')  # Optional filter by status
    carts = cart_service.get_user_carts(user_id, status)
    return jsonify([CartListSchema().dump(cart) for cart in carts]), 200

@bp.post("/cart/add")
@jwt_required()
@customer_only
@handle_errors("adding product to cart", handle_validation=True)
def add_to_cart():
    """
    Add a product to user's active cart
    
    Authentication: JWT token with customer role required
    """
    user_id = int(get_jwt_identity())
    data = AddToCartSchema().load(request.get_json() or {})
    
    cart_product = cart_service.add_product_to_cart(
        user_id=user_id,
        product_id=data['product_id'],
        quantity=data['quantity']
    )
    
    return jsonify(CartProductReadSchema().dump(cart_product)), 201

@bp.put("/cart/product/<int:product_id>")
@jwt_required()
@customer_only
@handle_errors("updating cart product")
def update_cart_product(product_id: int):
    """
    Update product quantity in user's active cart
    
    Authentication: JWT token with customer role required
    """
    user_id = int(get_jwt_identity())
    data = UpdateCartProductSchema().load(request.get_json() or {})
    
    cart_product = cart_service.update_product_quantity(
        user_id=user_id,
        product_id=product_id,
        quantity=data['quantity']
    )
    
    if cart_product:
        return jsonify(CartProductReadSchema().dump(cart_product)), 200
    else:
        return jsonify({"message": "Product removed from cart"}), 200

@bp.delete("/cart/product/<int:product_id>")
@jwt_required()
@customer_only
@handle_errors("removing product from cart")
def remove_from_cart(product_id: int):
    """
    Remove a product from user's active cart
    
    Authentication: JWT token with customer role required
    """
    user_id = int(get_jwt_identity())
    cart_service.remove_product_from_cart(user_id, product_id)
    return jsonify({"message": "Product removed from cart"}), 200

@bp.delete("/cart/clear")
@jwt_required()
@customer_only
@handle_errors("clearing cart")
def clear_cart():
    """
    Clear all products from user's active cart
    
    Authentication: JWT token with customer role required
    """
    user_id = int(get_jwt_identity())
    cart_service.clear_cart(user_id)
    return jsonify({"message": "Cart cleared successfully"}), 200

@bp.get("/cart/total")
@jwt_required()
@cached_response(timeout=120, key_prefix="cart.total", include_user=True)  # 2 min TTL
@handle_errors("calculating cart total")
def get_cart_total():
    """
    Get cart total and summary - CACHED (2 min TTL, user-specific)
    
    Cache: Response is cached for 2 minutes per user. Cache automatically
           expires to reflect cart changes. Use short TTL due to dynamic nature.
    """
    user_id = int(get_jwt_identity())
    cart = cart_service.get_or_create_active_cart(user_id)
    total_info = cart_service.calculate_cart_total(cart.id)
    return jsonify(total_info), 200

@bp.put("/cart/<int:cart_id>/status")
@jwt_required()
@cart_owner_required()
@handle_errors("updating cart status", handle_validation=True)
def update_cart_status(cart_id: int):
    """
    Update cart status
    
    Authentication: JWT token required (customer only)
    Authorization: User can only update their own carts
    """
    user_id = int(get_jwt_identity())
    data = CartUpdateSchema().load(request.get_json() or {})
    
    cart = cart_service.update_cart_status(
        cart_id=cart_id,
        status=data['status'],
        user_id=user_id
    )
    
    return jsonify(CartReadSchema().dump(cart)), 200

@bp.get("/cart/validate")
@jwt_required()
@handle_errors("validating cart for checkout")
def validate_cart():
    """
    Validate user's active cart for checkout
    """
    user_id = int(get_jwt_identity())
    cart = cart_service.get_or_create_active_cart(user_id)
    validation_results = cart_service.validate_cart_for_checkout(cart.id)
    return jsonify(validation_results), 200

# ===== ADMINISTRATIVE CART ENDPOINTS =====

@bp.get("/admin/carts")
@admin_only
@handle_errors("getting all carts")
def get_all_carts():
    """
    Get all carts in the system (Admin only)
    
    Authentication: JWT token with admin role required
    
    Query Parameters:
        - status (optional): Filter by cart status
        - user_id (optional): Filter by user ID
    
    Returns:
        HTTP 200: List of all carts
    """
    status = request.args.get('status')
    user_id = request.args.get('user_id')
    
    # Filter parameters for admin query
    filters = {}
    if status:
        filters['status'] = status
    if user_id:
        filters['user_id'] = int(user_id)
    
    # This would need to be implemented in cart_service
    return jsonify({"message": "Admin cart listing - to be implemented"}), 501

@bp.get("/admin/carts/<int:cart_id>")
@admin_only
@handle_errors("getting cart by admin")
def admin_get_cart(cart_id: int):
    """
    Get any cart by ID (Admin only)
    
    Authentication: JWT token with admin role required
    """
    # Admin can access any cart without ownership validation
    try:
        # This would need cart_service.get_cart_by_id_admin() method
        return jsonify({"message": "Admin cart detail - to be implemented"}), 501
    except Exception:
        return jsonify({"error": "Cart not found"}), 404

@bp.put("/admin/carts/<int:cart_id>/status")
@admin_only
@handle_errors("updating cart status by admin", handle_validation=True)
def admin_update_cart_status(cart_id: int):
    """
    Update any cart status (Admin only)
    
    Authentication: JWT token with admin role required
    """
    data = CartUpdateSchema().load(request.get_json() or {})
    
    # Admin can update any cart status
    # This would need cart_service.admin_update_cart_status() method
    return jsonify({"message": "Admin cart status update - to be implemented"}), 501

# ===== SALES ENDPOINTS (Placeholder for future implementation) =====

@bp.post("/checkout")
@jwt_required()
@customer_only
@handle_errors("processing checkout", handle_validation=True)
def checkout():
    """
    Convert cart to sale (checkout process)
    
    Authentication: JWT token with customer role required
    
    Request Body:
        - cart_id (required): ID of the cart to checkout
        - delivery_address_id (required): ID of delivery address
        - payment_method (optional): Payment method used
        - payment_reference (optional): Payment reference/transaction ID
        - generate_invoice (optional): Generate invoice automatically (default: false)
    
    Returns:
        HTTP 201: Sale created successfully with sale details and optional invoice
        HTTP 400: Validation errors or cart issues
        HTTP 404: Cart or delivery address not found
        HTTP 403: Access denied to cart or delivery address
    """
    user_id = int(get_jwt_identity())
    data = SaleFromCartSchema().load(request.get_json() or {})
    
    # Create sale from cart
    sale = sale_service.create_sale_from_cart(
        user_id=user_id,
        cart_id=data['cart_id'],
        delivery_address_id=data['delivery_address_id'],
        payment_method=data.get('payment_method'),
        payment_reference=data.get('payment_reference')
    )
    
    # Get detailed sale information for response
    sale_summary = sale_service.get_sale_summary(sale.id, user_id)
    
    response_data = {
        "message": "Checkout completed successfully",
        "sale": SaleReadSchema().dump(sale),
        "summary": sale_summary
    }
    
    # Generate invoice automatically if requested
    if data.get('generate_invoice', False):
        try:
            invoice = invoice_service.create_invoice(
                sale_id=sale.id,
                delivery_address_id=data['delivery_address_id'],
                user_id=user_id
            )
            response_data["invoice"] = InvoiceReadSchema().dump(invoice)
            response_data["message"] = "Checkout completed successfully with invoice generated"
        except Exception as e:
            # Don't fail the checkout if invoice generation fails
            response_data["warning"] = f"Sale completed but invoice generation failed: {str(e)}"
    
    return jsonify(response_data), 201

@bp.get("/sales")
@jwt_required()
@customer_only
@handle_errors("getting user sales")
def get_user_sales():
    """
    Get all sales for the current user
    
    Authentication: JWT token with customer role required
    
    Query Parameters:
        - start_date (optional): Filter sales from this date (YYYY-MM-DD)
        - end_date (optional): Filter sales until this date (YYYY-MM-DD)
        - summary (optional): Include summary statistics if true
    
    Returns:
        HTTP 200: List of user's sales
    """
    user_id = int(get_jwt_identity())
    
    # Parse optional date filters
    start_date = None
    end_date = None
    
    if request.args.get('start_date'):
        try:
            start_date = datetime.strptime(request.args.get('start_date'), '%Y-%m-%d')
        except ValueError:
            return jsonify({"message": "Invalid start_date format. Use YYYY-MM-DD"}), 400
    
    if request.args.get('end_date'):
        try:
            end_date = datetime.strptime(request.args.get('end_date'), '%Y-%m-%d')
        except ValueError:
            return jsonify({"message": "Invalid end_date format. Use YYYY-MM-DD"}), 400
    
    # Get user sales
    sales = sale_service.get_user_sales(user_id, start_date, end_date)
    
    response_data = {
        "sales": SaleListSchema(many=True).dump(sales),
        "count": len(sales)
    }
    
    # Include summary if requested
    if request.args.get('summary') == 'true':
        response_data["summary"] = sale_service.get_user_sales_summary(user_id)
    
    return jsonify(response_data), 200

@bp.get("/sales/<int:sale_id>")
@jwt_required()
@customer_only
@handle_errors("getting sale")
def get_sale(sale_id: int):
    """
    Get specific sale by ID (user can only access their own sales)
    
    Authentication: JWT token with customer role required
    
    Path Parameters:
        - sale_id: ID of the sale to retrieve
    
    Query Parameters:
        - include_summary (optional): Include detailed summary if true
    
    Returns:
        HTTP 200: Sale details
        HTTP 404: Sale not found
        HTTP 403: Access denied (sale belongs to another user)
    """
    user_id = int(get_jwt_identity())
    
    # Get sale with ownership validation
    sale = sale_service.get_sale_by_id(sale_id, user_id)
    
    response_data = {
        "sale": SaleReadSchema().dump(sale)
    }
    
    # Include detailed summary if requested
    if request.args.get('include_summary') == 'true':
        response_data["summary"] = sale_service.get_sale_summary(sale_id, user_id)
    
    return jsonify(response_data), 200

# ===== INVOICE ENDPOINTS =====

@bp.post("/invoices")
@jwt_required()
@customer_only
@handle_errors("creating invoice", handle_validation=True)
def create_invoice():
    """
    Create an invoice for a sale
    
    Authentication: JWT token with customer role required
    
    Request Body:
        - sale_id (required): ID of the sale to invoice
        - delivery_address_id (required): ID of delivery address
    
    Returns:
        HTTP 201: Invoice created successfully
        HTTP 400: Validation errors
        HTTP 404: Sale or delivery address not found
        HTTP 403: Access denied to sale or delivery address
    """
    user_id = int(get_jwt_identity())
    data = InvoiceCreateSchema().load(request.get_json() or {})
    
    # Create invoice
    invoice = invoice_service.create_invoice(
        sale_id=data['sale_id'],
        delivery_address_id=data['delivery_address_id'],
        user_id=user_id
    )
    
    return jsonify({
        "message": "Invoice created successfully",
        "invoice": InvoiceReadSchema().dump(invoice)
    }), 201

@bp.get("/invoices/<int:invoice_id>")
@jwt_required()
@customer_only
@handle_errors("getting invoice")
def get_invoice(invoice_id: int):
    """
    Get specific invoice by ID (user can only access their own invoices)
    
    Authentication: JWT token with customer role required
    
    Path Parameters:
        - invoice_id: ID of the invoice to retrieve
    
    Query Parameters:
        - include_details (optional): Include detailed summary if true
    
    Returns:
        HTTP 200: Invoice details
        HTTP 404: Invoice not found
        HTTP 403: Access denied (invoice belongs to another user)
    """
    user_id = int(get_jwt_identity())
    
    # Get invoice with ownership validation
    if request.args.get('include_details') == 'true':
        invoice = invoice_service.get_invoice_with_details(invoice_id, user_id)
        response_data = {
            "invoice": InvoiceDetailSchema().dump(invoice)
        }
    else:
        invoice = invoice_service.get_invoice_by_id(invoice_id, user_id)
        response_data = {
            "invoice": InvoiceReadSchema().dump(invoice)
        }
    
    # Include detailed summary if requested
    if request.args.get('include_summary') == 'true':
        response_data["summary"] = invoice_service.generate_invoice_summary(invoice_id, user_id)
    
    return jsonify(response_data), 200

@bp.get("/invoices")
@jwt_required()
@customer_only
@handle_errors("getting user invoices")
def get_user_invoices():
    """
    Get all invoices for the current user
    
    Authentication: JWT token with customer role required
    
    Query Parameters:
        - start_date (optional): Filter invoices from this date (YYYY-MM-DD)
        - end_date (optional): Filter invoices until this date (YYYY-MM-DD)
        - summary (optional): Include summary statistics if true
    
    Returns:
        HTTP 200: List of user's invoices
    """
    user_id = int(get_jwt_identity())
    
    # Parse optional date filters
    start_date = None
    end_date = None
    
    if request.args.get('start_date'):
        try:
            start_date = datetime.strptime(request.args.get('start_date'), '%Y-%m-%d')
        except ValueError:
            return jsonify({"message": "Invalid start_date format. Use YYYY-MM-DD"}), 400
    
    if request.args.get('end_date'):
        try:
            end_date = datetime.strptime(request.args.get('end_date'), '%Y-%m-%d')
        except ValueError:
            return jsonify({"message": "Invalid end_date format. Use YYYY-MM-DD"}), 400
    
    # Get user invoices
    invoices = invoice_service.get_user_invoices(user_id, start_date, end_date)
    
    response_data = {
        "invoices": InvoiceListSchema(many=True).dump(invoices),
        "count": len(invoices)
    }
    
    # Include summary if requested
    if request.args.get('summary') == 'true':
        response_data["summary"] = invoice_service.get_user_invoices_summary(user_id)
    
    return jsonify(response_data), 200

@bp.get("/sales/<int:sale_id>/invoices")
@jwt_required()
@customer_only
@handle_errors("getting sale invoices")
def get_sale_invoices(sale_id: int):
    """
    Get all invoices for a specific sale
    
    Authentication: JWT token with customer role required
    
    Path Parameters:
        - sale_id: ID of the sale
    
    Returns:
        HTTP 200: List of invoices for the sale
        HTTP 404: Sale not found
        HTTP 403: Access denied (sale belongs to another user)
    """
    user_id = int(get_jwt_identity())
    
    # Get invoices for sale with ownership validation
    invoices = invoice_service.get_invoices_for_sale(sale_id, user_id)
    
    return jsonify({
        "sale_id": sale_id,
        "invoices": InvoiceListSchema(many=True).dump(invoices),
        "count": len(invoices)
    }), 200

@bp.put("/invoices/<int:invoice_id>")
@jwt_required()
@customer_only
@handle_errors("updating invoice", handle_validation=True)
def update_invoice(invoice_id: int):
    """
    Update invoice information (user can only update their own invoices)
    
    Authentication: JWT token with customer role required
    
    Path Parameters:
        - invoice_id: ID of the invoice to update
    
    Request Body:
        - delivery_address_id (optional): New delivery address ID
    
    Returns:
        HTTP 200: Invoice updated successfully
        HTTP 404: Invoice not found
        HTTP 403: Access denied (invoice belongs to another user)
        HTTP 400: Validation errors
    """
    user_id = int(get_jwt_identity())
    data = InvoiceUpdateSchema().load(request.get_json() or {})
    
    # Update invoice
    updated_invoice = invoice_service.update_invoice(invoice_id, data, user_id)
    
    return jsonify({
        "message": "Invoice updated successfully",
        "invoice": InvoiceReadSchema().dump(updated_invoice)
    }), 200

@bp.delete("/invoices/<int:invoice_id>")
@jwt_required()
@customer_only
@handle_errors("deleting invoice")
def delete_invoice(invoice_id: int):
    """
    Delete an invoice (user can only delete their own invoices)
    
    Authentication: JWT token with customer role required
    
    Path Parameters:
        - invoice_id: ID of the invoice to delete
    
    Returns:
        HTTP 200: Invoice deleted successfully
        HTTP 404: Invoice not found
        HTTP 403: Access denied (invoice belongs to another user)
    """
    user_id = int(get_jwt_identity())
    
    # Delete invoice
    invoice_service.delete_invoice(invoice_id, user_id)
    
    return jsonify({"message": "Invoice deleted successfully"}), 200

# ===== ADMINISTRATIVE SALES ENDPOINTS =====

@bp.get("/admin/sales")
@admin_only
@cached_response(timeout=600, key_prefix="admin.sales")  # 10 min TTL
@handle_errors("getting all sales")
def get_all_sales():
    """
    Get all sales in the system (Admin only) - CACHED (10 min TTL)
    
    Authentication: JWT token with admin role required
    
    Query Parameters:
        - user_id (optional): Filter by user ID
        - date_from (optional): Filter by date range (YYYY-MM-DD)
        - date_to (optional): Filter by date range (YYYY-MM-DD)
        - analytics (optional): Include analytics if true
    
    Cache: Response is cached for 10 minutes. Especially beneficial when
           analytics=true due to expensive aggregation operations.
    
    Returns:
        HTTP 200: List of all sales with optional analytics
    """
    # Parse optional filters
    user_id = request.args.get('user_id')
    if user_id:
        try:
            user_id = int(user_id)
        except ValueError:
            return jsonify({"message": "Invalid user_id format"}), 400
    
    start_date = None
    end_date = None
    
    if request.args.get('date_from'):
        try:
            start_date = datetime.strptime(request.args.get('date_from'), '%Y-%m-%d')
        except ValueError:
            return jsonify({"message": "Invalid date_from format. Use YYYY-MM-DD"}), 400
    
    if request.args.get('date_to'):
        try:
            end_date = datetime.strptime(request.args.get('date_to'), '%Y-%m-%d')
        except ValueError:
            return jsonify({"message": "Invalid date_to format. Use YYYY-MM-DD"}), 400
    
    # Get sales with filters
    sales = sale_service.get_all_sales(user_id, start_date, end_date)
    
    response_data = {
        "sales": SaleListSchema(many=True).dump(sales),
        "count": len(sales),
        "filters": {
            "user_id": user_id,
            "date_from": request.args.get('date_from'),
            "date_to": request.args.get('date_to')
        }
    }
    
    # Include analytics if requested
    if request.args.get('analytics') == 'true':
        response_data["analytics"] = sale_service.get_sales_analytics(start_date, end_date)
    
    return jsonify(response_data), 200

@bp.get("/admin/sales/<int:sale_id>")
@admin_only
@handle_errors("getting sale by admin")
def admin_get_sale(sale_id: int):
    """
    Get any sale by ID (Admin only)
    
    Authentication: JWT token with admin role required
    
    Path Parameters:
        - sale_id: ID of the sale to retrieve
    
    Query Parameters:
        - include_summary (optional): Include detailed summary if true
    
    Returns:
        HTTP 200: Sale details
        HTTP 404: Sale not found
    """
    # Admin can access any sale without ownership validation
    sale = sale_service.get_sale_by_id(sale_id)
    
    response_data = {
        "sale": SaleReadSchema().dump(sale)
    }
    
    # Include detailed summary if requested
    if request.args.get('include_summary') == 'true':
        response_data["summary"] = sale_service.get_sale_summary(sale_id)
    
    return jsonify(response_data), 200

@bp.put("/admin/sales/<int:sale_id>")
@admin_only
@handle_errors("updating sale", handle_validation=True)
def admin_update_sale(sale_id: int):
    """
    Update sale information (Admin only)
    
    Authentication: JWT token with admin role required
    
    Path Parameters:
        - sale_id: ID of the sale to update
    
    Request Body:
        - total (optional): New total amount for the sale
    
    Returns:
        HTTP 200: Sale updated successfully
        HTTP 404: Sale not found
        HTTP 400: Validation errors
    """
    data = SaleUpdateSchema().load(request.get_json() or {})
    
    # Update sale
    updated_sale = sale_service.update_sale(sale_id, data)
    
    return jsonify({
        "message": "Sale updated successfully",
        "sale": SaleReadSchema().dump(updated_sale)
    }), 200

# ===== ADMINISTRATIVE INVOICE ENDPOINTS =====

@bp.get("/admin/invoices")
@admin_only
@handle_errors("getting all invoices")
def get_all_invoices():
    """
    Get all invoices in the system (Admin only)
    
    Authentication: JWT token with admin role required
    
    Query Parameters:
        - user_id (optional): Filter by user ID
        - date_from (optional): Filter by date range (YYYY-MM-DD)
        - date_to (optional): Filter by date range (YYYY-MM-DD)
        - analytics (optional): Include analytics if true
    
    Returns:
        HTTP 200: List of all invoices with optional analytics
    """
    # Parse optional filters
    user_id = request.args.get('user_id')
    if user_id:
        try:
            user_id = int(user_id)
        except ValueError:
            return jsonify({"message": "Invalid user_id format"}), 400
    
    start_date = None
    end_date = None
    
    if request.args.get('date_from'):
        try:
            start_date = datetime.strptime(request.args.get('date_from'), '%Y-%m-%d')
        except ValueError:
            return jsonify({"message": "Invalid date_from format. Use YYYY-MM-DD"}), 400
    
    if request.args.get('date_to'):
        try:
            end_date = datetime.strptime(request.args.get('date_to'), '%Y-%m-%d')
        except ValueError:
            return jsonify({"message": "Invalid date_to format. Use YYYY-MM-DD"}), 400
    
    # Get invoices with filters
    invoices = invoice_service.get_all_invoices(start_date, end_date, user_id)
    
    response_data = {
        "invoices": InvoiceListSchema(many=True).dump(invoices),
        "count": len(invoices),
        "filters": {
            "user_id": user_id,
            "date_from": request.args.get('date_from'),
            "date_to": request.args.get('date_to')
        }
    }
    
    # Include analytics if requested
    if request.args.get('analytics') == 'true':
        response_data["analytics"] = invoice_service.get_invoices_analytics(start_date, end_date)
    
    return jsonify(response_data), 200

@bp.get("/admin/invoices/<int:invoice_id>")
@admin_only
@handle_errors("getting invoice by admin")
def admin_get_invoice(invoice_id: int):
    """
    Get any invoice by ID (Admin only)
    
    Authentication: JWT token with admin role required
    
    Path Parameters:
        - invoice_id: ID of the invoice to retrieve
    
    Query Parameters:
        - include_details (optional): Include detailed summary if true
        - include_summary (optional): Include comprehensive summary if true
    
    Returns:
        HTTP 200: Invoice details
        HTTP 404: Invoice not found
    """
    # Admin can access any invoice without ownership validation
    if request.args.get('include_details') == 'true':
        invoice = invoice_service.get_invoice_with_details(invoice_id)
        response_data = {
            "invoice": InvoiceDetailSchema().dump(invoice)
        }
    else:
        invoice = invoice_service.get_invoice_by_id(invoice_id)
        response_data = {
            "invoice": InvoiceReadSchema().dump(invoice)
        }
    
    # Include detailed summary if requested
    if request.args.get('include_summary') == 'true':
        response_data["summary"] = invoice_service.generate_invoice_summary(invoice_id)
    
    return jsonify(response_data), 200

@bp.put("/admin/invoices/<int:invoice_id>")
@admin_only
@handle_errors("updating invoice by admin", handle_validation=True)
def admin_update_invoice(invoice_id: int):
    """
    Update any invoice information (Admin only)
    
    Authentication: JWT token with admin role required
    
    Path Parameters:
        - invoice_id: ID of the invoice to update
    
    Request Body:
        - delivery_address_id (optional): New delivery address ID
    
    Returns:
        HTTP 200: Invoice updated successfully
        HTTP 404: Invoice not found
        HTTP 400: Validation errors
    """
    data = InvoiceUpdateSchema().load(request.get_json() or {})
    
    # Admin can update any invoice without ownership validation
    updated_invoice = invoice_service.update_invoice(invoice_id, data)
    
    return jsonify({
        "message": "Invoice updated successfully",
        "invoice": InvoiceReadSchema().dump(updated_invoice)
    }), 200

@bp.delete("/admin/invoices/<int:invoice_id>")
@admin_only
@handle_errors("deleting invoice by admin")
def admin_delete_invoice(invoice_id: int):
    """
    Delete any invoice (Admin only)
    
    Authentication: JWT token with admin role required
    
    Path Parameters:
        - invoice_id: ID of the invoice to delete
    
    Returns:
        HTTP 200: Invoice deleted successfully
        HTTP 404: Invoice not found
    """
    # Admin can delete any invoice without ownership validation
    invoice_service.delete_invoice(invoice_id)
    
    return jsonify({"message": "Invoice deleted successfully"}), 200

@bp.post("/admin/invoices")
@admin_only
@handle_errors("creating invoice by admin", handle_validation=True)
def admin_create_invoice():
    """
    Create an invoice for any sale (Admin only)
    
    Authentication: JWT token with admin role required
    
    Request Body:
        - sale_id (required): ID of the sale to invoice
        - delivery_address_id (required): ID of delivery address
    
    Returns:
        HTTP 201: Invoice created successfully
        HTTP 400: Validation errors
        HTTP 404: Sale or delivery address not found
    """
    data = InvoiceCreateSchema().load(request.get_json() or {})
    
    # Admin can create invoices for any sale without ownership validation
    invoice = invoice_service.create_invoice(
        sale_id=data['sale_id'],
        delivery_address_id=data['delivery_address_id']
    )
    
    return jsonify({
        "message": "Invoice created successfully",
        "invoice": InvoiceReadSchema().dump(invoice)
    }), 201

@bp.get("/admin/invoices/search")
@admin_only
@handle_errors("searching invoices")
def admin_search_invoices():
    """
    Search invoices by various criteria (Admin only)
    
    Authentication: JWT token with admin role required
    
    Query Parameters:
        - min_total (optional): Minimum sale total
        - max_total (optional): Maximum sale total
    
    Returns:
        HTTP 200: List of matching invoices
        HTTP 400: Invalid search parameters
    """
    min_total = request.args.get('min_total')
    max_total = request.args.get('max_total')
    
    # Validate numeric parameters
    if min_total:
        try:
            min_total = float(min_total)
        except ValueError:
            return jsonify({"message": "Invalid min_total format"}), 400
    
    if max_total:
        try:
            max_total = float(max_total)
        except ValueError:
            return jsonify({"message": "Invalid max_total format"}), 400
    
    # Search invoices
    invoices = invoice_service.search_invoices(min_total, max_total)
    
    return jsonify({
        "invoices": InvoiceListSchema(many=True).dump(invoices),
        "count": len(invoices),
        "search_criteria": {
            "min_total": min_total,
            "max_total": max_total
        }
    }), 200