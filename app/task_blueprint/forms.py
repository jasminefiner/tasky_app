from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, DateField
from wtforms.validators import DataRequired, Email

class NewTaskForm(FlaskForm):
    body = StringField('New Task', validators=[DataRequired()])
    due = DateField('Due', format='%d/%m/%Y')
    submit = SubmitField('Add Task')
