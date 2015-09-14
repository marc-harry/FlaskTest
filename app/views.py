from flask import render_template, flash, url_for, redirect, request, g
from flask.ext.login import login_user, logout_user, current_user, login_required
from app import app, db
from .forms import LoginForm
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
        return render_template('login.html', title='Sign In', form=LoginForm())
    user = session.get('user')
    userdetails = json.loads(user.text)
    loggedinuser = User.query.filter_by(github_id=userdetails.get('id')).first()
    if loggedinuser is None:
        newuser = User(nickname=userdetails.get('login'), email=userdetails.get('email'), github_id=userdetails.get('id'))
        db.session.add(newuser)
        db.session.commit()
    login_user(loggedinuser)

    return redirect('/')


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))


@app.before_request
def before_request():
    g.user = current_user

