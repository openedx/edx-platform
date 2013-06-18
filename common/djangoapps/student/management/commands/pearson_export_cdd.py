import csv
import os
from collections import OrderedDict
from datetime import datetime
from optparse import make_option

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from student.models import TestCenterUser
from pytz import UTC


class Command(BaseCommand):

    CSV_TO_MODEL_FIELDS = OrderedDict([
        # Skipping optional field CandidateID
        ("ClientCandidateID", "client_candidate_id"),
        ("FirstName", "first_name"),
        ("LastName", "last_name"),
        ("MiddleName", "middle_name"),
        ("Suffix", "suffix"),
        ("Salutation", "salutation"),
        ("Email", "email"),
        # Skipping optional fields Username and Password
        ("Address1", "address_1"),
        ("Address2", "address_2"),
        ("Address3", "address_3"),
        ("City", "city"),
        ("State", "state"),
        ("PostalCode", "postal_code"),
        ("Country", "country"),
        ("Phone", "phone"),
        ("Extension", "extension"),
        ("PhoneCountryCode", "phone_country_code"),
        ("FAX", "fax"),
        ("FAXCountryCode", "fax_country_code"),
        ("CompanyName", "company_name"),
        # Skipping optional field CustomQuestion
        ("LastUpdate", "user_updated_at"),  # in UTC, so same as what we store
    ])

    # define defaults, even thought 'store_true' shouldn't need them.
    # (call_command will set None as default value for all options that don't have one,
    # so one cannot rely on presence/absence of flags in that world.)
    option_list = BaseCommand.option_list + (
        make_option('--dest-from-settings',
                    action='store_true',
                    dest='dest-from-settings',
                    default=False,
                    help='Retrieve the destination to export to from django.'),
        make_option('--destination',
                    action='store',
                    dest='destination',
                    default=None,
                    help='Where to store the exported files')
    )

    def handle(self, **options):
        # update time should use UTC in order to be comparable to the user_updated_at
        # field
        uploaded_at = datetime.now(UTC)

        # if specified destination is an existing directory, then
        # create a filename for it automatically.  If it doesn't exist,
        # then we will create the directory.
        # Name will use timestamp -- this is UTC, so it will look funny,
        # but it should at least be consistent with the other timestamps
        # used in the system.
        if 'dest-from-settings' in options and options['dest-from-settings']:
            if 'LOCAL_EXPORT' in settings.PEARSON:
                dest = settings.PEARSON['LOCAL_EXPORT']
            else:
                raise CommandError('--dest-from-settings was enabled but the'
                                   'PEARSON[LOCAL_EXPORT] setting was not set.')
        elif 'destination' in options and options['destination']:
            dest = options['destination']
        else:
            raise CommandError('--destination or --dest-from-settings must be used')

        if not os.path.isdir(dest):
            os.makedirs(dest)

        destfile = os.path.join(dest, uploaded_at.strftime("cdd-%Y%m%d-%H%M%S.dat"))

        # strings must be in latin-1 format.  CSV parser will
        # otherwise convert unicode objects to ascii.
        def ensure_encoding(value):
            if isinstance(value, unicode):
                return value.encode('iso-8859-1')
            else:
                return value

#        dump_all = options['dump_all']

        with open(destfile, "wb") as outfile:
            writer = csv.DictWriter(outfile,
                                    Command.CSV_TO_MODEL_FIELDS,
                                    delimiter="\t",
                                    quoting=csv.QUOTE_MINIMAL,
                                    extrasaction='ignore')
            writer.writeheader()
            for tcu in TestCenterUser.objects.order_by('id'):
                if tcu.needs_uploading:  # or dump_all
                    record = dict((csv_field, ensure_encoding(getattr(tcu, model_field)))
                                  for csv_field, model_field
                                  in Command.CSV_TO_MODEL_FIELDS.items())
                    record["LastUpdate"] = record["LastUpdate"].strftime("%Y/%m/%d %H:%M:%S")
                    writer.writerow(record)
                    tcu.uploaded_at = uploaded_at
                    tcu.save()
