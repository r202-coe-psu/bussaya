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
            name='Computer Engineering Project 2018-2019',
            description='Computer Engineering Project 2018-2019',
            code='CoE-2019',
            tags=['CoE', 'Project', '2019'],
            owner=user
            )

    class_.save()

if not class_:
    print('Cannot Save Class')
    sys.exit(1)


import csv

with open('grid-export.csv') as csv_file:
    csv_reader = csv.reader(csv_file)
    for row in csv_reader:
        print(row[2], row[3])
        name = row[2]
        student_id = row[3]

        project = models.Project.objects(name=name).first()
        if project:
            if student_id not in project.student_ids:
                project.student_ids.append(student_id)
        else:
            project = models.Project(name=name,
                                     class_=class_,
                                     student_ids=[student_id])
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
