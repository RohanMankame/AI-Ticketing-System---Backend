from flask import Blueprint, jsonify, request
from services.ticket_service import TicketService
from services.ai_service import AIService
from models.ticket import Ticket
from extensions import db

tickets_bp = Blueprint('tickets', __name__)


# Get all tickets
@tickets_bp.route('/', methods=['GET'])
def get_tickets():
    try:
        tickets = Ticket.query.all()
        return jsonify([ticket.to_dict() for ticket in tickets]), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500



# Analyze a ticket, set auto fields
@tickets_bp.route('/<int:ticket_id>/analyze', methods=['POST'])
def analyze_ticket(ticket_id):
    ticket = Ticket.query.get(ticket_id)
    if not ticket:
        return jsonify({"error": "Ticket not found"}), 404
    
    try:
        # 1. Categorize
        analysis = AIService.classify_ticket(ticket.summary)
        if analysis:
            ticket.auto_category = analysis.get('category')
            # Handle potential list or string for tags
            tags = analysis.get('tags')
            if isinstance(tags, list):
                ticket.auto_tags = ",".join(tags)
            else:
                ticket.auto_tags = str(tags)
            ticket.sentiment_score = analysis.get('sentiment')
        
        # 2. Embedding
        emb = AIService.generate_embedding(ticket.summary)
        if emb:
            import json
            ticket.embedding = json.dumps(emb)
        
        db.session.commit()
        return jsonify(ticket.to_dict()), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Suggest solution for a ticket
@tickets_bp.route('/<int:ticket_id>/suggest-solution', methods=['GET'])
def suggest_solution(ticket_id):
    try:
        # Get Ticket
        ticket = Ticket.query.get(ticket_id)
        if not ticket:
             return jsonify({"error": "Ticket not found"}), 404

        # 1. Get AI Suggestion based on similar tickets
        suggestion = AIService.suggest_solution(ticket_id)
        
        # 2. Search Knowledge Base
        relevant_docs = AIService.find_relevant_knowledge(ticket.summary)
        
        return jsonify({
            "ai_suggestion": suggestion,
            "relevant_knowledge": relevant_docs
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# get similar tickets
@tickets_bp.route('/<int:ticket_id>/similar', methods=['GET'])
def get_similar_tickets(ticket_id):
    try:
        similar_tickets = AIService.find_similar_tickets(ticket_id)
        return jsonify(similar_tickets), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500



# Import tickets from CSV
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

