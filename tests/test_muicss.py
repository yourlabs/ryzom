from django.test import SimpleTestCase, override_settings

from ryzom_example.settings import (
    CRUDLFAP_TEMPLATE_BACKEND, DEFAULT_TEMPLATE_BACKEND
)

from .test_django import NonModelFormTest


@override_settings(TEMPLATES=[
    # CRUDLFAP_TEMPLATE_BACKEND,
    # DEFAULT_TEMPLATE_BACKEND,
    {
        "BACKEND": "ryzom.backends.ryzom.Ryzom",
        "OPTIONS": {
            "app_dirname": "components",
            "components_module": "ryzom.components.muicss",
            # "components_prefix": "Mui",
        },
    },
])
class TestMuiNonModelForm(NonModelFormTest, SimpleTestCase):
    prefix = "Mui"
    pass
