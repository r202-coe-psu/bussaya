import datetime
import mongoengine as me


class Organization(me.Document):
    name = me.StringField(required=True, unique=True, max_length=255)
    website = me.StringField(max_length=512)
    remark = me.StringField()

    status = me.StringField(required=True, default="disactive")

    creator = me.ReferenceField("User", dbref=True)
    last_updated_by = me.ReferenceField("User", dbref=True)
    created_date = me.DateTimeField(required=True, default=datetime.datetime.now)
    updated_date = me.DateTimeField(required=True, default=datetime.datetime.now)

    meta = {"collection": "organizations"}


class Mentor(me.Document):
    name = me.StringField(required=True, unique=True)
    position = me.StringField()
    email = me.StringField()
    phone = me.StringField()

    remark = me.StringField()
    organization = me.ReferenceField("Organization", dbref=True)

    status = me.StringField(required=True, default="disactive")

    creator = me.ReferenceField("User", dbref=True)
    created_date = me.DateTimeField(required=True, default=datetime.datetime.now)
    updated_date = me.DateTimeField(required=True, default=datetime.datetime.now)

    meta = {"collection": "mentors"}
