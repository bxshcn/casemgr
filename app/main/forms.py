# -*- coding:utf-8 -*-
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, TextAreaField
from wtforms.validators import DataRequired, Length, Email, Regexp, EqualTo
from wtforms import ValidationError
from ..models import Scenario


class EditScenarioForm(FlaskForm):
    name = StringField(u'场景名称', validators=[DataRequired(), Length(1, 64)])
    content = TextAreaField(u'场景内容', validators=[DataRequired()])
    submit = SubmitField(u'确认')


class EditCaseForm(FlaskForm):
    content = TextAreaField(u'案例内容', validators=[DataRequired()])
    submit = SubmitField(u'确认')
