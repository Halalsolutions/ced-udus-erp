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


# Functions t check current user
def check_login_status():
    if not current_user.is_authenticated:
        flash('Login To Continue')
        return render_template('page-login.html')


# Checking if current user is loggend in
def login_is_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('Login To Continue')
            return redirect(url_for('login'))

        return f(*args, **kwargs)
    return decorated_function