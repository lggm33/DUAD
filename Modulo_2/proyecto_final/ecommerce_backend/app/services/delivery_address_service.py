import app.repos.delivery_address_repo as delivery_address_repo
from app.utils.exceptions import (
    DeliveryAddressNotFoundError,
    AppError,
    RepoError
)

def add_delivery_address(user_id: int, data: dict):
    return delivery_address_repo.add_delivery_address(user_id, data)

def get_delivery_addresses_by_user_id(user_id: int):
    return delivery_address_repo.get_delivery_addresses(user_id)

def update_delivery_address(delivery_address_id: int, data: dict):
    return delivery_address_repo.update_delivery_address(delivery_address_id, data)

def delete_delivery_address(delivery_address_id: int):
    return delivery_address_repo.delete_delivery_address(delivery_address_id)

def get_delivery_address_by_id(delivery_address_id: int):
    return delivery_address_repo.get_delivery_address_by_id(delivery_address_id)