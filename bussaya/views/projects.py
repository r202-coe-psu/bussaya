from flask import Blueprint, render_template, redirect, url_for, send_file, Response, request
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


def populate_obj(form, project):
    form.populate_obj(project)
    project.class_ = models.Class.objects.get(id=form.class_.data)
    project.advisor = models.User.objects.get(id=form.advisor.data)
    project.committees = [models.User.objects.get(id=uid) for uid in form.committees.data]
    if project.advisor in project.committees:
        project.committees.remove(project.advisor)
    project.creator = current_user._get_current_object()
    project.students = [current_user._get_current_object()]
    if form.contributors.data and len(form.contributors.data) > 0:
        contributor = models.User.objects.get(id=form.contributors.data)
        if contributor not in project.students:
            project.students.append(contributor)


def get_project_form(project=None):
    form = forms.projects.ProjectForm()

    if project:
        form = forms.projects.ProjectForm(obj=project)

    lecturers = models.User.objects(roles='lecturer').order_by('first_name')
    lec_choices = [(str(l.id), f'{l.first_name} {l.last_name}') for l in lecturers]
    form.advisor.choices = lec_choices
    form.committees.choices = lec_choices
    form.public.choices = [(d, d.title()) for d in form.public.choices]

    classes = models.Class.objects().order_by('-id')
    form.class_.choices = [(str(c.id), c.name) for c in classes]

    student_ids = []
    for c in classes:
        student_ids.extend(c.student_ids)

    form.contributors.choices = form.contributors.choices + [
            (str(s.id), f'{s.first_name} {s.last_name}')
            for s in models.User.objects(username__in=student_ids)]

    if project and request.method == 'GET':
        form.advisor.data = str(project.advisor.id)
        form.committees.data = [str(c.id) for c in project.committees]
        form.class_.data = str(project.class_.id)
        contributors = project.students
        contributors.remove(current_user._get_current_object())
        if len(contributors) > 0:
            form.contributors.data = str(contributors[0].id)

    return form


@module.route('/create', methods=['GET', 'POST'])
@login_required
def create():
    form = get_project_form()
    if not form.validate_on_submit():
        return render_template('/projects/create-edit.html',
                               form=form)

    project = models.Project()
    populate_obj(form, project)
    project.save()

    return redirect(url_for('dashboard.index'))


@module.route('/<project_id>/edit', methods=['GET', 'POST'])
@login_required
def edit(project_id):
    project = models.Project.objects.get(id=project_id)
    form = get_project_form(project)

    if not form.validate_on_submit():
        return render_template('/projects/create-edit.html',
                               form=form)

    populate_obj(form, project)
    project.save()

    return redirect(url_for('dashboard.index'))


def get_resource(data, type, project_id):
    resource = models.ProjectResource()
    resource.type = type
    resource.link = url_for(
            'projects.download',
            project_id=project_id,
            resource_id=resource.id,
            filename=data.filename)
    resource.data.put(data,
                      filename=data.filename,
                      content_type=data.content_type)

    return resource


@module.route('/<project_id>/upload', methods=['GET', 'POST'])
@login_required
def upload(project_id):
    project = models.Project.objects.get(id=project_id)
    if current_user._get_current_object() not in project.students:
        response = Response()
        response.status_code = 403
        return response

    form = forms.projects.ProjectResourceUploadForm()
    if not form.validate_on_submit():
        return render_template('/projects/upload.html',
                               form=form,
                               project=project)

    files = [form.report.data,
             form.presentation.data,
             form.similarity.data,
             form.poster.data,
             form.other.data]
    types = ['report', 'presentation', 'similarity', 'poster', 'other']

    for f, t in zip(files, types):
        if not f:
            continue
        resource = get_resource(f, t, project_id)
        project.resources.append(resource)

    files = [form.video.data,
             form.git.data
             ]
    types = ['video', 'git']
    for f, t in zip(files, types):
        if not f:
            continue
        resource = models.ProjectResource(
                type=t,
                link=f)
        project.resources.append(resource)
    project.save()

    return redirect(url_for('dashboard.index'))


@module.route('/<project_id>/approve')
@login_required
def approve(project_id):
    project = models.Project.objects.get(id=project_id)
    user = current_user._get_current_object()
    if user not in project.committees and user != project.advisor:
        response = Response()
        response.status_code = 403
        return response

    for approval in project.approvals:
        if approval.committee == user:
            return redirect(url_for('dashboard.index'))

    approval = models.ProjectApproval(
            committee=user,
            type='approve'
            )
    project.approvals.append(approval)
    project.save()

    return redirect(url_for('dashboard.index'))


@module.route('/<project_id>/resources/<resource_id>/<filename>')
def download(project_id, resource_id, filename):
    project = models.Project.objects.get(id=project_id)
    response = Response()
    response.status_code = 404

    if not project:
        return response

    resources = reversed(project.resources)
    resource = None
    for r in resources:
        if str(r.id) == resource_id and r.data.filename == filename:
            resource = r
            break

    if not current_user.is_authenticated:
        if resource.type not in project.public:
            return response

    if resource:
        response = send_file(
            resource.data,
            attachment_filename=resource.data.filename,
            # as_attachment=True,
            mimetype=resource.data.content_type)

    return response


@module.route('/<project_id>')
@login_required
def view(project_id):
    return 'wait for implementation'
