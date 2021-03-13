from flask import Blueprint, render_template, redirect, url_for, request, current_app
from flask_login import login_required, current_user

import qrcode
import io
import base64
from PIL import Image
import pathlib
import math

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

@module.route('/create', methods=['GET', 'POST'])
@login_required
def create():
    form = forms.elections.ElectionForm()
    classes = models.Class.objects()
    form.class_.choices = [ (str(c.id), c.name) for c in classes ]

    if not form.validate_on_submit():
        return render_template('/elections/create-edit.html',
                               form=form,
                               )
    election = models.Election()
    form.populate_obj(election)
    election.class_ = models.Class.objects.get(id=form.class_.data)
    election.owner = current_user._get_current_object()
    election.save()

    return redirect(url_for('elections.index'))


@module.route('/<election_id>/edit', methods=['GET', 'POST'])
@login_required
def edit(election_id):
    election = models.Election.objects.get(id=election_id)
    form = forms.elections.ElectionForm(obj=election)


    classes = models.Class.objects()
    form.class_.choices = [ (str(c.id), c.name) for c in classes ]

    if not form.validate_on_submit():
        print('errors', form.errors, form.data)
        return render_template('/elections/create-edit.html',
                               form=form,
                               election=election)

    election.started_date = form.started_date.data
    election.ended_date = form.ended_date.data
    election.save()

    return redirect(url_for('elections.index'))



@module.route('/<election_id>/generate_qrcode')
@login_required
def generate_qrcode(election_id):
    election = models.Election.objects.get(id=election_id)
    
    projects = models.Project.objects(class_=election.class_)

    coe_logo_path = pathlib.Path(current_app.root_path) / 'static' / 'images' / 'coe-logo.png'
    
    coe_logo = Image.open(coe_logo_path)
    coe_logo_width, coe_logo_height = coe_logo.size
   
    reduce_factor = 0.05
    coe_logo_width = int(coe_logo_width*reduce_factor)
    coe_logo_height = int(coe_logo_height*reduce_factor)
    coe_logo = coe_logo.resize((coe_logo_width, coe_logo_height))

    coe_logo_white = Image.new("RGBA", coe_logo.size, "WHITE")
    coe_logo_white.paste(coe_logo, (0, 0), coe_logo)

    qr_images = dict()
    for project in projects:
        url = request.url_root.replace(
                request.script_root, '')[:-1] + url_for(
                        'votings.vote',
                        election_id=election.id,
                        project_id=project.id
                        )

        qr = qrcode.QRCode(
            version=7,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=2,
        )
        qr.add_data(url)
        qr.make(fit=True)

        img = qr.make_image().convert('RGB')

        pos = ((img.size[0] - coe_logo.size[0]) // 2, (img.size[1] - coe_logo.size[1]) // 2)
        img.paste(coe_logo_white, pos)

        img_io = io.BytesIO()
        img.save(img_io, 'JPEG', quality=100)
        encoded = base64.b64encode(img_io.getvalue()).decode("ascii")

        qr_images[project.id] = dict(
                image=encoded,
                url=url
            )

    is_print = request.args.get('print', False)
    if is_print:
        return render_template(
                '/elections/generate-qrcode-print.html',
                election=election,
                class_=election.class_,
                projects=projects,
                qr_images=qr_images,
                pages=range(math.floor(len(projects) / 4)+1),
                )

    return render_template('/elections/generate-qrcode.html',
                           election=election,
                           class_=election.class_,
                           projects=projects,
                           qr_images=qr_images,
                           )

