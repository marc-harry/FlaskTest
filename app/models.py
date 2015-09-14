from app import db, lm
from flask_login import UserMixin


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nickname = db.Column(db.String(64), index=True, unique=True)
    email = db.Column(db.String(255), index=True, unique=True)
    posts = db.relationship('Post', backref='author', lazy='dynamic')

    github_id = db.Column(db.String(64), index=True, unique=True)

    def get_id(self):
        return str(self.id)

    def __repr__(self):
        return '<User %r>' % self.nickname


@lm.user_loader
def load_user(userid):
    return User.query.get(int(userid))


class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    body = db.Column(db.String(140))
    timestamp = db.Column(db.DateTime)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    def __repr__(self):
        return '<Post %r>' % self.body