class View():
    def __init__(self, channel_name):
        self.channel_name = channel_name
        self.reactive_divs = {}

    def addReactiveDiv(self, div):
        self.reactive_divs[div.name] = div

    def setcontent(self, name, content):
        div = self.reactive_divs[name]
        div.setcontent(content)

    def onurl(self, url):
        raise NotImplementedError

    def render(self, url):
        raise NotImplementedError

    def oncreate(self, url):
        pass

    def ondestroy(self, url):
        pass
