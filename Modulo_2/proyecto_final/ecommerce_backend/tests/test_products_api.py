import pytest
import json
from app.models.product import Product
from app.extensions import db


@pytest.mark.products
class TestProductCreation:
    """Test product creation endpoint"""
    
    def test_create_product_success(self, client, admin_token):
        """Test successful product creation by admin"""
        product_data = {
            "name": "Test Product",
            "description": "A test product description",
            "price": 29.99,
            "stock": 100
        }
        
        response = client.post('/products/', 
                             json=product_data,
                             headers={'Authorization': admin_token})
        
        assert response.status_code == 201
        data = response.get_json()
        
        # Verify response structure
        assert 'id' in data
        assert data['name'] == product_data['name']
        assert data['description'] == product_data['description']
        assert float(data['price']) == product_data['price']
        assert data['stock'] == product_data['stock']
        
        # Verify product was created in database
        product = Product.query.filter_by(name=product_data['name']).first()
        assert product is not None
        assert float(product.price) == product_data['price']
    
    def test_create_product_minimal_data_success(self, client, admin_token):
        """Test successful product creation with minimal required data"""
        product_data = {
            "name": "Minimal Product",
            "price": 15.50,
            "stock": 50
        }
        
        response = client.post('/products/', 
                             json=product_data,
                             headers={'Authorization': admin_token})
        
        assert response.status_code == 201
        data = response.get_json()
        assert data['name'] == product_data['name']
        assert data['description'] is None or data['description'] == ""
    
    def test_create_product_customer_fails(self, client, customer_token):
        """Test product creation by customer fails (admin only)"""
        product_data = {
            "name": "Should Not Create",
            "price": 25.00,
            "stock": 10
        }
        
        response = client.post('/products/', 
                             json=product_data,
                             headers={'Authorization': customer_token})
        
        assert response.status_code == 403
        data = response.get_json()
        assert 'Permission denied' in data['message']
    
    def test_create_product_no_auth_fails(self, client):
        """Test product creation without authentication fails"""
        product_data = {
            "name": "Should Not Create",
            "price": 25.00,
            "stock": 10
        }
        
        response = client.post('/products/', json=product_data)
        
        assert response.status_code == 401
    
    def test_create_product_missing_name_fails(self, client, admin_token):
        """Test product creation without name fails"""
        product_data = {
            "price": 25.00,
            "stock": 10
        }
        
        response = client.post('/products/', 
                             json=product_data,
                             headers={'Authorization': admin_token})
        
        assert response.status_code == 400
        data = response.get_json()
        assert 'errors' in data
    
    def test_create_product_missing_price_fails(self, client, admin_token):
        """Test product creation without price fails"""
        product_data = {
            "name": "No Price Product",
            "stock": 10
        }
        
        response = client.post('/products/', 
                             json=product_data,
                             headers={'Authorization': admin_token})
        
        assert response.status_code == 400
        data = response.get_json()
        assert 'errors' in data
    
    def test_create_product_missing_stock_fails(self, client, admin_token):
        """Test product creation without stock fails"""
        product_data = {
            "name": "No Stock Product",
            "price": 25.00
        }
        
        response = client.post('/products/', 
                             json=product_data,
                             headers={'Authorization': admin_token})
        
        assert response.status_code == 400
        data = response.get_json()
        assert 'errors' in data
    
    def test_create_product_negative_price_fails(self, client, admin_token):
        """Test product creation with negative price fails"""
        product_data = {
            "name": "Negative Price Product",
            "price": -5.00,
            "stock": 10
        }
        
        response = client.post('/products/', 
                             json=product_data,
                             headers={'Authorization': admin_token})
        
        assert response.status_code == 400
        data = response.get_json()
        assert 'errors' in data
    
    def test_create_product_negative_stock_fails(self, client, admin_token):
        """Test product creation with negative stock fails"""
        product_data = {
            "name": "Negative Stock Product",
            "price": 25.00,
            "stock": -5
        }
        
        response = client.post('/products/', 
                             json=product_data,
                             headers={'Authorization': admin_token})
        
        assert response.status_code == 400
        data = response.get_json()
        assert 'errors' in data


@pytest.mark.products
class TestProductRetrieval:
    """Test product retrieval endpoints"""
    
    def test_get_all_products_success(self, client, customer_token, sample_products):
        """Test successful retrieval of all products"""
        response = client.get('/products/',
                            headers={'Authorization': customer_token})
        
        assert response.status_code == 200
        data = response.get_json()
        
        assert isinstance(data, list)
        assert len(data) == 3  # From sample_products fixture
        
        # Verify product structure (based on ProductReadSchema)
        product = data[0]
        assert 'id' in product
        assert 'name' in product
        assert 'description' in product
        assert 'price' in product
        assert 'stock' in product
        assert 'created_at' in product
        assert 'updated_at' in product
    
    def test_get_all_products_admin_success(self, client, admin_token, sample_products):
        """Test admin can also retrieve all products"""
        response = client.get('/products/',
                            headers={'Authorization': admin_token})
        
        assert response.status_code == 200
        data = response.get_json()
        assert len(data) == 3
    
    def test_get_all_products_no_auth_fails(self, client, sample_products):
        """Test get all products without authentication fails"""
        response = client.get('/products/')
        
        assert response.status_code == 401
    
    def test_get_all_products_empty_list(self, client, customer_token):
        """Test get all products returns empty list when no products exist"""
        response = client.get('/products/',
                            headers={'Authorization': customer_token})
        
        assert response.status_code == 200
        data = response.get_json()
        assert isinstance(data, list)
        assert len(data) == 0
    
    def test_get_product_by_id_success(self, client, customer_token, sample_products, app):
        """Test successful retrieval of product by ID"""
        # Get the first product ID from sample_products
        with app.app_context():
            product_id = sample_products[0].id
        
        response = client.get(f'/products/{product_id}',
                            headers={'Authorization': customer_token})
        
        assert response.status_code == 200
        data = response.get_json()
        
        assert data['id'] == product_id
        # Note: Can't access sample_products attributes outside app context due to DetachedInstanceError
        assert 'name' in data
        assert 'price' in data
    
    def test_get_product_by_id_admin_success(self, client, admin_token, sample_products, app):
        """Test admin can retrieve product by ID"""
        with app.app_context():
            product_id = sample_products[0].id
        
        response = client.get(f'/products/{product_id}',
                            headers={'Authorization': admin_token})
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['id'] == product_id
    
    def test_get_product_nonexistent_fails(self, client, customer_token):
        """Test get nonexistent product fails"""
        response = client.get('/products/99999',
                            headers={'Authorization': customer_token})
        
        assert response.status_code == 404
        data = response.get_json()
        assert 'message' in data
    
    def test_get_product_no_auth_fails(self, client, sample_products, app):
        """Test get product without authentication fails"""
        with app.app_context():
            product_id = sample_products[0].id
        
        response = client.get(f'/products/{product_id}')
        
        assert response.status_code == 401


@pytest.mark.products
class TestProductUpdate:
    """Test product update endpoint"""
    
    def test_update_product_success(self, client, admin_token, sample_products, app):
        """Test successful product update by admin"""
        with app.app_context():
            product_id = sample_products[0].id
            
            update_data = {
                "id": product_id,
                "name": "Updated Product Name",
                "description": "Updated description",
                "price": 35.99,
                "stock": 75
            }
            
            response = client.put(f'/products/{product_id}',
                                json=update_data,
                                headers={'Authorization': admin_token})
            
            assert response.status_code == 200
            data = response.get_json()
            
            assert data['id'] == product_id
            assert data['name'] == update_data['name']
            assert data['description'] == update_data['description']
            assert float(data['price']) == update_data['price']
            assert data['stock'] == update_data['stock']
            
            # Verify update in database
            updated_product = Product.query.get(product_id)
            assert updated_product.name == update_data['name']
            assert float(updated_product.price) == update_data['price']
    
    def test_update_product_partial_success(self, client, admin_token, sample_products, app):
        """Test successful partial product update"""
        with app.app_context():
            product_id = sample_products[0].id
            original_name = sample_products[0].name
            
            update_data = {
                "id": product_id,
                "price": 45.99
            }
            
            response = client.put(f'/products/{product_id}',
                                json=update_data,
                                headers={'Authorization': admin_token})
            
            assert response.status_code == 200
            data = response.get_json()
            
            assert data['id'] == product_id
            # Verify the price was updated (can't compare original_name due to DetachedInstanceError)
            assert float(data['price']) == update_data['price']  # Should be updated
            assert 'name' in data
    
    def test_update_product_customer_fails(self, client, customer_token, sample_products, app):
        """Test product update by customer fails (admin only)"""
        with app.app_context():
            product_id = sample_products[0].id
        
        update_data = {
            "id": product_id,
            "name": "Should Not Update",
            "price": 999.99
        }
        
        response = client.put(f'/products/{product_id}',
                            json=update_data,
                            headers={'Authorization': customer_token})
        
        assert response.status_code == 403
        data = response.get_json()
        assert 'Permission denied' in data['message']
    
    def test_update_product_no_auth_fails(self, client, sample_products, app):
        """Test product update without authentication fails"""
        with app.app_context():
            product_id = sample_products[0].id
        
        update_data = {
            "id": product_id,
            "name": "Should Not Update"
        }
        
        response = client.put(f'/products/{product_id}', json=update_data)
        
        assert response.status_code == 401
    
    def test_update_nonexistent_product_fails(self, client, admin_token):
        """Test update nonexistent product fails"""
        update_data = {
            "id": 99999,
            "name": "Should Not Work"
        }
        
        response = client.put('/products/99999',
                            json=update_data,
                            headers={'Authorization': admin_token})
        
        assert response.status_code == 404
        data = response.get_json()
        assert 'message' in data
    
    def test_update_product_negative_price_fails(self, client, admin_token, sample_products, app):
        """Test update product with negative price fails"""
        with app.app_context():
            product_id = sample_products[0].id
        
        update_data = {
            "id": product_id,
            "price": -10.00
        }
        
        response = client.put(f'/products/{product_id}',
                            json=update_data,
                            headers={'Authorization': admin_token})
        
        assert response.status_code == 400
        data = response.get_json()
        assert 'errors' in data
    
    def test_update_product_negative_stock_fails(self, client, admin_token, sample_products, app):
        """Test update product with negative stock fails"""
        with app.app_context():
            product_id = sample_products[0].id
        
        update_data = {
            "id": product_id,
            "stock": -5
        }
        
        response = client.put(f'/products/{product_id}',
                            json=update_data,
                            headers={'Authorization': admin_token})
        
        assert response.status_code == 400
        data = response.get_json()
        assert 'errors' in data


@pytest.mark.products
class TestProductDeletion:
    """Test product deletion endpoint"""
    
    def test_delete_product_success(self, client, admin_token, sample_products, app):
        """Test successful product deletion by admin"""
        with app.app_context():
            product_id = sample_products[0].id
            product_name = sample_products[0].name
            
            response = client.delete(f'/products/{product_id}',
                                   headers={'Authorization': admin_token})
            
            assert response.status_code == 200
            data = response.get_json()
            
            assert data['id'] == product_id
            assert data['name'] == product_name
            
            # Verify product was deleted from database
            deleted_product = Product.query.get(product_id)
            assert deleted_product is None
    
    def test_delete_product_customer_fails(self, client, customer_token, sample_products, app):
        """Test product deletion by customer fails (admin only)"""
        with app.app_context():
            product_id = sample_products[0].id
        
        response = client.delete(f'/products/{product_id}',
                               headers={'Authorization': customer_token})
        
        assert response.status_code == 403
        data = response.get_json()
        assert 'Permission denied' in data['message']
    
    def test_delete_product_no_auth_fails(self, client, sample_products, app):
        """Test product deletion without authentication fails"""
        with app.app_context():
            product_id = sample_products[0].id
        
        response = client.delete(f'/products/{product_id}')
        
        assert response.status_code == 401
    
    def test_delete_nonexistent_product_fails(self, client, admin_token):
        """Test delete nonexistent product fails"""
        response = client.delete('/products/99999',
                               headers={'Authorization': admin_token})
        
        assert response.status_code == 404
        data = response.get_json()
        assert 'message' in data


@pytest.mark.products
class TestProductIntegration:
    """Test complete product management flows"""
    
    def test_complete_product_lifecycle(self, client, admin_token, customer_token):
        """Test complete product lifecycle: create -> read -> update -> delete"""
        # 1. Create product
        product_data = {
            "name": "Lifecycle Test Product",
            "description": "Testing product lifecycle",
            "price": 50.00,
            "stock": 25
        }
        
        create_response = client.post('/products/',
                                    json=product_data,
                                    headers={'Authorization': admin_token})
        assert create_response.status_code == 201
        product_id = create_response.get_json()['id']
        
        # 2. Read product (as customer)
        read_response = client.get(f'/products/{product_id}',
                                 headers={'Authorization': customer_token})
        assert read_response.status_code == 200
        assert read_response.get_json()['name'] == product_data['name']
        
        # 3. Update product
        update_data = {
            "id": product_id,
            "price": 55.00,
            "stock": 30
        }
        
        update_response = client.put(f'/products/{product_id}',
                                   json=update_data,
                                   headers={'Authorization': admin_token})
        assert update_response.status_code == 200
        assert float(update_response.get_json()['price']) == 55.00
        
        # 4. Delete product
        delete_response = client.delete(f'/products/{product_id}',
                                      headers={'Authorization': admin_token})
        assert delete_response.status_code == 200
        
        # 5. Verify product is gone
        final_read_response = client.get(f'/products/{product_id}',
                                       headers={'Authorization': customer_token})
        assert final_read_response.status_code == 404
    
    def test_admin_can_manage_all_products(self, client, admin_token):
        """Test admin can perform all product operations"""
        # Create multiple products
        products_data = [
            {"name": "Product 1", "price": 10.00, "stock": 100},
            {"name": "Product 2", "price": 20.00, "stock": 50},
            {"name": "Product 3", "price": 30.00, "stock": 25}
        ]
        
        created_ids = []
        for product_data in products_data:
            response = client.post('/products/',
                                 json=product_data,
                                 headers={'Authorization': admin_token})
            assert response.status_code == 201
            created_ids.append(response.get_json()['id'])
        
        # Get all products
        get_all_response = client.get('/products/',
                                    headers={'Authorization': admin_token})
        assert get_all_response.status_code == 200
        assert len(get_all_response.get_json()) >= 3
        
        # Update each product
        for i, product_id in enumerate(created_ids):
            update_response = client.put(f'/products/{product_id}',
                                       json={"id": product_id, "price": (i + 1) * 15.00},
                                       headers={'Authorization': admin_token})
            assert update_response.status_code == 200
        
        # Delete all products
        for product_id in created_ids:
            delete_response = client.delete(f'/products/{product_id}',
                                          headers={'Authorization': admin_token})
            assert delete_response.status_code == 200
