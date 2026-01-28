from typing import Any
from app.domain.notes.models import GameNote
from app.presentation.base import Presenter

class NotePresenter(Presenter):
    @staticmethod
    def public(note: GameNote) -> dict[str, Any]:
        return {
            "id": note.id,
            "game_id": note.game_id,
            "user_id": note.user_id,
            "title": note.title,
            "content": note.content,
            "visibility": note.visibility.value,
            "created_at": note.created_at.isoformat(),
            "updated_at": note.updated_at.isoformat(),
        }
    
    @staticmethod
    def collection(notes: list[GameNote]) -> list[dict[str, Any]]:
        return [NotePresenter.public(note) for note in notes]
