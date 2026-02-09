try:
    from . import site_config
except ImportError:
    from . import site_config_example as site_config


def get_site_config(key, default):
    """Get a config value from site_config."""
    return getattr(site_config, key, default)


def site_settings(request):
    """Make site configuration available to all templates."""
    return {
        'SITE_TITLE': get_site_config('SITE_TITLE', 'Memorial Page'),
        'SITE_SUBTITLE': get_site_config('SITE_SUBTITLE', 'In Loving Memory'),
        'SITE_DESCRIPTION': get_site_config('SITE_DESCRIPTION', ''),
        'PERSON_IMAGE': get_site_config('PERSON_IMAGE', 'images/person.png'),
        'HEADER_GRADIENT_START': get_site_config('HEADER_GRADIENT_START', '#667eea'),
        'HEADER_GRADIENT_END': get_site_config('HEADER_GRADIENT_END', '#764ba2'),
        'REQUIRE_APPROVAL': get_site_config('REQUIRE_APPROVAL', False),
        'BACKGROUND_IMAGE': get_site_config('BACKGROUND_IMAGE', ''),
        'THEME': get_site_config('THEME', 'default'),
        'CONTACT_EMAIL_USER': get_site_config('CONTACT_EMAIL', '').split('@')[0] if get_site_config('CONTACT_EMAIL', '') else '',
        'CONTACT_EMAIL_DOMAIN': get_site_config('CONTACT_EMAIL', '').split('@')[1] if '@' in get_site_config('CONTACT_EMAIL', '') else '',
        'FOOTER_TEXT': get_site_config('FOOTER_TEXT', ''),
        'CONTACT_PROMPT': get_site_config('CONTACT_PROMPT', 'Questions?'),
    }
