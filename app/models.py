from flask import current_app
from app import db, login_manager
from flask_login import UserMixin
from itsdangerous import JSONWebSignatureSerializer
from werkzeug.security import generate_password_hash, check_password_hash

class Task(UserMixin, db.Model):
    __tablename__ = 'tasks'
    id = db.Column(db.Integer, primary_key=True)
    body = db.Column(db.String(128))
    due = db.Column(db.DateTime, index=True)
    done = db.Column(db.Boolean, default=False)
    author_id = db.Column(db.Integer, db.ForeignKey('users.id'))

    author = db.relationship('User', foreign_keys=author_id, back_populates='tasks')

    def __repr__(self):
        return '<Task %r>' % self.id


class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=True)
    email = db.Column(db.String(120), unique=True, nullable=True)
    password_hash = db.Column(db.String(80))
    confirmed = db.Column(db.Boolean, default=False)
    tasks = db.relationship('Task', foreign_keys=Task.author_id, back_populates='author')

    def __repr__(self):
        return '<User {}>'.format(self.username)

    @property
    def password(self):
        raise AttributeError('password is not a readable attribute')

    @password.setter
    def password(self, password):
        self.password_hash = generate_password_hash(password)

    def verify_password(self, password):
        return check_password_hash(self.password_hash, password)

    def change_password(self, new_password):
        self.password_hash = generate_password_hash(new_password)

    def generate_confirmation_token(self, expiration=3600):
        s = JSONWebSignatureSerializer(current_app.config['SECRET_KEY'])
        return s.dumps({'confirm': self.id}).decode('utf-8')

    def confirm(self, token):
        s = JSONWebSignatureSerializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token.encode('utf-8'))
        except:
            return False
        if data.get('confirm') != self.id:
            return False
        self.confirmed = True
        db.session.add(self)
        return True

    def generate_reset_password_token(self, expiration=3600):
        s = JSONWebSignatureSerializer(current_app.config['SECRET_KEY'])
        return s.dumps({'reset_password': self.id}).decode('utf-8')
    @staticmethod
    def password_reset(token, new_password):
        s = JSONWebSignatureSerializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token.encode('utf-8'))
        except:
            return False
        user = User.query.get(data.get('reset_password'))
        if user is None:
            return False
        user.password = new_password
        db.session.add(user)
        return True

    def generate_email_change_token(self, new_email, expiration=3600):
        s = JSONWebSignatureSerializer(current_app.config['SECRET_KEY'])
        return s.dumps({'change_email': self.id, 'new_email': new_email}).decode('utf-8')

    def email_change(self, token):
        s = JSONWebSignatureSerializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token.encode('utf-8'))
        except:
            return False
        user = User.query.get(data.get('change_email'))
        new_email = data.get('new_email')
        if user is None:
            return False
        if new_email is None:
            return False
        if self.query.filter_by(email=new_email).first() is not None:
            return False
        self.email = new_email
        db.session.add(self)
        return True

    def __repr__(self):
        return '<User %r>' % self.username

@login_manager.user_loader
def user_loader(user_id):
    return User.query.get(int(user_id))
