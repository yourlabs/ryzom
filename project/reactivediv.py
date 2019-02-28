from project.component import Div
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer


class ReactiveDiv(Div):
    def __init__(self, name, view, content):
        super().__init__(content=content, _id=f'reactive_div_{name}')
        self.name = name
        self.view = view
        self.view.addReactiveDiv(self)

    def setcontent(self, content):
        self.content = content
        self.preparecontent()
        channel_name = self.view.channel_name
        channel = get_channel_layer()
        async_to_sync(channel.send)(channel_name, {
            'type': 'handle.ddp',
            'params': {
                'type': 'changed',
                'instance': self.to_obj()
            }
        })
