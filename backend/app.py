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
        user = User(username=form.username.data, email=form.email.data, password_hash=hashed_password, role=form.role.data)
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
    # Clear any existing flash messages
    from flask import get_flashed_messages
    get_flashed_messages()  # This clears the flash message queue
    
    logout_user()
    flash("You have been logged out.", "info")
    return redirect(url_for("login"))

@app.route("/create_quiz", methods=["GET", "POST"])
@login_required
def create_quiz():
    if current_user.role != 'professor':
        flash("This feature is only available for professors", "danger")
        return redirect(url_for('dashboard')) 
        
    form = QuizCreationForm()
    if form.validate_on_submit():
        print("Form validated successfully!")  # Debug
        existing_quiz = Quiz.query.filter_by(title=form.title.data, creator_id=current_user.id).first()
        # Save the quiz
        if not existing_quiz:
            quiz = Quiz(title=form.title.data,category=request.form.get('category'),  creator_id=current_user.id)
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
    if current_user.role == 'professor':
        quizzes = Quiz.query.filter_by(creator_id=current_user.id).all()
    else:
        # For students, show all quizzes (or assigned quizzes if you implement assignment logic)
        quizzes = Quiz.query.all()
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
            is_correct=is_correct,
            
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
        
        # Handle all questions (updated implementation)
        question_texts = request.form.getlist('question_text')
        question_types = request.form.getlist('question_type')
        options_list = request.form.getlist('options')
        correct_answers = request.form.getlist('correct_answer')
        
        # Get existing questions
        existing_questions = {q.id: q for q in quiz.questions}
        
        # Update or create questions
        for i in range(len(question_texts)):
            # Try to find existing question to update
            question_id = request.form.getlist('question_ids')[i] if 'question_ids' in request.form else None
            if question_id and int(question_id) in existing_questions:
                question = existing_questions[int(question_id)]
                question.text = question_texts[i]
                question.question_type = question_types[i]
                question.options = options_list[i] if question_types[i] == 'MCQ' else None
                question.correct_answer = correct_answers[i]
            else:
                # Create new question
                question = Question(
                    quiz_id=quiz.id,
                    text=question_texts[i],
                    question_type=question_types[i],
                    options=options_list[i] if question_types[i] == 'MCQ' else None,
                    correct_answer=correct_answers[i]
                )
                db.session.add(question)
        
        # Delete only questions that were removed
        submitted_question_ids = [int(id) for id in request.form.getlist('question_ids') if id]
        for q_id, question in existing_questions.items():
            if q_id not in submitted_question_ids:
                # First delete responses for this question
                Response.query.filter_by(question_id=q_id).delete()
                # Then delete the question
                db.session.delete(question)
        
        db.session.commit()
        flash("Quiz updated successfully!", "success")
        return redirect(url_for("quizzes"))

    # Pre-fill the form with existing data
    if request.method == "GET":
        form.title.data = quiz.title
        
    return render_template("edit_quiz.html", form=form, quiz=quiz, questions=quiz.questions)

@app.route("/quiz/<int:quiz_id>/delete", methods=["POST"])
@login_required
def delete_quiz(quiz_id):
    quiz = Quiz.query.get_or_404(quiz_id)
    
    if current_user.role != 'professor' or quiz.creator_id != current_user.id:
        flash("You don't have permission to delete this quiz", "danger")
        return redirect(url_for('quizzes'))

    try:
        # Get all question IDs for this quiz
        question_ids = [q.id for q in quiz.questions]
        
        # Delete all responses for these questions
        Response.query.filter(Response.question_id.in_(question_ids)).delete(synchronize_session=False)
        
        # Delete all questions
        Question.query.filter_by(quiz_id=quiz.id).delete(synchronize_session=False)
        
        # Finally delete the quiz
        db.session.delete(quiz)
        db.session.commit()
        flash("Quiz deleted successfully!", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Error deleting quiz: {str(e)}", "danger")
        app.logger.error(f"Error deleting quiz: {str(e)}")
    
    return redirect(url_for('quizzes'))
@app.route("/analytics")
@login_required
def analytics():
    # For professors - show all their quizzes' analytics
    if current_user.role == 'professor':
        quizzes = Quiz.query.filter_by(creator_id=current_user.id).all()
    # For students - show only their responses
    else:
        quizzes = Quiz.query.join(Question).join(Response).filter(
            Response.user_id == current_user.id
        ).distinct().all()
    
    quiz_data = []
    category_stats = {}
    
    for quiz in quizzes:
        questions_data = []
        correct = 0
        incorrect = 0
        
        for question in quiz.questions:
            # For professors - count all responses
            if current_user.role == 'professor':
                correct_count = Response.query.filter_by(
                    question_id=question.id,
                    is_correct=True
                ).count()
                incorrect_count = Response.query.filter_by(
                    question_id=question.id,
                    is_correct=False
                ).count()
            # For students - only count their own responses
            else:
                correct_count = Response.query.filter_by(
                    question_id=question.id,
                    user_id=current_user.id,
                    is_correct=True
                ).count()
                incorrect_count = Response.query.filter_by(
                    question_id=question.id,
                    user_id=current_user.id,
                    is_correct=False
                ).count()
            
            correct += correct_count
            incorrect += incorrect_count
            
            questions_data.append({
                'text': question.text,
                'correct_count': correct_count,
                'incorrect_count': incorrect_count
            })
        
        # Update category stats
        if quiz.category not in category_stats:
            category_stats[quiz.category] = {'correct': 0, 'incorrect': 0}
        category_stats[quiz.category]['correct'] += correct
        category_stats[quiz.category]['incorrect'] += incorrect
        
        if correct + incorrect > 0:
            quiz_data.append({
                'title': quiz.title,
                'category': quiz.category,
                'correct': correct,
                'incorrect': incorrect,
                'questions': questions_data
            })
    
    return render_template("analytics.html", 
                         quiz_data=quiz_data,
                         category_stats=category_stats)
if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)