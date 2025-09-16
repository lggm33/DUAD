# tests/test_auth_api.py
import pytest
import json
from app.models.user import User
from app.extensions import db


@pytest.mark.auth
class TestUserRegistration:
    """Test user registration endpoint"""
    
    def test_register_customer_success(self, client, valid_user_data):
        """Test successful customer registration"""
        response = client.post('/users/register', json=valid_user_data)
        
        assert response.status_code == 201
        data = response.get_json()
        
        # Verify response structure
        assert 'id' in data
        assert data['email'] == valid_user_data['email']
        assert data['name'] == valid_user_data['name']
        assert data['phone'] == valid_user_data['phone']
        assert data['role'] == 'customer'  # Default role
        
        # Verify user was created in database
        user = User.query.filter_by(email=valid_user_data['email']).first()
        assert user is not None
        assert user.role == 'customer'
    
    def test_register_admin_by_admin_success(self, client, admin_token, valid_user_data):
        """Test admin can create admin users"""
        print(f"\n=== DEBUG INFO ===")
        print(f"Admin token: {admin_token}")
        print(f"Admin token type: {type(admin_token)}")
        
        admin_user_data = {**valid_user_data, 'role': 'admin', 'email': 'newadmin@test.com'}
        
        response = client.post('/users/register', 
                             json=admin_user_data,
                             headers={'Authorization': admin_token})
        
        print(f"Request data: {admin_user_data}")
        print(f"Response status: {response.status_code}")
        print(f"Response data: {response.get_json()}")
        
        assert response.status_code == 201
        data = response.get_json()
        assert data['role'] == 'admin'
        
        # Verify in database
        user = User.query.filter_by(email='newadmin@test.com').first()
        assert user.role == 'admin'
    
    def test_register_admin_by_customer_fails(self, client, customer_token, valid_user_data):
        """Test customer cannot create admin users"""
        admin_user_data = {**valid_user_data, 'role': 'admin', 'email': 'shouldnotbeadmin@test.com'}
        
        response = client.post('/users/register',
                             json=admin_user_data,
                             headers={'Authorization': customer_token})
        
        assert response.status_code == 201
        data = response.get_json()
        assert data['role'] == 'customer'  # Role should be forced to customer
        
        # Verify in database
        user = User.query.filter_by(email='shouldnotbeadmin@test.com').first()
        assert user.role == 'customer'
    
    def test_register_duplicate_email_fails(self, client, app, valid_user_data):
        """Test registration with duplicate email fails"""
        with app.app_context():
            # Create a user first
            from app.models.user import User
            from app.extensions import db
            
            existing_user = User(
                email="existing@test.com",
                name="Existing User",
                role="customer"
            )
            existing_user.set_password("password123")
            db.session.add(existing_user)
            db.session.commit()
            
            duplicate_data = {**valid_user_data, 'email': 'existing@test.com'}
            
            response = client.post('/users/register', json=duplicate_data)
            
            assert response.status_code == 409
            data = response.get_json()
            assert 'message' in data
            assert 'email' in data['message'].lower()
    
    def test_register_invalid_email_fails(self, client, valid_user_data):
        """Test registration with invalid email fails"""
        invalid_data = {**valid_user_data, 'email': 'invalid-email'}
        
        response = client.post('/users/register', json=invalid_data)
        
        assert response.status_code == 400
        data = response.get_json()
        assert 'error' in data
    
    def test_register_short_password_fails(self, client, valid_user_data):
        """Test registration with short password fails"""
        invalid_data = {**valid_user_data, 'password': '123'}
        
        response = client.post('/users/register', json=invalid_data)
        
        assert response.status_code == 400
        data = response.get_json()
        assert 'error' in data
    
    def test_register_missing_required_fields_fails(self, client):
        """Test registration with missing required fields fails"""
        incomplete_data = {'email': 'test@test.com'}
        
        response = client.post('/users/register', json=incomplete_data)
        
        assert response.status_code == 400
        data = response.get_json()
        assert 'error' in data
    
    def test_register_empty_json_fails(self, client):
        """Test registration with empty JSON fails"""
        response = client.post('/users/register', json={})
        
        assert response.status_code == 400
        data = response.get_json()
        assert 'error' in data
    
    def test_register_no_json_fails(self, client):
        """Test registration with no JSON body fails"""
        response = client.post('/users/register', 
                             headers={'Content-Type': 'application/json'})
        
        assert response.status_code == 400


@pytest.mark.auth
class TestUserLogin:
    """Test user login endpoint"""
    
    def test_login_customer_success(self, client, app):
        """Test successful customer login"""
        with app.app_context():
            # Create user directly in test
            from app.models.user import User
            from app.extensions import db
            
            user = User(
                email="testlogin@test.com",
                name="Test Login User",
                role="customer"
            )
            user.set_password("testpassword123")
            db.session.add(user)
            db.session.commit()
            
            login_data = {
                "email": "testlogin@test.com",
                "password": "testpassword123"
            }
            
            response = client.post('/users/login', json=login_data)
            
            assert response.status_code == 200
            data = response.get_json()
            
            # Verify response structure
            assert 'access_token' in data
            assert 'refresh_token' in data
            assert 'user' in data
            
            # Verify user data
            user_data = data['user']
            assert user_data['email'] == "testlogin@test.com"
            assert user_data['name'] == "Test Login User"
            assert user_data['role'] == "customer"
            
            # Verify tokens are strings
            assert isinstance(data['access_token'], str)
            assert isinstance(data['refresh_token'], str)
    
    def test_login_admin_success(self, client, sample_admin, valid_admin_login_data):
        """Test successful admin login"""
        response = client.post('/users/login', json=valid_admin_login_data)
        
        assert response.status_code == 200
        data = response.get_json()
        
        assert data['user']['role'] == 'admin'
        assert 'access_token' in data
        assert 'refresh_token' in data
    
    def test_login_invalid_email_fails(self, client):
        """Test login with invalid email fails"""
        invalid_data = {
            'email': 'nonexistent@test.com',
            'password': 'anypassword'
        }
        
        response = client.post('/users/login', json=invalid_data)
        
        assert response.status_code == 401
        data = response.get_json()
        assert 'message' in data
        assert 'Invalid credentials' in data['message']
    
    def test_login_invalid_password_fails(self, client, sample_user):
        """Test login with invalid password fails"""
        invalid_data = {
            'email': "customer@test.com",  # Use the known email from fixture
            'password': 'wrongpassword'
        }
        
        response = client.post('/users/login', json=invalid_data)
        
        assert response.status_code == 401
        data = response.get_json()
        assert 'message' in data
        assert 'Invalid credentials' in data['message']
    
    def test_login_missing_fields_fails(self, client):
        """Test login with missing fields fails"""
        incomplete_data = {'email': 'test@test.com'}
        
        response = client.post('/users/login', json=incomplete_data)
        
        assert response.status_code == 400
        data = response.get_json()
        assert 'errors' in data
    
    def test_login_empty_json_fails(self, client):
        """Test login with empty JSON fails"""
        response = client.post('/users/login', json={})
        
        assert response.status_code == 400


@pytest.mark.auth
class TestTokenRefresh:
    """Test token refresh endpoint"""
    
    def test_refresh_token_success(self, client, customer_refresh_token):
        """Test successful token refresh"""
        response = client.post('/users/refresh',
                             headers={'Authorization': customer_refresh_token})
        
        assert response.status_code == 200
        data = response.get_json()
        
        assert 'access_token' in data
        assert isinstance(data['access_token'], str)
        assert len(data['access_token']) > 0
    
    def test_refresh_token_admin_success(self, client, admin_refresh_token):
        """Test successful admin token refresh"""
        response = client.post('/users/refresh',
                             headers={'Authorization': admin_refresh_token})
        
        assert response.status_code == 200
        data = response.get_json()
        assert 'access_token' in data
    
    def test_refresh_without_token_fails(self, client):
        """Test refresh without token fails"""
        response = client.post('/users/refresh')
        
        assert response.status_code == 401
        data = response.get_json()
        assert 'message' in data
        assert 'Missing or invalid Authorization header' in data['message']
    
    def test_refresh_with_access_token_fails(self, client, customer_token):
        """Test refresh with access token instead of refresh token fails"""
        response = client.post('/users/refresh',
                             headers={'Authorization': customer_token})
        
        assert response.status_code == 422
        data = response.get_json()
        assert 'message' in data
    
    def test_refresh_with_invalid_token_fails(self, client):
        """Test refresh with invalid token fails"""
        response = client.post('/users/refresh',
                             headers={'Authorization': 'Bearer invalid-token'})
        
        assert response.status_code == 422


@pytest.mark.auth
class TestLogout:
    """Test logout endpoints"""
    
    def test_logout_success(self, client, customer_refresh_token):
        """Test successful logout (refresh token revocation)"""
        response = client.post('/users/logout',
                             headers={'Authorization': customer_refresh_token})
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['message'] == 'Logged out (refresh revoked)'
    
    def test_logout_access_success(self, client, customer_token):
        """Test successful access token revocation"""
        response = client.post('/users/logout-access',
                             headers={'Authorization': customer_token})
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['message'] == 'Access token revoked'
    
    def test_logout_without_token_fails(self, client):
        """Test logout without token fails"""
        response = client.post('/users/logout')
        
        assert response.status_code == 401
    
    def test_logout_access_without_token_fails(self, client):
        """Test access token revocation without token fails"""
        response = client.post('/users/logout-access')
        
        assert response.status_code == 401
    
    def test_logout_with_access_token_fails(self, client, customer_token):
        """Test logout endpoint with access token fails (needs refresh token)"""
        response = client.post('/users/logout',
                             headers={'Authorization': customer_token})
        
        assert response.status_code == 422
    
    def test_logout_access_with_refresh_token_fails(self, client, customer_refresh_token):
        """Test access logout endpoint with refresh token fails (needs access token)"""
        response = client.post('/users/logout-access',
                             headers={'Authorization': customer_refresh_token})
        
        assert response.status_code == 422


@pytest.mark.auth
class TestMakeAdmin:
    """Test make admin endpoint"""
    
    def test_make_admin_success(self, client, admin_token, sample_user, app):
        """Test successful user promotion to admin"""
        with app.app_context():
            # Get user from database using known email to avoid DetachedInstanceError
            user = User.query.filter_by(email="customer@test.com").first()
            user_id = user.id
            
        response = client.post(f'/users/{user_id}/make-admin',
                             headers={'Authorization': admin_token})
        
        assert response.status_code == 200
        data = response.get_json()
        
        assert data['id'] == user_id
        assert data['role'] == 'admin'
        
        # Verify in database
        updated_user = User.query.get(user_id)
        assert updated_user.role == 'admin'
    
    def test_make_admin_already_admin_fails(self, client, admin_token, sample_admin, app):
        """Test promoting already admin user fails"""
        with app.app_context():
            # Get admin from database using known email to avoid DetachedInstanceError
            admin = User.query.filter_by(email="admin@test.com").first()
            admin_id = admin.id
            
        response = client.post(f'/users/{admin_id}/make-admin',
                             headers={'Authorization': admin_token})
        
        assert response.status_code == 400
        data = response.get_json()
        assert 'already an admin' in data['message']
    
    def test_make_admin_nonexistent_user_fails(self, client, admin_token):
        """Test promoting nonexistent user fails"""
        response = client.post('/users/99999/make-admin',
                             headers={'Authorization': admin_token})
        
        assert response.status_code == 404
        data = response.get_json()
        assert 'message' in data
    
    def test_make_admin_without_token_fails(self, client, sample_user, app):
        """Test make admin without token fails"""
        with app.app_context():
            # Get user from database using known email to avoid DetachedInstanceError
            user = User.query.filter_by(email="customer@test.com").first()
            user_id = user.id
            
        response = client.post(f'/users/{user_id}/make-admin')
        
        assert response.status_code == 401
    
    def test_make_admin_customer_token_fails(self, client, customer_token, sample_user, app):
        """Test make admin with customer token fails"""
        with app.app_context():
            # Get user from database using known email to avoid DetachedInstanceError
            user = User.query.filter_by(email="customer@test.com").first()
            user_id = user.id
            
        response = client.post(f'/users/{user_id}/make-admin',
                             headers={'Authorization': customer_token})
        
        assert response.status_code == 403
        data = response.get_json()
        assert 'Permission denied' in data['message']


@pytest.mark.auth
class TestAuthenticationFlow:
    """Test complete authentication flows"""
    
    def test_complete_auth_flow(self, client, valid_user_data):
        """Test complete authentication flow: register -> login -> refresh -> logout"""
        # 1. Register
        register_response = client.post('/users/register', json=valid_user_data)
        assert register_response.status_code == 201
        
        # 2. Login
        login_data = {
            'email': valid_user_data['email'],
            'password': valid_user_data['password']
        }
        login_response = client.post('/users/login', json=login_data)
        assert login_response.status_code == 200
        
        tokens = login_response.get_json()
        access_token = f"Bearer {tokens['access_token']}"
        refresh_token = f"Bearer {tokens['refresh_token']}"
        
        # 3. Refresh token
        refresh_response = client.post('/users/refresh',
                                     headers={'Authorization': refresh_token})
        assert refresh_response.status_code == 200
        
        new_access_token = f"Bearer {refresh_response.get_json()['access_token']}"
        
        # 4. Revoke access token
        logout_access_response = client.post('/users/logout-access',
                                           headers={'Authorization': new_access_token})
        assert logout_access_response.status_code == 200
        
        # 5. Logout (revoke refresh token)
        logout_response = client.post('/users/logout',
                                    headers={'Authorization': refresh_token})
        assert logout_response.status_code == 200
    
    def test_admin_create_and_promote_flow(self, client, admin_token, valid_user_data):
        """Test admin creating user and promoting to admin"""
        # 1. Admin creates regular user
        user_data = {**valid_user_data, 'email': 'promote@test.com'}
        register_response = client.post('/users/register',
                                      json=user_data,
                                      headers={'Authorization': admin_token})
        assert register_response.status_code == 201
        
        created_user = register_response.get_json()
        assert created_user['role'] == 'customer'
        
        # 2. Admin promotes user to admin
        promote_response = client.post(f'/users/{created_user["id"]}/make-admin',
                                     headers={'Authorization': admin_token})
        assert promote_response.status_code == 200
        
        promoted_user = promote_response.get_json()
        assert promoted_user['role'] == 'admin'
        
        # 3. Promoted user can now create admin users
        admin_user_data = {
            'email': 'newadmin@test.com',
            'password': 'adminpass123',
            'name': 'New Admin',
            'role': 'admin'
        }
        
        # First login as the promoted user
        login_response = client.post('/users/login', json={
            'email': 'promote@test.com',
            'password': valid_user_data['password']
        })
        promoted_token = f"Bearer {login_response.get_json()['access_token']}"
        
        # Create admin user
        create_admin_response = client.post('/users/register',
                                          json=admin_user_data,
                                          headers={'Authorization': promoted_token})
        assert create_admin_response.status_code == 201
        assert create_admin_response.get_json()['role'] == 'admin'
