import csv

from zipfile import ZipFile, is_zipfile
from time import strptime, strftime

from collections import OrderedDict
from datetime import datetime
from os.path import isdir
from optparse import make_option

from django.core.management.base import BaseCommand, CommandError

from student.models import TestCenterUser, TestCenterRegistration

class Command(BaseCommand):
    
    
    args = '<input zip file>'
    help = """
    Import Pearson confirmation files and update TestCenterUser and TestCenterRegistration tables
    with status.
    """
    def handle(self, *args, **kwargs):
        if len(args) < 1:
            print Command.help
            return

        source_zip = args[0]
        if not is_zipfile(source_zip):
            raise CommandError("Input file is not a zipfile: \"{}\"".format(source_zip))        
        
        # loop through all files in zip, and process them based on filename prefix:
        with ZipFile(source_zip, 'r') as zipfile:
            for fileinfo in zipfile.infolist():
                with zipfile.open(fileinfo) as zipentry:
                    if fileinfo.filename.startswith("eac-"):
                        self.process_eac(zipentry)
                    elif fileinfo.filename.startswith("vcdc-"):
                        self.process_vcdc(zipentry)
                    else:
                        raise CommandError("Unrecognized confirmation file type \"{}\" in confirmation zip file \"{}\"".format(fileinfo.filename, zipfile))
        
    def process_eac(self, eacfile):       
        print "processing eac"
        reader = csv.DictReader(eacfile, delimiter="\t")
        for row in reader:
            client_authorization_id = row['ClientAuthorizationID']
            if not client_authorization_id:
                if row['Status'] == 'Error':
                    print "Error in EAD file processing ({}): {}".format(row['Date'], row['Message'])
                else:
                    print "Encountered bad record: {}".format(row)
            else:
                try:
                    registration = TestCenterRegistration.objects.get(client_authorization_id=client_authorization_id)
                    print "Found authorization record for user {}".format(registration.testcenter_user.user.username)
                    # now update the record:
                    registration.upload_status = row['Status']
                    registration.upload_error_message =  row['Message']
                    try:
                        registration.processed_at = strftime('%Y-%m-%d %H:%M:%S', strptime(row['Date'], '%Y/%m/%d %H:%M:%S'))
                    except ValueError as ve:
                        print "Bad Date value found for {}: message {}".format(client_authorization_id, ve)
                    # store the authorization Id if one is provided.  (For debugging)
                    if row['AuthorizationID']:
                        try:
                            registration.authorization_id = int(row['AuthorizationID'])
                        except ValueError as ve:
                            print "Bad AuthorizationID value found for {}: message {}".format(client_authorization_id, ve)
                                
                    registration.confirmed_at = datetime.utcnow()
                    registration.save()
                except TestCenterRegistration.DoesNotExist:
                    print " Failed to find record for client_auth_id {}".format(client_authorization_id)

        
    def process_vcdc(self, vcdcfile):       
        print "processing vcdc"
        reader = csv.DictReader(vcdcfile, delimiter="\t")
        for row in reader:
            client_candidate_id = row['ClientCandidateID']
            if not client_candidate_id:
                if row['Status'] == 'Error':
                    print "Error in CDD file processing ({}): {}".format(row['Date'], row['Message'])
                else:
                    print "Encountered bad record: {}".format(row)
            else:
                try:
                    tcuser = TestCenterUser.objects.get(client_candidate_id=client_candidate_id)
                    print "Found demographics record for user {}".format(tcuser.user.username)
                    # now update the record:
                    tcuser.upload_status = row['Status']
                    tcuser.upload_error_message =  row['Message']
                    try:
                        tcuser.processed_at = strftime('%Y-%m-%d %H:%M:%S', strptime(row['Date'], '%Y/%m/%d %H:%M:%S'))
                    except ValueError as ve:
                        print "Bad Date value found for {}: message {}".format(client_candidate_id, ve)
                    # store the candidate Id if one is provided.  (For debugging)
                    if row['CandidateID']:
                        try:
                            tcuser.candidate_id = int(row['CandidateID'])
                        except ValueError as ve:
                            print "Bad CandidateID value found for {}: message {}".format(client_candidate_id, ve)
                    tcuser.confirmed_at = datetime.utcnow()
                    tcuser.save()
                except TestCenterUser.DoesNotExist:
                    print " Failed to find record for client_candidate_id {}".format(client_candidate_id)
        
