import datetime
from decimal import Decimal

import pony.db
from pony.db import Database
from pony.orm import *
from pony.sqltranslator import select, exists

class Student(Entity):
    _table_ = "Students"
    zach = PrimaryKey(int)
    name = Required(unicode, column="fio")
    group = Required("Group")
    stipendy = Required(Decimal, 10, 2, default=0)
    marks = Set("Mark")

class Group(Entity):
    _table_ = "Groups"
    number = PrimaryKey(str)
    kaf = Required(int)
    students = Set("Student")
    subjects = Set("Subject")

class Subject(Entity):
    _table_ = "Subjects"
    name = PrimaryKey(unicode)
    groups = Set("Group")
    marks = Set("Mark")

class Mark(Entity):
    _table_ = "Exams"
    student = Required(Student, column="student")
    subject = Required(Subject, column="subject")
    value = Required(int)
    date = Required(datetime.date)
    PrimaryKey(student, subject)

db = Database('sqlite', 'C:\\Data\\Docs\\Dev\\GAE\\alexander-kozlovsky\\pony\\examples\\orm\\students01\\students.db3')
pony.db.debug = False
generate_mapping(db, check_tables=True)
pony.db.debug = True

##g1 = Group.create(number='4142', kaf=44)
##g2 = Group.create(number='3137', kaf=33)
##s1 = Student.create(zach=123, name='John', group=g1)
##s2 = Student.create(zach=124, name='Mike', group=g1)
##s3 = Student.create(zach=125, name='Frank', group=g1)
##subj1 = Subject.create('Physics')
##subj2 = Subject.create('Math')
##subj3 = Subject.create('Chemistry')
##m1 = Mark.create(student=s1, subject=subj1, value=4)
##m2 = Mark.create(student=s2, subject=subj1, value=5)
##m3 = Mark.create(student=s1, subject=subj2, value=3)

trans = get_trans()

