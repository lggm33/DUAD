"""
API routes for RulesetTemplate management.
"""

from flask import Blueprint, jsonify, g

from app.presentation.common.auth import auth_required
from app.presentation.common.errors import error_response
from app.presentation.games.ruleset_presenters import RulesetPresenter
from app.domain.games.ruleset_repository import RulesetRepository
from app.extensions import db


ruleset_bp = Blueprint("ruleset", __name__, url_prefix="/api/v1/ruleset-templates")


def get_ruleset_repository() -> RulesetRepository:
    """Factory function to create RulesetRepository with current session."""
    session = db.get_session()
    return RulesetRepository(session)


@ruleset_bp.get("")
@auth_required
def list_ruleset_templates():
    """
    List all ruleset templates available to the authenticated user.
    
    Returns system-provided templates and templates created by the user.
    """
    ruleset_repo = get_ruleset_repository()
    
    templates = ruleset_repo.get_available_for_user(g.auth_user.user_id)
    
    return jsonify(RulesetPresenter.templates_collection(templates)), 200


@ruleset_bp.get("/<int:template_id>")
@auth_required
def get_ruleset_template(template_id: int):
    """
    Get a specific ruleset template by ID.
    
    Returns the template with its base_rules if the user has access.
    """
    ruleset_repo = get_ruleset_repository()
    
    template = ruleset_repo.get_by_id(template_id)
    
    if template is None:
        return error_response(
            "TEMPLATE_NOT_FOUND",
            "Ruleset template not found",
            status_code=404,
        )
    
    # Check access: system templates are public, user templates require ownership
    if not template.is_system_provided:
        if template.created_by_user_id != g.auth_user.user_id:
            return error_response(
                "FORBIDDEN",
                "You don't have access to this template",
                status_code=403,
            )
    
    return jsonify(RulesetPresenter.template_with_rules(template)), 200

