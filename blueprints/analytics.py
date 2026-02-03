from flask import Blueprint, jsonify
from services.analytics_service import AnalyticsService

analytics_bp = Blueprint('analytics', __name__)

@analytics_bp.route('/', methods=['GET'])
def get_analytics():
    return jsonify({"message": "Analytics endpoint test"})

@analytics_bp.route('/forecast', methods=['GET'])
def get_forecast():
    try:
        # 1. Get History
        history = AnalyticsService.get_ticket_volume_history(days=30)
        
        # 2. Generate Forecast
        forecast = AnalyticsService.forecast_future_volume(history, days_to_forecast=7)
        
        # 3. Get AI Insight
        insight = AnalyticsService.generate_insight(history, forecast)
        
        return jsonify({
            "history": history,
            "forecast": forecast,
            "explanation": insight
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
