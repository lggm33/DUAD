from typing import Optional, Any
from app.domain.notes.models import GameNote, NoteVisibility
from app.domain.notes.note_repository import NoteRepository
from app.domain.games.game_repository import GameRepository
from app.domain.games.game_membership_repository import GameMembershipRepository
from app.domain.games.game_service import GameService
from app.domain.games.models import GameMembershipStatus
from app.domain.notes.exceptions import (
    NoteNotFoundError,
    NoteAccessDeniedError,
    NoteValidationError
)
from app.domain.auth.models import AuthUser
from app.domain.games.exceptions import GameNotFoundError

class NoteService:
    def __init__(
        self,
        note_repository: NoteRepository,
        game_repository: GameRepository,
        game_membership_repository: GameMembershipRepository,
        game_service: GameService
    ) -> None:
        self._note_repository = note_repository
        self._game_repository = game_repository
        self._game_membership_repository = game_membership_repository
        self._game_service = game_service

    def create_note(
        self,
        game_id: int,
        user_id: int,
        title: str,
        content: str,
        visibility: NoteVisibility,
        auth_user: AuthUser
    ) -> GameNote:
        # 1. Validar juego existe
        game = self._game_repository.get_game_by_id(game_id)
        if not game:
            raise GameNotFoundError("Game not found")

        # 2. Validar membresía activa
        membership = self._game_membership_repository.get_game_membership_by_game_id_and_user_id(
            game_id, user_id
        )
        if not membership or membership.status != GameMembershipStatus.ACTIVE:
            raise NoteAccessDeniedError("User is not an active member of this game")

        # 3. Si visibility=SHARED, validar que es DM
        if visibility == NoteVisibility.SHARED:
            self._game_service.verify_dm_permissions(game, auth_user)

        # 4. Validar contenido
        if not title or len(title.strip()) == 0:
            raise NoteValidationError("Title is required")
        if len(title) > 255:
            raise NoteValidationError("Title is too long (max 255 characters)")
        if not content or len(content.strip()) == 0:
            raise NoteValidationError("Content is required")

        note = GameNote(
            game_id=game_id,
            user_id=user_id,
            title=title.strip(),
            content=content.strip(),
            visibility=visibility
        )
        return self._note_repository.create(note)

    def get_game_notes(self, game_id: int, auth_user: AuthUser) -> dict[str, list[GameNote]]:
        # 1. Validar membresía activa
        membership = self._game_membership_repository.get_game_membership_by_game_id_and_user_id(
            game_id, auth_user.user_id
        )
        if not membership or membership.status != GameMembershipStatus.ACTIVE:
            raise NoteAccessDeniedError("User is not an active member of this game")

        shared_notes = self._note_repository.get_game_shared_notes(game_id)
        private_notes = self._note_repository.get_user_private_notes(game_id, auth_user.user_id)

        return {
            "shared": shared_notes,
            "private": private_notes
        }

    def get_note_by_id(self, note_id: int, game_id: int, auth_user: AuthUser) -> GameNote:
        note = self._note_repository.get_by_id(note_id)
        if not note or note.game_id != game_id:
            raise NoteNotFoundError("Note not found")

        # Validar acceso: si es PRIVATE, verificar que es el autor
        if note.visibility == NoteVisibility.PRIVATE and note.user_id != auth_user.user_id:
            raise NoteAccessDeniedError("You don't have access to this private note")

        return note

    def update_note(
        self,
        note_id: int,
        game_id: int,
        auth_user: AuthUser,
        title: Optional[str] = None,
        content: Optional[str] = None,
        visibility: Optional[NoteVisibility] = None
    ) -> GameNote:
        note = self.get_note_by_id(note_id, game_id, auth_user)

        # Solo el autor puede editar
        if note.user_id != auth_user.user_id:
            raise NoteAccessDeniedError("Only the author can edit this note")

        if title is not None:
            if not title or len(title.strip()) == 0:
                raise NoteValidationError("Title is required")
            if len(title) > 255:
                raise NoteValidationError("Title is too long (max 255 characters)")
            note.title = title.strip()

        if content is not None:
            if not content or len(content.strip()) == 0:
                raise NoteValidationError("Content is required")
            note.content = content.strip()

        if visibility is not None:
            if visibility == NoteVisibility.SHARED:
                game = self._game_repository.get_game_by_id(game_id)
                self._game_service.verify_dm_permissions(game, auth_user)
            note.visibility = visibility

        return self._note_repository.update(note)

    def delete_note(self, note_id: int, game_id: int, auth_user: AuthUser) -> None:
        note = self.get_note_by_id(note_id, game_id, auth_user)

        # Solo el autor puede eliminar
        if note.user_id != auth_user.user_id:
            raise NoteAccessDeniedError("Only the author can delete this note")

        self._note_repository.delete(note)
