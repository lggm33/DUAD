from typing import Optional, List
from sqlalchemy.exc import SQLAlchemyError
from app.extensions import db
from app.models.product import Product
from app.utils.exceptions import RepoError

def create_product(data: dict) -> Product:
    try:
        product = Product(**data)
        db.session.add(product)
        db.session.commit()
        return product
    except SQLAlchemyError as e:
        db.session.rollback()
        raise RepoError(str(e))

def get_by_id(product_id: int) -> Optional[Product]:
    return db.session.get(Product, product_id)

def get_by_name(name: str) -> Optional[Product]:
    return Product.query.filter_by(name=name).first()

def get_all() -> List[Product]:
    return Product.query.all()

def update_product(product_id: int, data: dict) -> Optional[Product]:
    product = get_by_id(product_id)
    if not product:
        return None
    product.update(data)
    db.session.commit()
    return product

def delete_product(product_id: int) -> Optional[Product]:
    product = get_by_id(product_id)
    if not product:
        return None
    db.session.delete(product)
    db.session.commit()
    return product

    
