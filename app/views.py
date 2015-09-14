from flask import render_template, flash, url_for, redirect, request, g
from flask.ext.login import login_user, logout_user, current_user, login_required
from app import app, db
from datetime import datetime
from .forms import LoginForm, EditForm
from .OAuth import GitHubSignIn
import json
from .models import User

github = GitHubSignIn().service


@app.route('/')
@app.route('/index')
@login_required
def index():
    user = g.user
    posts = [
        {
            'author': {'nickname': 'Tester'},
            'body': 'Lovely day'
        },
        {
            'author': {'nickname': 'User123'},
            'body': 'Not so lovely day'
        }
    ]
    return render_template('index.html', user=user, posts=posts)


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        params = {'redirect_uri': 'http://localhost:5000/authorized', 'response_type': 'code'}
        url = github.get_authorize_url(**params)
        return redirect(url)
    return render_template('login.html', title='Sign In', form=form)


@app.route('/authorized')
def authorized():
    data = {'code': request.args.get('code'), 'grant_type': 'authorization_code', 'redirect_uri': 'http://localhost:5000/authorized'}
    session = github.get_auth_session(data=data)
    if not session.access_token_response.ok:
        return redirect(url_for('login'))
    user = session.get('user')
    userdetails = json.loads(user.text)
    loggedinuser = User.query.filter_by(github_id=userdetails.get('id')).first()
    if loggedinuser is None:
        nickname = userdetails.get('login')
        if nickname is None or nickname == '':
            nickname = str(userdetails.get('email')).split('@')[0]
        nickname = User.make_unique_nickname(nickname)
        newuser = User(nickname=nickname, email=userdetails.get('email'), github_id=userdetails.get('id'))
        db.session.add(newuser)
        db.session.commit()
    login_user(loggedinuser)

    return redirect(url_for('index'))


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))


@app.route('/user/<nickname>')
def user(nickname):
    user = User.query.filter_by(nickname=nickname).first()
    if user is None:
        flash('User %s not found' % nickname)
        return redirect(url_for('index'))
    posts = [
        {'author': user, 'body': 'Test post #1'},
        {'author': user, 'body': 'Test post #2'}
    ]
    return render_template('user.html', user=user, posts=posts)


@app.route('/edit', methods=['GET', 'POST'])
@login_required
def edit():
    form = EditForm(g.user.nickname)
    if form.validate_on_submit():
        g.user.nickname = form.nickname.data
        g.user.about_me = form.about_me.data
        db.session.add(g.user)
        db.session.commit()
        flash('Your changes have been saved.')
        return redirect(url_for('edit'))
    else:
        form.nickname.data = g.user.nickname
        form.about_me.data = g.user.about_me
    return render_template('edit.html', form=form)


@app.before_request
def before_request():
    g.user = current_user
    if g.user.is_authenticated:
        g.user.last_seen = datetime.utcnow()
        db.session.add(g.user)
        db.session.commit()


@app.errorhandler(404)
def not_found_error(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('500.html'), 500

