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
    def forecast_future_volume(history, days_to_forecast=7):
        """
        Forecast using SARIMAX (Seasonal ARIMA with eXogenous variables).
        Handles trends, seasonality, and irregular patterns.
        """
        if len(history) < 10:
            # Not enough data for SARIMAX, fallback to last value repeat
            last_count = history[-1]['count'] if history else 0
            last_date = datetime.strptime(history[-1]['date'], '%Y-%m-%d') if history else datetime.now()
            return [{'date': (last_date + timedelta(days=i+1)).strftime('%Y-%m-%d'), 
                     'count': int(last_count)} for i in range(days_to_forecast)]
        
        df = pd.DataFrame(history)
        df['date'] = pd.to_datetime(df['date'])
        series = df.set_index('date')['count'].astype(float)
        
        try:
            from statsmodels.tsa.statespace.sarimax import SARIMAX
            
            # SARIMAX parameters: (p, d, q) x (P, D, Q, s)
            # p, d, q = AR, differencing, MA order
            # P, D, Q, s = Seasonal AR, differencing, MA, and seasonal period
            # For weekly seasonality (7 days), use s=7
            
            seasonal_period = 7 if len(series) >= 14 else None
            
            if seasonal_period and len(series) >= 50:
                # Full SARIMAX with seasonality
                order = (1, 1, 1)
                seasonal_order = (1, 1, 1, seasonal_period)
                model = SARIMAX(series, order=order, seasonal_order=seasonal_order, 
                               enforce_stationarity=False, enforce_invertibility=False)
            elif len(series) >= 20:
                # Simpler SARIMAX without full seasonality
                order = (1, 1, 1)
                seasonal_order = (0, 0, 0, 0)
                model = SARIMAX(series, order=order, seasonal_order=seasonal_order, 
                               enforce_stationarity=False)
            else:
                # Minimal ARIMA for small datasets
                order = (1, 0, 1)
                seasonal_order = (0, 0, 0, 0)
                model = SARIMAX(series, order=order, seasonal_order=seasonal_order, 
                               enforce_stationarity=False)
            
            # Fit the model
            results = model.fit(disp=False, maxiter=200)
            
            # Forecast
            forecast_result = results.get_forecast(steps=days_to_forecast)
            forecast_vals = forecast_result.predicted_mean
            
            # Convert to results
            last_date = series.index[-1]
            forecast = []
            for i, val in enumerate(forecast_vals):
                next_date = last_date + timedelta(days=i+1)
                forecast.append({
                    'date': next_date.strftime('%Y-%m-%d'),
                    'count': max(0, int(round(float(val))))
                })
            return forecast
            
        except Exception as e:
            print(f"SARIMAX failed: {e}, falling back to exponential smoothing")
            return AnalyticsService._forecast_exponential_smoothing(history, days_to_forecast)

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
        Use AI to generate a text summary of the trend.
        """
        client = AIService.get_client()
        if not client:
            return "AI Insight unavailable (API Key missing)."

        prompt = f"""
        Analyze the following ticket volume data and provide a brief executive summary (2-3 sentences).
        Explain the current trend and the forecast.
        
        History (Last days summary):
        {json.dumps(history[-7:])} (Showing last 7 days for brevity)
        
        Forecast (Next days):
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