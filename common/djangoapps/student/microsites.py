from django.conf import settings


def get_microsite_config(request):
    if not settings.FEATURES.get("MICROSITES"):
        # microsites is not enabled
        return {}

    domain = request.META.get('HTTP_HOST')
    domain_parts = domain.split(".")
    # which site are we in?
    for subdomain, config in settings.MICROSITES.items():
        if domain_parts[0] == subdomain:
            return config

    # not found
    return {}


def get_microsite_tpl_func(request):
    config = get_microsite_config(request)

    def microsite_tpl_path(path):
        if not config:
            return path

        if "template_dir" in config:
            return config["template_dir"] / path

        subdomain = request.META.get("HTTP_HOST").split(".")[0]
        dirname = config.get("directory", subdomain)
        subdir = settings.ENV_ROOT / "microsites" / dirname
        template_dir = subdir / "templates"
        return template_dir / path

    return microsite_tpl_path
