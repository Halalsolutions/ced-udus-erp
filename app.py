from flask import Flask, request, render_template, url_for, redirect, flash
from flask_login import LoginManager, UserMixin, login_user, login_required, current_user, logout_user
from flask_toastr import Toastr
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Column, String, LargeBinary, event, func, cast, Date
import os
import calendar
import uuid
from datetime import datetime
from functools import wraps


#Setting up Flask
app = Flask(__name__)



# Flask Configurations
app.secret_key = os.environ.get('secret_key')
toastr = Toastr(app)
app.config['TOASTR_TIMEOUT'] = 3000
app.config['UPLOAD_FOLDER'] = './static/uploads'

# DB configurations (sqlalchemy)
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get('database_uri')
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)

# Setup loging manager
login_manager = LoginManager()
login_manager.init_app(app)
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


## User Table
class User(db.Model, UserMixin):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(250), nullable=False)
    last_name = db.Column(db.String(250), nullable=False)
    email = db.Column(db.String(250), nullable=False)
    password = db.Column(db.String(250), nullable=False)
    avatar_location = db.Column(db.String(250))

class Facilitator(db.Model):
    __tablename__ = 'facilitators'
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(250), nullable=False)
    last_name = db.Column(db.String(250), nullable=False)
    email = db.Column(db.String(250))
    joining_date = db.Column(db.Date)
    mobile_number = db.Column(db.String(255))
    gender = db.Column(db.String(50), nullable=False)
    course = db.Column(db.String(250))
    department = db.Column(db.String(250), nullable=False)

class Trainee(db.Model):
    __tablename__ = 'trainees'
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(250), nullable=False)
    last_name = db.Column(db.String(250), nullable=False)
    email = db.Column(db.String(250), nullable=False)
    registration_date = db.Column(db.Date, nullable=False)
    department = db.Column(db.String(250), nullable=False)
    gender = db.Column(db.String(250), nullable=False)
    mobile_number = db.Column(db.String(255))
    course = db.Column(db.String(250), nullable=False)
    address = db.Column(db.String(250))

class Course(db.Model):
    __tablename__ = 'courses'
    id = db.Column(db.Integer, primary_key=True)
    course_name = db.Column(db.String(250), nullable=False, unique=True)
    course_code = db.Column(db.String(250), nullable=False)
    course_details = db.Column(db.Text, nullable=False)
    course_duration = db.Column(db.String(250), nullable=False)
    course_price = db.Column(db.Integer, nullable=False)
    facilitator_name = db.Column(db.String(250), nullable=False)
    students_enrolled = db.Column(db.Integer)
    image_name = db.Column(db.String(255))


class InventoryItem(db.Model):
    __tablename__ = 'inventory_items'
    id = db.Column(db.Integer, primary_key=True)
    item_name = db.Column(db.String(250), nullable=False)
    course_for = db.Column(db.String(250), nullable=False)
    department_for = db.Column(db.String(250), nullable=False)
    price = db.Column(db.Integer, nullable=False)
    purchase_date = db.Column(db.Date, nullable=False)
    status = db.Column(db.String(250), nullable=False)
    item_details = db.Column(db.Text, nullable=False)

class Department(db.Model):
    __tablename__ = 'departments'
    id = db.Column(db.Integer, primary_key=True)
    department_name = db.Column(db.String(250), nullable=False)
    department_head = db.Column(db.String(250))
    mobile_number = db.Column(db.String(255))
    email = db.Column(db.String(250))

class Staff(db.Model):
    __tablename__ = 'staffs'
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(250), nullable=False)
    last_name = db.Column(db.String(250), nullable=False)
    email = db.Column(db.String(250))
    joining_date = db.Column(db.Date)
    mobile_number = db.Column(db.String(255))
    gender = db.Column(db.String(250))
    designation = db.Column(db.String(250))
    department = db.Column(db.String(250))
    address = db.Column(db.String(250))

class Fee(db.Model):
    __tablename__ = 'fees'
    id = db.Column(db.Integer, primary_key=True)
    trainee_name = db.Column(db.String(255))
    trainee_id = db.Column(db.String(255))
    invoice_number = db.Column(db.Integer, unique=True)
    department = db.Column(db.String(255))
    course = db.Column(db.String(255))
    payment_type = db.Column(db.String(255))
    payment_status = db.Column(db.String(255))
    payment_date = db.Column(db.Date)
    amount = db.Column(db.Integer)





# Create all database
with app.app_context():
    db.create_all()


# setting default starting value for fee.invoice_number and incrementing it by 1
@event.listens_for(Fee, 'before_insert')
def generate_invoice_number(mapper, connection, target):
    if not target.invoice_number:
        last_invoice = (
            db.session.query(Fee)
            .order_by(Fee.id.desc())
            .first()
        )
        target.invoice_number = last_invoice.invoice_number + 1 if last_invoice else 45778

# Calculate all fees collected
def calculate_total_amount():
    total_amount = db.session.query(db.func.sum(Fee.amount)).scalar()
    return total_amount if total_amount else 0

# claculate Students Increase Percentage
def calculate_percentage_increased(trainees):
    current_month = datetime.now().month
    last_month_trainees = Trainee.query.filter(func.extract('month', cast(Trainee.registration_date, Date)) == current_month - 1).count()
    current_month_trainees = Trainee.query.filter(func.extract('month', cast(Trainee.registration_date, Date)) == current_month).count()
    if last_month_trainees == 0:
        return "No Trainees Registered last month"

    percentage_increase = ((current_month_trainees - last_month_trainees) / last_month_trainees) * 100
    return f"{percentage_increase:.2f}% increase from last month"

# claculate Fees Increase Percentage
def calculate_fees_percentage_increased(trainees):
    current_month = datetime.now().month
    last_month_trainees = Fee.query.filter(func.extract('month', cast(Fee.payment_date, Date)) == current_month - 1).count()
    current_month_trainees = Fee.query.filter(func.extract('month', cast(Fee.payment_date, Date)) == current_month).count()
    if last_month_trainees == 0:
        return "No Fees Were Collected last month"

    percentage_increase = ((current_month_trainees - last_month_trainees) / last_month_trainees) * 100
    return f"{percentage_increase:.2f}% increase from last month"


def number_to_month_name(month_number):
    try:
        return calendar.month_name[month_number]
    except (IndexError, ValueError):
        return 'Invalid Month Number'


# get income expense data for moris chart by month
def get_monthly_income_expense_data():
    # calculate total income by month
    income_data = db.session.query(func.extract('month', Fee.payment_date).label('month'),
                                   func.sum(Fee.amount).label('total_income')
                                   ).group_by(func.extract('month', Fee.payment_date)).all()

    # calculate total expenses by month
    expense_data = db.session.query(func.extract('month', InventoryItem.purchase_date).label('month'),
                                    func.sum(InventoryItem.price).label('total_expenses')
                                    ).group_by(func.extract('month', InventoryItem.purchase_date)).all()

    # Convert the result to a list of dictionaries
    income_data = [{'month': month, 'total_income': int(total_income)} for month, total_income in income_data]
    expense_data = [{'month': month, 'total_expenses': int(total_expenses)} for month, total_expenses in expense_data]

    return income_data, expense_data

# covert string date to date ob
def to_date_obj(date):
    payment_date_str = date
    payment_date_obj = datetime.strptime(payment_date_str, '%Y-%m-%d')
    return payment_date_obj
# Functions t check current user
def check_login_status():
    if not current_user.is_authenticated:
        flash('Login To Continue')
        return render_template('page-login.html')

def login_is_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('Login To Continue')
            return redirect(url_for('login'))

        return f(*args, **kwargs)
    return decorated_function

@app.route('/')
def login_or_dashboard():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    else:
        return redirect(url_for('login'))



@app.route('/dashboard')
@login_is_required
def home():
    income_data, expense_data = get_monthly_income_expense_data()

    current_month = datetime.now().month

    #New Students Total
    new_trainees = Trainee.query.filter(
        func.extract('month', Trainee.registration_date) == current_month).count()
    print(new_trainees)

    # Courses Length Calculate
    all_courses = Course.query.all()
    course_length = len(all_courses)

    # All Students length and percentage Increase calculation
    all_trainees = Trainee.query.all()
    trainees_length = len(all_trainees)
    percentage_increase = calculate_percentage_increased(all_trainees)

    # Fee percentage increase calculation
    all_fees = Fee.query.all()
    fee_percentage_increase = calculate_fees_percentage_increased(all_fees)

    # calculate total fees collected
    all_fees = Fee.query.all()
    total_amount = calculate_total_amount()

    # Facilitators
    all_facilitators = Facilitator.query.all()

    return render_template('index-2.html', trainees=all_trainees,
                           percentage_increase=percentage_increase,
                           trainees_length=trainees_length,
                           new_trainees=new_trainees,
                           course_length=course_length,
                           fees_collected=total_amount,
                           fee_percentage_increase=fee_percentage_increase,
                           all_facilitators=all_facilitators,
                           all_trainees=all_trainees,
                           income_data=income_data,
                           expense_data=expense_data)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        new_user = User(first_name=request.form.get('first_name'),
                        last_name=request.form.get('last_name'),
                        email=request.form.get('email'),
                        password=request.form.get('password'),
                        avatar_location='../static/images/profile-photo.png')
        db.session.add(new_user)
        db.session.commit()
        login_user(new_user)
        flash('Welcome To Center For Entrepreneurship Development UDUSOK')
        return redirect(url_for('home'))
    return render_template('page-register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        user = User.query.filter_by(email=email).first()

        if user is not None:
            if password == user.password:
                login_user(user)
                flash('Login Successful', 'success')
                return redirect(url_for('home'))
            else:
                flash('Invalid Password', 'error')
                return redirect(url_for('login'))
        else:
            flash('User not Found', 'error')
            return redirect(url_for('login'))
    return render_template('page-login.html')

@app.route('/logout')
def logout():
    first_name = current_user.first_name
    last_name = current_user.last_name
    logout_user()
    flash(f'{first_name} {last_name} Logout Successful')
    return redirect(url_for('login'))

@app.route("/all-facilitators")
@login_is_required
def all_facilitators():

    facilitators = Facilitator.query.all()
    return render_template("all-professors.html", faclitators=facilitators)

@app.route("/add-facilitator", methods=['GET', 'POST'])
@login_is_required
def add_facilitator():

    departments = Department.query.all()
    if request.method == 'POST':

        date = to_date_obj(request.form.get('joining_date'))

        new_facilitator = Facilitator(first_name=request.form.get('first_name'),
                                      last_name=request.form.get('last_name'),
                                      email=request.form.get('email'),
                                      joining_date=date,
                                      mobile_number=request.form.get('mobile_number'),
                                      gender=request.form.get('gender'),

                                      department=request.form.get('department')
                                      )
        db.session.add(new_facilitator)
        db.session.commit()
        flash("Facilitator Added Successfully", "success")
        return redirect(url_for('all_facilitators'))
    return render_template('add-professor.html', departments=departments)

@app.route("/edit-facilitator", methods=['GET', 'POST'])
@login_is_required
def edit_facilitator():


    facilitator_to_edit = Facilitator.query.get(request.args.get('facilitator_id'))
    departments = Department.query.all()
    if request.method == 'POST':

        date = to_date_obj(request.form.get('joining_date'))

        facilitator_to_edit.first_name = request.form.get('first_name')
        facilitator_to_edit.last_name = request.form.get('last_name')
        facilitator_to_edit.email = request.form.get('email')
        facilitator_to_edit.joining_date = date
        facilitator_to_edit.mobile_number = request.form.get('mobile_number')
        facilitator_to_edit.gender = request.form.get('gender')

        facilitator_to_edit.department = request.form.get('department')
        db.session.commit()
        flash("Facilitator Edited Successfully", "success")
        return redirect(url_for('all_facilitators'))
    return render_template('edit-professor.html', facilitator_to_edit=facilitator_to_edit, departments=departments)

@app.route('/delete-facilitator')
@login_is_required
def delete_facilitator():

    facilitator_to_delete = Facilitator.query.get(request.args.get('facilitator_id'))
    db.session.delete(facilitator_to_delete)
    db.session.commit()
    flash('Facilitator Deleted Successfully', 'success')
    return redirect(url_for('all_facilitators'))


@app.route("/facilitator-profile")
@login_is_required
def facilitator_profile():

    return render_template('professor-profile.html')

@app.route("/all-trainees")
@login_is_required
def all_trainees():

    trainees = Trainee.query.all()
    return render_template('all-students.html', trainees=trainees)

@app.route("/add-trainee", methods=['GET', 'POST'])
@login_is_required
def add_trainee():

    courses = Course.query.all()
    departments = Department.query.all()
    if request.method == 'POST':
        course_to_increment = Course.query.filter_by(course_name=request.form.get('course')).first()

        date = to_date_obj(request.form.get('registration_date'))

        print(course_to_increment)
        print(request.form.get('course'))
        new_trainee = Trainee(first_name=request.form.get('first_name'),
                              last_name=request.form.get('last_name'),
                              email=request.form.get('email'),
                              registration_date=date,
                              department=request.form.get('department'),
                              course=request.form.get('course'),
                              gender=request.form.get('gender'),
                              mobile_number=request.form.get('mobile_number'),
                              address=request.form.get('address')
                              )
        course_to_increment.students_enrolled += 1
        db.session.add(new_trainee)
        db.session.commit()
        flash('Trainee Added Successfully', 'success')
        return redirect(url_for('all_trainees'))
    return render_template('add-student.html', courses=courses, departments=departments)

@app.route('/edit-trainee', methods=['GET', 'POST'])
@login_is_required
def edit_trainee():

    trainee_to_edit = Trainee.query.get(request.args.get('trainee_id'))
    if request.method == 'POST':
        date = to_date_obj(request.form.get('registration_date'))

        trainee_to_edit.first_name = request.form.get('first_name')
        trainee_to_edit.last_name = request.form.get('last_name')
        trainee_to_edit.email = request.form.get('email')
        trainee_to_edit.registration_date = date
        trainee_to_edit.department = request.form.get('department')
        trainee_to_edit.course = request.form.get('course')
        trainee_to_edit.gender = request.form.get('gender')
        trainee_to_edit.mobile_number = request.form.get('mobile_number')
        trainee_to_edit.address = request.form.get('address')
        db.session.commit()
        flash('Trainee Edited Successfully', 'success')
        return redirect(url_for('all_trainees'))
    return render_template('edit-student.html', trainee_to_edit=trainee_to_edit)

@app.route('/delete-trainee')
@login_is_required
def delete_trainee():

    trainee_to_delete = Trainee.query.get(request.args.get('trainee_id'))
    print(trainee_to_delete)
    db.session.delete(trainee_to_delete)
    db.session.commit()
    flash('Trainee Deleted Successfully', 'success')
    return redirect(url_for('all_trainees'))

@app.route("/about-trainee")
@login_is_required
def about_trainee():

    return render_template('about-student.html')

@app.route('/all-courses')
@login_is_required
def all_courses():

    courses = Course.query.all()
    return render_template('all-courses.html', courses=courses)

@app.route('/add-course', methods=['GET', 'POST'])
@login_is_required
def add_course():

    facilitators = Facilitator.query.all()
    if request.method == 'POST':
        image_file = request.files['image']
        image_file_name = image_file.filename
        if os.path.exists(os.path.join(app.config['UPLOAD_FOLDER'], image_file.filename)):
            image_file_name = f"{uuid.uuid4()}-{image_file.filename}"
            image_file.save(os.path.join(app.config['UPLOAD_FOLDER'], image_file_name))
        else:
            image_file.save(os.path.join(app.config['UPLOAD_FOLDER'], image_file_name))
        new_course = Course(course_name=request.form.get('course_name'),
                            course_code=request.form.get('course_code'),
                            course_details=request.form.get('course_details'),
                            course_duration=request.form.get('course_duration'),
                            course_price=request.form.get('course_price'),
                            facilitator_name=request.form.get('facilitator'),
                            image_name=image_file_name,
                            students_enrolled=0)
        db.session.add(new_course)
        db.session.commit()
        flash("Course Added Successfully", "success")
        return redirect(url_for('all_courses'))
    return render_template('add-courses.html', facilitators=facilitators)

@app.route('/edit-course', methods=['GET', 'POST'])
@login_is_required
def edit_course():

    facilitators = Facilitator.query.all()
    course_to_edit = Course.query.get(request.args.get('course_id'))
    if request.method == 'POST':
        course_to_edit.course_name = request.form.get('course_name')
        course_to_edit.course_code = request.form.get('course_code')
        course_to_edit.course_details = request.form.get('course_details')
        course_to_edit.course_duration = request.form.get('course_duration')
        course_to_edit.course_price = request.form.get('course_price')
        course_to_edit.facilitator_name = request.form.get('facilitator')
        flash('Course Edited Successfully', 'success')
        return redirect(url_for('all_courses'))
    return render_template('edit-courses.html', course_to_edit=course_to_edit, facilitators=facilitators)

@app.route('/about-course')
@login_is_required
def about_course():

    course_to_display = Course.query.get(request.args.get('course_id'))
    return render_template('about-courses.html', course_to_display=course_to_display)

@app.route('/inventory')
@login_is_required
def inventory():

    inventory_items = InventoryItem.query.all()
    return render_template('all-library.html', inventory_items=inventory_items)

@app.route('/add-to-inventory', methods=['GET', 'POST'])
@login_is_required
def add_to_inventory():

    courses = Course.query.all()
    departments = Department.query.all()
    if request.method == 'POST':
        date = to_date_obj(request.form.get('purchase_date'))

        new_item = InventoryItem(item_name=request.form.get('item_name'),
                                 price=request.form.get('item_price'),
                                 department_for=request.form.get('department_for'),
                                 course_for=request.form.get('course_for'),
                                 purchase_date=date,
                                 status=request.form.get('item_status'),
                                 item_details=request.form.get('item_details')
                                 )
        db.session.add(new_item)
        db.session.commit()
        flash('New Item Added To Inventory', 'success')
        return redirect(url_for('inventory'))
    return render_template('add-library.html', departments=departments, courses=courses)

@app.route('/edit-inventory-item', methods=['GET', 'POST'])
@login_is_required
def edit_inventory_item():

    courses = Course.query.all()
    departments = Department.query.all()
    item_to_edit = InventoryItem.query.get(request.args.get('item_id'))
    if request.method == 'POST':
        date = to_date_obj(request.form.get('purchase_date'))

        item_to_edit.item_name = request.form.get('item_name')
        item_to_edit.price = request.form.get('item_price')
        item_to_edit.department_for = request.form.get('department_for')
        item_to_edit.course_for = request.form.get('course_for')
        item_to_edit.purchase_date = date
        item_to_edit.status = request.form.get('item_status')
        item_to_edit.item_details = request.form.get('item_details')
        db.session.commit()
        flash('Item Edited Successfully', 'success')
        return redirect(url_for('inventory'))
    return render_template('edit-library.html', item_to_edit=item_to_edit, departments=departments, courses=courses)

@app.route('/delete-inventory-item')
@login_is_required
def delete_inventory_item():

    item_to_delete = InventoryItem.query.get(request.args.get('item_id'))
    db.session.delete(item_to_delete)
    db.session.commit()
    flash("Item Deleted Successfully", "success")
    return redirect(url_for('inventory'))

@app.route('/departments')
@login_is_required
def departments():

    all_departments = Department.query.all()
    return render_template('all-departments.html', all_departments=all_departments)

@app.route('/add-department', methods=['GET', 'POST'])
@login_is_required
def add_department():

    if request.method == 'POST':
        new_department = Department(department_name=request.form.get('department_name'),
                                    department_head=request.form.get('department_head'),
                                    mobile_number=request.form.get('mobile_number'),
                                    email=request.form.get('email')
                                    )
        db.session.add(new_department)
        db.session.commit()
        flash("New Department Added", "success")
        return redirect(url_for('departments'))
    return render_template('add-departments.html')

@app.route('/edit-department', methods=['GET', 'POST'])
@login_is_required
def edit_department():

    department_to_edit = Department.query.get(request.args.get('department_id'))
    if request.method == 'POST':
        department_to_edit.department_name = request.form.get('department_name')
        department_to_edit.department_head = request.form.get('department_head')
        department_to_edit.mobile_number = request.form.get('mobile_number')
        department_to_edit.email = request.form.get('email')
        db.session.commit()
        flash('Department Edited Successfully', 'success')
        return redirect(url_for('departments'))
    return render_template('edit-departments.html', department_to_edit=department_to_edit)

@app.route('/delete-department')
@login_is_required
def delete_department():

    department_to_delete = Department.query.get(request.args.get('department_id'))
    db.session.delete(department_to_delete)
    db.session.commit()
    flash('Department Deleted', 'success')
    return redirect(url_for('departments'))

@app.route('/staff')
@login_is_required
def staff():

    all_staff = Staff.query.all()
    return render_template('all-staff.html', all_staff=all_staff)

@app.route('/add-staff', methods=['GET', 'POST'])
@login_is_required
def add_staff():

    departments = Department.query.all()
    if request.method == 'POST':
        date = to_date_obj(request.form.get('joining_date'))

        new_staff = Staff(first_name=request.form.get('first_name'),
                          last_name=request.form.get('last_name'),
                          email=request.form.get('email'),
                          joining_date=date,
                          mobile_number=request.form.get('mobile_number'),
                          gender=request.form.get('gender'),
                          designation=request.form.get('designation'),
                          department=request.form.get('department'),
                          address=request.form.get('address')
                          )
        db.session.add(new_staff)
        db.session.commit()
        flash('Staff Added Successfully', 'success')
        return redirect(url_for('staff'))
    return render_template('add-staff.html', departments=departments)

@app.route('/edit-staff', methods=['GET', 'POST'])
@login_is_required
def edit_staff():

    departments = Department.query.all()
    staff_to_edit = Staff.query.get(request.args.get('staff_id'))
    if request.method == 'POST':
        date = to_date_obj(request.form.get('joining_date'))

        staff_to_edit.first_name = request.form.get('first_name')
        staff_to_edit.last_name = request.form.get('last_name')
        staff_to_edit.email = request.form.get('email')
        staff_to_edit.joining_date = date
        staff_to_edit.mobile_number = request.form.get('mobile_number')
        staff_to_edit.gender = request.form.get('gender')
        staff_to_edit.designation = request.form.get('designation')
        staff_to_edit.department = request.form.get('department')
        staff_to_edit.address = request.form.get('address')
        db.session.commit()
        flash('Staff Edited Successfully', 'success')
        return redirect(url_for('staff'))
    return render_template('edit-staff.html', staff_to_edit=staff_to_edit, departments=departments)

@app.route('/delete-staff')
@login_is_required
def delete_staff():

    staff_to_delete = Staff.query.get(request.args.get('staff_id'))
    db.session.delete(staff_to_delete)
    db.session.commit()
    flash('Staff Deleted Successfully', 'success')
    return redirect(url_for('staff'))

@app.route('/staff-profile')
@login_is_required
def staff_profile():

    return render_template('staff-profile.html')

@app.route('/fees-collection')
@login_is_required
def fees_collection():

    all_fees = Fee.query.all()
    return render_template('fees-collection.html', all_fees=all_fees)

@app.route('/add-fees', methods=['GET', 'POST'])
@login_is_required
def add_fees():

    trainees = Trainee.query.all()
    departments = Department.query.all()
    courses = Course.query.all()
    if request.method == 'POST':
        date = to_date_obj(request.form.get('payment_date'))

        new_fee = Fee(trainee_name=request.form.get('trainee_name'),
                      trainee_id=request.form['selected_trainee_id'],
                      department=request.form.get('department'),
                      course=request.form.get('course'),
                      amount=request.form.get('amount'),
                      payment_date=date,
                      payment_type=request.form.get('payment_type'),
                      payment_status=request.form.get('payment_status')
                      )
        db.session.add(new_fee)
        db.session.commit()
        flash('New Fee Added', 'success')
        return redirect(url_for('fees_collection'))
    return render_template('add-fees.html', trainees=trainees, departments=departments, courses=courses)

@app.route('/fees-receipt')
@login_is_required
def fees_receipt():

    fee = Fee.query.get(request.args.get('fee_id'))
    trainee = Trainee.query.get(fee.trainee_id)
    current_date = datetime.now().strftime("%d/%m/%Y")

    return render_template('fees-receipt.html', fee=fee, current_date=current_date, trainee=trainee)

@app.route('/edit-fee', methods=['GET', 'POST'])
@login_is_required
def edit_fee():

    trainees = Trainee.query.all()
    departments = Department.query.all()
    courses = Course.query.all()
    fee_to_edit = Fee.query.get(request.args.get('fee_id'))
    if request.method == 'POST':
        date = to_date_obj(request.form.get('payment_date'))

        fee_to_edit.trainee_name = request.form.get('trainee_name')
        fee_to_edit.department = request.form.get('department')
        fee_to_edit.course = request.form.get('course')
        fee_to_edit.amount = request.form.get('amount')
        fee_to_edit.payment_date = date
        fee_to_edit.payment_type = request.form.get('payment_type')
        fee_to_edit.payment_status = request.form.get('payment_status')
        db.session.commit()
        flash('Fee Updated Succussfully', 'success')
        trainee = Trainee.query.get(fee_to_edit.trainee_id)
        return redirect(url_for('fees_collection'))
    return render_template('edit-fees.html', fee_to_edit=fee_to_edit, trainees=trainees, departments=departments, courses=courses)

@app.route('/error-404')
def error_404():
    return render_template('page-error-404.html')

@app.route('/event-management')
@login_is_required
def event_management():

    return render_template('event-management.html')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)