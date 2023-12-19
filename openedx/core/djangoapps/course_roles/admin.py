""" Django admin page for course_roles djangoapp """

from django import forms
from django.contrib import admin
from django.contrib.auth import get_user_model
from django.utils.translation import gettext as _

from .models import UserRole
from organizations.models import Organization


User = get_user_model()  # pylint:disable=invalid-name


class UserRoleForm(forms.ModelForm):
    """Form for assigning users new roles in the Django Admin Panel"""
    email = forms.EmailField(required=True)

    def clean_org(self):
        """
        confirm org data is present if course data is present
        confirm org matches coures's org name
        """
        if self.cleaned_data.get("course") is not None and self.cleaned_data["org"] is None:
            course = self.cleaned_data.get("course")
            try:
                org = Organization.objects.get(name=course.org)
            except Exception as exc:
                err = _("An organization could not be found for {course}").format(course=course)
                raise forms.ValidationError(err) from exc
            return org
        if self.cleaned_data.get("course") and self.cleaned_data["org"]:
            org = self.cleaned_data["org"]
            org_name = self.cleaned_data.get("course").org
            if org.name.lower() != org_name.lower():
                err = _("Org name {org} is not valid. Valid name is {org_name}.").format(org=org, org_name=org_name)
                raise forms.ValidationError(err)
        return self.cleaned_data["org"]

    def clean_email(self):
        """
        Checking user object against given email id.
        """
        email = self.cleaned_data["email"]
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist as exc:
            err = _("Email does not exist. Could not find {email}. Please re-enter email address").format(email=email)
            raise forms.ValidationError(err) from exc
        except Exception as exc:
            err = _("There was an error submitting the email. Please re-enter email address")
            raise forms.ValidationError(err) from exc
        return user

    def clean(self):
        """
        Check if the user is already assigned this role in the DB for the context.
        Context can be course, org, or instance.
        """
        cleaned_data = super().clean()
        if not self.errors:
            if cleaned_data["course"]:
                user_role = UserRole.objects.filter(
                    user=cleaned_data.get("email"),
                    org=cleaned_data.get("org"),
                    course=cleaned_data.get("course"),
                    role=cleaned_data.get("role")
                )
            elif cleaned_data["org"]:
                user_role = UserRole.objects.filter(
                    user=cleaned_data.get("email"),
                    org=cleaned_data.get("org"),
                    course__isnull=True,
                    role=cleaned_data.get("role")
                )
            else:
                user_role = UserRole.objects.filter(
                    user=cleaned_data.get("email"),
                    org__isnull=True,
                    course__isnull=True,
                    role=cleaned_data.get("role")
                )
            if user_role.exists():
                raise forms.ValidationError(_(
                    "The {role} is already assigned to the user ({email}) for this context."
                    ).format(
                        role=cleaned_data.get("role"),
                        email=cleaned_data.get("email")
                    ))
        return cleaned_data

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.user_id:
            self.fields["email"].initial = self.instance.user.email
        self.fields["course"].widget.attrs.update(style="width: 25%")
        self.fields["org"].widget.attrs.update(style="width: 25%")
        self.fields["email"].widget.attrs.update(style="width: 25%")


class UserRoleAdmin(admin.ModelAdmin):
    """Admin panel for course_roles role assignment"""
    form = UserRoleForm
    raw_id_fields = ("user", "org", "course")

    fieldsets = (
        (_("Assign Course Role to User"), {
            "fields": (_("email"), _("course"), _("org"), _("role"),),
            # Translators: The <br> does not need to be translated.
            "description": _(
                "<br/>A role assigned to a course will only be"
                " valid for that course. Leave the org field blank.<br/>"
                "A role assigned to an org, without a course,"
                " will apply to all courses that are assigned to that org. Leave the course field blank."
                "<br/>A role assigned to neither a course nor an org will apply to"
                " all courses for the instance. Leave the course and org fields blank.<br/><br/>"
            )
        }),
    )

    list_display = (
        "id", "user", "course", "org", "role",
    )

    search_fields = (
        "id", "user__username", "user__email", "course", "org", "role",
    )

    def save_model(self, request, obj, form, change):
        obj.user = form.cleaned_data["email"]
        super().save_model(request, obj, form, change)


admin.site.register(UserRole, UserRoleAdmin)
