from itertools import izip

import cssutils
import json
import os
import sass

from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.sites.models import Site
from organizations.api import add_organization
from organizations.models import UserOrganizationMapping, Organization
from openedx.core.djangoapps.theming.models import SiteTheme


def get_initial_sass_variables():
    """
    This method loads the SASS variables file from the currently active theme. It is used as a default value
    for the sass_variables field on new Microsite objects.
    """
    return get_full_branding_list()


def get_branding_values_from_file():
    sass_var_file = os.path.join(settings.COMPREHENSIVE_THEME_DIR,
                                 settings.DEFAULT_SITE_THEME, 'customer_specific', 'lms', 'static',
                                 'sass', 'base', '_branding-basics.scss')
    with open(sass_var_file, 'r') as f:
        contents = f.read()
        values = sass_to_dict(contents)
    return values


def get_branding_labels_from_file(custom_branding=None):
    css_output = compile_sass('brand.scss', custom_branding)
    css_rules = cssutils.parseString(css_output, validate=False).cssRules
    labels = []
    for rule in css_rules:
        var_name = rule.selectorText.replace('.', '$')
        value = rule.style.content
        labels.append((var_name, value))
    return labels


def compile_sass(sass_file, custom_branding=None):
    sass_var_file = os.path.join(settings.COMPREHENSIVE_THEME_DIR,
                                 settings.DEFAULT_SITE_THEME, 'lms', 'static', 'sass', sass_file)
    customer_specific_includes = os.path.join(settings.COMPREHENSIVE_THEME_DIR,
                                              settings.DEFAULT_SITE_THEME,
                                              'customer_specific', 'lms', 'static', 'sass')
    importers = None
    if custom_branding:
        importers = [(0, custom_branding)]
    css_output = sass.compile(
        filename=sass_var_file,
        include_paths=[customer_specific_includes],
        importers=importers
    )
    return css_output


def get_full_branding_list():
    values = get_branding_values_from_file()
    labels = get_branding_labels_from_file()
    return [(val[0], (val[1], lab[1])) for val, lab in izip(values, labels)]


def get_initial_page_elements():
    return {
        'index': {
            'enabled': True,
            'content': []
        },
        'courses': {
            'enabled': True,
            'content': []
        },
        'course-about': {
            'enabled': True,
            'content': []
        },
        'about': {
            'enabled': True,
            'content': []
        },
        'blog': {
            'enabled': False,
            'content': []
        },
        'contact': {
            'enabled': True,
            'content': []
        },
        'copyright': {
            'enabled': True,
            'content': []
        },
        'donate': {
            'enabled': False,
            'content': []
        },
        'embargo': {
            'enabled': False,
            'content': []
        },
        'faq': {
            'enabled': False,
            'content': []
        },
        'help': {
            'enabled': False,
            'content': []
        },
        'honor': {
            'enabled': True,
            'content': []
        },
        'jobs': {
            'enabled': False,
            'content': []
        },
        'news': {
            'enabled': False,
            'content': []
        },
        'press': {
            'enabled': False,
            'content': []
        },
        'privacy': {
            'enabled': True,
            'content': []
        },
        'tos': {
            'enabled': True,
            'content': []
        },
    }


def sass_to_dict(sass_input):
    sass_vars = []
    lines = (line for line in sass_input.splitlines() if line and not line.startswith('//'))
    for line in lines:
        key, val = line.split(':')
        val = val.split('//')[0]
        val = val.strip().replace(";", "")
        sass_vars.append((key, val))
    return sass_vars


def sass_to_json_string(sass_input):
    sass_dict = sass_to_dict(sass_input)
    return json.dumps(sass_dict, sort_keys=True, indent=2)


def dict_to_sass(dict_input):
    sass_text = '\n'.join("{}: {};".format(key, val) for (key, val) in dict_input)
    return sass_text


def json_to_sass(json_input):
    sass_dict = json.loads(json_input)
    return dict_to_sass(sass_dict)


def bootstrap_site(site, organization_slug=None, user_email=None, password=None):
    from openedx.core.djangoapps.site_configuration.models import SiteConfiguration
    # don't use create because we need to call save() to set some values automatically
    site_config = SiteConfiguration(site=site, enabled=True)
    site_config.save()
    SiteTheme.objects.create(site=site, theme_dir_name=settings.DEFAULT_SITE_THEME)
    site.configuration_id = site_config.id
    # temp workarounds while old staging is still up and running
    if organization_slug:
        organization_data = add_organization({
            'name': organization_slug,
            'short_name': organization_slug
        })
        organization = Organization.objects.get(id=organization_data.get('id'))
        site_config.values['course_org_filter'] = organization_slug
        site_config.save()
    else:
        organization = {}
    if user_email:
        user = User.objects.get(email=user_email)
        UserOrganizationMapping.objects.create(user=user, organization=organization)
    else:
        user = {}
    return organization, site, user


def delete_site(site_id):
    site = Site.objects.get(id=site_id)
    site.configuration.delete()
    site.themes.delete()
    site.delete()
