import csv

from zipfile import ZipFile
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
        # TODO: check that it's a zip
        
        
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
            if client_authorization_id is not None:
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
                    # store the Authorization Id if one is provided.  (For debugging)
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
            if client_candidate_id is not None:
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
                    # store the Authorization Id if one is provided.  (For debugging)
                    if row['CandidateID']:
                        try:
                            tcuser.candidate_id = int(row['CandidateID'])
                        except ValueError as ve:
                            print "Bad CandidateID value found for {}: message {}".format(client_candidate_id, ve)
                    tcuser.confirmed_at = datetime.utcnow()
                    tcuser.save()
                except TestCenterUser.DoesNotExist:
                    print " Failed to find record for client_candidate_id {}".format(client_candidate_id)
        
        
#    def _try_parse_time(self, key):
#        """
#        Parse an optional metadata key containing a time: if present, complain
#        if it doesn't parse.
#        Return None if not present or invalid.
#        """
#        if key in self.exam_info:
#                try:
#                    return parse_time(self.exam_info[key])
#                except ValueError as e:
#                    msg = "Exam {0} in course {1} loaded with a bad exam_info key '{2}': '{3}'".format(self.exam_name, self.course_id, self.exam_info[key], e)
#                    log.warning(msg)
#                return None
#        
#        with open(destfile, "wb") as outfile:
#            writer = csv.DictWriter(outfile,
#                                    Command.CSV_TO_MODEL_FIELDS,
#                                    delimiter="\t",
#                                    quoting=csv.QUOTE_MINIMAL,
#                                    extrasaction='ignore')
#            writer.writeheader()
#            for tcu in TestCenterUser.objects.order_by('id'):
#                if dump_all or tcu.needs_uploading:
#                    record = dict((csv_field, ensure_encoding(getattr(tcu, model_field)))
#                                  for csv_field, model_field
#                                  in Command.CSV_TO_MODEL_FIELDS.items())
#                    record["LastUpdate"] = record["LastUpdate"].strftime("%Y/%m/%d %H:%M:%S")
#                    writer.writerow(record)
#                    tcu.uploaded_at = uploaded_at
#                    tcu.save()


        
