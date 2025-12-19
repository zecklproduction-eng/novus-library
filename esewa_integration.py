# eSewa Payment Integration for NOVUS
# Add these routes to your Flask app in app.py

from flask import redirect, url_for, session, flash
from datetime import datetime, timedelta

def register_esewa_routes(app, get_conn):
    """Register eSewa payment routes"""
    
    @app.get("/billing/esewa-success")
    def esewa_payment_success():
        """Handle eSewa payment success callback"""
        if "user_id" not in session:
            return redirect(url_for("login"))

        # Get the pending plan from session
        pending_plan = session.get("pending_plan")
        uid = session.get("user_id")

        if not pending_plan or pending_plan not in {"pro", "ultimate"}:
            flash("Payment verification failed.", "danger")
            return redirect(url_for("profile"))

        # Apply the plan based on type
        expires_at = None
        if pending_plan == "pro":
            expires_at = (datetime.utcnow() + timedelta(days=30)).isoformat()
        elif pending_plan == "ultimate":
            expires_at = None  # Forever

        # Update user plan in database
        conn = get_conn()
        c = conn.cursor()
        c.execute("UPDATE users SET plan=?, plan_expires_at=? WHERE id=?", (pending_plan, expires_at, uid))
        conn.commit()
        conn.close()

        # Update session
        session["plan"] = pending_plan
        session["plan_expires_at"] = expires_at
        
        # Clear pending plan data
        session.pop("pending_plan", None)
        session.pop("pending_plan_amount", None)
        session.pop("pending_plan_user_id", None)

        flash(f"Payment successful! Plan upgraded to {pending_plan}.", "success")
        return redirect(url_for("profile"))

    @app.get("/billing/checkout")
    def billing_checkout():
        if "user_id" not in session:
            return redirect(url_for("login"))

        plan = (request.args.get("plan", "pro") or "pro").strip().lower()
        if plan not in {"basic", "pro", "ultimate"}:
            flash("Invalid plan selected.", "danger")
            return redirect(url_for("profile"))

        uid = session.get("user_id")
        if not uid:
            return redirect(url_for("login"))

        # Basic plan is free - no payment needed
        if plan == "basic":
            conn = get_conn()
            c = conn.cursor()
            c.execute("UPDATE users SET plan=?, plan_expires_at=? WHERE id=?", ("basic", None, uid))
            conn.commit()
            conn.close()
            session["plan"] = "basic"
            session["plan_expires_at"] = None
            flash("Plan updated to Basic.", "success")
            return redirect(url_for("profile"))

        # For paid plans (Pro/Ultimate), redirect to eSewa payment
        # eSewa payment amounts (in NPR)
        plan_amounts = {
            "pro": 499,  # Rs. 499 for Pro
            "ultimate": 999  # Rs. 999 for Ultimate
        }
        
        amount = plan_amounts.get(plan, 0)
        if not amount:
            flash("Invalid plan amount.", "danger")
            return redirect(url_for("profile"))

        # Store pending plan in session temporarily
        session["pending_plan"] = plan
        session["pending_plan_amount"] = amount
        session["pending_plan_user_id"] = uid

        # Redirect to eSewa payment gateway
        esewa_url = "https://uat.esewa.com.np/epay/main"
        
        # Generate transaction ID
        transaction_id = f"TXN{uid}{int(datetime.utcnow().timestamp())}"
        
        # eSewa requires a success and failure URL
        success_url = url_for("esewa_payment_success", _external=True)
        failure_url = url_for("profile", _external=True)

        # Prepare eSewa payment parameters
        params = {
            "amt": amount,
            "psc": 0,  # Service charge
            "pdc": 0,  # Delivery charge
            "txAmt": amount,
            "total": amount,
            "tAmt": amount,
            "pid": transaction_id,
            "scd": "EPAYTEST",  # eSewa merchant code (change to your actual code)
            "su": success_url,
            "fu": failure_url
        }
        
        query_string = "&".join([f"{k}={v}" for k, v in params.items()])
        return redirect(f"{esewa_url}?{query_string}")
