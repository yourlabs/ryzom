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
                cls.create_publication(getattr(method, '__name__'))

    @classmethod
    def create_publication(cls, name):
        from ryzom_django_channels.models import Publication

        model_params = dict(
            model_module=cls.__module__,
            model_class=cls.__name__,
        )
        if pub := Publication.objects.filter(name=name).first():
            changed = False
            for k, v in model_params.items():
                if getattr(pub, k, None) != v:
                    setattr(pub, k, v)
                    changed = True
            if changed:
                pub.save()
        else:
            Publication.objects.create(name=name, **model_params)


def publish(func):
    @classmethod
    def wrapper(*args):
        return func(*args)
    wrapper.__publication__ = True
    wrapper.__name__ = func.__name__
    return wrapper
