import secrets
from datetime import datetime

from flask import (
    Blueprint, render_template, request, redirect, url_for, flash, current_app
)
from flask_login import login_user, logout_user, login_required, current_user

from models import User

bp = Blueprint("auth", __name__)


# =============================================================
# REGISTRATION ROUTES
# =============================================================

@bp.route("/register", methods=["GET", "POST"])
def register():
    """Single-page registration form for Resident and Vendor."""
    if request.method == "POST":
        role = request.form.get("role", "").strip()
        if role not in ("resident", "vendor"):
            flash("Please choose a valid role.", "danger")
            return redirect(url_for("auth.register"))

        full_name = request.form.get("full_name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        confirm = request.form.get("confirm_password", "")
        contact = request.form.get("contact_number", "").strip()
        city = request.form.get("city", "").strip()

        if not full_name or not email or not password:
            flash("Please fill in all required fields.", "danger")
            return redirect(url_for("auth.register"))

        if password != confirm:
            flash("Passwords do not match.", "danger")
            return redirect(url_for("auth.register"))

        if len(password) < 6:
            flash("Password must be at least 6 characters.", "danger")
            return redirect(url_for("auth.register"))

        if User.first(email=email):
            flash("An account with this email already exists.", "danger")
            return redirect(url_for("auth.login"))

        # ---------------- RESIDENT ----------------
        if role == "resident":
            user = User(
                full_name=full_name, email=email, role="resident",
                contact_number=contact, city=city,
                address=request.form.get("address", "").strip(),
                is_active_flag=True, subscription_status="trial",
            )
            user.set_password(password)
            user.save()
            login_user(user)
            flash(f"Welcome, {full_name}!", "success")
            return redirect(url_for("resident.dashboard"))

        # ---------------- VENDOR ----------------
        elif role == "vendor":
            user = User(
                full_name=full_name, email=email, role="vendor",
                contact_number=contact, city=city,
                business_name=request.form.get("business_name", "").strip(),
                business_address=request.form.get("business_address", "").strip(),
                is_active_flag=True, subscription_status="trial",
                vendor_status="pending",
            )
            user.set_password(password)
            user.save()
            login_user(user)
            flash(f"Welcome, {full_name}! Your vendor account is pending verification.", "success")
            return redirect(url_for("vendor.dashboard"))

    # GET — show the registration page
    return render_template("register.html")


@bp.route("/register/<role>", methods=["GET", "POST"])
def register_continue(role):
    """LGU / DTI-DA registration (separate page)."""
    if role != "lgu":
        # Anything other than 'lgu' goes to the main register page
        return redirect(url_for("auth.register"))

    if request.method == "POST":
        full_name = request.form.get("full_name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        confirm = request.form.get("confirm_password", "")
        contact = request.form.get("contact_number", "").strip()
        city = request.form.get("city", "").strip()
        org_name = request.form.get("org_name", "").strip()
        division = request.form.get("division", "").strip()

        if not full_name or not email or not password:
            flash("Please fill in all required fields.", "danger")
            return redirect(url_for("auth.register_continue", role="lgu"))

        if password != confirm:
            flash("Passwords do not match.", "danger")
            return redirect(url_for("auth.register_continue", role="lgu"))

        if len(password) < 6:
            flash("Password must be at least 6 characters.", "danger")
            return redirect(url_for("auth.register_continue", role="lgu"))

        if not org_name or not division:
            flash("Organization and division are required for LGU accounts.", "danger")
            return redirect(url_for("auth.register_continue", role="lgu"))

        if User.first(email=email):
            flash("An account with this email already exists.", "danger")
            return redirect(url_for("auth.login"))

        user = User(
            full_name=full_name, email=email, role="lgu_staff",
            contact_number=contact, city=city,
            org_name=org_name, division=division,
            is_active_flag=False,
            subscription_status="pending",
        )
        user.set_password(password)
        user.save()

        flash(
            "Your LGU / DTI-DA account request has been submitted. "
            "An administrator will review it shortly.",
            "info",
        )
        return redirect(url_for("auth.login"))

    return render_template("register_lgu.html")


# =============================================================
# BACKWARD-COMPATIBILITY ALIAS
# =============================================================
# The alias below makes `url_for('auth.register_form', role='lgu')` work.
# It redirects to `register_continue`.

bp.add_url_rule(
    "/register/<role>/form",
    endpoint="register_form",
    view_func=register_continue,
    methods=["GET", "POST"],
)


# =============================================================
# LOGIN / LOGOUT
# =============================================================

@bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        login_role = request.form.get("login_as", "").strip() or None

        user = User.first(email=email)

        if not user or not user.check_password(password):
            flash("Invalid email or password.", "danger")
            return redirect(url_for("auth.login"))

        if not user.is_active_flag:
            flash(
                "Your account is pending admin approval. "
                "Please wait for a confirmation email or contact the administrator.",
                "warning",
            )
            return redirect(url_for("auth.login"))

        if login_role and user.role != login_role:
            flash(
                f"This account is registered as '{user.role}'. Please select the correct role.",
                "danger",
            )
            return redirect(url_for("auth.login"))

        login_user(user)
        flash(f"Welcome back, {user.full_name or user.email}!", "success")

        if user.role == "resident":
            return redirect(url_for("resident.dashboard"))
        elif user.role == "vendor":
            return redirect(url_for("vendor.dashboard"))
        elif user.role in ("lgu_staff", "dti_da"):
            return redirect(url_for("lgu.dashboard"))
        elif user.role == "admin":
            return redirect(url_for("admin.dashboard"))

        return redirect(url_for("public.home"))

    return render_template("login.html")


@bp.route("/logout")
@login_required
def logout():
    logout_user()
    flash("You have been logged out.", "info")
    return redirect(url_for("public.home"))


# =============================================================
# PASSWORD / ACCOUNT
# =============================================================

@bp.route("/change-password", methods=["GET", "POST"])
@login_required
def change_password():
    if request.method == "POST":
        current = request.form.get("current_password", "")
        new = request.form.get("new_password", "")
        confirm = request.form.get("confirm_password", "")

        if not current_user.check_password(current):
            flash("Current password is incorrect.", "danger")
            return redirect(url_for("auth.change_password"))

        if new != confirm:
            flash("New passwords do not match.", "danger")
            return redirect(url_for("auth.change_password"))

        if len(new) < 6:
            flash("Password must be at least 6 characters.", "danger")
            return redirect(url_for("auth.change_password"))

        current_user.set_password(new)
        current_user.save()
        flash("Password updated successfully.", "success")
        return redirect(url_for("public.home"))

    return render_template("change_password.html")


@bp.route("/edit-account", methods=["GET", "POST"])
@login_required
def edit_account():
    if request.method == "POST":
        current_user.full_name = request.form.get("full_name", "").strip() or current_user.full_name
        current_user.contact_number = request.form.get("contact_number", "").strip() or current_user.contact_number
        current_user.address = request.form.get("address", "").strip() or current_user.address
        current_user.city = request.form.get("city", "").strip() or current_user.city
        current_user.save()
        flash("Account updated successfully.", "success")
        return redirect(url_for("public.home"))

    return render_template("edit_account.html")


@bp.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():
    if request.method == "POST":
        flash("If your email is registered, you will receive a reset link.", "info")
        return redirect(url_for("auth.login"))
    return render_template("forgot_password.html")