from extensions import db
from models.ticket import Ticket
import pandas as pd
from datetime import datetime

class TicketService:
    @staticmethod
    def process_csv_upload(file):
        try:
            # Read CSV
            df = pd.read_csv(file)
            
            # Normalize column names: lowercase and strip whitespace
            df.columns = [c.strip().lower() for c in df.columns]
            
            tickets_processed = 0
            
            for _, row in df.iterrows():
                issue_key = row.get('issue_key')
                if not issue_key or pd.isna(issue_key):
                    continue
                    
                # Parse dates
                created_at = TicketService._parse_date(row.get('created_at'))
                updated_at = TicketService._parse_date(row.get('updated_at'))
                due_date = TicketService._parse_date(row.get('due_date'))
                
                # Check if ticket exists
                ticket = Ticket.query.filter_by(issue_key=issue_key).first()
                
                if not ticket:
                    ticket = Ticket(issue_key=issue_key)
                    db.session.add(ticket)
                
                # Update fields
                ticket.issue_id = row.get('issue_id') if pd.notna(row.get('issue_id')) else None
                ticket.issue_type = row.get('issue_type')
                ticket.summary = row.get('summary')
                ticket.assignee = row.get('assignee')
                ticket.assignee_id = row.get('assignee_id')
                ticket.reporter = row.get('reporter')
                ticket.reporter_id = row.get('reporter_id')
                ticket.priority = row.get('priority')
                ticket.status = row.get('status')
                ticket.resolution = row.get('resolution') if pd.notna(row.get('resolution')) else None
                ticket.created_at = created_at
                ticket.updated_at = updated_at
                ticket.due_date = due_date
                
                tickets_processed += 1
            
            db.session.commit()
            return {"message": f"Successfully processed {tickets_processed} tickets", "count": tickets_processed}
            
        except Exception as e:
            db.session.rollback()
            raise e

    @staticmethod
    def _parse_date(date_str):
        if pd.isna(date_str) or not date_str:
            return None
        try:
            # Try format: YYYY-MM-DD HH:MM:SS
            return datetime.strptime(str(date_str).strip(), '%Y-%m-%d %H:%M:%S')
        except ValueError:
            try:
                # Fallback: use pandas to parse
                return pd.to_datetime(date_str).to_pydatetime()
            except:
                return None