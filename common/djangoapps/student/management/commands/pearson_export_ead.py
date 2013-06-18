import csv
import os
from collections import OrderedDict
from datetime import datetime
from optparse import make_option

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from student.models import TestCenterRegistration, ACCOMMODATION_REJECTED_CODE
from pytz import UTC


class Command(BaseCommand):

    CSV_TO_MODEL_FIELDS = OrderedDict([
        ('AuthorizationTransactionType', 'authorization_transaction_type'),
        ('AuthorizationID', 'authorization_id'),
        ('ClientAuthorizationID', 'client_authorization_id'),
        ('ClientCandidateID', 'client_candidate_id'),
        ('ExamAuthorizationCount', 'exam_authorization_count'),
        ('ExamSeriesCode', 'exam_series_code'),
        ('Accommodations', 'accommodation_code'),
        ('EligibilityApptDateFirst', 'eligibility_appointment_date_first'),
        ('EligibilityApptDateLast', 'eligibility_appointment_date_last'),
        ("LastUpdate", "user_updated_at"),  # in UTC, so same as what we store
    ])

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
                    help='Where to store the exported files'),
        make_option('--dump_all',
                    action='store_true',
                    dest='dump_all',
                    default=False,
                    ),
        make_option('--force_add',
                    action='store_true',
                    dest='force_add',
                    default=False,
                    ),
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

        destfile = os.path.join(dest, uploaded_at.strftime("ead-%Y%m%d-%H%M%S.dat"))

        dump_all = options['dump_all']

        with open(destfile, "wb") as outfile:
            writer = csv.DictWriter(outfile,
                                    Command.CSV_TO_MODEL_FIELDS,
                                    delimiter="\t",
                                    quoting=csv.QUOTE_MINIMAL,
                                    extrasaction='ignore')
            writer.writeheader()
            for tcr in TestCenterRegistration.objects.order_by('id'):
                if dump_all or tcr.needs_uploading:
                    record = dict((csv_field, getattr(tcr, model_field))
                                  for csv_field, model_field
                                  in Command.CSV_TO_MODEL_FIELDS.items())
                    record["LastUpdate"] = record["LastUpdate"].strftime("%Y/%m/%d %H:%M:%S")
                    record["EligibilityApptDateFirst"] = record["EligibilityApptDateFirst"].strftime("%Y/%m/%d")
                    record["EligibilityApptDateLast"] = record["EligibilityApptDateLast"].strftime("%Y/%m/%d")
                    if record["Accommodations"] == ACCOMMODATION_REJECTED_CODE:
                        record["Accommodations"] = ""
                    if options['force_add']:
                        record['AuthorizationTransactionType'] = 'Add'

                    writer.writerow(record)
                    tcr.uploaded_at = uploaded_at
                    tcr.save()
