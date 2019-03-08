from ryzom.models import Publications

to_publish = []


class Subscription():
    def __init__(self, name, params):
        pub = Publications.objects.get(name=name)
        if pub:
            self.name = name
            self.params = params
            self.publication = pub


class Publishable():
    _published = False
    _prepubs = {}

    @classmethod
    def publish(cls, name, template=None, query={}):
        if not cls._published:
            cls._prepubs[name] = (template, query)
            if cls not in to_publish:
                to_publish.append(cls)
        else:
            cls.do_publish(name, template, query)

    @classmethod
    def do_publish(cls, name, template, query):
        tmpl_cls, tmpl_mod = template[::-1].split('.', 1)
        tmpl_mod = tmpl_mod[::-1]
        tmpl_cls = tmpl_cls[::-1]
        kwargs = {
            'name': name,
            'model_module': cls.__module__,
            'model_class': cls.__name__,
            'template_module': tmpl_mod,
            'template_class': tmpl_cls,
            'query': query
        }
        Publications.objects.update_or_create(**kwargs)

    @classmethod
    def publish_all(cls):
        cls._published = True
        for k, v in cls._prepubs.items():
            name, template, query = k, *v
            cls.do_publish(name, template, query)
