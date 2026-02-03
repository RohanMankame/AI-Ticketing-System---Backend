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
            
            # Map CSV columns to model fields
            column_mapping = {
                'Issue key': 'issue_key',
                'Issue id': 'issue_id',
                'Issue Type': 'issue_type',
                'Summary': 'summary',
                'Assignee': 'assignee',
                'Assignee Id': 'assignee_id',
                'Reporter': 'reporter',
                'Reporter Id': 'reporter_id',
                'Priority': 'priority',
                'Status': 'status',
                'Resolution': 'resolution',
                'Created': 'created_at',
                'Updated': 'updated_at',
                'Due date': 'due_date'
            }
            
            # so that column names match mapping keys
            df.columns = [c.strip() for c in df.columns]
            
            tickets_processed = 0
            
            for _, row in df.iterrows():
                issue_key = row.get('Issue key')
                if not issue_key:
                    continue
                    
                # Parse dates
                created_at = TicketService._parse_date(row.get('Created'))
                updated_at = TicketService._parse_date(row.get('Updated'))
                due_date = TicketService._parse_date(row.get('Due date'))
                
                # Check if ticket exists
                ticket = Ticket.query.filter_by(issue_key=issue_key).first()
                
                if not ticket:
                    ticket = Ticket(issue_key=issue_key)
                    db.session.add(ticket)
                
                # Update fields
                ticket.issue_id = row.get('Issue id') if pd.notna(row.get('Issue id')) else None
                ticket.issue_type = row.get('Issue Type')
                ticket.summary = row.get('Summary')
                ticket.assignee = row.get('Assignee')
                ticket.assignee_id = row.get('Assignee Id')
                ticket.reporter = row.get('Reporter')
                ticket.reporter_id = row.get('Reporter Id')
                ticket.priority = row.get('Priority')
                ticket.status = row.get('Status')
                ticket.resolution = row.get('Resolution') if pd.notna(row.get('Resolution')) else None
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
            # Format date
            return datetime.strptime(date_str, '%d-%m-%Y %H:%M')
        except ValueError:
            try:
                return pd.to_datetime(date_str).to_pydatetime()
            except:
                return None
