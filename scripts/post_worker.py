import tarfile
import os
import shutil

full_path = os.path.realpath(__file__)
source_dir = full_path.replace("scripts/post_worker.py", "reports/")
output_filename = full_path.replace("post_worker.py", "reports.tar.gz")

print "source dir:", source_dir

count = 0

# walk through every subdirectory & add the folder if it is not empty
with tarfile.open(output_filename, "w:gz") as tar:
    for (path, dirs, files) in os.walk(source_dir):
        if len(files) > 0:
            print "tarring:", path
            tar.add(path, arcname=os.path.basename(path))
            count += 1

tar.close()

file_dest = os.environ['HOME'] + '/results/' + os.environ['TDDIUM_SESSION_ID'] + '/session/reports.tar.gz'

# if the tar file is not empty, copy it to the proper place
if count > 0:
    shutil.copyfile(output_filename, file_dest)
    print "done copying file"

# TODO: fold the remaining bash script into the Python script
# finding if there is any screenshots
# print "checking for screenshots"
# for (path, dirs, files) in os.walk('test_root/log'):
#    print files

print "TDDIUM_SESSION_ID:", os.environ['TDDIUM_SESSION_ID']