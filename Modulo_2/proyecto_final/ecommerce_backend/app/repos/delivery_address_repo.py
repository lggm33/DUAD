from app.extensions import db
from app.models.delivery_address import DeliveryAddress
from app.utils.exceptions import RepoError, NotFoundError
from sqlalchemy.exc import SQLAlchemyError

def add_delivery_address(user_id: int, data: dict):
    try:
        delivery_address = DeliveryAddress(
            user_id=user_id,
            address=data["address"],
            city=data["city"],
            postal_code=data["postal_code"],
            country=data["country"])
        db.session.add(delivery_address)
        db.session.commit()
        return delivery_address
    except SQLAlchemyError as e:
        db.session.rollback()
        raise RepoError(str(e))

def get_delivery_addresses(user_id: int):
    try:
        return DeliveryAddress.query.filter_by(user_id=user_id).all()
    except SQLAlchemyError as e:
        raise RepoError(str(e))

def get_delivery_address_by_id(delivery_address_id: int):
    try:
        return DeliveryAddress.query.get(delivery_address_id)
    except SQLAlchemyError as e:
        raise RepoError(str(e))

def update_delivery_address(delivery_address_id: int, data: dict):
    delivery_address = get_delivery_address_by_id(delivery_address_id)
    if not delivery_address:
        raise NotFoundError()
    try:
        # Only update fields that are provided
        if "address" in data:
            delivery_address.address = data["address"]
        if "city" in data:
            delivery_address.city = data["city"]
        if "postal_code" in data:
            delivery_address.postal_code = data["postal_code"]
        if "country" in data:
            delivery_address.country = data["country"]
        db.session.commit()
        return delivery_address
    except SQLAlchemyError as e:
        db.session.rollback()
        raise RepoError(str(e))

def delete_delivery_address(delivery_address_id: int):
    try:
        delivery_address = get_delivery_address_by_id(delivery_address_id)
        if not delivery_address:
            raise NotFoundError()
        db.session.delete(delivery_address)
        db.session.commit()
        return delivery_address
    except SQLAlchemyError as e:
        db.session.rollback()
        raise RepoError(str(e))