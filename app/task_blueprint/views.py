from flask import render_template, redirect, url_for, request, flash
from flask_login import login_required, current_user

from . import task
from .forms import NewTaskForm
from .. import db
from ..models import User, Task

@task.route('/', methods=['GET', 'POST'])
@task.route('/edit/<int:task_id>', methods=['GET', 'POST'])
@login_required
def home(task_id=None):
    form = NewTaskForm()
    if task_id is not None:
        task = Task.query.filter_by(id=task_id).first()
        if form.validate_on_submit():
            task.body = form.body.data
            task.due = form.due.data
            db.session.add(task)
            db.session.commit()
            flash('Your task has been updated', 'success')
            return redirect(url_for('task.home'))
        form.body.data = task.body
        form.due.data = task.due

    if form.validate_on_submit():
        new_task = Task(body=form.body.data, due=form.due.data, author=current_user._get_current_object())
        db.session.add(new_task)
        db.session.commit()
        flash('Your task has been added!', 'success')
    tasks = current_user.tasks
    return render_template('tasks/home.html', form=form, user=current_user, tasks=tasks)

@task.route('/delete/<int:task_id>')
@login_required
def delete(task_id):
    task = Task.query.filter_by(id=task_id).first()
    if task is not None:
        db.session.delete(task)
        db.session.commit()
        flash('You have deleted your task', 'warning')
    return redirect(url_for('task.home'))

@task.route('/complete/<int:task_id>')
@login_required
def complete(task_id):
    task = Task.query.filter_by(id=task_id).first()
    if not task.done:
        task.done = True
        db.session.add(task)
        db.session.commit()
        flash('Well done for completing your task', 'success')
    return redirect(url_for('task.home'))
