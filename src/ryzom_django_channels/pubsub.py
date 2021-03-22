'''
Defines the Publishable class and the module level variable
to_publish.
'''


class Publishable:
    '''
    The publishable class is meant to be inherited from
    by end user models. It defines a publish class method
    that's used to create a publication associated with the
    model inherited from it.
    '''

    @classmethod
    def publish(cls):
        for method in cls.__dict__.values():
            if getattr(method, '__publication__', False):
                cls.create_publication(
                    getattr(method, '__name__'),
                    getattr(method, '__template__')
                )

    @classmethod
    def create_publication(cls, name, template):
        from ryzom_django_channels.models import Publication

        tmpl_mod, tmpl_cls = template.rsplit('.', 1)
        kwargs = {
            'model_module': cls.__module__,
            'model_class': cls.__name__,
            'template_module': tmpl_mod,
            'template_class': tmpl_cls,
        }
        pub_exists = Publication.objects.filter(name=name).exists()
        if pub_exists:
            pub = Publication.objects.get(name=name)
            changed = False
            for k, v in kwargs.items():
                if getattr(pub, k, None) != v:
                    setattr(pub, k, v)
                    changed = True
            if changed:
                pub.save()
        else:
            Publication.objects.create(name=name, **kwargs)


def publish(component):
    def func_wrapper(func):
        @classmethod
        def wrapper(*args):
            return func(*args)
        wrapper.__publication__ = True
        wrapper.__template__ = component
        wrapper.__name__ = func.__name__
        return wrapper
    return func_wrapper
