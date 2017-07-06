"""
This app is used for creating/updating site's configuration. This app encapsulate configuration related logic for sites
and provides a way for sites to override default/system behavioural or presentation logic.

Models:
    SiteConfiguration (models.Model):
        This model contains configuration for a site and can be used to override OpenEdx configurations.

        Fields:
            site (OneToOneField): one to one field relating each configuration to a single site
            values (JSONField):  json field to store configurations for a site
        Usage:
            configuration of each site would be available as `configuration` attribute to django site.
            If you want to access current site's configuration simply access it as `request.site.configuration`.

    SiteConfigurationHistory (TimeStampedModel):
        This model keeps a track of all the changes made to SiteConfiguration with time stamps.

        Fields:
            site (ForeignKey): foreign-key to django Site
            values (JSONField): json field to store configurations for a site
        Usage:
            configuration history of each site would be available as `configuration_histories` attribute to django site.
            If you want to access a list of current site's configuration history simply access it as
            `request.site.configuration_histories.all()`.
"""
