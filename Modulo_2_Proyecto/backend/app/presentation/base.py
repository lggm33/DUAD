from typing import Any, TypeVar, Generic, Protocol

T = TypeVar("T")

class Presenter:
    """
    Base class for presenters.
    
    A presenter is responsible for converting domain entities or ORM objects
    into dictionaries suitable for API responses.
    """
    
    @staticmethod
    def public(entity: Any) -> dict[str, Any]:
        """
        Convert an entity to its public representation.
        To be overridden by subclasses.
        """
        raise NotImplementedError("Subclasses must implement public()")

    @staticmethod
    def collection(entities: list[Any]) -> list[dict[str, Any]]:
        """
        Convert a collection of entities to their public representation.
        """
        # This is a generic implementation that calls public() for each entity.
        # However, since public() is static and meant to be overridden, 
        # we might need a different approach if we want to use this in subclasses.
        # For now, let's keep it simple.
        raise NotImplementedError("Subclasses should implement collection() if needed or use a base helper.")
