"""
This app contains Mailchimp client and related tasks to send data to Mailchimp

Mailchimp client is based on third-party library mailchimp3, which provides an easy to use python wrapper over
mandrill APIs. Mandrill client depends on MAILCHIMP_API_KEY and MAILCHIMP_LIST_ID. In unit test it is recommended
to mock client so that there is no external dependency on code which also means no need for api keys.
"""
default_app_config = 'openedx.adg.common.mailchimp_pipeline.apps.MailchimpPipelineConfig'
