from optparse import make_option

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand, CommandError

from student.models import TestCenterUser, TestCenterRegistration, TestCenterRegistrationForm, get_testcenter_registration
from student.views import course_from_id
from xmodule.course_module import CourseDescriptor

class Command(BaseCommand):
    option_list = BaseCommand.option_list + (
        # registration info:
        make_option(
            '--accommodation_request',
            action='store',
            dest='accommodation_request',
        ),        
        make_option(
            '--accommodation_code',
            action='store',
            dest='accommodation_code',
        ),        
        make_option(
            '--client_authorization_id',
            action='store',
            dest='client_authorization_id',
        ),        
        # exam info:     
        make_option(
            '--exam_series_code',
            action='store',
            dest='exam_series_code',
        ),        
        make_option(
            '--eligibility_appointment_date_first',
            action='store',
            dest='eligibility_appointment_date_first',
        ),        
        make_option(
            '--eligibility_appointment_date_last',
            action='store',
            dest='eligibility_appointment_date_last',
        ),
        # internal values:
        make_option(
            '--authorization_id',
            action='store',
            dest='authorization_id',
            help='ID we receive from Pearson for a particular authorization'
        ),   
        make_option(
            '--upload_status',
            action='store',
            dest='upload_status',
            help='status value assigned by Pearson'
        ),   
        make_option(
            '--upload_error_message',
            action='store',
            dest='upload_error_message',
            help='error message provided by Pearson on a failure.'
        ),   
        # control values:
        make_option(
            '--ignore_registration_dates',
            action='store_true',
            dest='ignore_registration_dates',
            help='find exam info for course based on exam_series_code, even if it is not active.'
        ),   
    )
    args = "<student_username course_id>"
    help = "Create a TestCenterRegistration entry for a given Student"

    @staticmethod
    def is_valid_option(option_name):
        base_options = set(option.dest for option in BaseCommand.option_list)
        return option_name not in base_options


    def handle(self, *args, **options):
        username = args[0]
        course_id = args[1]
        print username, course_id

        our_options = dict((k, v) for k, v in options.items()
                           if Command.is_valid_option(k) and v is not None)
        student = User.objects.get(username=username)
        try:
            testcenter_user = TestCenterUser.objects.get(user=student)
        except TestCenterUser.DoesNotExist:
            raise CommandError("User {%s} does not exist".format(student))
            
        # check to see if a course_id was specified, and use information from that:
        course = course_from_id(course_id)
        if course is not None:
            if 'ignore_registration_dates' in our_options:
                examlist = [exam for exam in course.test_center_exams if exam.exam_series_code == our_options.get('exam_series_code')]
                exam = examlist[0] if len(examlist) > 0 else None
            else:
                exam = course.current_test_center_exam
        else: 
            # otherwise use explicit values (so we don't have to define a course):    
            exam_name = "Dummy Placeholder Name"
            exam_info = { 'Exam_Series_Code': our_options['exam_series_code'],
                          'First_Eligible_Appointment_Date' : our_options['eligibility_appointment_date_first'],
                          'Last_Eligible_Appointment_Date' : our_options['eligibility_appointment_date_last'],
                          }
            exam = CourseDescriptor.TestCenterExam(course_id, exam_name, exam_info)

        if exam is None:
            raise CommandError("Exam for course_id {%s} does not exist".format(course_id))

        exam_code = exam.exam_series_code
            
        UPDATE_FIELDS = ( 'accommodation_request',
                          'accommodation_code',
                          'client_authorization_id',
                          'exam_series_code',
                          'eligibility_appointment_date_first',
                          'eligibility_appointment_date_last',
                          )
        
        # create and save the registration:
        needs_updating = False
        registrations = get_testcenter_registration(student, course_id, exam_code)
        if len(registrations) > 0:
            registration = registrations[0]
            for fieldname in UPDATE_FIELDS:
                if fieldname in our_options and registration.__getattribute__(fieldname) != our_options[fieldname]:
                    needs_updating = True;
        else:
            accommodation_request = our_options.get('accommodation_request','')
            registration = TestCenterRegistration.create(testcenter_user, exam, accommodation_request)
            needs_updating = True

            
        if needs_updating:
            # first update the record with the new values, if any:
            for fieldname in UPDATE_FIELDS:
                if fieldname in our_options and fieldname not in TestCenterRegistrationForm.Meta.fields: 
                    registration.__setattr__(fieldname, our_options[fieldname])
            
            # the registration form normally populates the data dict with 
            # the accommodation request (if any).  But here we want to
            # specify only those values that might change, so update the dict with existing
            # values.
            form_options = dict(our_options)
            for propname in TestCenterRegistrationForm.Meta.fields:
                if propname not in form_options: 
                    form_options[propname] = registration.__getattribute__(propname)
            form = TestCenterRegistrationForm(instance=registration, data=form_options)
            if form.is_valid():
                form.update_and_save()
                print "Updated registration information for user's registration: username \"{}\" course \"{}\", examcode \"{}\"".format(student.username, course_id, exam_code) 
            else:
                if (len(form.errors) > 0):
                    print "Field Form errors encountered:"
                for fielderror in form.errors:
                    print "Field Form Error:  %s" % fielderror
                    if (len(form.non_field_errors()) > 0):
                        print "Non-field Form errors encountered:"
                        for nonfielderror in form.non_field_errors:
                            print "Non-field Form Error:  %s" % nonfielderror
                    
        else:
            print "No changes necessary to make to existing user's registration."
            
        # override internal values:
        change_internal = False
        registration = get_testcenter_registration(student, course_id, exam_code)[0]
        for internal_field in [ 'upload_error_message', 'upload_status', 'authorization_id']:
            if internal_field in our_options:
                registration.__setattr__(internal_field, our_options[internal_field])
                change_internal = True
                
        if change_internal:
            print "Updated  confirmation information in existing user's registration."
            registration.save()
        else:
            print "No changes necessary to make to confirmation information in existing user's registration."
        
            
