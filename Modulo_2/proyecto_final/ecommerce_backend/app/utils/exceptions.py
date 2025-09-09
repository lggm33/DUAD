from flask import jsonify
"""
Centralized exception classes for the application.
All services should use these exceptions for consistency.
"""


class AppError(Exception):
    """
    Base application error class.
    All custom exceptions should inherit from this.
    """
    status = 500  # Default HTTP status code
    message = "Internal server error"

    def __init__(self, message: str = None, status: int = None):
        self.message = message or self.message
        self.status = status or self.status
        super().__init__(self.message)

    def __str__(self):
        return self.message


# === COMMON HTTP ERRORS ===

class NotFoundError(AppError):
    """Resource not found (HTTP 404)"""
    status = 404
    message = "Resource not found"


class AlreadyExistsError(AppError):
    """Resource already exists (HTTP 409)"""
    status = 409
    message = "Resource already exists"


class ValidationError(AppError):
    """Validation failed (HTTP 400)"""
    status = 400
    message = "Validation error"


class UnauthorizedError(AppError):
    """Authentication failed (HTTP 401)"""
    status = 401
    message = "Authentication required"


class ForbiddenError(AppError):
    """Access forbidden (HTTP 403)"""
    status = 403
    message = "Access forbidden"


class BadRequestError(AppError):
    """Bad request (HTTP 400)"""
    status = 400
    message = "Bad request"


# === SPECIFIC BUSINESS LOGIC ERRORS ===

class UserNotFoundError(NotFoundError):
    """User not found"""
    message = "User not found"


class ProductNotFoundError(NotFoundError):
    """Product not found"""
    message = "Product not found"


class DeliveryAddressNotFoundError(NotFoundError):
    """Delivery address not found"""
    message = "Delivery address not found"


class EmailInUseError(AlreadyExistsError):
    """Email already in use"""
    message = "Email already in use"


class ProductNameInUseError(AlreadyExistsError):
    """Product name already in use"""
    message = "Product name already in use"


class InvalidCredentialsError(UnauthorizedError):
    """Invalid login credentials"""
    message = "Invalid credentials"


class InsufficientPermissionsError(ForbiddenError):
    """User doesn't have required permissions"""
    message = "Insufficient permissions"


# === CART SPECIFIC ERRORS ===

class CartNotFoundError(NotFoundError):
    """Cart not found"""
    message = "Cart not found"


class InsufficientStockError(ValidationError):
    """Insufficient stock available for product"""
    message = "Insufficient stock available"


class CartError(BadRequestError):
    """General cart operation error"""
    message = "Cart operation failed"


class EmptyCartError(ValidationError):
    """Cart is empty"""
    message = "Cart is empty"


class CartNotActiveError(BadRequestError):
    """Cart is not in active state"""
    message = "Cart is not active"


# === SALE SPECIFIC ERRORS ===

class SaleNotFoundError(NotFoundError):
    """Sale not found"""
    message = "Sale not found"


class SaleError(BadRequestError):
    """General sale operation error"""
    message = "Sale operation failed"


# === INVOICE SPECIFIC ERRORS ===

class InvoiceNotFoundError(NotFoundError):
    """Invoice not found"""
    message = "Invoice not found"


class InvoiceError(BadRequestError):
    """General invoice operation error"""
    message = "Invoice operation failed"


# === REPOSITORY ERRORS ===

class RepoError(AppError):
    """Database/Repository layer error"""
    status = 500
    message = "Database operation failed"

# === MessageErrors ===

def json_error(message: str, status: int):
    return jsonify({"message": message}), status

