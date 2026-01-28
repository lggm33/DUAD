from typing import Optional
from sqlalchemy.orm import Session
from app.domain.notes.models import GameNote, NoteVisibility

class NoteRepository:
    def __init__(self, session: Session) -> None:
        self._session = session
    
    def create(self, note: GameNote) -> GameNote:
        self._session.add(note)
        self._session.flush()
        return note
    
    def get_by_id(self, note_id: int) -> Optional[GameNote]:
        return self._session.query(GameNote).filter_by(id=note_id).first()
    
    def get_game_shared_notes(self, game_id: int) -> list[GameNote]:
        return (
            self._session.query(GameNote)
            .filter_by(game_id=game_id, visibility=NoteVisibility.SHARED)
            .order_by(GameNote.created_at.desc())
            .all()
        )
    
    def get_user_private_notes(self, game_id: int, user_id: int) -> list[GameNote]:
        return (
            self._session.query(GameNote)
            .filter_by(game_id=game_id, user_id=user_id, visibility=NoteVisibility.PRIVATE)
            .order_by(GameNote.created_at.desc())
            .all()
        )
    
    def update(self, note: GameNote) -> GameNote:
        self._session.flush()
        return note
    
    def delete(self, note: GameNote) -> None:
        self._session.delete(note)
        self._session.flush()
