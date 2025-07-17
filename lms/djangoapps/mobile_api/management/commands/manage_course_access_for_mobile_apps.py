"""
Management command to manage `mobile_available` flag for Open edX courses.

Features:
- Enable or disable mobile access to all or selected courses.
- Supports dry-run mode for safe preview.
- Provides detailed categorized reports of actions taken.

Options:
  --dry-run                Simulate the changes without saving them.
  --include-invitational   Include invitation-only courses when enabling mobile access.
  --disable-invitational   Disable mobile access for invitation-only courses.
  --disable-all            Disable mobile access for all courses (overrides all other options).

Valid usage patterns:
──────────────────────────
1. Enable mobile access (default):
   ./manage.py lms manage_course_access_for_mobile_apps

2. Simulate enabling (dry run):
   ./manage.py lms manage_course_access_for_mobile_apps --dry-run

3. Enable mobile access and also include invitation-only courses:
   ./manage.py lms manage_course_access_for_mobile_apps --include-invitational

4. Simulate enabling + invitation-only (dry run):
   ./manage.py lms manage_course_access_for_mobile_apps --include-invitational --dry-run

5. Disable mobile access for invitation-only courses only:
   ./manage.py lms manage_course_access_for_mobile_apps --disable-invitational

6. Simulate disable for invitation-only:
   ./manage.py lms manage_course_access_for_mobile_apps --disable-invitational --dry-run

7. Disable mobile access for ALL courses:
   ./manage.py lms manage_course_access_for_mobile_apps --disable-all

8. Simulate global disable (dry run):
   ./manage.py lms manage_course_access_for_mobile_apps --disable-all --dry-run
"""


from django.core.management.base import BaseCommand
from xmodule.modulestore.django import modulestore
from xmodule.modulestore import ModuleStoreEnum


class Command(BaseCommand):
    help = "Manage mobile availability (`mobile_available`) flag for Open edX courses."

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Simulate the changes without saving them.",
        )
        parser.add_argument(
            "--include-invitational",
            action="store_true",
            help="Also include invitation-only courses.",
        )
        parser.add_argument(
            "--disable-invitational",
            action="store_true",
            help="Disable mobile access for invitation-only courses.",
        )
        parser.add_argument(
            "--disable-all",
            action="store_true",
            help="Disable mobile access for all courses.",
        )

    def handle(self, *args, **options):
        store = modulestore()
        courses = store.get_courses()

        dry_run = options["dry_run"]
        include_invitational = options["include_invitational"]
        disable_invitational = options["disable_invitational"]
        disable_all = options["disable_all"]

        if disable_all and (disable_invitational or include_invitational):
            self.stderr.write(
                "❌ Invalid combination: --disable-all cannot be used with --disable-invitational"
                " or --include-invitational. Please use only one of these options."
            )
            return

        # Tracking categories
        updated_courses = []
        skipped_courses = []
        disabled_courses = []
        total_courses = len(courses)

        for course in courses:
            reason = None
            action = None

            if disable_all:
                if course.mobile_available:
                    action = "disable"
                    reason = "Global disable (--disable-all)"
                else:
                    reason = "Already disabled"
            elif disable_invitational and course.invitation_only:
                if course.mobile_available:
                    action = "disable"
                    reason = "Disable invitation-only course (--disable-invitational)"
                else:
                    reason = "Invitation-only course already disabled"
            elif not course.invitation_only or include_invitational:
                if not course.mobile_available:
                    action = "enable"
                    reason = "Enabled for mobile (default)"
                else:
                    reason = "Already enabled"
            else:
                reason = "Skipped invitation-only (no --include-invitational)"

            if action == "enable":
                if dry_run:
                    updated_courses.append((course.id, "Would enable", reason))
                else:
                    course.mobile_available = True
                    with store.branch_setting(ModuleStoreEnum.Branch.draft_preferred, course.id):
                        store.update_item(course, user_id=0)
                    updated_courses.append((course.id, "Enabled", reason))

            elif action == "disable":
                if dry_run:
                    disabled_courses.append((course.id, "Would disable", reason))
                else:
                    course.mobile_available = False
                    with store.branch_setting(ModuleStoreEnum.Branch.draft_preferred, course.id):
                        store.update_item(course, user_id=0)
                    disabled_courses.append((course.id, "Disabled", reason))
            else:
                skipped_courses.append((course.id, "Skipped", reason))

        # Print the categorized report
        self.stdout.write("\n📋 Summary Report\n" + "=" * 60)

        self.stdout.write(f"\n📦 Total courses scanned: {total_courses}")

        if updated_courses:
            self.stdout.write(f"\n✅ Courses Enabled for Mobile ({len(updated_courses)}):")
            for cid, status, reason in updated_courses:
                self.stdout.write(f"  - {cid} → {status} ({reason})")

        if disabled_courses:
            self.stdout.write(f"\n🚫 Courses Disabled for Mobile ({len(disabled_courses)}):")
            for cid, status, reason in disabled_courses:
                self.stdout.write(f"  - {cid} → {status} ({reason})")

        if skipped_courses:
            self.stdout.write(f"\n⏭️ Skipped Courses ({len(skipped_courses)}):")
            for cid, status, reason in skipped_courses:
                self.stdout.write(f"  - {cid} → {status} ({reason})")

        self.stdout.write("\n🎉 Done.\n")
