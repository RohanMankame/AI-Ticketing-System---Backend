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

    def to_dict(self):
        return {
            'id': self.id,
            'issue_key': self.issue_key,
            'issue_id': self.issue_id,
            'issue_type': self.issue_type,
            'summary': self.summary,
            'assignee': self.assignee,
            'status': self.status,
            'priority': self.priority,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'due_date': self.due_date.isoformat() if self.due_date else None
        }
