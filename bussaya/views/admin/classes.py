from flask import (Blueprint,
                   render_template,
                   url_for,
                   redirect
                   )
from flask_login import current_user, login_required

from bussaya import models
from bussaya import forms

module = Blueprint('admin.classes',
                   __name__,
                   url_prefix='/classes',
                   )


@module.route('/')
@login_required
def index():
    classes = models.Class.objects()
    return render_template('/admin/classes/index.html',
                           classes=classes)


@module.route('/create', methods=['GET', 'POST'])
@login_required
def create():
    form = forms.classes.ClassForm()
    if not form.validate_on_submit():
        return render_template('/admin/classes/create-edit.html',
                               form=form
                               )

    class_ = models.Class()
    form.populate_obj(class_)
    class_.owner = current_user._get_current_object()
    class_.save()

    return redirect(url_for('admin.classes.view', class_id=class_.id))


@module.route('/<class_id>')
@login_required
def view(class_id):
    class_ = models.Class.objects.get(id=class_id)
    return render_template('/admin/classes/view.html',
                           class_=class_)

