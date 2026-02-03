import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from models.ticket import Ticket
from services.ai_service import AIService
from extensions import db
import json

class AnalyticsService:
    @staticmethod
    def get_ticket_volume_history(days=30):
        """
        Aggregate ticket counts by day for the last N days.
        """
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        # Query tickets created in range
        tickets = Ticket.query.filter(Ticket.created_at >= start_date).all()
        
        # Create a DataFrame
        data = [{'created_at': t.created_at} for t in tickets if t.created_at]
        if not data:
            return []
            
        df = pd.DataFrame(data)
        df['date'] = df['created_at'].dt.date
        
        # Group by date and count
        daily_counts = df.groupby('date').size().reset_index(name='count')
        
        # Ensure all dates in range are present (fill gaps with 0)
        date_range = pd.date_range(start=start_date.date(), end=end_date.date())
        daily_counts.set_index('date', inplace=True)
        daily_counts = daily_counts.reindex(date_range, fill_value=0).reset_index()
        daily_counts.rename(columns={'index': 'date'}, inplace=True)
        
        # Convert to list of dicts
        result = []
        for _, row in daily_counts.iterrows():
            result.append({
                'date': row['date'].strftime('%Y-%m-%d'),
                'count': int(row['count'])
            })
            
        return result

    @staticmethod
    def forecast_future_volume(history, days_to_forecast=7):
        """
        Simple linear forecast based on recent history.
        """
        if len(history) < 2:
            return []
            
        df = pd.DataFrame(history)
        df['day_index'] = range(len(df))
        
        # Simple Linear Regression (y = mx + b)
        x = df['day_index'].values
        y = df['count'].values
        
        # Calculate slope (m) and intercept (b)
        A = np.vstack([x, np.ones(len(x))]).T
        m, b = np.linalg.lstsq(A, y, rcond=None)[0]
        
        # Forecast
        last_date = datetime.strptime(history[-1]['date'], '%Y-%m-%d')
        forecast = []
        
        start_idx = len(df)
        for i in range(days_to_forecast):
            next_idx = start_idx + i
            predicted_count = m * next_idx + b
            next_date = last_date + timedelta(days=i+1)
            
            forecast.append({
                'date': next_date.strftime('%Y-%m-%d'),
                'count': max(0, round(predicted_count)) # No negative tickets
            })
            
        return forecast

    @staticmethod
    def generate_insight(history, forecast):
        """
        Use AI to generate a text summary of the trend.
        """
        client = AIService.get_client()
        if not client:
            return "AI Insight unavailable (API Key missing)."

        prompt = f"""
        Analyze the following ticket volume data and provide a brief executive summary (2-3 sentences).
        Explain the current trend and the forecast.
        
        History (Last 30 days summary):
        {json.dumps(history[-7:])} (Showing last 7 days for brevity)
        
        Forecast (Next 7 days):
        {json.dumps(forecast)}
        
        Output just the text summary.
        """

        try:
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a data analyst."},
                    {"role": "user", "content": prompt}
                ]
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"Error generating insight: {str(e)}"
