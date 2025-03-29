from flask import Flask,render_template,redirect,request,url_for,flash,session 
from flask_sqlalchemy import SQLAlchemy
import os
from werkzeug.security import generate_password_hash,check_password_hash
from datetime import datetime,date
import matplotlib.pyplot as plt
import io
import base64


curr_dir = os.path.dirname(os.path.abspath(__file__))

app = Flask(__name__,template_folder='templates',static_folder='static')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///quizmaster.sqlite3'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'thisisakshayamuvva'
db = SQLAlchemy()

db.init_app(app)
app.app_context().push()

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(60),nullable=False)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    passhash = db.Column(db.String(256), nullable=False)
    qualification = db.Column(db.String(60), nullable=False)
    date_of_birth = db.Column(db.Date , nullable = False)
    is_admin = db.Column(db.Boolean, default=False)
    is_flagged = db.Column(db.Boolean, default=False)
    scores = db.relationship('Scores', back_populates = 'user',cascade = 'all, delete-orphan')
    
class Subject(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(60),nullable=False)
    #ser_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    description = db.Column(db.String(120), nullable=False)
    sub_chapter = db.relationship('Chapter', back_populates = 'subjects',cascade = 'all, delete-orphan')
    subject_standard = db.Column(db.Integer)

class Chapter(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(60),nullable=False)
    description = db.Column(db.String(120), nullable=False)
    subject_id = db.Column(db.Integer, db.ForeignKey('subject.id'), nullable=False)
    subjects = db.relationship('Subject', back_populates = 'sub_chapter')
    chap_quiz = db.relationship('Quiz', back_populates = 'chapter',cascade = 'all, delete-orphan')
    
class Quiz(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(60),nullable=False)
    quiz_time_duration = db.Column(db.Integer,nullable = False)
    quiz_date = db.Column(db.Date, nullable = False)
    chapter_id = db.Column(db.Integer, db.ForeignKey('chapter.id'), nullable=False)
    feedback = db.Column(db.String(250), nullable=True)
    chapter = db.relationship('Chapter', back_populates = 'chap_quiz')
    qsns = db.relationship('Question', back_populates = 'quiz',cascade = 'all, delete-orphan')
    score = db.relationship('Scores', back_populates = 'quiz',cascade = 'all, delete-orphan')
class Question(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    qsn = db.Column(db.String(350),nullable=False)
    opt1 = db.Column(db.String(160),nullable=False)
    opt2 = db.Column(db.String(160),nullable=False)
    opt3 = db.Column(db.String(160),nullable=True)
    opt4 = db.Column(db.String(160),nullable=True)
    crct_ans = db.Column(db.Integer,nullable=False)
    quiz_id = db.Column(db.Integer, db.ForeignKey('quiz.id'), nullable=False)
    quiz = db.relationship('Quiz', back_populates = 'qsns')
    
class Scores(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    score = db.Column(db.Integer,nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    quiz_id = db.Column(db.Integer, db.ForeignKey('quiz.id'), nullable=False)
    user = db.relationship('User', back_populates='scores')#user has scores-back populate
    quiz = db.relationship('Quiz', back_populates = 'score')#quiz has score
    quiz_taken_timestamp = db.Column(db.DateTime, nullable=False)
    percentage = db.Column(db.Integer,nullable=False)
    
    

def create_admin():
    admin = User.query.filter_by(is_admin=True).first()
    if not admin:
        password_hash = generate_password_hash('admin')
        admin = User(username= 'admin',
                     email = "admin@gmail.com",
                     passhash = password_hash,
                     name = 'Admin',
                     qualification='BS Data Science',
                     date_of_birth=date(2000,1,1),
                     is_admin = True)
        db.session.add(admin)
        db.session.commit()      



with app.app_context():
    db.create_all()
    create_admin()
    

#ROUTES

@app.route("/")
def home_page():
    return render_template('index.html')

@app.route("/login",methods=['GET','POST'])
def login():
    if request.method == 'GET':
        return render_template('login.html')
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username ).first()
        if user and user.is_flagged:
            flash('Your account has been suspended. Please contact admin.', 'danger')
            return render_template('login.html')
        if user and check_password_hash(user.passhash,password):
            session['user_id'] = user.id
            if user.is_admin:
                session['admin'] = user.id
                #return render_template('admin_dashboard.html',user=user)
                if 'admin' in session:
                    return redirect(url_for('admin_dashboard'))
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid username or password','info')
            return render_template('login.html')
            

@app.route("/register",methods=['GET','POST'])
def register():
    if request.method == 'GET':
        return render_template('register.html')
    if request.method == 'POST':
        name = request.form['name']
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        qualification = request.form['qualification']
        dob_str = request.form['date_of_birth']  
        dob = datetime.strptime(dob_str, "%Y-%m-%d").date()
        password_hash = generate_password_hash(password)
        user = User(name=name,username=username,email=email,passhash=password_hash,qualification=qualification,date_of_birth=dob)
        db.session.add(user)
        db.session.commit()
        return redirect(url_for('login'))   
    return render_template('register.html')

@app.route("/logout")
def logout():
    session.pop('user_id',None)
    session.pop('admin',None)
    return redirect(url_for('login'))

@app.route("/admin_dashboard", methods=['GET'])
def admin_dashboard():
    if 'admin' in session:
        search_query = request.args.get('search', '').strip()
        if search_query:
            subjects = Subject.query.filter(
                db.or_(
                    Subject.name.ilike(f'%{search_query}%'),
                    Subject.description.ilike(f'%{search_query}%')
                )
            ).all()
        else:
            subjects = Subject.query.all()
        all_scores = Scores.query.order_by(Scores.quiz_taken_timestamp.desc()).limit(10).all()
        
        return render_template('admin_dashboard.html', subject_created=subjects, all_scores=all_scores, search_query=search_query)
    return redirect(url_for('login'))    

@app.route('/user_management', methods=['GET'])
def user_management():
    if 'admin' not in session:
        return redirect(url_for('login'))
    search_query = request.args.get('search', '')
    if search_query:
        users = User.query.filter(
            (User.username.ilike(f'%{search_query}%')) |(User.email.ilike(f'%{search_query}%')) |(User.name.ilike(f'%{search_query}%'))).filter(User.is_admin == False).all()
    else:
        users = User.query.filter_by(is_admin=False).all()
    
    return render_template('user_management.html', users=users, search_query=search_query)

@app.route('/toggle_user_flag/<int:user_id>', methods=['POST'])
def toggle_user_flag(user_id):
    if 'admin' not in session:
        return redirect(url_for('login'))
    
    user = User.query.get(user_id)
    if user and not user.is_admin:
        user.is_flagged = not user.is_flagged
        db.session.commit()
        status = "flagged" if user.is_flagged else "unflagged"
        flash(f'User {user.username} has been {status}', 'success')
    
    return redirect(url_for('user_management'))
   
   
@app.route('/create_subject',methods=['GET','POST'])
def create_subject():
    if 'admin' in session:
        if request.method == 'POST':
            name = request.form['name']
            description = request.form['description']
            subject_standard = request.form['subject_standard']
            subject_to_create = Subject(name=name,description=description,subject_standard=subject_standard)
            db.session.add(subject_to_create)
            db.session.commit()
            flash('Subject created successfully!', 'success')
            return redirect(url_for('admin_dashboard')) 
        else:
            return render_template('sub_creation.html')  
    return redirect(url_for('login'))

@app.route('/edit_subject/<int:subject_id>',methods=['GET','POST'])
def edit_subject(subject_id):
    if 'admin' in session:
        subject_to_edit = Subject.query.filter_by(id =subject_id).first()
        if not subject_to_edit:
            return redirect(url_for('admin_dashboard'))
        if request.method == 'POST':
            name = request.form['name']
            description = request.form['description']
            subject_standard = request.form['subject_standard']
            
            subject_to_edit.name = name
            subject_to_edit.description = description
            subject_to_edit.subject_standard = subject_standard
            
            db.session.commit()
            flash('Subject Edited successfully!', 'success')
            return redirect(url_for('admin_dashboard')) 
        else:
            return render_template('sub_edit.html',subject = subject_to_edit)  
    return redirect('/login') 

@app.route('/delete_subject/<int:subject_id>',methods=['GET','POST'])
def delete_subject(subject_id):
    if 'admin' in session:
        subject_to_delete = Subject.query.filter_by(id =subject_id).first()
        if not subject_to_delete:
            return redirect(url_for('admin_dashboard'))
        # if request.method == 'POST':
        db.session.delete(subject_to_delete)
        db.session.commit()
        flash('Subject deleted successfully!', 'success')
        return redirect('/admin_dashboard')
        # flash('The delete of the subject cannot be done at this moment')
    return redirect('/login')

  

@app.route('/view_subject/<int:sub_id>', methods=['GET', 'POST'])
def view_subject(sub_id):
    if 'admin' in session:
        subject_to_view = Subject.query.filter_by(id=sub_id).first()
        if not subject_to_view:
            flash('Subject not found!', 'error')
            return redirect(url_for('admin_dashboard'))
        search_query = request.args.get('search', '').strip()
        chapters_query = Chapter.query.filter_by(subject_id=sub_id)
        if search_query:
            chapters = chapters_query.filter(
                db.or_(
                    Chapter.name.ilike(f'%{search_query}%'),
                    Chapter.description.ilike(f'%{search_query}%')
                )
            ).all()
        else:
            chapters = chapters_query.all()

        return render_template('sub_view.html', subject=subject_to_view, chapters_created=chapters, search_query=search_query)
    return redirect(url_for('login'))
     
@app.route('/create_chapter/<int:sub_id>',methods=['GET','POST'])
def add_chapter(sub_id):
    if 'admin' in session:
        if request.method == 'POST':
            name = request.form['name']
            description = request.form['description']
            chapter_to_add =    Chapter(
                name=name,
                description=description,
                subject_id = sub_id
            )
            db.session.add(chapter_to_add)
            db.session.commit()
            flash(' Chapter added successfully!', 'success')
            return redirect(url_for('view_subject',sub_id = sub_id)) 
        else:
            return render_template('chapter_add.html',subject_id = sub_id)  
    return redirect(url_for('login')) 
   
@app.route('/edit_chapter/<int:chapter_id>',methods=['GET','POST'])
def edit_chapter(chapter_id):
    if 'admin' in session:
        chapter_to_edit = Chapter.query.filter_by(id =chapter_id).first()
        if not chapter_to_edit:
            return redirect(url_for('admin_dashboard')) 
            return redirect(url_for('view_subject',sub_id = chapter_to_edit.subject_id))
        if request.method == "POST":
            name = request.form['name']
            description = request.form['description']
            
            chapter_to_edit.name = name
            chapter_to_edit.description = description
            
            db.session.commit()
            flash('Subject Edited successfully!', 'success')
            return redirect(url_for('view_subject',sub_id = chapter_to_edit.subject_id))
             
        else:
            return render_template('chapter_edit.html',chapter = chapter_to_edit)  
    return redirect('/login')    
   
   
@app.route('/delete_chapter/<int:chapter_id>',methods=['GET','POST'])
def delete_chapter(chapter_id):
    if 'admin' in session:
        chapter_to_delete = Chapter.query.filter_by(id =chapter_id).first()
        if not chapter_to_delete:
            return redirect(url_for('admin_dashboard'))
        subject_id = chapter_to_delete.subject_id
        db.session.delete(chapter_to_delete)
        db.session.commit()
        flash('chapter deleted successfully!', 'success')
        return redirect('/admin_dashboard')
    return redirect('/login') 

@app.route('/view_chapter/<int:chapter_id>', methods=['GET', 'POST'])
def view_chapter(chapter_id):
    if 'admin' in session:
        chapter_to_view = Chapter.query.filter_by(id=chapter_id).first()
        if not chapter_to_view:
            flash('Chapter not found!', 'error')
            return redirect(url_for('admin_dashboard'))

        search_query = request.args.get('search', '').strip()
        quiz_query = Quiz.query.filter_by(chapter_id=chapter_id)
        if search_query:
            quizzes = quiz_query.filter(db.or_(Quiz.name.ilike(f'%{search_query}%'),
                                               Quiz.feedback.ilike(f'%{search_query}%'))).all()
        else:
            quizzes = quiz_query.all()

        return render_template('chapter_view.html', chapter=chapter_to_view, quiz_created=quizzes, search_query=search_query)
    return redirect(url_for('login'))

   
@app.route('/create_quiz/<int:chapter_id>',methods=['GET','POST'])
def create_quiz(chapter_id):
    if 'admin' in session:
        if request.method == 'POST':
            name = request.form['name']
            time_str = request.form['quiz_time_duration']  
            hours, minutes = map(int, time_str.split(':'))
            quiz_time_duration = int(hours * 60 + minutes) 
            quiz_date = request.form['quiz_date']
            feedback = request.form['feedback']      
            quiz_date_formatted = datetime.strptime(quiz_date, "%Y-%m-%d").date() 
            quiz_to_add =  Quiz(
                name=name,
                quiz_time_duration=quiz_time_duration,
                quiz_date=quiz_date_formatted,
                feedback=feedback,
                chapter_id = chapter_id
            )
            db.session.add(quiz_to_add)
            db.session.commit()
            flash(' Quiz  added successfully!', 'success')
            return redirect(url_for('view_chapter',sub_id = quiz_to_add.chapter.subject_id,chapter_id = chapter_id)) 
        else:
            return render_template('quiz_add.html',chapter_id = chapter_id)  
    return redirect(url_for('login'))    
   
@app.route('/edit_quiz/<int:quiz_id>',methods=['GET','POST'])
def edit_quiz(quiz_id):
    if 'admin' in session:
        quiz_to_edit = Quiz.query.filter_by(id=quiz_id).first()
        if not quiz_to_edit:
            return redirect(url_for('admin_dashboard'))
        if request.method == 'POST':
            name = request.form['name']
            time_taken = request.form['quiz_time_duration']
            hours,minutes = map(int,time_taken.split(':'))
            quiz_time_duration = int(hours*60 + minutes)
            quiz_date = request.form['quiz_date']
            feedback = request.form['feedback']      
            quiz_date_formatted = datetime.strptime(quiz_date, "%Y-%m-%d").date()
            
            quiz_to_edit.name = name
            quiz_to_edit.quiz_time_duration = quiz_time_duration
            quiz_to_edit.quiz_date = quiz_date_formatted
            quiz_to_edit.feedback = feedback
            
            db.session.commit()
            flash('Quiz updated successfully!', 'success')
            return redirect(url_for('view_chapter', chapter_id=quiz_to_edit.chapter_id))
        else:
            return render_template('quiz_edit.html', quiz_to_edit =quiz_to_edit)
    return redirect(url_for('login'))

@app.route('/delete_quiz/<int:quiz_id>',methods=['GET','POST'])
def delete_quiz(quiz_id):
    if 'admin' in session:
        quiz_to_delete = Quiz.query.filter_by(id=quiz_id).first()
        if not quiz_to_delete:
            return redirect(url_for('admin_dashboard'))
        chapter_id = quiz_to_delete.chapter_id
        db.session.delete(quiz_to_delete)
        db.session.commit()
        flash('Quiz deleted successfully!', 'success')
        return redirect(url_for('view_chapter', chapter_id=chapter_id))
    return redirect(url_for('login'))

@app.route('/view_quiz/<int:quiz_id>',methods=['GET','POST'])
def view_quiz(quiz_id): 
    if 'admin' in session:
        quiz_to_view = Quiz.query.filter_by(id =quiz_id).first()
        questions = Question.query.filter_by(quiz_id = quiz_id).all()
        return render_template('quiz_view.html',quiz = quiz_to_view, questions_created = questions)
    return redirect(url_for('login'))

@app.route('/create_question/<int:quiz_id>', methods=['GET', 'POST'])
def create_question(quiz_id):
    if 'admin' in session:
        if request.method == 'POST':
            qsn = request.form['qsn']
            opt1 = request.form['opt1']
            opt2 = request.form['opt2']
            opt3 = request.form['opt3']
            opt4 = request.form['opt4']
            crct_ans = request.form['crct_ans']
            
            question_to_add = Question(
                qsn=qsn,
                opt1=opt1,
                opt2=opt2,
                opt3=opt3,
                opt4=opt4,
                crct_ans=crct_ans,
                quiz_id=quiz_id
            )
            db.session.add(question_to_add)
            db.session.commit()
            flash('Question added successfully!', 'success')
            return redirect(url_for('view_quiz', quiz_id=quiz_id))
        else:
            return render_template('question_add.html', quiz_id=quiz_id)
    return redirect(url_for('login'))

@app.route('/edit_question/<int:question_id>', methods=['GET', 'POST'])
def edit_question(question_id):
    if 'admin' in session:
        question_to_edit = Question.query.filter_by(id=question_id).first()
        if not question_to_edit:
            return redirect(url_for('admin_dashboard'))
        if request.method == 'POST':
            qsn = request.form['qsn']
            opt1 = request.form['opt1']
            opt2 = request.form['opt2']
            opt3 = request.form['opt3']
            opt4 = request.form['opt4']
            crct_ans = request.form['crct_ans']
            
            question_to_edit.qsn = qsn
            question_to_edit.opt1 = opt1
            question_to_edit.opt2 = opt2
            question_to_edit.opt3 = opt3
            question_to_edit.opt4 = opt4
            question_to_edit.crct_ans = crct_ans
            
            db.session.commit()
            flash('Question updated successfully!', 'success')
            return redirect(url_for('view_quiz', quiz_id=question_to_edit.quiz_id))
        else:
            return render_template('question_edit.html', question=question_to_edit)
    return redirect(url_for('login'))

@app.route('/delete_question/<int:question_id>', methods=['GET', 'POST'])
def delete_question(question_id):
    if 'admin' in session:
        question_to_delete = Question.query.filter_by(id=question_id).first()
        if not question_to_delete:
            return redirect(url_for('admin_dashboard'))
        quiz_id = question_to_delete.quiz_id
        db.session.delete(question_to_delete)
        db.session.commit()
        flash('Question deleted successfully!', 'success')
        return redirect(url_for('view_quiz', quiz_id=quiz_id))
    return redirect(url_for('login'))



@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user = User.query.get(session['user_id'])
   
    search_query = request.args.get('search', '').strip()
    selected_standard = request.args.get('standard', 'all')

    subjects_query = Subject.query
    if search_query:
        subjects_query = subjects_query.filter(
            db.or_(
                Subject.name.ilike(f'%{search_query}%'),
                Subject.description.ilike(f'%{search_query}%')
            )
        )
    if selected_standard != 'all':
        subjects_query = subjects_query.filter(Subject.subject_standard == selected_standard)
    subjects = subjects_query.all()
    return render_template('dashboard.html', user=user, subjects=subjects, search_query=search_query, selected_standard=selected_standard)


@app.route('/user_profile')
def user_profile():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user = User.query.get(session['user_id'])
    if not user:
        return redirect(url_for('logout'))
    
    return render_template('user_profile.html', user=user)
    
@app.route('/view_user_subject/<int:subject_id>')
def view_user_subject(subject_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    user = User.query.get(session['user_id'])
    subject = Subject.query.get(subject_id)
    chapters = Chapter.query.filter_by(subject_id=subject_id).all()
    today = date.today()  
    return render_template('user_subject_view.html', user=user, subject=subject, chapters=chapters,today=today)

@app.route('/start_quiz/<int:quiz_id>')
def start_quiz(quiz_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    quiz = Quiz.query.get(quiz_id)
    if not quiz:
        flash('Quiz not found!', 'error')
        return redirect(url_for('dashboard'))
    questions = Question.query.filter_by(quiz_id=quiz_id).all()
    if not questions:
        flash('No questions available for this quiz!', 'error')
        return redirect(url_for('dashboard'))
    return render_template('take_quiz.html', quiz=quiz, questions=questions)

@app.route('/submit_quiz/<int:quiz_id>', methods=['POST'])
def submit_quiz(quiz_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    quiz = Quiz.query.get(quiz_id)
    questions = Question.query.filter_by(quiz_id=quiz_id).all() 
    score = 0
    for question in questions:
        user_answer = request.form.get(f'answer_{question.id}')
        if user_answer and int(user_answer) == question.crct_ans:
            score += 1
    total_questions = len(questions)
    percentage = round((score / total_questions) * 100)
    new_score = Scores(score=score,user_id=session['user_id'],quiz_id=quiz_id,
                       quiz_taken_timestamp=datetime.now(),percentage=percentage)
    
    db.session.add(new_score)
    db.session.commit()
    
    return render_template('quiz_result.html',score=score,total_questions=total_questions,percentage=percentage)
    

@app.route('/user_history')
def user_history():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    user = User.query.get(session['user_id'])
    scores = db.session.query(Scores, Quiz, Chapter, Subject).join(Quiz, Scores.quiz_id == Quiz.id).join(
        Chapter, Quiz.chapter_id == Chapter.id).join(Subject, Chapter.subject_id == Subject.id).filter(
        Scores.user_id == session['user_id']).order_by(
        Scores.quiz_taken_timestamp.desc()).all()
    return render_template('user_history.html', user=user, scores=scores)

@app.route('/user_specific_history/<int:user_id>')
def user_specific_history(user_id):
    if 'admin' not in session:
        return redirect(url_for('login'))
    
    user = User.query.get(user_id)
    if not user:
        flash('User not found!', 'error')
        return redirect(url_for('user_management'))
    
    user_scores = db.session.query(Scores)\
        .filter_by(user_id=user_id)\
        .order_by(Scores.quiz_taken_timestamp.desc())\
        .all()
    
    return render_template('user_specific_history.html', user=user, user_scores=user_scores)
      
@app.route('/admin_summary')
def admin_summary():
    if 'admin' not in session:
        return redirect(url_for('login'))

    plt.figure(figsize=(10, 6))
    quizzes = Quiz.query.all()
    quiz_names = [quiz.name for quiz in quizzes]
    participation_counts = [len(quiz.score) for quiz in quizzes]
    
    plt.bar(quiz_names, participation_counts)
    plt.xticks(rotation=45)
    plt.title('Quiz Participation Summary')
    plt.xlabel('Quizzes')
    plt.ylabel('Number of Participants')
    
    
    buffer = io.BytesIO()
    plt.savefig(buffer, format='png', bbox_inches='tight')
    buffer.seek(0)
    participation_chart = base64.b64encode(buffer.getvalue()).decode()
    plt.close()
    
    plt.figure(figsize=(10, 6))
    subjects = Subject.query.all()
    subject_names = [subject.name for subject in subjects]
    avg_scores = []
    
    for subject in subjects:
        total_score = 0
        total_attempts = 0
        for chapter in subject.sub_chapter:
            for quiz in chapter.chap_quiz:
                if quiz.score: 
                    total_score += sum([score.score for score in quiz.score])
                    total_attempts += len(quiz.score)
        avg_score = total_score/total_attempts if total_attempts > 0 else 0
        avg_scores.append(avg_score)
    
    plt.bar(subject_names, avg_scores)
    plt.xticks(rotation=45)
    plt.title('Average Score per Subject')
    plt.xlabel('Subjects')
    plt.ylabel('Average Score')
    
    buffer = io.BytesIO()
    plt.savefig(buffer, format='png', bbox_inches='tight')
    buffer.seek(0)
    subject_chart = base64.b64encode(buffer.getvalue()).decode()
    plt.close()

    total_users = User.query.filter_by(is_admin=False).count()
    total_quizzes = Quiz.query.count()
    total_subjects = Subject.query.count()
    
    return render_template('admin_summary.html',participation_chart=participation_chart,subject_chart=subject_chart,
                        total_users=total_users,total_quizzes=total_quizzes,total_subjects=total_subjects)   
    
    
if __name__ == "__main__":
    app.run(debug=True)