from datetime import date, timedelta
from decimal import Decimal
from sqlalchemy import func, case
from app.extensions import db
from app.models.appointment import Appointment
from app.models.billing import BillingRecord, BillingItem
from app.models.patient import Patient
from app.models.visit import Visit
from app.models.doctor import Doctor
from app.models.department import Department


class DashboardService:
    """
    Aggregation queries for the admin dashboard.
    All queries are optimized to use existing indexes.
    """

    @staticmethod
    def get_summary() -> dict:
        """
        Today's snapshot — appointments, patients, revenue.

        Returns:
            Dict with today's key metrics
        """
        today = date.today()

        # Today's appointments by status
        today_appointments = Appointment.query.filter_by(
            appointment_date=today
        ).all()

        total_today = len(today_appointments)
        scheduled = sum(1 for a in today_appointments if a.status == 'scheduled')
        in_progress = sum(1 for a in today_appointments if a.status == 'in_progress')
        completed = sum(1 for a in today_appointments if a.status == 'completed')
        cancelled = sum(1 for a in today_appointments if a.status == 'cancelled')

        # Today's revenue — sum of paid billing records created today
        today_revenue = db.session.query(
            func.coalesce(func.sum(BillingRecord.total_amount), 0)
        ).filter(
            func.date(BillingRecord.payment_date) == today,
            BillingRecord.status == 'paid'
        ).scalar()

        # Pending payments
        pending_count = BillingRecord.query.filter_by(
            status='pending'
        ).count()

        pending_amount = db.session.query(
            func.coalesce(func.sum(BillingRecord.total_amount), 0)
        ).filter(
            BillingRecord.status == 'pending'
        ).scalar()

        # Total active patients
        total_patients = Patient.query.filter_by(is_active=True).count()

        # New patients this month
        first_of_month = today.replace(day=1)
        new_patients_this_month = Patient.query.filter(
            Patient.created_at >= first_of_month,
            Patient.is_active == True
        ).count()

        return {
            'today': {
                'date': today.isoformat(),
                'appointments': {
                    'total': total_today,
                    'scheduled': scheduled,
                    'in_progress': in_progress,
                    'completed': completed,
                    'cancelled': cancelled,
                },
                'revenue': float(today_revenue),
            },
            'pending_payments': {
                'count': pending_count,
                'amount': float(pending_amount),
            },
            'patients': {
                'total_active': total_patients,
                'new_this_month': new_patients_this_month,
            },
        }

    @staticmethod
    def get_revenue(period: str = '30days') -> dict:
        """
        Revenue timeseries with consultation vs test breakdown.

        Args:
            period: '7days', '30days', or '90days'

        Returns:
            Dict with daily revenue data points
        """
        today = date.today()

        period_map = {
            '7days': 7,
            '30days': 30,
            '90days': 90,
        }

        days = period_map.get(period, 30)
        start_date = today - timedelta(days=days)

        # Get paid billing records in period
        records = db.session.query(
            func.date(BillingRecord.payment_date).label('date'),
            func.sum(BillingItem.amount).label('amount'),
            BillingItem.category,
        ).join(
            BillingItem,
            BillingItem.billing_record_id == BillingRecord.id
        ).filter(
            BillingRecord.status == 'paid',
            func.date(BillingRecord.payment_date) >= start_date,
        ).group_by(
            func.date(BillingRecord.payment_date),
            BillingItem.category,
        ).all()

        # Build date → category → amount map
        revenue_map = {}
        for record in records:
            date_str = str(record.date)
            if date_str not in revenue_map:
                revenue_map[date_str] = {
                    'consultation': 0,
                    'test': 0,
                    'procedure': 0,
                    'other': 0,
                    'total': 0,
                }
            amount = float(record.amount)
            revenue_map[date_str][record.category] = amount
            revenue_map[date_str]['total'] += amount

        # Fill in missing dates with zeros
        data_points = []
        for i in range(days):
            day = start_date + timedelta(days=i)
            date_str = day.isoformat()
            if date_str in revenue_map:
                data_points.append({
                    'date': date_str,
                    **revenue_map[date_str]
                })
            else:
                data_points.append({
                    'date': date_str,
                    'consultation': 0,
                    'test': 0,
                    'procedure': 0,
                    'other': 0,
                    'total': 0,
                })

        total_revenue = sum(d['total'] for d in data_points)
        total_consultation = sum(d['consultation'] for d in data_points)
        total_tests = sum(d['test'] + d['procedure'] for d in data_points)

        return {
            'period': period,
            'start_date': start_date.isoformat(),
            'end_date': today.isoformat(),
            'summary': {
                'total': round(total_revenue, 2),
                'consultation': round(total_consultation, 2),
                'tests_and_procedures': round(total_tests, 2),
            },
            'data': data_points,
        }

    @staticmethod
    def get_department_stats() -> list:
        """
        Per-department appointment and revenue stats.

        Returns:
            List of department stat dicts
        """
        today = date.today()
        first_of_month = today.replace(day=1)

        departments = Department.query.filter_by(is_active=True).all()
        stats = []

        for dept in departments:
            # Total appointments this month
            monthly_appointments = Appointment.query.filter(
                Appointment.department_id == dept.id,
                Appointment.appointment_date >= first_of_month,
            ).count()

            # Completed this month
            completed = Appointment.query.filter(
                Appointment.department_id == dept.id,
                Appointment.appointment_date >= first_of_month,
                Appointment.status == 'completed',
            ).count()

            # Revenue this month
            monthly_revenue = db.session.query(
                func.coalesce(func.sum(BillingRecord.total_amount), 0)
            ).join(
                Visit, Visit.id == BillingRecord.visit_id
            ).join(
                Appointment, Appointment.id == Visit.appointment_id
            ).filter(
                Appointment.department_id == dept.id,
                BillingRecord.status == 'paid',
                func.date(BillingRecord.payment_date) >= first_of_month,
            ).scalar()

            stats.append({
                'department_id': dept.id,
                'department_name': dept.name,
                'consultation_fee': float(dept.consultation_fee),
                'monthly_appointments': monthly_appointments,
                'monthly_completed': completed,
                'completion_rate': round(
                    completed / monthly_appointments * 100
                    if monthly_appointments > 0 else 0, 1
                ),
                'monthly_revenue': float(monthly_revenue),
            })

        return stats

    @staticmethod
    def get_doctor_utilization() -> list:
        """
        Per-doctor appointment utilization stats.

        Returns:
            List of doctor utilization dicts
        """
        today = date.today()
        first_of_month = today.replace(day=1)

        # Total slots available per doctor per day (16 slots × working days)
        working_days_this_month = sum(
            1 for i in range((today - first_of_month).days + 1)
            if (first_of_month + timedelta(days=i)).weekday() < 6
        )
        total_slots = working_days_this_month * 16

        doctors = Doctor.query.filter_by(is_active=True).all()
        stats = []

        for doctor in doctors:
            monthly_appointments = Appointment.query.filter(
                Appointment.doctor_id == doctor.id,
                Appointment.appointment_date >= first_of_month,
                Appointment.status.notin_(['cancelled', 'no_show']),
            ).count()

            completed = Appointment.query.filter(
                Appointment.doctor_id == doctor.id,
                Appointment.appointment_date >= first_of_month,
                Appointment.status == 'completed',
            ).count()

            # Revenue generated this month
            monthly_revenue = db.session.query(
                func.coalesce(func.sum(BillingRecord.total_amount), 0)
            ).join(
                Visit, Visit.id == BillingRecord.visit_id
            ).filter(
                Visit.doctor_id == doctor.id,
                BillingRecord.status == 'paid',
                func.date(BillingRecord.payment_date) >= first_of_month,
            ).scalar()

            stats.append({
                'doctor_id': doctor.id,
                'doctor_name': doctor.user.full_name,
                'department': doctor.department.name,
                'specialization': doctor.specialization,
                'monthly_appointments': monthly_appointments,
                'monthly_completed': completed,
                'utilization_rate': round(
                    monthly_appointments / total_slots * 100
                    if total_slots > 0 else 0, 1
                ),
                'monthly_revenue': float(monthly_revenue),
            })

        return sorted(stats, key=lambda x: x['monthly_revenue'], reverse=True)