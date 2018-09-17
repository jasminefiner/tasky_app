from flask import render_template, redirect, url_for, request, flash
from flask_login import login_required, current_user
from datetime import datetime, date, timedelta
from . import task
from .forms import NewTaskForm, NewProjectForm
from .. import db
from ..models import User, Task, Project

@task.route('/', methods=['GET', 'POST'])
@task.route('/edit/<int:task_id>', methods=['GET', 'POST'])
@task.route('/project/<int:project_id>', methods=['GET', 'POST'])
@task.route('/status/<status>', methods=['GET', 'POST'])
@login_required
def home(task_id=None, project_id=None, status=None):
    taskform = NewTaskForm()
    taskform.project_id.choices = [(p.id, p.name) for p in current_user.projects]
    projectform = NewProjectForm()
    if task_id is not None:
        task = Task.query.filter_by(id=task_id).first()
        if taskform.validate_on_submit():
            project = Project.query.filter_by(id=taskform.project_id.data).first()
            task.body = taskform.body.data
            task.project = project
            task.due = taskform.due.data
            db.session.add(task)
            db.session.commit()
            flash('Your task has been updated', 'success')
            return redirect(url_for('task.home', project_id=project_id))
        taskform.body.data = task.body
        taskform.due.data = task.due

    if taskform.validate_on_submit():
        project = Project.query.filter_by(id=taskform.project_id.data).first()
        new_task = Task(body=taskform.body.data, due=taskform.due.data, project=project, author=current_user._get_current_object())
        db.session.add(new_task)
        db.session.commit()
        flash('Your task has been added!', 'success')
        return redirect(url_for('task.home', project_id=project_id))
    if projectform.validate_on_submit():
        new_project = Project(name=projectform.name.data, author=current_user._get_current_object())
        db.session.add(new_project)
        db.session.commit()
        flash('Your project has been created!', 'success')
        return redirect(url_for('task.home'))

    projects = current_user.projects
    if project_id is not None:
        project = Project.query.filter_by(id=project_id).first()
        tasks = project.tasks
    elif status == 'today':
        tasks = Task.query.filter_by(author=current_user).filter(Task.due >= date.today()).filter(Task.due < date.today() + timedelta(days=1))
    elif status == 'overdue':
        tasks = Task.query.filter_by(author=current_user).filter(Task.due < date.today())
    else:
        tasks = current_user.tasks
    return render_template('tasks/home.html', taskform=taskform, projectform=projectform, user=current_user, tasks=tasks, projects=projects)

@task.route('/delete/task/<int:task_id>')
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

@task.route('/delete/project/<int:project_id>')
@login_required
def delete_project(project_id):
    project = Project.query.filter_by(id=project_id).first()
    if project is not None:
        project.before_delete()
        db.session.delete(project)
        db.session.commit()
        flash('You have deleted your project. All tasks associated with that project have been moved to your inbox.', 'warning')
    return redirect(url_for('task.home'))
