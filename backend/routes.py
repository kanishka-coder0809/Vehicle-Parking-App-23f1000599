from app import app
from flask import render_template, request, redirect, flash, url_for, send_file, jsonify, session
from .models import db, Admin, User, ParkingLot, ParkingSpot, ReservedParkingSpot, ParkingLotReview, FavoriteParkingLot, NotificationLog, SpotAvailabilityAlert, MonthlySubscription, WalletTransaction
from flask_login import login_user,logout_user, login_required, current_user
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import and_, or_, cast, String
from datetime import datetime
from calendar import month_name
from io import BytesIO, StringIO
import csv
import os
import re
from werkzeug.utils import secure_filename
import matplotlib
matplotlib.use('Agg')
import matplotlib.pylab as plt

try:
    from flask_mail import Mail, Message  # type: ignore[import-not-found]
    MAIL_AVAILABLE = True
except Exception:
    MAIL_AVAILABLE = False

try:
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
    PDF_AVAILABLE = True
except Exception:
    PDF_AVAILABLE = False


mail = Mail(app) if MAIL_AVAILABLE else None
UPLOAD_DIR = os.path.join("static", "user_profiles")
os.makedirs(UPLOAD_DIR, exist_ok=True)

SUBSCRIPTION_PLANS = {
    "basic": {
        "name": "Basic",
        "monthly_fee": 99,
        "yearly_fee": 1188,
        "features": [
            "5% discount on bookings",
            "Faster checkout",
            "2% wallet cashback",
        ],
    },
    "commuter": {
        "name": "Advanced",
        "monthly_fee": 399,
        "yearly_fee": 4788,
        "features": [
            "Daily 1 hour free parking",
            "Discounted extra hours",
            "Priority booking",
            "FASTag auto billing",
        ],
    },
    "premium": {
        "name": "Premium Unlimited",
        "monthly_fee": 2499,
        "yearly_fee": 29988,
        "features": [
            "Unlimited parking at select locations",
            "Reserved slots",
            "No surge pricing",
            "Fast entry/exit (QR / FASTag)",
        ],
    },
}


def _build_avg_ratings(lots):
    avg_ratings = {}
    for lot in lots:
        lot_reviews = db.session.query(ParkingLotReview).filter_by(lot_id=lot.id).all()
        if lot_reviews:
            avg_ratings[lot.id] = round(sum(review.rating for review in lot_reviews) / len(lot_reviews), 1)
        else:
            avg_ratings[lot.id] = 0
    return avg_ratings


def _build_favorite_ids(user_id):
    favorites = db.session.query(FavoriteParkingLot).filter_by(user_id=user_id).all()
    return {fav.lot_id for fav in favorites}


def _resolve_logo_path():
    logo_candidates = [
        os.path.join(app.root_path, "static", "images", "logo.png"),
        os.path.join(app.root_path, "static", "images", "Logo.png"),
    ]
    for path in logo_candidates:
        if os.path.exists(path):
            return path
    return None


def _build_pdf_bytes(title, table_headers, table_rows, meta_rows=None):
    buffer = BytesIO()
    if PDF_AVAILABLE:
        doc = SimpleDocTemplate(buffer, pagesize=A4, leftMargin=36, rightMargin=36, topMargin=24, bottomMargin=24)
        styles = getSampleStyleSheet()
        elements = []

        # Branded header: logo + FindMySpot title
        logo_path = _resolve_logo_path()
        brand_text = Paragraph(
            "<b>FindMySpot</b><br/><font size='9' color='#555555'>Smart Parking Management</font>",
            styles["Normal"],
        )
        if logo_path:
            logo = Image(logo_path, width=0.45 * inch, height=0.45 * inch)
            header_table = Table([[logo, brand_text]], colWidths=[0.6 * inch, 6.4 * inch])
        else:
            header_table = Table([[brand_text]], colWidths=[7.0 * inch])

        header_table.setStyle(
            TableStyle(
                [
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                    ("LEFTPADDING", (0, 0), (-1, -1), 0),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                    ("TOPPADDING", (0, 0), (-1, -1), 0),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
                ]
            )
        )
        elements.append(header_table)

        title_style = ParagraphStyle(
            name="TitleStyle",
            parent=styles["Heading2"],
            textColor=colors.HexColor("#123A8F"),
            spaceAfter=8,
        )
        elements.append(Paragraph(title, title_style))
        elements.append(Spacer(1, 6))

        if meta_rows:
            meta_table = Table(meta_rows, colWidths=[1.8 * inch, 5.2 * inch])
            meta_table.setStyle(
                TableStyle(
                    [
                        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F5F7FA")),
                        ("TEXTCOLOR", (0, 0), (-1, -1), colors.black),
                        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                        ("FONTNAME", (1, 0), (1, -1), "Helvetica"),
                        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#D2D7E0")),
                        ("LEFTPADDING", (0, 0), (-1, -1), 6),
                        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                        ("TOPPADDING", (0, 0), (-1, -1), 5),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                    ]
                )
            )
            elements.append(meta_table)
            elements.append(Spacer(1, 10))

        table_data = [table_headers] + table_rows
        col_width = 7.0 / max(len(table_headers), 1)
        data_table = Table(table_data, colWidths=[col_width * inch for _ in table_headers], repeatRows=1)
        data_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#123A8F")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#D2D7E0")),
                    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F9FBFF")]),
                    ("LEFTPADDING", (0, 0), (-1, -1), 6),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                    ("TOPPADDING", (0, 0), (-1, -1), 5),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                ]
            )
        )
        elements.append(data_table)

        doc.build(elements)
    else:
        # Fallback stream if reportlab is unavailable.
        plain = [title]
        if meta_rows:
            plain.extend([f"{key}: {value}" for key, value in meta_rows])
        plain.append(" | ".join(table_headers))
        plain.extend([" | ".join(str(cell) for cell in row) for row in table_rows])
        buffer.write(("\n".join(plain)).encode("utf-8"))
    buffer.seek(0)
    return buffer


def _send_notification(user, subject, message):
    created_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    email_status = "sent"
    if MAIL_AVAILABLE:
        try:
            msg = Message(subject=subject, recipients=[user.email], body=message)
            mail.send(msg)
        except Exception:
            email_status = "logged-only"
    else:
        email_status = "logged-only"

    db.session.add(
        NotificationLog(
            user_id=user.id,
            channel="email",
            subject=subject,
            message=message,
            status=email_status,
            created_at=created_at,
        )
    )
    db.session.add(
        NotificationLog(
            user_id=user.id,
            channel="sms",
            subject=subject,
            message=message,
            status="simulated",
            created_at=created_at,
        )
    )


def _notify_spot_available(lot_id):
    alerts = db.session.query(SpotAvailabilityAlert).filter_by(lot_id=lot_id, is_active=True).all()
    lot = db.session.query(ParkingLot).filter_by(id=lot_id).first()
    if not lot:
        return
    for alert in alerts:
        user = db.session.query(User).filter_by(id=alert.user_id).first()
        if user:
            _send_notification(
                user,
                "Parking Spot Available",
                f"A parking spot is now available at {lot.prime_location_name}, {lot.city}.",
            )
        alert.is_active = False


def _get_active_subscription(user_id):
    today = datetime.now().date()
    subscriptions = db.session.query(MonthlySubscription).filter_by(user_id=user_id, is_active=True).all()
    for sub in subscriptions:
        start_date = datetime.strptime(sub.start_date, '%Y-%m-%d').date()
        end_date = datetime.strptime(sub.end_date, '%Y-%m-%d').date()
        if start_date <= today <= end_date:
            return sub
        sub.is_active = False
    return None


def _get_subscription_plan(tier):
    return SUBSCRIPTION_PLANS.get((tier or "").lower())


def _is_first_subscription(user_id):
    return db.session.query(MonthlySubscription).filter_by(user_id=user_id).count() == 0


def _normalize_billing_cycle(billing_cycle):
    return "yearly" if (billing_cycle or "").lower() == "yearly" else "monthly"


def _subscription_cycle_label(billing_cycle):
    return "Yearly" if _normalize_billing_cycle(billing_cycle) == "yearly" else "Monthly"


def _subscription_cycle_from_record(subscription):
    if not subscription:
        return "monthly"
    try:
        start_date = datetime.strptime(subscription.start_date, '%Y-%m-%d').date()
        end_date = datetime.strptime(subscription.end_date, '%Y-%m-%d').date()
        return "yearly" if (end_date - start_date).days >= 360 else "monthly"
    except Exception:
        return "monthly"


def _subscription_charge_amount(user_id, tier, billing_cycle="monthly"):
    plan = _get_subscription_plan(tier)
    if not plan:
        return None
    cycle = _normalize_billing_cycle(billing_cycle)
    if cycle == "yearly":
        return float(plan.get("yearly_fee", plan["monthly_fee"] * 12))
    return 49 if _is_first_subscription(user_id) else float(plan["monthly_fee"])


def _subscription_paid_amount(subscription):
    if not subscription:
        return 0.0

    billing_cycle = _subscription_cycle_from_record(subscription)
    plan = _get_subscription_plan(subscription.tier)
    fallback_amount = float(
        plan.get("yearly_fee", plan["monthly_fee"] * 12)
        if (plan and billing_cycle == "yearly")
        else (plan["monthly_fee"] if plan else 0)
    )

    plan_name = plan["name"] if plan else (subscription.tier or "Subscription")
    activation_logs = db.session.query(NotificationLog).filter(
        NotificationLog.user_id == subscription.user_id,
        NotificationLog.subject == "Subscription Activated",
        NotificationLog.message.ilike(f"%{plan_name}%"),
    ).order_by(NotificationLog.id.desc()).all()

    for log in activation_logs:
        amount_match = re.search(r"Payment received:\s*Rs\s*([0-9]+(?:\.[0-9]+)?)", log.message or "")
        if amount_match:
            try:
                return round(float(amount_match.group(1)), 2)
            except (TypeError, ValueError):
                continue

    return round(fallback_amount, 2)


def _subscription_tier(subscription):
    if not subscription:
        return ""
    if isinstance(subscription, str):
        return subscription.lower()
    return (getattr(subscription, "tier", "") or "").lower()


def _calculate_parking_amount(hourly_rate, duration_minutes, subscription=None):
    duration_hours = max(float(duration_minutes) / 60.0, 0)
    base_amount = float(hourly_rate or 0) * duration_hours

    tier = _subscription_tier(subscription)
    if not tier:
        return round(base_amount, 2)

    if tier == "basic":
        return round(base_amount * 0.95, 2)
    if tier == "commuter":
        chargeable_hours = max(duration_hours - 1.0, 0)
        return round(chargeable_hours * float(hourly_rate or 0) * 0.80, 2)
    if tier == "premium":
        return 0.0
    return round(base_amount, 2)


def _build_pricing_breakdown(hourly_rate, duration_minutes, subscription=None):
    rate = float(hourly_rate or 0)
    minutes = _parse_duration_minutes(duration_minutes)
    duration_hours = round(float(minutes) / 60.0, 2)
    base_amount = round((rate * minutes) / 60.0, 2)
    final_amount = _calculate_parking_amount(rate, minutes, subscription)
    tier = _subscription_tier(subscription)

    discount_rows = []
    plan_name = None
    active_features = []

    if tier:
        plan = _get_subscription_plan(tier)
        if plan:
            plan_name = plan["name"]
            active_features = plan.get("features", [])

    if tier == "basic":
        basic_discount = round(max(base_amount - final_amount, 0), 2)
        if basic_discount > 0:
            discount_rows.append({"label": "Basic plan discount (5%)", "amount": basic_discount})
    elif tier == "commuter":
        free_hours = min(duration_hours, 1.0)
        free_value = round(free_hours * rate, 2)
        if free_value > 0:
            discount_rows.append({"label": "Advanced free 1 hour", "amount": free_value})

        extra_hours = max(duration_hours - 1.0, 0)
        extra_base = round(extra_hours * rate, 2)
        extra_discount = round(extra_base * 0.20, 2)
        if extra_discount > 0:
            discount_rows.append({"label": "Advanced extra-hours discount (20%)", "amount": extra_discount})
    elif tier == "premium":
        if base_amount > 0:
            discount_rows.append({"label": "Premium unlimited coverage", "amount": base_amount})

    total_savings = round(sum(row["amount"] for row in discount_rows), 2)

    return {
        "duration_hours": duration_hours,
        "base_amount": base_amount,
        "final_amount": round(final_amount, 2),
        "total_savings": total_savings,
        "plan_tier": tier,
        "plan_name": plan_name,
        "discount_rows": discount_rows,
        "active_features": active_features,
    }


def _infer_subscription_tier_from_reservation(reservation):
    planned_minutes = _parse_duration_minutes(getattr(reservation, "planned_duration_minutes", 60))
    hourly_rate = float(getattr(reservation, "parkingCost_unitTime", 0) or getattr(reservation.Parking_Lot, "price", 0) or 0)
    planned_amount = float(reservation.planned_amount if reservation.planned_amount is not None else _planned_amount(hourly_rate, planned_minutes))

    no_plan_amount = _planned_amount(hourly_rate, planned_minutes)
    basic_amount = _calculate_parking_amount(hourly_rate, planned_minutes, "basic")
    commuter_amount = _calculate_parking_amount(hourly_rate, planned_minutes, "commuter")

    if hourly_rate > 0 and abs(planned_amount - 0) < 0.01:
        return "premium"
    if abs(planned_amount - basic_amount) < 0.5:
        return "basic"
    if abs(planned_amount - commuter_amount) < 0.5:
        return "commuter"
    if abs(planned_amount - no_plan_amount) < 0.5:
        return ""
    return ""


def _credit_basic_cashback_if_eligible(user, subscription_tier, billed_amount, booking_id):
    if _subscription_tier(subscription_tier) != "basic":
        return 0.0
    cashback = round(float(billed_amount or 0) * 0.02, 2)
    if cashback > 0:
        _record_wallet_transaction(user, "credit", cashback, f"Basic cashback for booking #{booking_id}")
    return cashback


def _parse_duration_minutes(raw_minutes):
    try:
        minutes = int(raw_minutes)
    except (TypeError, ValueError):
        return 60

    return max(15, min(minutes, 720))


def _duration_label(duration_minutes):
    hours = duration_minutes // 60
    minutes = duration_minutes % 60
    parts = []
    if hours:
        parts.append(f"{hours} hr" if hours == 1 else f"{hours} hrs")
    if minutes:
        parts.append(f"{minutes} min")
    return " ".join(parts) if parts else "0 min"


def _planned_amount(hourly_rate, duration_minutes):
    return round((float(hourly_rate or 0) * float(duration_minutes)) / 60.0, 2)


def _wallet_balance(user):
    return float(user.wallet_balance or 0)


def _record_wallet_transaction(user, transaction_type, amount, description, allow_negative=False):
    amount = round(float(amount), 2)
    user.wallet_balance = round(_wallet_balance(user), 2)
    if transaction_type in ("debit", "withdrawal"):
        updated_balance = user.wallet_balance - amount
        user.wallet_balance = round(updated_balance if allow_negative else max(updated_balance, 0), 2)
    else:
        user.wallet_balance = round(user.wallet_balance + amount, 2)

    db.session.add(
        WalletTransaction(
            user_id=user.id,
            transaction_type=transaction_type,
            amount=amount,
            description=description,
            balance_after=user.wallet_balance,
            created_at=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        )
    )


def _credit_wallet(user, amount, description):
    if amount and amount > 0:
        _record_wallet_transaction(user, "refund", amount, description)


def _debit_wallet(user, amount, description):
    if amount and amount > 0:
        if _wallet_balance(user) < amount:
            return False
        _record_wallet_transaction(user, "debit", amount, description)
        return True
    return True


def _sync_booking_wallet_adjustments(user_id):
    user = db.session.query(User).filter_by(id=user_id).first()
    if not user:
        return

    completed_bookings = db.session.query(ReservedParkingSpot).filter(
        ReservedParkingSpot.user_id == user_id,
        ReservedParkingSpot.leaving_timestamp != "Not yet left",
    ).all()

    for booking in completed_bookings:
        booking_ref = f"booking #{booking.id}"
        has_refund_txn = db.session.query(WalletTransaction).filter(
            WalletTransaction.user_id == user_id,
            WalletTransaction.description.ilike(f"%{booking_ref}%"),
            WalletTransaction.transaction_type == "refund",
        ).first()
        has_penalty_txn = db.session.query(WalletTransaction).filter(
            WalletTransaction.user_id == user_id,
            WalletTransaction.description.ilike(f"%{booking_ref}%"),
            WalletTransaction.transaction_type == "debit",
        ).first()

        unit_price = float(booking.planned_amount if booking.planned_amount is not None else (booking.parkingCost_unitTime or 0))
        total_cost = float(booking.total_cost or booking.billed_amount or 0)

        implied_refund = round(max(unit_price - total_cost, 0), 2)
        implied_penalty = round(max(total_cost - unit_price, 0), 2)

        if booking.refund_amount is None or (booking.refund_amount == 0 and implied_refund > 0):
            booking.refund_amount = implied_refund

        if implied_refund > 0 and not has_refund_txn:
            _credit_wallet(user, implied_refund, f"Refund for booking #{booking.id}")

        if implied_penalty > 0 and not has_penalty_txn:
            _record_wallet_transaction(user, "debit", implied_penalty, f"Overtime penalty for booking #{booking.id}", allow_negative=True)


def _auto_book_for_subscription(subscription):
    if not subscription or not subscription.auto_book_enabled or not subscription.preferred_lot_id:
        return

    user_has_active = db.session.query(ReservedParkingSpot).filter(
        ReservedParkingSpot.user_id == subscription.user_id,
        ReservedParkingSpot.leaving_timestamp == "Not yet left",
    ).first()
    if user_has_active:
        return

    spot = db.session.query(ParkingSpot).filter_by(lot_id=subscription.preferred_lot_id, status='A').first()
    if not spot:
        return

    spot.status = 'O'
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    db.session.add(
        ReservedParkingSpot(
            spot_id=spot.id,
            lot_id=subscription.preferred_lot_id,
            user_id=subscription.user_id,
            parking_timestamp=now,
            leaving_timestamp="Not yet left",
            parkingCost_unitTime=0,
            vehicle_number="AUTO-BOOK",
        )
    )
    user = db.session.query(User).filter_by(id=subscription.user_id).first()
    lot = db.session.query(ParkingLot).filter_by(id=subscription.preferred_lot_id).first()
    if user and lot:
        _send_notification(
            user,
            "Auto Booking Confirmed",
            f"Your subscription auto-booked a spot at {lot.prime_location_name}.",
        )


def _send_booking_reminders_for_user(user_id):
    active_bookings = db.session.query(ReservedParkingSpot).filter(
        ReservedParkingSpot.user_id == user_id,
        ReservedParkingSpot.leaving_timestamp == "Not yet left",
        ReservedParkingSpot.reminder_sent == False,
    ).all()
    user = db.session.query(User).filter_by(id=user_id).first()
    if not user:
        return

    now = datetime.now()
    for booking in active_bookings:
        start_dt = datetime.strptime(booking.parking_timestamp, '%Y-%m-%d %H:%M:%S')
        if (now - start_dt).total_seconds() >= 3600:
            _send_notification(
                user,
                "Booking Reminder",
                f"Your booking at {booking.Parking_Lot.prime_location_name} is still active.",
            )
            booking.reminder_sent = True


def _create_booking_reservation(user_id, lot_id, vehicle_no, duration_minutes=60, commit=True):
    lot = db.session.query(ParkingLot).filter_by(id=lot_id).first()
    if not lot:
        return None, "Invalid Parking Lot"

    available_spot = db.session.query(ParkingSpot).filter_by(lot_id=lot_id, status='A').first()
    if not available_spot:
        return None, "No available parking spots in this lot."

    formatted_vehicle_number = _format_vehicle_number(vehicle_no)
    if not formatted_vehicle_number:
        return None, "Vehicle number is required."

    same_vehicle_active_booking = _get_active_booking_for_vehicle(user_id, formatted_vehicle_number)
    if same_vehicle_active_booking:
        return None, "This vehicle number already has an active booking. Please use a different vehicle number or release the existing booking first."

    available_spot.status = 'O'
    active_subscription = _get_active_subscription(user_id)
    hourly_rate = float(lot.price or 0)
    planned_minutes = _parse_duration_minutes(duration_minutes)
    planned_amount = _calculate_parking_amount(hourly_rate, planned_minutes, active_subscription)

    now = datetime.now()
    reservation = ReservedParkingSpot(
        spot_id=available_spot.id,
        lot_id=lot.id,
        user_id=user_id,
        parking_timestamp=now.strftime('%Y-%m-%d %H:%M:%S'),
        leaving_timestamp="Not yet left",
        parkingCost_unitTime=int(round(hourly_rate)),
        planned_duration_minutes=planned_minutes,
        planned_amount=planned_amount,
        vehicle_number=formatted_vehicle_number,
    )
    db.session.add(reservation)

    user = db.session.query(User).filter_by(id=user_id).first()
    if user:
        _send_notification(user, "Booking Confirmed", f"Your booking is confirmed at {lot.prime_location_name}.")

    if commit:
        db.session.commit()
    return reservation, None


def _normalize_vehicle_number(vehicle_no):
    return re.sub(r"[^A-Za-z0-9]", "", (vehicle_no or "")).upper()


def _format_vehicle_number(vehicle_no):
    return _normalize_vehicle_number(vehicle_no)


def _get_active_booking_for_vehicle(user_id, vehicle_no):
    normalized_vehicle = _normalize_vehicle_number(vehicle_no)
    if not normalized_vehicle:
        return None

    active_bookings = db.session.query(ReservedParkingSpot).filter(
        ReservedParkingSpot.user_id == user_id,
        ReservedParkingSpot.leaving_timestamp == "Not yet left",
    ).all()

    for booking in active_bookings:
        if _normalize_vehicle_number(getattr(booking, "vehicle_number", "")) == normalized_vehicle:
            return booking

    return None


def _wallet_transaction_category(transaction):
    description = (transaction.description or '').lower()
    transaction_type = (transaction.transaction_type or '').lower()

    if transaction_type == 'refund' or 'refund' in description:
        return 'refund'
    if 'penalty' in description or 'overtime' in description:
        return 'penalty'
    if transaction_type == 'debit':
        return 'withdraw'
    return 'added'


def _build_wallet_distribution_chart(transactions):
    counts = {
        'added': 0,
        'withdraw': 0,
        'refund': 0,
        'penalty': 0,
    }

    for transaction in transactions:
        category = _wallet_transaction_category(transaction)
        counts[category] += float(transaction.amount or 0)

    labels = []
    values = []
    colors = []
    palette = {
        'added': '#1d66e5',
        'withdraw': '#f59e0b',
        'refund': '#10b981',
        'penalty': '#ef4444',
    }
    label_map = {
        'added': 'Added Money',
        'withdraw': 'Withdraw',
        'refund': 'Refund',
        'penalty': 'Penalty',
    }

    for key in ['added', 'withdraw', 'refund', 'penalty']:
        value = counts[key]
        if value > 0:
            labels.append(label_map[key])
            values.append(value)
            colors.append(palette[key])

    chart_dir = os.path.join(app.root_path, 'static', 'user')
    os.makedirs(chart_dir, exist_ok=True)

    def _render_wallet_chart(chart_path, is_dark=False):
        text_color = '#f3f7ff' if is_dark else '#111827'
        title_color = '#dbe8ff' if is_dark else '#173b7a'
        wedge_edge = '#c7d6ef' if is_dark else 'white'
        auto_text_color = '#f8fbff'

        plt.figure(figsize=(6.2, 6.2), facecolor='none')
        plt.gca().set_facecolor('none')

        if values:
            wedges, texts, autotexts = plt.pie(
                values,
                labels=labels,
                colors=colors,
                autopct=lambda pct: f'{pct:.0f}%' if pct >= 5 else '',
                startangle=90,
                counterclock=False,
                wedgeprops={'edgecolor': wedge_edge, 'linewidth': 1.6},
                textprops={'fontsize': 10, 'fontweight': 'bold', 'color': text_color},
            )
            for autotext in autotexts:
                autotext.set_color(auto_text_color)
                autotext.set_fontsize(10)
            plt.title('Wallet Transaction Distribution', fontsize=15, fontweight='bold', color=title_color, pad=16)
            plt.axis('equal')
        else:
            plt.text(0.5, 0.5, 'No wallet activity yet', ha='center', va='center', fontsize=14, fontweight='bold', color=text_color)
            plt.axis('off')

        plt.tight_layout()
        plt.savefig(chart_path, dpi=180, bbox_inches='tight', transparent=True)
        plt.close()

    light_chart_path = os.path.join(chart_dir, 'wallet_transaction_pie_light.png')
    dark_chart_path = os.path.join(chart_dir, 'wallet_transaction_pie_dark.png')
    _render_wallet_chart(light_chart_path, is_dark=False)
    _render_wallet_chart(dark_chart_path, is_dark=True)

    return {
        'light_path': '/static/user/wallet_transaction_pie_light.png',
        'dark_path': '/static/user/wallet_transaction_pie_dark.png',
        'counts': counts,
    }

@app.route("/")
def index():
    return render_template("home.html")

@app.route("/logout")
@login_required
def logout():
    logout_user()
    flash('Logged Out Successfully !!', 'success')
    return redirect(url_for('login'))

@app.route("/register", methods = ["GET", "POST"])
def register():
    if request.method == "GET": 
        return render_template("register.html")
    elif request.method == "POST":
        u_name = request.form.get("name")
        u_email = request.form.get("email")
        u_password = request.form.get("password")
        u_phone = request.form.get("phone")
        u_city = request.form.get("city")
        u_pincode = request.form.get("pincode")
        user = db.session.query(User).filter_by(email = u_email).first()
        if user:
            flash('E-mail Alreay Exist !!', 'warning')
            return redirect(url_for('register'))
        else:
            new_user = User(name = u_name, email = u_email, password = u_password, phone = u_phone, city = u_city, pincode = u_pincode)
            db.session.add(new_user)
            db.session.commit()
            flash('E-mail Registered !!', 'success')
            return redirect(url_for('login'))

@app.route("/login", methods =["GET", "POST"])
def login():
    if request.method == "GET":
        return render_template("login.html")
    elif request.method == "POST":
        l_email = request.form.get("email")
        l_password = request.form.get("password")

        login = db.session.query(Admin).filter_by(email=l_email).first() or db.session.query(User).filter_by(email=l_email).first()

        if login:
            if login.password == l_password:
                if isinstance(login, Admin):
                    login_user(login)
                    flash('Logged in successfully!', 'success')
                    return redirect(f"/admin/dashboard")
                elif isinstance(login, User):
                    login_user(login)
                    flash('Logged in successfully!', 'success')
                    return redirect(f"/user/dashboard")
            else:
                flash('Invalid password !!', 'danger')
                return redirect(url_for('login'))
        else:
            flash('Invalid E-mail !!', 'danger')
            return redirect(url_for('login'))

@app.route("/admin/dashboard")
@login_required  
def admin_dash():
    all_par = db.session.query(ParkingLot).all()
    all_users = db.session.query(User).all()

    user_histories = {
        user.id: ReservedParkingSpot.query.filter_by(user_id=user.id).all()
        for user in all_users
    }

    # Check and create missing parking spots for each lot
    for lot in all_par:
        existing_spots = db.session.query(ParkingSpot).filter_by(lot_id=lot.id).count()
        if existing_spots < lot.maximum_number_of_spots:
            for _ in range(existing_spots + 1, lot.maximum_number_of_spots + 1):
                new_spot = ParkingSpot(lot_id=lot.id, status="A")  # A = Available
                db.session.add(new_spot)
            db.session.commit()
    return render_template("/admin/dashboard.html", all_par = all_par, all_users = all_users, user_histories= user_histories)


@app.route("/admin/search", methods = ["GET", "POST"])
@login_required
def admin_search():
    all_users = db.session.query(User).all()

    user_histories = {
        user.id: ReservedParkingSpot.query.filter_by(user_id=user.id).all()
        for user in all_users
    }

    if request.method == "GET":
        return render_template("/admin/search.html")
    elif request.method == "POST":
        type = request.form.get("searchby")
        query = request.form.get("search_query")
        result = []
        if type == "user":
            result = db.session.query(User).filter(User.name.ilike(f"%{query}%")).all()
        elif type == "parking":
            result = db.session.query(ParkingLot).filter(ParkingLot.prime_location_name.ilike(f"%{query}%")).all()
        return render_template("/admin/search.html", results = result, type = type, user_histories= user_histories, request = request)
    
@app.route("/admin/summary")
@login_required
def admin_summary():
    if request.method == "GET":
        parkings = db.session.query(ParkingLot).all()
        park_names = []
        book_count = []
        for parking in parkings:
            park_names.append(parking.prime_location_name)
            book_count.append(len(parking.reserved_parking_spot))
        plt.barh(y = park_names, width = book_count)
        plt.savefig("./static/admin/parkinglot_booking_count.png", bbox_inches='tight', pad_inches=0.5)
        plt.close()

        # Peak booking hour graph
        hourly_count = {h: 0 for h in range(24)}
        all_bookings = db.session.query(ReservedParkingSpot).all()
        for booking in all_bookings:
            hour = datetime.strptime(booking.parking_timestamp, '%Y-%m-%d %H:%M:%S').hour
            hourly_count[hour] += 1

        plt.figure(figsize=(8, 4))
        plt.plot(list(hourly_count.keys()), list(hourly_count.values()), marker='o')
        plt.xlabel("Hour of Day")
        plt.ylabel("Bookings")
        plt.title("Peak Booking Hours")
        plt.savefig("./static/admin/peak_booking_hours.png", bbox_inches='tight', pad_inches=0.5)
        plt.close()

        # KPI metrics
        now = datetime.now()
        month_bookings = []
        for booking in all_bookings:
            if booking.leaving_timestamp == "Not yet left":
                continue
            leaving_dt = datetime.strptime(booking.leaving_timestamp, '%Y-%m-%d %H:%M:%S')
            if leaving_dt.year == now.year and leaving_dt.month == now.month:
                month_bookings.append(booking)

        total_revenue = 0
        for booking in month_bookings:
            if booking.total_cost is not None:
                total_revenue += booking.total_cost
            else:
                in_time = datetime.strptime(booking.parking_timestamp, '%Y-%m-%d %H:%M:%S')
                out_time = datetime.strptime(booking.leaving_timestamp, '%Y-%m-%d %H:%M:%S')
                total_revenue += (out_time - in_time).total_seconds() / 3600 * booking.parkingCost_unitTime

        lot_booking_counts = {
            lot.prime_location_name: len(lot.reserved_parking_spot) for lot in parkings
        }
        most_booked_lot = max(lot_booking_counts, key=lot_booking_counts.get) if lot_booking_counts else "N/A"
        active_users_count = db.session.query(ReservedParkingSpot).filter_by(leaving_timestamp="Not yet left").count()

        occupancy_by_lot = []
        for lot in parkings:
            occupied = len([spot for spot in lot.spots if spot.status == 'O'])
            rate = round((occupied / lot.maximum_number_of_spots) * 100, 2) if lot.maximum_number_of_spots else 0
            occupancy_by_lot.append({"name": lot.prime_location_name, "rate": rate})

        return render_template(
            "/admin/summary.html",
            total_revenue=round(total_revenue, 2),
            month_label=f"{month_name[now.month]} {now.year}",
            most_booked_lot=most_booked_lot,
            active_users_count=active_users_count,
            occupancy_by_lot=occupancy_by_lot,
        )

@app.route("/user/dashboard")
@login_required
def user_dash():
    # Fetch all lots with at least one available spot
    all_par = db.session.query(ParkingLot).join(ParkingSpot).filter(ParkingSpot.status == 'A').distinct().all()
    avg_ratings = _build_avg_ratings(all_par)
    favorite_lot_ids = _build_favorite_ids(current_user.id)
    user_review_lot_ids = {
        review.lot_id for review in db.session.query(ParkingLotReview).filter_by(user_id=current_user.id).all()
    }
    active_subscription = _get_active_subscription(current_user.id)

    if active_subscription:
        _auto_book_for_subscription(active_subscription)

    _send_booking_reminders_for_user(current_user.id)
    _sync_booking_wallet_adjustments(current_user.id)
    db.session.commit()

    #fetch registered users
    booking_history = db.session.query(ReservedParkingSpot).filter_by(user_id=current_user.id).all()
    # Add duration and planned/remaining time details for history table.
    for booking in booking_history:
        planned_minutes = int(getattr(booking, "planned_duration_minutes", 60) or 60)
        booking.booked_for = _duration_label(planned_minutes)
        booking.remaining_seconds = 0

        if booking.leaving_timestamp != "Not yet left":
            start_time = datetime.strptime(booking.parking_timestamp, "%Y-%m-%d %H:%M:%S")
            end_time = datetime.strptime(booking.leaving_timestamp, "%Y-%m-%d %H:%M:%S")
            duration = end_time - start_time
            booking.duration = str(duration)  # This will be like '0:45:00' (HH:MM:SS)
            booking.time_left = "--"
        else:
            booking.duration = "Ongoing"
            start_time = datetime.strptime(booking.parking_timestamp, "%Y-%m-%d %H:%M:%S")
            elapsed_seconds = max((datetime.now() - start_time).total_seconds(), 0)
            remaining_seconds = int((planned_minutes * 60) - elapsed_seconds)
            booking.remaining_seconds = remaining_seconds

            if remaining_seconds > 0:
                rem_hours = remaining_seconds // 3600
                rem_minutes = (remaining_seconds % 3600) // 60
                rem_secs = remaining_seconds % 60
                booking.time_left = f"{rem_hours:02d}:{rem_minutes:02d}:{rem_secs:02d}"
            else:
                overtime_seconds = abs(remaining_seconds)
                over_hours = overtime_seconds // 3600
                over_minutes = (overtime_seconds % 3600) // 60
                over_secs = overtime_seconds % 60
                booking.time_left = f"Over by {over_hours:02d}:{over_minutes:02d}:{over_secs:02d}"
    return render_template(
        "/user/dashboard.html",
        curr_user=current_user,
        all_par=all_par,
        booking_history=booking_history,
        avg_ratings=avg_ratings,
        favorite_lot_ids=favorite_lot_ids,
        user_review_lot_ids=user_review_lot_ids,
        active_subscription=active_subscription,
    )


@app.route("/user/profile", methods=["GET", "POST"])
@login_required
def user_profile():
    if request.method == "GET":
        user_notifications = db.session.query(NotificationLog).filter_by(user_id=current_user.id).order_by(NotificationLog.id.desc()).all()
        notif_seen_key = f"notif_seen_{current_user.id}"
        last_seen_notification_id = int(session.get(notif_seen_key, 0) or 0)
        unread_ids = [n.id for n in user_notifications if n.id > last_seen_notification_id]
        unread_count = len(unread_ids)
        active_subscription = _get_active_subscription(current_user.id)
        active_features = []
        active_cycle = "monthly"
        if active_subscription:
            plan = _get_subscription_plan(active_subscription.tier)
            active_features = plan.get("features", []) if plan else []
            active_cycle = _subscription_cycle_from_record(active_subscription)
        return render_template(
            "/user/profile.html",
            user_notifications=user_notifications,
            unread_count=unread_count,
            unread_ids=unread_ids,
            active_subscription=active_subscription,
            active_features=active_features,
            active_cycle=active_cycle,
        )

    current_user.name = request.form.get("name")
    current_user.phone = request.form.get("phone")
    current_user.city = request.form.get("city")
    current_user.pincode = request.form.get("pincode")
    current_user.date_of_birth = request.form.get("date_of_birth") or None
    current_user.gender = request.form.get("gender") or None
    current_user.bio = request.form.get("bio") or None
    current_user.full_address = request.form.get("full_address") or None
    current_user.state = request.form.get("state") or None
    current_user.landmark = request.form.get("landmark") or None
    current_user.vehicle_type = request.form.get("vehicle_type") or None
    current_user.vehicle_number = request.form.get("vehicle_number") or None
    current_user.preferred_parking_type = request.form.get("preferred_parking_type") or None
    current_user.preferred_location = request.form.get("preferred_location") or None
    current_user.time_preference = request.form.get("time_preference") or None
    current_user.alternate_phone = request.form.get("alternate_phone") or None
    current_user.secondary_email = request.form.get("secondary_email") or None

    profile_file = request.files.get("profile_image")
    if profile_file and profile_file.filename:
        safe_name = secure_filename(profile_file.filename)
        filename = f"user_{current_user.id}_{safe_name}"
        save_path = os.path.join(UPLOAD_DIR, filename)
        profile_file.save(save_path)
        current_user.profile_image = filename

    cover_file = request.files.get("cover_photo")
    if cover_file and cover_file.filename:
        safe_name = secure_filename(cover_file.filename)
        filename = f"cover_{current_user.id}_{safe_name}"
        save_path = os.path.join(UPLOAD_DIR, filename)
        cover_file.save(save_path)
        current_user.cover_photo = filename

    db.session.commit()
    flash("Profile updated successfully.", "success")
    return redirect("/user/profile")


@app.route("/user/remove-profile-image", methods=["POST"])
@login_required
def remove_profile_image():
    if current_user.profile_image and current_user.profile_image != "default.png":
        image_path = os.path.join(UPLOAD_DIR, current_user.profile_image)
        if os.path.exists(image_path):
            try:
                os.remove(image_path)
            except OSError:
                pass
    db.session.commit()
    flash("Profile image removed.", "success")
    return redirect("/user/profile")


@app.route("/user/notifications/mark-read", methods=["POST"])
@login_required
def mark_notifications_read():
    latest = db.session.query(NotificationLog.id).filter_by(user_id=current_user.id).order_by(NotificationLog.id.desc()).first()
    latest_id = int(latest[0]) if latest else 0
    session[f"notif_seen_{current_user.id}"] = latest_id
    return jsonify({"success": True, "unread_count": 0})


@app.route("/user/subscriptions", methods=["GET"])
@login_required
def user_subscriptions():
    active_subscription = _get_active_subscription(current_user.id)
    active_features = []
    active_cycle = "monthly"
    active_plan_name = "No Active Plan"
    next_billing_date = "-"
    amount_to_be_charged = 0.0
    billing_cycle_label = "Monthly"

    if active_subscription:
        plan = _get_subscription_plan(active_subscription.tier)
        active_features = plan.get("features", []) if plan else []
        active_cycle = _subscription_cycle_from_record(active_subscription)
        billing_cycle_label = _subscription_cycle_label(active_cycle)
        active_plan_name = plan["name"] if plan else (active_subscription.tier or "Subscription").title()
        next_billing_date = active_subscription.end_date
        if plan:
            amount_to_be_charged = float(
                plan.get("yearly_fee", plan["monthly_fee"] * 12)
                if active_cycle == "yearly"
                else plan["monthly_fee"]
            )

    subscription_history_records = (
        db.session.query(MonthlySubscription)
        .filter_by(user_id=current_user.id)
        .order_by(MonthlySubscription.id.desc())
        .all()
    )

    subscription_history = []
    for record in subscription_history_records:
        record_plan = _get_subscription_plan(record.tier)
        cycle = _subscription_cycle_from_record(record)
        plan_name = record_plan["name"] if record_plan else (record.tier or "Subscription").title()
        subscription_history.append(
            {
                "date": record.start_date,
                "plan": plan_name,
                "amount": _subscription_paid_amount(record),
                "status": "Active" if record.is_active else "Completed",
                "billing_cycle": _subscription_cycle_label(cycle),
            }
        )

    return render_template(
        "/user/subscriptions.html",
        active_subscription=active_subscription,
        active_features=active_features,
        active_cycle=active_cycle,
        first_month_offer=_is_first_subscription(current_user.id),
        subscription_plans=SUBSCRIPTION_PLANS,
        billing_summary={
            "current_plan": active_plan_name,
            "next_billing_date": next_billing_date,
            "amount_to_be_charged": round(amount_to_be_charged, 2),
            "billing_cycle": billing_cycle_label,
        },
        subscription_history=subscription_history,
    )


@app.route("/user/wallet", methods=["GET"])
@login_required
def user_wallet():
    _sync_booking_wallet_adjustments(current_user.id)
    db.session.commit()
    transactions = db.session.query(WalletTransaction).filter_by(user_id=current_user.id).order_by(WalletTransaction.id.desc()).all()
    active_subscription = _get_active_subscription(current_user.id)
    wallet_chart = _build_wallet_distribution_chart(transactions)
    return render_template(
        "/user/wallet.html",
        wallet_balance=_wallet_balance(current_user),
        transactions=transactions,
        active_subscription=active_subscription,
        wallet_chart=wallet_chart,
    )


@app.route("/wallet/add-money", methods=["POST"])
@login_required
def wallet_add_money():
    amount = request.form.get("amount", type=float)
    if not amount or amount <= 0:
        flash("Enter a valid amount to add.", "danger")
        return redirect("/user/wallet")

    _record_wallet_transaction(current_user, "credit", amount, "Added money to wallet")
    db.session.commit()
    flash(f"Rs {round(amount, 2)} added to wallet.", "success")
    return redirect("/user/wallet")


@app.route("/wallet/withdraw", methods=["POST"])
@login_required
def wallet_withdraw():
    amount = request.form.get("amount", type=float)
    if not amount or amount <= 0:
        flash("Enter a valid amount to withdraw.", "danger")
        return redirect("/user/wallet")

    if _wallet_balance(current_user) < amount:
        flash("Insufficient wallet balance.", "danger")
        return redirect("/user/wallet")

    _record_wallet_transaction(current_user, "withdrawal", amount, "Withdrawn from wallet")
    db.session.commit()
    flash(f"Rs {round(amount, 2)} withdrawn from wallet.", "success")
    return redirect("/user/wallet")


@app.route("/user/change-password", methods=["POST"])
@login_required
def change_password():
    old_password = request.form.get("old_password")
    new_password = request.form.get("new_password")
    if current_user.password != old_password:
        flash("Current password is incorrect.", "danger")
        return redirect("/user/profile")
    current_user.password = new_password
    db.session.commit()
    flash("Password changed successfully.", "success")
    return redirect("/user/profile")


@app.route("/subscription/subscribe", methods=["POST"])
@login_required
def subscribe_monthly_pass():
    tier = request.form.get("tier")
    if not _get_subscription_plan(tier):
        flash("Invalid subscription plan selected.", "danger")
        return redirect("/user/subscriptions")
    return redirect(url_for("subscription_payment", tier=tier))


@app.route("/subscription/payment", methods=["GET"])
@login_required
def subscription_payment():
    tier = request.args.get("tier")
    billing_cycle = _normalize_billing_cycle(request.args.get("billing_cycle"))
    plan = _get_subscription_plan(tier)
    if not plan:
        flash("Invalid subscription plan selected.", "danger")
        return redirect("/user/subscriptions")

    payable_amount = _subscription_charge_amount(current_user.id, tier, billing_cycle)
    wallet_balance = _wallet_balance(current_user)
    return render_template(
        "/user/subscription_payment.html",
        tier=tier,
        plan=plan,
        billing_cycle=billing_cycle,
        cycle_label=_subscription_cycle_label(billing_cycle),
        payable_amount=payable_amount,
        wallet_balance=wallet_balance,
        insufficient_balance=wallet_balance < float(payable_amount),
    )


@app.route("/subscription/activate", methods=["POST"])
@login_required
def activate_subscription():
    tier = request.form.get("tier")
    billing_cycle = _normalize_billing_cycle(request.form.get("billing_cycle"))
    method = (request.form.get("method") or "card").lower()
    plan = _get_subscription_plan(tier)
    if not plan:
        flash("Invalid subscription plan selected.", "danger")
        return redirect("/user/subscriptions")

    payable_amount = _subscription_charge_amount(current_user.id, tier, billing_cycle)

    if method == "wallet":
        if _wallet_balance(current_user) < float(payable_amount):
            flash("Insufficient wallet balance.", "danger")
            return redirect(url_for("subscription_payment", tier=tier, billing_cycle=billing_cycle))
        _record_wallet_transaction(current_user, "debit", payable_amount, f"{plan['name']} {billing_cycle} subscription payment")

    today = datetime.now().date()
    from datetime import timedelta
    end_date = today + timedelta(days=365 if billing_cycle == "yearly" else 30)

    existing = db.session.query(MonthlySubscription).filter_by(user_id=current_user.id, is_active=True).all()
    for sub in existing:
        sub.is_active = False

    new_sub = MonthlySubscription(
        user_id=current_user.id,
        tier=tier,
        monthly_fee=int(plan["monthly_fee"]),
        start_date=today.strftime('%Y-%m-%d'),
        end_date=end_date.strftime('%Y-%m-%d'),
        is_active=True,
        auto_book_enabled=False,
        preferred_lot_id=None,
    )
    db.session.add(new_sub)
    _send_notification(
        current_user,
        "Subscription Activated",
        f"Your {plan['name']} {_subscription_cycle_label(billing_cycle)} plan is active. Payment received: Rs {round(float(payable_amount), 2)} via {method.upper()}.",
    )
    db.session.commit()

    flash(f"{plan['name']} {_subscription_cycle_label(billing_cycle)} plan activated successfully.", "success")
    return redirect("/user/subscriptions")


@app.route("/subscription/cancel", methods=["POST"])
@login_required
def cancel_subscription():
    active_sub = _get_active_subscription(current_user.id)
    if not active_sub:
        flash("No active subscription found.", "warning")
        return redirect("/user/subscriptions")

    start_date = datetime.strptime(active_sub.start_date, '%Y-%m-%d').date()
    end_date = datetime.strptime(active_sub.end_date, '%Y-%m-%d').date()
    today = datetime.now().date()

    total_days = max((end_date - start_date).days, 1)
    remaining_days = max((end_date - today).days, 0)
    paid_amount = _subscription_paid_amount(active_sub)
    refund_amount = round((paid_amount * remaining_days) / total_days, 2) if remaining_days > 0 else 0

    if refund_amount > 0:
        _record_wallet_transaction(
            current_user,
            "refund",
            refund_amount,
            f"Subscription cancellation refund ({active_sub.tier.title()})",
        )

    active_sub.is_active = False
    db.session.commit()
    if refund_amount > 0:
        flash(f"Refund successful in wallet: Rs {refund_amount}", "success")
    else:
        flash("Subscription cancelled. No refundable days left.", "info")
    return redirect("/user/subscriptions")


@app.route("/alert/subscribe", methods=["POST"])
@login_required
def subscribe_availability_alert():
    lot_id = request.form.get("lot_id")
    if not lot_id:
        flash("Invalid lot selection.", "danger")
        return redirect(request.referrer or "/user/dashboard")
    lot_id = int(lot_id)

    existing = db.session.query(SpotAvailabilityAlert).filter_by(user_id=current_user.id, lot_id=lot_id).first()
    if existing:
        existing.is_active = True
    else:
        db.session.add(
            SpotAvailabilityAlert(
                user_id=current_user.id,
                lot_id=lot_id,
                is_active=True,
                created_at=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            )
        )
    db.session.commit()
    flash("You will be notified when a spot is available.", "info")
    return redirect(request.referrer or "/user/dashboard")


@app.route("/user/favorites")
@login_required
def user_favorites():
    favorite_entries = db.session.query(FavoriteParkingLot).filter_by(user_id=current_user.id).all()
    favorite_lot_ids = {fav.lot_id for fav in favorite_entries}

    if favorite_lot_ids:
        favorite_lots = db.session.query(ParkingLot).filter(ParkingLot.id.in_(favorite_lot_ids)).all()
    else:
        favorite_lots = []

    avg_ratings = _build_avg_ratings(favorite_lots)

    return render_template(
        "/user/favorites.html",
        favorite_lots=favorite_lots,
        avg_ratings=avg_ratings,
        favorite_lot_ids=favorite_lot_ids,
    )

@app.route("/user/search", methods = ["GET", "POST"])
@login_required
def user_search():
    all_users = db.session.query(User).all()

    user_histories = {
        user.id: ReservedParkingSpot.query.filter_by(user_id=user.id).all()
        for user in all_users
    }

    if request.method == "GET":
        return render_template(
            "/user/search.html",
            avg_ratings={},
            favorite_lot_ids=set(),
            results=[],
            query_text="",
        )
    elif request.method == "POST":
        type = request.form.get("searchby")
        query = (request.form.get("search_query") or "").strip()
        smart_query = (request.form.get("smart_search") or "").strip()
        query_text = smart_query or query
        result = []

        if query_text:
            if type in {"name", "address", "city", "pincode"}:
                # Legacy radio-based path support.
                if type == "name":
                    result = db.session.query(ParkingLot).filter(ParkingLot.prime_location_name.ilike(f"%{query_text}%")).all()
                elif type == "address":
                    result = db.session.query(ParkingLot).filter(ParkingLot.address.ilike(f"%{query_text}%")).all()
                elif type == "city":
                    result = db.session.query(ParkingLot).filter(ParkingLot.city.ilike(f"%{query_text}%")).all()
                elif type == "pincode":
                    result = db.session.query(ParkingLot).filter(cast(ParkingLot.pin_code, String).ilike(f"%{query_text}%")).all()
            else:
                # Smart search across key parking attributes.
                result = (
                    db.session.query(ParkingLot)
                    .filter(
                        or_(
                            ParkingLot.prime_location_name.ilike(f"%{query_text}%"),
                            ParkingLot.address.ilike(f"%{query_text}%"),
                            ParkingLot.city.ilike(f"%{query_text}%"),
                            cast(ParkingLot.pin_code, String).ilike(f"%{query_text}%"),
                        )
                    )
                    .all()
                )

        avg_ratings = _build_avg_ratings(result)
        favorite_lot_ids = _build_favorite_ids(current_user.id)
        return render_template(
            "/user/search.html",
            results=result,
            type=type or "smart",
            user_histories=user_histories,
            request=request,
            avg_ratings=avg_ratings,
            favorite_lot_ids=favorite_lot_ids,
            query_text=query_text,
        )

@app.route('/user/summary')
@login_required
def user_summary():
    now = datetime.now()
    bookings = (
        ReservedParkingSpot.query
        .filter_by(user_id=current_user.id)
        .order_by(ReservedParkingSpot.id.desc())
        .all()
    )

    summary_data = []
    location_counts = {}
    total_duration_minutes = 0
    completed_spend_total = 0.0
    month_spend_total = 0.0
    highest_cost_booking = 0.0

    for booking in bookings:
        in_time = datetime.strptime(booking.parking_timestamp, "%Y-%m-%d %H:%M:%S")
        is_active = booking.leaving_timestamp == "Not yet left"
        out_time = now if is_active else datetime.strptime(booking.leaving_timestamp, "%Y-%m-%d %H:%M:%S")
        duration_seconds = max((out_time - in_time).total_seconds(), 0)
        duration_minutes = int(duration_seconds // 60)
        hourly_rate = float(getattr(booking, "parkingCost_unitTime", 0) or 0)
        cost_value = float(booking.total_cost) if booking.total_cost is not None else round((duration_seconds / 3600) * hourly_rate, 2)
        if is_active and booking.planned_amount is not None:
            # Show planned amount for active bookings where final billing is not yet generated.
            cost_value = float(booking.planned_amount)

        lot_name = booking.Parking_Lot.prime_location_name
        location_counts[lot_name] = location_counts.get(lot_name, 0) + 1
        total_duration_minutes += duration_minutes

        if not is_active:
            completed_spend_total += cost_value
            if out_time.year == now.year and out_time.month == now.month:
                month_spend_total += cost_value

        highest_cost_booking = max(highest_cost_booking, cost_value)

        summary_data.append({
            "spot_id": booking.spot_id,
            "lot_name": lot_name,
            "location": f"{booking.Parking_Lot.city}",
            "in_time": in_time.strftime("%Y-%m-%d %H:%M:%S"),
            "out_time": booking.leaving_timestamp if not is_active else "In Progress",
            "duration": _duration_label(duration_minutes),
            "duration_minutes": duration_minutes,
            "vehicle_number": booking.vehicle_number,
            "cost": f"₹{cost_value:.2f}",
            "cost_value": round(cost_value, 2),
            "status": "Active" if is_active else "Completed",
            "date": in_time.strftime("%Y-%m-%d"),
        })

    total_bookings = len(summary_data)
    avg_duration_minutes = int(round(total_duration_minutes / total_bookings)) if total_bookings else 0
    most_visited_location = max(location_counts, key=location_counts.get) if location_counts else "-"

    location_options = sorted({entry["lot_name"] for entry in summary_data})
    vehicle_options = sorted({entry["vehicle_number"] for entry in summary_data if entry["vehicle_number"]})

    return render_template(
        '/user/summary.html',
        summary_data=summary_data,
        location_options=location_options,
        vehicle_options=vehicle_options,
        summary_stats={
            "total_bookings": total_bookings,
            "total_spend": round(completed_spend_total, 2),
            "average_duration": _duration_label(avg_duration_minutes),
            "most_visited_location": most_visited_location,
            "month_spend": round(month_spend_total, 2),
            "highest_cost_booking": round(highest_cost_booking, 2),
        },
    )


@app.route('/user/summary/export-csv')
@login_required
def user_summary_export_csv():
    bookings = (
        ReservedParkingSpot.query
        .filter_by(user_id=current_user.id)
        .order_by(ReservedParkingSpot.id.desc())
        .all()
    )

    csv_buffer = StringIO()
    writer = csv.writer(csv_buffer)
    writer.writerow(["Spot ID", "Lot Name", "Location", "In Time", "Out Time", "Duration", "Vehicle No", "Status", "Cost"])

    now = datetime.now()
    for booking in bookings:
        in_time = datetime.strptime(booking.parking_timestamp, "%Y-%m-%d %H:%M:%S")
        is_active = booking.leaving_timestamp == "Not yet left"
        out_time = now if is_active else datetime.strptime(booking.leaving_timestamp, "%Y-%m-%d %H:%M:%S")
        duration_minutes = int(max((out_time - in_time).total_seconds(), 0) // 60)
        hourly_rate = float(getattr(booking, "parkingCost_unitTime", 0) or 0)
        cost_value = float(booking.total_cost) if booking.total_cost is not None else round((max((out_time - in_time).total_seconds(), 0) / 3600) * hourly_rate, 2)
        if is_active and booking.planned_amount is not None:
            cost_value = float(booking.planned_amount)

        writer.writerow([
            booking.spot_id,
            booking.Parking_Lot.prime_location_name,
            booking.Parking_Lot.city,
            in_time.strftime("%Y-%m-%d %H:%M:%S"),
            booking.leaving_timestamp if not is_active else "In Progress",
            _duration_label(duration_minutes),
            booking.vehicle_number,
            "Active" if is_active else "Completed",
            f"{cost_value:.2f}",
        ])

    output = BytesIO()
    output.write(csv_buffer.getvalue().encode("utf-8"))
    output.seek(0)
    return send_file(output, as_attachment=True, download_name="booking_summary.csv", mimetype="text/csv")


@app.route("/parkingLots", methods=["POST"])
def parkingLot():
    if request.args.get("task") == "create":
        par_name = request.form.get("name")
        par_price = request.form.get("price")
        par_add = request.form.get("address")
        par_city = request.form.get("city")
        par_pin = request.form.get("pincode")
        par_max = request.form.get("maximum_number_of_spots")
        parking = db.session.query(ParkingLot).filter_by(prime_location_name=par_name).first()
        if parking:
            flash('Parking Lot Already Existed !!', 'warning')
            return redirect('/admin/dashboard')
        else:
            new_par = ParkingLot(prime_location_name = par_name, price = par_price, address = par_add, city = par_city, pin_code = par_pin, maximum_number_of_spots = par_max)
            db.session.add(new_par)
            db.session.commit()
            flash('Parking Lot Created !!', 'success')
            return redirect('/admin/dashboard')
    elif request.args.get("task") == "edit":
        par_name = request.form.get("name")
        par_price = request.form.get("price")
        par_add = request.form.get("address")
        par_city = request.form.get("city")
        par_pin = request.form.get("pincode")
        par_max = int(request.form.get("maximum_number_of_spots")) #ensure that it is a integer
        parking = db.session.query(ParkingLot).filter_by(prime_location_name=par_name).first()
        if parking:
            # Get current number of ParkingSpots
            current_spots = db.session.query(ParkingSpot).filter_by(lot_id=parking.id).all()
            current_count = len(current_spots)

            # Update ParkingLot fields
            parking.prime_location_name = par_name
            parking.price = par_price
            parking.address = par_add
            parking.city = par_city
            parking.pin_code = par_pin
            parking.maximum_number_of_spots = par_max
            
            # Handle difference in spot count
            if par_max > current_count:
                # Add new spots
                for _ in range(current_count + 1, par_max + 1):
                    new_spot = ParkingSpot(lot_id=parking.id, status='A')
                    db.session.add(new_spot)
            elif par_max < current_count:
                # Remove extra spots (Only remove available ones to avoid deleting reserved)
                removable_spots = [spot for spot in current_spots if spot.status == 'A']
                for spot in removable_spots[:current_count - par_max]:
                    db.session.delete(spot)
            db.session.commit()
            flash('Parking Lot Edited !!', 'success')
            return redirect('/admin/dashboard')
        else:
            flash('Parking Lot Does not Exist !!', 'warning')
            return redirect('/admin/dashboard')

@app.route("/booking", methods=["POST"])
@login_required
def booking():
    lot_id = request.form.get("lot_id", type=int)
    vehicle_no = request.form.get("vehicle_number")
    duration_minutes = _parse_duration_minutes(request.form.get("duration_minutes"))

    reservation, error_message = _create_booking_reservation(
        current_user.id,
        lot_id,
        vehicle_no,
        duration_minutes=duration_minutes,
    )
    if error_message:
        flash(error_message, "danger")
        return redirect("/user/dashboard")

    flash("Parking Spot Booked Successfully!", "success")
    return redirect("/user/dashboard")


@app.route("/payment/checkout", methods=["GET"])
@login_required
def payment_checkout():
    lot_id = request.args.get("lot_id", type=int)
    vehicle_number = _format_vehicle_number(request.args.get("vehicle_number"))
    duration_minutes = _parse_duration_minutes(request.args.get("duration_minutes"))

    lot = db.session.query(ParkingLot).filter_by(id=lot_id).first()
    if not lot:
        flash("Invalid parking lot selected.", "danger")
        return redirect("/user/dashboard")

    refund_rules = [
        {"label": "Within 15 minutes", "refund": "100%"},
        {"label": "Within 1 hour", "refund": "50%"},
        {"label": "After 1 hour", "refund": "0%"},
    ]

    active_booking = _get_active_booking_for_vehicle(current_user.id, vehicle_number)
    active_subscription = _get_active_subscription(current_user.id)
    pricing_breakdown = _build_pricing_breakdown(lot.price, duration_minutes, active_subscription)
    payable_amount = pricing_breakdown["final_amount"]

    return render_template(
        "/user/payment_options.html",
        lot=lot,
        vehicle_number=vehicle_number,
        duration_minutes=duration_minutes,
        duration_label=_duration_label(duration_minutes),
        payable_amount=payable_amount,
        pricing_breakdown=pricing_breakdown,
        refund_rules=refund_rules,
        active_booking=active_booking,
    )


@app.route("/payment/checkout/card", methods=["GET"])
@login_required
def payment_checkout_card():
    lot_id = request.args.get("lot_id", type=int)
    vehicle_number = _format_vehicle_number(request.args.get("vehicle_number"))
    duration_minutes = _parse_duration_minutes(request.args.get("duration_minutes"))

    lot = db.session.query(ParkingLot).filter_by(id=lot_id).first()
    if not lot:
        flash("Invalid parking lot selected.", "danger")
        return redirect("/user/dashboard")

    refund_rules = [
        {"label": "Within 15 minutes", "refund": "100%"},
        {"label": "Within 1 hour", "refund": "50%"},
        {"label": "After 1 hour", "refund": "0%"},
    ]

    active_booking = _get_active_booking_for_vehicle(current_user.id, vehicle_number)
    active_subscription = _get_active_subscription(current_user.id)
    pricing_breakdown = _build_pricing_breakdown(lot.price, duration_minutes, active_subscription)
    payable_amount = pricing_breakdown["final_amount"]

    return render_template(
        "/user/payment_checkout.html",
        lot=lot,
        vehicle_number=vehicle_number,
        duration_minutes=duration_minutes,
        duration_label=_duration_label(duration_minutes),
        payable_amount=payable_amount,
        pricing_breakdown=pricing_breakdown,
        refund_rules=refund_rules,
        active_booking=active_booking,
    )


@app.route("/payment/checkout/upi", methods=["GET"])
@login_required
def payment_checkout_upi():
    lot_id = request.args.get("lot_id", type=int)
    vehicle_number = _format_vehicle_number(request.args.get("vehicle_number"))
    duration_minutes = _parse_duration_minutes(request.args.get("duration_minutes"))

    lot = db.session.query(ParkingLot).filter_by(id=lot_id).first()
    if not lot:
        flash("Invalid parking lot selected.", "danger")
        return redirect("/user/dashboard")

    refund_rules = [
        {"label": "Within 15 minutes", "refund": "100%"},
        {"label": "Within 1 hour", "refund": "50%"},
        {"label": "After 1 hour", "refund": "0%"},
    ]

    active_booking = _get_active_booking_for_vehicle(current_user.id, vehicle_number)
    active_subscription = _get_active_subscription(current_user.id)
    pricing_breakdown = _build_pricing_breakdown(lot.price, duration_minutes, active_subscription)
    payable_amount = pricing_breakdown["final_amount"]

    return render_template(
        "/user/payment_upi.html",
        lot=lot,
        vehicle_number=vehicle_number,
        duration_minutes=duration_minutes,
        duration_label=_duration_label(duration_minutes),
        payable_amount=payable_amount,
        pricing_breakdown=pricing_breakdown,
        refund_rules=refund_rules,
        active_booking=active_booking,
        payment_label=f"Pay Rs {payable_amount:.2f} Now",
    )


@app.route("/payment/checkout/wallet", methods=["GET"])
@login_required
def payment_checkout_wallet():
    lot_id = request.args.get("lot_id", type=int)
    vehicle_number = _format_vehicle_number(request.args.get("vehicle_number"))
    duration_minutes = _parse_duration_minutes(request.args.get("duration_minutes"))

    lot = db.session.query(ParkingLot).filter_by(id=lot_id).first()
    if not lot:
        flash("Invalid parking lot selected.", "danger")
        return redirect("/user/dashboard")

    refund_rules = [
        {"label": "Within 15 minutes", "refund": "100%"},
        {"label": "Within 1 hour", "refund": "50%"},
        {"label": "After 1 hour", "refund": "0%"},
    ]

    active_booking = _get_active_booking_for_vehicle(current_user.id, vehicle_number)
    active_subscription = _get_active_subscription(current_user.id)
    pricing_breakdown = _build_pricing_breakdown(lot.price, duration_minutes, active_subscription)
    payable_amount = pricing_breakdown["final_amount"]

    wallet_balance = _wallet_balance(current_user)
    insufficient_balance = wallet_balance < float(payable_amount)

    return render_template(
        "/user/payment_wallet.html",
        lot=lot,
        vehicle_number=vehicle_number,
        duration_minutes=duration_minutes,
        duration_label=_duration_label(duration_minutes),
        payable_amount=payable_amount,
        pricing_breakdown=pricing_breakdown,
        refund_rules=refund_rules,
        active_booking=active_booking,
        wallet_balance=wallet_balance,
        insufficient_balance=insufficient_balance,
        payment_label=f"Pay Rs {payable_amount:.2f} from Wallet",
    )


@app.route("/payment/confirm/wallet", methods=["POST"])
@login_required
def payment_confirm_wallet():
    payload = request.get_json(silent=True) or {}
    lot_id = payload.get("lot_id")
    vehicle_number = _format_vehicle_number(payload.get("vehicle_number"))
    duration_minutes = _parse_duration_minutes(payload.get("duration_minutes"))

    if not lot_id:
        return jsonify({"success": False, "message": "Invalid lot selected."}), 400
    if not vehicle_number:
        return jsonify({"success": False, "message": "Vehicle number is required."}), 400

    lot = db.session.query(ParkingLot).filter_by(id=int(lot_id)).first()
    if not lot:
        return jsonify({"success": False, "message": "Invalid parking lot selected."}), 400

    active_subscription = _get_active_subscription(current_user.id)
    payable_amount = _calculate_parking_amount(lot.price, duration_minutes, active_subscription)

    if _wallet_balance(current_user) < float(payable_amount):
        return jsonify({"success": False, "message": "Insufficient wallet balance."}), 400

    reservation, error_message = _create_booking_reservation(
        current_user.id,
        int(lot_id),
        vehicle_number,
        duration_minutes=duration_minutes,
        commit=False,
    )
    if error_message:
        db.session.rollback()
        return jsonify({"success": False, "message": error_message}), 400

    _record_wallet_transaction(current_user, "debit", payable_amount, f"Parking payment for booking #{reservation.id}")
    db.session.commit()

    return jsonify(
        {
            "success": True,
            "message": "Wallet payment successful. Booking confirmed.",
            "booking_id": reservation.id,
            "spot_id": reservation.spot_id,
            "lot_name": reservation.Parking_Lot.prime_location_name,
            "wallet_balance": current_user.wallet_balance,
        }
    )


@app.route("/payment/checkout/fastag", methods=["GET"])
@login_required
def payment_checkout_fastag():
    lot_id = request.args.get("lot_id", type=int)
    vehicle_number = _format_vehicle_number(request.args.get("vehicle_number"))
    duration_minutes = _parse_duration_minutes(request.args.get("duration_minutes"))
    return redirect(url_for("payment_checkout_wallet", lot_id=lot_id, vehicle_number=vehicle_number, duration_minutes=duration_minutes))


@app.route("/payment/confirm", methods=["POST"])
@login_required
def payment_confirm():
    payload = request.get_json(silent=True) or {}
    lot_id = payload.get("lot_id")
    vehicle_number = _format_vehicle_number(payload.get("vehicle_number"))
    duration_minutes = _parse_duration_minutes(payload.get("duration_minutes"))

    if not lot_id:
        return jsonify({"success": False, "message": "Invalid lot selected."}), 400
    if not vehicle_number:
        return jsonify({"success": False, "message": "Vehicle number is required."}), 400

    reservation, error_message = _create_booking_reservation(
        current_user.id,
        int(lot_id),
        vehicle_number,
        duration_minutes=duration_minutes,
    )
    if error_message:
        return jsonify({"success": False, "message": error_message}), 400

    return jsonify(
        {
            "success": True,
            "message": "Payment successful. Booking confirmed.",
            "booking_id": reservation.id,
            "spot_id": reservation.spot_id,
            "lot_name": reservation.Parking_Lot.prime_location_name,
        }
    )

@app.route("/release/<int:booking_id>", methods=["POST"])
@login_required
def release_spot(booking_id):
    # Fetch the reservation with the given ID and confirm it belongs to the current user
    reservation = ReservedParkingSpot.query.filter_by(id=booking_id, user_id=current_user.id).first()
    
    if not reservation:
        flash("Reservation not found.", "danger")
        return redirect("/user/dashboard")

    if reservation.leaving_timestamp != "Not yet left":
        flash("Spot already released.", "warning")
        return redirect("/user/dashboard")

    # Set leaving timestamp to now
    now_dt = datetime.now()
    reservation.leaving_timestamp = now_dt.strftime('%Y-%m-%d %H:%M:%S')

    start_dt = datetime.strptime(reservation.parking_timestamp, '%Y-%m-%d %H:%M:%S')
    parked_hours = max((now_dt - start_dt).total_seconds() / 3600, 0)
    parked_minutes = int(round(parked_hours * 60))
    hourly_rate = float(reservation.parkingCost_unitTime or reservation.Parking_Lot.price or 0)
    active_subscription = _get_active_subscription(current_user.id)
    billed_tier = _infer_subscription_tier_from_reservation(reservation) or _subscription_tier(active_subscription)
    base_paid_amount = float(reservation.planned_amount if reservation.planned_amount is not None else hourly_rate)
    total_amount = _calculate_parking_amount(hourly_rate, parked_minutes, billed_tier)
    reservation.billed_amount = total_amount
    reservation.refund_amount = round(max(base_paid_amount - total_amount, 0), 2)
    reservation.total_cost = total_amount

    # Fetch the associated spot
    spot = ParkingSpot.query.filter_by(id=reservation.spot_id).first()
    if spot:
        spot.status = 'A'  # Mark it as available
        _notify_spot_available(spot.lot_id)

    if total_amount < base_paid_amount:
        _credit_wallet(current_user, reservation.refund_amount, f"Refund for early release booking #{reservation.id}")
    elif total_amount > base_paid_amount:
        penalty_amount = round(total_amount - base_paid_amount, 2)
        _record_wallet_transaction(current_user, "debit", penalty_amount, f"Overtime penalty for booking #{reservation.id}", allow_negative=True)

    _credit_basic_cashback_if_eligible(current_user, billed_tier, total_amount, reservation.id)

    db.session.commit()
    flash("Spot released successfully.", "success")
    return redirect("/user/dashboard")


@app.route("/cancel/<int:booking_id>", methods=["POST"])
@login_required
def cancel_booking(booking_id):
    reservation = ReservedParkingSpot.query.filter_by(id=booking_id, user_id=current_user.id).first()

    if not reservation:
        flash("Reservation not found.", "danger")
        return redirect("/user/dashboard")

    if reservation.leaving_timestamp != "Not yet left":
        flash("Booking already closed.", "warning")
        return redirect("/user/dashboard")

    now_dt = datetime.now()
    start_dt = datetime.strptime(reservation.parking_timestamp, '%Y-%m-%d %H:%M:%S')
    parked_hours = max((now_dt - start_dt).total_seconds() / 3600, 0)
    parked_minutes = int(round(parked_hours * 60))
    hourly_rate = float(reservation.parkingCost_unitTime or reservation.Parking_Lot.price or 0)
    active_subscription = _get_active_subscription(current_user.id)
    billed_tier = _infer_subscription_tier_from_reservation(reservation) or _subscription_tier(active_subscription)
    gross_cost = _calculate_parking_amount(hourly_rate, parked_minutes, billed_tier)

    if parked_hours <= 0.25:
        refund_percent = 100
    elif parked_hours <= 1:
        refund_percent = 50
    else:
        refund_percent = 0

    base_paid_amount = float(reservation.planned_amount if reservation.planned_amount is not None else (hourly_rate if hourly_rate > 0 else gross_cost))
    refund_amount = round(max(base_paid_amount - gross_cost, 0), 2) if refund_percent > 0 else 0
    reservation.billed_amount = gross_cost
    reservation.refund_amount = refund_amount
    reservation.total_cost = gross_cost
    reservation.leaving_timestamp = now_dt.strftime('%Y-%m-%d %H:%M:%S')

    spot = ParkingSpot.query.filter_by(id=reservation.spot_id).first()
    if spot:
        spot.status = 'A'
        _notify_spot_available(spot.lot_id)

    if refund_amount > 0:
        _credit_wallet(current_user, refund_amount, f"Refund for booking #{reservation.id}")
    elif gross_cost > base_paid_amount:
        penalty_amount = round(gross_cost - base_paid_amount, 2)
        _record_wallet_transaction(current_user, "debit", penalty_amount, f"Overtime penalty for booking #{reservation.id}", allow_negative=True)

    _credit_basic_cashback_if_eligible(current_user, billed_tier, gross_cost, reservation.id)

    db.session.commit()
    flash(
        f"Booking cancelled. Refund: Rs {refund_amount} ({refund_percent}%). Final charge: Rs {reservation.total_cost}.",
        "success",
    )
    return redirect("/user/dashboard")


@app.route("/favorite/toggle", methods=["POST"])
@login_required
def toggle_favorite():
    lot_id = request.form.get("lot_id")
    if not lot_id:
        flash("Invalid parking lot.", "danger")
        return redirect(request.referrer or "/user/dashboard")
    lot_id = int(lot_id)
    lot = db.session.query(ParkingLot).filter_by(id=lot_id).first()

    if not lot:
        flash("Parking lot not found.", "danger")
        return redirect(request.referrer or "/user/dashboard")

    favorite = db.session.query(FavoriteParkingLot).filter_by(user_id=current_user.id, lot_id=lot_id).first()
    if favorite:
        db.session.delete(favorite)
        flash("Removed from favorites.", "info")
    else:
        db.session.add(FavoriteParkingLot(user_id=current_user.id, lot_id=lot_id))
        flash("Added to favorites.", "success")

    db.session.commit()
    return redirect(request.referrer or "/user/dashboard")


@app.route("/review", methods=["POST"])
@login_required
def submit_review():
    lot_id = request.form.get("lot_id")
    rating = request.form.get("rating")
    comment = request.form.get("comment", "")

    if not lot_id or not rating:
        flash("Rating submission failed.", "danger")
        return redirect(request.referrer or "/user/dashboard")

    lot_id = int(lot_id)
    rating = int(rating)
    if rating < 1 or rating > 5:
        flash("Rating should be between 1 and 5.", "warning")
        return redirect(request.referrer or "/user/dashboard")

    completed_booking = db.session.query(ReservedParkingSpot).filter(
        ReservedParkingSpot.user_id == current_user.id,
        ReservedParkingSpot.lot_id == lot_id,
        ReservedParkingSpot.leaving_timestamp != "Not yet left",
    ).first()

    if not completed_booking:
        flash("You can review a lot only after completing a booking.", "warning")
        return redirect(request.referrer or "/user/dashboard")

    review = db.session.query(ParkingLotReview).filter_by(user_id=current_user.id, lot_id=lot_id).first()
    if review:
        review.rating = rating
        review.comment = comment.strip()
        review.created_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        flash("Your review has been updated.", "success")
    else:
        db.session.add(
            ParkingLotReview(
                lot_id=lot_id,
                user_id=current_user.id,
                rating=rating,
                comment=comment.strip(),
                created_at=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            )
        )
        flash("Thanks for rating this parking lot.", "success")

    db.session.commit()
    return redirect(request.referrer or "/user/dashboard")


@app.route("/user/receipt/<int:booking_id>")
@login_required
def user_receipt_pdf(booking_id):
    booking = db.session.query(ReservedParkingSpot).filter_by(id=booking_id, user_id=current_user.id).first()
    if not booking:
        flash("Booking not found.", "danger")
        return redirect("/user/dashboard")

    if booking.leaving_timestamp == "Not yet left":
        flash("Please release or cancel booking before downloading receipt.", "warning")
        return redirect("/user/dashboard")

    if booking.total_cost is None:
        in_time = datetime.strptime(booking.parking_timestamp, '%Y-%m-%d %H:%M:%S')
        out_time = datetime.strptime(booking.leaving_timestamp, '%Y-%m-%d %H:%M:%S')
        recomputed_billed = round((out_time - in_time).total_seconds() / 3600 * booking.parkingCost_unitTime, 2)
        booking.billed_amount = recomputed_billed
        booking.refund_amount = booking.refund_amount or 0
        booking.total_cost = round(recomputed_billed - booking.refund_amount, 2)
        db.session.commit()

    billed_amount = booking.billed_amount if booking.billed_amount is not None else booking.total_cost
    refund_amount = booking.refund_amount if booking.refund_amount is not None else 0
    final_paid = booking.total_cost if booking.total_cost is not None else round(billed_amount - refund_amount, 2)

    if booking.billed_amount is None or booking.refund_amount is None:
        booking.billed_amount = billed_amount
        booking.refund_amount = refund_amount
        booking.total_cost = final_paid
        db.session.commit()

    receipt_rows = [
        ["Receipt ID", booking.id],
        ["Customer Name", current_user.name],
        ["Parking Lot", booking.Parking_Lot.prime_location_name],
        ["Spot ID", booking.spot_id],
        ["Vehicle Number", booking.vehicle_number],
        ["Check-in Time", booking.parking_timestamp],
        ["Check-out Time", booking.leaving_timestamp],
        ["Price Per Hour", f"Rs {booking.parkingCost_unitTime}"],
        ["Billed Amount", f"Rs {round(billed_amount, 2)}"],
        ["Refund Amount", f"Rs {round(refund_amount, 2)}"],
        ["Final Paid", f"Rs {round(final_paid, 2)}"],
    ]
    pdf_buffer = _build_pdf_bytes(
        "Booking Receipt",
        ["Field", "Details"],
        receipt_rows,
        [["Generated On", datetime.now().strftime('%Y-%m-%d %H:%M:%S')]],
    )
    lot_name_slug = secure_filename(booking.Parking_Lot.prime_location_name).replace("_", "-").lower()
    return send_file(
        pdf_buffer,
        as_attachment=True,
        download_name=f"receipt_{lot_name_slug}_spot-{booking.spot_id}_{booking.id}.pdf",
        mimetype="application/pdf",
    )


@app.route("/user/monthly-invoice")
@login_required
def user_monthly_invoice():
    now = datetime.now()
    bookings = db.session.query(ReservedParkingSpot).filter_by(user_id=current_user.id).all()
    invoice_table_rows = []
    total = 0
    for booking in bookings:
        if booking.leaving_timestamp == "Not yet left":
            continue
        leaving_dt = datetime.strptime(booking.leaving_timestamp, '%Y-%m-%d %H:%M:%S')
        if leaving_dt.year == now.year and leaving_dt.month == now.month:
            row_cost = booking.total_cost or 0
            total += row_cost
            invoice_table_rows.append(
                [
                    booking.id,
                    booking.Parking_Lot.prime_location_name,
                    booking.parking_timestamp,
                    booking.leaving_timestamp,
                    f"Rs {round(row_cost, 2)}",
                ]
            )

    if not invoice_table_rows:
        invoice_table_rows = [["-", "No completed bookings", "-", "-", "Rs 0.00"]]

    pdf_buffer = _build_pdf_bytes(
        "Monthly Invoice",
        ["Booking ID", "Parking Lot", "Check-in", "Check-out", "Amount"],
        invoice_table_rows,
        [
            ["Customer", current_user.name],
            ["Month", f"{month_name[now.month]} {now.year}"],
            ["Total Amount", f"Rs {round(total, 2)}"],
        ],
    )
    return send_file(pdf_buffer, as_attachment=True, download_name=f"invoice_{now.year}_{now.month}.pdf", mimetype="application/pdf")


@app.route("/admin/user-report-pdf/<int:user_id>")
@login_required
def admin_user_report_pdf(user_id):
    user = db.session.query(User).filter_by(id=user_id).first()
    if not user:
        flash("User not found.", "danger")
        return redirect("/admin/dashboard")

    bookings = db.session.query(ReservedParkingSpot).filter_by(user_id=user.id).all()
    report_rows = []
    for booking in bookings:
        report_rows.append(
            [
                booking.id,
                booking.Parking_Lot.prime_location_name,
                booking.parking_timestamp,
                booking.leaving_timestamp,
                booking.vehicle_number,
                f"Rs {round(booking.total_cost if booking.total_cost is not None else 0, 2)}",
            ]
        )

    if not report_rows:
        report_rows = [["-", "No bookings", "-", "-", "-", "Rs 0.00"]]

    pdf_buffer = _build_pdf_bytes(
        "User Booking Report",
        ["Booking ID", "Parking Lot", "Check-in", "Check-out", "Vehicle", "Amount"],
        report_rows,
        [
            ["User ID", user.id],
            ["Name", user.name],
            ["Email", user.email],
            ["Phone", user.phone],
            ["Total Bookings", len(bookings)],
        ],
    )
    return send_file(pdf_buffer, as_attachment=True, download_name=f"user_{user.id}_report.pdf", mimetype="application/pdf")


@app.route("/admin/send-reminders", methods=["POST"])
@login_required
def send_all_booking_reminders():
    all_users = db.session.query(User).all()
    for user in all_users:
        _send_booking_reminders_for_user(user.id)
    db.session.commit()
    flash("Reminder notifications have been processed.", "success")
    return redirect("/admin/summary")


@app.route("/delete_parking/<int:lot_id>", methods=["POST"])
@login_required
def delete_parking(lot_id):
    lot = db.session.query(ParkingLot).filter_by(id=lot_id).first()

    if not lot:
        flash("Parking lot not found.", "danger")
        return redirect("/admin/dashboard")

    # Check if any of the spots are booked
    booked_spots = [spot for spot in lot.spots if spot.status == 'O']
    if booked_spots:
        flash("Cannot delete parking lot with active bookings.", "warning")
        return redirect("/admin/dashboard")

    # Also ensure no ReservedParkingSpot exists (historically)
    if lot.reserved_parking_spot:
        flash("Cannot delete parking lot with past reservations.", "warning")
        return redirect("/admin/dashboard")

    # Delete all associated spots first
    for spot in lot.spots:
        db.session.delete(spot)

    db.session.delete(lot)
    db.session.commit()
    flash("Parking lot deleted successfully.", "success")
    return redirect("/admin/dashboard")
