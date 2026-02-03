from extensions import db
from datetime import datetime

class KnowledgeArticle(db.Model):
    __tablename__ = 'knowledge_articles'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    url = db.Column(db.String(500)) 
    type = db.Column(db.String(50), default='solution') 
    embedding = db.Column(db.Text) 
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'content': self.content,
            'url': self.url,
            'type': self.type,
            'created_at': self.created_at.isoformat()
        }
