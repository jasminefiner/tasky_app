from flask import render_template, redirect, url_for, flash, session, request
from flask_login import login_user, logout_user, current_user, login_required
from flask_mail import Message
from .forms import LogInForm, RegistrationForm, ChangePasswordForm, ResetPasswordRequestForm, PasswordResetForm, EmailChangeForm
from . import auth
from .. import db, mail
from ..models import User

@auth.route('/login', methods=['GET', 'POST'])
def login():
    form = LogInForm()
    if current_user.is_authenticated:
        flash('You are already logged in!', 'warning')
        return redirect(url_for('main.index'))
    if form.validate_on_submit():
        email = form.email.data
        password = form.password.data

        user = User.query.filter_by(email=email).first()

        if user and user.verify_password(password):
            login_user(user)
            next = request.args.get('next')
            if next is None or not next.startswith('/'):
                next = url_for('main.index')
            return redirect(next)
        flash("Invalid email or password", 'danger')
    for field, errors in form.errors.items():
        for error in errors:
            flash(u"Error in the %s field - %s" % (
                getattr(form, field).label.text,
                error
            ), 'danger')
    return render_template('auth/form.html', form=form, name='Log In', current_user=current_user)

@auth.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        if User.query.filter_by(email=form.email.data).first() is not None:
            flash('A user with that email address has already registered.', 'danger')
            return redirect(url_for('auth.register'))
        elif User.query.filter_by(username=form.username.data).first() is not None:
            flash('Username is taken.', 'danger')
            return redirect(url_for('auth.register'))

        # form is validated and all good. Create the user.
        user = User(email=form.email.data, username=form.username.data, password=form.password.data)
        db.session.add(user)
        db.session.commit()

        # Generate confirmation token
        token = user.generate_confirmation_token()

        # Send confirmation token to user
        msg = Message()
        msg.recipients = [user.email] # this will be user.email
        msg.html = render_template('auth/email/account_confirmation.html', user=user, token=token)
        mail.send(msg)
        flash('You have successfully registered. Please check your email to confirm your account.', 'success')
        return redirect(url_for('auth.login'))
    for field, errors in form.errors.items():
        for error in errors:
            flash(u"Error in the %s field - %s" % (
                getattr(form, field).label.text,
                error
            ), 'danger')
    return render_template('auth/form.html', form=form, name='Register', current_user=current_user)

@auth.route('/logout')
def logout():
    logout_user()
    flash('You have been logged out.', 'warning')
    return redirect(url_for('main.index'))

@auth.route('/confirm/<token>')
@login_required
def confirm(token):
    if current_user.confirmed:
        flash('current_user is confirmed')
        return redirect(url_for('main.index'))
    if current_user.confirm(token):
        db.session.commit()
        flash('You have successfully confirmed your account.', 'success')
    else:
        flash('Invalid confirmation token. Your token has either expired or is invalid.')
    return redirect(url_for('main.index'))

@auth.before_app_request
def before_request():
    if current_user.is_authenticated and not current_user.confirmed and request.blueprint != 'auth' and request.endpoint != 'static':
        return redirect(url_for('auth.unconfirmed'))

@auth.route('/unconfirmed')
@login_required
def unconfirmed():
    if current_user.confirmed:
        flash('You are confirmed!', 'success')
        return redirect(url_for('main.index'))
    return render_template('auth/unconfirmed.html', user=current_user)

@auth.route('/confirm')
@login_required
def resend_confirmation():
    if current_user.confirmed:
        flash('You are already confirmed. No need to send new link.', 'success')
        return redirect(url_for('main.index'))
    token = current_user.generate_confirmation_token()
    # Send confirmation token to user
    msg = Message()
    msg.recipients = [current_user.email] # this will be user.email
    msg.html = render_template('auth/email/account_confirmation.html', user=current_user, token=token)
    mail.send(msg)

    flash('A new confirmation token email has been send to you.', 'success')
    return redirect(url_for('main.index'))

@auth.route('/change_password', methods=['GET', 'POST'])
@login_required
def change_password():
    form = ChangePasswordForm()
    if form.validate_on_submit():
        if current_user.verify_password(form.oldpassword.data):
            current_user.change_password(form.newpassword.data)
            db.session.add(current_user)
            db.session.commit()
            flash('Your password has been updated!', 'success')
            return redirect(url_for('main.index'))
        flash('Your password is incorrect.', 'danger')
    for field, errors in form.errors.items():
        for error in errors:
            flash(u"Error in the %s field - %s" % (
                getattr(form, field).label.text,
                error
            ), 'danger')
    return render_template('auth/form.html', form=form, name='Change Password')

@auth.route('/password_reset_request', methods=['GET', 'POST'])
def password_reset_request():
    form = ResetPasswordRequestForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user is not None:
            token = user.generate_reset_password_token()
            msg = Message()
            msg.recipients = [form.email.data] # this will be user.email
            msg.html = render_template('auth/email/password_reset.html', user=user, token=token)
            mail.send(msg)
            flash('An email with a link to reset your password has been sent to you.', 'success')
            return redirect(url_for('main.index'))
        flash('Sorry, there is no account registered to that email address.', 'danger')
        return redirect(url_for('main.index'))
    return render_template('auth/form.html', form=form, name='Please enter your email address.')

@auth.route('/password_reset/<token>', methods=['GET', 'POST'])
def password_reset(token):
    form = PasswordResetForm()
    if not current_user.is_anonymous:
        flash('You are already logged in. You do not need to request a new password.', 'warning')
        return redirect(url_for('main.index'))
    if form.validate_on_submit():
        if User.password_reset(token, form.newpassword.data):
            db.session.commit()
            flash('Your password has been updated. Please log in.', 'success')
            return redirect(url_for('auth.login'))
        else:
            flash('Invalid confirmation token. Your token has either expired or is invalid.', 'danger')
            return redirect(url_for('auth.login'))
    for field, errors in form.errors.items():
        for error in errors:
            flash(u"Error in the %s field - %s" % (
                getattr(form, field).label.text,
                error
            ), 'danger')
    return render_template('auth/form.html', form=form, name='Reset Password')

@auth.route('/email_change_request', methods=['GET', 'POST'])
@login_required
def email_change_request():
    form = EmailChangeForm()
    if form.validate_on_submit():
        if User.query.filter_by(email=form.email.data):
            token = current_user.generate_email_change_token(form.email.data)
            msg = Message()
            msg.recipients = [form.email.data] # this will be user.email
            msg.html = render_template('auth/email/email_change.html', user=current_user, token=token)
            mail.send(msg)
            flash('An email with a link to confirm your new email address has been sent to you.', 'success')
            return redirect(url_for('main.index'))
        flash('That email is already registered. Please choose a different one.', 'danger')
    return render_template('auth/form.html', form=form, name='Change Email')

@auth.route('/email_change/<token>')
@login_required
def email_change(token):
    if current_user.email_change(token):
        db.session.commit()
        flash('You have successfully updated your email address.', 'success')
    else:
        flash('Invalid confirmation token. Your token has either expired or is invalid.')
    return redirect(url_for('main.index'))
