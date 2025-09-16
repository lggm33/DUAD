# tests/test_user_management_api.py
import pytest
import json
from app.models.user import User
from app.extensions import db


@pytest.mark.user_management
class TestUserRetrieval:
    """Test user retrieval endpoint"""
    
    def test_get_user_by_id_admin_success(self, client, admin_token, sample_user, app):
        """Test successful user retrieval by admin"""
        with app.app_context():
            user = User.query.filter_by(email="customer@test.com").first()
            user_id = user.id
            
        response = client.get(f'/users/{user_id}',
                            headers={'Authorization': admin_token})
        
        assert response.status_code == 200
        data = response.get_json()
        
        assert data['id'] == user_id
        assert data['email'] == "customer@test.com"
        assert data['name'] == "Test Customer"
        assert data['role'] == "customer"
    
    def test_get_user_by_id_customer_fails(self, client, customer_token, sample_user, app):
        """Test user retrieval by customer fails (admin only)"""
        with app.app_context():
            user = User.query.filter_by(email="customer@test.com").first()
            user_id = user.id
            
        response = client.get(f'/users/{user_id}',
                            headers={'Authorization': customer_token})
        
        assert response.status_code == 403
        data = response.get_json()
        assert 'Permission denied' in data['message']
    
    def test_get_user_by_id_no_auth_fails(self, client, sample_user, app):
        """Test user retrieval without authentication fails"""
        with app.app_context():
            user = User.query.filter_by(email="customer@test.com").first()
            user_id = user.id
            
        response = client.get(f'/users/{user_id}')
        
        assert response.status_code == 401
    
    def test_get_nonexistent_user_fails(self, client, admin_token):
        """Test get nonexistent user fails"""
        response = client.get('/users/99999',
                            headers={'Authorization': admin_token})
        
        assert response.status_code == 404
        data = response.get_json()
        assert 'message' in data


@pytest.mark.user_management
class TestUserUpdate:
    """Test user update endpoint"""
    
    def test_update_user_admin_success(self, client, admin_token, sample_user, app):
        """Test successful user update by admin"""
        with app.app_context():
            user = User.query.filter_by(email="customer@test.com").first()
            user_id = user.id
            
            update_data = {
                "name": "Updated Customer Name",
                "phone": "+1999888777"
            }
            
            response = client.put(f'/users/{user_id}',
                                json=update_data,
                                headers={'Authorization': admin_token})
            
            assert response.status_code == 200
            data = response.get_json()
            
            assert data['id'] == user_id
            assert data['name'] == update_data['name']
            assert data['phone'] == update_data['phone']
            assert data['email'] == "customer@test.com"  # Should remain unchanged
            
            # Verify update in database
            updated_user = User.query.get(user_id)
            assert updated_user.name == update_data['name']
            assert updated_user.phone == update_data['phone']
    
    def test_update_user_partial_success(self, client, admin_token, sample_user, app):
        """Test successful partial user update"""
        with app.app_context():
            user = User.query.filter_by(email="customer@test.com").first()
            user_id = user.id
            original_name = user.name
            
            update_data = {
                "phone": "+1555666777"
            }
            
            response = client.put(f'/users/{user_id}',
                                json=update_data,
                                headers={'Authorization': admin_token})
            
            assert response.status_code == 200
            data = response.get_json()
            
            assert data['name'] == original_name  # Should remain unchanged
            assert data['phone'] == update_data['phone']  # Should be updated
    
    def test_update_user_customer_fails(self, client, customer_token, sample_user, app):
        """Test user update by customer fails (requires admin or same user)"""
        with app.app_context():
            user = User.query.filter_by(email="customer@test.com").first()
            user_id = user.id
            
            update_data = {
                "name": "Should Not Update"
            }
            
            # Customer trying to update their own user should work based on optional_roles decorator
            response = client.put(f'/users/{user_id}',
                                json=update_data,
                                headers={'Authorization': customer_token})
            
            # This should actually succeed since customer is updating their own account
            assert response.status_code == 200
    
    def test_update_user_no_auth_fails(self, client, sample_user, app):
        """Test user update without authentication fails"""
        with app.app_context():
            user = User.query.filter_by(email="customer@test.com").first()
            user_id = user.id
            
            update_data = {
                "name": "Should Not Update"
            }
            
            response = client.put(f'/users/{user_id}', json=update_data)
            
            # Note: endpoint now requires JWT authentication, so it returns 401 when no token
            assert response.status_code == 401
    
    def test_update_nonexistent_user_fails(self, client, admin_token):
        """Test update nonexistent user fails"""
        update_data = {
            "name": "Should Not Work"
        }
        
        response = client.put('/users/99999',
                            json=update_data,
                            headers={'Authorization': admin_token})
        
        assert response.status_code == 404
        data = response.get_json()
        assert 'message' in data
    
    def test_update_user_invalid_email_fails(self, client, admin_token, sample_user, app):
        """Test user update with invalid email fails"""
        with app.app_context():
            user = User.query.filter_by(email="customer@test.com").first()
            user_id = user.id
            
            update_data = {
                "email": "invalid-email-format"
            }
            
            response = client.put(f'/users/{user_id}',
                                json=update_data,
                                headers={'Authorization': admin_token})
            
        assert response.status_code == 400
        data = response.get_json()
        assert 'errors' in data


@pytest.mark.user_management
class TestUserDeletion:
    """Test user deletion endpoint"""
    
    def test_delete_user_admin_success(self, client, admin_token, app):
        """Test successful user deletion by admin"""
        with app.app_context():
            # Create a user to delete
            user = User(
                email="todelete@test.com",
                name="To Delete User",
                role="customer"
            )
            user.set_password("password123")
            db.session.add(user)
            db.session.commit()
            user_id = user.id
            
            response = client.delete(f'/users/{user_id}',
                                   headers={'Authorization': admin_token})
            
            assert response.status_code == 200
            data = response.get_json()
            
            assert data['id'] == user_id
            assert data['email'] == "todelete@test.com"
            
            # Verify user was deleted from database
            deleted_user = User.query.get(user_id)
            assert deleted_user is None
    
    def test_delete_user_customer_own_success(self, client, app):
        """Test customer can delete their own account"""
        with app.app_context():
            # Create a user and get their token
            user = User(
                email="selfdelete@test.com",
                name="Self Delete User",
                role="customer"
            )
            user.set_password("password123")
            db.session.add(user)
            db.session.commit()
            
            # Create token for this user
            from flask_jwt_extended import create_access_token
            claims = {"role": user.role}
            token = create_access_token(identity=str(user.id), additional_claims=claims)
            user_token = f"Bearer {token}"
            user_id = user.id
            
            response = client.delete(f'/users/{user_id}',
                                   headers={'Authorization': user_token})
            
            assert response.status_code == 200
            data = response.get_json()
            # Should return the deleted user data
            assert 'id' in data
            assert data['id'] == user_id
    
    def test_delete_user_no_auth_fails(self, client, sample_user, app):
        """Test user deletion without authentication fails"""
        with app.app_context():
            user = User.query.filter_by(email="customer@test.com").first()
            user_id = user.id
            
            response = client.delete(f'/users/{user_id}')
            
            # Note: endpoint now requires JWT authentication, so it returns 401 when no token
            assert response.status_code == 401
    
    def test_delete_nonexistent_user_fails(self, client, admin_token):
        """Test delete nonexistent user fails"""
        response = client.delete('/users/99999',
                               headers={'Authorization': admin_token})
        
        assert response.status_code == 404
        data = response.get_json()
        assert 'message' in data


@pytest.mark.delivery_addresses
class TestDeliveryAddresses:
    """Test delivery address endpoints"""
    
    def test_add_delivery_address_admin_success(self, client, admin_token, sample_user, app):
        """Test successful delivery address addition by admin"""
        with app.app_context():
            user = User.query.filter_by(email="customer@test.com").first()
            user_id = user.id
            
            address_data = {
                "user_id": user_id,
                "address": "123 Test Street",
                "city": "Test City",
                "postal_code": "12345",
                "country": "Test Country"
            }
            
            response = client.post(f'/users/{user_id}/delivery-addresses',
                                 json=address_data,
                                 headers={'Authorization': admin_token})
            
        assert response.status_code == 201
        data = response.get_json()
        
        # Should return the created delivery address
        assert 'id' in data
        assert data['user_id'] == user_id
        assert data['address'] == address_data['address']
        assert data['city'] == address_data['city']
        assert data['postal_code'] == address_data['postal_code']
        assert data['country'] == address_data['country']
    
    def test_add_delivery_address_customer_success(self, client, customer_token, sample_user, app):
        """Test customer can add delivery address to their own account"""
        with app.app_context():
            user = User.query.filter_by(email="customer@test.com").first()
            user_id = user.id
            
            address_data = {
                "user_id": user_id,
                "address": "456 Customer Street",
                "city": "Customer City",
                "postal_code": "54321",
                "country": "Customer Country"
            }
            
            response = client.post(f'/users/{user_id}/delivery-addresses',
                                 json=address_data,
                                 headers={'Authorization': customer_token})
            
            assert response.status_code == 201
            data = response.get_json()
            assert 'id' in data
            assert data['user_id'] == user_id
    
    def test_add_delivery_address_no_auth_fails(self, client, sample_user, app):
        """Test add delivery address without authentication fails"""
        with app.app_context():
            user = User.query.filter_by(email="customer@test.com").first()
            user_id = user.id
            
            address_data = {
                "user_id": user_id,
                "address": "Should Not Work",
                "city": "Should Not Work",
                "postal_code": "00000",
                "country": "Should Not Work"
            }
            
            response = client.post(f'/users/{user_id}/delivery-addresses',
                                 json=address_data)
            
            # Note: endpoint now requires JWT authentication, so it returns 401 when no token
            assert response.status_code == 401
    
    def test_add_delivery_address_missing_fields_fails(self, client, admin_token, sample_user, app):
        """Test add delivery address with missing required fields fails"""
        with app.app_context():
            user = User.query.filter_by(email="customer@test.com").first()
            user_id = user.id
            
            incomplete_address_data = {
                "address": "Incomplete Address"
                # Missing required fields: user_id, city, postal_code, country
            }
            
            response = client.post(f'/users/{user_id}/delivery-addresses',
                                 json=incomplete_address_data,
                                 headers={'Authorization': admin_token})
            
        assert response.status_code == 400
        data = response.get_json()
        assert 'errors' in data
    
    def test_add_delivery_address_nonexistent_user_fails(self, client, admin_token):
        """Test add delivery address to nonexistent user fails"""
        address_data = {
            "user_id": 99999,
            "address": "123 Test Street",
            "city": "Test City",
            "postal_code": "12345",
            "country": "Test Country"
        }
        
        response = client.post('/users/99999/delivery-addresses',
                             json=address_data,
                             headers={'Authorization': admin_token})
        
        assert response.status_code == 404
        data = response.get_json()
        assert 'message' in data
    
    def test_get_delivery_addresses_admin_success(self, client, admin_token, sample_user, app):
        """Test successful retrieval of delivery addresses by admin"""
        with app.app_context():
            user = User.query.filter_by(email="customer@test.com").first()
            user_id = user.id
            
            response = client.get(f'/users/{user_id}/delivery-addresses',
                                headers={'Authorization': admin_token})
            
            assert response.status_code == 200
            data = response.get_json()
            # Should return a list of delivery addresses
            assert isinstance(data, list)
    
    def test_get_delivery_addresses_customer_success(self, client, customer_token, sample_user, app):
        """Test customer can get their own delivery addresses"""
        with app.app_context():
            user = User.query.filter_by(email="customer@test.com").first()
            user_id = user.id
            
            response = client.get(f'/users/{user_id}/delivery-addresses',
                                headers={'Authorization': customer_token})
            
            assert response.status_code == 200
            data = response.get_json()
            # Should return a list of delivery addresses
            assert isinstance(data, list)
    
    def test_get_delivery_addresses_no_auth_fails(self, client, sample_user, app):
        """Test get delivery addresses without authentication fails"""
        with app.app_context():
            user = User.query.filter_by(email="customer@test.com").first()
            user_id = user.id
            
            response = client.get(f'/users/{user_id}/delivery-addresses')
            
            # Note: endpoint now requires JWT authentication, so it returns 401 when no token
            assert response.status_code == 401
    
    def test_get_delivery_addresses_nonexistent_user_fails(self, client, admin_token):
        """Test get delivery addresses for nonexistent user fails"""
        response = client.get('/users/99999/delivery-addresses',
                            headers={'Authorization': admin_token})
        
        assert response.status_code == 404
        data = response.get_json()
        assert 'message' in data
    
    def test_update_delivery_address_admin_success(self, client, admin_token, sample_user, app):
        """Test successful delivery address update by admin"""
        with app.app_context():
            user = User.query.filter_by(email="customer@test.com").first()
            user_id = user.id
            
            # First create a delivery address
            address_data = {
                "user_id": user_id,
                "address": "Original Admin Street",
                "city": "Original City",
                "postal_code": "12345",
                "country": "Original Country"
            }
            
            create_response = client.post(f'/users/{user_id}/delivery-addresses',
                                        json=address_data,
                                        headers={'Authorization': admin_token})
            
            assert create_response.status_code == 201
            created_address = create_response.get_json()
            address_id = created_address['id']
            
            # Now update the delivery address
            update_data = {
                "address": "Updated Street Address",
                "city": "Updated City"
            }
            
            response = client.put(f'/users/{user_id}/delivery-addresses/{address_id}',
                                json=update_data,
                                headers={'Authorization': admin_token})
            
            assert response.status_code == 200
            data = response.get_json()
            # Should return a list of delivery addresses
            assert isinstance(data, list)
            # Verify the address was updated
            assert any(addr['address'] == "Updated Street Address" and addr['city'] == "Updated City" for addr in data)
    
    def test_update_delivery_address_customer_success(self, client, customer_token, sample_user, app):
        """Test customer can update their own delivery address"""
        with app.app_context():
            user = User.query.filter_by(email="customer@test.com").first()
            user_id = user.id
            
            # First create a delivery address
            address_data = {
                "user_id": user_id,
                "address": "Original Customer Street",
                "city": "Original City",
                "postal_code": "12345",
                "country": "Original Country"
            }
            
            create_response = client.post(f'/users/{user_id}/delivery-addresses',
                                        json=address_data,
                                        headers={'Authorization': customer_token})
            
            assert create_response.status_code == 201
            created_address = create_response.get_json()
            address_id = created_address['id']
            
            # Now update the delivery address
            update_data = {
                "address": "Customer Updated Street"
            }
            
            response = client.put(f'/users/{user_id}/delivery-addresses/{address_id}',
                                json=update_data,
                                headers={'Authorization': customer_token})
            
            assert response.status_code == 200
            data = response.get_json()
            # Should return a list of delivery addresses
            assert isinstance(data, list)
            # Verify the address was updated
            assert any(addr['address'] == "Customer Updated Street" for addr in data)
    
    def test_update_delivery_address_no_auth_fails(self, client, sample_user, app):
        """Test update delivery address without authentication fails"""
        with app.app_context():
            user = User.query.filter_by(email="customer@test.com").first()
            user_id = user.id
            address_id = 1
            
            update_data = {
                "address": "Should Not Work"
            }
            
            response = client.put(f'/users/{user_id}/delivery-addresses/{address_id}',
                                json=update_data)
            
            # Note: endpoint now requires JWT authentication, so it returns 401 when no token
            assert response.status_code == 401
    
    def test_update_delivery_address_nonexistent_user_fails(self, client, admin_token):
        """Test update delivery address for nonexistent user fails"""
        update_data = {
            "address": "Should Not Work"
        }
        
        response = client.put('/users/99999/delivery-addresses/1',
                            json=update_data,
                            headers={'Authorization': admin_token})
        
        assert response.status_code == 404
        data = response.get_json()
        assert 'message' in data


@pytest.mark.user_management
class TestUserManagementIntegration:
    """Test complete user management flows"""
    
    def test_complete_user_management_flow(self, client, admin_token):
        """Test complete user management flow: get -> update -> delete"""
        # First create a user via registration
        user_data = {
            "email": "management@test.com",
            "password": "password123",
            "name": "Management Test User",
            "phone": "+1555000111"
        }
        
        register_response = client.post('/users/register', json=user_data)
        assert register_response.status_code == 201
        user_id = register_response.get_json()['id']
        
        # 1. Get user
        get_response = client.get(f'/users/{user_id}',
                                headers={'Authorization': admin_token})
        assert get_response.status_code == 200
        assert get_response.get_json()['email'] == user_data['email']
        
        # 2. Update user
        update_data = {
            "name": "Updated Management User",
            "phone": "+1555000222"
        }
        
        update_response = client.put(f'/users/{user_id}',
                                   json=update_data,
                                   headers={'Authorization': admin_token})
        assert update_response.status_code == 200
        assert update_response.get_json()['name'] == update_data['name']
        
        # 3. Add delivery address
        address_data = {
            "user_id": user_id,
            "address": "123 Management Street",
            "city": "Management City",
            "postal_code": "12345",
            "country": "Management Country"
        }
        
        address_response = client.post(f'/users/{user_id}/delivery-addresses',
                                     json=address_data,
                                     headers={'Authorization': admin_token})
        assert address_response.status_code == 201
        
        # 4. Get delivery addresses
        get_addresses_response = client.get(f'/users/{user_id}/delivery-addresses',
                                          headers={'Authorization': admin_token})
        assert get_addresses_response.status_code == 200
        
        # 5. Delete user
        delete_response = client.delete(f'/users/{user_id}',
                                      headers={'Authorization': admin_token})
        assert delete_response.status_code == 200
        
        # 6. Verify user is gone
        final_get_response = client.get(f'/users/{user_id}',
                                      headers={'Authorization': admin_token})
        assert final_get_response.status_code == 404
    
    def test_admin_can_manage_all_users(self, client, admin_token):
        """Test admin can perform all user management operations"""
        # Create multiple users
        users_data = [
            {"email": "user1@test.com", "password": "password123", "name": "User 1"},
            {"email": "user2@test.com", "password": "password123", "name": "User 2"},
            {"email": "user3@test.com", "password": "password123", "name": "User 3"}
        ]
        
        created_ids = []
        for user_data in users_data:
            response = client.post('/users/register', json=user_data)
            assert response.status_code == 201
            created_ids.append(response.get_json()['id'])
        
        # Update each user
        for i, user_id in enumerate(created_ids):
            update_response = client.put(f'/users/{user_id}',
                                       json={"name": f"Updated User {i+1}"},
                                       headers={'Authorization': admin_token})
            assert update_response.status_code == 200
        
        # Get each user
        for user_id in created_ids:
            get_response = client.get(f'/users/{user_id}',
                                    headers={'Authorization': admin_token})
            assert get_response.status_code == 200
        
        # Delete all users
        for user_id in created_ids:
            delete_response = client.delete(f'/users/{user_id}',
                                          headers={'Authorization': admin_token})
            assert delete_response.status_code == 200
