from flask import Flask, request, render_template, url_for, redirect, flash, jsonify
from flask_login import LoginManager, UserMixin, login_user, login_required, current_user, logout_user
from flask_toastr import Toastr
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Column, String, LargeBinary, event, func, cast, Date
import os
import calendar
import uuid
from datetime import datetime
from functools import wraps
from models import db, User, Facilitator, Trainee, Course, InventoryItem, Staff, Department, Fee, Event
from helpers import *
from db_helpers import *
from decorators import *
from listeners import *

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
db.init_app(app)

# Setup loging manager
login_manager = LoginManager()
login_manager.init_app(app)


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


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
    fee_percentage_increase = calculate_fees_percentage_increased()

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
        new_user = create_new_user(request.form)
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
        create_facilitator(request.form)
        return redirect(url_for('all_facilitators'))
    return render_template('add-professor.html', departments=departments)


@app.route("/edit-facilitator", methods=['GET', 'POST'])
@login_is_required
def edit_facilitator():
    facilitator_to_edit = Facilitator.query.get(request.args.get('facilitator_id'))
    departments = Department.query.all()
    if request.method == 'POST':
        facilitator_edit(facilitator_to_edit, request.form)
        return redirect(url_for('all_facilitators'))
    return render_template('edit-professor.html', facilitator_to_edit=facilitator_to_edit, departments=departments)


@app.route('/delete-facilitator')
@login_is_required
def delete_facilitator():
    delete_a_facilitator(request.args)
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
        add_a_trainee(request.form)
        return redirect(url_for('all_trainees'))
    return render_template('add-student.html', courses=courses, departments=departments)


@app.route('/edit-trainee', methods=['GET', 'POST'])
@login_is_required
def edit_trainee():
    departments = Department.query.all()
    courses = Course.query.all()
    trainee_to_edit = Trainee.query.get(request.args.get('trainee_id'))
    if request.method == 'POST':
        edit_a_trainee(trainee_to_edit, request.form)
        return redirect(url_for('all_trainees'))
    return render_template('edit-student.html', trainee_to_edit=trainee_to_edit, departments=departments, courses=courses)


@app.route('/delete-trainee')
@login_is_required
def delete_trainee():
    delete_a_trainee(request.args)
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
        config_folder = app.config['UPLOAD_FOLDER']
        add_a_course(config_folder, request.files, request.form)
        return redirect(url_for('all_courses'))
    return render_template('add-courses.html', facilitators=facilitators)


@app.route('/edit-course', methods=['GET', 'POST'])
@login_is_required
def edit_course():
    facilitators = Facilitator.query.all()
    course_to_edit = Course.query.get(request.args.get('course_id'))
    if request.method == 'POST':
        edit_a_course(request.args, request.form)
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
        add_an_inventory(request.form)
        return redirect(url_for('inventory'))
    return render_template('add-library.html', departments=departments, courses=courses)


@app.route('/edit-inventory-item', methods=['GET', 'POST'])
@login_is_required
def edit_inventory_item():
    courses = Course.query.all()
    departments = Department.query.all()
    item_to_edit = InventoryItem.query.get(request.args.get('item_id'))
    if request.method == 'POST':
        edit_an_inventory(item_to_edit, request.form)
        return redirect(url_for('inventory'))
    return render_template('edit-library.html', item_to_edit=item_to_edit, departments=departments, courses=courses)


@app.route('/delete-inventory-item')
@login_is_required
def delete_inventory_item():
    delete_an_inventory(request.args)
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
        add_a_department(request.form)
        return redirect(url_for('departments'))
    return render_template('add-departments.html')


@app.route('/edit-department', methods=['GET', 'POST'])
@login_is_required
def edit_department():
    department_to_edit = Department.query.get(request.args.get('department_id'))
    if request.method == 'POST':
        edit_a_department(department_to_edit, request.form)
        return redirect(url_for('departments'))
    return render_template('edit-departments.html', department_to_edit=department_to_edit)


@app.route('/delete-department')
@login_is_required
def delete_department():
    delete_a_department(request.args)
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
        add_a_staff(request.form)
        return redirect(url_for('staff'))
    return render_template('add-staff.html', departments=departments)


@app.route('/edit-staff', methods=['GET', 'POST'])
@login_is_required
def edit_staff():
    departments = Department.query.all()
    staff_to_edit = Staff.query.get(request.args.get('staff_id'))
    if request.method == 'POST':
        edit_a_staff(staff_to_edit, request.form)
        return redirect(url_for('staff'))
    return render_template('edit-staff.html', staff_to_edit=staff_to_edit, departments=departments)


@app.route('/delete-staff')
@login_is_required
def delete_staff():
    delete_a_staff(request.args)
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
        add_a_fee(request.form)
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
        edit_a_fee(fee_to_edit, request.form)
        return redirect(url_for('fees_collection'))
    return render_template('edit-fees.html', fee_to_edit=fee_to_edit, trainees=trainees, departments=departments, courses=courses)


@app.route('/error-404')
def error_404():
    return render_template('page-error-404.html')


@app.route('/event-management', methods=['GET', 'POST'])
@login_is_required
def event_management():
    events = Event.query.all()
    if request.method == 'POST':
        add_an_event(request.form)
        return redirect(url_for('event_management'))
    return render_template('event-management.html', events=events)


@app.route('/get_events')
def get_events():
    # Query events from the database
    events = Event.query.all()

    # Convert events to FullCalendar-compatible format
    formatted_events = []
    for event in events:
        formatted_events.append({
            'id': event.id,
            'title': event.event_name,
            'start': event.event_date.strftime('%Y-%m-%d'),
            'end': event.event_date.strftime('%Y-%m-%d'),
            'description': event.event_name
        })

    return jsonify(formatted_events)


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        generate_invoice_number
    app.run(host='0.0.0.0', port=5000, debug=True)

