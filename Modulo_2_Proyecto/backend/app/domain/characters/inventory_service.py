"""
Service for inventory management operations.

Handles all inventory-related business logic including
item addition, updates, and deletion with proper validation.
"""

from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy.orm.attributes import flag_modified

from app.domain.characters.character_repository import CharacterRepository
from app.domain.characters.exceptions import (
    CharacterNotFoundError,
    CharacterAccessDeniedError,
    InventoryItemNotFoundError,
)


class InventoryService:
    """Service for inventory operations."""

    def __init__(
        self,
        character_repository: CharacterRepository,
    ) -> None:
        self._character_repo = character_repository

    def get_inventory(self, character_id: int, user_id: int) -> list[dict]:
        """
        Get all inventory items for a character.

        Args:
            character_id: The character ID
            user_id: The requesting user ID

        Returns:
            List of inventory items

        Raises:
            CharacterNotFoundError: If character not found
            CharacterAccessDeniedError: If user doesn't own the character
        """
        character = self._character_repo.get_by_id(character_id)

        if not character:
            raise CharacterNotFoundError("Character not found")

        self._verify_character_ownership(character, user_id)

        character_data = character.data if character.data else {}
        inventory = character_data.get("inventory", [])

        return self._validate_inventory(inventory)

    def add_item(
        self,
        character_id: int,
        user_id: int,
        name: str,
        description: str,
        quantity: int,
    ) -> dict:
        """
        Add a new item to the character's inventory.

        Args:
            character_id: The character ID
            user_id: The requesting user ID
            name: Item name
            description: Item description
            quantity: Item quantity

        Returns:
            The created item with its generated ID

        Raises:
            CharacterNotFoundError: If character not found
            CharacterAccessDeniedError: If user doesn't own the character
        """
        character = self._character_repo.get_by_id(character_id)

        if not character:
            raise CharacterNotFoundError("Character not found")

        self._verify_character_ownership(character, user_id)

        # Generate unique ID for the item
        item_id = str(uuid.uuid4())

        new_item = {
            "id": item_id,
            "name": name.strip(),
            "description": description.strip(),
            "quantity": quantity,
        }

        # Get current inventory and add new item
        character_data = character.data.copy() if character.data else {}
        inventory = character_data.get("inventory", [])
        inventory.append(new_item)
        character_data["inventory"] = inventory

        # Update character data
        character.data = character_data
        flag_modified(character, "data")

        return new_item

    def update_item(
        self,
        character_id: int,
        user_id: int,
        item_id: str,
        name: str | None = None,
        description: str | None = None,
        quantity: int | None = None,
    ) -> dict:
        """
        Update an existing inventory item.

        Args:
            character_id: The character ID
            user_id: The requesting user ID
            item_id: The item ID
            name: New name (optional)
            description: New description (optional)
            quantity: New quantity (optional)

        Returns:
            The updated item

        Raises:
            CharacterNotFoundError: If character not found
            CharacterAccessDeniedError: If user doesn't own the character
            InventoryItemNotFoundError: If item not found
        """
        character = self._character_repo.get_by_id(character_id)

        if not character:
            raise CharacterNotFoundError("Character not found")

        self._verify_character_ownership(character, user_id)

        # Find and update the item
        character_data = character.data.copy() if character.data else {}
        inventory = character_data.get("inventory", [])
        inventory = self._validate_inventory(inventory)

        item_found = False
        updated_item = {}
        for item in inventory:
            if item.get("id") == item_id:
                if name is not None:
                    item["name"] = name.strip()
                if description is not None:
                    item["description"] = description.strip()
                if quantity is not None:
                    item["quantity"] = quantity
                item_found = True
                updated_item = item
                break

        if not item_found:
            raise InventoryItemNotFoundError("Item not found in inventory")

        character_data["inventory"] = inventory

        # Update character data
        character.data = character_data
        flag_modified(character, "data")

        return updated_item

    def delete_item(
        self,
        character_id: int,
        user_id: int,
        item_id: str,
    ) -> None:
        """
        Delete an item from the character's inventory.

        Args:
            character_id: The character ID
            user_id: The requesting user ID
            item_id: The item ID

        Raises:
            CharacterNotFoundError: If character not found
            CharacterAccessDeniedError: If user doesn't own the character
            InventoryItemNotFoundError: If item not found
        """
        character = self._character_repo.get_by_id(character_id)

        if not character:
            raise CharacterNotFoundError("Character not found")

        self._verify_character_ownership(character, user_id)

        # Find and remove the item
        character_data = character.data.copy() if character.data else {}
        inventory = character_data.get("inventory", [])
        inventory = self._validate_inventory(inventory)

        initial_length = len(inventory)
        inventory = [item for item in inventory if item.get("id") != item_id]

        if len(inventory) == initial_length:
            raise InventoryItemNotFoundError("Item not found in inventory")

        character_data["inventory"] = inventory

        # Update character data
        character.data = character_data
        flag_modified(character, "data")

    def _validate_inventory(self, inventory: list) -> list[dict]:
        """
        Validate and sanitize inventory structure.

        Filters out invalid items (non-dict entries).

        Args:
            inventory: Raw inventory list

        Returns:
            List of valid inventory items
        """
        valid_inventory = []
        for item in inventory:
            if isinstance(item, dict):
                valid_inventory.append(item)
        return valid_inventory

    def _verify_character_ownership(self, character: Any, user_id: int) -> None:
        """
        Verify that the user owns the character.

        Args:
            character: The character object
            user_id: The user ID to verify

        Raises:
            CharacterAccessDeniedError: If user doesn't own the character
        """
        if character.user_id != user_id:
            raise CharacterAccessDeniedError(
                "You can only modify your own character's inventory"
            )
