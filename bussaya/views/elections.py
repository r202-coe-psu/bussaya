from flask import Blueprint, render_template, redirect, url_for
from flask_login import login_required

from .. import forms
from .. import models


module = Blueprint('elections', __name__, url_prefix='/elections')
subviews = []


@module.route('/', methods=['GET', 'POST'])
@login_required
# @acl.allows.requires(acl.is_admin)
def index():
    elections = models.Election.objects
    return render_template('/elections/index.html',
                           elections=elections)


@module.route('/<election_id>/edit', methods=['GET', 'POST'])
@login_required
# @acl.allows.requires(acl.is_admin)
def edit(election_id):
    election = models.Election.objects.get(id=election_id)
    form = forms.elections.ElectionForm(obj=election)

    if not form.validate_on_submit():
        print('errors', form.errors, form.data)
        return render_template('/elections/edit.html',
                               form=form,
                               election=election)

    election.started_date = form.started_date.data
    election.ended_date = form.ended_date.data
    election.save()

    return redirect(url_for('elections.index'))
