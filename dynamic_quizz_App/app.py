from flask import Flask, render_template, redirect, url_for, flash, request
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from flask_mail import Mail, Message
from forms import RegistrationForm, LoginForm, QuizCreationForm, RequestResetForm, ResetPasswordForm
from models import db, User, Quiz, Question, Response
from config import Config

app = Flask(__name__)
app.config.from_object(Config)

db.init_app(app)
bcrypt = Bcrypt(app)
mail = Mail(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))


@app.route("/")
def home():
    return render_template("index.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode("utf-8")
        user = User(username=form.username.data, email=form.email.data, password_hash=hashed_password)
        db.session.add(user)
        db.session.commit()
        flash("Registration successful! Please log in.", "success")
        return redirect(url_for("login"))
    return render_template("register.html", form=form)

@app.route("/login", methods=["GET", "POST"])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and bcrypt.check_password_hash(user.password_hash, form.password.data):
            login_user(user)
            flash("Login successful!", "success")
            return redirect(url_for("dashboard"))
        else:
            flash("Invalid email or password.", "danger")
    return render_template("login.html", form=form)

@app.route("/dashboard")
@login_required
def dashboard():
    return render_template("dashboard.html", username=current_user.username)

@app.route("/logout")
@login_required
def logout():
    logout_user()
    flash("You have been logged out.", "info")
    return redirect(url_for("login"))

@app.route("/create_quiz", methods=["GET", "POST"])
@login_required
def create_quiz():
    form = QuizCreationForm()
    if form.validate_on_submit():
        print("Form validated successfully!")  # Debug
        existing_quiz = Quiz.query.filter_by(title=form.title.data, creator_id=current_user.id).first()
        # Save the quiz
        if not existing_quiz:
            quiz = Quiz(title=form.title.data, creator_id=current_user.id)
            db.session.add(quiz)
            db.session.commit()
        else:
            quiz = existing_quiz

        # Add multiple questions
        question_texts = request.form.getlist('question_text')
        question_types = request.form.getlist('question_type')
        options_list = request.form.getlist('options')
        correct_answers = request.form.getlist('correct_answer')

        print("Captured Questions:", question_texts)  # Debug
        print("Question Types:", question_types)  # Debug

        for i in range(len(question_texts)):
            question = Question(
                quiz_id=quiz.id,
                text=question_texts[i],
                question_type=question_types[i],
                options=options_list[i] if question_types[i] == 'MCQ' else None,
                correct_answer=correct_answers[i]
            )
            db.session.add(question)
        db.session.commit()

        flash("Quiz and Questions added successfully!", "success")
        return redirect(url_for("quizzes"))
    else:
        print("Form validation failed:", form.errors)
    return render_template("create_quiz.html", form=form)


@app.route("/quizzes")
@login_required
def quizzes():
    quizzes = Quiz.query.filter_by(creator_id=current_user.id).all()
    return render_template("quizzes.html", quizzes=quizzes)

@app.route("/quiz/<int:quiz_id>")
@login_required
def view_quiz(quiz_id):
    quiz = Quiz.query.get_or_404(quiz_id)
    questions = Question.query.filter_by(quiz_id=quiz_id).all()
    return render_template("quiz.html", quiz=quiz, questions=questions)

@app.route("/quiz/<int:quiz_id>/submit", methods=["POST"])
@login_required
def submit_quiz(quiz_id):
    quiz = Quiz.query.get_or_404(quiz_id)
    questions = Question.query.filter_by(quiz_id=quiz_id).all()
    score = 0
    results = []

    for question in questions:
        user_answer = request.form.get(f"answer_{question.id}")
        is_correct = user_answer and user_answer.strip().lower() == question.correct_answer.strip().lower()
        # Save the user's response to the database
        response = Response(
            user_id=current_user.id,
            question_id=question.id,
            answer=user_answer,
            is_correct=is_correct
        )
        db.session.add(response)
        if is_correct:
            score += 1
        results.append({
            "question": question.text,
            "user_answer": user_answer,
            "correct_answer": question.correct_answer,
            "is_correct": is_correct
        })
        db.session.commit()
    flash(f"You scored {score}/{len(questions)}!", "info")
    return render_template("quiz_results.html", quiz=quiz, results=results, score=score)

@app.route("/quiz/<int:quiz_id>/edit", methods=["GET", "POST"])
@login_required
def edit_quiz(quiz_id):
    quiz = Quiz.query.get_or_404(quiz_id)
    form = QuizCreationForm()

    if form.validate_on_submit():
        quiz.title = form.title.data
        db.session.commit()

        # Update questions (this is a simplified example; you can expand it)
        for question in quiz.questions:
            question.text = form.question_text.data
            question.question_type = form.question_type.data
            question.options = form.options.data if form.question_type.data == 'MCQ' else None
            question.correct_answer = form.correct_answer.data
            db.session.commit()

        flash("Quiz updated successfully!", "success")
        return redirect(url_for("quizzes"))

    # Pre-fill the form with existing data
    if request.method == "GET":
        form.title.data = quiz.title
        if quiz.questions:
            form.question_text.data = quiz.questions[0].text
            form.question_type.data = quiz.questions[0].question_type
            form.options.data = quiz.questions[0].options
            form.correct_answer.data = quiz.questions[0].correct_answer

    return render_template("edit_quiz.html", form=form, quiz=quiz)

@app.route("/quiz/<int:quiz_id>/delete", methods=["POST"])
@login_required
def delete_quiz(quiz_id):
    quiz = Quiz.query.get_or_404(quiz_id)

    #delete associated questions first
    for question in quiz.questions:
        db.session.delete(question)

    db.session.delete(quiz)
    db.session.commit()
    flash("Quiz deleted successfully!", "success")
    return redirect(url_for("quizzes"))
@app.route("/analytics")
@login_required
def analytics():
    quizzes = Quiz.query.filter_by(creator_id=current_user.id).all()
    quiz_titles = [quiz.title for quiz in quizzes]
    quiz_scores = []
    for quiz in quizzes:
        score = 0
        for question in quiz.questions:
            score += sum(1 for response in question.responses if response.is_correct)
        quiz_scores.append(score)

    return render_template("analytics.html", quiz_titles=quiz_titles, quiz_scores=quiz_scores)

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)
