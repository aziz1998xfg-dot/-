import os
from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = "dz_artisan_secret_key"

# --- [كلمة المرور السرية الخاصة بك] ---
ADMIN_PASSWORD = "azizi9999gh" 

RENDER_DISK_PATH = '/opt/render/project/src/data'
if os.path.exists(RENDER_DISK_PATH):
    PERSISTENT_DIR = RENDER_DISK_PATH
else:
    PERSISTENT_DIR = os.path.abspath(os.path.dirname(__file__))

app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{os.path.join(PERSISTENT_DIR, "hana_ntowro.db")}'
app.config['UPLOAD_FOLDER'] = os.path.join(PERSISTENT_DIR, 'static/uploads')

db = SQLAlchemy(app)
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

class Artisan(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    wilaya = db.Column(db.String(50), nullable=False)
    job_type = db.Column(db.String(50), nullable=False)
    description = db.Column(db.Text, nullable=True)
    receipt_img = db.Column(db.String(200), nullable=True)
    status = db.Column(db.String(20), default="Pending_Payment")

WILAYAS = [
    "01- أدرار", "02- الشلف", "03- الأغواط", "04- أم البواقي", "05- باتنة", "06- بجاية", 
    "07- بسكرة", "08- بشار", "09- البليدة", "10- البويرة", "11- تمنراست", "12- تبسة", 
    "13- تلمسان", "14- تيارت", "15- تيزي وزو", "16- الجزائر", "17- الجلفة", "18- جيجل", 
    "19- سطيف", "20- سعيدة", "21- سكيكدة", "22- سيدي بلعباس", "23- عنابة", "24- قالمة", 
    "25- قسنطينة", "26- المدية", "27- مستغانم", "28- المسيلة", "29- معسكر", "30- ورقلة", 
    "31- وهران", "32- البيض", "33- إليزي", "34- برج بوعريريج", "35- بومرداس", "36- الطارف", 
    "37- تندوف", "38- تسمسيلت", "39- الوادي", "40- خنشلة", "41- سوق أهراس", "42- تيبازة", 
    "43- ميلة", "44- عين الدفلى", "45- النعامة", "46- عين تموشنت", "47- غرداية", "48- غليزان",
    "49- تيميمون", "50- برج باجي مختار", "51- أولاد جلال", "52- بني عباس", "53- عين صالح", 
    "54- عين قزام", "55- تقرت", "56- جانت", "57- المغير", "58- المنيعة"
]

JOBS = ["ميكانيكي", "سباك", "كهربائي", "حلاق متنقل", "لحام", "صيانة عتاد المنزل", "خدمات التوصيل", "بناء", "دهان", "أخرى"]

# 1. الصفحة الرئيسية المشتركة (عرض وبحث + تفعيل مباشر)
@app.route('/', methods=['GET', 'POST'])
def index():
    # معالجة دخول الأدمن من نفس الصفحة
    if request.method == 'POST' and 'admin_pass' in request.form:
        if request.form['admin_pass'] == ADMIN_PASSWORD:
            session['is_admin'] = True
            flash("مرحباً بك يا مسؤول! تم تفعيل وضع إدارة الصلاحيات المباشر.", "success")
        else:
            flash("كلمة المرور خاطئة!", "danger")
            
    selected_wilaya = request.args.get('wilaya')
    selected_job = request.args.get('job')
    search_text = request.args.get('search_text')
    
    # إذا كنت أدمن: ستعرض لك الحسابات المفعلة والمعلقة للمراجعة، وإذا كنت زائر عادي: المفعلة فقط
    if session.get('is_admin'):
        query = Artisan.query
    else:
        query = Artisan.query.filter_by(status="Activated")
        
    if selected_job:
        query = query.filter_by(job_type=selected_job)
    if selected_wilaya:
        query = query.filter_by(wilaya=selected_wilaya)
    if search_text:
        query = query.filter(Artisan.description.like(f"%{search_text}%") | Artisan.name.like(f"%{search_text}%"))
        
    artisans = query.all()
    return render_template('index.html', artisans=artisans, wilayas=WILAYAS, jobs=JOBS)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        phone = request.form['phone']
        wilaya = request.form['wilaya']
        job = request.form['job']
        description = request.form['description']
        
        file = request.files['receipt']
        filename = None
        if file:
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            
        new_artisan = Artisan(name=name, phone=phone, wilaya=wilaya, job_type=job, description=description, receipt_img=filename, status="Under_Review")
        db.session.add(new_artisan)
        db.session.commit()
        flash("تم تسجيل معلوماتك بنجاح! سيتم مراجعة الدفع وتفعيل صفحتك قريباً.", "success")
        return redirect(url_for('index'))
    return render_template('register.html', wilayas=WILAYAS, jobs=JOBS)

@app.route('/delete-service', methods=['GET', 'POST'])
def delete_service():
    if request.method == 'POST':
        phone = request.form['phone']
        artisan = Artisan.query.filter_by(phone=phone).first()
        if artisan:
            db.session.delete(artisan)
            db.session.commit()
            flash("تم حذف بطاقتك بنجاح.", "success")
            return redirect(url_for('index'))
        flash("رقم الهاتف غير مسجل.", "danger")
    return render_template('delete_service.html')

# --- [مسارات التحكم السريع الخاصة بك كمسؤول] ---
@app.route('/admin/approve/<int:id>')
def approve_artisan(id):
    if not session.get('is_admin'): return redirect(url_for('index'))
    artisan = Artisan.query.get_or_404(id)
    artisan.status = "Activated"
    db.session.commit()
    flash(f"تم منح الصلاحية وتفعيل خدمة {artisan.name} بنجاح!", "success")
    return redirect(url_for('index'))

@app.route('/admin/reject/<int:id>')
def reject_artisan(id):
    if not session.get('is_admin'): return redirect(url_for('index'))
    artisan = Artisan.query.get_or_404(id)
    db.session.delete(artisan)
    db.session.commit()
    flash("تم رفض وحذف الطلب.", "info")
    return redirect(url_for('index'))

@app.route('/admin/logout')
def admin_logout():
    session.pop('is_admin', None)
    return redirect(url_for('index'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
