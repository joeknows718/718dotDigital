from . import main 
from flask import  render_template, session, url_for, redirect, flash, request, current_app
from flask.ext.login import login_required, current_user
from datetime import datetime 
from . import main 
from .forms import EditProfileForm, EditProfileAdminForm, PostForm, CommentForm
from .. import db
from ..models import User, Role, Permission, Post, Comment
from ..decorators import admin_required, permission_required


@main.route('/', methods=['GET','POST'])
def index():
	form = PostForm()
	if current_user.can(Permission.WRITE_ARTICLES) and form.validate_on_submit():
		post = Post(title=form.title.data, body=form.body.data, author=current_user._get_current_object())
		db.session.add(post)
		return redirect(url_for('.index'))
	page = request.args.get('page', 1, type=int)
	show_followed = False 
	if current_user.is_authenticated():
		show_followed = bool(request.cookies.get('show_followed', ''))
	if show_followed:
		query = current_user.followed_posts
	else:
		query = Post.query
	pagination = query.order_by(Post.timestamp.desc()).paginate(
		page, per_page=current_app.config['POSTS_PER_PAGE'],
		error_out=False)
	posts = pagination.items
	return render_template('index.html',
							form=form,
							posts=posts,
							pagination=pagination,
							show_followed=show_followed)


@main.route('/user/<username>')
def user(username):
	user = User.query.filter_by(username=username).first_or_404()
	page = request.args.get('page', 1, type=int)
	pagination = user.posts.order_by(Post.timestamp.desc()).paginate(
		page, per_page=current_app.config['POSTS_PER_PAGE'], error_out=False)
	posts = pagination.items
	return render_template('user.html', user=user, posts=posts, pagination=pagination)


@main.route('/edit-profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
	form = EditProfileForm()
	if form.validate_on_submit():
		current_user.name = form.name.data
		current_user.location = form.location.data
		current_user.about_me = form.about_me.data
		db.session.add(user)
		flash('Your profile has been updated!')
		return (url_for('.user', username=current_user.username))
	form.name.data = current_user.name
	form.location.data = current_user.location
	form.about_me.data = current_user.about_me
	return render_template('edit_profile.html', form=form)


@main.route('/edit-profile/<int:id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_profile_admin(id):
	user = User.query.get_or_404(id)
	form = EditProfileAdminForm(user=user)
	if form.validate_on_submit():
		user.email =  form.email.data
		user.username = form.username.data
		user.confirmed =  form.confirmed.data 
		user.role = Role.query.get(form.role.data)
		user.name = form.name.data
		user.location = form.location.data
		user.about_me = form.about_me.data
		db.session.add(user)
		flash('This profile has been updated')
		return redirect(url_for('.user', username=user.username))
	form.email.data = user.email
	form.username.data = user.username
	form.confirmed.data = user.confirmed
	form.role.data = user.role_id
	form.name.data = user.name
	form.location.data = user.location
	form.about_me.data = user.about_me
	return render_template('edit_profile.html', form=form, user=user)


@main.route('/post/<int:id>', methods=['GET', 'POST'])
def post(id):
	post = Post.query.get_or_404(id)
	form = CommentForm()
	if  form.validate_on_submit():
		comment = Comment(body=form.body.data,
						  post=post,
						  author=current_user._get_current_object())
		db.session.add(comment)
		flash('Your comment is up.')
		return redirect(url_for('.post', id=post.id, page=-1))
	page = request.args.get('page', 1, type=int)
	if page == -1:
		page = (post.comments.count() -1 / current_app.config['COMMENTS_PER_PAGE'] + 1)
	pagination = post.comments.order_by(Comment.timestamp.desc()).paginate(
		page, per_page=current_app.config['COMMENTS_PER_PAGE'],
		error_out=False)
	comments = pagination.items 
	return render_template('post.html', 
							posts=[post], 
							form=form, 
							comments=comments, 
							pagination=pagination)


@main.route('/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit(id):
	post = Post.query.get_or_404(id)
	if current_user != post.author and not current_user.can(Permission.ADMINISTER):
		abort(403)
	form = PostForm()
	if form.validate_on_submit():
		post.title = form.title.data
		post.body = form.body.data
		db.session.add(post)
		flash('The post has been updated.')
		return redirect(url_for('.post', id=post.id))
	form.title.data = post.title
	form.body.data = post.body
	return render_template('edit_post.html', form=form)


@main.route('/follow/<username>')
@login_required
@permission_required(Permission.FOLLOW)
def follow(username):
	user = User.query.filter_by(username=usernamed).first()
	if user is None:
		flash('Invalid User')
		return redirect(url_for('.index'))
	if current_user.is_following(user):
		flash('You are already following them')
		return redirect(url_for('.user', username=username))
	current_user.follow(user)
	flash('You are now following %s.' % username)
	return redirect(url_for('.user', username=username))


@main.route('/unfollow/<username>')
@login_required
@permission_required(Permission.FOLLOW)
def unfollow(username):
	user = User.query.filter_by(username=username).first()
	if user is None:
		flash('Invalid User')
		return redirect(url_for('.index'))
	if current_user.is_following(user) is False:
		flash('You are not following them')
		return redirect(url_for('.user', username=username))
	current_user.unfollow(user)
	return redirect(url_for('.user', username=username))


@main.route('/followers/<username>')
def followers(username):
	user = User.query.filter_by(username=username).first()
	if user is None:
		flash('Invalid User')
		redirect(url_for('.index'))
	page = request.args.get('page', 1, type=int)
	pagination = user.followers.paginate(page,
										 per_page=current_app.config['FOLLOWERS_PER_PAGE'],
										 error_out=False)
	follows = [{'user' : item.follower, 'timestamp' : item.timestamp} for item in pagination.items]  
	return render_template('followers.html', user=user,
							title="Followers of",
							endpoint='.followers',
							pagination=pagination,
							follows=follows)


@main.route('/following/<username>')
def followed_by(username):
	user = User.query.filter_by(username=username).first()
	if user is None:
		flash('Invalid User')
		redirect(url_for('.index'))
	page = request.args.get('page', 1, type=int)
	pagination = user.followed.paginate(page, 
										per_page=current_app.config['FOLLOWERS_PER_PAGE'],
										error_out=False)
	follows = [{'user' : item.followed, 'timestamp' : item.timestamp} for item in pagination.items]
	return render_template('followers.html', user=user,
							title="Followed by",
							endpoint='.followed_by',
							pagination=pagination,
							follows=follows)


@main.route('/all')
@login_required
def show_all():
	resp = make_response(redirect(url_for('.index')))
	resp.set_cookie('show_followed', '', max_age=30*24*60*60)
	return resp


@main.route('/followed')
@login_required
def show_followed():
	resp = make_response(redirect(url_for('.index')))
	resp.set_cookie('show_followed', '1', max_age=30*24*60*60)


@main.route('/delete/<int:id>')
@login_required 
def delete(id):
	post = Post.query.get(id)
	if post is None:
		flash(gettext('Post not found'))
		return redirect(url_for('.index'))
	if current_user != post.author and not current_user.can(Permission.ADMINISTER):
		abort(403)
	db.session.delete(post)
	flash('Your post has been deleted.')
	return redirect(url_for('.index'))


@main.route('/delete-comment/<int:id>')
@login_required 
def delete_comment(id):
	comment = Comment.query.get(id)
	post = comment.post
	if comment is None:
		flash(gettext('Comment not found'))
		return redirect(url_for('.post', id=post.id))
	if current_user != comment.author and not current_user.can(Permission.ADMINISTER):
		abort(403)
	db.session.delete(comment)
	flash('Your comment has been deleted.')
	return redirect(url_for('.post', id=post.id))


@main.route('/edit-comment/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_comment(id):
	comment = Comment.query.get_or_404(id)
	if current_user != comment.author and not current_user.can(Permission.ADMINISTER):
		abort(403)
	form = CommentForm()
	if form.validate_on_submit():
		comment.body = form.body.data
		db.session.add(comment)
		flash('The comment has been updated.')
		return redirect(url_for('.post', id=comment.post.id))
	form.body.data = comment.body
	return render_template('edit_comment.html', form=form)


@main.route('/moderate')
@login_required
@permission_required(Permission.MODERATE_COMMENTS)
def moderate():
	page = request.args.get('page', 1, type=int)
	pagination = Comment.query.order_by(Comment.timestamp.desc()).paginate(
		page, per_page=current_app.config['COMMENTS_PER_PAGE'],
		error_out=False)
	comments = pagination.items
	return render_template('moderate.html',
							comments=comments,
							pagination=pagination, 
							page=page)


@main.route('/moderate/enable/<int:id>')
@login_required
@permission_required(Permission.MODERATE_COMMENTS)
def moderate_enable(id):
	comment = Comment.query.get_or_404(id)
	comment.disabled =  False 
	db.session.add(comment)
	return redirect(url_for('.moderate',
							page=request.args.get('page', 1, type=int)))


@main.route('/moderate/disable/<int:id>')
@login_required
@permission_required(Permission.MODERATE_COMMENTS)
def moderate_disable(id):
	comment = Comment.query.get_or_404(id)
	comment.disabled = True 
	db.session.add(comment)
	return redirect(url_for('.moderate',
							page=request.args.get('page', 1, type=int)))









