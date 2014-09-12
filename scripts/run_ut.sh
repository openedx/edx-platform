mkdir -p jscover-dist && wget http://files.edx.org/testeng/JSCover-1.0.2.zip -P jscover-dist && unzip jscover-dist/JSCover-1.0.2.zip -d jscover-dist/ && cp jscover-dist/target/dist/JSCover-all.jar jscover-dist && export JSCOVER_JAR=$PWD/jscover-dist/JSCover-all.jar && paver test

echo '******************************************************'

echo 'Collecting Coverage...'

paver coverage

echo 'Coverage Collection Completed'


current_path=`pwd`
reports_path=$current_path/reports
dest_path=$HOME/results/$TDDIUM_SESSION_ID/session/
unit_combined_rpt=$reports_path/diff_coverage_combined.html

echo 'Copying '$unit_combined_rpt' to '$dest_path

cp -f $unit_combined_rpt $dest_path

echo '******************************************************'
