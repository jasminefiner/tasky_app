from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, DateField, SelectField
from wtforms.validators import DataRequired, Email

class NewTaskForm(FlaskForm):
    body = StringField('New Task', validators=[DataRequired()])
    due = DateField('Due', format='%d/%m/%Y')
    project_id = SelectField('Project', coerce=int)
    submit = SubmitField('Add Task')

class NewProjectForm(FlaskForm):
    name = StringField('New Project', validators=[DataRequired()])
    submit = SubmitField('Add')
