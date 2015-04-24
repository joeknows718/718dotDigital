from flask import render_template, redirect, request, url_for, flash
from . import auth
from .. import db
from flask.ext.login import login_user, logout_user, login_required, current_user
from ..models import User 
from .forms import LoginForm , RegistrationForm, ChangePasswordForm, PasswordResetRequestForm, PasswordResetForm, ChangeEmailForm
from ..emails import send_mail

@auth.before_app_request
def before_request():
	if current_user.is_authenticated(): 
		current_user.ping
		if not current_user.confirmed and request.endpoint[:5] != 'auth.':
			return redirect(url_for('auth.unconfirmed'))


@auth.route('/login', methods=['GET', 'POST'])
def login(): 
	form = LoginForm()
	if form.validate_on_submit():
		user = User.query.filter_by(email=form.email.data).first()
		if user is not None and user.verify_password(form.password.data):
			login_user(user, form.remember_me.data)
			return redirect(request.args.get('next') or url_for('main.index'))
		flash('Invalid user name or password.')
	return render_template('auth/login.html', form=form)


@auth.route('/logout')
@login_required
def logout():
	logout_user()
	flash('You have been logged out.')
	return redirect(url_for('main.index'))


@auth.route('/register', methods=['GET', 'POST'])
def register():
	form = RegistrationForm()
	if form.validate_on_submit():
		user = User(email=form.email.data,
					username=form.username.data,
					password=form.password.data)
		db.session.add(user)
		db.session.commit()
		token = user.generate_confirmation_token()
		send_mail(user.email, 'Confirm Your Account',
				'auth/email/confirm',
				user=user,
				token=token)
		flash('Check your email to confirm your account!')
		return redirect(url_for('main.index'))
	return render_template('auth/register.html', form=form)


@auth.route('/confirm/<token>')
@login_required
def confirm(token):
	if current_user.confirmed:
		return(url_for('main.index'))
	if current_user.confirm(token):
		flash('You have been confirmed - thanks.')
	else:
		flash('The confirmation link you used is either invalid or expired..')
	return redirect(url_for('main.index'))


@auth.route('/confirm')
@login_required
def resend_confirmation():
	token = current_user.generate_confirmation_token()
	send_mail(current_user.email, 'Confirm Your Account',
			 'auth/email/confirm',
			 user=current_user, 
			 token=token)
	flash('A confirmation email has been resent.')
	return	redirect(url_for('main.index'))


@auth.route('/unconfirmed')
def unconfirmed():
	if current_user.is_anonymous() or current_user.confirmed:
		return redirect('main.index')
	return render_template('auth/unconfirmed.html')


@auth.route('/change-password', methods=['GET', 'POST'])
def change_password():
	form = ChangePasswordForm()
	if form.validate_on_submit():
		if current_user.verify_password(form.old_password.data):
			current_user.password = form.password.data
			db.session.add(current_user)
			flash('Your password has been changed')
			return redirect(url_for('main.index'))
		else:
			flash('Invalid Password')
	return render_template('auth/change_password.html', form=form)


@auth.route('/reset', methods=['GET', 'POST'])
def password_reset_request():
	if not current_user.is_anonymous():
		return(url_for('main.index'))
	form =  PasswordResetRequestForm()
	if form.validate_on_submit():
		user = User.query.filter_by(email=form.email.data).first()
		if user:
			token = user.generate_reset_token()
			send_email(user.email,
					'Reset Your Password',
					'auth/email/rest_password',
					user=user,
					token=token,
					next=request.args.get('next'))
			flash('An email with instructions to reset your password has been sent to your email')
			return redirect(url_for('auth.login'))
		else:
			flash("That email is not associated with an account, please register")
			redirect(url_for('auth.register'))
	return render_template('auth/reset_password.html', form=form)


@auth.route('/reset/<token>', methods=['GET', 'POST'])
def password_reset(token):
	if not current_user.is_anonymous():
		return redirect(url_for('main.index'))
	form = PasswordResetForm()
	if form.validate_on_submit():
		user = User.query.filter_by(email=form.email.data).first()
		if user is None:
			return redirect(url_for('main.index'))
		if user.reset_password(token, form.password.data):
			flash('Your password has been updated.')
			return redirect(url_for('auth.login'))
		else:
			return redirect(url_for('main.index'))
	return render_template('auth/reset_password.html', form=form)

@auth.route('/change-email', methods=['GET', 'POST'])
@login_required
def change_email_request():
	form = ChangeEmailForm()
	if form.validate_on_submit():
		if current_user.verify_password(form.password.data):
			new_email = form.email.data
			token = current_user.generate_email_change_token(new_email)
			send_email(new_email, 
					"Confirm your new email address.", 
					'auth/email/change_email',
					user=current_user,
					token=token)
			flash('An email with confirmation instructions has been sent to your new email.')
			return redirect(url_for('main.index'))
		else:
			flash('Invalid email or password.')
	return render_template("auth/change_email.html", form=form)

@auth.route('/change-email/<token>')
@login_required
def change_email(token):
	if current_user.change_email(token):
		flash('Your email has been updated')
	else:
		flash('Invalid Request')
	return redirect(url_for('main.index'))


