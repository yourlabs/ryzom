'''
Defines the ReactiveComponent class to be inherited
to create reactive content
'''
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

from ryzom.components import Component


class ReactiveComponent(Component):
    '''
    Subclass of component with reactive content.
    It takes a unique name and a ryzom.views.View in addition
    to common component parameters.

    :param str name: The (unique) name of the instance
    :param View view: The rizom View this instance is attached to
    '''
    def __init__(self, name, view, *content, **attrs):
        self.name = name
        self.view = view
        super().__init__(*content, **attrs)
        self.view.addReactiveComponent(self)

    def setcontent(self, content):
        '''
        This method should be called only by the associated view
        to update the component contents, then it sends the new
        content to the client associated with the view instance

        :param list(Component) content: A list of Component to replace \
                the current content of the instance
        '''
        self.content = content
        self.preparecontent()
        channel_name = self.view.request.client.channel
        if channel_name:
            channel = get_channel_layer()
            async_to_sync(channel.send)(channel_name, {
                'type': 'handle.ddp',
                'params': {
                    'type': 'changed',
                    'instance': self.to_obj()
                }
            })


class ReactiveDiv(ReactiveComponent):
    def __init__(self, name, view, *content):
        attrs = {
            'tag': 'div',
            '_id': f'reactive_div_{name}',
        }
        super().__init__(name, view, *content, **attrs)
