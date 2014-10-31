#!/bin/sh

EXIT=0

store_exit_code() {
    code=$?
    if [ ${code} -ne 0 ]
    then
        EXIT=${code}
    fi
}


echo 'Configuring jscover...'
mkdir -p jscover-dist && wget http://files.edx.org/testeng/JSCover-1.0.2.zip -P jscover-dist && unzip jscover-dist/JSCover-1.0.2.zip -d jscover-dist/ && cp jscover-dist/target/dist/JSCover-all.jar jscover-dist && export JSCOVER_JAR=$PWD/jscover-dist/JSCover-all.jar
store_exit_code
echo 'jscover configured'

paver test
store_exit_code

echo 'Collecting Coverage...'
paver coverage
store_exit_code
echo 'Coverage Collection Completed'


current_path=`pwd`
reports_path=${current_path}/reports
dest_path=${HOME}/results/${TDDIUM_SESSION_ID}/session/
unit_combined_rpt=${reports_path}/diff_coverage_combined.html

echo 'Copying '${unit_combined_rpt}' to '${dest_path}
cp -f ${unit_combined_rpt} ${dest_path}
store_exit_code
echo 'Copied '${unit_combined_rpt}

echo 'Merging unit coverage reports...'
python ./scripts/cov_merge.py unit && python ./scripts/metrics/publish.py
store_exit_code
echo 'Unit coverage reports merged'

exit ${EXIT}

