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


db = SQLAlchemy()


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


class Event(db.Model):
    __tablename__ = 'events'
    id = db.Column(db.Integer, primary_key=True)
    event_name = db.Column(db.String(250))
    event_date = db.Column(db.Date)