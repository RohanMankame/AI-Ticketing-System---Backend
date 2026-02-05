from extensions import db
from datetime import datetime

class KnowledgeArticle(db.Model):
    __tablename__ = 'knowledge_articles'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    url = db.Column(db.String(500)) 
    type = db.Column(db.String(50), default='solution') 
    tags = db.Column(db.Text)  # NEW: store as CSV
    embedding = db.Column(db.Text) 
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        
        tag_list = []
        if self.tags:
            tag_list = [t.strip() for t in str(self.tags).split(',') if t.strip()]

        return {
            'id': self.id,
            'title': self.title,
            'content': self.content,
            'url': self.url,
            'type': self.type,
            'tags': tag_list, 
            'created_at': self.created_at.isoformat()
        }
