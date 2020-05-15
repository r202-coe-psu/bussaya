import datetime
from flask import (Blueprint,
                   render_template,
                   url_for,
                   redirect,
                   current_app,
                   send_file,
                   abort)
from flask_login import login_user, logout_user, login_required, current_user
from flask_principal import Identity, identity_changed

from .. import models
from .. import oauth2
from .. import forms

module = Blueprint('accounts', __name__)


def get_user_and_remember():
    client = oauth2.oauth2_client
    result = client.principal.get('me')
    print('got: ', result.json())
    data = result.json()

    user = models.User.objects(
            username=data.get('username', '')).first()
    if not user:
        user = models.User(id=data.get('id'),
                           first_name=data.get('first_name'),
                           last_name=data.get('last_name'),
                           email=data.get('email'),
                           username=data.get('username'),
                           status='active')
        roles = []
        for role in ['student', 'lecturer', 'staff']:
            if role in data.get('roles', []):
                roles.append(role)

        user.save()

    if user:
        login_user(user, remember=True)


@module.route('/login', methods=('GET', 'POST'))
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))

    return render_template('/accounts/login.html')


@module.route('/login-principal')
def login_principal():
    client = oauth2.oauth2_client
    redirect_uri = url_for('accounts.authorized_principal',
                           _external=True)
    response = client.principal.authorize_redirect(redirect_uri)

    return response


@module.route('/login-engpsu')
def login_engpsu():
    client = oauth2.oauth2_client
    redirect_uri = url_for('accounts.authorized_engpsu',
                           _external=True)
    response = client.engpsu.authorize_redirect(redirect_uri)
    return response


@module.route('/authorized-principal')
def authorized_principal():
    client = oauth2.oauth2_client

    try:
        token = client.principal.authorize_access_token()
    except Exception as e:
        print(e)
        return redirect(url_for('accounts.login'))

    get_user_and_remember()
    oauth2token = models.OAuth2Token(
            name=client.principal.name,
            user=current_user._get_current_object(),
            access_token=token.get('access_token'),
            token_type=token.get('token_type'),
            refresh_token=token.get('refresh_token', None),
            expires=datetime.datetime.utcfromtimestamp(
                token.get('expires_at'))
            )
    oauth2token.save()

    return redirect(url_for('dashboard.index'))


@module.route('/authorized-engpsu')
def authorized_engpsu():
    client = oauth2.oauth2_client
    try:
        token = client.engpsu.authorize_access_token()
    except Exception as e:
        print(e)
        return redirect(url_for('accounts.login'))

    userinfo_response = client.engpsu.get('userinfo')
    userinfo = userinfo_response.json()

    user = models.User.objects(username=userinfo.get('username')).first()

    if not user:
        user = models.User(
                username=userinfo.get('username'),
                email=userinfo.get('email'),
                first_name=userinfo.get('first_name'),
                last_name=userinfo.get('last_name'),
                status='active')
        user.resources[client.engpsu.name] = userinfo
        # if 'staff_id' in userinfo.keys():
        #     user.roles.append('staff')
        # elif 'student_id' in userinfo.keys():
        #     user.roles.append('student')
        if userinfo['username'].isdigit():
            user.roles.append('student')
        elif 'COE_LECTURERS' in current_app.config \
                and userinfo['username'] in current_app.config['COE_LECTURERS']:
            user.roles.append('lecturer')
            user.roles.append('CoE-lecturer')
        else:
            user.roles.append('staff')

        user.save()

        # if userinfo['username'].isdigit():
        #     project = models.Project.objects(
        #             student_ids=userinfo['username']).first()

        #     if project and user not in project.owners:
        #         project.owners.append(user)
        #         project.save()
    else:
        user.resources[client.engpsu.name] = userinfo
        user.save()

    login_user(user)
    identity_changed.send(
            current_app._get_current_object(),
            identity=Identity(str(user.id)))

    oauth2token = models.OAuth2Token(
            name=client.engpsu.name,
            user=user,
            access_token=token.get('access_token'),
            token_type=token.get('token_type'),
            refresh_token=token.get('refresh_token', None),
            expires=datetime.datetime.utcfromtimestamp(
                token.get('expires_in'))
            )
    oauth2token.save()

    return redirect(url_for('dashboard.index'))


@module.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('site.index'))


@module.route('/accounts/<user_id>')
def profile(user_id):
    user = models.User.objects.get(id=user_id)
    return render_template('/accounts/index.html',
                           user=user)


@module.route('/accounts')
@login_required
def index():
    return render_template('/accounts/index.html', user=current_user)


@module.route('/accounts/edit-profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    form = forms.accounts.ProfileForm(
            obj=current_user,
            )
    if not form.validate_on_submit():
        return render_template('/accounts/edit-profile.html', form=form)

    user = current_user._get_current_object()
    form.populate_obj(user)

    if form.pic.data:
        if user.picture:
            user.picture.replace(form.pic.data,
                                 filename=form.pic.data.filename,
                                 content_type=form.pic.data.content_type)
        else:
            user.picture.put(form.pic.data,
                             filename=form.pic.data.filename,
                             content_type=form.pic.data.content_type)

    user.save()

    return redirect(url_for('accounts.index'))


@module.route('/accounts/<user_id>/picture/<filename>', methods=['GET', 'POST'])
def picture(user_id, filename):
    user = models.User.objects.get(id=user_id)

    if not user or not user.picture or user.picture.filename != filename:
        return abort(403)

    response = send_file(
            user.picture,
            attachment_filename=user.picture.filename,
            mimetype=user.picture.content_type
            )
    return response
