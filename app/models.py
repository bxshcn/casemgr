# -*- coding: utf-8 -*-
from datetime import datetime
import hashlib
from werkzeug.security import generate_password_hash, check_password_hash
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from markdown import markdown
import bleach
from flask import current_app, request, url_for
from flask_login import UserMixin, AnonymousUserMixin
from app.exceptions import ValidationError
from . import db, login_manager


class Permission:
    FOLLOW = 1
    EDIT = 2
    DELCASE = 4
    DELSCENARIO = 8


class Role(db.Model):
    __tablename__ = 'roles'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True)
    default = db.Column(db.Boolean, default=False, index=True)
    permissions = db.Column(db.Integer)
    users = db.relationship('User', backref='role', lazy='dynamic')

    def __init__(self, **kwargs):
        super(Role, self).__init__(**kwargs)
        if self.permissions is None:
            self.permissions = 0

    @staticmethod
    def insert_roles():
        roles = {
            u'用户': [Permission.FOLLOW, Permission.EDIT],
            u'协管员': [Permission.FOLLOW, Permission.EDIT, Permission.DELCASE],
            u'管理员': [Permission.FOLLOW, Permission.EDIT,
                     Permission.DELCASE, Permission.DELSCENARIO],
        }
        default_role = u'用户'
        for r in roles:
            role = Role.query.filter_by(name=r).first()
            if role is None:
                role = Role(name=r)
            role.reset_permissions()
            for perm in roles[r]:
                role.add_permission(perm)
            role.default = (role.name == default_role)
            db.session.add(role)
        db.session.commit()

    def add_permission(self, perm):
        if not self.has_permission(perm):
            self.permissions += perm

    def remove_permission(self, perm):
        if self.has_permission(perm):
            self.permissions -= perm

    def reset_permissions(self):
        self.permissions = 0

    def has_permission(self, perm):
        return self.permissions & perm == perm

    def __repr__(self):
        return '<Role %r>' % self.name


class Follow(db.Model):
    __tablename__ = 'follows'
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'),
                        primary_key=True)
    scenario_id = db.Column(db.Integer, db.ForeignKey('scenarios.id'),
                            primary_key=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)


class Rely(db.Model):
    __tablename__ = 'relies'
    # the relier scenario relies on relied scenario
    relier_id = db.Column(db.Integer, db.ForeignKey('scenarios.id'),
                          primary_key=True)
    # the scenario relied by others
    relied_id = db.Column(db.Integer, db.ForeignKey('scenarios.id'),
                          primary_key=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)


class Scenario(db.Model):
    __tablename__ = 'scenarios'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True)
    content = db.Column(db.Text)
    remark = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    edit_userid = db.Column(db.Integer, db.ForeignKey('users.id'))
    cases = db.relationship('Case', backref='scenario', lazy='dynamic')

    # the scenarios which are relied by the current scenario (self)
    # that's to say, the current scenario is the relier
    # 我依赖的
    relied = db.relationship('Rely',
                             foreign_keys=[Rely.relier_id],
                             backref=db.backref('relier', lazy='joined'),
                             lazy='dynamic',
                             cascade='all, delete-orphan')
    # the scenarios which rely on the current scenario (self)
    # that's to say, the current scenario is the relied
    # 依赖我的
    reliers = db.relationship('Rely',
                              foreign_keys=[Rely.relied_id],
                              backref=db.backref('relied', lazy='joined'),
                              lazy='dynamic',
                              cascade='all, delete-orphan')

    def is_followed_by(self, user):
        if user.id is None:
            return False
        return self.followed_users.filter_by(
            user_id=user.id).first() is not None

    # the auxiliary functions used to handle rely relationship between scenario
    def rely(self, scenario):
        if not self.is_relying(scenario):
            f = Rely(relier=self, relied=scenario)
            db.session.add(f)

    def unrely(self, scenario):
        f = self.relied.filter_by(relied_id=scenario.id).first()
        if f:
            db.session.delete(f)

    def is_relying(self, scenario):
        if scenario.id is None:
            return False
        return self.relied.filter_by(
            relied_id=scenario.id).first() is not None

    def is_relied_by(self, scenario):
        if scenario.id is None:
            return False
        return self.reliers.filter_by(
            relier_id=scenario.id).first() is not None


class Case(db.Model):
    __tablename__ = 'cases'
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text)
    remark = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    scenario_id = db.Column(db.Integer, db.ForeignKey('scenarios.id'))
    edit_userid = db.Column(db.Integer, db.ForeignKey('users.id'))


class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(64), unique=True, index=True)
    username = db.Column(db.String(64), unique=True, index=True)
    role_id = db.Column(db.Integer, db.ForeignKey('roles.id'))
    password_hash = db.Column(db.String(128))
    confirmed = db.Column(db.Boolean, default=False)
    member_since = db.Column(db.DateTime(), default=datetime.utcnow)
    last_seen = db.Column(db.DateTime(), default=datetime.utcnow)
    last_informed = db.Column(db.DateTime(), default=datetime.utcnow)
#    follow_scenarios = db.relationship('Scenario',
#                                       secondary="follows",
#                                       backref=db.backref(
#                                           'followed_users', lazy='joined'),
#                                       lazy='dynamic',
#                                       cascade='all, delete-orphan')
    edit_scenarios = db.relationship(
        'Scenario', backref='edit_user', lazy='dynamic')
    edit_cases = db.relationship('Case', backref='edit_user', lazy='dynamic')

    def __init__(self, **kwargs):
        super(User, self).__init__(**kwargs)
        if self.role is None:
            if self.email == current_app.config['CASEMGR_ADMIN']:
                self.role = Role.query.filter_by(name='管理员').first()
            if self.role is None:
                self.role = Role.query.filter_by(default=True).first()

    @property
    def password(self):
        raise AttributeError('password is not a readable attribute')

    @password.setter
    def password(self, password):
        self.password_hash = generate_password_hash(password)

    def verify_password(self, password):
        return check_password_hash(self.password_hash, password)

    def generate_confirmation_token(self, expiration=3600):
        s = Serializer(current_app.config['SECRET_KEY'], expiration)
        return s.dumps({'confirm': self.id}).decode('utf-8')

    def confirm(self, token):
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token.encode('utf-8'))
        except Exception:
            return False
        if data.get('confirm') != self.id:
            return False
        self.confirmed = True
        db.session.add(self)
        return True

    def generate_reset_token(self, expiration=3600):
        s = Serializer(current_app.config['SECRET_KEY'], expiration)
        return s.dumps({'reset': self.id}).decode('utf-8')

    @staticmethod
    def reset_password(token, new_password):
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token.encode('utf-8'))
        except Exception:
            return False
        user = User.query.get(data.get('reset'))
        if user is None:
            return False
        user.password = new_password
        db.session.add(user)
        return True

    def generate_email_change_token(self, new_email, expiration=3600):
        s = Serializer(current_app.config['SECRET_KEY'], expiration)
        return s.dumps(
            {'change_email': self.id, 'new_email': new_email}).decode('utf-8')

    def change_email(self, token):
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token.encode('utf-8'))
        except Exception:
            return False
        if data.get('change_email') != self.id:
            return False
        new_email = data.get('new_email')
        if new_email is None:
            return False
        if self.query.filter_by(email=new_email).first() is not None:
            return False
        self.email = new_email
        db.session.add(self)
        return True

    def can(self, perm):
        return self.role is not None and self.role.has_permission(perm)

    def is_administrator(self):
        return self.can(Permission.DELSENARIO)

    def is_assistant(self):
        return self.can(Permission.DELCASE) and not self.can(Permission.DELSENARIO)

    def ping(self):
        self.last_seen = datetime.utcnow()
        db.session.add(self)
        db.session.commit()

    def follow(self, scenario):
        if not self.is_following(scenario):
            f = Follow(user=self, scenario=scenario)
            db.session.add(f)

    def unfollow(self, scenario):
        f = self.follow_scenarios.filter_by(scenario_id=scenario.id).first()
        if f:
            db.session.delete(f)

    def is_following(self, scenario):
        if scenario.id is None:
            return False
        return self.scenarios.filter_by(
            scenario_id=scenario.id).first() is not None

# 当前用户所关注的场景列表
# select scenario_id from follows join users where follows.user_id = users.id;找到scenarios_id列表
# select * from scenarios where scenario_id in
# select left.id,right.id from left join association on left.id=association.left_id
# join right on association.right_id=right.id
    @property
    def followed_scenarios(self):
        return Scenario.query.join(Follow, Follow.scenario_id == Scenario.id)\
            .filter(Follow.user_id == self.id)

    def generate_auth_token(self, expiration):
        s = Serializer(current_app.config['SECRET_KEY'],
                       expires_in=expiration)
        return s.dumps({'id': self.id}).decode('utf-8')

    @staticmethod
    def verify_auth_token(token):
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token)
        except Exception:
            return None
        return User.query.get(data['id'])

    def __repr__(self):
        return '<User %r>' % self.username


class AnonymousUser(AnonymousUserMixin):
    def can(self, permissions):
        return False

    def is_assistant(sefl):
        return False

    def is_administrator(self):
        return False


login_manager.anonymous_user = AnonymousUser


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))
