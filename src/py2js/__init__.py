from .transpiler import transpile, transpile_body, transpile_class


class Mixin:
    py2js = None

    def render_js(self):
        if self.py2js:
            return transpile_body(self.py2js, self=self)


class HTMLElementMixin:
    HTMLElement = None

    def render_js(self):
        if self.HTMLElement:
            return transpile_class(
                self.HTMLElement,
                superclass='HTMLElement',
                newname=type(self).__name__,
            )
