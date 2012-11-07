import csv
import uuid
from collections import defaultdict, OrderedDict
from datetime import datetime

from django.core.management.base import BaseCommand, CommandError

from student.models import TestCenterUser

def generate_id():
    return "{:012}".format(uuid.uuid4().int % (10**12))

class Command(BaseCommand):
    args = '<output_file>'
    help = """
    Export user information from TestCenterUser model into a tab delimited
    text file with a format that Pearson expects.
    """
    FIELDS = [
        'AuthorizationTransactionType',
        'AuthorizationID',
        'ClientAuthorizationID',
        'ClientCandidateID',
        'ExamAuthorizationCount',
        'ExamSeriesCode',
        'EligibilityApptDateFirst',
        'EligibilityApptDateLast',
        'LastUpdate',
    ]
    
    def handle(self, *args, **kwargs):
        if len(args) < 1:
            print Command.help
            return

        # self.reset_sample_data()

        with open(args[0], "wb") as outfile:
            writer = csv.DictWriter(outfile,
                                    Command.FIELDS,
                                    delimiter="\t",
                                    quoting=csv.QUOTE_MINIMAL,
                                    extrasaction='ignore')
            writer.writeheader()
            for tcu in TestCenterUser.objects.order_by('id')[:5]:
                record = defaultdict(
                    lambda: "",
                    AuthorizationTransactionType="Add",
                    ClientAuthorizationID=generate_id(),
                    ClientCandidateID=tcu.client_candidate_id,
                    ExamAuthorizationCount="1",
                    ExamSeriesCode="6002x001",
                    EligibilityApptDateFirst="2012/12/15",
                    EligibilityApptDateLast="2012/12/30",
                    LastUpdate=datetime.utcnow().strftime("%Y/%m/%d %H:%M:%S")
                )
                writer.writerow(record)














    def reset_sample_data(self):
        def make_sample(**kwargs):
            data = dict((model_field, kwargs.get(model_field, ""))
                        for model_field in Command.CSV_TO_MODEL_FIELDS.values())
            return TestCenterUser(**data)
        
        # TestCenterUser.objects.all().delete()
        
        samples = [
            make_sample(
                client_candidate_id=generate_id(),
                first_name="Jack",
                last_name="Doe",
                middle_name="C",
                address_1="11 Cambridge Center",
                address_2="Suite 101",
                city="Cambridge",
                state="MA",
                postal_code="02140",
                country="USA",
                phone="(617)555-5555",
                phone_country_code="1",
                user_updated_at=datetime.utcnow()
            ),
            make_sample(
                client_candidate_id=generate_id(),
                first_name="Clyde",
                last_name="Smith",
                middle_name="J",
                suffix="Jr.",
                salutation="Mr.",
                address_1="1 Penny Lane",
                city="Honolulu",
                state="HI",
                postal_code="96792",
                country="USA",
                phone="555-555-5555",
                phone_country_code="1",
                user_updated_at=datetime.utcnow()
            ),
            make_sample(
                client_candidate_id=generate_id(),
                first_name="Patty",
                last_name="Lee",
                salutation="Dr.",
                address_1="P.O. Box 555",
                city="Honolulu",
                state="HI",
                postal_code="96792",
                country="USA",
                phone="808-555-5555",
                phone_country_code="1",
                user_updated_at=datetime.utcnow()
            ),
            make_sample(
                client_candidate_id=generate_id(),
                first_name="Jimmy",
                last_name="James",
                address_1="2020 Palmer Blvd.",
                city="Springfield",
                state="MA",
                postal_code="96792",
                country="USA",
                phone="917-555-5555",
                phone_country_code="1",
                extension="2039",
                fax="917-555-5556",
                fax_country_code="1",
                company_name="ACME Traps",
                user_updated_at=datetime.utcnow()
            ),
            make_sample(
                client_candidate_id=generate_id(),
                first_name="Yeong-Un",
                last_name="Seo",
                address_1="Duryu, Lotte 101",
                address_2="Apt 55",
                city="Daegu",
                country="KOR",
                phone="917-555-5555",
                phone_country_code="011",
                user_updated_at=datetime.utcnow()
            ),

        ]
        
        for tcu in samples:
            tcu.save()
        

        