# tests/conftest.py
import pytest
import tempfile
import os
from app import create_app
from app.extensions import db
from app.models.user import User
from app.models.product import Product
from app.models.cart import Cart
from app.models.cart_product import CartProduct
from app.models.sale import Sale
from app.models.sale_product import SaleProduct
from app.models.delivery_address import DeliveryAddress
from app.models.invoice import Invoice
from flask_jwt_extended import create_access_token, create_refresh_token


@pytest.fixture(scope='session')
def app():
    """Create application for testing"""
    # Create temporary database file
    db_fd, db_path = tempfile.mkstemp()
    
    # Test configuration - Use environment Redis Cloud settings for testing
    test_config = {
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': f'sqlite:///{db_path}',
        'SQLALCHEMY_TRACK_MODIFICATIONS': False,
        'JWT_SECRET_KEY': 'test-secret-key-for-testing-only',
        'WTF_CSRF_ENABLED': False,
        'CACHE_TYPE': 'RedisCache',  # Use Redis cache for testing to match production
        'CACHE_REDIS_HOST': os.getenv('REDIS_HOST', 'localhost'),
        'CACHE_REDIS_PORT': int(os.getenv('REDIS_PORT', 6379)),
        'CACHE_REDIS_PASSWORD': os.getenv('REDIS_PASSWORD'),
        'CACHE_REDIS_USERNAME': os.getenv('REDIS_USERNAME'),
        'CACHE_DEFAULT_TIMEOUT': 300
    }
    
    # Create app with test config
    app = create_app(config=test_config)
    
    with app.app_context():
        # Create all tables
        db.create_all()
        yield app
        
        # Cleanup
        db.drop_all()
        os.close(db_fd)
        os.unlink(db_path)


@pytest.fixture
def client(app):
    """Flask test client"""
    return app.test_client()


@pytest.fixture
def runner(app):
    """Flask test CLI runner"""
    return app.test_cli_runner()


@pytest.fixture(autouse=True)
def clean_db(app):
    """Clean database before each test"""
    with app.app_context():
        # Clear all tables in proper order (due to foreign key constraints)
        db.session.query(Invoice).delete()
        db.session.query(SaleProduct).delete()
        db.session.query(Sale).delete()
        db.session.query(CartProduct).delete()
        db.session.query(Cart).delete()
        db.session.query(DeliveryAddress).delete()
        db.session.query(Product).delete()
        db.session.query(User).delete()
        db.session.commit()
        yield
        # Cleanup after test
        db.session.rollback()


@pytest.fixture
def sample_user(app):
    """Create a sample customer user"""
    with app.app_context():
        user = User(
            email="customer@test.com",
            name="Test Customer",
            phone="+1234567890",
            role="customer"
        )
        user.set_password("testpassword123")
        db.session.add(user)
        db.session.commit()
        return user


@pytest.fixture
def sample_admin(app):
    """Create a sample admin user"""
    with app.app_context():
        admin = User(
            email="admin@test.com",
            name="Test Admin",
            phone="+0987654321",
            role="admin"
        )
        admin.set_password("adminpassword123")
        db.session.add(admin)
        db.session.commit()
        return admin


@pytest.fixture
def customer_token(app, sample_user):
    """Generate JWT access token for customer user"""
    with app.app_context():
        # Get user from database using known email to avoid DetachedInstanceError
        user = User.query.filter_by(email="customer@test.com").first()
        claims = {"role": user.role}
        token = create_access_token(identity=str(user.id), additional_claims=claims)
        return f"Bearer {token}"


@pytest.fixture
def admin_token(app, sample_admin):
    """Generate JWT access token for admin user"""
    with app.app_context():
        # Get user from database using known email to avoid DetachedInstanceError
        user = User.query.filter_by(email="admin@test.com").first()
        claims = {"role": user.role}
        token = create_access_token(identity=str(user.id), additional_claims=claims)
        return f"Bearer {token}"


@pytest.fixture
def customer_refresh_token(app, sample_user):
    """Generate JWT refresh token for customer user"""
    with app.app_context():
        # Get user from database using known email to avoid DetachedInstanceError
        user = User.query.filter_by(email="customer@test.com").first()
        claims = {"role": user.role}
        token = create_refresh_token(identity=str(user.id), additional_claims=claims)
        return f"Bearer {token}"


@pytest.fixture
def admin_refresh_token(app, sample_admin):
    """Generate JWT refresh token for admin user"""
    with app.app_context():
        # Get user from database using known email to avoid DetachedInstanceError
        user = User.query.filter_by(email="admin@test.com").first()
        claims = {"role": user.role}
        token = create_refresh_token(identity=str(user.id), additional_claims=claims)
        return f"Bearer {token}"


@pytest.fixture
def sample_products(app):
    """Create sample products for testing"""
    with app.app_context():
        products = [
            Product(
                name="Premium Dog Food",
                description="High quality dog food for all breeds",
                price=29.99,
                stock=100
            ),
            Product(
                name="Cat Toy Mouse",
                description="Interactive toy mouse for cats",
                price=12.50,
                stock=50
            ),
            Product(
                name="Bird Cage Large",
                description="Spacious cage for medium to large birds",
                price=89.99,
                stock=25
            )
        ]
        
        for product in products:
            db.session.add(product)
        db.session.commit()
        
        # Refresh objects to ensure they are bound to the session
        db.session.refresh(products[0])
        db.session.refresh(products[1])
        db.session.refresh(products[2])
        
        return products


@pytest.fixture
def valid_user_data():
    """Valid user registration data"""
    return {
        "email": "newuser@test.com",
        "password": "newpassword123",
        "name": "New Test User",
        "phone": "+1555123456"
    }


@pytest.fixture
def valid_login_data():
    """Valid login credentials"""
    return {
        "email": "customer@test.com",
        "password": "testpassword123"
    }


@pytest.fixture
def valid_admin_login_data():
    """Valid admin login credentials"""
    return {
        "email": "admin@test.com",
        "password": "adminpassword123"
    }


@pytest.fixture
def valid_product_data():
    """Valid product creation data"""
    return {
        "name": "Test Product",
        "description": "A test product for testing purposes",
        "price": 25.99,
        "stock": 50
    }


@pytest.fixture
def valid_delivery_address_data():
    """Valid delivery address data"""
    return {
        "user_id": 1,
        "address": "123 Test Street",
        "city": "Test City",
        "postal_code": "12345",
        "country": "Test Country"
    }


@pytest.fixture
def sample_delivery_address(app, sample_user):
    """Create a sample delivery address"""
    with app.app_context():
        # Get user from database to avoid DetachedInstanceError
        user = User.query.filter_by(email="customer@test.com").first()
        
        delivery_address = DeliveryAddress(
            user_id=user.id,
            address="123 Test Street",
            city="Test City",
            postal_code="12345",
            country="Test Country"
        )
        db.session.add(delivery_address)
        db.session.commit()
        db.session.refresh(delivery_address)
        return delivery_address


@pytest.fixture
def sample_cart(app, sample_user):
    """Create a sample cart"""
    with app.app_context():
        # Get user from database to avoid DetachedInstanceError
        user = User.query.filter_by(email="customer@test.com").first()
        
        cart = Cart(
            user_id=user.id,
            status='active'
        )
        db.session.add(cart)
        db.session.commit()
        db.session.refresh(cart)
        return cart


@pytest.fixture
def sample_cart_with_products(app, sample_user, sample_products):
    """Create a sample cart with products"""
    with app.app_context():
        # Get user from database to avoid DetachedInstanceError
        user = User.query.filter_by(email="customer@test.com").first()
        
        cart = Cart(
            user_id=user.id,
            status='active'
        )
        db.session.add(cart)
        db.session.commit()
        
        # Add products to cart
        for i, product in enumerate(sample_products[:2]):  # Add first 2 products
            cart_product = CartProduct(
                cart_id=cart.id,
                product_id=product.id,
                quantity=i + 1  # 1, 2 quantities
            )
            db.session.add(cart_product)
        
        db.session.commit()
        db.session.refresh(cart)
        return cart


@pytest.fixture
def sample_sale(app, sample_user, sample_products):
    """Create a sample sale"""
    with app.app_context():
        # Get user from database to avoid DetachedInstanceError
        user = User.query.filter_by(email="customer@test.com").first()
        
        sale = Sale(
            user_id=user.id,
            total=99.99
        )
        db.session.add(sale)
        db.session.commit()
        
        # Add products to sale
        for i, product in enumerate(sample_products[:2]):  # Add first 2 products
            sale_product = SaleProduct(
                sale_id=sale.id,
                product_id=product.id,
                quantity=i + 1,  # 1, 2 quantities
                price=product.price
            )
            db.session.add(sale_product)
        
        db.session.commit()
        db.session.refresh(sale)
        return sale


@pytest.fixture
def sample_invoice(app, sample_sale, sample_delivery_address):
    """Create a sample invoice"""
    with app.app_context():
        invoice = Invoice(
            sale_id=sample_sale.id,
            delivery_address_id=sample_delivery_address.id
        )
        db.session.add(invoice)
        db.session.commit()
        db.session.refresh(invoice)
        return invoice
