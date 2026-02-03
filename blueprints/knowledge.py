from flask import Blueprint, jsonify, request
from models.knowledge import KnowledgeArticle
from services.ai_service import AIService
from extensions import db
import json

knowledge_bp = Blueprint('knowledge', __name__)


# Add Article
@knowledge_bp.route('/', methods=['POST'])
def add_article():
    data = request.get_json()
    if not data or 'title' not in data or 'content' not in data:
        return jsonify({"error": "Title and content are required"}), 400

    try:
        # Generate embedding
        embedding_vector = AIService.generate_embedding(data['title'] + "\n" + data['content'])
        embedding_str = json.dumps(embedding_vector) if embedding_vector else None

        article = KnowledgeArticle(
            title=data['title'],
            content=data['content'],
            url=data.get('url'),
            type=data.get('type', 'manual'),
            embedding=embedding_str
        )
        db.session.add(article)
        db.session.commit()
        return jsonify(article.to_dict()), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# Get All Articles
@knowledge_bp.route('/', methods=['GET'])
def get_all_articles():
    try:
        articles = KnowledgeArticle.query.all()
        return jsonify([a.to_dict() for a in articles]), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# Search Knowledge
@knowledge_bp.route('/search', methods=['GET'])
def search_knowledge():
    query = request.args.get('q')
    if not query:
        return jsonify({"error": "Query parameter 'q' is required"}), 400

    try:
        results = AIService.find_relevant_knowledge(query)
        return jsonify(results), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# Draft Article for single ticket or group of tickets
@knowledge_bp.route('/draft', methods=['POST'])
def draft_article():
    data = request.get_json()
    ticket_ids = data.get('ticket_ids')
    if not ticket_ids or not isinstance(ticket_ids, list):
        return jsonify({"error": "ticket_ids list is required"}), 400

    try:
        draft = AIService.draft_article_from_tickets(ticket_ids)
        if not draft:
            return jsonify({"error": "Could not generate draft"}), 500
        return jsonify(draft), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
