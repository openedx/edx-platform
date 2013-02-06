from optparse import make_option

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand, CommandError

from student.models import TestCenterUser, TestCenterUserForm


class Command(BaseCommand):
    option_list = BaseCommand.option_list + (
        # demographics:
        make_option(
            '--first_name',
            action='store',
            dest='first_name',
        ),
        make_option(
            '--middle_name',
            action='store',
            dest='middle_name',
        ),
        make_option(
            '--last_name',
            action='store',
            dest='last_name',
        ),
        make_option(
            '--suffix',
            action='store',
            dest='suffix',
        ),
        make_option(
            '--salutation',
            action='store',
            dest='salutation',
        ),
        make_option(
            '--address_1',
            action='store',
            dest='address_1',
        ),
        make_option(
            '--address_2',
            action='store',
            dest='address_2',
        ),
        make_option(
            '--address_3',
            action='store',
            dest='address_3',
        ),
        make_option(
            '--city',
            action='store',
            dest='city',
        ),
        make_option(
            '--state',
            action='store',
            dest='state',
            help='Two letter code (e.g. MA)'
        ),
        make_option(
            '--postal_code',
            action='store',
            dest='postal_code',
        ),
        make_option(
            '--country',
            action='store',
            dest='country',
            help='Three letter country code (ISO 3166-1 alpha-3), like USA'
        ),
        make_option(
            '--phone',
            action='store',
            dest='phone',
            help='Pretty free-form (parens, spaces, dashes), but no country code'
        ),
        make_option(
            '--extension',
            action='store',
            dest='extension',
        ),
        make_option(
            '--phone_country_code',
            action='store',
            dest='phone_country_code',
            help='Phone country code, just "1" for the USA'
        ),
        make_option(
            '--fax',
            action='store',
            dest='fax',
            help='Pretty free-form (parens, spaces, dashes), but no country code'
        ),
        make_option(
            '--fax_country_code',
            action='store',
            dest='fax_country_code',
            help='Fax country code, just "1" for the USA'
        ),
        make_option(
            '--company_name',
            action='store',
            dest='company_name',
        ),
        # internal values:
        make_option(
            '--client_candidate_id',
            action='store',
            dest='client_candidate_id',
            help='ID we assign a user to identify them to Pearson'
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
    )
    args = "<student_username>"
    help = "Create or modify a TestCenterUser entry for a given Student"

    @staticmethod
    def is_valid_option(option_name):
        base_options = set(option.dest for option in BaseCommand.option_list)
        return option_name not in base_options


    def handle(self, *args, **options):
        username = args[0]
        print username

        our_options = dict((k, v) for k, v in options.items()
                           if Command.is_valid_option(k) and v is not None)
        student = User.objects.get(username=username)
        try:
            testcenter_user = TestCenterUser.objects.get(user=student)
            needs_updating = testcenter_user.needs_update(our_options)
        except TestCenterUser.DoesNotExist:
            # do additional initialization here:
            testcenter_user = TestCenterUser.create(student)
            needs_updating = True

        if needs_updating:
            # the registration form normally populates the data dict with
            # all values from the testcenter_user.  But here we only want to
            # specify those values that change, so update the dict with existing
            # values.
            form_options = dict(our_options)
            for propname in TestCenterUser.user_provided_fields():
                if propname not in form_options:
                    form_options[propname] = testcenter_user.__getattribute__(propname)
            form = TestCenterUserForm(instance=testcenter_user, data=form_options)
            if form.is_valid():
                form.update_and_save()
            else:
                errorlist = []
                if (len(form.errors) > 0):
                    errorlist.append("Field Form errors encountered:")
                    for fielderror in form.errors:
                        errorlist.append("Field Form Error:  {}".format(fielderror))
                if (len(form.non_field_errors()) > 0):
                    errorlist.append("Non-field Form errors encountered:")
                    for nonfielderror in form.non_field_errors:
                        errorlist.append("Non-field Form Error:  {}".format(nonfielderror))
                raise CommandError("\n".join(errorlist))
        else:
            print "No changes necessary to make to existing user's demographics."

        # override internal values:
        change_internal = False
        testcenter_user = TestCenterUser.objects.get(user=student)
        for internal_field in ['upload_error_message', 'upload_status', 'client_candidate_id']:
            if internal_field in our_options:
                testcenter_user.__setattr__(internal_field, our_options[internal_field])
                change_internal = True

        if change_internal:
            testcenter_user.save()
            print "Updated  confirmation information in existing user's demographics."
        else:
            print "No changes necessary to make to confirmation information in existing user's demographics."
