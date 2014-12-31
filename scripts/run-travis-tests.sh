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
        paver run_quality -p 100
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
        paver test_bokchoy --skip_firefox_version_validation -t common/test/acceptance/tests/test_annotatable.py common/test/acceptance/tests/test_ora.py
        ;;

    "bok-2")
        paver test_bokchoy --skip_firefox_version_validation -t common/test/acceptance/tests/discussion/test_cohort_management.py common/test/acceptance/tests/discussion/test_cohorts.py common/test/acceptance/tests/discussion/test_discussion.py
        ;;

    "bok-3")
        paver test_bokchoy --skip_firefox_version_validation -t common/test/acceptance/tests/lms/test_lms.py common/test/acceptance/tests/lms/test_lms_acid_xblock.py common/test/acceptance/tests/lms/test_lms_courseware.py common/test/acceptance/tests/lms/test_lms_instructor_dashboard.py common/test/acceptance/tests/lms/test_lms_matlab_problem.py common/test/acceptance/tests/lms/test_lms_staff_view.py
        ;;

    "bok-4")
        paver test_bokchoy --skip_firefox_version_validation -t common/test/acceptance/tests/studio/test_studio_acid_xblock.py common/test/acceptance/tests/studio/test_studio_bad_data.py common/test/acceptance/tests/studio/test_studio_container.py common/test/acceptance/tests/studio/test_studio_general.py common/test/acceptance/tests/studio/test_studio_outline.py common/test/acceptance/tests/studio/test_studio_rerun.py common/test/acceptance/tests/studio/test_studio_settings.py common/test/acceptance/tests/studio/test_studio_split_test.py common/test/acceptance/tests/studio/test_studio_with_ora_component.py
        ;;

    "bok-5")
        paver test_bokchoy --skip_firefox_version_validation -t common/test/acceptance/tests/video/test_studio_video_editor.py common/test/acceptance/tests/video/test_studio_video_module.py common/test/acceptance/tests/video/test_studio_video_transcript.py common/test/acceptance/tests/video/test_video_handout.py common/test/acceptance/tests/video/test_video_module.py common/test/acceptance/tests/video/test_video_times.py
        ;;

    "bok-shard1")
        paver test_bokchoy --skip_firefox_version_validation --extra_args="-a shard_1"  # untested command
        ;;

    *)
        paver --help
        ;;
esac
