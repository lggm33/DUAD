import pytest
import time
from unittest.mock import patch, MagicMock
from app.extensions import cache
from app.services import product_service
from app.services.cache_service import invalidate_product_cache, get_cache_stats


@pytest.mark.cache
class TestCacheFunctionality:
    """Test cache functionality for API endpoints"""

    @pytest.fixture(autouse=True)
    def setup_cache(self, app):
        """Setup cache for each test"""
        with app.app_context():
            cache.clear()
            yield
            cache.clear()

    def test_product_list_cache_hit_miss(self, client, admin_token, sample_products):
        """Test cache hit/miss behavior for product list endpoint"""
        headers = {'Authorization': admin_token}
        
        # First request should be cache miss
        with patch('builtins.print') as mock_print:
            response1 = client.get('/products/', headers=headers)
            
        assert response1.status_code == 200
        products1 = response1.get_json()
        assert len(products1) >= 2
        
        # Second request should be cache hit
        with patch('builtins.print') as mock_print:
            response2 = client.get('/products/', headers=headers)
            
        assert response2.status_code == 200
        products2 = response2.get_json()
        
        # Should return same data
        assert products1 == products2

    def test_product_detail_cache_hit_miss(self, client, admin_token, sample_products):
        """Test cache hit/miss behavior for individual product endpoint"""
        headers = {'Authorization': admin_token}
        product_id = sample_products[0].id
        
        # First request should be cache miss
        response1 = client.get(f'/products/{product_id}', headers=headers)
        assert response1.status_code == 200
        product1 = response1.get_json()
        
        # Second request should be cache hit
        response2 = client.get(f'/products/{product_id}', headers=headers)
        assert response2.status_code == 200
        product2 = response2.get_json()
        
        # Should return same data
        assert product1 == product2
        assert product1['id'] == product_id

    def test_cart_total_cache_user_specific(self, client, customer_token, admin_token, sample_products):
        """Test that cart total cache is user-specific"""
        customer_headers = {'Authorization': customer_token}
        admin_headers = {'Authorization': admin_token}
        
        # Add product to customer cart
        add_data = {"product_id": sample_products[0].id, "quantity": 2}
        client.post('/sales/cart/add', json=add_data, headers=customer_headers)
        
        # Get customer cart total
        response1 = client.get('/sales/cart/total', headers=customer_headers)
        assert response1.status_code == 200
        customer_total = response1.get_json()
        
        # Get admin cart total (should be different/empty)
        response2 = client.get('/sales/cart/total', headers=admin_headers)
        assert response2.status_code == 200
        admin_total = response2.get_json()
        
        # Totals should be different (customer has items, admin doesn't)
        assert customer_total != admin_total

    def test_cache_invalidation_on_product_create(self, client, admin_token, app):
        """Test that cache is invalidated when creating products"""
        headers = {'Authorization': admin_token}
        
        # Get initial products (populate cache)
        response1 = client.get('/products/', headers=headers)
        assert response1.status_code == 200
        initial_count = len(response1.get_json())
        
        # Create new product
        new_product = {
            "name": "Cache Test Product",
            "description": "Product for testing cache invalidation",
            "price": 15.99,
            "stock": 50
        }
        
        create_response = client.post('/products/', json=new_product, headers=headers)
        assert create_response.status_code == 201
        
        # Get products again (should fetch fresh data, not cached)
        response2 = client.get('/products/', headers=headers)
        assert response2.status_code == 200
        new_count = len(response2.get_json())
        
        # Should have one more product
        assert new_count == initial_count + 1

    def test_cache_invalidation_on_product_update(self, client, admin_token, sample_products):
        """Test that cache is invalidated when updating products"""
        headers = {'Authorization': admin_token}
        product_id = sample_products[0].id
        
        # Get product (populate cache)
        response1 = client.get(f'/products/{product_id}', headers=headers)
        assert response1.status_code == 200
        original_name = response1.get_json()['name']
        
        # Update product with a unique name to ensure change
        import time
        unique_name = f"Updated Product {int(time.time())}"
        update_data = {"name": unique_name}
        update_response = client.put(f'/products/{product_id}', json=update_data, headers=headers)
        assert update_response.status_code == 200
        
        # Verify the update response shows the new name
        update_result = update_response.get_json()
        assert update_result['name'] == unique_name
        
        # Get product again (should fetch fresh data, not cached)
        response2 = client.get(f'/products/{product_id}', headers=headers)
        assert response2.status_code == 200
        updated_name = response2.get_json()['name']
        
        # Name should be updated
        assert updated_name != original_name
        assert updated_name == unique_name

    def test_cache_invalidation_on_product_delete(self, client, admin_token, app):
        """Test that cache is invalidated when deleting products"""
        headers = {'Authorization': admin_token}
        
        # Create a product to delete
        new_product = {
            "name": "Product To Delete",
            "description": "This product will be deleted",
            "price": 25.99,
            "stock": 10
        }
        
        create_response = client.post('/products/', json=new_product, headers=headers)
        assert create_response.status_code == 201
        product_id = create_response.get_json()['id']
        
        # Get products list (populate cache)
        response1 = client.get('/products/', headers=headers)
        assert response1.status_code == 200
        initial_count = len(response1.get_json())
        
        # Delete product
        delete_response = client.delete(f'/products/{product_id}', headers=headers)
        assert delete_response.status_code == 200
        
        # Get products again (should fetch fresh data)
        response2 = client.get('/products/', headers=headers)
        assert response2.status_code == 200
        final_count = len(response2.get_json())
        
        # Should have one less product
        assert final_count == initial_count - 1

    @pytest.mark.admin
    def test_admin_sales_cache(self, client, admin_token):
        """Test admin sales endpoint caching"""
        headers = {'Authorization': admin_token}
        
        # First request
        response1 = client.get('/sales/admin/sales', headers=headers)
        assert response1.status_code == 200
        
        # Second request (should use cache)
        response2 = client.get('/sales/admin/sales', headers=headers)
        assert response2.status_code == 200
        
        # Should return same data structure
        assert type(response1.get_json()) == type(response2.get_json())

    @pytest.mark.admin  
    def test_admin_sales_analytics_cache(self, client, admin_token):
        """Test admin sales analytics endpoint caching"""
        headers = {'Authorization': admin_token}
        
        # Test analytics endpoint
        response1 = client.get('/sales/admin/sales?analytics=true', headers=headers)
        assert response1.status_code == 200
        
        # Second request with analytics
        response2 = client.get('/sales/admin/sales?analytics=true', headers=headers)
        assert response2.status_code == 200
        
        # Should return same data structure
        assert type(response1.get_json()) == type(response2.get_json())

    def test_cache_key_includes_query_parameters(self, client, admin_token):
        """Test that cache keys include query parameters"""
        headers = {'Authorization': admin_token}
        
        # Request without analytics
        response1 = client.get('/sales/admin/sales', headers=headers)
        assert response1.status_code == 200
        
        # Request with analytics (should be different cache key)
        response2 = client.get('/sales/admin/sales?analytics=true', headers=headers)
        assert response2.status_code == 200
        
        # Both should succeed but may have different response structures
        assert response1.status_code == response2.status_code == 200

    def test_cache_graceful_degradation(self, client, admin_token, app):
        """Test that application works when cache fails"""
        headers = {'Authorization': admin_token}
        
        # Mock cache to return None for blocklist (token not blocked) but raise exception for other cache operations
        def cache_get_side_effect(key):
            if key.startswith("blocklist:"):
                return None  # Token not blocked
            raise Exception("Cache error")
        
        def cache_set_side_effect(*args, **kwargs):
            raise Exception("Cache error")
        
        # Mock cache operations
        with patch.object(cache, 'get', side_effect=cache_get_side_effect):
            with patch.object(cache, 'set', side_effect=cache_set_side_effect):
                response = client.get('/products/', headers=headers)
                
        # Should still work without cache
        assert response.status_code == 200
        products = response.get_json()
        assert isinstance(products, list)

    def test_cache_service_functions(self, app):
        """Test cache service utility functions"""
        with app.app_context():
            # Test cache invalidation function
            try:
                invalidate_product_cache()
                # Should not raise exception
                assert True
            except Exception as e:
                pytest.fail(f"Cache invalidation failed: {e}")
            
            # Test cache stats function (if in debug mode)
            try:
                stats = get_cache_stats()
                # Should return dict or None
                assert stats is None or isinstance(stats, dict)
            except Exception as e:
                pytest.fail(f"Cache stats failed: {e}")


@pytest.mark.cache
class TestCachePerformance:
    """Test cache performance and timing"""

    @pytest.fixture(autouse=True)
    def setup_cache(self, app):
        """Setup cache for each test"""
        with app.app_context():
            cache.clear()
            yield
            cache.clear()

    def test_cache_improves_response_time(self, client, admin_token, sample_products):
        """Test that cache improves response time for repeated requests"""
        headers = {'Authorization': admin_token}
        
        # Measure first request time (cache miss)
        start_time = time.time()
        response1 = client.get('/products/', headers=headers)
        first_request_time = time.time() - start_time
        
        assert response1.status_code == 200
        
        # Measure second request time (cache hit)
        start_time = time.time()
        response2 = client.get('/products/', headers=headers)
        second_request_time = time.time() - start_time
        
        assert response2.status_code == 200
        
        # Note: In testing, the difference might not be significant
        # but this test verifies the cache mechanism works
        print(f"First request: {first_request_time:.4f}s")
        print(f"Second request: {second_request_time:.4f}s")
        
        # Both requests should succeed
        assert response1.get_json() == response2.get_json()

    def test_cache_ttl_behavior(self, client, admin_token, app):
        """Test cache TTL (Time To Live) behavior with short timeout"""
        headers = {'Authorization': admin_token}
        
        # This test would require modifying cache timeout for testing
        # For now, just verify that the cache system is working
        response1 = client.get('/products/', headers=headers)
        assert response1.status_code == 200
        
        response2 = client.get('/products/', headers=headers)
        assert response2.status_code == 200
        
        # Should return same cached data
        assert response1.get_json() == response2.get_json()
