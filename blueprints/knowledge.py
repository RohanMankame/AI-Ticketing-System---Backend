from flask import Blueprint, jsonify, request
from models.knowledge import KnowledgeArticle
from services.ai_service import AIService
from extensions import db
import json

knowledge_bp = Blueprint('knowledge', __name__)



@knowledge_bp.route('/', methods=['POST'])
def add_article():
    """
    add a knowledge base article.
    Expected JSON body: { "title": "Article Title", "content": "Article content", "url": "http://example.com", "type": "solution", "tags": ["tag1", "tag2"] }
    """
    data = request.get_json()
    if not data or 'title' not in data or 'content' not in data:
        return jsonify({"error": "Title and content are required"}), 400

    try:
        # Generate embedding
        embedding_vector = AIService.generate_embedding(data['title'] + "\n" + data['content'])
        embedding_str = json.dumps(embedding_vector) if embedding_vector else None

        # Handle tags: accept as list or CSV string
        tags_input = data.get('tags', [])
        if isinstance(tags_input, list):
            tags_str = ",".join(tags_input)
        else:
            tags_str = str(tags_input) if tags_input else None

        article = KnowledgeArticle(
            title=data['title'],
            content=data['content'],
            url=data.get('url'),
            type=data.get('type', 'solution'),
            tags=tags_str,
            embedding=embedding_str
        )
        db.session.add(article)
        db.session.commit()
        return jsonify(article.to_dict()), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500



@knowledge_bp.route('/', methods=['GET'])
def get_all_articles():
    """
    Get all knowledge base articles.
    """
    try:
        articles = KnowledgeArticle.query.all()
        return jsonify([a.to_dict() for a in articles]), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500



@knowledge_bp.route('/<int:article_id>', methods=['GET'])
def get_article(article_id):
    """
    Get a knowledge base article by its ID.
    """
    try:
        article = KnowledgeArticle.query.get(article_id)
        if not article:
            return jsonify({"error": "Article not found"}), 404
        return jsonify(article.to_dict()), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500




@knowledge_bp.route('/search', methods=['GET'])
def search_knowledge():
    """
    Search knowledge base articles based on a query string.
    Query param: q=search text
    Returns a list of relevant articles.
    """
    query = request.args.get('q')
    if not query:
        return jsonify({"error": "Query parameter 'q' is required"}), 400

    try:
        results = AIService.find_relevant_knowledge(query)
        return jsonify(results), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@knowledge_bp.route('/draft', methods=['POST'])
def draft_article():
    """
    Draft a knowledge base article based on resolved tickets.
    """
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


@knowledge_bp.route('/<int:article_id>', methods=['DELETE'])
def delete_article(article_id):
    """
    Delete an article by its ID.
    """
    try:
        article = KnowledgeArticle.query.get(article_id)
        if not article:
            return jsonify({"error": "Article not found"}), 404
            
        db.session.delete(article)
        db.session.commit()
        return jsonify({"message": "Article deleted successfully"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
