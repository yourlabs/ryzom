#! /usr/bin/env python

import ast
import inspect
import textwrap
import re

from . import formater


def scope(func):
    func.scope = True
    return func

class JSError(Exception):
    pass

class JS(object):

    name_map = {
        'self'   : 'this',
        'True'   : 'true',
        'False'  : 'false',
        'None'  : 'null',

        'int' : '_int',
        'float' : '_float',

        'super' : '_super',
        'print' : 'console.log',

        # ideally we should check, that this name is available:
        'py_builtins' : '___py_hard_to_collide',
    }

    builtin = set([
        'NotImplementedError',
        'ZeroDivisionError',
        'AssertionError',
        'AttributeError',
        'RuntimeError',
        'ImportError',
        'TypeError',
        'ValueError',
        'NameError',
        'IndexError',
        'KeyError',
        'StopIteration',

        '_int',
        '_float',
        'max',
        'min',
        'sum',
    ])

    bool_op = {
        'And'    : ' && ',
        'Or'     : ' || ',
    }

    unary_op = {
        'Invert' : '~',
        'Not'    : '!',
        'UAdd'   : '+',
        'USub'   : '-',
    }

    binary_op = {
        'Add'    : '+',
        'Sub'    : '-',
        'Mult'   : '*',
        'Div'    : '/',
        'Mod'    : '%',
        'LShift' : '<<',
        'RShift' : '>>',
        'BitOr'  : '|',
        'BitXor' : '^',
        'BitAnd' : '&',
    }

    comparison_op = {
            'Eq'    : " == ",
            'NotEq' : " != ",
            'Lt'    : " < ",
            'LtE'   : " <= ",
            'Gt'    : " > ",
            'GtE'   : " >= ",
            'Is'    : " === ",
            'IsNot' : "is not", # Not implemented yet
        }

    funcs = {
            'range' : 'visit_Range',
            'len': 'visit_Len',
    }

    def __init__(self, context=None):
        self.__formater = formater.Formater()
        self.write = self.__formater.write
        self.read = self.__formater.read
        self.indent = self.__formater.indent
        self.dedent = self.__formater.dedent
        self.dummy = 0
        self.classes = ['dict', 'list', 'tuple']
        # This is the name of the class that we are currently in:
        self._class_name = None

        # This lists all variables in the local scope:
        self._scope = []
        #All calls to names within _class_names will be preceded by 'new'
        self._class_names = set()
        self._classes = {}
        self._functions = {}

        if context:
            _copy_context = context.copy()
            for key in _copy_context.keys():
                if callable(_copy_context[key]):
                    value = context.pop(key)
                    source = inspect.getsource(value)
                    source = textwrap.dedent(source)
                    tree = ast.parse(source)
                    sub = JS()
                    sub.visit(tree)
                    self.write(sub.read())

        self._context = context or {}

    def new_dummy(self):
        dummy = "__dummy%d__" % self.dummy
        self.dummy += 1
        return dummy

    def name(self, node):
        return node.__class__.__name__

    def get_bool_op(self, node):
        return self.bool_op[node.op.__class__.__name__]

    def get_unary_op(self, node):
        return self.unary_op[node.op.__class__.__name__]

    def get_binary_op(self, node):
        return self.binary_op[node.op.__class__.__name__]

    def get_comparison_op(self, node):
        return self.comparison_op[node.__class__.__name__]

    def visit(self, node, scope=None):
        try:
            visitor = getattr(self, 'visit_' + self.name(node))
        except AttributeError:
            raise JSError("syntax not supported (%s)" % node)

        if hasattr(visitor, 'statement'):
            return visitor(node, scope)
        else:
            return visitor(node)

    def visit_Module(self, node):
        for stmt in node.body:
            self.visit(stmt)

    def visit_AsyncFunctionDef(self, node):
        self.is_async = True
        self.visit_FunctionDef(node)

    def visit_Await(self, node):
        return f'await {self.visit(node.value)}'

    @scope
    def visit_FunctionDef(self, node):
        is_static = False
        is_javascript = False
        if node.decorator_list:
            if len(node.decorator_list) == 1 and \
                    isinstance(node.decorator_list[0], ast.Name) and \
                    node.decorator_list[0].id == "JavaScript":
                is_javascript = True # this is our own decorator
            elif self._class_name and \
                    len(node.decorator_list) == 1 and \
                    isinstance(node.decorator_list[0], ast.Name) and \
                    node.decorator_list[0].id == "staticmethod":
                is_static = True
            else:
                raise JSError("decorators are not supported")

        # XXX: disable $def for now, because it doesn't work in IE:
        if self._class_name:
        #if 1:
            if node.args.vararg is not None:
                raise JSError("star arguments are not supported")

            if node.args.kwarg is not None:
                raise JSError("keyword arguments are not supported")

            if node.decorator_list and not is_static and not is_javascript:
                raise JSError("decorators are not supported")

            defaults = [None]*(len(node.args.args) - len(node.args.defaults)) + node.args.defaults

            js_args = []
            js_defaults = []
            self._scope = [arg for arg in node.args.args]

            for arg, default in zip(node.args.args, defaults):
                if not isinstance(arg, ast.arg):
                    raise JSError("tuples in argument list are not supported")

                js_args.append(arg.arg)

                if default is not None:
                    js_defaults.append("%(id)s = typeof(%(id)s) != 'undefined' ? %(id)s : %(def)s;\n" % { 'id': arg.arg, 'def': self.visit(default) })

            if self._class_name:
                prep = "%s.prototype.%s = function(" % \
                        (self._class_name, node.name)
                if not is_static:
                    if not (js_args[0] == "self"):
                        raise NotImplementedError("The first argument must be 'self'.")
                    del js_args[0]
            else:
                prep = "function %s(" % node.name
            self.write(prep + ", ".join(js_args) + ") {")
            self.indent()
            for stmt in js_defaults:
                self.write(stmt)
            for stmt in node.body:
                self.visit(stmt)
            self.dedent()
            self.write('}')

            #If method is static, we also add it directly to the class
            if is_static:
                self.write("%s.%s = %s.prototype.%s;" % \
                        (self._class_name, node.name, self._class_name, node.name))
            #Otherwise, we wrap it to take 'self' into account
            else:
                func_name = node.name
                self.write("%s.%s = function() {" % (self._class_name, func_name))
                self.write("    %s.prototype.%s.apply(arguments[0],Array.slice(arguments,1));"% (self._class_name, func_name))
                self.write("}")

            self._scope = []
        else:
            _args = [arg for arg in node.args.args if arg.arg != 'self']
            defaults = [None]*(len(_args) - len(node.args.defaults)) + node.args.defaults

            args = []
            defaults2 = {}
            for arg, default in zip(_args, defaults):
                if arg.arg == 'self':
                    continue
                if not isinstance(arg, ast.arg):
                    raise JSError("tuples in argument list are not supported")
                if default:
                    args.append(f'{arg.arg} = {self.visit(default)}')
                else:
                    args.append(arg.arg)
            args = ", ".join(args)
            func_name = node.name
            if func_name == '__init__':
                func_name = 'constructor'
            if node.args.args and node.args.args[0].arg == 'self':
                prep = "%s(%s) {" % (func_name, args)
            else:
                prep = "function %s(%s) {" % (func_name, args)
            if getattr(self, 'is_async', False):
                prep = 'async ' + prep
                self.is_async = False
            self.write(prep)
            self._scope = [arg.arg for arg in node.args.args]
            self.indent()
            for stmt in node.body:
                self.visit(stmt)
            self.dedent()
            self.write("}")

    @scope
    def visit_ClassDef(self, node):
        if node.bases:
            self.write(f"class {node.name} extends {node.bases[0].id}" + " {")
        else:
            self.write(f"class {node.name}" + " {")
        self.indent()

        for stmt in node.body:
            if isinstance(stmt, ast.Assign):
                value = self.visit(stmt.value)
                for t in stmt.targets:
                    var = self.visit(t)
                    self.write("%s = %s;" % (var, value))
            else:
                self.visit(stmt)

        self.dedent()
        self.write("}")

    def visit_Return(self, node):
        if node.value is not None:
            self.write("return %s;" % self.visit(node.value))
        else:
            self.write("return;")

    def visit_Delete(self, node):
        return node

    @scope
    def visit_Assign(self, node):
        assert len(node.targets) == 1
        target = node.targets[0]
        value = self.visit(node.value)
        var = self.visit(target)
        if isinstance(target, ast.Name):
            if not (var in self._scope):
                self._scope.append(var)
                declare = "var "
            else:
                declare = ""
            self.write("%s%s = %s;" % (declare, var, value))
        elif isinstance(target, ast.Attribute):
            js = self.write("%s.%s = %s;" % (self.visit(target.value), str(target.attr), value))
        elif isinstance(target, ast.Subscript):
            js = self.write(f"{self.visit(target)} = {value};")
        else:
            raise JSError("Unsupported assignment type")

    def visit_AugAssign(self, node):
        # TODO: Make sure that all the logic in Assign also works in AugAssign
        target = self.visit(node.target)
        value = self.visit(node.value)

        if isinstance(node.op, ast.Pow):
            self.write("%s = Math.pow(%s, %s);" % (target, target, value))
        if isinstance(node.op, ast.FloorDiv):
            self.write("%s = Math.floor((%s)/(%s));" % (target, target, value))

        self.write("%s %s= %s;" % (target, self.get_binary_op(node), value))

    @scope
    def visit_For(self, node):
        if not isinstance(node.target, ast.Name):
            raise JSError("argument decomposition in 'for' loop is not supported")

        for_target = self.visit(node.target)
        for_iter = self.visit(node.iter)

        self.write(f"for (const {for_target} of {for_iter}) {{")
        self.indent()
        for stmt in node.body:
            self.visit(stmt)
        self.dedent()
        self.write("}")

        if node.orelse:
            self.write("if (%s) {" % orelse_dummy)
            self.indent()
            for stmt in node.orelse:
                self.visit(stmt)
            self.dedent()
            self.write("}")

    @scope
    def visit_While(self, node):

        if not node.orelse:
            self.write("while (%s) {" % self.visit(node.test))
        else:
            orelse_dummy = self.new_dummy()

            self.write("var %s = false;" % orelse_dummy)
            self.write("while (1) {");
            self.write("    if (!(%s)) {" % self.visit(node.test))
            self.write("        %s = true;" % orelse_dummy)
            self.write("        break;")
            self.write("    }")
        self.indent()
        for stmt in node.body:
            self.visit(stmt)
        self.dedent()

        self.write("}")

        if node.orelse:
            self.write("if (%s) {" % orelse_dummy)
            self.indent()
            for stmt in node.orelse:
                self.visit(stmt)
            self.dedent()
            self.write("}")

    @scope
    def visit_If(self, node):
        self.write("if (%s) {" % self.visit(node.test))
        self.indent()
        for stmt in node.body:
            self.visit(stmt)
        self.dedent()
        if node.orelse:
            self.write("} else {")
            self.indent()
            for stmt in node.orelse:
                self.visit(stmt)
            self.dedent()
        self.write("}")

    @scope
    def _visit_With(self, node):
        pass

    @scope
    def _visit_Raise(self, node):
        pass

    @scope
    def _visit_TryExcept(self, node):
        pass

    @scope
    def _visit_TryFinally(self, node):
        pass

    def visit_Assert(self, node):
        test = self.visit(node.test)

        if node.msg is not None:
            self.write("assert(%s, %s);" % (test, self.visit(node.msg)))
        else:
            self.write("assert(%s);" % test)

    def _visit_Import(self, node):
        pass

    def _visit_ImportFrom(self, node):
        pass

    def _visit_Exec(self, node):
        pass

    def visit_Global(self, node):
        self._scope.extend(node.names)

    def visit_Expr(self, node):
        self.write(self.visit(node.value) + ";")

    def visit_Pass(self, node):
        self.write("/* pass */")

    def visit_Break(self, node):
        self.write("break;")

    def visit_Continue(self, node):
        self.write("continue;")

    def visit_arguments(self, node):
        return ", ".join([self.visit(arg) for arg in node.args])

    def visit_arg(self, node):
        return node.arg

    def visit_Lambda(self, node):
        args = self.visit(node.args)
        body = self.visit(node.body)
        formater = self.__formater
        indent = formater._Formater__indent_string * (formater._Formater__indentation + 1)
        indent2 = formater._Formater__indent_string * formater._Formater__indentation
        return "\n%s(%s) => {return %s}\n%s" % (indent, args, body, indent2)

    def visit_BoolOp(self, node):
        op = self.get_bool_op(node).join([ "%s" % self.visit(val) for val in node.values ])
        return f'({op})'

    def visit_UnaryOp(self, node):
        return "%s(%s)" % (self.get_unary_op(node), self.visit(node.operand))

    def visit_BinOp(self, node):
        if isinstance(node.op, ast.Mod) and isinstance(node.left, ast.Str):
            left = self.visit(node.left)
            if isinstance(node.right, (ast.Tuple, ast.List)):
                right = self.visit(node.right)
                return "vsprintf(js(%s), js(%s))" % (left, right)
            else:
                right = self.visit(node.right)
                return "sprintf(js(%s), %s)" % (left, right)
        left = self.visit(node.left)
        right = self.visit(node.right)

        if isinstance(node.op, ast.Pow):
            return "Math.pow(%s, %s)" % (left, right)
        if isinstance(node.op, ast.FloorDiv):
            return "Math.floor((%s)/(%s))" % (left, right)

        return "(%s %s %s)" % (left, self.get_binary_op(node), right)

    def visit_Compare(self, node):
        assert len(node.ops) == 1
        assert len(node.comparators) == 1
        op = node.ops[0]
        comp = node.comparators[0]
        if isinstance(op, ast.In):
            return "%s.includes(%s)" % (
                    self.visit(comp),
                    self.visit(node.left),
                    )
        elif isinstance(op, ast.NotIn):
            return "!(%s.includes(%s))" % (
                    self.visit(comp),
                    self.visit(node.left),
                    )
        else:
            return "%s %s %s" % (self.visit(node.left),
                    self.get_comparison_op(op),
                    self.visit(comp)
                    )

    def visit_Name(self, node):
        id = node.id
        try:
            id = self.name_map[id]
        except KeyError:
            pass

        if id in self.builtin:
            id = "py_builtins." + id;

        #~ if id in self._classes:
            #~ id = '_' + id;
        elif self._context and id in self._context:
            value = self._context[id]
            if isinstance(value, str):
                return "\"%s\"" % value
            else:
                return "%s" % value

        return id

    def visit_Constant(self, node):
        if isinstance(node.value, str):
            return self.visit_Str(node)
        elif isinstance(node.value, bool):
            return 'true' if node.value else 'false'
        else:
            return self.visit_Num(node)

    def visit_Num(self, node):
        return node.n

    def visit_Str(self, node):
        # Uses the Python builtin repr() of a string and the strip string type
        # from it. This is to ensure Javascriptness, even when they use things
        # like b"\\x00" or u"\\u0000".
        return "%s" % repr(node.s).lstrip("urb")

    def visit_Call(self, node):
        func = self.visit(node.func)
        #~ if func in self._class_names:
            #~ func = 'new '+func
        if node.keywords:
            keywords = []
            for kw in node.keywords:
                keywords.append("%s: %s" % (kw.arg, self.visit(kw.value)))
            keywords = "{" + ", ".join(keywords) + "}"
            js_args = ",".join([ self.visit(arg) for arg in node.args ])
            return "%s.args([%s], %s)" % (func, js_args,
                    keywords)
        else:
            if getattr(node, 'starargs', None) is not None:
                raise JSError("star arguments are not supported")

            if getattr(node, 'kwargs', None) is not None:
                raise JSError("keyword arguments are not supported")

            try:
                js_args = ",".join([str(self.visit(arg)) for arg in node.args ])
            except:
                raise

            if func in self.funcs.keys():
                method = getattr(self, self.funcs[func])
                return method(js_args)

            return "%s(%s)" % (func, js_args)

    def visit_Raise(self, node):
        assert node.inst is None
        assert node.tback is None
        self.write("throw %s;" % self.visit(node.type))

    def visit_Print(self, node):
        assert node.dest is None
        assert node.nl
        values = [self.visit(v) for v in node.values]
        values = ", ".join(values)
        self.write("py_builtins.print(%s);" % values)

    def visit_Attribute(self, node):
        if (
            isinstance(node.value, ast.Name)
            and node.value.id in self._context
            and hasattr(self._context[node.value.id], node.attr)
        ):
            obj = self._context[node.value.id]
            value = getattr(obj, node.attr)
            if isinstance(value, str):
                return f'"{value}"'
            elif callable(value):
                base_name = ''
                try:
                    for cls in inspect.getmro(value.__self__.__class__):
                        if value.__name__ in cls.__dict__:
                            base_name = cls.__name__
                except AttributeError:
                    pass
                if not base_name:
                    base_name = getattr(obj, '__name__', type(obj).__name__)
                name = base_name + f'_{node.attr}'
                if name not in self._functions:
                    self._functions[name] = value
                return name
            elif str(value) in self.name_map:
                return self.name_map[str(value)]
            elif isinstance(value, (int, float)):
                return f'{value}'
            else:
                return value

        value = self.visit(node.value)

        if value == 'new':
            return "%s %s" % (value, node.attr)

        if not isinstance(value, str):
            value = getattr(value, node.attr)
            if isinstance(value, str):
                return f'"{value}"'
            return value
        return "%s.%s" % (self.visit(node.value), node.attr)

    def visit_Tuple(self, node):
        els = [self.visit(e) for e in node.elts]
        return "[%s]" % (", ".join(els))

    def visit_Dict(self, node):
        els = []
        for k, v in zip(node.keys, node.values):
            els.append('%s: %s' % (self.visit(k), self.visit(v)))

        if len(els) > 1:
            indent_str = self.__formater._Formater__indent_string
            indent_lvl = self.__formater._Formater__indentation
            indent = indent_str * indent_lvl
            indent2 = indent + indent_str
            return "{\n%s%s\n%s}" % (indent2, f",\n{indent2}".join(els), indent)
        return "{%s}" % (", ".join(els))

    def visit_List(self, node):
        els = [str(self.visit(e)) for e in node.elts]
        return "[%s]" % (", ".join(els))

    def visit_Slice(self, node):
        if node.lower and node.upper and node.step:
            return "slice(%s, %s, %s)" % (self.visit(node.lower),
                    self.visit(node.upper), self.visit(node.step))
        if node.lower and node.upper:
            return "slice(%s, %s)" % (self.visit(node.lower),
                    self.visit(node.upper))
        if node.upper and not node.step:
            return "slice(%s)" % (self.visit(node.upper))
        if node.lower and not node.step:
            return "slice(%s, null)" % (self.visit(node.lower))
        if not node.lower and not node.upper and not node.step:
            return "slice(null)"
        raise NotImplementedError("Slice")

    def visit_Subscript(self, node):
        return "%s[%s]" % (self.visit(node.value), self.visit(node.slice))

    def visit_Index(self, node):
        return self.visit(node.value)

    #specifics
    def visit_Range(self, args):
        return f"[...Array({args}).keys()]"

    def visit_Len(self, args):
        return f"{args}.length"


def convert_py2js(s, context=None):
    """
    Takes Python code as a string 's' and converts this to JavaScript.

    Example:

    >>> convert_py2js("x[3:]")
    'x.__getitem__(slice(3, null));'

    """
    t = ast.parse(textwrap.dedent(s))
    v = JS(context)
    v.visit(t)
    js = v.read()
    return js


def transpile(obj_or_src, **context):
    """
    Transpile a Python object or source code into javascript.
    """
    if isinstance(obj_or_src, str):
        src = obj_or_src
    else:
        src = inspect.getsource(obj_or_src)
    return convert_py2js(src, context)


def transpile_body(obj, **context):
    src = inspect.getsource(obj)
    src = '\n'.join(src.split('\n')[1:])
    src = textwrap.dedent(src)
    return transpile(src, **context)


def transpile_class(cls, superclass=None, newname=None, **context):
    src = inspect.getsource(cls)
    lines = src.split('\n')
    if newname:
        lines[0] = re.sub('class ([^:])*:', f'class {newname}:', lines[0])
    if superclass:
        lines[0] = re.sub('[()]*:', f'({superclass}):', lines[0])
    src = '\n'.join(lines)
    src = textwrap.dedent(src)
    return transpile(src, **context)


def transpile_function(func, newname=None, **context):
    src = inspect.getsource(func)
    src = textwrap.dedent(src)
    lines = src.split('\n')
    if newname:
        lines[0] = re.sub('def ([^(])*', f'def {newname}', lines[0])
    src = '\n'.join(lines)
    return transpile(src, **context)
