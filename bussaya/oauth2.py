from flask import g, config, session, redirect, url_for
from flask_login import current_user, login_user
from authlib.integrations.flask_client import OAuth

from . import models
import mongoengine as me

import datetime


def fetch_token(name):
    token = models.OAuth2Token.objects(
        name=name, user=current_user._get_current_object()
    ).first()
    return token.to_dict()


def update_token(name, token):
    item = models.OAuth2Token(
        name=name, user=current_user._get_current_object()
    ).first()
    item.token_type = token.get("token_type", "Bearer")
    item.access_token = token.get("access_token")
    item.refresh_token = token.get("refresh_token")
    item.expires = datetime.datetime.utcfromtimestamp(token.get("expires_at"))

    item.save()
    return item


oauth2_client = OAuth()


def create_user_google(user_info):
    user = models.User(
        username=user_info.get("email"),
        picture_url=user_info.get("picture"),
        email=user_info.get("email"),
        first_name=user_info.get("given_name"),
        last_name=user_info.get("family_name"),
        status="active",
    )
    user.save()
    return user


def create_user_line(user_info):
    name = user_info.get("name", "")
    names = ["", ""]
    if name:
        names = name.split(" ")
        if len(names) < 2:
            names.append("")

    user = models.User(
        username=user_info.get("email", name),
        subid=user_info.get("sub"),
        picture_url=user_info.get("picture"),
        email=user_info.get("email", ""),
        first_name=names[0],
        last_name=names[1],
        status="active",
    )
    user.save()
    return user


def create_user_facebook(user_info):
    user = models.User(
        username=user_info.get("email"),
        picture_url=f"http://graph.facebook.com/{user_info.get('sub')}/picture?type=large",
        email=user_info.get("email"),
        first_name=user_info.get("first_name"),
        last_name=user_info.get("last_name"),
        status="active",
    )
    user.save()
    return user


def get_user_info(remote, token):
    if remote.name == "google":
        resp = remote.get("userinfo")
        return resp.json()
    elif remote.name == "facebook":
        USERINFO_FIELDS = [
            "id",
            "name",
            "first_name",
            "middle_name",
            "last_name",
            "email",
            "website",
            "gender",
            "locale",
        ]
        USERINFO_ENDPOINT = "me?fields=" + ",".join(USERINFO_FIELDS)
        resp = remote.get(USERINFO_ENDPOINT)
        profile = resp.json()
        return profile
    elif remote.name == "line":
        id_token = token.get("id_token")
        # print("id_token", id_token)
        resp = requests.post(
            "https://api.line.me/oauth2/v2.1/verify",
            data={"id_token": str(id_token), "client_id": remote.client_id},
        )

        # resp = requests.get(
        #     "https://api.line.me/v2/profile",
        #     headers={"Authorization": f"Bearer {token.get('access_token')}"},
        # )

        userinfo = resp.json()
        return userinfo


def handle_authorized_oauth2(remote, token):
    # print(remote.name)
    # print(token)
    user_info = get_user_info(remote, token)

    user = None
    if "email" in user_info and user_info["email"]:
        user = models.User.objects(me.Q(email=user_info.get("email"))).first()
    elif "sub" in user_info:
        user = models.User.objects(subid=user_info.get("sub")).first()

    if not user:
        if remote.name == "google":
            user = create_user_google(user_info)
        elif remote.name == "facebook":
            user = create_user_facebook(user_info)
        elif remote.name == "line":
            user = create_user_line(user_info)

    login_user(user)
    user.resources[remote.name] = user_info
    user.save()

    if token:
        oauth2token = models.OAuth2Token(
            name=remote.name,
            user=user,
            access_token=token.get("access_token"),
            token_type=token.get("token_type"),
            refresh_token=token.get("refresh_token", None),
            expires=datetime.datetime.utcfromtimestamp(token.get("expires_in")),
        )
        oauth2token.save()

    next_uri = session.get("next", None)
    if next_uri:
        session.pop("next")
        return redirect(next_uri)
    return redirect(url_for("site.index"))


def handle_authorize(remote, token, user_info):

    if not user_info:
        return redirect(url_for("accounts.login"))

    user = models.User.objects(
        me.Q(username=user_info.get("name")) | me.Q(email=user_info.get("email"))
    ).first()
    if not user:
        user = models.User(
            username=user_info.get("name"),
            email=user_info.get("email"),
            first_name=user_info.get("given_name", ""),
            last_name=user_info.get("family_name", ""),
            status="active",
        )
        user.resources[remote.name] = user_info
        email = user_info.get("email")
        if email[: email.find("@")].isdigit():
            user.roles.append("student")
        user.save()

    login_user(user)

    if token:
        oauth2token = models.OAuth2Token(
            name=remote.name,
            user=user,
            access_token=token.get("access_token"),
            token_type=token.get("token_type"),
            refresh_token=token.get("refresh_token", None),
            expires=datetime.datetime.utcfromtimestamp(token.get("expires_in")),
        )
        oauth2token.save()
    next_uri = session.get("next", None)
    if next_uri:
        session.pop("next")
        return redirect(next_uri)
    return redirect(url_for("dashboard.index"))


# def create_flask_blueprint(backend, oauth, handle_authorize):
#     from flask import Blueprint, request, url_for, current_app, session
#     from authlib.flask.client import RemoteApp
#     from authlib.common.security import generate_token
#     from loginpass._core import register_to

#     remote = register_to(backend, oauth, RemoteApp)
#     nonce_key = '_{}:nonce'.format(backend.OAUTH_NAME)
#     bp = Blueprint('loginpass_' + backend.OAUTH_NAME, __name__)

#     @bp.route('/auth')
#     def auth():
#         id_token = request.args.get('id_token')
#         if request.args.get('code'):
#             token = remote.authorize_access_token(verify=False)
#             if id_token:
#                 token['id_token'] = id_token
#         elif id_token:
#             token = {'id_token': id_token}
#         elif request.args.get('oauth_verifier'):
#             # OAuth 1
#             token = remote.authorize_access_token(verify=False)
#         else:
#             # handle failed
#             return handle_authorize(remote, None, None)
#         if 'id_token' in token:
#             nonce = session[nonce_key]
#             user_info = remote.parse_openid(token, nonce)
#         else:
#             user_info = remote.profile(token=token)
#         return handle_authorize(remote, token, user_info)

#     @bp.route('/login')
#     def login():
#         redirect_uri = url_for('.auth', _external=True)
#         conf_key = '{}_AUTHORIZE_PARAMS'.format(backend.OAUTH_NAME.upper())
#         params = current_app.config.get(conf_key, {})
#         if 'oidc' in backend.OAUTH_TYPE:
#             nonce = generate_token(20)
#             session[nonce_key] = nonce
#             params['nonce'] = nonce
#         return remote.authorize_redirect(redirect_uri, **params)

#     return bp


def init_oauth(app):
    oauth2_client.init_app(app, fetch_token=fetch_token, update_token=update_token)

    # oauth2_client.register('principal')
    oauth2_client.register("engpsu")
    oauth2_client.register("google")
