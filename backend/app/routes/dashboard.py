from flask import Blueprint, request
from flask_jwt_extended import jwt_required
from app.services.dashboard_service import DashboardService
from app.utils.decorators import role_required
from app.utils.helpers import error_response, success_response

dashboard_bp = Blueprint('dashboard', __name__)


@dashboard_bp.route('/summary', methods=['GET'])
@jwt_required()
@role_required(['admin'])
def get_summary():
    """
    Today's clinic snapshot.
    GET /api/v1/dashboard/summary
    admin only.
    """
    summary = DashboardService.get_summary()
    return success_response(summary, 200)


@dashboard_bp.route('/revenue', methods=['GET'])
@jwt_required()
@role_required(['admin'])
def get_revenue():
    """
    Revenue timeseries with consultation vs test breakdown.
    GET /api/v1/dashboard/revenue?period=30days
    admin only.
    """
    period = request.args.get('period', '30days')
    if period not in ['7days', '30days', '90days']:
        return error_response(
            "Invalid period. Use: 7days, 30days, or 90days", 400
        )

    revenue = DashboardService.get_revenue(period)
    return success_response(revenue, 200)


@dashboard_bp.route('/department-stats', methods=['GET'])
@jwt_required()
@role_required(['admin'])
def get_department_stats():
    """
    Per-department appointment and revenue stats.
    GET /api/v1/dashboard/department-stats
    admin only.
    """
    stats = DashboardService.get_department_stats()
    return success_response({'departments': stats}, 200)


@dashboard_bp.route('/doctor-utilization', methods=['GET'])
@jwt_required()
@role_required(['admin'])
def get_doctor_utilization():
    """
    Per-doctor utilization stats.
    GET /api/v1/dashboard/doctor-utilization
    admin only.
    """
    stats = DashboardService.get_doctor_utilization()
    return success_response({'doctors': stats}, 200)