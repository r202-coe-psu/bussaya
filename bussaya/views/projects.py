from flask import Blueprint, render_template, redirect, url_for
from flask_login import login_required, current_user

from .. import forms
from .. import models


module = Blueprint('projects', __name__, url_prefix='/projects')


@module.route('/')
@login_required
def index():
    elections = models.Election.objects
    return render_template('/elections/index.html',
                           elections=elections)


@module.route('/create', methods=['GET', 'POST'])
@login_required
def create():
    form = forms.projects.ProjectForm()

    lecturers = models.User.objects(roles='lecturer').order_by('first_name')
    lec_choices = [(str(l.id), f'{l.first_name} {l.last_name}') for l in lecturers ]
    form.advisor.choices = lec_choices
    form.committees.choices = lec_choices
    form.public.choices = [(d, d.title()) for d in form.public.choices]

    classes = models.Class.objects().order_by('-id')
    form.class_.choices = [(str(c.id), c.name) for c in classes]
    
    student_ids = []
    for c in classes:
        student_ids.extend(c.student_ids)

    form.contributors.choices = form.contributors.choices + [(str(s.id), f'{s.first_name} {s.last_name}') 
             for s in models.User.objects(username__in=student_ids)]

    if not form.validate_on_submit():
        return render_template('/projects/create-edit.html',
                               form=form)
    
    project = models.Project()
    form.populate_obj(project)
    project.class_ = models.Class.objects.get(id=form.class_.data)
    project.advisor = models.User.objects.get(id=form.advisor.data)
    project.committees = [models.User.objects.get(id=uid) for uid in form.committees.data]
    project.creator = current_user._get_current_object()
    project.students = [current_user._get_current_object()]
    if form.contributors.data and len(form.contributors.data) > 0:
        project.students.append(models.User.objects.get(id=form.contributors.data))
    project.save()

    return redirect(url_for('dashboard.index'))

@module.route('/<project_id>/edit', methods=['GET', 'POST'])
@login_required
def edit(project_id):
    project = models.Project.objects.get(id=project_id)
    form = forms.projects.ProjectForm(obj=project)

    lecturers = models.User.objects(roles='lecturer').order_by('first_name')
    lec_choices = [(str(l.id), f'{l.first_name} {l.last_name}') for l in lecturers ]
    form.advisor.choices = lec_choices
    form.committees.choices = lec_choices
    form.public.choices = [(d, d.title()) for d in form.public.choices]

    classes = models.Class.objects().order_by('-id')
    form.class_.choices = [(str(c.id), c.name) for c in classes]
    
    student_ids = []
    for c in classes:
        student_ids.extend(c.student_ids)

    form.contributors.choices = form.contributors.choices + [(str(s.id), f'{s.first_name} {s.last_name}') 
             for s in models.User.objects(username__in=student_ids)]

    if not form.validate_on_submit():
        form.advisor.data = str(project.advisor.id)
        form.committees.data = [str(c.id) for c in project.committees]
        form.class_.data = str(project.class_.id)
        contributors = project.students
        contributors.remove(current_user._get_current_object())
        if len(contributors) > 0:
            form.contributors.data = str(contributors[0].id)
        return render_template('/projects/create-edit.html',
                               form=form)
    
    form.populate_obj(project)
    project.class_ = models.Class.objects.get(id=form.class_.data)
    project.advisor = models.User.objects.get(id=form.advisor.data)
    project.committees = [models.User.objects.get(id=uid) for uid in form.committees.data]
    project.creator = current_user._get_current_object()
    project.students = [current_user._get_current_object()]
    if form.contributors.data and len(form.contributors.data) > 0:
        project.students.append(models.User.objects.get(id=form.contributors.data))
    project.save()

    return redirect(url_for('dashboard.index'))



@module.route('/<project_id>/upload', methods=['GET', 'POST'])
@login_required
def upload(project_id):
    
    return redirect(url_for('dashboard.index'))

@module.route('/<project_id>')
@login_required
def view(project_id):
    pass
