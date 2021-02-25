'''
Ryzom is a reactive full-stack Python framework built on top of the Django
framework.
Ryzom is highly inspired by the open source software MeteorJS; if you like
JavaScript and don't know it, please give it a try!

Ryzom will always stay open source.
'''
default_app_config = 'ryzom.apps.BaseConfig'


templates = dict()
def template(name, *wrappers):
    from ryzom.components.components import CTree
    global templates
    def decorator(component):
        templates[name] = CTree(*wrappers + (component,))
        return component
    return decorator
