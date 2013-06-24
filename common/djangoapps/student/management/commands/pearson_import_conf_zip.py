import csv

from zipfile import ZipFile, is_zipfile
from time import strptime, strftime

from datetime import datetime
from dogapi import dog_http_api

from django.core.management.base import BaseCommand, CommandError
from django.conf import settings

from student.models import TestCenterUser, TestCenterRegistration
from pytz import UTC


class Command(BaseCommand):

    dog_http_api.api_key = settings.DATADOG_API
    args = '<input zip file>'
    help = """
    Import Pearson confirmation files and update TestCenterUser
    and TestCenterRegistration tables with status.
    """

    @staticmethod
    def datadog_error(string, tags):
        dog_http_api.event("Pearson Import", string, alert_type='error', tags=[tags])

    def handle(self, *args, **kwargs):
        if len(args) < 1:
            print Command.help
            return

        source_zip = args[0]
        if not is_zipfile(source_zip):
            error = "Input file is not a zipfile: \"{}\"".format(source_zip)
            Command.datadog_error(error, source_zip)
            raise CommandError(error)

        # loop through all files in zip, and process them based on filename prefix:
        with ZipFile(source_zip, 'r') as zipfile:
            for fileinfo in zipfile.infolist():
                with zipfile.open(fileinfo) as zipentry:
                    if fileinfo.filename.startswith("eac-"):
                        self.process_eac(zipentry)
                    elif fileinfo.filename.startswith("vcdc-"):
                        self.process_vcdc(zipentry)
                    else:
                        error = "Unrecognized confirmation file type\"{}\" in confirmation zip file \"{}\"".format(fileinfo.filename, zipfile)
                        Command.datadog_error(error, source_zip)
                        raise CommandError(error)

    def process_eac(self, eacfile):
        print "processing eac"
        reader = csv.DictReader(eacfile, delimiter="\t")
        for row in reader:
            client_authorization_id = row['ClientAuthorizationID']
            if not client_authorization_id:
                if row['Status'] == 'Error':
                    Command.datadog_error("Error in EAD file processing ({}): {}".format(row['Date'], row['Message']), eacfile.name)
                else:
                    Command.datadog_error("Encountered bad record: {}".format(row), eacfile.name)
            else:
                try:
                    registration = TestCenterRegistration.objects.get(client_authorization_id=client_authorization_id)
                    Command.datadog_error("Found authorization record for user {}".format(registration.testcenter_user.user.username), eacfile.name)
                    # now update the record:
                    registration.upload_status = row['Status']
                    registration.upload_error_message = row['Message']
                    try:
                        registration.processed_at = strftime('%Y-%m-%d %H:%M:%S', strptime(row['Date'], '%Y/%m/%d %H:%M:%S'))
                    except ValueError as ve:
                        Command.datadog_error("Bad Date value found for {}: message {}".format(client_authorization_id, ve), eacfile.name)
                    # store the authorization Id if one is provided.  (For debugging)
                    if row['AuthorizationID']:
                        try:
                            registration.authorization_id = int(row['AuthorizationID'])
                        except ValueError as ve:
                            Command.datadog_error("Bad AuthorizationID value found for {}: message {}".format(client_authorization_id, ve), eacfile.name)

                    registration.confirmed_at = datetime.now(UTC)
                    registration.save()
                except TestCenterRegistration.DoesNotExist:
                    Command.datadog_error("Failed to find record for client_auth_id {}".format(client_authorization_id), eacfile.name)

    def process_vcdc(self, vcdcfile):
        print "processing vcdc"
        reader = csv.DictReader(vcdcfile, delimiter="\t")
        for row in reader:
            client_candidate_id = row['ClientCandidateID']
            if not client_candidate_id:
                if row['Status'] == 'Error':
                    Command.datadog_error("Error in CDD file processing ({}): {}".format(row['Date'], row['Message']), vcdcfile.name)
                else:
                    Command.datadog_error("Encountered bad record: {}".format(row), vcdcfile.name)
            else:
                try:
                    tcuser = TestCenterUser.objects.get(client_candidate_id=client_candidate_id)
                    Command.datadog_error("Found demographics record for user {}".format(tcuser.user.username), vcdcfile.name)
                    # now update the record:
                    tcuser.upload_status = row['Status']
                    tcuser.upload_error_message = row['Message']
                    try:
                        tcuser.processed_at = strftime('%Y-%m-%d %H:%M:%S', strptime(row['Date'], '%Y/%m/%d %H:%M:%S'))
                    except ValueError as ve:
                        Command.datadog_error("Bad Date value found for {}: message {}".format(client_candidate_id, ve), vcdcfile.name)
                    # store the candidate Id if one is provided.  (For debugging)
                    if row['CandidateID']:
                        try:
                            tcuser.candidate_id = int(row['CandidateID'])
                        except ValueError as ve:
                            Command.datadog_error("Bad CandidateID value found for {}: message {}".format(client_candidate_id, ve), vcdcfile.name)
                    tcuser.confirmed_at = datetime.utcnow()
                    tcuser.save()
                except TestCenterUser.DoesNotExist:
                    Command.datadog_error(" Failed to find record for client_candidate_id {}".format(client_candidate_id), vcdcfile.name)
