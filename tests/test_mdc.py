import pytest

from ryzom.components import component_html, Div, Text
from ryzom.components.mdc import *
from ryzom.test import pretty


class TestMdc(object):

    def test_mdc_top_app_bar(self):
        c = MdcTopAppBar(Text("Page title"))
        assert pretty(c.to_html()) == '''%header
  class=mdc-top-app-bar app-bar
  data-mdc-auto-init=MDCTopAppBar
  id=app-bar
  %div
    class=mdc-top-app-bar__row
    %section
      class=mdc-top-app-bar__section mdc-top-app-bar__section--align-start
      %button
        aria-label=Open navigation menu
        class=material-icons mdc-top-app-bar__navigation-icon mdc-icon-button
        menu
      %span
        class=mdc-top-app-bar__title
        Page title
        '''.strip()

    def test_mdc_drawer(self):
        c = MdcDrawer(
                MdcNavList(
                    MdcListItem(
                        Text("Home"),
                        icon='home',
                        href='#',
                        active=True,
                    ),
                )
        )
        assert pretty(c.to_html()) == '''%aside
  class=mdc-drawer mdc-drawer--dismissible mdc-top-app-bar--fixed-adjust
  data-mdc-auto-init=MDCDrawer
  %div
    class=mdc-drawer__content
    %nav
      class=mdc-list
      %a
        aria-current=page
        class=mdc-list-item mdc-list-item--activated
        href=#
        tabindex=0
        %span
          class=mdc-list-item__ripple
        %i
          aria-hidden=true
          class=material-icons mdc-list-item__graphic
          home
        %span
          class=mdc-list-item__text
          Home
       '''.strip()

    def test_mdc_app_content(self):
        c = MdcAppContent(Text('Content'))
        assert pretty(c.to_html()) == '''%div
  class=mdc-drawer-app-content mdc-top-app-bar--fixed-adjust
  %main
    class=main-content
    id=main-content
    Content
        '''.strip()

    def pass_test_mdc_text_input(self):
        c = MdcTextInput()
        assert pretty(c) == '''%label
            class=mdc-text-field mdc-text-field--filled mdc-text-field--label-floating
            %span
                class=mdc-text-field__ripple
            %input
                class=mdc-text-field__input
                type=text
                aria-labelledby=label-id
                value=
            %span
                class=mdc-floating-label mdc-floating-label--float-above
                id=label-id
                Label
            %span
                class=mdc-line-ripple
        '''.strip()

