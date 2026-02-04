try:
    from . import site_config
except ImportError:
    from . import site_config_example as site_config


def site_settings(request):
    """Make site configuration available to all templates."""
    return {
        'SITE_TITLE': getattr(site_config, 'SITE_TITLE', 'Memorial Page'),
        'SITE_SUBTITLE': getattr(site_config, 'SITE_SUBTITLE', 'In Loving Memory'),
        'SITE_DESCRIPTION': getattr(site_config, 'SITE_DESCRIPTION', ''),
        'PERSON_IMAGE': getattr(site_config, 'PERSON_IMAGE', 'images/person.png'),
        'HEADER_GRADIENT_START': getattr(site_config, 'HEADER_GRADIENT_START', '#667eea'),
        'HEADER_GRADIENT_END': getattr(site_config, 'HEADER_GRADIENT_END', '#764ba2'),
    }
