from flask_migrate import history
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from models.ticket import Ticket
from services.ai_service import AIService
from extensions import db
import json
import warnings
warnings.filterwarnings('ignore')

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
            # Return empty days for the range
            date_range = pd.date_range(start=start_date.date(), end=end_date.date())
            result = []
            for date in date_range:
                result.append({
                    'date': date.strftime('%Y-%m-%d'),
                    'count': 0
                })
            return result
            
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
    def get_ticket_volume_by_type(days=30):
        """
        Get ticket volume history broken down by issue type.
        Returns: {date: str, Bug: int, Feature Request: int, Support: int, Task: int, total: int}
        """
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        tickets = Ticket.query.filter(Ticket.created_at >= start_date).all()
        
        if not tickets:
            date_range = pd.date_range(start=start_date.date(), end=end_date.date())
            result = []
            for date in date_range:
                result.append({
                    'date': date.strftime('%Y-%m-%d'),
                    'Bug': 0,
                    'Feature Request': 0,
                    'Support': 0,
                    'Task': 0,
                    'total': 0
                })
            return result
        
        # Create DataFrame with dates and types
        data = [{'created_at': t.created_at, 'issue_type': t.issue_type} for t in tickets if t.created_at]
        df = pd.DataFrame(data)
        df['date'] = df['created_at'].dt.date
        
        # Pivot by type
        type_counts = df.groupby(['date', 'issue_type']).size().unstack(fill_value=0)
        
        # Ensure all dates in range
        date_range = pd.date_range(start=start_date.date(), end=end_date.date())
        type_counts = type_counts.reindex(date_range, fill_value=0)
        
        # Ensure all types exist as columns
        for issue_type in ['Bug', 'Feature Request', 'Support', 'Task']:
            if issue_type not in type_counts.columns:
                type_counts[issue_type] = 0
        
        # Build result
        result = []
        for date_idx, row in type_counts.iterrows():
            total = int(row[['Bug', 'Feature Request', 'Support', 'Task']].sum())
            result.append({
                'date': date_idx.strftime('%Y-%m-%d'),
                'Bug': int(row.get('Bug', 0)),
                'Feature Request': int(row.get('Feature Request', 0)),
                'Support': int(row.get('Support', 0)),
                'Task': int(row.get('Task', 0)),
                'total': total
            })
        
        return result

    @staticmethod
    def forecast_future_volume(history, days_to_forecast=7):
        """
        Forecast using Exponential Smoothing as primary method.
        More stable and appropriate for business ticket data.
        """
        if len(history) < 3:
            # Not enough data, repeat last value
            last_count = history[-1]['count'] if history else 0
            last_date = datetime.strptime(history[-1]['date'], '%Y-%m-%d') if history else datetime.now()
            return [{'date': (last_date + timedelta(days=i+1)).strftime('%Y-%m-%d'), 
                    'count': int(last_count)} for i in range(days_to_forecast)]
        
        df = pd.DataFrame(history)
        df['date'] = pd.to_datetime(df['date'])
        series = df.set_index('date')['count'].astype(float)
        
        try:
            # Use ExponentialSmoothing as primary (conservative, stable)
            return AnalyticsService._forecast_exponential_smoothing(history, days_to_forecast)
        except Exception as e:
            print(f"ExponentialSmoothing failed: {e}, falling back to linear")
            return AnalyticsService._forecast_linear(history, days_to_forecast)

    @staticmethod
    def forecast_volume_by_type(history_by_type, days_to_forecast=7):
        """
        Forecast ticket volume by type.
        history_by_type: list of dicts with {date, Bug, Feature Request, Support, Task, total}
        Returns: list of dicts with same structure for forecasted dates
        """
        if len(history_by_type) < 3:
            last = history_by_type[-1] if history_by_type else {}
            last_date = datetime.strptime(last.get('date', datetime.now().strftime('%Y-%m-%d')), '%Y-%m-%d')
            return [{'date': (last_date + timedelta(days=i+1)).strftime('%Y-%m-%d'),
                     'Bug': int(last.get('Bug', 0)),
                     'Feature Request': int(last.get('Feature Request', 0)),
                     'Support': int(last.get('Support', 0)),
                     'Task': int(last.get('Task', 0)),
                     'total': int(last.get('total', 0))} for i in range(days_to_forecast)]
        
        forecast_result = []
        
        # Forecast each type separately
        for issue_type in ['Bug', 'Feature Request', 'Support', 'Task']:
            type_history = [{'date': h['date'], 'count': h[issue_type]} for h in history_by_type]
            type_forecast = AnalyticsService.forecast_future_volume(type_history, days_to_forecast)
            
            for i, forecast_item in enumerate(type_forecast):
                if i >= len(forecast_result):
                    forecast_result.append({
                        'date': forecast_item['date'],
                        'Bug': 0,
                        'Feature Request': 0,
                        'Support': 0,
                        'Task': 0
                    })
                forecast_result[i][issue_type] = forecast_item['count']
        
        # Calculate totals
        for item in forecast_result:
            item['total'] = item['Bug'] + item['Feature Request'] + item['Support'] + item['Task']
        
        return forecast_result

    @staticmethod
    def _forecast_exponential_smoothing(history, days_to_forecast):
        """Fallback to Exponential Smoothing if SARIMAX fails."""
        from statsmodels.tsa.holtwinters import ExponentialSmoothing
        
        if len(history) < 3:
            last_count = history[-1]['count'] if history else 0
            last_date = datetime.strptime(history[-1]['date'], '%Y-%m-%d') if history else datetime.now()
            return [{'date': (last_date + timedelta(days=i+1)).strftime('%Y-%m-%d'), 
                     'count': int(last_count)} for i in range(days_to_forecast)]
        
        df = pd.DataFrame(history)
        df['date'] = pd.to_datetime(df['date'])
        series = df.set_index('date')['count'].astype(float)
        
        try:
            seasonal = 7 if len(series) >= 14 else None
            if seasonal:
                model = ExponentialSmoothing(series, trend='add', seasonal='add', seasonal_periods=seasonal)
            else:
                model = ExponentialSmoothing(series, trend='add', seasonal=None)
            
            fitted = model.fit(optimized=True)
            forecast_vals = fitted.forecast(steps=days_to_forecast)
            
            last_date = series.index[-1]
            forecast = []
            for i, val in enumerate(forecast_vals):
                next_date = last_date + timedelta(days=i+1)
                forecast.append({
                    'date': next_date.strftime('%Y-%m-%d'),
                    'count': max(0, int(round(float(val))))
                })
            return forecast
        except Exception as e2:
            print(f"Exponential Smoothing also failed: {e2}, using linear fallback")
            return AnalyticsService._forecast_linear(history, days_to_forecast)

    @staticmethod
    def _forecast_linear(history, days_to_forecast):
        """Final fallback: simple linear regression."""
        if len(history) < 2:
            return []
        df = pd.DataFrame(history)
        df['day_index'] = range(len(df))
        x = df['day_index'].values
        y = df['count'].values
        A = np.vstack([x, np.ones(len(x))]).T
        m, b = np.linalg.lstsq(A, y, rcond=None)[0]
        
        last_date = datetime.strptime(history[-1]['date'], '%Y-%m-%d')
        forecast = []
        start_idx = len(df)
        for i in range(days_to_forecast):
            next_idx = start_idx + i
            predicted_count = m * next_idx + b
            next_date = last_date + timedelta(days=i+1)
            forecast.append({
                'date': next_date.strftime('%Y-%m-%d'),
                'count': max(0, int(round(predicted_count)))
            })
        return forecast

    @staticmethod
    def generate_insight(history, forecast):
        """
        Use AI to generate a text summary of the trend based on full user-selected history.
        """
        client = AIService.get_client()
        if not client:
            return "AI Insight unavailable (API Key missing)."

        # Calculate statistics from FULL history (user-selected period)
        counts = [h['count'] for h in history]
        avg_tickets = sum(counts) / len(counts) if counts else 0
        min_tickets = min(counts) if counts else 0
        max_tickets = max(counts) if counts else 0
        total_tickets = sum(counts)
        
        # Calculate trend from full period
        if len(counts) >= 2:
            first_half_avg = sum(counts[:len(counts)//2]) / (len(counts)//2) if len(counts)//2 > 0 else 0
            second_half_avg = sum(counts[len(counts)//2:]) / (len(counts) - len(counts)//2) if len(counts) - len(counts)//2 > 0 else 0
            trend = "increasing" if second_half_avg > first_half_avg else "decreasing"
            trend_change = round(((second_half_avg - first_half_avg) / first_half_avg * 100), 1) if first_half_avg > 0 else 0
        else:
            trend = "stable"
            trend_change = 0

        prompt = f"""
        Analyze the following ticket volume data and provide a brief executive summary (2-3 sentences).
        Explain the overall trend and what the forecast indicates.
        
        Historical Data Analysis (Full selected period):
        - Period length: {len(history)} days
        - Total tickets: {int(total_tickets)}
        - Average tickets/day: {avg_tickets:.1f}
        - Min tickets/day: {int(min_tickets)}
        - Max tickets/day: {int(max_tickets)}
        - Overall trend: {trend} ({trend_change:+.1f}%)
        
        Full Historical Data (dates and counts):
        {json.dumps(history)}
        
        Forecast (Next {len(forecast)} days):
        {json.dumps(forecast)}
        
        Output just a 2-3 sentence executive summary.
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