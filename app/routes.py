"""REST endpoints for subscriptions."""

from datetime import date

from flask import Blueprint, jsonify, request

from app.db import get_db

bp = Blueprint("api", __name__)

BILLING_CYCLES = {"monthly", "yearly"}


#payload validation
def validate(payload):
    """Return (clean_data, error_message)."""
    if not isinstance(payload, dict):
        return None, "Request body must be a JSON object"

    name = payload.get("name")
    if not isinstance(name, str) or not name.strip():
        return None, "name is required"

    cost = payload.get("cost")
    if isinstance(cost, bool) or not isinstance(cost, (int, float)) or cost < 0:
        return None, "cost must be a non-negative number"

    cycle = payload.get("billing_cycle")
    if cycle not in BILLING_CYCLES:
        return None, "billing_cycle must be 'monthly' or 'yearly'"

    try:
        renewal = date.fromisoformat(str(payload.get("renewal_date")))
    except ValueError:
        return None, "renewal_date must be YYYY-MM-DD"

    return {
        "name": name.strip(),
        "cost": float(cost),
        "billing_cycle": cycle,
        "renewal_date": renewal.isoformat(),
    }, None


#CRUD API
@bp.get("/health")
def health():
    return jsonify(status="ok")


@bp.get("/subscriptions")
def list_subscriptions():
    rows = get_db().execute("SELECT * FROM subscriptions ORDER BY renewal_date").fetchall()
    return jsonify([dict(r) for r in rows])


@bp.post("/subscriptions")
def create_subscription():
    data, error = validate(request.get_json(silent=True))
    if error:
        return jsonify(error=error), 400

    conn = get_db()
    cur = conn.execute(
        "INSERT INTO subscriptions (name, cost, billing_cycle, renewal_date) "
        "VALUES (:name, :cost, :billing_cycle, :renewal_date)",
        data,
    )
    conn.commit()
    return jsonify(id=cur.lastrowid, **data), 201


@bp.get("/subscriptions/<int:sub_id>")
def get_subscription(sub_id):
    row = get_db().execute("SELECT * FROM subscriptions WHERE id = ?", (sub_id,)).fetchone()
    if row is None:
        return jsonify(error="not found"), 404
    return jsonify(dict(row))


@bp.delete("/subscriptions/<int:sub_id>")
def delete_subscription(sub_id):
    conn = get_db()
    cur = conn.execute("DELETE FROM subscriptions WHERE id = ?", (sub_id,))
    conn.commit()
    if cur.rowcount == 0:
        return jsonify(error="not found"), 404
    return "", 204


@bp.get("/subscriptions/summary")
def summary():
    """Total monthly spend (yearly plans prorated to /12)."""
    rows = get_db().execute("SELECT cost, billing_cycle FROM subscriptions").fetchall()
    monthly = sum(r["cost"] if r["billing_cycle"] == "monthly" else r["cost"] / 12 for r in rows)
    return jsonify(count=len(rows), monthly_total=round(monthly, 2), yearly_total=round(monthly * 12, 2))
