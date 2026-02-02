from flask import Blueprint, jsonify, request
from services.ticket_service import TicketService

tickets_bp = Blueprint('tickets', __name__)

from models.ticket import Ticket

@tickets_bp.route('/', methods=['GET'])
def get_tickets():
    try:
        tickets = Ticket.query.all()
        return jsonify([ticket.to_dict() for ticket in tickets]), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500



@tickets_bp.route('/import', methods=['POST'])
def import_tickets():
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400
    
    file = request.files['file']
    
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400
        
    if file:
        try:
            result = TicketService.process_csv_upload(file)
            return jsonify(result), 200
        except Exception as e:
            return jsonify({"error": str(e)}), 500

