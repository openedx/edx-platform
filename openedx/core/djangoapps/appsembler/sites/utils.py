import json
import os

from django.conf import settings
from django.contrib.sites.models import Site
from openedx.core.djangoapps.theming.models import SiteTheme


def get_initial_sass_variables():
    """
    This method loads the SASS variables file from the currently active theme. It is used as a default value
    for the sass_variables field on new Microsite objects.
    """
    sass_var_file = os.path.join(settings.ENV_ROOT, "themes",
                                 settings.THEME_NAME, 'lms', 'src', 'base', '_branding-basics.scss')
    with open(sass_var_file, 'r') as f:
        return f.read()


def get_initial_page_elements():
    return {
        'index': [
            [
                "hero-element",
                "static-blocks/_hero-section-01.html",
                {
                    "hero_title": "Welcome to this test site, buddy!", #leave value empty if you don't want it displayed.
                    "hero_subtitle": "Bringing you mobile optimized courses about Open edX. We're Appsembler. Awesome!", # leave value empty if you don't want it displayed.
                    "cta_link": "http://www.appsembler.com",  ## leave value empty if you don't want a CTA button displayed.
                    "cta_link_text": "Awesome link!",  ## leave value empty if you don't want a CTA button displayed.
                    "popup_video_url": "MZrctLnsF4M", ## YouTube video ID - leave value empty if you don't want a video button and modal displayed.
                    "popup_video_text": "Watch our video", ## leave value empty if you don't want a video button and modal displayed.
                    "popup_video_id": "HeroVideo", ## leave value empty if you don't want a video button and modal displayed.
                    "bg_image_url": "/static/themes/amc-beta/images/hero-image.jpg", ## leave empty if you want just a full color background
                    "extra_css": ""  ## add custom css to be added inline to the wrapper element
                }
           ]
        ]
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


def bootstrap_site(site):
    from openedx.core.djangoapps.site_configuration.models import SiteConfiguration
    # don't use create because we need to call save() to set some values automatically
    site_config = SiteConfiguration(site=site, enabled=True)
    site_config.save()
    SiteTheme.objects.create(site=site, theme_dir_name=settings.THEME_NAME)
    site.configuration_id = site_config.id
    return site

def delete_site(site_id):
    site = Site.objects.get(id=site_id)
    site.configuration.delete()
    site.themes.delete()
    site.delete()
