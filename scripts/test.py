import sys
import datetime 

from bussaya import models

settings = dict(MONGODB_DB='bussayadb')

models.init_mongoengine(settings)

user = models.User.objects.first()

print('Got user', user.first_name, user.last_name)

if not user:
    print('Required atless one user')
    sys.exit(1)

models.Class.drop_collection()
models.Election.drop_collection()
models.Project.drop_collection()
models.Voting.drop_collection()

class_ = models.Class.objects.first()

if not class_:
    class_ = models.Class(
            name='Computer Engineering Project',
            description='Computer Engineering Project 2018-2019',
            code='CoE-2019',
            tags=['CoE', 'Project', '2019'],
            owner=user
            )

    class_.save()

if not class_:
    print('Cannot Save Class')
    sys.exit(1)


project_infos = [
        ('5910110298', 'Project Title 1'),
        ('5910110044', 'Project Title 2'),
        ('5910110377', 'Project Title 3'),
        ('5910110095', 'Project Title 4'),
        ('5910110422', 'Project Title 5'),
        ('5910130041', 'Project Title 6'),
        ]

for sid, name in project_infos:
    project = models.Project.objects(name=name).first()
    if project:
        continue

    project = models.Project(name=name,
                             class_=class_,
                             student_ids=[sid])
    project.save()

now = datetime.datetime.now()

election = models.Election.objects(started_date__lte=now,
                                   ended_date__gte=now,
                                   class_=class_)
if not election:

    election = models.Election(
            owner=user,
            class_=class_,
            started_date=now,
            ended_date=now + datetime.timedelta(minutes=60)
            )

    election.save()
