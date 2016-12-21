from itertools import izip

import cssutils
import json
import os
import sass

from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.sites.models import Site
from django.contrib.staticfiles.templatetags.staticfiles import static
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


def get_initial_page_elements():
    return {
      "embargo": {
        "content": []
      },
      "index": {
        "content":[
          {
            "element-type":"layout-single-col",
            "element-path":"page-builder/layouts/_single-col.html",
            "options":{
              "layout-bg-image": static("{}/images/example-assets/Screen%20Shot%202016-12-07%20at%2012.31.01_aFeMCtH.png".format(settings.DEFAULT_SITE_THEME)),
              "bg-color":"#fff",
              "margin-right":"marg-r-0",
              "margin-bottom":"marg-b-0",
              "layout-bg-image-size":"bg-img-size--cover",
              "text-color":"#000",
              "margin-top":"marg-t-0",
              "padding-right":"padd-r-0",
              "margin-left":"marg-l-0",
              "padding-bottom":"padd-b-200",
              "align-content":"align-content-center",
              "text-alignment":"text-align--center",
              "padding-top":"padd-t-200",
              "padding-left":"padd-l-0"
            },
            "children":{
              "column-1":[
                {
                  "element-type":"heading",
                  "element-path":"page-builder/elements/_heading.html",
                  "options":{
                    "font-size":"font-size--48px",
                    "margin-right":"marg-r-0",
                    "margin-bottom":"marg-b-20",
                    "text-color":"#ffffff",
                    "margin-top":"marg-t-0",
                    "margin-left":"marg-l-0",
                    "text-content":"We just took care of the Open edX tech stuff so you can focus on education!",
                    "font-family":"font--primary--bold",
                    "text-alignment":"text-align--center"
                  }
                },
                {
                  "element-type":"paragraph-text",
                  "element-path":"page-builder/elements/_paragraph.html",
                  "options":{
                    "font-size":"font-size--20px",
                    "margin-right":"marg-r-0",
                    "margin-bottom":"marg-b-5",
                    "text-color":"#f9f9f9",
                    "margin-top":"marg-t-5",
                    "margin-left":"marg-l-0",
                    "text-content":"Welcome to your Appsembler powered Open edX site! ",
                    "font-family":"font--primary--light",
                    "text-alignment":"text-align--center"
                  }
                },
                {
                  "element-type":"cta-button",
                  "element-path":"page-builder/elements/_cta-button.html",
                  "options":{
                    "font-size":"font-size--16px",
                    "bg-color":"#294854",
                    "border-color":"#ffffff",
                    "margin-right":"marg-r-0",
                    "border-width":"border-width--2px",
                    "margin-bottom":"marg-b-0",
                    "text-color":"#ffffff",
                    "margin-top":"marg-t-30",
                    "padding-right":"padd-r-30",
                    "margin-left":"marg-l-0",
                    "url":"www.appsembler.com",
                    "padding-bottom":"padd-b-15",
                    "text-content":"Visit our knowledgebase",
                    "padding-top":"padd-t-15",
                    "font-family":"font--primary--regular",
                    "padding-left":"padd-l-30"
                  }
                }
              ]
            }
          },
          {
            "element-type":"layout-50:50",
            "element-path":"page-builder/layouts/_two-col-50-50.html",
            "options":{
              "layout-bg-image":"",
              "bg-color":"#fff",
              "margin-right":"marg-r-0",
              "margin-bottom":"marg-b-0",
              "layout-bg-image-size":"bg-img-size--cover",
              "text-color":"#000",
              "margin-top":"marg-t-0",
              "padding-right":"padd-r-0",
              "margin-left":"marg-l-0",
              "padding-bottom":"padd-b-75",
              "align-content":"align-content-center",
              "text-alignment":"text-align--left",
              "padding-top":"padd-t-75",
              "padding-left":"padd-l-0"
            },
            "children":{
              "column-1":[
                {
                  "element-type":"heading",
                  "element-path":"page-builder/elements/_heading.html",
                  "options":{
                    "font-size":"font-size--24px",
                    "margin-right":"marg-r-0",
                    "margin-bottom":"marg-b-20",
                    "text-color":"#0090c1",
                    "margin-top":"marg-t-0",
                    "margin-left":"marg-l-0",
                    "text-content":"Now it's up to you!",
                    "font-family":"font--primary--bold",
                    "text-alignment":"text-align--left"
                  }
                },
                {
                  "element-type":"paragraph-text",
                  "element-path":"page-builder/elements/_paragraph.html",
                  "options":{
                    "font-size":"font-size--14px",
                    "margin-right":"marg-r-0",
                    "margin-bottom":"marg-b-5",
                    "text-color":"#323232",
                    "margin-top":"marg-t-5",
                    "margin-left":"marg-l-0",
                    "text-content":"Lorem ipsum dolor sit amet, consectetuer adipiscing elit, sed diam nonummy nibh euismod tincidunt ut laoreet dolore magna aliquam erat volutpat. Ut wisi enim ad minim veniam, quis nostrud exerci tation ullamcorper suscipit lobortis nisl ut aliquip ex ea commodo consequat. ",
                    "font-family":"font--primary--regular",
                    "text-alignment":"text-align--left"
                  }
                },
                {
                  "element-type":"popup-video-cta-button",
                  "element-path":"page-builder/elements/_popup-video-cta-button.html",
                  "options":{
                    "font-size":"font-size--16px",
                    "font-family":"font--primary--regular",
                    "bg-color":"#ffffff",
                    "border-color":"#0090c1",
                    "margin-right":"marg-r-0",
                    "border-width":"border-width--2px",
                    "margin-bottom":"marg-b-0",
                    "text-color":"#0090c1",
                    "margin-top":"marg-t-15",
                    "padding-right":"padd-r-15",
                    "margin-left":"marg-l-0",
                    "url":"www.google.com",
                    "padding-bottom":"padd-b-10",
                    "text-content":"View our tutorial video!",
                    "padding-top":"padd-t-10",
                    "youtube-video-id":"bJNNp7HNFZw",
                    "padding-left":"padd-l-15"
                  }
                }
              ],
              "column-2":[
                {
                  "element-type":"image-graphic",
                  "element-path":"page-builder/elements/_image-graphic.html",
                  "options":{
                    "margin-left":"marg-l-auto",
                    "image-alt-text":"Click around!",
                    "margin-bottom":"marg-b-0",
                    "image-file":static("{}/images/example-assets/laptop-mockup--01_6J4dpdp.png".format(settings.DEFAULT_SITE_THEME)),
                    "margin-top":"marg-t-0",
                    "margin-right":"marg-r-auto",
                    "link-url":"",
                    "image-width":"set-width--80percent"
                  }
                }
              ]
            }
          },
          {
            "element-type":"layout-single-col",
            "element-path":"page-builder/layouts/_single-col.html",
            "options":{
              "layout-bg-image":"",
              "bg-color":"#fff",
              "margin-right":"marg-r-0",
              "margin-bottom":"marg-b-0",
              "layout-bg-image-size":"bg-img-size--cover",
              "text-color":"#000",
              "margin-top":"marg-t-0",
              "padding-right":"padd-r-0",
              "margin-left":"marg-l-0",
              "padding-bottom":"padd-b-75",
              "align-content":"align-content-center",
              "text-alignment":"text-align--center",
              "padding-top":"padd-t-75",
              "padding-left":"padd-l-0"
            },
            "children":{
              "column-1":[
                {
                  "element-type":"heading",
                  "element-path":"page-builder/elements/_heading.html",
                  "options":{
                    "font-size":"font-size--20px",
                    "margin-right":"marg-r-0",
                    "margin-bottom":"marg-b-30",
                    "text-color":"#0090c1",
                    "margin-top":"marg-t-0",
                    "margin-left":"marg-l-0",
                    "text-content":"You can use your Open edX site to provide:",
                    "font-family":"font--primary--regular",
                    "text-alignment":"text-align--center"
                  }
                },
                {
                  "element-type":"layout-50:50",
                  "element-path":"page-builder/layouts/_two-col-50-50.html",
                  "options":{
                    "layout-bg-image":"",
                    "bg-color":"#fff",
                    "margin-right":"marg-r-0",
                    "margin-bottom":"marg-b-0",
                    "layout-bg-image-size":"bg-img-size--cover",
                    "text-color":"#000",
                    "margin-top":"marg-t-0",
                    "padding-right":"padd-r-0",
                    "margin-left":"marg-l-0",
                    "padding-bottom":"padd-b-20",
                    "align-content":"align-content-center",
                    "text-alignment":"text-align--left",
                    "padding-top":"padd-t-20",
                    "padding-left":"padd-l-0"
                  },
                  "children":{
                    "column-1":[
                      {
                        "element-type":"layout-50:50",
                        "element-path":"page-builder/layouts/_two-col-50-50.html",
                        "options":{
                          "layout-bg-image":"",
                          "bg-color":"#fff",
                          "margin-right":"marg-r-0",
                          "margin-bottom":"marg-b-0",
                          "layout-bg-image-size":"bg-img-size--cover",
                          "text-color":"#000",
                          "margin-top":"marg-t-0",
                          "padding-right":"padd-r-0",
                          "margin-left":"marg-l-0",
                          "padding-bottom":"padd-b-20",
                          "align-content":"align-content-center",
                          "text-alignment":"text-align--left",
                          "padding-top":"padd-t-20",
                          "padding-left":"padd-l-0"
                        },
                        "children":{
                          "column-1":[
                            {
                              "element-type":"image-graphic",
                              "element-path":"page-builder/elements/_image-graphic.html",
                              "options":{
                                "margin-left":"marg-l-auto",
                                "image-alt-text":"Corporate Learning",
                                "margin-bottom":"marg-b-20",
                                "image-file":static("{}/images/example-assets/icon__corporate-learning_bwTWIFu.svg".format(settings.DEFAULT_SITE_THEME)),
                                "margin-top":"marg-t-0",
                                "margin-right":"marg-r-auto",
                                "link-url":"",
                                "image-width":"set-width--40percent"
                              }
                            },
                            {
                              "element-type":"heading",
                              "element-path":"page-builder/elements/_heading.html",
                              "options":{
                                "font-size":"font-size--16px",
                                "margin-right":"marg-r-0",
                                "margin-bottom":"marg-b-0",
                                "text-color":"#5d6060",
                                "margin-top":"marg-t-0",
                                "margin-left":"marg-l-0",
                                "text-content":"Corporate Learning",
                                "font-family":"font--primary--bold",
                                "text-alignment":"text-align--center"
                              }
                            }
                          ],
                          "column-2":[
                            {
                              "element-type":"image-graphic",
                              "element-path":"page-builder/elements/_image-graphic.html",
                              "options":{
                                "margin-left":"marg-l-auto",
                                "image-alt-text":"Higher Education",
                                "margin-bottom":"marg-b-20",
                                "image-file":static("{}/images/example-assets/icon__higher-education_DxImyGx.svg".format(settings.DEFAULT_SITE_THEME)),
                                "margin-top":"marg-t-0",
                                "margin-right":"marg-r-auto",
                                "link-url":"",
                                "image-width":"set-width--40percent"
                              }
                            },
                            {
                              "element-type":"heading",
                              "element-path":"page-builder/elements/_heading.html",
                              "options":{
                                "font-size":"font-size--16px",
                                "margin-right":"marg-r-0",
                                "margin-bottom":"marg-b-0",
                                "text-color":"#5d6060",
                                "margin-top":"marg-t-0",
                                "margin-left":"marg-l-0",
                                "text-content":"Higher Education",
                                "font-family":"font--primary--bold",
                                "text-alignment":"text-align--center"
                              }
                            }
                          ]
                        }
                      }
                    ],
                    "column-2":[
                      {
                        "element-type":"layout-50:50",
                        "element-path":"page-builder/layouts/_two-col-50-50.html",
                        "options":{
                          "layout-bg-image":"",
                          "bg-color":"#fff",
                          "margin-right":"marg-r-0",
                          "margin-bottom":"marg-b-0",
                          "layout-bg-image-size":"bg-img-size--cover",
                          "text-color":"#000",
                          "margin-top":"marg-t-0",
                          "padding-right":"padd-r-0",
                          "margin-left":"marg-l-0",
                          "padding-bottom":"padd-b-20",
                          "align-content":"align-content-center",
                          "text-alignment":"text-align--left",
                          "padding-top":"padd-t-20",
                          "padding-left":"padd-l-0"
                        },
                        "children":{
                          "column-1":[
                            {
                              "element-type":"image-graphic",
                              "element-path":"page-builder/elements/_image-graphic.html",
                              "options":{
                                "margin-left":"marg-l-auto",
                                "image-alt-text":"Continuing education",
                                "margin-bottom":"marg-b-20",
                                "image-file":static("{}/images/example-assets/icon__continuing-education_dFMr53s.svg".format(settings.DEFAULT_SITE_THEME)),
                                "margin-top":"marg-t-0",
                                "margin-right":"marg-r-auto",
                                "link-url":"",
                                "image-width":"set-width--40percent"
                              }
                            },
                            {
                              "element-type":"heading",
                              "element-path":"page-builder/elements/_heading.html",
                              "options":{
                                "font-size":"font-size--16px",
                                "margin-right":"marg-r-0",
                                "margin-bottom":"marg-b-0",
                                "text-color":"#5d6060",
                                "margin-top":"marg-t-0",
                                "margin-left":"marg-l-0",
                                "text-content":"Continuing education",
                                "font-family":"font--primary--bold",
                                "text-alignment":"text-align--center"
                              }
                            }
                          ],
                          "column-2":[
                            {
                              "element-type":"image-graphic",
                              "element-path":"page-builder/elements/_image-graphic.html",
                              "options":{
                                "margin-left":"marg-l-auto",
                                "image-alt-text":"Professional development",
                                "margin-bottom":"marg-b-20",
                                "image-file":static("{}/images/example-assets/icon__professional-development_wRweLjm.svg".format(settings.DEFAULT_SITE_THEME)),
                                "margin-top":"marg-t-0",
                                "margin-right":"marg-r-auto",
                                "link-url":"",
                                "image-width":"set-width--40percent"
                              }
                            },
                            {
                              "element-type":"heading",
                              "element-path":"page-builder/elements/_heading.html",
                              "options":{
                                "font-size":"font-size--16px",
                                "margin-right":"marg-r-0",
                                "margin-bottom":"marg-b-0",
                                "text-color":"#5d6060",
                                "margin-top":"marg-t-0",
                                "margin-left":"marg-l-0",
                                "text-content":"Professional development",
                                "font-family":"font--primary--bold",
                                "text-alignment":"text-align--center"
                              }
                            }
                          ]
                        }
                      }
                    ]
                  }
                },
                {
                  "element-type":"paragraph-text",
                  "element-path":"page-builder/elements/_paragraph.html",
                  "options":{
                    "font-size":"font-size--14px",
                    "margin-right":"marg-r-0",
                    "margin-bottom":"marg-b-5",
                    "text-color":"#323232",
                    "margin-top":"marg-t-30",
                    "margin-left":"marg-l-0",
                    "text-content":"Appsembler is an edX partner and Open edX service provider and contributor. We provide custom Open edX development, implementation, integration, managed hosting, support and training, as well as advanced Open edX services such as SCORM support and Virtual Software Labs. ",
                    "font-family":"font--primary--light",
                    "text-alignment":"text-align--center"
                  }
                },
                {
                  "element-type":"paragraph-text",
                  "element-path":"page-builder/elements/_paragraph.html",
                  "options":{
                    "font-size":"font-size--14px",
                    "margin-right":"marg-r-0",
                    "margin-bottom":"marg-b-5",
                    "text-color":"#323232",
                    "margin-top":"marg-t-5",
                    "margin-left":"marg-l-0",
                    "text-content":"edX is a nonprofit initiative created by founding partners Harvard and MIT and composed of dozens of leading global institutions. Open edX is the open source software that powers edX.org and hundreds of other online learning sites around the world.",
                    "font-family":"font--primary--light",
                    "text-alignment":"text-align--center"
                  }
                }
              ]
            }
          },
          {
            "element-type":"layout-single-col",
            "element-path":"page-builder/layouts/_single-col.html",
            "options":{
              "layout-bg-image":"",
              "bg-color":"#fff",
              "margin-right":"marg-r-0",
              "margin-bottom":"marg-b-0",
              "layout-bg-image-size":"bg-img-size--cover",
              "text-color":"#000",
              "margin-top":"marg-t-0",
              "padding-right":"padd-r-0",
              "margin-left":"marg-l-0",
              "padding-bottom":"padd-b-20",
              "align-content":"align-content-center",
              "text-alignment":"text-align--left",
              "padding-top":"padd-t-20",
              "padding-left":"padd-l-0"
            },
            "children":{
              "column-1":[
                {
                  "element-type":"layout-single-col",
                  "element-path":"page-builder/layouts/_single-col.html",
                  "options":{
                    "layout-bg-image":"",
                    "bg-color":"#34495e",
                    "margin-right":"marg-r-0",
                    "margin-bottom":"marg-b-0",
                    "layout-bg-image-size":"bg-img-size--cover",
                    "text-color":"#000",
                    "margin-top":"marg-t-0",
                    "padding-right":"padd-r-0",
                    "margin-left":"marg-l-0",
                    "padding-bottom":"padd-b-0",
                    "align-content":"align-content-center",
                    "text-alignment":"text-align--left",
                    "padding-top":"padd-t-5",
                    "padding-left":"padd-l-0"
                  },
                  "children":{
                    "column-1":[]
                  }
                }
              ]
            }
          },
          {
            "element-type":"layout-single-col",
            "element-path":"page-builder/layouts/_single-col.html",
            "options":{
              "layout-bg-image":"",
              "bg-color":"#fff",
              "margin-right":"marg-r-0",
              "margin-bottom":"marg-b-0",
              "layout-bg-image-size":"bg-img-size--cover",
              "text-color":"#000",
              "margin-top":"marg-t-0",
              "padding-right":"padd-r-0",
              "margin-left":"marg-l-0",
              "padding-bottom":"padd-b-75",
              "align-content":"align-content-center",
              "text-alignment":"text-align--left",
              "padding-top":"padd-t-75",
              "padding-left":"padd-l-0"
            },
            "children":{
              "column-1":[
                {
                  "element-type":"paragraph-text",
                  "element-path":"page-builder/elements/_paragraph.html",
                  "options":{
                    "font-size":"font-size--16px",
                    "margin-right":"marg-r-0",
                    "margin-bottom":"marg-b-5",
                    "text-color":"#aaa7a7",
                    "margin-top":"marg-t-5",
                    "margin-left":"marg-l-0",
                    "text-content":"The content seen on this site is put here just to show you what you can build using our page manager - to change it do the following:",
                    "font-family":"font--primary--regular",
                    "text-alignment":"text-align--left"
                  }
                },
                {
                  "element-type":"layout-1:1:1",
                  "element-path":"page-builder/layouts/_three-col.html",
                  "options":{
                    "layout-bg-image":"",
                    "bg-color":"#fff",
                    "margin-right":"marg-r-0",
                    "margin-bottom":"marg-b-0",
                    "layout-bg-image-size":"bg-img-size--cover",
                    "text-color":"#000",
                    "margin-top":"marg-t-20",
                    "padding-right":"padd-r-0",
                    "margin-left":"marg-l-0",
                    "padding-bottom":"padd-b-20",
                    "align-content":"align-content-top",
                    "text-alignment":"text-align--left",
                    "padding-top":"padd-t-20",
                    "padding-left":"padd-l-0"
                  },
                  "children":{
                    "column-1":[
                      {
                        "element-type":"paragraph-text",
                        "element-path":"page-builder/elements/_paragraph.html",
                        "options":{
                          "font-size":"font-size--24px",
                          "margin-right":"marg-r-0",
                          "margin-bottom":"marg-b-5",
                          "text-color":"#0090c1",
                          "margin-top":"marg-t-5",
                          "margin-left":"marg-l-0",
                          "text-content":"1. Log in to your AMC Dashboard using the email and password you set up during signup.",
                          "font-family":"font--primary--light",
                          "text-alignment":"text-align--left"
                        }
                      }
                    ],
                    "column-3":[
                      {
                        "element-type":"paragraph-text",
                        "element-path":"page-builder/elements/_paragraph.html",
                        "options":{
                          "font-size":"font-size--24px",
                          "margin-right":"marg-r-0",
                          "margin-bottom":"marg-b-5",
                          "text-color":"#0090c1",
                          "margin-top":"marg-t-5",
                          "margin-left":"marg-l-0",
                          "text-content":"3. Remove the example content and start adding your own!",
                          "font-family":"font--primary--light",
                          "text-alignment":"text-align--left"
                        }
                      }
                    ],
                    "column-2":[
                      {
                        "element-type":"paragraph-text",
                        "element-path":"page-builder/elements/_paragraph.html",
                        "options":{
                          "font-size":"font-size--24px",
                          "margin-right":"marg-r-0",
                          "margin-bottom":"marg-b-5",
                          "text-color":"#0090c1",
                          "margin-top":"marg-t-5",
                          "margin-left":"marg-l-0",
                          "text-content":"2. Go to \"Content management\", then find \"Index\" page (should be right up on top and click \"Edit page\"",
                          "font-family":"font--primary--light",
                          "text-alignment":"text-align--left"
                        }
                      }
                    ]
                  }
                }
              ]
            }
          },
            {
                "element-type": "layout-single-col",
                "element-path": "page-builder/layouts/_single-col.html",
                "options": {
                    "layout-bg-image": "",
                    "bg-color": "#fff",
                    "margin-right": "marg-r-0",
                    "margin-bottom": "marg-b-0",
                    "layout-bg-image-size": "bg-img-size--cover",
                    "text-color": "#000",
                    "margin-top": "marg-t-0",
                    "padding-right": "padd-r-0",
                    "margin-left": "marg-l-0",
                    "padding-bottom": "padd-b-20",
                    "align-content": "align-content-center",
                    "text-alignment": "text-align--left",
                    "padding-top": "padd-t-20",
                    "padding-left": "padd-l-0"
                },
                "children": {
                    "column-1": [
                        {
                            "element-type": "layout-single-col",
                            "element-path": "page-builder/layouts/_single-col.html",
                            "options": {
                                "layout-bg-image": "",
                                "bg-color": "#34495e",
                                "margin-right": "marg-r-0",
                                "margin-bottom": "marg-b-0",
                                "layout-bg-image-size": "bg-img-size--cover",
                                "text-color": "#000",
                                "margin-top": "marg-t-0",
                                "padding-right": "padd-r-0",
                                "margin-left": "marg-l-0",
                                "padding-bottom": "padd-b-0",
                                "align-content": "align-content-center",
                                "text-alignment": "text-align--left",
                                "padding-top": "padd-t-5",
                                "padding-left": "padd-l-0"
                            },
                            "children": {
                                "column-1": []
                            }
                        }
                    ]
                }
            },
            {
                "element-type": "layout-single-col",
                "element-path": "page-builder/layouts/_single-col.html",
                "options": {
                    "layout-bg-image": "",
                    "bg-color": "#fff",
                    "margin-right": "marg-r-0",
                    "margin-bottom": "marg-b-50",
                    "layout-bg-image-size": "bg-img-size--cover",
                    "text-color": "#000",
                    "margin-top": "marg-t-0",
                    "padding-right": "padd-r-0",
                    "margin-left": "marg-l-0",
                    "padding-bottom": "padd-b-100",
                    "align-content": "align-content-center",
                    "text-alignment": "text-align--left",
                    "padding-top": "padd-t-75",
                    "padding-left": "padd-l-0"
                },
                "children": {
                    "column-1": [
                        {
                            "element-type": "heading",
                            "element-path": "page-builder/elements/_heading.html",
                            "options": {
                                "font-size": "font-size--32px",
                                "margin-right": "marg-r-0",
                                "margin-bottom": "marg-b-20",
                                "text-color": "#0090c1",
                                "margin-top": "marg-t-0",
                                "margin-left": "marg-l-0",
                                "text-content": "Here's an example of courses listing:",
                                "font-family": "font--primary--regular",
                                "text-alignment": "text-align--left"
                            }
                        },
                        {
                            "element-type": "paragraph-text",
                            "element-path": "page-builder/elements/_paragraph.html",
                            "options": {
                                "font-size": "font-size--14px",
                                "margin-right": "marg-r-0",
                                "margin-bottom": "marg-b-30",
                                "text-color": "#323232",
                                "margin-top": "marg-t-5",
                                "margin-left": "marg-l-0",
                                "text-content": "You can list a number of your latest courses on the Index page using the \"Courses Listing\" page element that you can add through our Page editor. Please note that this element can only be added to the Index page.",
                                "font-family": "font--primary--regular",
                                "text-alignment": "text-align--left"
                            }
                        },
                        {
                            "element-type": "courses-listing",
                            "element-path": "page-builder/elements/_courses-listing.html",
                            "options": {
                                "tile-type": "course-tile-01",
                                "num-of-courses": "4",
                                "text-alignment": "text-align--left"
                            }
                        }
                    ]
                }
            }
        ]
      },
      "about":{
        "content":[
          {
            "element-type":"layout-50:50",
            "element-path":"page-builder/layouts/_two-col-50-50.html",
            "options":{
              "layout-bg-image":"",
              "bg-color":"#34495e",
              "margin-right":"marg-r-0",
              "margin-bottom":"marg-b-0",
              "layout-bg-image-size":"bg-img-size--cover",
              "text-color":"#000",
              "margin-top":"marg-t-0",
              "padding-right":"padd-r-0",
              "margin-left":"marg-l-0",
              "padding-bottom":"padd-b-50",
              "align-content":"align-content-center",
              "text-alignment":"text-align--left",
              "padding-top":"padd-t-200",
              "padding-left":"padd-l-0"
            },
            "children":{
              "column-1":[
                {
                  "element-type":"heading",
                  "element-path":"page-builder/elements/_heading.html",
                  "options":{
                    "font-size":"font-size--48px",
                    "margin-right":"marg-r-0",
                    "margin-bottom":"marg-b-20",
                    "text-color":"#ffffff",
                    "margin-top":"marg-t-0",
                    "margin-left":"marg-l-0",
                    "text-content":"This is an example title of the static page",
                    "font-family":"font--primary--regular",
                    "text-alignment":"text-align--left"
                  }
                },
                {
                  "element-type":"paragraph-text",
                  "element-path":"page-builder/elements/_paragraph.html",
                  "options":{
                    "font-size":"font-size--18px",
                    "margin-right":"marg-r-0",
                    "margin-bottom":"marg-b-5",
                    "text-color":"#ffffff",
                    "margin-top":"marg-t-5",
                    "margin-left":"marg-l-0",
                    "text-content":"Vivamus scelerisque odio ut lectus luctus, eget viverra leo aliquet.",
                    "font-family":"font--primary--regular",
                    "text-alignment":"text-align--left"
                  }
                }
              ],
              "column-2":[]
            }
          },
          {
            "element-type":"layout-single-col",
            "element-path":"page-builder/layouts/_single-col.html",
            "options":{
              "layout-bg-image":"",
              "bg-color":"#fff",
              "margin-right":"marg-r-0",
              "margin-bottom":"marg-b-0",
              "layout-bg-image-size":"bg-img-size--cover",
              "text-color":"#000",
              "margin-top":"marg-t-0",
              "padding-right":"padd-r-0",
              "margin-left":"marg-l-0",
              "padding-bottom":"padd-b-20",
              "align-content":"align-content-center",
              "text-alignment":"text-align--left",
              "padding-top":"padd-t-20",
              "padding-left":"padd-l-0"
            },
            "children":{
              "column-1":[
                {
                  "element-type":"content-block",
                  "element-path":"page-builder/elements/_content-block.html",
                  "options":{
                    "content":"<p>Lorem ipsum dolor sit amet, consectetur adipiscing elit. <a href=\"#\">Mauris libero nulla</a>, sagittis at erat non, commodo porta nunc. Donec ultrices erat vel vehicula posuere. Morbi a justo metus. Ut et libero congue, interdum diam sit amet, scelerisque massa. Sed non purus mi. Fusce posuere vel ante eu tempus.<em> Integer interdum libero libero, sit amet fermentum nisl pretium ac. In suscipit, elit eget vulputate bibendum, arcu libero </em><em><strong>tristique</strong></em><em> diam, ut fringilla augue est in neque.</em> Suspendisse consequat ex non lacinia sodales.In feugiat eu erat non interdum. <del>Donec nec accumsan augue.</del> Sed consequat quis mauris ut interdum. Aliquam porttitor risus egestas, maximus quam a, cursus erat. Donec in sem ligula. Sed non convallis dui. Phasellus scelerisque maximus vestibulum.</p>\n<p><br></p>\n<h1>This is an H1 (large) heading</h1>\n<p>Fusce nunc est, euismod sit amet vehicula non, facilisis eu purus. Curabitur cursus et neque nec fringilla. Phasellus aliquam pulvinar risus. Praesent magna sem, consequat ut quam at, euismod maximus ipsum. Vestibulum porttitor blandit ultrices. <strong>Nam tempus hendrerit</strong> ipsum vitae elementum. Suspendisse sit amet eleifend tellus. Pellentesque habitant morbi tristique senectus et netus et malesuada fames ac turpis egestas. Aenean nec aliquam leo.Mauris sollicitudin ligula vitae erat mollis, a hendrerit mi molestie. Proin sit amet diam quis dolor ornare lacinia eu ut dui. In vitae congue diam. Aenean pharetra feugiat nulla, in ultrices nisl venenatis non. Donec nulla turpis, commodo eget pretium non, auctor vestibulum nibh. Donec sit amet sodales augue. Ut et odio at magna tempus interdum quis ut mauris. Nullam tristique semper condimentum. Sed sollicitudin lacus at felis vehicula bibendum. Nunc pharetra tincidunt urna. Suspendisse dignissim dui quis dolor fringilla porttitor. Morbi pellentesque eros quis lacus tristique maximus. Suspendisse laoreet sagittis ultrices.Pellentesque sit amet pellentesque felis.</p>\n<p><br></p>\n<h2>This is an H2 (medium) heading</h2>\n<p>Phasellus ex massa, hendrerit porta hendrerit a, pretium et justo. <ins>Vivamus eget dui sed justo consequat malesuada. Integer a commodo augue.</ins> Morbi rutrum suscipit efficitur. Vivamus ac libero ullamcorper, rhoncus nulla at, accumsan tellus. In hac habitasse platea dictumst. Donec maximus ex a faucibus commodo. In vel eros non diam pellentesque maximus. Curabitur fermentum accumsan lectus, ut aliquam ipsum pulvinar quis. Vestibulum ante ipsum primis in faucibus orci luctus et ultrices posuere cubilia Curae;Nam convallis egestas consectetur. Ut ac eleifend enim, a efficitur magna. Sed cursus ornare finibus. Mauris quis tincidunt justo. Cras efficitur, enim non pharetra ultrices, eros augue eleifend nisl, at congue elit leo quis arcu. Sed luctus, nibh vitae efficitur maximus, turpis ante porta diam, facilisis ultrices dui sem sed libero. Nulla pulvinar nisi eget cursus eleifend. Aliquam erat volutpat. Integer tortor nulla, auctor vitae vestibulum ut, sagittis sed velit. Integer a luctus arcu. Nam congue et elit sit amet porta. Cras euismod ipsum massa, quis elementum ligula lobortis quis. Mauris eu augue efficitur, feugiat augue non, aliquam ligula.Nulla a orci a felis mollis scelerisque. Pellentesque neque velit, faucibus nec mi eu, commodo tincidunt risus.</p>\n<p><br></p>\n<h3>This is an H3 (small) heading</h3>\n<p>Sed tempus justo leo, non sollicitudin mi eleifend a. Curabitur sed diam pulvinar, dictum nisl ut, blandit metus. Maecenas non sem quis ligula commodo egestas. Integer malesuada eleifend est, in commodo eros fermentum sed. Maecenas commodo nibh quis porttitor vehicula. Aenean blandit rutrum dolor, non ullamcorper est aliquam ac.Etiam interdum semper tempor. Phasellus condimentum massa eu libero sagittis cursus. Sed at lorem vel nulla elementum fringilla nec at eros. Aenean facilisis scelerisque tortor, non malesuada arcu scelerisque a. Ut est ante, iaculis at ultricies non, molestie placerat leo. Cras ullamcorper pellentesque erat in blandit. Nunc tortor ligula, fringilla ac risus quis, venenatis iaculis quam. Aliquam eget ex vitae ligula imperdiet finibus. Nullam ex metus, placerat ac arcu non, imperdiet consequat tortor. Donec varius elementum odio et rutrum. Sed in aliquam eros, sed sagittis erat. Vivamus tristique congue dictum. Proin tincidunt quis neque eget aliquam. Morbi sollicitudin orci lectus, a vulputate turpis porta a. Fusce facilisis ullamcorper dui in consequat.</p>\n<p><br></p>\n<h3>Code block follows</h3>\n<pre><code>Sed vitae convallis sapien, mollis fermentum ex.Curabitur rhoncus leo accumsan eros scelerisque, eget rhoncus augue porttitor. Praesent pretium mattis nibh, sit amet euismod nulla suscipit nec. Proin vehicula felis sit amet libero tempor, faucibus ultrices leo laoreet. Phasellus ultricies sapien urna, eget fringilla turpis rutrum vel. Donec nec nisl ultricies, lacinia diam in, finibus elit. Maecenas et felis eu lectus ultricies vestibulum. Aliquam accumsan efficitur lectus ut consequat. Sed quis aliquet justo, ut convallis eros.Vivamus vestibulum quam dictum orci aliquam, eget tincidunt est tincidunt. Curabitur pretium ut elit eget aliquet. Sed rhoncus metus sapien, eget malesuada ex dictum eu. Quisque auctor magna nibh, vel sollicitudin dui cursus sit amet.</code></pre>\n<p>In laoreet faucibus lorem vel fringilla. Sed et dolor sem. Proin velit augue, condimentum in enim sed, finibus tincidunt purus. Maecenas efficitur, lacus finibus vulputate luctus, urna eros iaculis lacus, a cursus lacus metus sit amet lacus. Maecenas porttitor imperdiet magna, et scelerisque nunc ornare nec. Integer consequat hendrerit neque, sed condimentum velit commodo a.</p>\n<p><br></p>\n<h3>Unordered list:</h3>\n<p>Praesent ultricies commodo arcu, at vulputate metus rutrum ut.Etiam vel ante vel nulla pellentesque aliquam sed at erat. In faucibus ac leo a dignissim. Donec augue lorem, sagittis sed tempus et, auctor vitae risus:</p>\n<ul>\n  <li>Fusce vel bibendum felis.</li>\n  <li>Phasellus vitae diam felis. Nulla rhoncus felis sit amet fringilla tincidunt. Pellentesque vestibulum, est non congue hendrerit, elit leo bibendum mauris, a malesuada quam massa ut lectus.</li>\n  <li>Vestibulum nec ornare neque.</li>\n  <li>Nunc mattis ex in vestibulum dapibus.</li>\n  <li>Quisque cursus lacus dui, consequat viverra purus lobortis ac. In hac habitasse platea dictumst.</li>\n</ul>\n<h3><br></h3>\n<h3>Ordered list:</h3>\n<p>Mauris sollicitudin ligula vitae erat mollis, a hendrerit mi molestie. Proin sit amet diam quis dolor ornare lacinia eu ut dui. In vitae congue diam. Aenean pharetra feugiat nulla, in ultrices nisl venenatis non. Donec nulla turpis, commodo eget pretium non, auctor vestibulum nibh:</p>\n<ol>\n  <li>Donec sit amet sodales augue. Ut et odio at magna tempus interdum quis ut mauris.</li>\n  <li>Nullam tristique semper condimentum.</li>\n  <li>Sed sollicitudin lacus at felis vehicula bibendum. Nunc pharetra tincidunt urna.</li>\n  <li>Suspendisse dignissim dui quis dolor fringilla porttitor.</li>\n  <li>Morbi pellentesque eros quis lacus tristique maximus. Suspendisse laoreet sagittis ultrices.</li>\n</ol>",
                    "margin-top":"marg-t-30",
                    "margin-bottom":"marg-b-100",
                    "margin-left":"marg-l-0",
                    "margin-right":"marg-r-0"
                  }
                }
              ]
            }
          }
        ]
      },
      "course-about":{
        "content":[
          {
            "element-type":"course-about-template",
            "element-path":"design-templates/pages/course-about/_course-about-01.html",
            "options":{
              "courseware-button-view-courseware-text":"View Courseware",
              "courseware-button-enroll-text":"Enroll in",
              "courseware-button-in-cart-text":"Course is in your cart.",
              "view-in-studio-button-text":"View About Page in studio",
              "courseware-button-enrollment-closed-text":"Enrollment is Closed",
              "courseware-button-add-to-cart-text":"Add to Cart / Price:",
              "courseware-button-invitation-only-text":"Enrollment in this course is by invitation only",
              "courseware-button-course-full-text":"Course is full",
              "courseware-button-already-enrolled-text":"You are enrolled in this course"
            }
          }
        ]
      },
      "jobs":{
        "content":[
          {
            "element-type":"layout-50:50",
            "element-path":"page-builder/layouts/_two-col-50-50.html",
            "options":{
              "layout-bg-image":"",
              "bg-color":"#34495e",
              "margin-right":"marg-r-0",
              "margin-bottom":"marg-b-0",
              "layout-bg-image-size":"bg-img-size--cover",
              "text-color":"#000",
              "margin-top":"marg-t-0",
              "padding-right":"padd-r-0",
              "margin-left":"marg-l-0",
              "padding-bottom":"padd-b-50",
              "align-content":"align-content-center",
              "text-alignment":"text-align--left",
              "padding-top":"padd-t-200",
              "padding-left":"padd-l-0"
            },
            "children":{
              "column-1":[
                {
                  "element-type":"heading",
                  "element-path":"page-builder/elements/_heading.html",
                  "options":{
                    "font-size":"font-size--48px",
                    "margin-right":"marg-r-0",
                    "margin-bottom":"marg-b-20",
                    "text-color":"#ffffff",
                    "margin-top":"marg-t-0",
                    "margin-left":"marg-l-0",
                    "text-content":"This is an example title of the static page",
                    "font-family":"font--primary--regular",
                    "text-alignment":"text-align--left"
                  }
                },
                {
                  "element-type":"paragraph-text",
                  "element-path":"page-builder/elements/_paragraph.html",
                  "options":{
                    "font-size":"font-size--18px",
                    "margin-right":"marg-r-0",
                    "margin-bottom":"marg-b-5",
                    "text-color":"#ffffff",
                    "margin-top":"marg-t-5",
                    "margin-left":"marg-l-0",
                    "text-content":"Vivamus scelerisque odio ut lectus luctus, eget viverra leo aliquet.",
                    "font-family":"font--primary--regular",
                    "text-alignment":"text-align--left"
                  }
                }
              ],
              "column-2":[]
            }
          },
          {
            "element-type":"layout-single-col",
            "element-path":"page-builder/layouts/_single-col.html",
            "options":{
              "layout-bg-image":"",
              "bg-color":"#fff",
              "margin-right":"marg-r-0",
              "margin-bottom":"marg-b-0",
              "layout-bg-image-size":"bg-img-size--cover",
              "text-color":"#000",
              "margin-top":"marg-t-0",
              "padding-right":"padd-r-0",
              "margin-left":"marg-l-0",
              "padding-bottom":"padd-b-20",
              "align-content":"align-content-center",
              "text-alignment":"text-align--left",
              "padding-top":"padd-t-20",
              "padding-left":"padd-l-0"
            },
            "children":{
              "column-1":[
                {
                  "element-type":"content-block",
                  "element-path":"page-builder/elements/_content-block.html",
                  "options":{
                    "content":"<p>Lorem ipsum dolor sit amet, consectetur adipiscing elit. <a href=\"#\">Mauris libero nulla</a>, sagittis at erat non, commodo porta nunc. Donec ultrices erat vel vehicula posuere. Morbi a justo metus. Ut et libero congue, interdum diam sit amet, scelerisque massa. Sed non purus mi. Fusce posuere vel ante eu tempus.<em> Integer interdum libero libero, sit amet fermentum nisl pretium ac. In suscipit, elit eget vulputate bibendum, arcu libero </em><em><strong>tristique</strong></em><em> diam, ut fringilla augue est in neque.</em> Suspendisse consequat ex non lacinia sodales.In feugiat eu erat non interdum. <del>Donec nec accumsan augue.</del> Sed consequat quis mauris ut interdum. Aliquam porttitor risus egestas, maximus quam a, cursus erat. Donec in sem ligula. Sed non convallis dui. Phasellus scelerisque maximus vestibulum.</p>\n<p><br></p>\n<h1>This is an H1 (large) heading</h1>\n<p>Fusce nunc est, euismod sit amet vehicula non, facilisis eu purus. Curabitur cursus et neque nec fringilla. Phasellus aliquam pulvinar risus. Praesent magna sem, consequat ut quam at, euismod maximus ipsum. Vestibulum porttitor blandit ultrices. <strong>Nam tempus hendrerit</strong> ipsum vitae elementum. Suspendisse sit amet eleifend tellus. Pellentesque habitant morbi tristique senectus et netus et malesuada fames ac turpis egestas. Aenean nec aliquam leo.Mauris sollicitudin ligula vitae erat mollis, a hendrerit mi molestie. Proin sit amet diam quis dolor ornare lacinia eu ut dui. In vitae congue diam. Aenean pharetra feugiat nulla, in ultrices nisl venenatis non. Donec nulla turpis, commodo eget pretium non, auctor vestibulum nibh. Donec sit amet sodales augue. Ut et odio at magna tempus interdum quis ut mauris. Nullam tristique semper condimentum. Sed sollicitudin lacus at felis vehicula bibendum. Nunc pharetra tincidunt urna. Suspendisse dignissim dui quis dolor fringilla porttitor. Morbi pellentesque eros quis lacus tristique maximus. Suspendisse laoreet sagittis ultrices.Pellentesque sit amet pellentesque felis.</p>\n<p><br></p>\n<h2>This is an H2 (medium) heading</h2>\n<p>Phasellus ex massa, hendrerit porta hendrerit a, pretium et justo. <ins>Vivamus eget dui sed justo consequat malesuada. Integer a commodo augue.</ins> Morbi rutrum suscipit efficitur. Vivamus ac libero ullamcorper, rhoncus nulla at, accumsan tellus. In hac habitasse platea dictumst. Donec maximus ex a faucibus commodo. In vel eros non diam pellentesque maximus. Curabitur fermentum accumsan lectus, ut aliquam ipsum pulvinar quis. Vestibulum ante ipsum primis in faucibus orci luctus et ultrices posuere cubilia Curae;Nam convallis egestas consectetur. Ut ac eleifend enim, a efficitur magna. Sed cursus ornare finibus. Mauris quis tincidunt justo. Cras efficitur, enim non pharetra ultrices, eros augue eleifend nisl, at congue elit leo quis arcu. Sed luctus, nibh vitae efficitur maximus, turpis ante porta diam, facilisis ultrices dui sem sed libero. Nulla pulvinar nisi eget cursus eleifend. Aliquam erat volutpat. Integer tortor nulla, auctor vitae vestibulum ut, sagittis sed velit. Integer a luctus arcu. Nam congue et elit sit amet porta. Cras euismod ipsum massa, quis elementum ligula lobortis quis. Mauris eu augue efficitur, feugiat augue non, aliquam ligula.Nulla a orci a felis mollis scelerisque. Pellentesque neque velit, faucibus nec mi eu, commodo tincidunt risus.</p>\n<p><br></p>\n<h3>This is an H3 (small) heading</h3>\n<p>Sed tempus justo leo, non sollicitudin mi eleifend a. Curabitur sed diam pulvinar, dictum nisl ut, blandit metus. Maecenas non sem quis ligula commodo egestas. Integer malesuada eleifend est, in commodo eros fermentum sed. Maecenas commodo nibh quis porttitor vehicula. Aenean blandit rutrum dolor, non ullamcorper est aliquam ac.Etiam interdum semper tempor. Phasellus condimentum massa eu libero sagittis cursus. Sed at lorem vel nulla elementum fringilla nec at eros. Aenean facilisis scelerisque tortor, non malesuada arcu scelerisque a. Ut est ante, iaculis at ultricies non, molestie placerat leo. Cras ullamcorper pellentesque erat in blandit. Nunc tortor ligula, fringilla ac risus quis, venenatis iaculis quam. Aliquam eget ex vitae ligula imperdiet finibus. Nullam ex metus, placerat ac arcu non, imperdiet consequat tortor. Donec varius elementum odio et rutrum. Sed in aliquam eros, sed sagittis erat. Vivamus tristique congue dictum. Proin tincidunt quis neque eget aliquam. Morbi sollicitudin orci lectus, a vulputate turpis porta a. Fusce facilisis ullamcorper dui in consequat.</p>\n<p><br></p>\n<h3>Code block follows</h3>\n<pre><code>Sed vitae convallis sapien, mollis fermentum ex.Curabitur rhoncus leo accumsan eros scelerisque, eget rhoncus augue porttitor. Praesent pretium mattis nibh, sit amet euismod nulla suscipit nec. Proin vehicula felis sit amet libero tempor, faucibus ultrices leo laoreet. Phasellus ultricies sapien urna, eget fringilla turpis rutrum vel. Donec nec nisl ultricies, lacinia diam in, finibus elit. Maecenas et felis eu lectus ultricies vestibulum. Aliquam accumsan efficitur lectus ut consequat. Sed quis aliquet justo, ut convallis eros.Vivamus vestibulum quam dictum orci aliquam, eget tincidunt est tincidunt. Curabitur pretium ut elit eget aliquet. Sed rhoncus metus sapien, eget malesuada ex dictum eu. Quisque auctor magna nibh, vel sollicitudin dui cursus sit amet.</code></pre>\n<p>In laoreet faucibus lorem vel fringilla. Sed et dolor sem. Proin velit augue, condimentum in enim sed, finibus tincidunt purus. Maecenas efficitur, lacus finibus vulputate luctus, urna eros iaculis lacus, a cursus lacus metus sit amet lacus. Maecenas porttitor imperdiet magna, et scelerisque nunc ornare nec. Integer consequat hendrerit neque, sed condimentum velit commodo a.</p>\n<p><br></p>\n<h3>Unordered list:</h3>\n<p>Praesent ultricies commodo arcu, at vulputate metus rutrum ut.Etiam vel ante vel nulla pellentesque aliquam sed at erat. In faucibus ac leo a dignissim. Donec augue lorem, sagittis sed tempus et, auctor vitae risus:</p>\n<ul>\n  <li>Fusce vel bibendum felis.</li>\n  <li>Phasellus vitae diam felis. Nulla rhoncus felis sit amet fringilla tincidunt. Pellentesque vestibulum, est non congue hendrerit, elit leo bibendum mauris, a malesuada quam massa ut lectus.</li>\n  <li>Vestibulum nec ornare neque.</li>\n  <li>Nunc mattis ex in vestibulum dapibus.</li>\n  <li>Quisque cursus lacus dui, consequat viverra purus lobortis ac. In hac habitasse platea dictumst.</li>\n</ul>\n<h3><br></h3>\n<h3>Ordered list:</h3>\n<p>Mauris sollicitudin ligula vitae erat mollis, a hendrerit mi molestie. Proin sit amet diam quis dolor ornare lacinia eu ut dui. In vitae congue diam. Aenean pharetra feugiat nulla, in ultrices nisl venenatis non. Donec nulla turpis, commodo eget pretium non, auctor vestibulum nibh:</p>\n<ol>\n  <li>Donec sit amet sodales augue. Ut et odio at magna tempus interdum quis ut mauris.</li>\n  <li>Nullam tristique semper condimentum.</li>\n  <li>Sed sollicitudin lacus at felis vehicula bibendum. Nunc pharetra tincidunt urna.</li>\n  <li>Suspendisse dignissim dui quis dolor fringilla porttitor.</li>\n  <li>Morbi pellentesque eros quis lacus tristique maximus. Suspendisse laoreet sagittis ultrices.</li>\n</ol>",
                    "margin-top":"marg-t-30",
                    "margin-bottom":"marg-b-100",
                    "margin-left":"marg-l-0",
                    "margin-right":"marg-r-0"
                  }
                }
              ]
            }
          }
        ]
      },
      "help":{
        "content":[
          {
            "element-type":"layout-50:50",
            "element-path":"page-builder/layouts/_two-col-50-50.html",
            "options":{
              "layout-bg-image":"",
              "bg-color":"#34495e",
              "margin-right":"marg-r-0",
              "margin-bottom":"marg-b-0",
              "layout-bg-image-size":"bg-img-size--cover",
              "text-color":"#000",
              "margin-top":"marg-t-0",
              "padding-right":"padd-r-0",
              "margin-left":"marg-l-0",
              "padding-bottom":"padd-b-50",
              "align-content":"align-content-center",
              "text-alignment":"text-align--left",
              "padding-top":"padd-t-200",
              "padding-left":"padd-l-0"
            },
            "children":{
              "column-1":[
                {
                  "element-type":"heading",
                  "element-path":"page-builder/elements/_heading.html",
                  "options":{
                    "font-size":"font-size--48px",
                    "margin-right":"marg-r-0",
                    "margin-bottom":"marg-b-20",
                    "text-color":"#ffffff",
                    "margin-top":"marg-t-0",
                    "margin-left":"marg-l-0",
                    "text-content":"This is an example title of the static page",
                    "font-family":"font--primary--regular",
                    "text-alignment":"text-align--left"
                  }
                },
                {
                  "element-type":"paragraph-text",
                  "element-path":"page-builder/elements/_paragraph.html",
                  "options":{
                    "font-size":"font-size--18px",
                    "margin-right":"marg-r-0",
                    "margin-bottom":"marg-b-5",
                    "text-color":"#ffffff",
                    "margin-top":"marg-t-5",
                    "margin-left":"marg-l-0",
                    "text-content":"Vivamus scelerisque odio ut lectus luctus, eget viverra leo aliquet.",
                    "font-family":"font--primary--regular",
                    "text-alignment":"text-align--left"
                  }
                }
              ],
              "column-2":[]
            }
          },
          {
            "element-type":"layout-single-col",
            "element-path":"page-builder/layouts/_single-col.html",
            "options":{
              "layout-bg-image":"",
              "bg-color":"#fff",
              "margin-right":"marg-r-0",
              "margin-bottom":"marg-b-0",
              "layout-bg-image-size":"bg-img-size--cover",
              "text-color":"#000",
              "margin-top":"marg-t-0",
              "padding-right":"padd-r-0",
              "margin-left":"marg-l-0",
              "padding-bottom":"padd-b-20",
              "align-content":"align-content-center",
              "text-alignment":"text-align--left",
              "padding-top":"padd-t-20",
              "padding-left":"padd-l-0"
            },
            "children":{
              "column-1":[
                {
                  "element-type":"content-block",
                  "element-path":"page-builder/elements/_content-block.html",
                  "options":{
                    "content":"<p>Lorem ipsum dolor sit amet, consectetur adipiscing elit. <a href=\"#\">Mauris libero nulla</a>, sagittis at erat non, commodo porta nunc. Donec ultrices erat vel vehicula posuere. Morbi a justo metus. Ut et libero congue, interdum diam sit amet, scelerisque massa. Sed non purus mi. Fusce posuere vel ante eu tempus.<em> Integer interdum libero libero, sit amet fermentum nisl pretium ac. In suscipit, elit eget vulputate bibendum, arcu libero </em><em><strong>tristique</strong></em><em> diam, ut fringilla augue est in neque.</em> Suspendisse consequat ex non lacinia sodales.In feugiat eu erat non interdum. <del>Donec nec accumsan augue.</del> Sed consequat quis mauris ut interdum. Aliquam porttitor risus egestas, maximus quam a, cursus erat. Donec in sem ligula. Sed non convallis dui. Phasellus scelerisque maximus vestibulum.</p>\n<p><br></p>\n<h1>This is an H1 (large) heading</h1>\n<p>Fusce nunc est, euismod sit amet vehicula non, facilisis eu purus. Curabitur cursus et neque nec fringilla. Phasellus aliquam pulvinar risus. Praesent magna sem, consequat ut quam at, euismod maximus ipsum. Vestibulum porttitor blandit ultrices. <strong>Nam tempus hendrerit</strong> ipsum vitae elementum. Suspendisse sit amet eleifend tellus. Pellentesque habitant morbi tristique senectus et netus et malesuada fames ac turpis egestas. Aenean nec aliquam leo.Mauris sollicitudin ligula vitae erat mollis, a hendrerit mi molestie. Proin sit amet diam quis dolor ornare lacinia eu ut dui. In vitae congue diam. Aenean pharetra feugiat nulla, in ultrices nisl venenatis non. Donec nulla turpis, commodo eget pretium non, auctor vestibulum nibh. Donec sit amet sodales augue. Ut et odio at magna tempus interdum quis ut mauris. Nullam tristique semper condimentum. Sed sollicitudin lacus at felis vehicula bibendum. Nunc pharetra tincidunt urna. Suspendisse dignissim dui quis dolor fringilla porttitor. Morbi pellentesque eros quis lacus tristique maximus. Suspendisse laoreet sagittis ultrices.Pellentesque sit amet pellentesque felis.</p>\n<p><br></p>\n<h2>This is an H2 (medium) heading</h2>\n<p>Phasellus ex massa, hendrerit porta hendrerit a, pretium et justo. <ins>Vivamus eget dui sed justo consequat malesuada. Integer a commodo augue.</ins> Morbi rutrum suscipit efficitur. Vivamus ac libero ullamcorper, rhoncus nulla at, accumsan tellus. In hac habitasse platea dictumst. Donec maximus ex a faucibus commodo. In vel eros non diam pellentesque maximus. Curabitur fermentum accumsan lectus, ut aliquam ipsum pulvinar quis. Vestibulum ante ipsum primis in faucibus orci luctus et ultrices posuere cubilia Curae;Nam convallis egestas consectetur. Ut ac eleifend enim, a efficitur magna. Sed cursus ornare finibus. Mauris quis tincidunt justo. Cras efficitur, enim non pharetra ultrices, eros augue eleifend nisl, at congue elit leo quis arcu. Sed luctus, nibh vitae efficitur maximus, turpis ante porta diam, facilisis ultrices dui sem sed libero. Nulla pulvinar nisi eget cursus eleifend. Aliquam erat volutpat. Integer tortor nulla, auctor vitae vestibulum ut, sagittis sed velit. Integer a luctus arcu. Nam congue et elit sit amet porta. Cras euismod ipsum massa, quis elementum ligula lobortis quis. Mauris eu augue efficitur, feugiat augue non, aliquam ligula.Nulla a orci a felis mollis scelerisque. Pellentesque neque velit, faucibus nec mi eu, commodo tincidunt risus.</p>\n<p><br></p>\n<h3>This is an H3 (small) heading</h3>\n<p>Sed tempus justo leo, non sollicitudin mi eleifend a. Curabitur sed diam pulvinar, dictum nisl ut, blandit metus. Maecenas non sem quis ligula commodo egestas. Integer malesuada eleifend est, in commodo eros fermentum sed. Maecenas commodo nibh quis porttitor vehicula. Aenean blandit rutrum dolor, non ullamcorper est aliquam ac.Etiam interdum semper tempor. Phasellus condimentum massa eu libero sagittis cursus. Sed at lorem vel nulla elementum fringilla nec at eros. Aenean facilisis scelerisque tortor, non malesuada arcu scelerisque a. Ut est ante, iaculis at ultricies non, molestie placerat leo. Cras ullamcorper pellentesque erat in blandit. Nunc tortor ligula, fringilla ac risus quis, venenatis iaculis quam. Aliquam eget ex vitae ligula imperdiet finibus. Nullam ex metus, placerat ac arcu non, imperdiet consequat tortor. Donec varius elementum odio et rutrum. Sed in aliquam eros, sed sagittis erat. Vivamus tristique congue dictum. Proin tincidunt quis neque eget aliquam. Morbi sollicitudin orci lectus, a vulputate turpis porta a. Fusce facilisis ullamcorper dui in consequat.</p>\n<p><br></p>\n<h3>Code block follows</h3>\n<pre><code>Sed vitae convallis sapien, mollis fermentum ex.Curabitur rhoncus leo accumsan eros scelerisque, eget rhoncus augue porttitor. Praesent pretium mattis nibh, sit amet euismod nulla suscipit nec. Proin vehicula felis sit amet libero tempor, faucibus ultrices leo laoreet. Phasellus ultricies sapien urna, eget fringilla turpis rutrum vel. Donec nec nisl ultricies, lacinia diam in, finibus elit. Maecenas et felis eu lectus ultricies vestibulum. Aliquam accumsan efficitur lectus ut consequat. Sed quis aliquet justo, ut convallis eros.Vivamus vestibulum quam dictum orci aliquam, eget tincidunt est tincidunt. Curabitur pretium ut elit eget aliquet. Sed rhoncus metus sapien, eget malesuada ex dictum eu. Quisque auctor magna nibh, vel sollicitudin dui cursus sit amet.</code></pre>\n<p>In laoreet faucibus lorem vel fringilla. Sed et dolor sem. Proin velit augue, condimentum in enim sed, finibus tincidunt purus. Maecenas efficitur, lacus finibus vulputate luctus, urna eros iaculis lacus, a cursus lacus metus sit amet lacus. Maecenas porttitor imperdiet magna, et scelerisque nunc ornare nec. Integer consequat hendrerit neque, sed condimentum velit commodo a.</p>\n<p><br></p>\n<h3>Unordered list:</h3>\n<p>Praesent ultricies commodo arcu, at vulputate metus rutrum ut.Etiam vel ante vel nulla pellentesque aliquam sed at erat. In faucibus ac leo a dignissim. Donec augue lorem, sagittis sed tempus et, auctor vitae risus:</p>\n<ul>\n  <li>Fusce vel bibendum felis.</li>\n  <li>Phasellus vitae diam felis. Nulla rhoncus felis sit amet fringilla tincidunt. Pellentesque vestibulum, est non congue hendrerit, elit leo bibendum mauris, a malesuada quam massa ut lectus.</li>\n  <li>Vestibulum nec ornare neque.</li>\n  <li>Nunc mattis ex in vestibulum dapibus.</li>\n  <li>Quisque cursus lacus dui, consequat viverra purus lobortis ac. In hac habitasse platea dictumst.</li>\n</ul>\n<h3><br></h3>\n<h3>Ordered list:</h3>\n<p>Mauris sollicitudin ligula vitae erat mollis, a hendrerit mi molestie. Proin sit amet diam quis dolor ornare lacinia eu ut dui. In vitae congue diam. Aenean pharetra feugiat nulla, in ultrices nisl venenatis non. Donec nulla turpis, commodo eget pretium non, auctor vestibulum nibh:</p>\n<ol>\n  <li>Donec sit amet sodales augue. Ut et odio at magna tempus interdum quis ut mauris.</li>\n  <li>Nullam tristique semper condimentum.</li>\n  <li>Sed sollicitudin lacus at felis vehicula bibendum. Nunc pharetra tincidunt urna.</li>\n  <li>Suspendisse dignissim dui quis dolor fringilla porttitor.</li>\n  <li>Morbi pellentesque eros quis lacus tristique maximus. Suspendisse laoreet sagittis ultrices.</li>\n</ol>",
                    "margin-top":"marg-t-30",
                    "margin-bottom":"marg-b-100",
                    "margin-left":"marg-l-0",
                    "margin-right":"marg-r-0"
                  }
                }
              ]
            }
          }
        ]
      },
      "copyright":{
        "content":[
          {
            "element-type":"layout-50:50",
            "element-path":"page-builder/layouts/_two-col-50-50.html",
            "options":{
              "layout-bg-image":"",
              "bg-color":"#34495e",
              "margin-right":"marg-r-0",
              "margin-bottom":"marg-b-0",
              "layout-bg-image-size":"bg-img-size--cover",
              "text-color":"#000",
              "margin-top":"marg-t-0",
              "padding-right":"padd-r-0",
              "margin-left":"marg-l-0",
              "padding-bottom":"padd-b-50",
              "align-content":"align-content-center",
              "text-alignment":"text-align--left",
              "padding-top":"padd-t-200",
              "padding-left":"padd-l-0"
            },
            "children":{
              "column-1":[
                {
                  "element-type":"heading",
                  "element-path":"page-builder/elements/_heading.html",
                  "options":{
                    "font-size":"font-size--48px",
                    "margin-right":"marg-r-0",
                    "margin-bottom":"marg-b-20",
                    "text-color":"#ffffff",
                    "margin-top":"marg-t-0",
                    "margin-left":"marg-l-0",
                    "text-content":"This is an example title of the static page",
                    "font-family":"font--primary--regular",
                    "text-alignment":"text-align--left"
                  }
                },
                {
                  "element-type":"paragraph-text",
                  "element-path":"page-builder/elements/_paragraph.html",
                  "options":{
                    "font-size":"font-size--18px",
                    "margin-right":"marg-r-0",
                    "margin-bottom":"marg-b-5",
                    "text-color":"#ffffff",
                    "margin-top":"marg-t-5",
                    "margin-left":"marg-l-0",
                    "text-content":"Vivamus scelerisque odio ut lectus luctus, eget viverra leo aliquet.",
                    "font-family":"font--primary--regular",
                    "text-alignment":"text-align--left"
                  }
                }
              ],
              "column-2":[]
            }
          },
          {
            "element-type":"layout-single-col",
            "element-path":"page-builder/layouts/_single-col.html",
            "options":{
              "layout-bg-image":"",
              "bg-color":"#fff",
              "margin-right":"marg-r-0",
              "margin-bottom":"marg-b-0",
              "layout-bg-image-size":"bg-img-size--cover",
              "text-color":"#000",
              "margin-top":"marg-t-0",
              "padding-right":"padd-r-0",
              "margin-left":"marg-l-0",
              "padding-bottom":"padd-b-20",
              "align-content":"align-content-center",
              "text-alignment":"text-align--left",
              "padding-top":"padd-t-20",
              "padding-left":"padd-l-0"
            },
            "children":{
              "column-1":[
                {
                  "element-type":"content-block",
                  "element-path":"page-builder/elements/_content-block.html",
                  "options":{
                    "content":"<p>Lorem ipsum dolor sit amet, consectetur adipiscing elit. <a href=\"#\">Mauris libero nulla</a>, sagittis at erat non, commodo porta nunc. Donec ultrices erat vel vehicula posuere. Morbi a justo metus. Ut et libero congue, interdum diam sit amet, scelerisque massa. Sed non purus mi. Fusce posuere vel ante eu tempus.<em> Integer interdum libero libero, sit amet fermentum nisl pretium ac. In suscipit, elit eget vulputate bibendum, arcu libero </em><em><strong>tristique</strong></em><em> diam, ut fringilla augue est in neque.</em> Suspendisse consequat ex non lacinia sodales.In feugiat eu erat non interdum. <del>Donec nec accumsan augue.</del> Sed consequat quis mauris ut interdum. Aliquam porttitor risus egestas, maximus quam a, cursus erat. Donec in sem ligula. Sed non convallis dui. Phasellus scelerisque maximus vestibulum.</p>\n<p><br></p>\n<h1>This is an H1 (large) heading</h1>\n<p>Fusce nunc est, euismod sit amet vehicula non, facilisis eu purus. Curabitur cursus et neque nec fringilla. Phasellus aliquam pulvinar risus. Praesent magna sem, consequat ut quam at, euismod maximus ipsum. Vestibulum porttitor blandit ultrices. <strong>Nam tempus hendrerit</strong> ipsum vitae elementum. Suspendisse sit amet eleifend tellus. Pellentesque habitant morbi tristique senectus et netus et malesuada fames ac turpis egestas. Aenean nec aliquam leo.Mauris sollicitudin ligula vitae erat mollis, a hendrerit mi molestie. Proin sit amet diam quis dolor ornare lacinia eu ut dui. In vitae congue diam. Aenean pharetra feugiat nulla, in ultrices nisl venenatis non. Donec nulla turpis, commodo eget pretium non, auctor vestibulum nibh. Donec sit amet sodales augue. Ut et odio at magna tempus interdum quis ut mauris. Nullam tristique semper condimentum. Sed sollicitudin lacus at felis vehicula bibendum. Nunc pharetra tincidunt urna. Suspendisse dignissim dui quis dolor fringilla porttitor. Morbi pellentesque eros quis lacus tristique maximus. Suspendisse laoreet sagittis ultrices.Pellentesque sit amet pellentesque felis.</p>\n<p><br></p>\n<h2>This is an H2 (medium) heading</h2>\n<p>Phasellus ex massa, hendrerit porta hendrerit a, pretium et justo. <ins>Vivamus eget dui sed justo consequat malesuada. Integer a commodo augue.</ins> Morbi rutrum suscipit efficitur. Vivamus ac libero ullamcorper, rhoncus nulla at, accumsan tellus. In hac habitasse platea dictumst. Donec maximus ex a faucibus commodo. In vel eros non diam pellentesque maximus. Curabitur fermentum accumsan lectus, ut aliquam ipsum pulvinar quis. Vestibulum ante ipsum primis in faucibus orci luctus et ultrices posuere cubilia Curae;Nam convallis egestas consectetur. Ut ac eleifend enim, a efficitur magna. Sed cursus ornare finibus. Mauris quis tincidunt justo. Cras efficitur, enim non pharetra ultrices, eros augue eleifend nisl, at congue elit leo quis arcu. Sed luctus, nibh vitae efficitur maximus, turpis ante porta diam, facilisis ultrices dui sem sed libero. Nulla pulvinar nisi eget cursus eleifend. Aliquam erat volutpat. Integer tortor nulla, auctor vitae vestibulum ut, sagittis sed velit. Integer a luctus arcu. Nam congue et elit sit amet porta. Cras euismod ipsum massa, quis elementum ligula lobortis quis. Mauris eu augue efficitur, feugiat augue non, aliquam ligula.Nulla a orci a felis mollis scelerisque. Pellentesque neque velit, faucibus nec mi eu, commodo tincidunt risus.</p>\n<p><br></p>\n<h3>This is an H3 (small) heading</h3>\n<p>Sed tempus justo leo, non sollicitudin mi eleifend a. Curabitur sed diam pulvinar, dictum nisl ut, blandit metus. Maecenas non sem quis ligula commodo egestas. Integer malesuada eleifend est, in commodo eros fermentum sed. Maecenas commodo nibh quis porttitor vehicula. Aenean blandit rutrum dolor, non ullamcorper est aliquam ac.Etiam interdum semper tempor. Phasellus condimentum massa eu libero sagittis cursus. Sed at lorem vel nulla elementum fringilla nec at eros. Aenean facilisis scelerisque tortor, non malesuada arcu scelerisque a. Ut est ante, iaculis at ultricies non, molestie placerat leo. Cras ullamcorper pellentesque erat in blandit. Nunc tortor ligula, fringilla ac risus quis, venenatis iaculis quam. Aliquam eget ex vitae ligula imperdiet finibus. Nullam ex metus, placerat ac arcu non, imperdiet consequat tortor. Donec varius elementum odio et rutrum. Sed in aliquam eros, sed sagittis erat. Vivamus tristique congue dictum. Proin tincidunt quis neque eget aliquam. Morbi sollicitudin orci lectus, a vulputate turpis porta a. Fusce facilisis ullamcorper dui in consequat.</p>\n<p><br></p>\n<h3>Code block follows</h3>\n<pre><code>Sed vitae convallis sapien, mollis fermentum ex.Curabitur rhoncus leo accumsan eros scelerisque, eget rhoncus augue porttitor. Praesent pretium mattis nibh, sit amet euismod nulla suscipit nec. Proin vehicula felis sit amet libero tempor, faucibus ultrices leo laoreet. Phasellus ultricies sapien urna, eget fringilla turpis rutrum vel. Donec nec nisl ultricies, lacinia diam in, finibus elit. Maecenas et felis eu lectus ultricies vestibulum. Aliquam accumsan efficitur lectus ut consequat. Sed quis aliquet justo, ut convallis eros.Vivamus vestibulum quam dictum orci aliquam, eget tincidunt est tincidunt. Curabitur pretium ut elit eget aliquet. Sed rhoncus metus sapien, eget malesuada ex dictum eu. Quisque auctor magna nibh, vel sollicitudin dui cursus sit amet.</code></pre>\n<p>In laoreet faucibus lorem vel fringilla. Sed et dolor sem. Proin velit augue, condimentum in enim sed, finibus tincidunt purus. Maecenas efficitur, lacus finibus vulputate luctus, urna eros iaculis lacus, a cursus lacus metus sit amet lacus. Maecenas porttitor imperdiet magna, et scelerisque nunc ornare nec. Integer consequat hendrerit neque, sed condimentum velit commodo a.</p>\n<p><br></p>\n<h3>Unordered list:</h3>\n<p>Praesent ultricies commodo arcu, at vulputate metus rutrum ut.Etiam vel ante vel nulla pellentesque aliquam sed at erat. In faucibus ac leo a dignissim. Donec augue lorem, sagittis sed tempus et, auctor vitae risus:</p>\n<ul>\n  <li>Fusce vel bibendum felis.</li>\n  <li>Phasellus vitae diam felis. Nulla rhoncus felis sit amet fringilla tincidunt. Pellentesque vestibulum, est non congue hendrerit, elit leo bibendum mauris, a malesuada quam massa ut lectus.</li>\n  <li>Vestibulum nec ornare neque.</li>\n  <li>Nunc mattis ex in vestibulum dapibus.</li>\n  <li>Quisque cursus lacus dui, consequat viverra purus lobortis ac. In hac habitasse platea dictumst.</li>\n</ul>\n<h3><br></h3>\n<h3>Ordered list:</h3>\n<p>Mauris sollicitudin ligula vitae erat mollis, a hendrerit mi molestie. Proin sit amet diam quis dolor ornare lacinia eu ut dui. In vitae congue diam. Aenean pharetra feugiat nulla, in ultrices nisl venenatis non. Donec nulla turpis, commodo eget pretium non, auctor vestibulum nibh:</p>\n<ol>\n  <li>Donec sit amet sodales augue. Ut et odio at magna tempus interdum quis ut mauris.</li>\n  <li>Nullam tristique semper condimentum.</li>\n  <li>Sed sollicitudin lacus at felis vehicula bibendum. Nunc pharetra tincidunt urna.</li>\n  <li>Suspendisse dignissim dui quis dolor fringilla porttitor.</li>\n  <li>Morbi pellentesque eros quis lacus tristique maximus. Suspendisse laoreet sagittis ultrices.</li>\n</ol>",
                    "margin-top":"marg-t-30",
                    "margin-bottom":"marg-b-100",
                    "margin-left":"marg-l-0",
                    "margin-right":"marg-r-0"
                  }
                }
              ]
            }
          }
        ]
      },
      "privacy":{
        "content":[
          {
            "element-type":"layout-50:50",
            "element-path":"page-builder/layouts/_two-col-50-50.html",
            "options":{
              "layout-bg-image":"",
              "bg-color":"#34495e",
              "margin-right":"marg-r-0",
              "margin-bottom":"marg-b-0",
              "layout-bg-image-size":"bg-img-size--cover",
              "text-color":"#000",
              "margin-top":"marg-t-0",
              "padding-right":"padd-r-0",
              "margin-left":"marg-l-0",
              "padding-bottom":"padd-b-50",
              "align-content":"align-content-center",
              "text-alignment":"text-align--left",
              "padding-top":"padd-t-200",
              "padding-left":"padd-l-0"
            },
            "children":{
              "column-1":[
                {
                  "element-type":"heading",
                  "element-path":"page-builder/elements/_heading.html",
                  "options":{
                    "font-size":"font-size--48px",
                    "margin-right":"marg-r-0",
                    "margin-bottom":"marg-b-20",
                    "text-color":"#ffffff",
                    "margin-top":"marg-t-0",
                    "margin-left":"marg-l-0",
                    "text-content":"This is an example title of the static page",
                    "font-family":"font--primary--regular",
                    "text-alignment":"text-align--left"
                  }
                },
                {
                  "element-type":"paragraph-text",
                  "element-path":"page-builder/elements/_paragraph.html",
                  "options":{
                    "font-size":"font-size--18px",
                    "margin-right":"marg-r-0",
                    "margin-bottom":"marg-b-5",
                    "text-color":"#ffffff",
                    "margin-top":"marg-t-5",
                    "margin-left":"marg-l-0",
                    "text-content":"Vivamus scelerisque odio ut lectus luctus, eget viverra leo aliquet.",
                    "font-family":"font--primary--regular",
                    "text-alignment":"text-align--left"
                  }
                }
              ],
              "column-2":[]
            }
          },
          {
            "element-type":"layout-single-col",
            "element-path":"page-builder/layouts/_single-col.html",
            "options":{
              "layout-bg-image":"",
              "bg-color":"#fff",
              "margin-right":"marg-r-0",
              "margin-bottom":"marg-b-0",
              "layout-bg-image-size":"bg-img-size--cover",
              "text-color":"#000",
              "margin-top":"marg-t-0",
              "padding-right":"padd-r-0",
              "margin-left":"marg-l-0",
              "padding-bottom":"padd-b-20",
              "align-content":"align-content-center",
              "text-alignment":"text-align--left",
              "padding-top":"padd-t-20",
              "padding-left":"padd-l-0"
            },
            "children":{
              "column-1":[
                {
                  "element-type":"content-block",
                  "element-path":"page-builder/elements/_content-block.html",
                  "options":{
                    "content":"<p>Lorem ipsum dolor sit amet, consectetur adipiscing elit. <a href=\"#\">Mauris libero nulla</a>, sagittis at erat non, commodo porta nunc. Donec ultrices erat vel vehicula posuere. Morbi a justo metus. Ut et libero congue, interdum diam sit amet, scelerisque massa. Sed non purus mi. Fusce posuere vel ante eu tempus.<em> Integer interdum libero libero, sit amet fermentum nisl pretium ac. In suscipit, elit eget vulputate bibendum, arcu libero </em><em><strong>tristique</strong></em><em> diam, ut fringilla augue est in neque.</em> Suspendisse consequat ex non lacinia sodales.In feugiat eu erat non interdum. <del>Donec nec accumsan augue.</del> Sed consequat quis mauris ut interdum. Aliquam porttitor risus egestas, maximus quam a, cursus erat. Donec in sem ligula. Sed non convallis dui. Phasellus scelerisque maximus vestibulum.</p>\n<p><br></p>\n<h1>This is an H1 (large) heading</h1>\n<p>Fusce nunc est, euismod sit amet vehicula non, facilisis eu purus. Curabitur cursus et neque nec fringilla. Phasellus aliquam pulvinar risus. Praesent magna sem, consequat ut quam at, euismod maximus ipsum. Vestibulum porttitor blandit ultrices. <strong>Nam tempus hendrerit</strong> ipsum vitae elementum. Suspendisse sit amet eleifend tellus. Pellentesque habitant morbi tristique senectus et netus et malesuada fames ac turpis egestas. Aenean nec aliquam leo.Mauris sollicitudin ligula vitae erat mollis, a hendrerit mi molestie. Proin sit amet diam quis dolor ornare lacinia eu ut dui. In vitae congue diam. Aenean pharetra feugiat nulla, in ultrices nisl venenatis non. Donec nulla turpis, commodo eget pretium non, auctor vestibulum nibh. Donec sit amet sodales augue. Ut et odio at magna tempus interdum quis ut mauris. Nullam tristique semper condimentum. Sed sollicitudin lacus at felis vehicula bibendum. Nunc pharetra tincidunt urna. Suspendisse dignissim dui quis dolor fringilla porttitor. Morbi pellentesque eros quis lacus tristique maximus. Suspendisse laoreet sagittis ultrices.Pellentesque sit amet pellentesque felis.</p>\n<p><br></p>\n<h2>This is an H2 (medium) heading</h2>\n<p>Phasellus ex massa, hendrerit porta hendrerit a, pretium et justo. <ins>Vivamus eget dui sed justo consequat malesuada. Integer a commodo augue.</ins> Morbi rutrum suscipit efficitur. Vivamus ac libero ullamcorper, rhoncus nulla at, accumsan tellus. In hac habitasse platea dictumst. Donec maximus ex a faucibus commodo. In vel eros non diam pellentesque maximus. Curabitur fermentum accumsan lectus, ut aliquam ipsum pulvinar quis. Vestibulum ante ipsum primis in faucibus orci luctus et ultrices posuere cubilia Curae;Nam convallis egestas consectetur. Ut ac eleifend enim, a efficitur magna. Sed cursus ornare finibus. Mauris quis tincidunt justo. Cras efficitur, enim non pharetra ultrices, eros augue eleifend nisl, at congue elit leo quis arcu. Sed luctus, nibh vitae efficitur maximus, turpis ante porta diam, facilisis ultrices dui sem sed libero. Nulla pulvinar nisi eget cursus eleifend. Aliquam erat volutpat. Integer tortor nulla, auctor vitae vestibulum ut, sagittis sed velit. Integer a luctus arcu. Nam congue et elit sit amet porta. Cras euismod ipsum massa, quis elementum ligula lobortis quis. Mauris eu augue efficitur, feugiat augue non, aliquam ligula.Nulla a orci a felis mollis scelerisque. Pellentesque neque velit, faucibus nec mi eu, commodo tincidunt risus.</p>\n<p><br></p>\n<h3>This is an H3 (small) heading</h3>\n<p>Sed tempus justo leo, non sollicitudin mi eleifend a. Curabitur sed diam pulvinar, dictum nisl ut, blandit metus. Maecenas non sem quis ligula commodo egestas. Integer malesuada eleifend est, in commodo eros fermentum sed. Maecenas commodo nibh quis porttitor vehicula. Aenean blandit rutrum dolor, non ullamcorper est aliquam ac.Etiam interdum semper tempor. Phasellus condimentum massa eu libero sagittis cursus. Sed at lorem vel nulla elementum fringilla nec at eros. Aenean facilisis scelerisque tortor, non malesuada arcu scelerisque a. Ut est ante, iaculis at ultricies non, molestie placerat leo. Cras ullamcorper pellentesque erat in blandit. Nunc tortor ligula, fringilla ac risus quis, venenatis iaculis quam. Aliquam eget ex vitae ligula imperdiet finibus. Nullam ex metus, placerat ac arcu non, imperdiet consequat tortor. Donec varius elementum odio et rutrum. Sed in aliquam eros, sed sagittis erat. Vivamus tristique congue dictum. Proin tincidunt quis neque eget aliquam. Morbi sollicitudin orci lectus, a vulputate turpis porta a. Fusce facilisis ullamcorper dui in consequat.</p>\n<p><br></p>\n<h3>Code block follows</h3>\n<pre><code>Sed vitae convallis sapien, mollis fermentum ex.Curabitur rhoncus leo accumsan eros scelerisque, eget rhoncus augue porttitor. Praesent pretium mattis nibh, sit amet euismod nulla suscipit nec. Proin vehicula felis sit amet libero tempor, faucibus ultrices leo laoreet. Phasellus ultricies sapien urna, eget fringilla turpis rutrum vel. Donec nec nisl ultricies, lacinia diam in, finibus elit. Maecenas et felis eu lectus ultricies vestibulum. Aliquam accumsan efficitur lectus ut consequat. Sed quis aliquet justo, ut convallis eros.Vivamus vestibulum quam dictum orci aliquam, eget tincidunt est tincidunt. Curabitur pretium ut elit eget aliquet. Sed rhoncus metus sapien, eget malesuada ex dictum eu. Quisque auctor magna nibh, vel sollicitudin dui cursus sit amet.</code></pre>\n<p>In laoreet faucibus lorem vel fringilla. Sed et dolor sem. Proin velit augue, condimentum in enim sed, finibus tincidunt purus. Maecenas efficitur, lacus finibus vulputate luctus, urna eros iaculis lacus, a cursus lacus metus sit amet lacus. Maecenas porttitor imperdiet magna, et scelerisque nunc ornare nec. Integer consequat hendrerit neque, sed condimentum velit commodo a.</p>\n<p><br></p>\n<h3>Unordered list:</h3>\n<p>Praesent ultricies commodo arcu, at vulputate metus rutrum ut.Etiam vel ante vel nulla pellentesque aliquam sed at erat. In faucibus ac leo a dignissim. Donec augue lorem, sagittis sed tempus et, auctor vitae risus:</p>\n<ul>\n  <li>Fusce vel bibendum felis.</li>\n  <li>Phasellus vitae diam felis. Nulla rhoncus felis sit amet fringilla tincidunt. Pellentesque vestibulum, est non congue hendrerit, elit leo bibendum mauris, a malesuada quam massa ut lectus.</li>\n  <li>Vestibulum nec ornare neque.</li>\n  <li>Nunc mattis ex in vestibulum dapibus.</li>\n  <li>Quisque cursus lacus dui, consequat viverra purus lobortis ac. In hac habitasse platea dictumst.</li>\n</ul>\n<h3><br></h3>\n<h3>Ordered list:</h3>\n<p>Mauris sollicitudin ligula vitae erat mollis, a hendrerit mi molestie. Proin sit amet diam quis dolor ornare lacinia eu ut dui. In vitae congue diam. Aenean pharetra feugiat nulla, in ultrices nisl venenatis non. Donec nulla turpis, commodo eget pretium non, auctor vestibulum nibh:</p>\n<ol>\n  <li>Donec sit amet sodales augue. Ut et odio at magna tempus interdum quis ut mauris.</li>\n  <li>Nullam tristique semper condimentum.</li>\n  <li>Sed sollicitudin lacus at felis vehicula bibendum. Nunc pharetra tincidunt urna.</li>\n  <li>Suspendisse dignissim dui quis dolor fringilla porttitor.</li>\n  <li>Morbi pellentesque eros quis lacus tristique maximus. Suspendisse laoreet sagittis ultrices.</li>\n</ol>",
                    "margin-top":"marg-t-30",
                    "margin-bottom":"marg-b-100",
                    "margin-left":"marg-l-0",
                    "margin-right":"marg-r-0"
                  }
                }
              ]
            }
          }
        ]
      },
      "course-card":"course-tile-01",
      "faq":{
        "content":[
          {
            "element-type":"layout-50:50",
            "element-path":"page-builder/layouts/_two-col-50-50.html",
            "options":{
              "layout-bg-image":"",
              "bg-color":"#34495e",
              "margin-right":"marg-r-0",
              "margin-bottom":"marg-b-0",
              "layout-bg-image-size":"bg-img-size--cover",
              "text-color":"#000",
              "margin-top":"marg-t-0",
              "padding-right":"padd-r-0",
              "margin-left":"marg-l-0",
              "padding-bottom":"padd-b-50",
              "align-content":"align-content-center",
              "text-alignment":"text-align--left",
              "padding-top":"padd-t-200",
              "padding-left":"padd-l-0"
            },
            "children":{
              "column-1":[
                {
                  "element-type":"heading",
                  "element-path":"page-builder/elements/_heading.html",
                  "options":{
                    "font-size":"font-size--48px",
                    "margin-right":"marg-r-0",
                    "margin-bottom":"marg-b-20",
                    "text-color":"#ffffff",
                    "margin-top":"marg-t-0",
                    "margin-left":"marg-l-0",
                    "text-content":"This is an example title of the static page",
                    "font-family":"font--primary--regular",
                    "text-alignment":"text-align--left"
                  }
                },
                {
                  "element-type":"paragraph-text",
                  "element-path":"page-builder/elements/_paragraph.html",
                  "options":{
                    "font-size":"font-size--18px",
                    "margin-right":"marg-r-0",
                    "margin-bottom":"marg-b-5",
                    "text-color":"#ffffff",
                    "margin-top":"marg-t-5",
                    "margin-left":"marg-l-0",
                    "text-content":"Vivamus scelerisque odio ut lectus luctus, eget viverra leo aliquet.",
                    "font-family":"font--primary--regular",
                    "text-alignment":"text-align--left"
                  }
                }
              ],
              "column-2":[]
            }
          },
          {
            "element-type":"layout-single-col",
            "element-path":"page-builder/layouts/_single-col.html",
            "options":{
              "layout-bg-image":"",
              "bg-color":"#fff",
              "margin-right":"marg-r-0",
              "margin-bottom":"marg-b-0",
              "layout-bg-image-size":"bg-img-size--cover",
              "text-color":"#000",
              "margin-top":"marg-t-0",
              "padding-right":"padd-r-0",
              "margin-left":"marg-l-0",
              "padding-bottom":"padd-b-20",
              "align-content":"align-content-center",
              "text-alignment":"text-align--left",
              "padding-top":"padd-t-20",
              "padding-left":"padd-l-0"
            },
            "children":{
              "column-1":[
                {
                  "element-type":"content-block",
                  "element-path":"page-builder/elements/_content-block.html",
                  "options":{
                    "content":"<p>Lorem ipsum dolor sit amet, consectetur adipiscing elit. <a href=\"#\">Mauris libero nulla</a>, sagittis at erat non, commodo porta nunc. Donec ultrices erat vel vehicula posuere. Morbi a justo metus. Ut et libero congue, interdum diam sit amet, scelerisque massa. Sed non purus mi. Fusce posuere vel ante eu tempus.<em> Integer interdum libero libero, sit amet fermentum nisl pretium ac. In suscipit, elit eget vulputate bibendum, arcu libero </em><em><strong>tristique</strong></em><em> diam, ut fringilla augue est in neque.</em> Suspendisse consequat ex non lacinia sodales.In feugiat eu erat non interdum. <del>Donec nec accumsan augue.</del> Sed consequat quis mauris ut interdum. Aliquam porttitor risus egestas, maximus quam a, cursus erat. Donec in sem ligula. Sed non convallis dui. Phasellus scelerisque maximus vestibulum.</p>\n<p><br></p>\n<h1>This is an H1 (large) heading</h1>\n<p>Fusce nunc est, euismod sit amet vehicula non, facilisis eu purus. Curabitur cursus et neque nec fringilla. Phasellus aliquam pulvinar risus. Praesent magna sem, consequat ut quam at, euismod maximus ipsum. Vestibulum porttitor blandit ultrices. <strong>Nam tempus hendrerit</strong> ipsum vitae elementum. Suspendisse sit amet eleifend tellus. Pellentesque habitant morbi tristique senectus et netus et malesuada fames ac turpis egestas. Aenean nec aliquam leo.Mauris sollicitudin ligula vitae erat mollis, a hendrerit mi molestie. Proin sit amet diam quis dolor ornare lacinia eu ut dui. In vitae congue diam. Aenean pharetra feugiat nulla, in ultrices nisl venenatis non. Donec nulla turpis, commodo eget pretium non, auctor vestibulum nibh. Donec sit amet sodales augue. Ut et odio at magna tempus interdum quis ut mauris. Nullam tristique semper condimentum. Sed sollicitudin lacus at felis vehicula bibendum. Nunc pharetra tincidunt urna. Suspendisse dignissim dui quis dolor fringilla porttitor. Morbi pellentesque eros quis lacus tristique maximus. Suspendisse laoreet sagittis ultrices.Pellentesque sit amet pellentesque felis.</p>\n<p><br></p>\n<h2>This is an H2 (medium) heading</h2>\n<p>Phasellus ex massa, hendrerit porta hendrerit a, pretium et justo. <ins>Vivamus eget dui sed justo consequat malesuada. Integer a commodo augue.</ins> Morbi rutrum suscipit efficitur. Vivamus ac libero ullamcorper, rhoncus nulla at, accumsan tellus. In hac habitasse platea dictumst. Donec maximus ex a faucibus commodo. In vel eros non diam pellentesque maximus. Curabitur fermentum accumsan lectus, ut aliquam ipsum pulvinar quis. Vestibulum ante ipsum primis in faucibus orci luctus et ultrices posuere cubilia Curae;Nam convallis egestas consectetur. Ut ac eleifend enim, a efficitur magna. Sed cursus ornare finibus. Mauris quis tincidunt justo. Cras efficitur, enim non pharetra ultrices, eros augue eleifend nisl, at congue elit leo quis arcu. Sed luctus, nibh vitae efficitur maximus, turpis ante porta diam, facilisis ultrices dui sem sed libero. Nulla pulvinar nisi eget cursus eleifend. Aliquam erat volutpat. Integer tortor nulla, auctor vitae vestibulum ut, sagittis sed velit. Integer a luctus arcu. Nam congue et elit sit amet porta. Cras euismod ipsum massa, quis elementum ligula lobortis quis. Mauris eu augue efficitur, feugiat augue non, aliquam ligula.Nulla a orci a felis mollis scelerisque. Pellentesque neque velit, faucibus nec mi eu, commodo tincidunt risus.</p>\n<p><br></p>\n<h3>This is an H3 (small) heading</h3>\n<p>Sed tempus justo leo, non sollicitudin mi eleifend a. Curabitur sed diam pulvinar, dictum nisl ut, blandit metus. Maecenas non sem quis ligula commodo egestas. Integer malesuada eleifend est, in commodo eros fermentum sed. Maecenas commodo nibh quis porttitor vehicula. Aenean blandit rutrum dolor, non ullamcorper est aliquam ac.Etiam interdum semper tempor. Phasellus condimentum massa eu libero sagittis cursus. Sed at lorem vel nulla elementum fringilla nec at eros. Aenean facilisis scelerisque tortor, non malesuada arcu scelerisque a. Ut est ante, iaculis at ultricies non, molestie placerat leo. Cras ullamcorper pellentesque erat in blandit. Nunc tortor ligula, fringilla ac risus quis, venenatis iaculis quam. Aliquam eget ex vitae ligula imperdiet finibus. Nullam ex metus, placerat ac arcu non, imperdiet consequat tortor. Donec varius elementum odio et rutrum. Sed in aliquam eros, sed sagittis erat. Vivamus tristique congue dictum. Proin tincidunt quis neque eget aliquam. Morbi sollicitudin orci lectus, a vulputate turpis porta a. Fusce facilisis ullamcorper dui in consequat.</p>\n<p><br></p>\n<h3>Code block follows</h3>\n<pre><code>Sed vitae convallis sapien, mollis fermentum ex.Curabitur rhoncus leo accumsan eros scelerisque, eget rhoncus augue porttitor. Praesent pretium mattis nibh, sit amet euismod nulla suscipit nec. Proin vehicula felis sit amet libero tempor, faucibus ultrices leo laoreet. Phasellus ultricies sapien urna, eget fringilla turpis rutrum vel. Donec nec nisl ultricies, lacinia diam in, finibus elit. Maecenas et felis eu lectus ultricies vestibulum. Aliquam accumsan efficitur lectus ut consequat. Sed quis aliquet justo, ut convallis eros.Vivamus vestibulum quam dictum orci aliquam, eget tincidunt est tincidunt. Curabitur pretium ut elit eget aliquet. Sed rhoncus metus sapien, eget malesuada ex dictum eu. Quisque auctor magna nibh, vel sollicitudin dui cursus sit amet.</code></pre>\n<p>In laoreet faucibus lorem vel fringilla. Sed et dolor sem. Proin velit augue, condimentum in enim sed, finibus tincidunt purus. Maecenas efficitur, lacus finibus vulputate luctus, urna eros iaculis lacus, a cursus lacus metus sit amet lacus. Maecenas porttitor imperdiet magna, et scelerisque nunc ornare nec. Integer consequat hendrerit neque, sed condimentum velit commodo a.</p>\n<p><br></p>\n<h3>Unordered list:</h3>\n<p>Praesent ultricies commodo arcu, at vulputate metus rutrum ut.Etiam vel ante vel nulla pellentesque aliquam sed at erat. In faucibus ac leo a dignissim. Donec augue lorem, sagittis sed tempus et, auctor vitae risus:</p>\n<ul>\n  <li>Fusce vel bibendum felis.</li>\n  <li>Phasellus vitae diam felis. Nulla rhoncus felis sit amet fringilla tincidunt. Pellentesque vestibulum, est non congue hendrerit, elit leo bibendum mauris, a malesuada quam massa ut lectus.</li>\n  <li>Vestibulum nec ornare neque.</li>\n  <li>Nunc mattis ex in vestibulum dapibus.</li>\n  <li>Quisque cursus lacus dui, consequat viverra purus lobortis ac. In hac habitasse platea dictumst.</li>\n</ul>\n<h3><br></h3>\n<h3>Ordered list:</h3>\n<p>Mauris sollicitudin ligula vitae erat mollis, a hendrerit mi molestie. Proin sit amet diam quis dolor ornare lacinia eu ut dui. In vitae congue diam. Aenean pharetra feugiat nulla, in ultrices nisl venenatis non. Donec nulla turpis, commodo eget pretium non, auctor vestibulum nibh:</p>\n<ol>\n  <li>Donec sit amet sodales augue. Ut et odio at magna tempus interdum quis ut mauris.</li>\n  <li>Nullam tristique semper condimentum.</li>\n  <li>Sed sollicitudin lacus at felis vehicula bibendum. Nunc pharetra tincidunt urna.</li>\n  <li>Suspendisse dignissim dui quis dolor fringilla porttitor.</li>\n  <li>Morbi pellentesque eros quis lacus tristique maximus. Suspendisse laoreet sagittis ultrices.</li>\n</ol>",
                    "margin-top":"marg-t-30",
                    "margin-bottom":"marg-b-100",
                    "margin-left":"marg-l-0",
                    "margin-right":"marg-r-0"
                  }
                }
              ]
            }
          }
        ]
      },
      "blog":{
        "content":[
          {
            "element-type":"layout-50:50",
            "element-path":"page-builder/layouts/_two-col-50-50.html",
            "options":{
              "layout-bg-image":"",
              "bg-color":"#34495e",
              "margin-right":"marg-r-0",
              "margin-bottom":"marg-b-0",
              "layout-bg-image-size":"bg-img-size--cover",
              "text-color":"#000",
              "margin-top":"marg-t-0",
              "padding-right":"padd-r-0",
              "margin-left":"marg-l-0",
              "padding-bottom":"padd-b-50",
              "align-content":"align-content-center",
              "text-alignment":"text-align--left",
              "padding-top":"padd-t-200",
              "padding-left":"padd-l-0"
            },
            "children":{
              "column-1":[
                {
                  "element-type":"heading",
                  "element-path":"page-builder/elements/_heading.html",
                  "options":{
                    "font-size":"font-size--48px",
                    "margin-right":"marg-r-0",
                    "margin-bottom":"marg-b-20",
                    "text-color":"#ffffff",
                    "margin-top":"marg-t-0",
                    "margin-left":"marg-l-0",
                    "text-content":"This is an example title of the static page",
                    "font-family":"font--primary--regular",
                    "text-alignment":"text-align--left"
                  }
                },
                {
                  "element-type":"paragraph-text",
                  "element-path":"page-builder/elements/_paragraph.html",
                  "options":{
                    "font-size":"font-size--18px",
                    "margin-right":"marg-r-0",
                    "margin-bottom":"marg-b-5",
                    "text-color":"#ffffff",
                    "margin-top":"marg-t-5",
                    "margin-left":"marg-l-0",
                    "text-content":"Vivamus scelerisque odio ut lectus luctus, eget viverra leo aliquet.",
                    "font-family":"font--primary--regular",
                    "text-alignment":"text-align--left"
                  }
                }
              ],
              "column-2":[]
            }
          },
          {
            "element-type":"layout-single-col",
            "element-path":"page-builder/layouts/_single-col.html",
            "options":{
              "layout-bg-image":"",
              "bg-color":"#fff",
              "margin-right":"marg-r-0",
              "margin-bottom":"marg-b-0",
              "layout-bg-image-size":"bg-img-size--cover",
              "text-color":"#000",
              "margin-top":"marg-t-0",
              "padding-right":"padd-r-0",
              "margin-left":"marg-l-0",
              "padding-bottom":"padd-b-20",
              "align-content":"align-content-center",
              "text-alignment":"text-align--left",
              "padding-top":"padd-t-20",
              "padding-left":"padd-l-0"
            },
            "children":{
              "column-1":[
                {
                  "element-type":"content-block",
                  "element-path":"page-builder/elements/_content-block.html",
                  "options":{
                    "content":"<p>Lorem ipsum dolor sit amet, consectetur adipiscing elit. <a href=\"#\">Mauris libero nulla</a>, sagittis at erat non, commodo porta nunc. Donec ultrices erat vel vehicula posuere. Morbi a justo metus. Ut et libero congue, interdum diam sit amet, scelerisque massa. Sed non purus mi. Fusce posuere vel ante eu tempus.<em> Integer interdum libero libero, sit amet fermentum nisl pretium ac. In suscipit, elit eget vulputate bibendum, arcu libero </em><em><strong>tristique</strong></em><em> diam, ut fringilla augue est in neque.</em> Suspendisse consequat ex non lacinia sodales.In feugiat eu erat non interdum. <del>Donec nec accumsan augue.</del> Sed consequat quis mauris ut interdum. Aliquam porttitor risus egestas, maximus quam a, cursus erat. Donec in sem ligula. Sed non convallis dui. Phasellus scelerisque maximus vestibulum.</p>\n<p><br></p>\n<h1>This is an H1 (large) heading</h1>\n<p>Fusce nunc est, euismod sit amet vehicula non, facilisis eu purus. Curabitur cursus et neque nec fringilla. Phasellus aliquam pulvinar risus. Praesent magna sem, consequat ut quam at, euismod maximus ipsum. Vestibulum porttitor blandit ultrices. <strong>Nam tempus hendrerit</strong> ipsum vitae elementum. Suspendisse sit amet eleifend tellus. Pellentesque habitant morbi tristique senectus et netus et malesuada fames ac turpis egestas. Aenean nec aliquam leo.Mauris sollicitudin ligula vitae erat mollis, a hendrerit mi molestie. Proin sit amet diam quis dolor ornare lacinia eu ut dui. In vitae congue diam. Aenean pharetra feugiat nulla, in ultrices nisl venenatis non. Donec nulla turpis, commodo eget pretium non, auctor vestibulum nibh. Donec sit amet sodales augue. Ut et odio at magna tempus interdum quis ut mauris. Nullam tristique semper condimentum. Sed sollicitudin lacus at felis vehicula bibendum. Nunc pharetra tincidunt urna. Suspendisse dignissim dui quis dolor fringilla porttitor. Morbi pellentesque eros quis lacus tristique maximus. Suspendisse laoreet sagittis ultrices.Pellentesque sit amet pellentesque felis.</p>\n<p><br></p>\n<h2>This is an H2 (medium) heading</h2>\n<p>Phasellus ex massa, hendrerit porta hendrerit a, pretium et justo. <ins>Vivamus eget dui sed justo consequat malesuada. Integer a commodo augue.</ins> Morbi rutrum suscipit efficitur. Vivamus ac libero ullamcorper, rhoncus nulla at, accumsan tellus. In hac habitasse platea dictumst. Donec maximus ex a faucibus commodo. In vel eros non diam pellentesque maximus. Curabitur fermentum accumsan lectus, ut aliquam ipsum pulvinar quis. Vestibulum ante ipsum primis in faucibus orci luctus et ultrices posuere cubilia Curae;Nam convallis egestas consectetur. Ut ac eleifend enim, a efficitur magna. Sed cursus ornare finibus. Mauris quis tincidunt justo. Cras efficitur, enim non pharetra ultrices, eros augue eleifend nisl, at congue elit leo quis arcu. Sed luctus, nibh vitae efficitur maximus, turpis ante porta diam, facilisis ultrices dui sem sed libero. Nulla pulvinar nisi eget cursus eleifend. Aliquam erat volutpat. Integer tortor nulla, auctor vitae vestibulum ut, sagittis sed velit. Integer a luctus arcu. Nam congue et elit sit amet porta. Cras euismod ipsum massa, quis elementum ligula lobortis quis. Mauris eu augue efficitur, feugiat augue non, aliquam ligula.Nulla a orci a felis mollis scelerisque. Pellentesque neque velit, faucibus nec mi eu, commodo tincidunt risus.</p>\n<p><br></p>\n<h3>This is an H3 (small) heading</h3>\n<p>Sed tempus justo leo, non sollicitudin mi eleifend a. Curabitur sed diam pulvinar, dictum nisl ut, blandit metus. Maecenas non sem quis ligula commodo egestas. Integer malesuada eleifend est, in commodo eros fermentum sed. Maecenas commodo nibh quis porttitor vehicula. Aenean blandit rutrum dolor, non ullamcorper est aliquam ac.Etiam interdum semper tempor. Phasellus condimentum massa eu libero sagittis cursus. Sed at lorem vel nulla elementum fringilla nec at eros. Aenean facilisis scelerisque tortor, non malesuada arcu scelerisque a. Ut est ante, iaculis at ultricies non, molestie placerat leo. Cras ullamcorper pellentesque erat in blandit. Nunc tortor ligula, fringilla ac risus quis, venenatis iaculis quam. Aliquam eget ex vitae ligula imperdiet finibus. Nullam ex metus, placerat ac arcu non, imperdiet consequat tortor. Donec varius elementum odio et rutrum. Sed in aliquam eros, sed sagittis erat. Vivamus tristique congue dictum. Proin tincidunt quis neque eget aliquam. Morbi sollicitudin orci lectus, a vulputate turpis porta a. Fusce facilisis ullamcorper dui in consequat.</p>\n<p><br></p>\n<h3>Code block follows</h3>\n<pre><code>Sed vitae convallis sapien, mollis fermentum ex.Curabitur rhoncus leo accumsan eros scelerisque, eget rhoncus augue porttitor. Praesent pretium mattis nibh, sit amet euismod nulla suscipit nec. Proin vehicula felis sit amet libero tempor, faucibus ultrices leo laoreet. Phasellus ultricies sapien urna, eget fringilla turpis rutrum vel. Donec nec nisl ultricies, lacinia diam in, finibus elit. Maecenas et felis eu lectus ultricies vestibulum. Aliquam accumsan efficitur lectus ut consequat. Sed quis aliquet justo, ut convallis eros.Vivamus vestibulum quam dictum orci aliquam, eget tincidunt est tincidunt. Curabitur pretium ut elit eget aliquet. Sed rhoncus metus sapien, eget malesuada ex dictum eu. Quisque auctor magna nibh, vel sollicitudin dui cursus sit amet.</code></pre>\n<p>In laoreet faucibus lorem vel fringilla. Sed et dolor sem. Proin velit augue, condimentum in enim sed, finibus tincidunt purus. Maecenas efficitur, lacus finibus vulputate luctus, urna eros iaculis lacus, a cursus lacus metus sit amet lacus. Maecenas porttitor imperdiet magna, et scelerisque nunc ornare nec. Integer consequat hendrerit neque, sed condimentum velit commodo a.</p>\n<p><br></p>\n<h3>Unordered list:</h3>\n<p>Praesent ultricies commodo arcu, at vulputate metus rutrum ut.Etiam vel ante vel nulla pellentesque aliquam sed at erat. In faucibus ac leo a dignissim. Donec augue lorem, sagittis sed tempus et, auctor vitae risus:</p>\n<ul>\n  <li>Fusce vel bibendum felis.</li>\n  <li>Phasellus vitae diam felis. Nulla rhoncus felis sit amet fringilla tincidunt. Pellentesque vestibulum, est non congue hendrerit, elit leo bibendum mauris, a malesuada quam massa ut lectus.</li>\n  <li>Vestibulum nec ornare neque.</li>\n  <li>Nunc mattis ex in vestibulum dapibus.</li>\n  <li>Quisque cursus lacus dui, consequat viverra purus lobortis ac. In hac habitasse platea dictumst.</li>\n</ul>\n<h3><br></h3>\n<h3>Ordered list:</h3>\n<p>Mauris sollicitudin ligula vitae erat mollis, a hendrerit mi molestie. Proin sit amet diam quis dolor ornare lacinia eu ut dui. In vitae congue diam. Aenean pharetra feugiat nulla, in ultrices nisl venenatis non. Donec nulla turpis, commodo eget pretium non, auctor vestibulum nibh:</p>\n<ol>\n  <li>Donec sit amet sodales augue. Ut et odio at magna tempus interdum quis ut mauris.</li>\n  <li>Nullam tristique semper condimentum.</li>\n  <li>Sed sollicitudin lacus at felis vehicula bibendum. Nunc pharetra tincidunt urna.</li>\n  <li>Suspendisse dignissim dui quis dolor fringilla porttitor.</li>\n  <li>Morbi pellentesque eros quis lacus tristique maximus. Suspendisse laoreet sagittis ultrices.</li>\n</ol>",
                    "margin-top":"marg-t-30",
                    "margin-bottom":"marg-b-100",
                    "margin-left":"marg-l-0",
                    "margin-right":"marg-r-0"
                  }
                }
              ]
            }
          }
        ]
      },
      "courses":{
        "content":[
          {
            "element-type":"course-catalogue-template",
            "element-path":"design-templates/pages/course-catalogue/_course-catalogue-01.html",
            "options":{
              "discovery-facet-option":"facet_option-01",
              "course-card":"course-tile-01",
              "search-enabled":True,
              "discovery-facet":"facet-01"
            }
          }
        ]
      },
      "contact":{
        "content":[
          {
            "element-type":"layout-50:50",
            "element-path":"page-builder/layouts/_two-col-50-50.html",
            "options":{
              "layout-bg-image":"",
              "bg-color":"#34495e",
              "margin-right":"marg-r-0",
              "margin-bottom":"marg-b-0",
              "layout-bg-image-size":"bg-img-size--cover",
              "text-color":"#000",
              "margin-top":"marg-t-0",
              "padding-right":"padd-r-0",
              "margin-left":"marg-l-0",
              "padding-bottom":"padd-b-50",
              "align-content":"align-content-center",
              "text-alignment":"text-align--left",
              "padding-top":"padd-t-200",
              "padding-left":"padd-l-0"
            },
            "children":{
              "column-1":[
                {
                  "element-type":"heading",
                  "element-path":"page-builder/elements/_heading.html",
                  "options":{
                    "font-size":"font-size--48px",
                    "margin-right":"marg-r-0",
                    "margin-bottom":"marg-b-20",
                    "text-color":"#ffffff",
                    "margin-top":"marg-t-0",
                    "margin-left":"marg-l-0",
                    "text-content":"This is an example title of the static page",
                    "font-family":"font--primary--regular",
                    "text-alignment":"text-align--left"
                  }
                },
                {
                  "element-type":"paragraph-text",
                  "element-path":"page-builder/elements/_paragraph.html",
                  "options":{
                    "font-size":"font-size--18px",
                    "margin-right":"marg-r-0",
                    "margin-bottom":"marg-b-5",
                    "text-color":"#ffffff",
                    "margin-top":"marg-t-5",
                    "margin-left":"marg-l-0",
                    "text-content":"Vivamus scelerisque odio ut lectus luctus, eget viverra leo aliquet.",
                    "font-family":"font--primary--regular",
                    "text-alignment":"text-align--left"
                  }
                }
              ],
              "column-2":[]
            }
          },
          {
            "element-type":"layout-single-col",
            "element-path":"page-builder/layouts/_single-col.html",
            "options":{
              "layout-bg-image":"",
              "bg-color":"#fff",
              "margin-right":"marg-r-0",
              "margin-bottom":"marg-b-0",
              "layout-bg-image-size":"bg-img-size--cover",
              "text-color":"#000",
              "margin-top":"marg-t-0",
              "padding-right":"padd-r-0",
              "margin-left":"marg-l-0",
              "padding-bottom":"padd-b-20",
              "align-content":"align-content-center",
              "text-alignment":"text-align--left",
              "padding-top":"padd-t-20",
              "padding-left":"padd-l-0"
            },
            "children":{
              "column-1":[
                {
                  "element-type":"content-block",
                  "element-path":"page-builder/elements/_content-block.html",
                  "options":{
                    "content":"<p>Lorem ipsum dolor sit amet, consectetur adipiscing elit. <a href=\"#\">Mauris libero nulla</a>, sagittis at erat non, commodo porta nunc. Donec ultrices erat vel vehicula posuere. Morbi a justo metus. Ut et libero congue, interdum diam sit amet, scelerisque massa. Sed non purus mi. Fusce posuere vel ante eu tempus.<em> Integer interdum libero libero, sit amet fermentum nisl pretium ac. In suscipit, elit eget vulputate bibendum, arcu libero </em><em><strong>tristique</strong></em><em> diam, ut fringilla augue est in neque.</em> Suspendisse consequat ex non lacinia sodales.In feugiat eu erat non interdum. <del>Donec nec accumsan augue.</del> Sed consequat quis mauris ut interdum. Aliquam porttitor risus egestas, maximus quam a, cursus erat. Donec in sem ligula. Sed non convallis dui. Phasellus scelerisque maximus vestibulum.</p>\n<p><br></p>\n<h1>This is an H1 (large) heading</h1>\n<p>Fusce nunc est, euismod sit amet vehicula non, facilisis eu purus. Curabitur cursus et neque nec fringilla. Phasellus aliquam pulvinar risus. Praesent magna sem, consequat ut quam at, euismod maximus ipsum. Vestibulum porttitor blandit ultrices. <strong>Nam tempus hendrerit</strong> ipsum vitae elementum. Suspendisse sit amet eleifend tellus. Pellentesque habitant morbi tristique senectus et netus et malesuada fames ac turpis egestas. Aenean nec aliquam leo.Mauris sollicitudin ligula vitae erat mollis, a hendrerit mi molestie. Proin sit amet diam quis dolor ornare lacinia eu ut dui. In vitae congue diam. Aenean pharetra feugiat nulla, in ultrices nisl venenatis non. Donec nulla turpis, commodo eget pretium non, auctor vestibulum nibh. Donec sit amet sodales augue. Ut et odio at magna tempus interdum quis ut mauris. Nullam tristique semper condimentum. Sed sollicitudin lacus at felis vehicula bibendum. Nunc pharetra tincidunt urna. Suspendisse dignissim dui quis dolor fringilla porttitor. Morbi pellentesque eros quis lacus tristique maximus. Suspendisse laoreet sagittis ultrices.Pellentesque sit amet pellentesque felis.</p>\n<p><br></p>\n<h2>This is an H2 (medium) heading</h2>\n<p>Phasellus ex massa, hendrerit porta hendrerit a, pretium et justo. <ins>Vivamus eget dui sed justo consequat malesuada. Integer a commodo augue.</ins> Morbi rutrum suscipit efficitur. Vivamus ac libero ullamcorper, rhoncus nulla at, accumsan tellus. In hac habitasse platea dictumst. Donec maximus ex a faucibus commodo. In vel eros non diam pellentesque maximus. Curabitur fermentum accumsan lectus, ut aliquam ipsum pulvinar quis. Vestibulum ante ipsum primis in faucibus orci luctus et ultrices posuere cubilia Curae;Nam convallis egestas consectetur. Ut ac eleifend enim, a efficitur magna. Sed cursus ornare finibus. Mauris quis tincidunt justo. Cras efficitur, enim non pharetra ultrices, eros augue eleifend nisl, at congue elit leo quis arcu. Sed luctus, nibh vitae efficitur maximus, turpis ante porta diam, facilisis ultrices dui sem sed libero. Nulla pulvinar nisi eget cursus eleifend. Aliquam erat volutpat. Integer tortor nulla, auctor vitae vestibulum ut, sagittis sed velit. Integer a luctus arcu. Nam congue et elit sit amet porta. Cras euismod ipsum massa, quis elementum ligula lobortis quis. Mauris eu augue efficitur, feugiat augue non, aliquam ligula.Nulla a orci a felis mollis scelerisque. Pellentesque neque velit, faucibus nec mi eu, commodo tincidunt risus.</p>\n<p><br></p>\n<h3>This is an H3 (small) heading</h3>\n<p>Sed tempus justo leo, non sollicitudin mi eleifend a. Curabitur sed diam pulvinar, dictum nisl ut, blandit metus. Maecenas non sem quis ligula commodo egestas. Integer malesuada eleifend est, in commodo eros fermentum sed. Maecenas commodo nibh quis porttitor vehicula. Aenean blandit rutrum dolor, non ullamcorper est aliquam ac.Etiam interdum semper tempor. Phasellus condimentum massa eu libero sagittis cursus. Sed at lorem vel nulla elementum fringilla nec at eros. Aenean facilisis scelerisque tortor, non malesuada arcu scelerisque a. Ut est ante, iaculis at ultricies non, molestie placerat leo. Cras ullamcorper pellentesque erat in blandit. Nunc tortor ligula, fringilla ac risus quis, venenatis iaculis quam. Aliquam eget ex vitae ligula imperdiet finibus. Nullam ex metus, placerat ac arcu non, imperdiet consequat tortor. Donec varius elementum odio et rutrum. Sed in aliquam eros, sed sagittis erat. Vivamus tristique congue dictum. Proin tincidunt quis neque eget aliquam. Morbi sollicitudin orci lectus, a vulputate turpis porta a. Fusce facilisis ullamcorper dui in consequat.</p>\n<p><br></p>\n<h3>Code block follows</h3>\n<pre><code>Sed vitae convallis sapien, mollis fermentum ex.Curabitur rhoncus leo accumsan eros scelerisque, eget rhoncus augue porttitor. Praesent pretium mattis nibh, sit amet euismod nulla suscipit nec. Proin vehicula felis sit amet libero tempor, faucibus ultrices leo laoreet. Phasellus ultricies sapien urna, eget fringilla turpis rutrum vel. Donec nec nisl ultricies, lacinia diam in, finibus elit. Maecenas et felis eu lectus ultricies vestibulum. Aliquam accumsan efficitur lectus ut consequat. Sed quis aliquet justo, ut convallis eros.Vivamus vestibulum quam dictum orci aliquam, eget tincidunt est tincidunt. Curabitur pretium ut elit eget aliquet. Sed rhoncus metus sapien, eget malesuada ex dictum eu. Quisque auctor magna nibh, vel sollicitudin dui cursus sit amet.</code></pre>\n<p>In laoreet faucibus lorem vel fringilla. Sed et dolor sem. Proin velit augue, condimentum in enim sed, finibus tincidunt purus. Maecenas efficitur, lacus finibus vulputate luctus, urna eros iaculis lacus, a cursus lacus metus sit amet lacus. Maecenas porttitor imperdiet magna, et scelerisque nunc ornare nec. Integer consequat hendrerit neque, sed condimentum velit commodo a.</p>\n<p><br></p>\n<h3>Unordered list:</h3>\n<p>Praesent ultricies commodo arcu, at vulputate metus rutrum ut.Etiam vel ante vel nulla pellentesque aliquam sed at erat. In faucibus ac leo a dignissim. Donec augue lorem, sagittis sed tempus et, auctor vitae risus:</p>\n<ul>\n  <li>Fusce vel bibendum felis.</li>\n  <li>Phasellus vitae diam felis. Nulla rhoncus felis sit amet fringilla tincidunt. Pellentesque vestibulum, est non congue hendrerit, elit leo bibendum mauris, a malesuada quam massa ut lectus.</li>\n  <li>Vestibulum nec ornare neque.</li>\n  <li>Nunc mattis ex in vestibulum dapibus.</li>\n  <li>Quisque cursus lacus dui, consequat viverra purus lobortis ac. In hac habitasse platea dictumst.</li>\n</ul>\n<h3><br></h3>\n<h3>Ordered list:</h3>\n<p>Mauris sollicitudin ligula vitae erat mollis, a hendrerit mi molestie. Proin sit amet diam quis dolor ornare lacinia eu ut dui. In vitae congue diam. Aenean pharetra feugiat nulla, in ultrices nisl venenatis non. Donec nulla turpis, commodo eget pretium non, auctor vestibulum nibh:</p>\n<ol>\n  <li>Donec sit amet sodales augue. Ut et odio at magna tempus interdum quis ut mauris.</li>\n  <li>Nullam tristique semper condimentum.</li>\n  <li>Sed sollicitudin lacus at felis vehicula bibendum. Nunc pharetra tincidunt urna.</li>\n  <li>Suspendisse dignissim dui quis dolor fringilla porttitor.</li>\n  <li>Morbi pellentesque eros quis lacus tristique maximus. Suspendisse laoreet sagittis ultrices.</li>\n</ol>",
                    "margin-top":"marg-t-30",
                    "margin-bottom":"marg-b-100",
                    "margin-left":"marg-l-0",
                    "margin-right":"marg-r-0"
                  }
                }
              ]
            }
          }
        ]
      },
      "tos":{
        "content":[
          {
            "element-type":"layout-50:50",
            "element-path":"page-builder/layouts/_two-col-50-50.html",
            "options":{
              "layout-bg-image":"",
              "bg-color":"#34495e",
              "margin-right":"marg-r-0",
              "margin-bottom":"marg-b-0",
              "layout-bg-image-size":"bg-img-size--cover",
              "text-color":"#000",
              "margin-top":"marg-t-0",
              "padding-right":"padd-r-0",
              "margin-left":"marg-l-0",
              "padding-bottom":"padd-b-50",
              "align-content":"align-content-center",
              "text-alignment":"text-align--left",
              "padding-top":"padd-t-200",
              "padding-left":"padd-l-0"
            },
            "children":{
              "column-1":[
                {
                  "element-type":"heading",
                  "element-path":"page-builder/elements/_heading.html",
                  "options":{
                    "font-size":"font-size--48px",
                    "margin-right":"marg-r-0",
                    "margin-bottom":"marg-b-20",
                    "text-color":"#ffffff",
                    "margin-top":"marg-t-0",
                    "margin-left":"marg-l-0",
                    "text-content":"This is an example title of the static page",
                    "font-family":"font--primary--regular",
                    "text-alignment":"text-align--left"
                  }
                },
                {
                  "element-type":"paragraph-text",
                  "element-path":"page-builder/elements/_paragraph.html",
                  "options":{
                    "font-size":"font-size--18px",
                    "margin-right":"marg-r-0",
                    "margin-bottom":"marg-b-5",
                    "text-color":"#ffffff",
                    "margin-top":"marg-t-5",
                    "margin-left":"marg-l-0",
                    "text-content":"Vivamus scelerisque odio ut lectus luctus, eget viverra leo aliquet.",
                    "font-family":"font--primary--regular",
                    "text-alignment":"text-align--left"
                  }
                }
              ],
              "column-2":[]
            }
          },
          {
            "element-type":"layout-single-col",
            "element-path":"page-builder/layouts/_single-col.html",
            "options":{
              "layout-bg-image":"",
              "bg-color":"#fff",
              "margin-right":"marg-r-0",
              "margin-bottom":"marg-b-0",
              "layout-bg-image-size":"bg-img-size--cover",
              "text-color":"#000",
              "margin-top":"marg-t-0",
              "padding-right":"padd-r-0",
              "margin-left":"marg-l-0",
              "padding-bottom":"padd-b-20",
              "align-content":"align-content-center",
              "text-alignment":"text-align--left",
              "padding-top":"padd-t-20",
              "padding-left":"padd-l-0"
            },
            "children":{
              "column-1":[
                {
                  "element-type":"content-block",
                  "element-path":"page-builder/elements/_content-block.html",
                  "options":{
                    "content":"<p>Lorem ipsum dolor sit amet, consectetur adipiscing elit. <a href=\"#\">Mauris libero nulla</a>, sagittis at erat non, commodo porta nunc. Donec ultrices erat vel vehicula posuere. Morbi a justo metus. Ut et libero congue, interdum diam sit amet, scelerisque massa. Sed non purus mi. Fusce posuere vel ante eu tempus.<em> Integer interdum libero libero, sit amet fermentum nisl pretium ac. In suscipit, elit eget vulputate bibendum, arcu libero </em><em><strong>tristique</strong></em><em> diam, ut fringilla augue est in neque.</em> Suspendisse consequat ex non lacinia sodales.In feugiat eu erat non interdum. <del>Donec nec accumsan augue.</del> Sed consequat quis mauris ut interdum. Aliquam porttitor risus egestas, maximus quam a, cursus erat. Donec in sem ligula. Sed non convallis dui. Phasellus scelerisque maximus vestibulum.</p>\n<p><br></p>\n<h1>This is an H1 (large) heading</h1>\n<p>Fusce nunc est, euismod sit amet vehicula non, facilisis eu purus. Curabitur cursus et neque nec fringilla. Phasellus aliquam pulvinar risus. Praesent magna sem, consequat ut quam at, euismod maximus ipsum. Vestibulum porttitor blandit ultrices. <strong>Nam tempus hendrerit</strong> ipsum vitae elementum. Suspendisse sit amet eleifend tellus. Pellentesque habitant morbi tristique senectus et netus et malesuada fames ac turpis egestas. Aenean nec aliquam leo.Mauris sollicitudin ligula vitae erat mollis, a hendrerit mi molestie. Proin sit amet diam quis dolor ornare lacinia eu ut dui. In vitae congue diam. Aenean pharetra feugiat nulla, in ultrices nisl venenatis non. Donec nulla turpis, commodo eget pretium non, auctor vestibulum nibh. Donec sit amet sodales augue. Ut et odio at magna tempus interdum quis ut mauris. Nullam tristique semper condimentum. Sed sollicitudin lacus at felis vehicula bibendum. Nunc pharetra tincidunt urna. Suspendisse dignissim dui quis dolor fringilla porttitor. Morbi pellentesque eros quis lacus tristique maximus. Suspendisse laoreet sagittis ultrices.Pellentesque sit amet pellentesque felis.</p>\n<p><br></p>\n<h2>This is an H2 (medium) heading</h2>\n<p>Phasellus ex massa, hendrerit porta hendrerit a, pretium et justo. <ins>Vivamus eget dui sed justo consequat malesuada. Integer a commodo augue.</ins> Morbi rutrum suscipit efficitur. Vivamus ac libero ullamcorper, rhoncus nulla at, accumsan tellus. In hac habitasse platea dictumst. Donec maximus ex a faucibus commodo. In vel eros non diam pellentesque maximus. Curabitur fermentum accumsan lectus, ut aliquam ipsum pulvinar quis. Vestibulum ante ipsum primis in faucibus orci luctus et ultrices posuere cubilia Curae;Nam convallis egestas consectetur. Ut ac eleifend enim, a efficitur magna. Sed cursus ornare finibus. Mauris quis tincidunt justo. Cras efficitur, enim non pharetra ultrices, eros augue eleifend nisl, at congue elit leo quis arcu. Sed luctus, nibh vitae efficitur maximus, turpis ante porta diam, facilisis ultrices dui sem sed libero. Nulla pulvinar nisi eget cursus eleifend. Aliquam erat volutpat. Integer tortor nulla, auctor vitae vestibulum ut, sagittis sed velit. Integer a luctus arcu. Nam congue et elit sit amet porta. Cras euismod ipsum massa, quis elementum ligula lobortis quis. Mauris eu augue efficitur, feugiat augue non, aliquam ligula.Nulla a orci a felis mollis scelerisque. Pellentesque neque velit, faucibus nec mi eu, commodo tincidunt risus.</p>\n<p><br></p>\n<h3>This is an H3 (small) heading</h3>\n<p>Sed tempus justo leo, non sollicitudin mi eleifend a. Curabitur sed diam pulvinar, dictum nisl ut, blandit metus. Maecenas non sem quis ligula commodo egestas. Integer malesuada eleifend est, in commodo eros fermentum sed. Maecenas commodo nibh quis porttitor vehicula. Aenean blandit rutrum dolor, non ullamcorper est aliquam ac.Etiam interdum semper tempor. Phasellus condimentum massa eu libero sagittis cursus. Sed at lorem vel nulla elementum fringilla nec at eros. Aenean facilisis scelerisque tortor, non malesuada arcu scelerisque a. Ut est ante, iaculis at ultricies non, molestie placerat leo. Cras ullamcorper pellentesque erat in blandit. Nunc tortor ligula, fringilla ac risus quis, venenatis iaculis quam. Aliquam eget ex vitae ligula imperdiet finibus. Nullam ex metus, placerat ac arcu non, imperdiet consequat tortor. Donec varius elementum odio et rutrum. Sed in aliquam eros, sed sagittis erat. Vivamus tristique congue dictum. Proin tincidunt quis neque eget aliquam. Morbi sollicitudin orci lectus, a vulputate turpis porta a. Fusce facilisis ullamcorper dui in consequat.</p>\n<p><br></p>\n<h3>Code block follows</h3>\n<pre><code>Sed vitae convallis sapien, mollis fermentum ex.Curabitur rhoncus leo accumsan eros scelerisque, eget rhoncus augue porttitor. Praesent pretium mattis nibh, sit amet euismod nulla suscipit nec. Proin vehicula felis sit amet libero tempor, faucibus ultrices leo laoreet. Phasellus ultricies sapien urna, eget fringilla turpis rutrum vel. Donec nec nisl ultricies, lacinia diam in, finibus elit. Maecenas et felis eu lectus ultricies vestibulum. Aliquam accumsan efficitur lectus ut consequat. Sed quis aliquet justo, ut convallis eros.Vivamus vestibulum quam dictum orci aliquam, eget tincidunt est tincidunt. Curabitur pretium ut elit eget aliquet. Sed rhoncus metus sapien, eget malesuada ex dictum eu. Quisque auctor magna nibh, vel sollicitudin dui cursus sit amet.</code></pre>\n<p>In laoreet faucibus lorem vel fringilla. Sed et dolor sem. Proin velit augue, condimentum in enim sed, finibus tincidunt purus. Maecenas efficitur, lacus finibus vulputate luctus, urna eros iaculis lacus, a cursus lacus metus sit amet lacus. Maecenas porttitor imperdiet magna, et scelerisque nunc ornare nec. Integer consequat hendrerit neque, sed condimentum velit commodo a.</p>\n<p><br></p>\n<h3>Unordered list:</h3>\n<p>Praesent ultricies commodo arcu, at vulputate metus rutrum ut.Etiam vel ante vel nulla pellentesque aliquam sed at erat. In faucibus ac leo a dignissim. Donec augue lorem, sagittis sed tempus et, auctor vitae risus:</p>\n<ul>\n  <li>Fusce vel bibendum felis.</li>\n  <li>Phasellus vitae diam felis. Nulla rhoncus felis sit amet fringilla tincidunt. Pellentesque vestibulum, est non congue hendrerit, elit leo bibendum mauris, a malesuada quam massa ut lectus.</li>\n  <li>Vestibulum nec ornare neque.</li>\n  <li>Nunc mattis ex in vestibulum dapibus.</li>\n  <li>Quisque cursus lacus dui, consequat viverra purus lobortis ac. In hac habitasse platea dictumst.</li>\n</ul>\n<h3><br></h3>\n<h3>Ordered list:</h3>\n<p>Mauris sollicitudin ligula vitae erat mollis, a hendrerit mi molestie. Proin sit amet diam quis dolor ornare lacinia eu ut dui. In vitae congue diam. Aenean pharetra feugiat nulla, in ultrices nisl venenatis non. Donec nulla turpis, commodo eget pretium non, auctor vestibulum nibh:</p>\n<ol>\n  <li>Donec sit amet sodales augue. Ut et odio at magna tempus interdum quis ut mauris.</li>\n  <li>Nullam tristique semper condimentum.</li>\n  <li>Sed sollicitudin lacus at felis vehicula bibendum. Nunc pharetra tincidunt urna.</li>\n  <li>Suspendisse dignissim dui quis dolor fringilla porttitor.</li>\n  <li>Morbi pellentesque eros quis lacus tristique maximus. Suspendisse laoreet sagittis ultrices.</li>\n</ol>",
                    "margin-top":"marg-t-30",
                    "margin-bottom":"marg-b-100",
                    "margin-left":"marg-l-0",
                    "margin-right":"marg-r-0"
                  }
                }
              ]
            }
          }
        ]
      },
      "press":{
        "content":[
          {
            "element-type":"layout-50:50",
            "element-path":"page-builder/layouts/_two-col-50-50.html",
            "options":{
              "layout-bg-image":"",
              "bg-color":"#34495e",
              "margin-right":"marg-r-0",
              "margin-bottom":"marg-b-0",
              "layout-bg-image-size":"bg-img-size--cover",
              "text-color":"#000",
              "margin-top":"marg-t-0",
              "padding-right":"padd-r-0",
              "margin-left":"marg-l-0",
              "padding-bottom":"padd-b-50",
              "align-content":"align-content-center",
              "text-alignment":"text-align--left",
              "padding-top":"padd-t-200",
              "padding-left":"padd-l-0"
            },
            "children":{
              "column-1":[
                {
                  "element-type":"heading",
                  "element-path":"page-builder/elements/_heading.html",
                  "options":{
                    "font-size":"font-size--48px",
                    "margin-right":"marg-r-0",
                    "margin-bottom":"marg-b-20",
                    "text-color":"#ffffff",
                    "margin-top":"marg-t-0",
                    "margin-left":"marg-l-0",
                    "text-content":"This is an example title of the static page",
                    "font-family":"font--primary--regular",
                    "text-alignment":"text-align--left"
                  }
                },
                {
                  "element-type":"paragraph-text",
                  "element-path":"page-builder/elements/_paragraph.html",
                  "options":{
                    "font-size":"font-size--18px",
                    "margin-right":"marg-r-0",
                    "margin-bottom":"marg-b-5",
                    "text-color":"#ffffff",
                    "margin-top":"marg-t-5",
                    "margin-left":"marg-l-0",
                    "text-content":"Vivamus scelerisque odio ut lectus luctus, eget viverra leo aliquet.",
                    "font-family":"font--primary--regular",
                    "text-alignment":"text-align--left"
                  }
                }
              ],
              "column-2":[]
            }
          },
          {
            "element-type":"layout-single-col",
            "element-path":"page-builder/layouts/_single-col.html",
            "options":{
              "layout-bg-image":"",
              "bg-color":"#fff",
              "margin-right":"marg-r-0",
              "margin-bottom":"marg-b-0",
              "layout-bg-image-size":"bg-img-size--cover",
              "text-color":"#000",
              "margin-top":"marg-t-0",
              "padding-right":"padd-r-0",
              "margin-left":"marg-l-0",
              "padding-bottom":"padd-b-20",
              "align-content":"align-content-center",
              "text-alignment":"text-align--left",
              "padding-top":"padd-t-20",
              "padding-left":"padd-l-0"
            },
            "children":{
              "column-1":[
                {
                  "element-type":"content-block",
                  "element-path":"page-builder/elements/_content-block.html",
                  "options":{
                    "content":"<p>Lorem ipsum dolor sit amet, consectetur adipiscing elit. <a href=\"#\">Mauris libero nulla</a>, sagittis at erat non, commodo porta nunc. Donec ultrices erat vel vehicula posuere. Morbi a justo metus. Ut et libero congue, interdum diam sit amet, scelerisque massa. Sed non purus mi. Fusce posuere vel ante eu tempus.<em> Integer interdum libero libero, sit amet fermentum nisl pretium ac. In suscipit, elit eget vulputate bibendum, arcu libero </em><em><strong>tristique</strong></em><em> diam, ut fringilla augue est in neque.</em> Suspendisse consequat ex non lacinia sodales.In feugiat eu erat non interdum. <del>Donec nec accumsan augue.</del> Sed consequat quis mauris ut interdum. Aliquam porttitor risus egestas, maximus quam a, cursus erat. Donec in sem ligula. Sed non convallis dui. Phasellus scelerisque maximus vestibulum.</p>\n<p><br></p>\n<h1>This is an H1 (large) heading</h1>\n<p>Fusce nunc est, euismod sit amet vehicula non, facilisis eu purus. Curabitur cursus et neque nec fringilla. Phasellus aliquam pulvinar risus. Praesent magna sem, consequat ut quam at, euismod maximus ipsum. Vestibulum porttitor blandit ultrices. <strong>Nam tempus hendrerit</strong> ipsum vitae elementum. Suspendisse sit amet eleifend tellus. Pellentesque habitant morbi tristique senectus et netus et malesuada fames ac turpis egestas. Aenean nec aliquam leo.Mauris sollicitudin ligula vitae erat mollis, a hendrerit mi molestie. Proin sit amet diam quis dolor ornare lacinia eu ut dui. In vitae congue diam. Aenean pharetra feugiat nulla, in ultrices nisl venenatis non. Donec nulla turpis, commodo eget pretium non, auctor vestibulum nibh. Donec sit amet sodales augue. Ut et odio at magna tempus interdum quis ut mauris. Nullam tristique semper condimentum. Sed sollicitudin lacus at felis vehicula bibendum. Nunc pharetra tincidunt urna. Suspendisse dignissim dui quis dolor fringilla porttitor. Morbi pellentesque eros quis lacus tristique maximus. Suspendisse laoreet sagittis ultrices.Pellentesque sit amet pellentesque felis.</p>\n<p><br></p>\n<h2>This is an H2 (medium) heading</h2>\n<p>Phasellus ex massa, hendrerit porta hendrerit a, pretium et justo. <ins>Vivamus eget dui sed justo consequat malesuada. Integer a commodo augue.</ins> Morbi rutrum suscipit efficitur. Vivamus ac libero ullamcorper, rhoncus nulla at, accumsan tellus. In hac habitasse platea dictumst. Donec maximus ex a faucibus commodo. In vel eros non diam pellentesque maximus. Curabitur fermentum accumsan lectus, ut aliquam ipsum pulvinar quis. Vestibulum ante ipsum primis in faucibus orci luctus et ultrices posuere cubilia Curae;Nam convallis egestas consectetur. Ut ac eleifend enim, a efficitur magna. Sed cursus ornare finibus. Mauris quis tincidunt justo. Cras efficitur, enim non pharetra ultrices, eros augue eleifend nisl, at congue elit leo quis arcu. Sed luctus, nibh vitae efficitur maximus, turpis ante porta diam, facilisis ultrices dui sem sed libero. Nulla pulvinar nisi eget cursus eleifend. Aliquam erat volutpat. Integer tortor nulla, auctor vitae vestibulum ut, sagittis sed velit. Integer a luctus arcu. Nam congue et elit sit amet porta. Cras euismod ipsum massa, quis elementum ligula lobortis quis. Mauris eu augue efficitur, feugiat augue non, aliquam ligula.Nulla a orci a felis mollis scelerisque. Pellentesque neque velit, faucibus nec mi eu, commodo tincidunt risus.</p>\n<p><br></p>\n<h3>This is an H3 (small) heading</h3>\n<p>Sed tempus justo leo, non sollicitudin mi eleifend a. Curabitur sed diam pulvinar, dictum nisl ut, blandit metus. Maecenas non sem quis ligula commodo egestas. Integer malesuada eleifend est, in commodo eros fermentum sed. Maecenas commodo nibh quis porttitor vehicula. Aenean blandit rutrum dolor, non ullamcorper est aliquam ac.Etiam interdum semper tempor. Phasellus condimentum massa eu libero sagittis cursus. Sed at lorem vel nulla elementum fringilla nec at eros. Aenean facilisis scelerisque tortor, non malesuada arcu scelerisque a. Ut est ante, iaculis at ultricies non, molestie placerat leo. Cras ullamcorper pellentesque erat in blandit. Nunc tortor ligula, fringilla ac risus quis, venenatis iaculis quam. Aliquam eget ex vitae ligula imperdiet finibus. Nullam ex metus, placerat ac arcu non, imperdiet consequat tortor. Donec varius elementum odio et rutrum. Sed in aliquam eros, sed sagittis erat. Vivamus tristique congue dictum. Proin tincidunt quis neque eget aliquam. Morbi sollicitudin orci lectus, a vulputate turpis porta a. Fusce facilisis ullamcorper dui in consequat.</p>\n<p><br></p>\n<h3>Code block follows</h3>\n<pre><code>Sed vitae convallis sapien, mollis fermentum ex.Curabitur rhoncus leo accumsan eros scelerisque, eget rhoncus augue porttitor. Praesent pretium mattis nibh, sit amet euismod nulla suscipit nec. Proin vehicula felis sit amet libero tempor, faucibus ultrices leo laoreet. Phasellus ultricies sapien urna, eget fringilla turpis rutrum vel. Donec nec nisl ultricies, lacinia diam in, finibus elit. Maecenas et felis eu lectus ultricies vestibulum. Aliquam accumsan efficitur lectus ut consequat. Sed quis aliquet justo, ut convallis eros.Vivamus vestibulum quam dictum orci aliquam, eget tincidunt est tincidunt. Curabitur pretium ut elit eget aliquet. Sed rhoncus metus sapien, eget malesuada ex dictum eu. Quisque auctor magna nibh, vel sollicitudin dui cursus sit amet.</code></pre>\n<p>In laoreet faucibus lorem vel fringilla. Sed et dolor sem. Proin velit augue, condimentum in enim sed, finibus tincidunt purus. Maecenas efficitur, lacus finibus vulputate luctus, urna eros iaculis lacus, a cursus lacus metus sit amet lacus. Maecenas porttitor imperdiet magna, et scelerisque nunc ornare nec. Integer consequat hendrerit neque, sed condimentum velit commodo a.</p>\n<p><br></p>\n<h3>Unordered list:</h3>\n<p>Praesent ultricies commodo arcu, at vulputate metus rutrum ut.Etiam vel ante vel nulla pellentesque aliquam sed at erat. In faucibus ac leo a dignissim. Donec augue lorem, sagittis sed tempus et, auctor vitae risus:</p>\n<ul>\n  <li>Fusce vel bibendum felis.</li>\n  <li>Phasellus vitae diam felis. Nulla rhoncus felis sit amet fringilla tincidunt. Pellentesque vestibulum, est non congue hendrerit, elit leo bibendum mauris, a malesuada quam massa ut lectus.</li>\n  <li>Vestibulum nec ornare neque.</li>\n  <li>Nunc mattis ex in vestibulum dapibus.</li>\n  <li>Quisque cursus lacus dui, consequat viverra purus lobortis ac. In hac habitasse platea dictumst.</li>\n</ul>\n<h3><br></h3>\n<h3>Ordered list:</h3>\n<p>Mauris sollicitudin ligula vitae erat mollis, a hendrerit mi molestie. Proin sit amet diam quis dolor ornare lacinia eu ut dui. In vitae congue diam. Aenean pharetra feugiat nulla, in ultrices nisl venenatis non. Donec nulla turpis, commodo eget pretium non, auctor vestibulum nibh:</p>\n<ol>\n  <li>Donec sit amet sodales augue. Ut et odio at magna tempus interdum quis ut mauris.</li>\n  <li>Nullam tristique semper condimentum.</li>\n  <li>Sed sollicitudin lacus at felis vehicula bibendum. Nunc pharetra tincidunt urna.</li>\n  <li>Suspendisse dignissim dui quis dolor fringilla porttitor.</li>\n  <li>Morbi pellentesque eros quis lacus tristique maximus. Suspendisse laoreet sagittis ultrices.</li>\n</ol>",
                    "margin-top":"marg-t-30",
                    "margin-bottom":"marg-b-100",
                    "margin-left":"marg-l-0",
                    "margin-right":"marg-r-0"
                  }
                }
              ]
            }
          }
        ]
      },
      "news":{
        "content":[
          {
            "element-type":"layout-50:50",
            "element-path":"page-builder/layouts/_two-col-50-50.html",
            "options":{
              "layout-bg-image":"",
              "bg-color":"#34495e",
              "margin-right":"marg-r-0",
              "margin-bottom":"marg-b-0",
              "layout-bg-image-size":"bg-img-size--cover",
              "text-color":"#000",
              "margin-top":"marg-t-0",
              "padding-right":"padd-r-0",
              "margin-left":"marg-l-0",
              "padding-bottom":"padd-b-50",
              "align-content":"align-content-center",
              "text-alignment":"text-align--left",
              "padding-top":"padd-t-200",
              "padding-left":"padd-l-0"
            },
            "children":{
              "column-1":[
                {
                  "element-type":"heading",
                  "element-path":"page-builder/elements/_heading.html",
                  "options":{
                    "font-size":"font-size--48px",
                    "margin-right":"marg-r-0",
                    "margin-bottom":"marg-b-20",
                    "text-color":"#ffffff",
                    "margin-top":"marg-t-0",
                    "margin-left":"marg-l-0",
                    "text-content":"This is an example title of the static page",
                    "font-family":"font--primary--regular",
                    "text-alignment":"text-align--left"
                  }
                },
                {
                  "element-type":"paragraph-text",
                  "element-path":"page-builder/elements/_paragraph.html",
                  "options":{
                    "font-size":"font-size--18px",
                    "margin-right":"marg-r-0",
                    "margin-bottom":"marg-b-5",
                    "text-color":"#ffffff",
                    "margin-top":"marg-t-5",
                    "margin-left":"marg-l-0",
                    "text-content":"Vivamus scelerisque odio ut lectus luctus, eget viverra leo aliquet.",
                    "font-family":"font--primary--regular",
                    "text-alignment":"text-align--left"
                  }
                }
              ],
              "column-2":[]
            }
          },
          {
            "element-type":"layout-single-col",
            "element-path":"page-builder/layouts/_single-col.html",
            "options":{
              "layout-bg-image":"",
              "bg-color":"#fff",
              "margin-right":"marg-r-0",
              "margin-bottom":"marg-b-0",
              "layout-bg-image-size":"bg-img-size--cover",
              "text-color":"#000",
              "margin-top":"marg-t-0",
              "padding-right":"padd-r-0",
              "margin-left":"marg-l-0",
              "padding-bottom":"padd-b-20",
              "align-content":"align-content-center",
              "text-alignment":"text-align--left",
              "padding-top":"padd-t-20",
              "padding-left":"padd-l-0"
            },
            "children":{
              "column-1":[
                {
                  "element-type":"content-block",
                  "element-path":"page-builder/elements/_content-block.html",
                  "options":{
                    "content":"<p>Lorem ipsum dolor sit amet, consectetur adipiscing elit. <a href=\"#\">Mauris libero nulla</a>, sagittis at erat non, commodo porta nunc. Donec ultrices erat vel vehicula posuere. Morbi a justo metus. Ut et libero congue, interdum diam sit amet, scelerisque massa. Sed non purus mi. Fusce posuere vel ante eu tempus.<em> Integer interdum libero libero, sit amet fermentum nisl pretium ac. In suscipit, elit eget vulputate bibendum, arcu libero </em><em><strong>tristique</strong></em><em> diam, ut fringilla augue est in neque.</em> Suspendisse consequat ex non lacinia sodales.In feugiat eu erat non interdum. <del>Donec nec accumsan augue.</del> Sed consequat quis mauris ut interdum. Aliquam porttitor risus egestas, maximus quam a, cursus erat. Donec in sem ligula. Sed non convallis dui. Phasellus scelerisque maximus vestibulum.</p>\n<p><br></p>\n<h1>This is an H1 (large) heading</h1>\n<p>Fusce nunc est, euismod sit amet vehicula non, facilisis eu purus. Curabitur cursus et neque nec fringilla. Phasellus aliquam pulvinar risus. Praesent magna sem, consequat ut quam at, euismod maximus ipsum. Vestibulum porttitor blandit ultrices. <strong>Nam tempus hendrerit</strong> ipsum vitae elementum. Suspendisse sit amet eleifend tellus. Pellentesque habitant morbi tristique senectus et netus et malesuada fames ac turpis egestas. Aenean nec aliquam leo.Mauris sollicitudin ligula vitae erat mollis, a hendrerit mi molestie. Proin sit amet diam quis dolor ornare lacinia eu ut dui. In vitae congue diam. Aenean pharetra feugiat nulla, in ultrices nisl venenatis non. Donec nulla turpis, commodo eget pretium non, auctor vestibulum nibh. Donec sit amet sodales augue. Ut et odio at magna tempus interdum quis ut mauris. Nullam tristique semper condimentum. Sed sollicitudin lacus at felis vehicula bibendum. Nunc pharetra tincidunt urna. Suspendisse dignissim dui quis dolor fringilla porttitor. Morbi pellentesque eros quis lacus tristique maximus. Suspendisse laoreet sagittis ultrices.Pellentesque sit amet pellentesque felis.</p>\n<p><br></p>\n<h2>This is an H2 (medium) heading</h2>\n<p>Phasellus ex massa, hendrerit porta hendrerit a, pretium et justo. <ins>Vivamus eget dui sed justo consequat malesuada. Integer a commodo augue.</ins> Morbi rutrum suscipit efficitur. Vivamus ac libero ullamcorper, rhoncus nulla at, accumsan tellus. In hac habitasse platea dictumst. Donec maximus ex a faucibus commodo. In vel eros non diam pellentesque maximus. Curabitur fermentum accumsan lectus, ut aliquam ipsum pulvinar quis. Vestibulum ante ipsum primis in faucibus orci luctus et ultrices posuere cubilia Curae;Nam convallis egestas consectetur. Ut ac eleifend enim, a efficitur magna. Sed cursus ornare finibus. Mauris quis tincidunt justo. Cras efficitur, enim non pharetra ultrices, eros augue eleifend nisl, at congue elit leo quis arcu. Sed luctus, nibh vitae efficitur maximus, turpis ante porta diam, facilisis ultrices dui sem sed libero. Nulla pulvinar nisi eget cursus eleifend. Aliquam erat volutpat. Integer tortor nulla, auctor vitae vestibulum ut, sagittis sed velit. Integer a luctus arcu. Nam congue et elit sit amet porta. Cras euismod ipsum massa, quis elementum ligula lobortis quis. Mauris eu augue efficitur, feugiat augue non, aliquam ligula.Nulla a orci a felis mollis scelerisque. Pellentesque neque velit, faucibus nec mi eu, commodo tincidunt risus.</p>\n<p><br></p>\n<h3>This is an H3 (small) heading</h3>\n<p>Sed tempus justo leo, non sollicitudin mi eleifend a. Curabitur sed diam pulvinar, dictum nisl ut, blandit metus. Maecenas non sem quis ligula commodo egestas. Integer malesuada eleifend est, in commodo eros fermentum sed. Maecenas commodo nibh quis porttitor vehicula. Aenean blandit rutrum dolor, non ullamcorper est aliquam ac.Etiam interdum semper tempor. Phasellus condimentum massa eu libero sagittis cursus. Sed at lorem vel nulla elementum fringilla nec at eros. Aenean facilisis scelerisque tortor, non malesuada arcu scelerisque a. Ut est ante, iaculis at ultricies non, molestie placerat leo. Cras ullamcorper pellentesque erat in blandit. Nunc tortor ligula, fringilla ac risus quis, venenatis iaculis quam. Aliquam eget ex vitae ligula imperdiet finibus. Nullam ex metus, placerat ac arcu non, imperdiet consequat tortor. Donec varius elementum odio et rutrum. Sed in aliquam eros, sed sagittis erat. Vivamus tristique congue dictum. Proin tincidunt quis neque eget aliquam. Morbi sollicitudin orci lectus, a vulputate turpis porta a. Fusce facilisis ullamcorper dui in consequat.</p>\n<p><br></p>\n<h3>Code block follows</h3>\n<pre><code>Sed vitae convallis sapien, mollis fermentum ex.Curabitur rhoncus leo accumsan eros scelerisque, eget rhoncus augue porttitor. Praesent pretium mattis nibh, sit amet euismod nulla suscipit nec. Proin vehicula felis sit amet libero tempor, faucibus ultrices leo laoreet. Phasellus ultricies sapien urna, eget fringilla turpis rutrum vel. Donec nec nisl ultricies, lacinia diam in, finibus elit. Maecenas et felis eu lectus ultricies vestibulum. Aliquam accumsan efficitur lectus ut consequat. Sed quis aliquet justo, ut convallis eros.Vivamus vestibulum quam dictum orci aliquam, eget tincidunt est tincidunt. Curabitur pretium ut elit eget aliquet. Sed rhoncus metus sapien, eget malesuada ex dictum eu. Quisque auctor magna nibh, vel sollicitudin dui cursus sit amet.</code></pre>\n<p>In laoreet faucibus lorem vel fringilla. Sed et dolor sem. Proin velit augue, condimentum in enim sed, finibus tincidunt purus. Maecenas efficitur, lacus finibus vulputate luctus, urna eros iaculis lacus, a cursus lacus metus sit amet lacus. Maecenas porttitor imperdiet magna, et scelerisque nunc ornare nec. Integer consequat hendrerit neque, sed condimentum velit commodo a.</p>\n<p><br></p>\n<h3>Unordered list:</h3>\n<p>Praesent ultricies commodo arcu, at vulputate metus rutrum ut.Etiam vel ante vel nulla pellentesque aliquam sed at erat. In faucibus ac leo a dignissim. Donec augue lorem, sagittis sed tempus et, auctor vitae risus:</p>\n<ul>\n  <li>Fusce vel bibendum felis.</li>\n  <li>Phasellus vitae diam felis. Nulla rhoncus felis sit amet fringilla tincidunt. Pellentesque vestibulum, est non congue hendrerit, elit leo bibendum mauris, a malesuada quam massa ut lectus.</li>\n  <li>Vestibulum nec ornare neque.</li>\n  <li>Nunc mattis ex in vestibulum dapibus.</li>\n  <li>Quisque cursus lacus dui, consequat viverra purus lobortis ac. In hac habitasse platea dictumst.</li>\n</ul>\n<h3><br></h3>\n<h3>Ordered list:</h3>\n<p>Mauris sollicitudin ligula vitae erat mollis, a hendrerit mi molestie. Proin sit amet diam quis dolor ornare lacinia eu ut dui. In vitae congue diam. Aenean pharetra feugiat nulla, in ultrices nisl venenatis non. Donec nulla turpis, commodo eget pretium non, auctor vestibulum nibh:</p>\n<ol>\n  <li>Donec sit amet sodales augue. Ut et odio at magna tempus interdum quis ut mauris.</li>\n  <li>Nullam tristique semper condimentum.</li>\n  <li>Sed sollicitudin lacus at felis vehicula bibendum. Nunc pharetra tincidunt urna.</li>\n  <li>Suspendisse dignissim dui quis dolor fringilla porttitor.</li>\n  <li>Morbi pellentesque eros quis lacus tristique maximus. Suspendisse laoreet sagittis ultrices.</li>\n</ol>",
                    "margin-top":"marg-t-30",
                    "margin-bottom":"marg-b-100",
                    "margin-left":"marg-l-0",
                    "margin-right":"marg-r-0"
                  }
                }
              ]
            }
          }
        ]
      },
      "donate":{
        "content":[
          {
            "element-type":"layout-50:50",
            "element-path":"page-builder/layouts/_two-col-50-50.html",
            "options":{
              "layout-bg-image":"",
              "bg-color":"#34495e",
              "margin-right":"marg-r-0",
              "margin-bottom":"marg-b-0",
              "layout-bg-image-size":"bg-img-size--cover",
              "text-color":"#000",
              "margin-top":"marg-t-0",
              "padding-right":"padd-r-0",
              "margin-left":"marg-l-0",
              "padding-bottom":"padd-b-50",
              "align-content":"align-content-center",
              "text-alignment":"text-align--left",
              "padding-top":"padd-t-200",
              "padding-left":"padd-l-0"
            },
            "children":{
              "column-1":[
                {
                  "element-type":"heading",
                  "element-path":"page-builder/elements/_heading.html",
                  "options":{
                    "font-size":"font-size--48px",
                    "margin-right":"marg-r-0",
                    "margin-bottom":"marg-b-20",
                    "text-color":"#ffffff",
                    "margin-top":"marg-t-0",
                    "margin-left":"marg-l-0",
                    "text-content":"This is an example title of the static page",
                    "font-family":"font--primary--regular",
                    "text-alignment":"text-align--left"
                  }
                },
                {
                  "element-type":"paragraph-text",
                  "element-path":"page-builder/elements/_paragraph.html",
                  "options":{
                    "font-size":"font-size--18px",
                    "margin-right":"marg-r-0",
                    "margin-bottom":"marg-b-5",
                    "text-color":"#ffffff",
                    "margin-top":"marg-t-5",
                    "margin-left":"marg-l-0",
                    "text-content":"Vivamus scelerisque odio ut lectus luctus, eget viverra leo aliquet.",
                    "font-family":"font--primary--regular",
                    "text-alignment":"text-align--left"
                  }
                }
              ],
              "column-2":[]
            }
          },
          {
            "element-type":"layout-single-col",
            "element-path":"page-builder/layouts/_single-col.html",
            "options":{
              "layout-bg-image":"",
              "bg-color":"#fff",
              "margin-right":"marg-r-0",
              "margin-bottom":"marg-b-0",
              "layout-bg-image-size":"bg-img-size--cover",
              "text-color":"#000",
              "margin-top":"marg-t-0",
              "padding-right":"padd-r-0",
              "margin-left":"marg-l-0",
              "padding-bottom":"padd-b-20",
              "align-content":"align-content-center",
              "text-alignment":"text-align--left",
              "padding-top":"padd-t-20",
              "padding-left":"padd-l-0"
            },
            "children":{
              "column-1":[
                {
                  "element-type":"content-block",
                  "element-path":"page-builder/elements/_content-block.html",
                  "options":{
                    "content":"<p>Lorem ipsum dolor sit amet, consectetur adipiscing elit. <a href=\"#\">Mauris libero nulla</a>, sagittis at erat non, commodo porta nunc. Donec ultrices erat vel vehicula posuere. Morbi a justo metus. Ut et libero congue, interdum diam sit amet, scelerisque massa. Sed non purus mi. Fusce posuere vel ante eu tempus.<em> Integer interdum libero libero, sit amet fermentum nisl pretium ac. In suscipit, elit eget vulputate bibendum, arcu libero </em><em><strong>tristique</strong></em><em> diam, ut fringilla augue est in neque.</em> Suspendisse consequat ex non lacinia sodales.In feugiat eu erat non interdum. <del>Donec nec accumsan augue.</del> Sed consequat quis mauris ut interdum. Aliquam porttitor risus egestas, maximus quam a, cursus erat. Donec in sem ligula. Sed non convallis dui. Phasellus scelerisque maximus vestibulum.</p>\n<p><br></p>\n<h1>This is an H1 (large) heading</h1>\n<p>Fusce nunc est, euismod sit amet vehicula non, facilisis eu purus. Curabitur cursus et neque nec fringilla. Phasellus aliquam pulvinar risus. Praesent magna sem, consequat ut quam at, euismod maximus ipsum. Vestibulum porttitor blandit ultrices. <strong>Nam tempus hendrerit</strong> ipsum vitae elementum. Suspendisse sit amet eleifend tellus. Pellentesque habitant morbi tristique senectus et netus et malesuada fames ac turpis egestas. Aenean nec aliquam leo.Mauris sollicitudin ligula vitae erat mollis, a hendrerit mi molestie. Proin sit amet diam quis dolor ornare lacinia eu ut dui. In vitae congue diam. Aenean pharetra feugiat nulla, in ultrices nisl venenatis non. Donec nulla turpis, commodo eget pretium non, auctor vestibulum nibh. Donec sit amet sodales augue. Ut et odio at magna tempus interdum quis ut mauris. Nullam tristique semper condimentum. Sed sollicitudin lacus at felis vehicula bibendum. Nunc pharetra tincidunt urna. Suspendisse dignissim dui quis dolor fringilla porttitor. Morbi pellentesque eros quis lacus tristique maximus. Suspendisse laoreet sagittis ultrices.Pellentesque sit amet pellentesque felis.</p>\n<p><br></p>\n<h2>This is an H2 (medium) heading</h2>\n<p>Phasellus ex massa, hendrerit porta hendrerit a, pretium et justo. <ins>Vivamus eget dui sed justo consequat malesuada. Integer a commodo augue.</ins> Morbi rutrum suscipit efficitur. Vivamus ac libero ullamcorper, rhoncus nulla at, accumsan tellus. In hac habitasse platea dictumst. Donec maximus ex a faucibus commodo. In vel eros non diam pellentesque maximus. Curabitur fermentum accumsan lectus, ut aliquam ipsum pulvinar quis. Vestibulum ante ipsum primis in faucibus orci luctus et ultrices posuere cubilia Curae;Nam convallis egestas consectetur. Ut ac eleifend enim, a efficitur magna. Sed cursus ornare finibus. Mauris quis tincidunt justo. Cras efficitur, enim non pharetra ultrices, eros augue eleifend nisl, at congue elit leo quis arcu. Sed luctus, nibh vitae efficitur maximus, turpis ante porta diam, facilisis ultrices dui sem sed libero. Nulla pulvinar nisi eget cursus eleifend. Aliquam erat volutpat. Integer tortor nulla, auctor vitae vestibulum ut, sagittis sed velit. Integer a luctus arcu. Nam congue et elit sit amet porta. Cras euismod ipsum massa, quis elementum ligula lobortis quis. Mauris eu augue efficitur, feugiat augue non, aliquam ligula.Nulla a orci a felis mollis scelerisque. Pellentesque neque velit, faucibus nec mi eu, commodo tincidunt risus.</p>\n<p><br></p>\n<h3>This is an H3 (small) heading</h3>\n<p>Sed tempus justo leo, non sollicitudin mi eleifend a. Curabitur sed diam pulvinar, dictum nisl ut, blandit metus. Maecenas non sem quis ligula commodo egestas. Integer malesuada eleifend est, in commodo eros fermentum sed. Maecenas commodo nibh quis porttitor vehicula. Aenean blandit rutrum dolor, non ullamcorper est aliquam ac.Etiam interdum semper tempor. Phasellus condimentum massa eu libero sagittis cursus. Sed at lorem vel nulla elementum fringilla nec at eros. Aenean facilisis scelerisque tortor, non malesuada arcu scelerisque a. Ut est ante, iaculis at ultricies non, molestie placerat leo. Cras ullamcorper pellentesque erat in blandit. Nunc tortor ligula, fringilla ac risus quis, venenatis iaculis quam. Aliquam eget ex vitae ligula imperdiet finibus. Nullam ex metus, placerat ac arcu non, imperdiet consequat tortor. Donec varius elementum odio et rutrum. Sed in aliquam eros, sed sagittis erat. Vivamus tristique congue dictum. Proin tincidunt quis neque eget aliquam. Morbi sollicitudin orci lectus, a vulputate turpis porta a. Fusce facilisis ullamcorper dui in consequat.</p>\n<p><br></p>\n<h3>Code block follows</h3>\n<pre><code>Sed vitae convallis sapien, mollis fermentum ex.Curabitur rhoncus leo accumsan eros scelerisque, eget rhoncus augue porttitor. Praesent pretium mattis nibh, sit amet euismod nulla suscipit nec. Proin vehicula felis sit amet libero tempor, faucibus ultrices leo laoreet. Phasellus ultricies sapien urna, eget fringilla turpis rutrum vel. Donec nec nisl ultricies, lacinia diam in, finibus elit. Maecenas et felis eu lectus ultricies vestibulum. Aliquam accumsan efficitur lectus ut consequat. Sed quis aliquet justo, ut convallis eros.Vivamus vestibulum quam dictum orci aliquam, eget tincidunt est tincidunt. Curabitur pretium ut elit eget aliquet. Sed rhoncus metus sapien, eget malesuada ex dictum eu. Quisque auctor magna nibh, vel sollicitudin dui cursus sit amet.</code></pre>\n<p>In laoreet faucibus lorem vel fringilla. Sed et dolor sem. Proin velit augue, condimentum in enim sed, finibus tincidunt purus. Maecenas efficitur, lacus finibus vulputate luctus, urna eros iaculis lacus, a cursus lacus metus sit amet lacus. Maecenas porttitor imperdiet magna, et scelerisque nunc ornare nec. Integer consequat hendrerit neque, sed condimentum velit commodo a.</p>\n<p><br></p>\n<h3>Unordered list:</h3>\n<p>Praesent ultricies commodo arcu, at vulputate metus rutrum ut.Etiam vel ante vel nulla pellentesque aliquam sed at erat. In faucibus ac leo a dignissim. Donec augue lorem, sagittis sed tempus et, auctor vitae risus:</p>\n<ul>\n  <li>Fusce vel bibendum felis.</li>\n  <li>Phasellus vitae diam felis. Nulla rhoncus felis sit amet fringilla tincidunt. Pellentesque vestibulum, est non congue hendrerit, elit leo bibendum mauris, a malesuada quam massa ut lectus.</li>\n  <li>Vestibulum nec ornare neque.</li>\n  <li>Nunc mattis ex in vestibulum dapibus.</li>\n  <li>Quisque cursus lacus dui, consequat viverra purus lobortis ac. In hac habitasse platea dictumst.</li>\n</ul>\n<h3><br></h3>\n<h3>Ordered list:</h3>\n<p>Mauris sollicitudin ligula vitae erat mollis, a hendrerit mi molestie. Proin sit amet diam quis dolor ornare lacinia eu ut dui. In vitae congue diam. Aenean pharetra feugiat nulla, in ultrices nisl venenatis non. Donec nulla turpis, commodo eget pretium non, auctor vestibulum nibh:</p>\n<ol>\n  <li>Donec sit amet sodales augue. Ut et odio at magna tempus interdum quis ut mauris.</li>\n  <li>Nullam tristique semper condimentum.</li>\n  <li>Sed sollicitudin lacus at felis vehicula bibendum. Nunc pharetra tincidunt urna.</li>\n  <li>Suspendisse dignissim dui quis dolor fringilla porttitor.</li>\n  <li>Morbi pellentesque eros quis lacus tristique maximus. Suspendisse laoreet sagittis ultrices.</li>\n</ol>",
                    "margin-top":"marg-t-30",
                    "margin-bottom":"marg-b-100",
                    "margin-left":"marg-l-0",
                    "margin-right":"marg-r-0"
                  }
                }
              ]
            }
          }
        ]
      },
      "honor":{
        "content":[
          {
            "element-type":"layout-50:50",
            "element-path":"page-builder/layouts/_two-col-50-50.html",
            "options":{
              "layout-bg-image":"",
              "bg-color":"#34495e",
              "margin-right":"marg-r-0",
              "margin-bottom":"marg-b-0",
              "layout-bg-image-size":"bg-img-size--cover",
              "text-color":"#000",
              "margin-top":"marg-t-0",
              "padding-right":"padd-r-0",
              "margin-left":"marg-l-0",
              "padding-bottom":"padd-b-50",
              "align-content":"align-content-center",
              "text-alignment":"text-align--left",
              "padding-top":"padd-t-200",
              "padding-left":"padd-l-0"
            },
            "children":{
              "column-1":[
                {
                  "element-type":"heading",
                  "element-path":"page-builder/elements/_heading.html",
                  "options":{
                    "font-size":"font-size--48px",
                    "margin-right":"marg-r-0",
                    "margin-bottom":"marg-b-20",
                    "text-color":"#ffffff",
                    "margin-top":"marg-t-0",
                    "margin-left":"marg-l-0",
                    "text-content":"This is an example title of the static page",
                    "font-family":"font--primary--regular",
                    "text-alignment":"text-align--left"
                  }
                },
                {
                  "element-type":"paragraph-text",
                  "element-path":"page-builder/elements/_paragraph.html",
                  "options":{
                    "font-size":"font-size--18px",
                    "margin-right":"marg-r-0",
                    "margin-bottom":"marg-b-5",
                    "text-color":"#ffffff",
                    "margin-top":"marg-t-5",
                    "margin-left":"marg-l-0",
                    "text-content":"Vivamus scelerisque odio ut lectus luctus, eget viverra leo aliquet.",
                    "font-family":"font--primary--regular",
                    "text-alignment":"text-align--left"
                  }
                }
              ],
              "column-2":[]
            }
          },
          {
            "element-type":"layout-single-col",
            "element-path":"page-builder/layouts/_single-col.html",
            "options":{
              "layout-bg-image":"",
              "bg-color":"#fff",
              "margin-right":"marg-r-0",
              "margin-bottom":"marg-b-0",
              "layout-bg-image-size":"bg-img-size--cover",
              "text-color":"#000",
              "margin-top":"marg-t-0",
              "padding-right":"padd-r-0",
              "margin-left":"marg-l-0",
              "padding-bottom":"padd-b-20",
              "align-content":"align-content-center",
              "text-alignment":"text-align--left",
              "padding-top":"padd-t-20",
              "padding-left":"padd-l-0"
            },
            "children":{
              "column-1":[
                {
                  "element-type":"content-block",
                  "element-path":"page-builder/elements/_content-block.html",
                  "options":{
                    "content":"<p>Lorem ipsum dolor sit amet, consectetur adipiscing elit. <a href=\"#\">Mauris libero nulla</a>, sagittis at erat non, commodo porta nunc. Donec ultrices erat vel vehicula posuere. Morbi a justo metus. Ut et libero congue, interdum diam sit amet, scelerisque massa. Sed non purus mi. Fusce posuere vel ante eu tempus.<em> Integer interdum libero libero, sit amet fermentum nisl pretium ac. In suscipit, elit eget vulputate bibendum, arcu libero </em><em><strong>tristique</strong></em><em> diam, ut fringilla augue est in neque.</em> Suspendisse consequat ex non lacinia sodales.In feugiat eu erat non interdum. <del>Donec nec accumsan augue.</del> Sed consequat quis mauris ut interdum. Aliquam porttitor risus egestas, maximus quam a, cursus erat. Donec in sem ligula. Sed non convallis dui. Phasellus scelerisque maximus vestibulum.</p>\n<p><br></p>\n<h1>This is an H1 (large) heading</h1>\n<p>Fusce nunc est, euismod sit amet vehicula non, facilisis eu purus. Curabitur cursus et neque nec fringilla. Phasellus aliquam pulvinar risus. Praesent magna sem, consequat ut quam at, euismod maximus ipsum. Vestibulum porttitor blandit ultrices. <strong>Nam tempus hendrerit</strong> ipsum vitae elementum. Suspendisse sit amet eleifend tellus. Pellentesque habitant morbi tristique senectus et netus et malesuada fames ac turpis egestas. Aenean nec aliquam leo.Mauris sollicitudin ligula vitae erat mollis, a hendrerit mi molestie. Proin sit amet diam quis dolor ornare lacinia eu ut dui. In vitae congue diam. Aenean pharetra feugiat nulla, in ultrices nisl venenatis non. Donec nulla turpis, commodo eget pretium non, auctor vestibulum nibh. Donec sit amet sodales augue. Ut et odio at magna tempus interdum quis ut mauris. Nullam tristique semper condimentum. Sed sollicitudin lacus at felis vehicula bibendum. Nunc pharetra tincidunt urna. Suspendisse dignissim dui quis dolor fringilla porttitor. Morbi pellentesque eros quis lacus tristique maximus. Suspendisse laoreet sagittis ultrices.Pellentesque sit amet pellentesque felis.</p>\n<p><br></p>\n<h2>This is an H2 (medium) heading</h2>\n<p>Phasellus ex massa, hendrerit porta hendrerit a, pretium et justo. <ins>Vivamus eget dui sed justo consequat malesuada. Integer a commodo augue.</ins> Morbi rutrum suscipit efficitur. Vivamus ac libero ullamcorper, rhoncus nulla at, accumsan tellus. In hac habitasse platea dictumst. Donec maximus ex a faucibus commodo. In vel eros non diam pellentesque maximus. Curabitur fermentum accumsan lectus, ut aliquam ipsum pulvinar quis. Vestibulum ante ipsum primis in faucibus orci luctus et ultrices posuere cubilia Curae;Nam convallis egestas consectetur. Ut ac eleifend enim, a efficitur magna. Sed cursus ornare finibus. Mauris quis tincidunt justo. Cras efficitur, enim non pharetra ultrices, eros augue eleifend nisl, at congue elit leo quis arcu. Sed luctus, nibh vitae efficitur maximus, turpis ante porta diam, facilisis ultrices dui sem sed libero. Nulla pulvinar nisi eget cursus eleifend. Aliquam erat volutpat. Integer tortor nulla, auctor vitae vestibulum ut, sagittis sed velit. Integer a luctus arcu. Nam congue et elit sit amet porta. Cras euismod ipsum massa, quis elementum ligula lobortis quis. Mauris eu augue efficitur, feugiat augue non, aliquam ligula.Nulla a orci a felis mollis scelerisque. Pellentesque neque velit, faucibus nec mi eu, commodo tincidunt risus.</p>\n<p><br></p>\n<h3>This is an H3 (small) heading</h3>\n<p>Sed tempus justo leo, non sollicitudin mi eleifend a. Curabitur sed diam pulvinar, dictum nisl ut, blandit metus. Maecenas non sem quis ligula commodo egestas. Integer malesuada eleifend est, in commodo eros fermentum sed. Maecenas commodo nibh quis porttitor vehicula. Aenean blandit rutrum dolor, non ullamcorper est aliquam ac.Etiam interdum semper tempor. Phasellus condimentum massa eu libero sagittis cursus. Sed at lorem vel nulla elementum fringilla nec at eros. Aenean facilisis scelerisque tortor, non malesuada arcu scelerisque a. Ut est ante, iaculis at ultricies non, molestie placerat leo. Cras ullamcorper pellentesque erat in blandit. Nunc tortor ligula, fringilla ac risus quis, venenatis iaculis quam. Aliquam eget ex vitae ligula imperdiet finibus. Nullam ex metus, placerat ac arcu non, imperdiet consequat tortor. Donec varius elementum odio et rutrum. Sed in aliquam eros, sed sagittis erat. Vivamus tristique congue dictum. Proin tincidunt quis neque eget aliquam. Morbi sollicitudin orci lectus, a vulputate turpis porta a. Fusce facilisis ullamcorper dui in consequat.</p>\n<p><br></p>\n<h3>Code block follows</h3>\n<pre><code>Sed vitae convallis sapien, mollis fermentum ex.Curabitur rhoncus leo accumsan eros scelerisque, eget rhoncus augue porttitor. Praesent pretium mattis nibh, sit amet euismod nulla suscipit nec. Proin vehicula felis sit amet libero tempor, faucibus ultrices leo laoreet. Phasellus ultricies sapien urna, eget fringilla turpis rutrum vel. Donec nec nisl ultricies, lacinia diam in, finibus elit. Maecenas et felis eu lectus ultricies vestibulum. Aliquam accumsan efficitur lectus ut consequat. Sed quis aliquet justo, ut convallis eros.Vivamus vestibulum quam dictum orci aliquam, eget tincidunt est tincidunt. Curabitur pretium ut elit eget aliquet. Sed rhoncus metus sapien, eget malesuada ex dictum eu. Quisque auctor magna nibh, vel sollicitudin dui cursus sit amet.</code></pre>\n<p>In laoreet faucibus lorem vel fringilla. Sed et dolor sem. Proin velit augue, condimentum in enim sed, finibus tincidunt purus. Maecenas efficitur, lacus finibus vulputate luctus, urna eros iaculis lacus, a cursus lacus metus sit amet lacus. Maecenas porttitor imperdiet magna, et scelerisque nunc ornare nec. Integer consequat hendrerit neque, sed condimentum velit commodo a.</p>\n<p><br></p>\n<h3>Unordered list:</h3>\n<p>Praesent ultricies commodo arcu, at vulputate metus rutrum ut.Etiam vel ante vel nulla pellentesque aliquam sed at erat. In faucibus ac leo a dignissim. Donec augue lorem, sagittis sed tempus et, auctor vitae risus:</p>\n<ul>\n  <li>Fusce vel bibendum felis.</li>\n  <li>Phasellus vitae diam felis. Nulla rhoncus felis sit amet fringilla tincidunt. Pellentesque vestibulum, est non congue hendrerit, elit leo bibendum mauris, a malesuada quam massa ut lectus.</li>\n  <li>Vestibulum nec ornare neque.</li>\n  <li>Nunc mattis ex in vestibulum dapibus.</li>\n  <li>Quisque cursus lacus dui, consequat viverra purus lobortis ac. In hac habitasse platea dictumst.</li>\n</ul>\n<h3><br></h3>\n<h3>Ordered list:</h3>\n<p>Mauris sollicitudin ligula vitae erat mollis, a hendrerit mi molestie. Proin sit amet diam quis dolor ornare lacinia eu ut dui. In vitae congue diam. Aenean pharetra feugiat nulla, in ultrices nisl venenatis non. Donec nulla turpis, commodo eget pretium non, auctor vestibulum nibh:</p>\n<ol>\n  <li>Donec sit amet sodales augue. Ut et odio at magna tempus interdum quis ut mauris.</li>\n  <li>Nullam tristique semper condimentum.</li>\n  <li>Sed sollicitudin lacus at felis vehicula bibendum. Nunc pharetra tincidunt urna.</li>\n  <li>Suspendisse dignissim dui quis dolor fringilla porttitor.</li>\n  <li>Morbi pellentesque eros quis lacus tristique maximus. Suspendisse laoreet sagittis ultrices.</li>\n</ol>",
                    "margin-top":"marg-t-30",
                    "margin-bottom":"marg-b-100",
                    "margin-left":"marg-l-0",
                    "margin-right":"marg-r-0"
                  }
                }
              ]
            }
          }
        ]
      }
    }
