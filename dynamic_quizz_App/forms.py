from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, TextAreaField, RadioField
from wtforms.validators import DataRequired, Email, EqualTo, Length

class RegistrationForm(FlaskForm):
    username = StringField("Username", validators=[DataRequired(), Length(min=3, max=50)])
    email = StringField("Email", validators=[DataRequired(), Email()])
    password = PasswordField("Password", validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField("Confirm Password", validators=[DataRequired(), EqualTo("password")])
    submit = SubmitField("Register")

class LoginForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired(), Email()])
    password = PasswordField("Password", validators=[DataRequired()])
    submit = SubmitField("Login")

class QuizCreationForm(FlaskForm):
    title = StringField("Quiz Title", validators=[DataRequired()])
    question_text = TextAreaField("Question", validators=[DataRequired()])
    question_type = RadioField("Question Type", choices=[('MCQ', 'Multiple Choice'), ('True/False', 'True/False')], validators=[DataRequired()])
    options = StringField("Options (Comma-separated for MCQ)")
    correct_answer = StringField("Correct Answer", validators=[DataRequired()])
    submit = SubmitField("Create Quiz")

class RequestResetForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired(), Email()])
    submit = SubmitField("Request Password Reset")

class ResetPasswordForm(FlaskForm):
    password = PasswordField("New Password", validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField("Confirm Password", validators=[DataRequired(), EqualTo("password")])
    submit = SubmitField("Reset Password")
