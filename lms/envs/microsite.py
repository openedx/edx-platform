# Configuration data to support 'microsites' that are bound - in middleware - 
# based on incoming hostname domain
# For local test purposes, let's define a "OpenedX" subdomain brand
_MICROSITE_CONFIGURATION = {
    "openedx": {
        # A display string that will be displayed when user visits the microsite. Given that we are handling this
        # in configuration, it will not be localizable
        "platform_name": "Open edX",
        # override for USE_CUSTOM_THEME set otherwhere in config
        "USE_CUSTOM_THEME": True,
        # override for THEME_NAME set otherwhere in config, which is part of the
        # Stanford Theming contribution
        "THEME_NAME": "openedx",
        # allow for microsite to load in an additional .css file that can override
        # the platform's default CSS definitions. For example, swap out the background image.
        "css_overrides_file": "microsites/openedx/css/openedx.css",
        # This is a CSS literal which will be added to every page
        "css_overrides": None,
        # what logo file to display, note that we shouldn't check in trademarked logos
        # into the repository, so these images will have to be deployed/managed outside of
        # code pushes
        "logo_image_file": "open_edX_logo.png",
        # also allow for a specification of a separate URL for the logo image so that we don't
        # need to check it into the repo
        "logo_image_url": None,
        # what filter to use when displaying the course catalog on the landing page     
        "course_org_filter": "CDX",
        # filter dashboard to only show this ORG's courses?
        "show_only_org_on_student_dashboard": True,
        # email from field on outbound emails
        "email_from_address": "openedx@edx.org",
        "payment_support_email": "openedx@edx.org",
        # override for ENABLE_MKTG_SITE set otherwhere in config
        # this is to indicate that the LMS is 'behind' a separate marketing website which
        # is a different web application
        "ENABLE_MKTG_SITE":  False,
        # override the SITE_NAME setting
        "SITE_NAME": 'openedx.localhost',
        # setting to indicate whether to show the "university partner" list on the landing page
        "show_university_partners": False,
        # setting to hide the promo video on the homepage
        "show_homepage_promo_video": False,
        # These 4 following items define the template substitutions to use in the courseware pages
        # these templates reside in lms/templates
        "header_extra_file": None,
        "header_file": "navigation.html",
        "google_analytics_file": "google_analytics.html",
        "footer_file": "openedx-footer.html",
        # This override is a HTML literal to put as the page footer, unfortunately this HTML becomes
        # non-localizable if we define in configuration. NOTE: This will take presendence over 'footer_file'
        "footer_html": """
            <div class="wrapper wrapper-footer">
                <footer>
                    <div class="colophon">
                        <div class="colophon-about">
                            <p>Open edX is a non-profit created by founding partners Harvard and MIT whose mission is to bring the best of higher education to students of all ages anywhere in the world, wherever there is Internet access. Open edX's free online MOOCs are interactive and subjects include computer science, public health, and artificial intelligence.</p>
                        </div>
                    </div>
                    <div class="references">
                        <p class="copyright">&#169; 2013 edX, some rights reserved.</p>
                        <nav class="nav-legal">
                            <ul>
                        </nav>
                    </div>
                </footer>
            </div>
        """,
        # this control whether the home header (the overlay) shows on the homepage
        # for example the overlay which says "The Future of Online Education", has the background image, 
        # as well as the top-level promo video
        "show_home_header": False,
        # This controls whether the social sharing links of the course about page should be displayed
        "course_about_show_social_links": True,
        # This is the text on the course index page which is overlaid on top of the background image
        "course_index_overlay_text": "Explore free courses from leading universities.",
        # This is the logo that displays in the overlay on top of the backgroundimage
        "course_index_overlay_logo_file": "/static/images/edx_bw.png",
        # we can  specify the email templatea here itself rather than referring to an on-disk
        # template file. This helps to keep branding stuff out of the repo and we can manage it via
        # configuration. Unfortunately, using this technique causes I18N issues, but Open edX wasn't
        # natively supporting I18N on email on-disk templates, so this isn't a regression
        "email_templates": {
            "activation_email": {
                "subject": "Your account for Open edX",
                "body":
                    "Thank you for signing up for Open edX! To activate\n"
                    "your account, please copy and paste this address into your web\n"
                    "browser's address bar:\n"
                    "\n"
                    "https://${ site_domain }/activate/${ key }\n"
                    "\n"
                    "If you didn't request this, you don't need to do anything; you won't\n"
                    "receive any more email from us. Please do not reply to this e-mail;\n"
                    "if you require assistance, check the help section of the Open edX web site.\n"
            },
            "confirm_email_change": {
                "subject": "Request to change Open edX account e-mail\n",
                "body":
                    "<%! from django.core.urlresolvers import reverse %>\n"
                    "This is to confirm that you changed the e-mail associated with\n"
                    "Open edX from ${old_email} to ${new_email}. If you\n"
                    "did not make this request, please contact us immediately. Contact\n"
                    "information is listed at:\n"
                    "\n"
                    "https://${ site_domain }${reverse('contact')}\n"
                    "\n"
                    "We keep a log of old e-mails, so if this request was unintentional, we\n"
                    "can investigate."
            },
            "allowed_enroll": {
                "subject": "You have been invited to register for ${course_name}",
                "body": 
                    "To finish your registration, please visit ${registration_url} and fill\n"
                    "out the registration form making sure to use ${email_address} in the E-mail field.\n"
                    "% if auto_enroll:\n"
                    "Once you have registered and activated your account, you will see\n"
                    "${course_name} listed on your dashboard.\n"
                    "% else:\n"
                    "Once you have registered and activated your account, visit ${course_about_url}\n"
                    "to join the course.\n"
                    "% endif\n"
                    "\n----\nThis email was automatically sent from ${site_name} to\n"
                    "${email_address}"
            },
            "enrolled_enroll": {
                "subject": "You have been enrolled in ${course_name}",
                "body": 
                    "Dear ${full_name}\n"
                    "\n"
                    "You have been enrolled in {course_name} at ${platform_name} by a member\n"
                    "of the course staff. The course should now appear on your ${site_name}\n"
                    "dashboard.\n"
                    "\n"
                    "To start accessing course materials, please visit ${course_url}"
                    "\n"
                    "\n"
                    "----\n"
                    "This email was automatically sent from ${site_name} to\n"
                    "${full_name}"
            },
            "allowed_unenroll": {
                "subject": "You have been un-enrolled from ${course_name}",
                "body": 
                    "\n"
                    "Dear Student,\n"
                    "\n"
                    "You have been un-enrolled from course ${course_name} by a member\n"
                    "of the course staff. Please disregard the invitation\n"
                    "previously sent.\n"
                    "\n"
                    "----\n"
                    "This email was automatically sent from ${site_name}\n"
                    "to ${email_address}"
            },
            "enrolled_unenroll": {
                "subject": "You have been un-enrolled from ${course_name}",
                "body":
                    "\n"             
                    "Dear ${full_name}\n"
                    "\n"
                    "You have been un-enrolled in ${course_name} at ${site_name} by a member\n"
                    "of the course staff. The course will no longer appear on your\n"
                    "${site_name} dashboard.\n"
                    "\n"
                    "Your other courses have not been affected.\n"
                    "\n"
                    "----\n"
                    "This email was automatically sent from ${site_name} to\n"
                    "${full_name}"
            },
            "order_confirmation_email": {
                "subject": "Order Payment Confirmation",
                "body":
                    "Hi ${order.user.profile.name}\n"
                    "\n"
                    "Your payment was successful. You will see the charge below on your next credit or debit card statement.\n"
                    "The charge will show up on your statement under the company name ${settings.CC_MERCHANT_NAME}.\n"
                    "If you have billing questions, please contact ${settings.PAYMENT_SUPPORT_EMAIL}.\n"
                    "-The ${settings.PLATFORM_NAME} Team\n"
                    "\n"
                    "Your order number is: ${order.id}\n"
                    "\n"
                    "The items in your order are:\n"
                    "\n"
                    "Quantity - Description - Price\n"
                    "%for order_item in order_items:\n"
                    "${order_item.qty} - ${order_item.line_desc} - ${'$'' if order_item.currency == 'usd' else ''}${order_item.line_cost}\n" 
                    "%endfor\n"
                    "\n"
                    "Total billed to credit/debit card: ${order.total_cost}${'$'' if order.currency == 'usd' else '')}\n"
                    "\n"
                    "% if has_billing_info:"
                    "${order.bill_to_cardtype} ${_('#:'')} ${order.bill_to_ccnum}"
                    "${order.bill_to_first} ${order.bill_to_last}"
                    "${order.bill_to_street1}"
                    "${order.bill_to_street2}"
                    "${order.bill_to_city}, ${order.bill_to_state} ${order.bill_to_postalcode}"
                    "${order.bill_to_country.upper()}"
                    "% endif"
                    "\n"
                    "%for order_item in order_items:\n"
                    "${order_item.additional_instruction_text}\n"
                    "%endfor\n"
            }
        },
    },
    "edge": {
        # if set will render to different template in the index page
        # if not set, then the default index page will be rendered
        "university_profile_template": "university_profile/edge.html",
    }
}
