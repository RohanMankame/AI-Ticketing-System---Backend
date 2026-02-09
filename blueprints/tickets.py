from flask import Blueprint, jsonify, request
from services.ticket_service import TicketService
from services.ai_service import AIService
from models.ticket import Ticket
from extensions import db

tickets_bp = Blueprint('tickets', __name__)



@tickets_bp.route('/', methods=['GET'])
def get_tickets():
    """
    Get all tickets.
    """
    try:
        tickets = Ticket.query.all()
        return jsonify([ticket.to_dict() for ticket in tickets]), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    

@tickets_bp.route('/<int:ticket_id>', methods=['GET'])
def get_ticket(ticket_id):
    """
    Get a ticket by its ID.
    """
    try:
        ticket = Ticket.query.get(ticket_id)
        if not ticket:
            return jsonify({"error": "Ticket not found"}), 404
        return jsonify(ticket.to_dict()), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500




@tickets_bp.route('/<int:ticket_id>/analyze', methods=['POST'])
def analyze_ticket(ticket_id):
    """
    Analyze a ticket, set auto fields.
    """
    ticket = Ticket.query.get(ticket_id)
    if not ticket:
        return jsonify({"error": "Ticket not found"}), 404
    
    try:
        # Categorize
        analysis = AIService.classify_ticket(ticket.summary)
        if analysis:
            ticket.auto_category = analysis.get('category')
            tags = analysis.get('tags')
            if isinstance(tags, list):
                ticket.auto_tags = ",".join(tags)
            else:
                ticket.auto_tags = str(tags)
            ticket.sentiment_score = analysis.get('sentiment')
        
        #  Embedding
        emb = AIService.generate_embedding(ticket.summary)
        if emb:
            import json
            ticket.embedding = json.dumps(emb)
        
        # Generate AI solution (NEW)
        suggestion = AIService.suggest_solution(ticket_id)
        if suggestion and suggestion.get('suggested_solution'):
            ticket.auto_solution = suggestion['suggested_solution']
        
        db.session.commit()
        return jsonify(ticket.to_dict()), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
    

@tickets_bp.route('/<int:ticket_id>/suggest-solution', methods=['GET'])
def suggest_solution(ticket_id):
    """
    Suggest a solution for a ticket based on AI analysis and relevant knowledge base articles.
    """
    try:
        # Get Ticket
        ticket = Ticket.query.get(ticket_id)
        if not ticket:
             return jsonify({"error": "Ticket not found"}), 404

        # Get AI Suggestion based on similar tickets
        suggestion = AIService.suggest_solution(ticket_id)
        
        # Search Knowledge Base
        relevant_docs = AIService.find_relevant_knowledge(ticket.summary)
        
        return jsonify({
            "ai_suggestion": suggestion,
            "relevant_knowledge": relevant_docs
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500



@tickets_bp.route('/<int:ticket_id>/similar', methods=['GET'])
def get_similar_tickets(ticket_id):
    """
    Get similar tickets based on embedding similarity.
    Returns a list of similar tickets with their similarity score.
    """
    try:
        similar_tickets = AIService.find_similar_tickets(ticket_id)
        return jsonify(similar_tickets), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500




@tickets_bp.route('/import', methods=['POST'])
def import_tickets():
    """
    Import tickets from a CSV file.
    """
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





@tickets_bp.route('/tags', methods=['GET'])
def get_all_ticket_tags():
    """
    Get all unique tags from analyzed tickets with their occurrence count.
    """
    try:
        tags = AIService.get_all_ticket_tags()
        return jsonify({
            "total_unique_tags": len(tags),
            "tags": tags
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@tickets_bp.route('/tags/<tag>', methods=['GET'])
def get_tickets_by_tag(tag):
    """
    Get all tickets that have a specific tag.
    Query params: none required
    """
    try:
        result = AIService.get_tickets_by_tag(tag)
        return jsonify(result), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500