'''
Defines the Publishable class and the module level variable
to_publish.
'''
to_publish = []
'''
This variable is intented to be used only in the ryzom.apps
AppConfig.ready() to populate the DB with publications
at server startup.
'''


class Publishable:
    '''
    The publishable class is meant to be inherited from
    by end user models. It defines a publish class method
    that's used to create a publication associated with the
    model inherited from it.
    '''
    _published = False
    _prepubs = {}

    @classmethod
    def publish(cls, name, template=None):
        '''
        This method permit the publication of a model
        specifying the (unique) name of the publication,
        the template used to render the model inheriting from
        this class, and the query that will filter, order,
        limit, ..etc, the set published.
        It defers the publication until the DB is ready to
        accept new entries.

        :param str name: A unique name
        :param str template: A Component module and class \
                `module.submodule.Class`
        :param list query: A list of dict of query parameters

        :examples:
            ::

                Task.publish('task', 'todos.components.task.Task', [
                    {'order_by': '-about'},
                    {'limit': 5},
                    {'offset': 3}
                ])
        '''
        if not cls._published:
            if not cls in cls._prepubs:
                cls._prepubs[cls] = {}
            cls._prepubs[cls][name] = template
            if cls not in to_publish:
                to_publish.append(cls)
        else:
            cls.do_publish(name, template)

    @classmethod
    def do_publish(cls, name, template):
        '''f
        This method actually created the real publication,
        called by the publish_all() method, or by publish()
        if the publishable has already been published.
        If a publication of given name already exists,
        this method only updates its fields.

        :parameters: see :meth:`publish`
        '''
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

    @classmethod
    def publish_all(cls):
        '''
        This method is called by the ryzom.apps AppConfig.ready()
        at server startup to populate the DB with the publications
        associated to the current model class.
        '''
        cls._published = True
        for k, v in cls._prepubs[cls].items():
            name, template = k, v
            cls.do_publish(name, template)


def publish(component):
    def func_wrapper(func):
        @classmethod
        def wrapper(*args):
            cls = args[0]
            if not cls._published:
                cls.publish(func.__name__, component)
            else:
                return func(*args)
        return wrapper
    return func_wrapper
