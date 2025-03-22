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
    

#routes 

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
                return render_template('admin_dashboard.html',user=user)
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



# @app.route("/dashboard")
# def dashboard():
#     if 'user_id' in session:
#         user = User.query.get(session['user_id'])
#         # if user.is_admin:
#         #     return render_template('admin_dashboard.html',user=user)
#         return render_template('dashboard.html',user=user)
#     else:
#         return redirect(url_for('login'))

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    user = User.query.get(session['user_id'])
    return render_template('dashboard.html', user=user)


@app.route("/admin_dashboard")
def admin_dashboard():
    render_template('admin_dashboard.html')
    
    
if __name__ == "__main__":
    app.run(debug=True)