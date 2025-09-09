import app.repos.product_repo as product_repo
from app.utils.exceptions import (
    ProductNotFoundError,
    ProductNameInUseError,
    AppError,
    RepoError
)
from app.utils.cache_decorators import cached_response
from app.services.cache_service import invalidate_product_cache

def create_product(data: dict):
    try:
        if product_repo.get_by_name(data["name"]):
            raise ProductNameInUseError()
        product = product_repo.create_product(data)
        # Invalidate cache after creating product
        invalidate_product_cache()
        return product
    except product_repo.RepoError as e:
        print(f"Unexpected error while creating product: {e}")
        raise AppError(f"Could not create product: {e}")

# CRÍTICO - Cache largo para productos individuales (1 hora)
@cached_response(timeout=3600, key_prefix="products.get_by_id")
def get_product_by_id(product_id: int):
    product = product_repo.get_by_id(product_id)
    if not product:
        raise ProductNotFoundError()
    return product

# CRÍTICO - Cache largo para catálogo de productos (30 min)
@cached_response(timeout=1800, key_prefix="products.get_all")
def get_all_products():
    return product_repo.get_all()

def update_product(product_id: int, data: dict):
    updated_product = product_repo.update_product(product_id, data)
    if not updated_product:
        raise ProductNotFoundError()
    # Invalidate cache after updating product
    invalidate_product_cache()
    return updated_product

def delete_product(product_id: int):
    deleted_product = product_repo.delete_product(product_id)
    if not deleted_product:
        raise ProductNotFoundError()
    # Invalidate cache after deleting product
    invalidate_product_cache()
    return deleted_product