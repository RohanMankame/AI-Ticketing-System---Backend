from flask import Blueprint, jsonify, request
from services.analytics_service import AnalyticsService

analytics_bp = Blueprint('analytics', __name__)

@analytics_bp.route('/', methods=['GET'])
def analytics_root():
    return jsonify({"message": "Analytics API"}), 200

@analytics_bp.route('/forecast', methods=['GET'])
def forecast_volume():
    """
    Forecast total ticket volume.
    Query params: days=30 (history window), days_to_forecast=7 (prediction length)
    """
    days = request.args.get('days', 30, type=int)
    days_to_forecast = request.args.get('days_to_forecast', 7, type=int)
    
    try:
        history = AnalyticsService.get_ticket_volume_history(days)
        forecast = AnalyticsService.forecast_future_volume(history, days_to_forecast)
        explanation = AnalyticsService.generate_insight(history, forecast)
        
        return jsonify({
            "period": f"Last {days} days",
            "forecast_window": f"Next {days_to_forecast} days",
            "history": history,
            "forecast": forecast,
            "explanation": explanation
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@analytics_bp.route('/forecast-by-type', methods=['GET'])
def forecast_volume_by_type():
    """
    Forecast ticket volume broken down by type (Bug, Feature Request, Support, Task).
    Query params: days=30 (history window), days_to_forecast=7 (prediction length)
    """
    days = request.args.get('days', 30, type=int)
    days_to_forecast = request.args.get('days_to_forecast', 7, type=int)
    
    try:
        history = AnalyticsService.get_ticket_volume_by_type(days)
        forecast = AnalyticsService.forecast_volume_by_type(history, days_to_forecast)
        
        return jsonify({
            "period": f"Last {days} days",
            "forecast_window": f"Next {days_to_forecast} days",
            "history": history,
            "forecast": forecast,
            "breakdown": {
                "Bug": "Critical issues and defects",
                "Feature Request": "New feature requests",
                "Support": "User support questions",
                "Task": "Internal tasks and improvements"
            }
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500