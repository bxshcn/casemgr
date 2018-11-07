# -*- coding:utf-8 -*-
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import DataRequired, Length, Email, Regexp, EqualTo
from wtforms import ValidationError
from ..models import User


class LoginForm(FlaskForm):
    email = StringField(u'邮箱', validators=[DataRequired(), Length(1, 64),
                                           Email()])
    password = PasswordField(u'密码', validators=[DataRequired()])
    remember_me = BooleanField(u'保持登录')
    submit = SubmitField(u'登录')


class RegistrationForm(FlaskForm):
    email = StringField(u'邮箱', validators=[DataRequired(), Length(1, 64),
                                           Email()])
    username = StringField(u'用户', validators=[
        DataRequired(), Length(1, 64)])
    password = PasswordField(u'密码', validators=[
        DataRequired(), EqualTo('password2', message=u'两次输入的密码必须匹配')])
    password2 = PasswordField(u'请重新输入密码', validators=[DataRequired()])
    submit = SubmitField(u'注册')

    def validate_email(self, field):
        if User.query.filter_by(email=field.data).first():
            raise ValidationError(u'该邮箱已被注册')

    def validate_username(self, field):
        if User.query.filter_by(username=field.data).first():
            raise ValidationError(u'用户名已被使用')


class ChangePasswordForm(FlaskForm):
    old_password = PasswordField(u'旧密码', validators=[DataRequired()])
    password = PasswordField(u'新密码', validators=[
        DataRequired(), EqualTo('password2', message='两次输入的密码必须匹配')])
    password2 = PasswordField(u'请重新输入密码',
                              validators=[DataRequired()])
    submit = SubmitField(u'更新密码')


class PasswordResetRequestForm(FlaskForm):
    email = StringField(u'邮箱', validators=[DataRequired(), Length(1, 64),
                                           Email()])
    submit = SubmitField(u'重置密码')


class PasswordResetForm(FlaskForm):
    password = PasswordField(u'新密码', validators=[
        DataRequired(), EqualTo('password2', message='两次输入的密码必须匹配')])
    password2 = PasswordField(u'请重新输入新密码', validators=[DataRequired()])
    submit = SubmitField(u'重置密码')


class ChangeEmailForm(FlaskForm):
    email = StringField(u'新邮箱', validators=[DataRequired(), Length(1, 64),
                                            Email()])
    password = PasswordField(u'密码', validators=[DataRequired()])
    submit = SubmitField(u'更新邮箱')

    def validate_email(self, field):
        if User.query.filter_by(email=field.data).first():
            raise ValidationError(u'该邮箱已被注册')
