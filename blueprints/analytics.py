from flask import Blueprint, jsonify

analytics_bp = Blueprint('analytics', __name__)

@analytics_bp.route('/', methods=['GET'])
def get_analytics():
    return jsonify({"message": "Analytics endpoint test"})
