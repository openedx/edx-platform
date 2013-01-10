import csv
from collections import OrderedDict
from datetime import datetime
from os.path import isdir
from fs.path import pathjoin
from optparse import make_option

from django.core.management.base import BaseCommand

from student.models import TestCenterRegistration

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
        ("LastUpdate", "user_updated_at"), # in UTC, so same as what we store
    ])

    args = '<output_file_or_dir>'
    help = """
    Export user registration information from TestCenterRegistration model into a tab delimited
    text file with a format that Pearson expects.
    """

    option_list = BaseCommand.option_list + (
        make_option(
            '--dump_all',
            action='store_true',
            dest='dump_all',
        ),
        make_option(
            '--force_add',
            action='store_true',
            dest='force_add',
        ),
    )
    
    
    def handle(self, *args, **kwargs):
        if len(args) < 1:
            print Command.help
            return

        # update time should use UTC in order to be comparable to the user_updated_at 
        # field
        uploaded_at = datetime.utcnow()

        # if specified destination is an existing directory, then 
        # create a filename for it automatically.  If it doesn't exist,
        # or exists as a file, then we will just write to it.
        # Name will use timestamp -- this is UTC, so it will look funny,
        # but it should at least be consistent with the other timestamps 
        # used in the system.
        dest = args[0]
        if isdir(dest):
            destfile = pathjoin(dest, uploaded_at.strftime("ead-%Y%m%d-%H%M%S.dat"))
        else:
            destfile = dest

        dump_all = kwargs['dump_all']

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
                    if kwargs['force_add']:
                        record['AuthorizationTransactionType'] = 'Add'

                    writer.writerow(record)
                    tcr.uploaded_at = uploaded_at
                    tcr.save()


  

        