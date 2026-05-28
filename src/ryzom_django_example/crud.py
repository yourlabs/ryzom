"""
CRUD components demo — shows ActionButton, ActionMenu, ActionDropdown
with hardcoded mock data so the example has no database dependency.
"""
from types import SimpleNamespace

from django.urls import path
from django.views import generic

from ryzom_django.html import template
from ryzom_django_mdc import html
from ryzom_django_mdc.crudlfap import ActionButton, ActionMenu, ActionDropdown


def mock_view(label, url, icon=None, color='inherit', controller=None):
    return SimpleNamespace(
        label=label,
        url=url,
        icon=icon,
        color=color,
        controller=controller,
        urlname=label.lower().replace(' ', '_'),
    )


BOOKS = [
    {'id': 1, 'title': 'The Pragmatic Programmer', 'author': 'Hunt & Thomas'},
    {'id': 2, 'title': 'Clean Code', 'author': 'Robert C. Martin'},
    {'id': 3, 'title': 'Designing Data-Intensive Applications', 'author': 'Kleppmann'},
]


class CrudDocument(html.Html):
    title = 'CRUD Components Demo'


@template('crud_demo.html', CrudDocument)
class CrudDemoComponent(html.Div):

    def to_html(self, *content, **context):
        model_actions = [
            mock_view('Create', '/crud/create/', icon='add',
                      color='var(--mdc-theme-primary)'),
            mock_view('Import', '/crud/import/', icon='upload_file'),
        ]

        rows = []
        for book in BOOKS:
            row_actions = [
                mock_view('Edit', f'/crud/{book["id"]}/edit/', icon='edit'),
                mock_view('Delete', f'/crud/{book["id"]}/delete/',
                          icon='delete', color='#c00', controller='modal'),
            ]
            rows.append(html.Tr(
                html.Td(book['title']),
                html.Td(book['author']),
                html.Td(ActionDropdown(row_actions)),
            ))

        table = html.Table(
            html.Thead(html.Tr(
                html.Th('Title', style='text-align: left; padding: 8px 16px'),
                html.Th('Author', style='text-align: left; padding: 8px 16px'),
                html.Th('Actions', style='padding: 8px 16px'),
            )),
            html.Tbody(*rows),
            style='width: 100%; border-collapse: collapse',
            cls='mdc-data-table__table',
        )

        demo = html.Div(
            html.H2('Books', style='margin-bottom: 0.5em'),
            ActionMenu(model_actions),
            html.Div(table, cls='mdc-data-table', style='width: 100%'),
            style='max-width: 900px; margin: 2em auto; padding: 0 1em',
        )

        return super().to_html(demo, *content, **context)


class CrudDemoView(generic.TemplateView):
    template_name = 'crud_demo.html'


urlpatterns = [path('', CrudDemoView.as_view())]
