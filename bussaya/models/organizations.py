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

    def get_mentors(self):
        print(Mentor.objects(organization=self))
        return Mentor.objects(organization=self)


class Mentor(me.Document):
    name = me.StringField(required=True, unique=True, max_length=255)
    position = me.StringField(max_length=255)
    email = me.StringField(max_length=255)
    phone = me.StringField(max_length=255)

    remark = me.StringField()
    organization = me.ReferenceField("Organization", dbref=True)

    status = me.StringField(required=True, default="disactive")

    adder = me.ReferenceField("User", dbref=True)
    last_updated_by = me.ReferenceField("User", dbref=True)
    created_date = me.DateTimeField(required=True, default=datetime.datetime.now)
    updated_date = me.DateTimeField(required=True, default=datetime.datetime.now)

    meta = {"collection": "mentors"}

    def get_fullname(self):
        return self.get_full_name()

    def get_full_name(self):
        return self.name

    def get_picture(self):
        return None
