#!/usr/bin/env bash
set -ev

# Violations thresholds for failing the build
PYLINT_THRESHOLD=3600
PEP8_THRESHOLD=0

case "${TEST_SUITE}" in

    "quality")
        paver find_fixme > fixme.log
        paver run_pep8 -l $PEP8_THRESHOLD > pep8.log
        paver run_pylint -l $PYLINT_THRESHOLD > pylint.log
        # Run quality task. Pass in the 'fail-under' percentage to diff-quality
        # First fetch origin/master because travis only fetches the branch it is building
        git fetch origin +master:master
        paver run_quality --compare-branch=master --percentage=100
        ;;

    "unit-cms")
        paver test_system -s cms --fasttest
        ;;

    # Issues with the bulk email xml to plaintext via lynx process
    "unit-lms")
        paver test_system -s lms --fasttest
        ;;

    "unit-lib")
        paver test_lib
        ;;

    "unit-js")
        paver test_js
        ;;

    "lettuce-cms")
        paver test_acceptance -s cms
        ;;

    "lettuce-lms")
        paver test_acceptance -s lms
        ;;

    "bok-1")
        paver test_bokchoy --skip_firefox_version_validation -t test_annotatable.py
        paver test_bokchoy --skip_firefox_version_validation --fasttest -t test_ora.py
        ;;

    "bok-2")
        paver test_bokchoy --skip_firefox_version_validation -t discussion/test_cohort_management.py
        paver test_bokchoy --skip_firefox_version_validation --fasttest -t discussion/test_cohorts.py
        paver test_bokchoy --skip_firefox_version_validation --fasttest -t discussion/test_discussion.py
        ;;

    "bok-3")
        paver test_bokchoy --skip_firefox_version_validation -t lms/test_lms.py
        paver test_bokchoy --skip_firefox_version_validation --fasttest -t lms/test_lms_acid_xblock.py
        paver test_bokchoy --skip_firefox_version_validation --fasttest -t lms/test_lms_courseware.py
        paver test_bokchoy --skip_firefox_version_validation --fasttest -t lms/test_lms_instructor_dashboard.py
        paver test_bokchoy --skip_firefox_version_validation --fasttest -t lms/test_lms_matlab_problem.py
        paver test_bokchoy --skip_firefox_version_validation --fasttest -t lms/test_lms_staff_view.py
        ;;

    "bok-4")
        paver test_bokchoy --skip_firefox_version_validation -t studio/test_studio_acid_xblock.py
        paver test_bokchoy --skip_firefox_version_validation --fasttest -t studio/test_studio_bad_data.py
        paver test_bokchoy --skip_firefox_version_validation --fasttest -t studio/test_studio_container.py
        paver test_bokchoy --skip_firefox_version_validation --fasttest -t studio/test_studio_general.py
        paver test_bokchoy --skip_firefox_version_validation --fasttest -t studio/test_studio_outline.py
        paver test_bokchoy --skip_firefox_version_validation --fasttest -t studio/test_studio_rerun.py
        paver test_bokchoy --skip_firefox_version_validation --fasttest -t studio/test_studio_settings.py
        paver test_bokchoy --skip_firefox_version_validation --fasttest -t studio/test_studio_split_test.py
        paver test_bokchoy --skip_firefox_version_validation --fasttest -t studio/test_studio_with_ora_component.py
        ;;

    "bok-5")
        paver test_bokchoy --skip_firefox_version_validation -t video/test_studio_video_editor.py
        paver test_bokchoy --skip_firefox_version_validation --fasttest -t video/test_studio_video_module.py
        paver test_bokchoy --skip_firefox_version_validation --fasttest -t video/test_studio_video_transcript.py
        paver test_bokchoy --skip_firefox_version_validation --fasttest -t video/test_video_handout.py
        paver test_bokchoy --skip_firefox_version_validation --fasttest -t video/test_video_module.py
        paver test_bokchoy --skip_firefox_version_validation --fasttest -t video/test_video_times.py
        ;;

    "bok-shard1")
        paver test_bokchoy --skip_firefox_version_validation --extra_args="-a shard_1"  # untested command
        ;;

    *)
        paver --help
        ;;
esac
