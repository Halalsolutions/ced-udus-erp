from flask import request, url_for, redirect, flash
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
from helpers import to_date_obj


# Create New User
def create_new_user(request_form):
    new_user = User(first_name=request_form.get('first_name'),
                    last_name=request_form.get('last_name'),
                    email=request_form.get('email'),
                    password=request_form.get('password'),
                    avatar_location='../static/images/profile-photo.png')

    return new_user


def login_to_dashboard(request_form):
    email = request_form.get('email')
    password = request_form.get('password')
    user = User.query.filter_by(email=email).first()
    if user is not None:
        if password == user.password:
            login_user(user)
            flash('Login Successful', 'success')
            return redirect(url_for('home', _external=True))
        else:
            flash('Invalid Password', 'error')
            return redirect(url_for('login'))
    else:
        flash('User not Found', 'error')
        return redirect(url_for('login'))


def create_facilitator(request_form):
    date = to_date_obj(request_form.get('joining_date'))
    new_facilitator = Facilitator(
        first_name=request_form.get('first_name'),
        last_name=request_form.get('last_name'),
        email=request_form.get('email'),
        joining_date=date,
        mobile_number=request_form.get('mobile_number'),
        gender=request_form.get('gender'),
        department=request_form.get('department')
    )
    db.session.add(new_facilitator)
    db.session.commit()
    flash("Facilitator Added Successfully", "success")


def facilitator_edit(facilitator, request_form):
    date = to_date_obj(request_form.get('joining_date'))

    facilitator.first_name = request_form.get('first_name')
    facilitator.last_name = request_form.get('last_name')
    facilitator.email = request_form.get('email')
    facilitator.joining_date = date
    facilitator.mobile_number = request_form.get('mobile_number')
    facilitator.gender = request_form.get('gender')

    facilitator.department = request_form.get('department')
    db.session.commit()
    flash("Facilitator Edited Successfully", "success")


def delete_a_facilitator(request_args):
    facilitator_to_delete = Facilitator.query.get(request_args.get('facilitator_id'))
    db.session.delete(facilitator_to_delete)
    db.session.commit()
    flash('Facilitator Deleted Successfully', 'success')


def add_a_trainee(request_form):
    course_to_increment = Course.query.filter_by(course_name=request_form.get('course')).first()

    date = to_date_obj(request_form.get('registration_date'))

    print(course_to_increment)
    print(request_form.get('course'))
    new_trainee = Trainee(first_name=request_form.get('first_name'),
                          last_name=request_form.get('last_name'),
                          email=request_form.get('email'),
                          registration_date=date,
                          department=request_form.get('department'),
                          course=request_form.get('course'),
                          gender=request_form.get('gender'),
                          mobile_number=request_form.get('mobile_number'),
                          address=request_form.get('address')
                          )
    course_to_increment.students_enrolled += 1
    db.session.add(new_trainee)
    db.session.commit()
    flash('Trainee Added Successfully', 'success')
    
    
def edit_a_trainee(trainee_to_edit, request_form):
    date = to_date_obj(request_form.get('registration_date'))

    trainee_to_edit.first_name = request_form.get('first_name')
    trainee_to_edit.last_name = request_form.get('last_name')
    trainee_to_edit.email = request_form.get('email')
    trainee_to_edit.registration_date = date
    trainee_to_edit.department = request_form.get('department')
    trainee_to_edit.course = request_form.get('course')
    trainee_to_edit.gender = request_form.get('gender')
    trainee_to_edit.mobile_number = request_form.get('mobile_number')
    trainee_to_edit.address = request_form.get('address')
    db.session.commit()
    flash('Trainee Edited Successfully', 'success')


def delete_a_trainee(request_args):
    trainee_to_delete = Trainee.query.get(request_args.get('trainee_id'))
    db.session.delete(trainee_to_delete)
    db.session.commit()
    flash('Trainee Deleted Successfully', 'success')
    

def add_a_course(config_folder, request_files, request_form):
    image_file = request_files['image']
    image_file_name = image_file.filename
    if os.path.exists(os.path.join(config_folder, image_file.filename)):
        image_file_name = f"{uuid.uuid4()}-{image_file.filename}"
        image_file.save(os.path.join(config_folder, image_file_name))
    else:
        image_file.save(os.path.join(config_folder, image_file_name))
    new_course = Course(course_name=request_form.get('course_name'),
                        course_code=request_form.get('course_code'),
                        course_details=request_form.get('course_details'),
                        course_duration=request_form.get('course_duration'),
                        course_price=request_form.get('course_price'),
                        facilitator_name=request_form.get('facilitator'),
                        image_name=image_file_name,
                        students_enrolled=0)
    db.session.add(new_course)
    db.session.commit()
    flash("Course Added Successfully", "success")
    
    
def edit_a_course(request_args, request_form):
    course_to_edit = Course.query.get(request.args.get('course_id'))
    course_to_edit.course_name = request_form.get('course_name')
    course_to_edit.course_code = request_form.get('course_code')
    course_to_edit.course_details = request_form.get('course_details')
    course_to_edit.course_duration = request_form.get('course_duration')
    course_to_edit.course_price = request_form.get('course_price')
    course_to_edit.facilitator_name = request_form.get('facilitator')
    db.session.commit()
    flash('Course Edited Successfully', 'success')
    
    
def add_an_inventory(request_form):
    date = to_date_obj(request_form.get('purchase_date'))

    new_item = InventoryItem(item_name=request_form.get('item_name'),
                             price=request_form.get('item_price'),
                             department_for=request_form.get('department_for'),
                             course_for=request_form.get('course_for'),
                             purchase_date=date,
                             status=request_form.get('item_status'),
                             item_details=request_form.get('item_details')
                             )
    db.session.add(new_item)
    db.session.commit()
    flash('New Item Added To Inventory', 'success')
    
    
def edit_an_inventory(item_to_edit, request_form):
    date = to_date_obj(request_form.get('purchase_date'))

    item_to_edit.item_name = request_form.get('item_name')
    item_to_edit.price = request_form.get('item_price')
    item_to_edit.department_for = request_form.get('department_for')
    item_to_edit.course_for = request_form.get('course_for')
    item_to_edit.purchase_date = date
    item_to_edit.status = request_form.get('item_status')
    item_to_edit.item_details = request_form.get('item_details')
    db.session.commit()
    flash('Item Edited Successfully', 'success')


def delete_an_inventory(request_args):
    item_to_delete = InventoryItem.query.get(request_args.get('item_id'))
    db.session.delete(item_to_delete)
    db.session.commit()
    flash("Item Deleted Successfully", "success")
    
    
def add_a_department(request_form):
    new_department = Department(department_name=request_form.get('department_name'),
                                department_head=request_form.get('department_head'),
                                mobile_number=request_form.get('mobile_number'),
                                email=request_form.get('email')
                                )
    db.session.add(new_department)
    db.session.commit()
    flash("New Department Added", "success")


def edit_a_department(department_to_edit, request_form):
    department_to_edit.department_name = request_form.get('department_name')
    department_to_edit.department_head = request_form.get('department_head')
    department_to_edit.mobile_number = request_form.get('mobile_number')
    department_to_edit.email = request_form.get('email')
    db.session.commit()
    flash('Department Edited Successfully', 'success')


def delete_a_department(request_args):
    department_to_delete = Department.query.get(request_args.get('department_id'))
    db.session.delete(department_to_delete)
    db.session.commit()
    flash('Department Deleted', 'success')
    
    
def add_a_staff(request_form):
    date = to_date_obj(request_form.get('joining_date'))

    new_staff = Staff(first_name=request_form.get('first_name'),
                      last_name=request_form.get('last_name'),
                      email=request_form.get('email'),
                      joining_date=date,
                      mobile_number=request_form.get('mobile_number'),
                      gender=request_form.get('gender'),
                      designation=request_form.get('designation'),
                      department=request_form.get('department'),
                      address=request_form.get('address')
                      )
    db.session.add(new_staff)
    db.session.commit()
    flash('Staff Added Successfully', 'success')
    
    
def edit_a_staff(staff_to_edit, request_form):
    date = to_date_obj(request_form.get('joining_date'))
    staff_to_edit.first_name = request_form.get('first_name')
    staff_to_edit.last_name = request_form.get('last_name')
    staff_to_edit.email = request_form.get('email')
    staff_to_edit.joining_date = date
    staff_to_edit.mobile_number = request_form.get('mobile_number')
    staff_to_edit.gender = request_form.get('gender')
    staff_to_edit.designation = request_form.get('designation')
    staff_to_edit.department = request_form.get('department')
    staff_to_edit.address = request_form.get('address')
    db.session.commit()
    flash('Staff Edited Successfully', 'success')


def delete_a_staff(request_args):
    staff_to_delete = Staff.query.get(request_args.get('staff_id'))
    db.session.delete(staff_to_delete)
    db.session.commit()
    flash('Staff Deleted Successfully', 'success')
    
    
    
def add_a_fee(request_form):
    date = to_date_obj(request_form.get('payment_date'))
    new_fee = Fee(trainee_name=request_form.get('trainee_name'),
                  trainee_id=request_form['selected_trainee_id'],
                  department=request_form.get('department'),
                  course=request_form.get('course'),
                  amount=request_form.get('amount'),
                  payment_date=date,
                  payment_type=request_form.get('payment_type'),
                  payment_status=request_form.get('payment_status')
                  )
    db.session.add(new_fee)
    db.session.commit()
    flash('New Fee Added', 'success')
    
    
def edit_a_fee(fee_to_edit, request_form):
    date = to_date_obj(request_form.get('payment_date'))

    fee_to_edit.trainee_name = request_form.get('trainee_name')
    fee_to_edit.department = request_form.get('department')
    fee_to_edit.course = request_form.get('course')
    fee_to_edit.amount = request_form.get('amount')
    fee_to_edit.payment_date = date
    fee_to_edit.payment_type = request_form.get('payment_type')
    fee_to_edit.payment_status = request_form.get('payment_status')
    db.session.commit()
    flash('Fee Updated Succussfully', 'success')
    
    
def add_an_event(request_form):
    date = to_date_obj(request_form.get('event_date'))
    new_event = Event(event_name=request_form.get('event_name'),
                      event_date=date)
    db.session.add(new_event)
    db.session.commit()
    flash('Event Added', 'success')
    