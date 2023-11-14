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


# covert string date to date ob
def to_date_obj(date_string):
    return datetime.strptime(date_string, "%Y-%m-%d").date()


# Calculate all fees collected
def calculate_total_amount():
    total_amount = db.session.query(db.func.sum(Fee.amount)).scalar()
    return total_amount if total_amount else 0



# claculate Students Increase Percentage
def calculate_percentage_increased(trainees):
    current_month = datetime.now().month
    last_month_trainees = Trainee.query.filter(func.extract('month', Trainee.registration_date) == current_month - 1).count()
    current_month_trainees = Trainee.query.filter(func.extract('month', Trainee.registration_date) == current_month).count()
    if last_month_trainees == 0:
        return "No Trainees Registered last month"

    percentage_increase = ((current_month_trainees - last_month_trainees) / last_month_trainees) * 100
    return f"{percentage_increase:.2f}% increase from last month"


# claculate Fees Increase Percentage
def calculate_fees_percentage_increased():
    current_month = datetime.now().month
    last_month_total = (
        Fee.query
        .with_entities(func.sum(Fee.amount))
        .filter(func.extract('month', Fee.payment_date) == current_month - 1)
        .scalar()
    )

    current_month_total = (
        Fee.query
        .with_entities(func.sum(Fee.amount))
        .filter(func.extract('month', Fee.payment_date) == current_month)
        .scalar()
    )

    if last_month_total is None:
        return "No records last month"

    percentage_increase = ((current_month_total - last_month_total) / last_month_total) * 100
    return f"{percentage_increase:.2f}% increase from last month"



# Function to convert number to month name
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
    income_data = [{'month': number_to_month_name(int(month)), 'total_income': int(total_income)} for month, total_income in income_data]
    expense_data = [{'month': number_to_month_name(int(month)), 'total_expenses': int(total_expenses)} for month, total_expenses in expense_data]

    return income_data, expense_data