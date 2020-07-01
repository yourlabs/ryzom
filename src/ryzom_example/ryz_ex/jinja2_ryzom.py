from django.template.loader import render_to_string
from jinja2.utils import contextfunction


@contextfunction
def render_form(context, form):
    # django-betterforms has multiple calls for different forms so
    # using context['parent']['view'] isn't simple.
    # Jinja2 Context is immutable, so create our own with form parameter.
    context = dict(context=context,
                   form=form,
                   )
    return render_to_string('ryzom.components.django.Form', context)
