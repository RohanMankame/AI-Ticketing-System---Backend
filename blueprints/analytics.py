from flask import Blueprint, jsonify, request
from services.analytics_service import AnalyticsService

analytics_bp = Blueprint('analytics', __name__)

@analytics_bp.route('/', methods=['GET'])
def get_analytics():
    return jsonify({"message": "Analytics endpoint test"})

@analytics_bp.route('/forecast', methods=['GET'])
def get_forecast():
    try:
        # Read query params (or use defaults)
        days = int(request.args.get('days', 7))
        days_to_forecast = int(request.args.get('days_to_forecast', 7))
        
        # 1. Get History (exactly `days` worth)
        history = AnalyticsService.get_ticket_volume_history(days=days)
        
        # 2. Generate Forecast (exactly `days_to_forecast` entries)
        forecast = AnalyticsService.forecast_future_volume(history, days_to_forecast=days_to_forecast)
        
        # 3. Get AI Insight
        insight = AnalyticsService.generate_insight(history, forecast)
        
        return jsonify({
            "history": history,
            "forecast": forecast,
            "explanation": insight,
            "metadata": {
                "history_days": len(history),
                "forecast_days": len(forecast)
            }
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500