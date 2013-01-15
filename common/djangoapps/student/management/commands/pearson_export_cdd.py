import csv
from collections import OrderedDict
from datetime import datetime
from os.path import isdir
from optparse import make_option

from django.core.management.base import BaseCommand

from student.models import TestCenterUser

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
        ("LastUpdate", "user_updated_at"), # in UTC, so same as what we store
    ])

    option_list = BaseCommand.option_list + (
        make_option(
            '--dump_all',
            action='store_true',
            dest='dump_all',
        ),
    )
    
    args = '<output_file_or_dir>'
    help = """
    Export user demographic information from TestCenterUser model into a tab delimited
    text file with a format that Pearson expects.
    """
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
            destfile = os.path.join(dest, uploaded_at.strftime("cdd-%Y%m%d-%H%M%S.dat"))
        else:
            destfile = dest
        
        # strings must be in latin-1 format.  CSV parser will
        # otherwise convert unicode objects to ascii.
        def ensure_encoding(value):
            if isinstance(value, unicode):
                return value.encode('iso-8859-1')
            else:
                return value
            
        dump_all = kwargs['dump_all']

        with open(destfile, "wb") as outfile:
            writer = csv.DictWriter(outfile,
                                    Command.CSV_TO_MODEL_FIELDS,
                                    delimiter="\t",
                                    quoting=csv.QUOTE_MINIMAL,
                                    extrasaction='ignore')
            writer.writeheader()
            for tcu in TestCenterUser.objects.order_by('id'):
                if dump_all or tcu.needs_uploading:
                    record = dict((csv_field, ensure_encoding(getattr(tcu, model_field)))
                                  for csv_field, model_field
                                  in Command.CSV_TO_MODEL_FIELDS.items())
                    record["LastUpdate"] = record["LastUpdate"].strftime("%Y/%m/%d %H:%M:%S")
                    writer.writerow(record)
                    tcu.uploaded_at = uploaded_at
                    tcu.save()


        
