import pytest

from ryzom.html import Div, Text
from ryzom import test
from ryzom_mdc.html import *


class TestMdc(object):
    def test_mdc_top_app_bar(self):
        c = MdcTopAppBar(
            Text("Page title"),
            action_items=[
                ('more_vert', 'Options', '#'),
            ],
        )
        test.assert_equals_fixture('test_mdc_top_app_bar', c.to_html())

    def test_mdc_drawer(self):
        c = MdcDrawer(
                MdcDrawerHeader(
                    drawer_title="Title",
                    drawer_subtitle="subtitle",
                ),
                MdcNavList(
                    MdcListItem(
                        Text("Home"),
                        icon='home',
                        href='#',
                        active=True,
                    ),
                )
        )
        test.assert_equals_fixture('test_mdc_drawer', c.to_html())

    def test_mdc_app_content(self):
        c = MdcAppContent(Text('Content'))
        test.assert_equals_fixture('test_mdc_app_content', c.to_html())
