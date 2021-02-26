from ryzom import html


@html.template('django/forms/widgets/input.html')
@html.template('django/forms/widgets/text.html')
class MDCInputWidget(html.Input):
    def __init__(self, **context):
        attrs = {'class': 'mdc-text-field__input'}
        attrs['type'] = context.get('type', 'text')
        if 'widget' in context:
            attrs.update(context['widget']['attrs'])
            attrs.update(dict(
                name=context['widget']['name'],
                value=context['widget']['value'],
            ))
        super().__init__(**attrs)
