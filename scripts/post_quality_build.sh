current_path=`pwd`

reports_path=$current_path/reports

dest_path=$HOME/results/$TDDIUM_SESSION_ID/session/

echo "Getting Quality Reports... "

pep8_rpt=$reports_path/diff_quality/diff_quality_pep8.html
pylint_rpt=$reports_path/diff_quality/diff_quality_pylint.html

cp -f $pep8_rpt $dest_path
cp -f $pylint_rpt $dest_path

echo "Reports can be found in "$dest_path
