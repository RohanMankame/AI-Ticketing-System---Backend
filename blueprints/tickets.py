from flask import Blueprint, jsonify

tickets_bp = Blueprint('tickets', __name__)

@tickets_bp.route('/', methods=['GET'])
def get_tickets():
    return jsonify({"message": "Tickets endpoint test"})
