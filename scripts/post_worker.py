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

session_path = os.path.join(
    os.environ['HOME'],
    'results',
    os.environ['TDDIUM_SESSION_ID'],
    'session')

file_dest = os.path.join(session_path, 'reports.tar.gz')

# if the tar file is not empty, copy it to the proper place
if count > 0:
    print 'copying tar file to:', file_dest
    shutil.copyfile(output_filename, file_dest)

# finding if there is any screenshot or log file
print 'attaching failed screenshots and logs (if any)'
for (path, dirs, files) in os.walk('test_root/log'):
    for filename in files:
        if filename.find('png') != -1 or filename.find('log') != -1:
            filepath = os.path.join(path, filename)
            print 'copying file:', filepath
            destpath = os.path.join(session_path, filename)
            print 'destination:', destpath
            shutil.copyfile(filepath, destpath)

print 'TDDIUM_SESSION_ID:', os.environ['TDDIUM_SESSION_ID']