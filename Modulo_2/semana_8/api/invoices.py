from flask import Blueprint, jsonify, Response
from auth import require_auth

# Create blueprint for invoices endpoints
invoices_bp = Blueprint('invoices', __name__)

# Initialize managers (will be passed from main)
db_manager = None

def init_invoices_bp(db_mgr):
    """Initialize the invoices blueprint with managers"""
    global db_manager
    db_manager = db_mgr

@invoices_bp.route('/invoices', methods=['GET'])
@require_auth()
def get_user_invoices(current_user):
    """Get current user's invoices - requires valid token"""
    try:
        user_id = current_user['id']
        invoices = db_manager.get_invoices_by_user_id(user_id)
        invoices_list = []
        for invoice in invoices:
            invoices_list.append({
                'id': invoice[0],
                'user_id': invoice[1],
                'product_id': invoice[2],
                'quantity': invoice[3],
                'total_amount': invoice[4]
            })
        return jsonify(invoices=invoices_list)
    except Exception as e:
        return Response(status=500, response="Error retrieving invoices")

@invoices_bp.route('/invoices/all', methods=['GET'])
@require_auth('admin')
def get_all_invoices(current_user):
    """Get all invoices - requires admin role"""
    try:
        invoices = db_manager.get_all_invoices()
        invoices_list = []
        for invoice in invoices:
            invoices_list.append({
                'id': invoice[0],
                'user_id': invoice[1],
                'product_id': invoice[2],
                'quantity': invoice[3],
                'total_amount': invoice[4]
            })
        return jsonify(invoices=invoices_list)
    except Exception as e:
        return Response(status=500, response="Error retrieving all invoices")
