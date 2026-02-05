from extensions import db
from datetime import datetime

class Ticket(db.Model):
    __tablename__ = 'tickets'

    id = db.Column(db.Integer, primary_key=True)
    issue_key = db.Column(db.String(50), unique=True, nullable=False)
    issue_id = db.Column(db.Integer, nullable=True)
    issue_type = db.Column(db.String(50))
    summary = db.Column(db.Text)
    assignee = db.Column(db.String(100))
    assignee_id = db.Column(db.String(100))
    reporter = db.Column(db.String(100))
    reporter_id = db.Column(db.String(100))
    priority = db.Column(db.String(50))
    status = db.Column(db.String(50))
    resolution = db.Column(db.String(100))
    created_at = db.Column(db.DateTime)
    updated_at = db.Column(db.DateTime)
    due_date = db.Column(db.DateTime)

    # AI Analysis Fields
    auto_category = db.Column(db.String(100))
    auto_tags = db.Column(db.Text)  
    sentiment_score = db.Column(db.Float)
    auto_solution = db.Column(db.Text)  
    embedding = db.Column(db.Text)

    def to_dict(self):
        # Parse auto_tags CSV into list
        tag_list = []
        if self.auto_tags:
            tag_list = [t.strip() for t in str(self.auto_tags).split(',') if t.strip()]

        return {
            'id': self.id,
            'issue_key': self.issue_key,
            'issue_id': self.issue_id,
            'issue_type': self.issue_type,
            'summary': self.summary,
            'assignee': self.assignee,
            'assignee_id': self.assignee_id,
            'reporter': self.reporter,
            'reporter_id': self.reporter_id,
            'status': self.status,
            'priority': self.priority,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'due_date': self.due_date.isoformat() if self.due_date else None,
            'auto_category': self.auto_category,
            'auto_tags': tag_list,
            'sentiment_score': self.sentiment_score,
            'auto_solution': self.auto_solution,
        }