import csv
from collections import OrderedDict
from datetime import datetime

from django.core.management.base import BaseCommand, CommandError

from student.models import TestCenterUser

class Command(BaseCommand):
    CSV_TO_MODEL_FIELDS = OrderedDict([
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

    args = '<output_file>'
    help = """
    Export user information from TestCenterUser model into a tab delimited
    text file with a format that Pearson expects.
    """
    def handle(self, *args, **kwargs):
        if len(args) < 1:
            print Command.help
            return


        with open(args[0], "wb") as outfile:
            writer = csv.DictWriter(outfile,
                                    Command.CSV_TO_MODEL_FIELDS,
                                    delimiter="\t",
                                    quoting=csv.QUOTE_MINIMAL,
                                    extrasaction='ignore')
            writer.writeheader()
            for tcu in TestCenterUser.objects.order_by('id'):
                record = dict((csv_field, getattr(tcu, model_field))
                              for csv_field, model_field
                              in Command.CSV_TO_MODEL_FIELDS.items())
                record["LastUpdate"] = record["LastUpdate"].strftime("%Y/%m/%d %H:%M:%S")
                writer.writerow(record)

