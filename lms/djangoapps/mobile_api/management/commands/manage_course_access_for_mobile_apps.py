"""
Management command to manage the `mobile_available` flag for Open edX courses.

Features:
- Enable or disable mobile access to all or selected courses.
- Supports dry-run mode for safe preview.
- Handles invitation-only courses via flags.
- Allows targeting specific courses using --course-id or filtering by --org.

Options:
────────────────────────────────────────
  --dry-run                  Simulate the changes without saving.
  --disable-all              Disable mobile access for all selected courses.
  --disable-invitational     Disable mobile access for invitation-only courses only.
  --enable-invitational      Enable mobile access for invitation-only courses only.
  --course-id                Target one or more specific course IDs (can be repeated).
  --org                      Filter by one or more organization short codes (can be repeated).

Valid Usage Examples:
────────────────────────────────────────
1. Enable mobile access for all active courses:
   ./manage.py lms manage_course_access_for_mobile_apps

2. Simulate changes without saving (dry-run):
   ./manage.py lms manage_course_access_for_mobile_apps --dry-run

3. Enable mobile access for invitation-only courses:
   ./manage.py lms manage_course_access_for_mobile_apps --enable-invitational

4. Disable mobile access for invitation-only courses:
   ./manage.py lms manage_course_access_for_mobile_apps --disable-invitational

5. Disable mobile access for **all** courses:
   ./manage.py lms manage_course_access_for_mobile_apps --disable-all

6. Enable mobile access for **specific course IDs**:
   ./manage.py lms manage_course_access_for_mobile_apps \
       --course-id="course-v1:OrgX+MyCourse+2024_T1" \
       --course-id="course-v1:OrgY+Other+2024"

7. Disable mobile access for **specific course IDs only**:
   ./manage.py lms manage_course_access_for_mobile_apps \
       --disable-all \
       --course-id="course-v1:OrgX+MyCourse+2024_T1" \
       --course-id="course-v1:OrgY+Other+2024"

8. Target courses by organization(s):
   ./manage.py lms manage_course_access_for_mobile_apps --org=OrgX --org=OrgY

9. Disable mobile access for **all courses from selected orgs**:
   ./manage.py lms manage_course_access_for_mobile_apps \
       --disable-all \
       --org=OrgX --org=OrgY

Notes:
────────────────────────────────────────
- You may combine `--org` or `--course-id` with any enable/disable option to filter the target set.
- `--disable-all` cannot be combined with `--disable-invitational` or `--enable-invitational`.
- Invitation-only mode flags only act on courses with `invitation_only=True`.
"""

import logging
from datetime import datetime

import pytz
from django.core.management.base import BaseCommand, CommandError
from django.db.models import Q
from openedx.core.djangoapps.content.course_overviews.models import CourseOverview
from opaque_keys.edx.keys import CourseKey

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Update the mobile_available flag for courses with flexible options."

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Simulate the changes without saving.",
        )
        parser.add_argument(
            "--disable-all",
            action="store_true",
            help="Disable mobile access for all courses.",
        )
        parser.add_argument(
            "--disable-invitational",
            action="store_true",
            help="Disable mobile access for invitation-only courses.",
        )
        parser.add_argument(
            "--enable-invitational",
            action="store_true",
            help="Enable mobile access for invitation-only courses.",
        )
        parser.add_argument(
            "--course-id",
            action="append",
            help="Target specific course IDs (opaque key format). Can be repeated.",
        )
        parser.add_argument(
            "--org",
            action="append",
            help="Filter by one or more organization short codes. Can be repeated.",
        )

    def handle(self, *args, **options):
        dry_run = options["dry_run"]
        disable_all = options["disable_all"]
        disable_invitational = options["disable_invitational"]
        enable_invitational = options["enable_invitational"]
        course_ids = options.get("course_id") or []
        orgs = options.get("org") or []
        now = datetime.now(pytz.UTC)

        # Validation
        if disable_all and (disable_invitational or enable_invitational):
            raise CommandError(
                "--disable-all cannot be used with --disable-invitational or --enable-invitational"
            )

        course_overviews = CourseOverview.objects.all()

        if course_ids:
            valid_keys = []
            for cid in course_ids:
                try:
                    valid_keys.append(CourseKey.from_string(cid))
                except Exception as e:
                    raise CommandError(f"Invalid course ID '{cid}': {e}")
            course_overviews = course_overviews.filter(id__in=valid_keys)
        else:
            course_overviews = course_overviews.filter(
                Q(end__isnull=True) | Q(end__gte=now)
            )
            if orgs:
                org_filter = Q()
                for org in orgs:
                    org_filter |= Q(org__iexact=org)
                course_overviews = course_overviews.filter(org_filter)

        updated_courses = []
        skipped_invitationals = []
        skipped_already_set = []
        skipped_already_disabled = []

        for course in course_overviews:
            reason_skipped = None

            if disable_all:
                if course.mobile_available:
                    msg = f"Disabling mobile access for course: {course.id}"
                    if not dry_run:
                        course.mobile_available = False
                        course.save()
                    updated_courses.append((course.id, msg))
                else:
                    reason_skipped = "Already mobile_available=False"
                    skipped_already_disabled.append(course.id)

            elif disable_invitational:
                if course.invitation_only:
                    if course.mobile_available:
                        msg = f"Disabling mobile access for invitation-only course: {course.id}"
                        if not dry_run:
                            course.mobile_available = False
                            course.save()
                        updated_courses.append((course.id, msg))
                    else:
                        reason_skipped = "Invitation-only and already disabled"
                        skipped_already_disabled.append(course.id)
                else:
                    reason_skipped = "Not invitation-only course"
                    if course.mobile_available:
                        skipped_already_set.append(course.id)
                    else:
                        skipped_already_disabled.append(course.id)

            elif enable_invitational:
                if course.invitation_only:
                    if course.mobile_available:
                        reason_skipped = "Invitation-only and already enabled"
                        skipped_invitationals.append(course.id)
                    else:
                        msg = f"Enabling mobile access for course: {course.id}"
                        if not dry_run:
                            course.mobile_available = True
                            course.save()
                        updated_courses.append((course.id, msg))

            elif course.mobile_available:
                reason_skipped = "Already mobile_available=True"
                skipped_already_set.append(course.id)

            elif course.invitation_only:
                reason_skipped = "Invitation-only course"
                skipped_invitationals.append(course.id)

            else:
                msg = f"Enabling mobile access for course: {course.id}"
                if not dry_run:
                    course.mobile_available = True
                    course.save()
                updated_courses.append((course.id, msg))

            if reason_skipped:
                logger.info(f"Skipped {course.id}: {reason_skipped}")

        # Summary
        self.stdout.write("\n===== Mobile Availability Update Report =====")
        self.stdout.write(f"Total courses scanned: {len(course_overviews)}")
        self.stdout.write(f"Courses updated: {len(updated_courses)}")
        for cid, msg in updated_courses:
            self.stdout.write(f"  [UPDATED] {cid}: {msg}")

        self.stdout.write(f"\nSkipped invitation-only: {len(skipped_invitationals)}")
        for cid in skipped_invitationals:
            self.stdout.write(f"  [SKIPPED - INVITE] {cid}")

        self.stdout.write(f"\nSkipped already enabled: {len(skipped_already_set)}")
        for cid in skipped_already_set:
            self.stdout.write(f"  [SKIPPED - ALREADY ENABLED] {cid}")

        self.stdout.write(
            f"\nSkipped already disabled: {len(skipped_already_disabled)}"
        )
        for cid in skipped_already_disabled:
            self.stdout.write(f"  [SKIPPED - ALREADY DISABLED] {cid}")

        self.stdout.write("============================================\n")
