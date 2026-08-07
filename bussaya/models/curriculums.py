import mongoengine as me
import datetime


class Curriculum(me.Document):
    meta = {"collection": "curriculums"}

    name = me.StringField(required=True, max_length=255)
    name_th = me.StringField(max_length=255, default="")
    code = me.StringField(max_length=100)

    status = me.StringField(required=True, default="active")

    creator = me.ReferenceField("User", dbref=True)
    last_updated_by = me.ReferenceField("User", dbref=True)

    created_date = me.DateTimeField(required=True, default=datetime.datetime.now)
    updated_date = me.DateTimeField(required=True, default=datetime.datetime.now)

    def get_plos(self):
        return PLO.objects(curriculum=self, status="active").order_by("order")

    def get_clos(self):
        return CLO.objects(curriculum=self, status="active").order_by("order")


class PLO(me.Document):
    meta = {"collection": "plos"}

    curriculum = me.ReferenceField("Curriculum", dbref=True, required=True)

    code = me.StringField(required=True, max_length=50)
    description = me.StringField(required=True)
    description_th = me.StringField(default="")
    order = me.IntField(default=0)

    status = me.StringField(required=True, default="active")

    created_date = me.DateTimeField(required=True, default=datetime.datetime.now)
    updated_date = me.DateTimeField(required=True, default=datetime.datetime.now)

    def get_label(self):
        curriculum_code = self.curriculum.code if self.curriculum else ""
        return f"[{curriculum_code}] {self.code} - {self.description}"


class CLO(me.Document):
    meta = {"collection": "clos"}

    curriculum = me.ReferenceField("Curriculum", dbref=True, required=True)
    plos = me.ListField(me.ReferenceField("PLO", dbref=True))

    code = me.StringField(required=True, max_length=50)
    description = me.StringField(required=True)
    description_th = me.StringField(default="")
    order = me.IntField(default=0)

    status = me.StringField(required=True, default="active")

    created_date = me.DateTimeField(required=True, default=datetime.datetime.now)
    updated_date = me.DateTimeField(required=True, default=datetime.datetime.now)

    # flask_mongoengine's model_form looks up "{field_name}_label_modifier" on the
    # model to label options of a ListField(ReferenceField(...)) - field_args
    # label_modifier is ignored for that field type.
    plos_label_modifier = staticmethod(lambda plo: plo.get_label())

    def get_label(self):
        curriculum_code = self.curriculum.code if self.curriculum else ""
        return f"[{curriculum_code}] {self.code} - {self.description}"
