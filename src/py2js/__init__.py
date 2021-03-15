from .transpiler import transpile, transpile_body, transpile_class


class Mixin:
    py2js = None

    def render_js(self):
        if self.py2js:
            return transpile_body(self.py2js, self=self)


class HTMLElementMixin:
    HTMLElement = None

    @classmethod
    def render_js(cls):
        if cls.HTMLElement:
            return transpile_class(
                cls.HTMLElement,
                superclass='HTMLElement',
                newname=cls.__name__,
            )
