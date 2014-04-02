# -*- coding: utf-8 -*-
"""
Command to generate statistics.
"""
import csv
import sys

from django.core.management.base import BaseCommand
from optparse import make_option

from xmodule.modulestore.django import modulestore
from courseware.access import _has_staff_access_to_course_id
from django.contrib.auth.models import User

from instructor.offline_gradecalc import student_grades
from courseware import grades
import logging



class Command(BaseCommand):
    """
    Command to manually regenerate statistics.
    """

    help = ("Usage: statistic --dry-run \n"
            "")

    option_list = BaseCommand.option_list + (
        make_option('-n', '--dry-run',
                    action='store_true', dest='dry_run', default=False,
                    help="Do everything except writing files. "),
    )

    def handle(self, *args, **options):

        dry_run = options['dry_run']

        if len(args) == 0:
            print "Init OK"
        else:
            print self.help
            return

        
        if dry_run:
            print "Doing a dry run."
        fullstat()

       


coursemap = {
    u'CPM/Astr012013/2013-2014' : u'Астрономия',
    u'CPM/Bi012013/2013-2014' : u'Биология',
    #u'CPM/EDX_01/2013-2014' : u'',
    u'CPM/Eco012013/2013-2014' : u'Экология',
    u'CPM/Econom012013/2013-2014' : u'Экономика',
    #u'CPM/Econom022013/2013-2014' : u'',
    u'CPM/En012013/2013-2014' : u'Английский язык',
    #u'CPM/En02/2013' : u'',
    u'CPM/French012013/2013-2014' : u'Французский язык',
    u'CPM/Geo02_2013/2013-2014' : u'География',
    u'CPM/Hist012013/2013-2014' : u'История',
    #u'CPM/Hist022013/2013-2014' : u'',
    u'CPM/Lit01/2013-2014' : u'Литература',
    #u'CPM/Lit022013/2013-2014' : u'',
    u'CPM/MXK012013/2013-2014' : u'Искусство (МХК)',
    u'CPM/Ma01_2013/2013-2014' : u'Математика',
    #u'CPM/Mus012013/2013-2014' : u'',
    u'CPM/Nem012013/2013-2014' : u'Немецкий язык',
    u'CPM/OBG012013/2013-2014' : u'ОБЖ',
    #u'CPM/PID01/2013-2014' : u'',
    u'CPM/Pravo012013/2013-2014' : u'Право',
    #u'CPM/Pravo022013/2013-2014' : u'',
    #u'CPM/Psi012013/2013-2014' : u'',
    u'CPM/Russian001/2013' : u'Русский язык',
    u'CPM/Techno012013/2013-2014' : u'Технология',
    u'CPM/chemistry01/2013' : u'Химия',
    #u'CPM/french01/2013' : u'Французский язык',
    u'CPM/gym01/2013' : u'Физическая культура',
    u'CPM/inf07/2013-2014' : u'Информатика',
    u'CPM/physics01/2013' : u'Физика',
    u'CPM/socio01/2013' : u'Обществознание',
    u'CPM/volimp01/2013' : u'Вводный курс',
}

def gendata(request):
    data = {}
    for course in modulestore().get_courses():
        data[course.id] = {}
        print("Loading info for course {courseid}".format(courseid = course.id))
        
        enrolled_students = User.objects.filter(
            courseenrollment__course_id=course.id,
        ).prefetch_related("groups").order_by('username')
        enrolled_students = [st for st in enrolled_students if not _has_staff_access_to_course_id(st, course.id)]
        
        if len(enrolled_students) <= 0:
            continue

        #Category weights
        gradeset = student_grades(enrolled_students[0], request, course, keep_raw_scores=False, use_offline=False)
        category_weights = {}

        for section in gradeset['grade_breakdown']:
            category_weights[section['category']] = section['weight']    

        for user in enrolled_students:
            data[course.id][user.email] = {}

            #User
            data[course.id][user.email]["user"] = user

            #Raw statistic by problems
            gradeset = student_grades(user, request, course, keep_raw_scores=True, use_offline=False)
            statprob = [(getattr(score, 'earned', '') or score[0]) for score in gradeset['raw_scores']]
            
            #By subsection
            statsec = []
            complition = 0
            complition_cnt = 0
                
            try:
                courseware_summary = grades.progress_summary(user, request, course);

                for chapter in courseware_summary:
                    total = 0
                    flag = False
                    for section in chapter['sections']:
                        if not section['graded'] or len(section['format']) < 1:
                            continue
                        flag = True
                        statsec += [((section['section_total'].earned / section['section_total'].possible) if section['section_total'].possible else 0)]
                        total += ((section['section_total'].earned / section['section_total'].possible) if section['section_total'].possible else 0) * category_weights.get(section['format'], 0.0)
                    statsec += [total]
                    if flag:
                        complition += total
                        complition_cnt += 1
            except:
                pass

            if complition_cnt == 0:
                complition = 0
            else:
                complition = complition / complition_cnt
            if complition > 0.7:
                data[course.id][user.email]["0.7"] =  True
            else:
                data[course.id][user.email]["0.7"] =  False
            
            if complition > 0.99:
                data[course.id][user.email]["1.0"] =  True
            else:
                data[course.id][user.email]["1.0"] =  False

            data[course.id][user.email]["prob_info"] = statprob
            data[course.id][user.email]["sec_info"] = statsec
        print("Loading info for course {courseid} - COMPLETE - total {users}".format(courseid = course.id, users = len (data[course.id]) ))
    return data


def fullstat(request = None):

    request = DummyRequest()
    

    header = [u'ФИО', u'ФИО (измененное)', u'логин школы', u'email', u'email (измененное)', u'курс', u'зарег. в пакет рег.', u"дата рег. на курс", u'2/3', u'100%', u'Задачи/Задания(Модули)']
    assignments = []
    datatablefull = {'header': header, 'assignments': assignments, 'students': []}
    datafull = []

    for course in modulestore().get_courses():
        
        datarow = [u'-', u'-', u'-', u'-', u'-', course.id, u'-', u'-', u'-']
        
        assignments = []
        
        enrolled_students = User.objects.filter(
            courseenrollment__course_id=course.id,
        ).prefetch_related("groups").order_by('username')
        enrolled_students = [st for st in enrolled_students if not _has_staff_access_to_course_id(st, course.id)]
        
        if len(enrolled_students) <= 0:
            continue
            
        gradeset = student_grades(enrolled_students[0], request, course, keep_raw_scores=True, use_offline=False)
        courseware_summary = grades.progress_summary(enrolled_students[0], request, course);

        if courseware_summary is None:
            continue

        assignments += [score.section for score in gradeset['raw_scores']]
        
        for chapter in courseware_summary:
            for section in chapter['sections']:
                if not section['graded'] or len(section['format']) < 1:
                    continue
                assignments += [section['format']]
            assignments += [chapter['display_name']]

        datarow += assignments
        datafull.append(datarow)
        

    edxdata = gendata(request)


    print("Dumping fullstat")

    f = open("/opt/data.csv")

    if f is None:
        return False;

    ff = UnicodeDictReader(f, delimiter=';', quoting=csv.QUOTE_NONE)

    usermap = {}
    idx = 0
    for row in ff:
        idx += 1
        usermap.setdefault(row['email'],[]).append(row)

    
    for course in modulestore().get_courses():
        enrolled_students = User.objects.filter(
            courseenrollment__course_id=course.id,
            courseenrollment__is_active=1,
        ).prefetch_related("groups").order_by('username')
        enrolled_students = [st for st in enrolled_students if not _has_staff_access_to_course_id(st, course.id)]

        idx = 0
        for user in enrolled_students:
            try:
                idx += 1

                datarow = []

                found = False
                rows = []
                try:
                    for elem in user.profile.get_meta().get('old_emails',[])[::-1]:
                        if usermap[elem[0]]:
                            found = True
                            rows = usermap[elem[0]]
                            break
                    if not found and usermap[user.email]:
                        found = True
                        rows = usermap[user.email]
                except:
                    pass

                off_reg = False
                try:
                    for row in rows:
                        found = False
                        for course_id, course_name in coursemap.iteritems():
                            if course_name in row['subject']:
                                found = True
                                off_reg = True
                                break
                        if found:
                            break
                except:
                    pass
                

                #User
                name = ''
                try:
                    name = rows[0]['second-name'] + ' ' + rows[0]['first-name'] + ' ' + rows[0]['patronymic']
                except:
                    pass
                datarow += [name]
                if user.profile.name != name:
                    datarow += [user.profile.name]
                else:
                    datarow += [u'']
                try:
                    datarow += [rows[0]['login']]
                except:
                    datarow += ['']
                email = ''
                try:
                    datarow += [rows[0]['email']]
                    email = rows[0]['email']
                except:
                    datarow += ['']
                if user.email != email:
                    datarow += [user.email]
                else:
                    datarow += [u'']
                #Course
                datarow += [course.display_name]

                if off_reg:
                    datarow += [u'Да']
                else:
                    datarow += [u'Нет']

                try:
                    courseenrollment = user.courseenrollment_set.filter(course_id = course.id)[0]
                    datarow += [courseenrollment.created.strftime('%d/%m/%Y')]
                except:
                    continue
                
                #Raw statistic by problems
                statprob = edxdata[course.id][user.email]["prob_info"]
                
                #By subsection
                statsec = edxdata[course.id][user.email]["sec_info"]

                if edxdata[course.id][user.email]["0.7"]:
                    datarow += [u"Да"]
                else:
                    datarow += [u"Нет"]
                
                if edxdata[course.id][user.email]["1.0"]:
                    datarow += [u"Да"]
                else:
                    datarow += [u"Нет"]

                if len(statsec) > 0 and len(statprob) > 0:
                    datarow += statprob
                    datarow += statsec
                
                datafull.append(datarow)
            except:
                logging.exception("Something awful happened in fullstat!")
                pass
    datatablefull['data'] = datafull
    return_csv('full_stat.csv',datatablefull, open("/var/www/edx/fullstat.csv", "wb"))


    for course in modulestore().get_courses():

        print("Dumping course {courseid}".format(courseid = course.id))


        assignments = []
        
        enrolled_students = User.objects.filter(
            courseenrollment__course_id=course.id,
        ).prefetch_related("groups").order_by('username')
        enrolled_students = [st for st in enrolled_students if not _has_staff_access_to_course_id(st, course.id)]
        
        if len(enrolled_students) <= 0:
            continue

        gradeset = student_grades(enrolled_students[0], request, course, keep_raw_scores=True, use_offline=False)
        courseware_summary = grades.progress_summary(enrolled_students[0], request, course);

        if courseware_summary is None:
            print "No courseware_summary"
            continue

        assignments += [score.section for score in gradeset['raw_scores']]
        
        for chapter in courseware_summary:
            for section in chapter['sections']:
                if not section['graded'] or len(section['format']) < 1:
                    continue
                assignments += [section['format']]
            assignments += [chapter['display_name']]

        header = [u'ФИО', u'логин школы', u'email', u"дата регистрации на курс", u'2/3', u'100%']
        header += assignments
        datatable = {'header': header, 'assignments': assignments, 'students': []}
        data = []
                
        for user in enrolled_students:
            try:
                datarow = []

                #User
                name = user.profile.name
                datarow += [name]
                datarow += [user.profile.work_login]
                datarow += [user.email]

                courseenrollment = user.courseenrollment_set.filter(course_id = course.id)[0]

                datarow += [courseenrollment.created.strftime('%d/%m/%Y')]
                
                #Raw statistic by problems
                statprob = edxdata[course.id][user.email]["prob_info"]
                
                #By subsection
                statsec = edxdata[course.id][user.email]["sec_info"]

                if edxdata[course.id][user.email]["0.7"]:
                    datarow += [u"Да"]
                else:
                    datarow += [u"Нет"]
                
                if edxdata[course.id][user.email]["1.0"]:
                    datarow += [u"Да"]
                else:
                    datarow += [u"Нет"]


                if len(statsec) > 0 and len(statprob) > 0:
                    datarow += statprob
                    datarow += statsec
                else:
                    datarow += [0] * len(assignments)
                
                data.append(datarow)
            except:
                logging.exception("Something awful happened in {course_id}!".format(course_id = course.id))
                pass
        datatable['data'] = data
        return_csv(course.id,datatable, open("/var/www/edx/" + course.id.replace('/','_') + ".xls", "wb"), encoding="cp1251", dialect="excel-tab")
        return_csv(course.id,datatable, open("/var/www/edx/" + course.id.replace('/','_') + ".csv", "wb"))

    return True


def UnicodeDictReader(utf8_data, **kwargs):
    csv_reader = csv.DictReader(utf8_data, **kwargs)
    for row in csv_reader:
        yield dict([(key, unicode(value, 'utf-8')) for key, value in row.iteritems()])  


def return_csv(func, datatable, file_pointer=None, encoding="utf-8", dialect="excel"):
    """Outputs a CSV file from the contents of a datatable."""
    if file_pointer is None:
        return None
    else:
        response = file_pointer
    writer = csv.writer(response, dialect=dialect, quotechar='"', quoting=csv.QUOTE_ALL)
    encoded_row = [unicode(s).encode(encoding) for s in datatable['header']]
    writer.writerow(encoded_row)
    for datarow in datatable['data']:
        encoded_row = [unicode(s).encode(encoding) for s in datarow]
        writer.writerow(encoded_row)
    return response


def progressbar(cnt, total):
    i = (cnt * 20) / total
    sys.stdout.write('\r')
    sys.stdout.write("[%-20s] %d%%" % ('='*i, 5*i))
    sys.stdout.flush()


class DummyRequest(object):
    """Dummy request"""

    META = {}

    def __init__(self):
        self.session = {}
        self.user = None
        self.host = None
        self.secure = True

    def get_host(self):
        """Return a default host."""
        return self.host

    def is_secure(self):
        """Always secure."""
        return self.secure
