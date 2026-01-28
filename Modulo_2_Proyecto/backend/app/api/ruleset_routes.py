"""
API routes for RulesetTemplate management.
"""
from flask import Blueprint, jsonify, g

from app.extensions import db

from app.domain.games.ruleset_repository import RulesetRepository
from app.domain.games.ruleset_service import RulesetService
from app.domain.games.exceptions import (
    RulesetNotFoundError,
    RulesetAccessDeniedError,
)

from app.presentation.games.ruleset_presenters import RulesetPresenter

from app.presentation.common.auth import auth_required
from app.presentation.common.errors import error_response

ruleset_bp = Blueprint("ruleset", __name__, url_prefix="/api/v1/ruleset-templates")

def get_ruleset_service() -> RulesetService:
    """
    Create and configure the ruleset service with all dependencies.

    This factory function instantiates the ruleset repository and
    creates the service with it.

    Note: Session is NOT passed to services. Transactions are handled
    automatically by Flask's request teardown.

    Returns:
        Configured RulesetService instance
    """
    session = db.get_session()
    ruleset_repo = RulesetRepository(session)
    return RulesetService(ruleset_repo)


# ============================================================================
# ENDPOINTS
# ============================================================================

@ruleset_bp.get("")
@auth_required
def list_ruleset_templates():
    """
    List all ruleset templates available to the authenticated user.

    Returns system-provided templates and templates created by the user.

    Returns:
        200: List of available ruleset templates with their base rules
    """
    service = get_ruleset_service()

    templates = service.get_available_templates(g.auth_user.user_id)

    return jsonify(RulesetPresenter.templates_collection(templates)), 200


@ruleset_bp.get("/<int:template_id>")
@auth_required
def get_ruleset_template(template_id: int):
    """
    Get a specific ruleset template by ID.

    Returns the template with its base_rules if the user has access.
    System templates are publicly accessible, user templates require ownership.

    Returns:
        200: Template details with base_rules
        404: Template not found
        403: Access denied to user-created template
    """
    service = get_ruleset_service()

    try:
        template = service.get_template_by_id(template_id, g.auth_user.user_id)
        return jsonify(RulesetPresenter.template_with_rules(template)), 200

    except RulesetNotFoundError as e:
        return error_response("NOT_FOUND", str(e), status_code=404)
    except RulesetAccessDeniedError as e:
        return error_response("FORBIDDEN", str(e), status_code=403)

