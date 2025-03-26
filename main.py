from flask import Flask,render_template,redirect,request,url_for,flash,session 
from flask_sqlalchemy import SQLAlchemy
import os
from werkzeug.security import generate_password_hash,check_password_hash
from datetime import datetime,date



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
def hello_world():
    return render_template('homepage.html')

@app.route("/login",methods=['GET','POST'])
def login():
    if request.method == 'GET':
        return render_template('login.html')
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username ).first()
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
        dob_str = request.form['date_of_birth']  # Assuming input type="date"
        dob = datetime.strptime(dob_str, "%Y-%m-%d").date()
        password_hash = generate_password_hash(password)
        user = User(name=name,username=username,email=email,passhash=password_hash,qualification=qualification,date_of_birth=dob)
        db.session.add(user)
        db.session.commit()
        return redirect(url_for('login'))   
    return render_template('register.html')



@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    user = User.query.get(session['user_id'])
    return render_template('dashboard.html', user=user)


@app.route("/admin_dashboard",methods=['GET'])
def admin_dashboard():
    if 'admin' in session:
        subs = Subject.query.all()
        return render_template('admin_dashboard.html',subject_created = subs)
   
   
@app.route('/create_subject',methods=['GET','POST'])
def create_subject():
    if 'admin' in session:
        if request.method == 'POST':
            name = request.form['name']
            description = request.form['description']
            subject_standard = request.form['subject_standard']
            subject_to_create = Subject(
                name=name,
                description=description,
                subject_standard=subject_standard
            )
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
        if request.method == 'POST':
            db.session.delete(subject_to_delete)
            db.session.commit()
            flash('Subject deleted successfully!', 'success')
            return redirect('/admin_dashboard')
        flash('The delete of the subject cannot be done at this moment')
    return redirect('/login')


@app.route('/view_subject/<int:sub_id>',methods=['GET','POST'])
def view_subject(sub_id):
    if 'admin' in session:
        subject_to_view = Subject.query.filter_by(id =sub_id).first()
        chapters = Chapter.query.filter_by(subject_id = sub_id).all()
        return render_template('sub_view.html',subject = subject_to_view, chapters_created = chapters)
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

# @app.route('/view_chapter/<int:chapter_id>',methods=['GET','POST'])
# def view_chapter(sub_id,chapter_id):
#     if 'admin' in session:
#         chapter_to_view = Chapter.query.filter_by(id =chapter_id).first()
#         quiz = Quiz.query.filter_by(chapter_id = chapter_id).all()
#         return render_template('chapter_view.html',chapter = chapter_to_view, quiz_created = quiz)
#     return redirect(url_for('login'))


@app.route('/view_chapter/<int:chapter_id>',methods=['GET','POST'])
def view_chapter(chapter_id):
    if 'admin' in session:
        chapter_to_view = Chapter.query.filter_by(id=chapter_id).first()
        quizzes = Quiz.query.filter_by(chapter_id=chapter_id).all()
        return render_template('chapter_view.html', 
                             chapter=chapter_to_view, 
                             quiz_created=quizzes)
    return redirect(url_for('login'))

   
@app.route('/create_quiz/<int:chapter_id>',methods=['GET','POST'])
def create_quiz(chapter_id):
    if 'admin' in session:
        if request.method == 'POST':
            name = request.form['name']
            time_str = request.form['quiz_time_duration']  
            hours, minutes = map(int, time_str.split(':'))
            quiz_time_duration = hours * 60 + minutes 
            # quiz_time_duration = request.form['quiz_time_duration']
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

# @app.route('/edit_quiz/<int:quiz_id>',methods=['GET','POST'])
# def edit_quiz(quiz_id):
#     if 'admin' in session:
#         quiz_to_edit = Quiz.query.filter_by(id =quiz_id).first()
#         if quiz_to_edit:
#             if request.method == 'POST':
#                 name = request.form['name']
#                 quiz_time_duration = request.form['quiz_time_duration']
#                 quiz_date = request.form['quiz_date']
#                 feedback = request.form['feedback']      
#                 quiz_date_formatted = datetime.strptime(quiz_date, "%Y-%m-%d").date() 
                
#                 quiz_to_edit.name  =  name,
#                 quiz_to_edit.quiz_time_duration =  quiz_time_duration,
#                 quiz_to_edit.quiz_date = quiz_date_formatted,
#                 quiz_to_edit.feedback = feedback,
                
                
                
#                 db.session.commit()
#                 flash(' Quiz  added successfully!', 'success')
#                 return redirect(url_for('view_chapter',chapter_id = quiz_to_edit.chapter_id,)) 
#             else:
#                 return render_template('quiz_add.html',quiz_to_edit=quiz_to_edit)  
#         return redirect('/view_chapter',sub_id = quiz_to_edit.chapter.subject_id,chapter_id = quiz_to_edit.chapter_id)
#     return redirect(url_for('login'))     
   
@app.route('/edit_quiz/<int:quiz_id>',methods=['GET','POST'])
def edit_quiz(quiz_id):
    if 'admin' in session:
        quiz_to_edit = Quiz.query.filter_by(id=quiz_id).first()
        if not quiz_to_edit:
            return redirect(url_for('admin_dashboard'))
        if request.method == 'POST':
            name = request.form['name']
            quiz_time_duration = request.form['quiz_time_duration']
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

# @app.route('/delete_quiz/<int:quiz_id>',methods=['GET','POST'])
# def delete_quiz(quiz_id):
#     if 'admin' in session:
#         quiz_to_delete = Quiz.query.filter_by(id =quiz_id).first()
#         if not quiz_to_delete:
#             return redirect(url_for('admin_dashboard'))
#         chapter_id = quiz_to_delete.chapter_id
#         db.session.delete(quiz_to_delete)
#         db.session.commit()
#         flash('Quiz deleted successfully!', 'success')
#         return redirect('/view_chapter',chapter_id = chapter_id)
#     return redirect('/login')  


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




if __name__ == "__main__":
    app.run(debug=True)