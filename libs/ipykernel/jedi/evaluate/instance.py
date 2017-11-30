from abc import abstractproperty

from jedi._compatibility import is_py3
from jedi.common import unite
from jedi import debug
from jedi.evaluate import compiled
from jedi.evaluate import filters
from jedi.evaluate.context import Context, LazyKnownContext, LazyKnownContexts
from jedi.evaluate.cache import memoize_default
from jedi.cache import memoize_method
from jedi.evaluate import representation as er
from jedi.evaluate.dynamic import search_params
from jedi.evaluate import iterable


class AbstractInstanceContext(Context):
    """
    This class is used to evaluate instances.
    """
    api_type = 'instance'

    def __init__(self, evaluator, parent_context, class_context, var_args):
        super(AbstractInstanceContext, self).__init__(evaluator, parent_context)
        # Generated instances are classes that are just generated by self
        # (No var_args) used.
        self.class_context = class_context
        self.var_args = var_args

    def is_class(self):
        return False

    @property
    def py__call__(self):
        names = self.get_function_slot_names('__call__')
        if not names:
            # Means the Instance is not callable.
            raise AttributeError

        def execute(arguments):
            return unite(name.execute(arguments) for name in names)

        return execute

    def py__class__(self):
        return self.class_context

    def py__bool__(self):
        # Signalize that we don't know about the bool type.
        return None

    def get_function_slot_names(self, name):
        # Python classes don't look at the dictionary of the instance when
        # looking up `__call__`. This is something that has to do with Python's
        # internal slot system (note: not __slots__, but C slots).
        for filter in self.get_filters(include_self_names=False):
            names = filter.get(name)
            if names:
                return names
        return []

    def execute_function_slots(self, names, *evaluated_args):
        return unite(
            name.execute_evaluated(*evaluated_args)
            for name in names
        )

    def py__get__(self, obj):
        # Arguments in __get__ descriptors are obj, class.
        # `method` is the new parent of the array, don't know if that's good.
        names = self.get_function_slot_names('__get__')
        if names:
            if isinstance(obj, AbstractInstanceContext):
                return self.execute_function_slots(names, obj, obj.class_context)
            else:
                none_obj = compiled.create(self.evaluator, None)
                return self.execute_function_slots(names, none_obj, obj)
        else:
            return set([self])

    def get_filters(self, search_global=None, until_position=None,
                    origin_scope=None, include_self_names=True):
        if include_self_names:
            for cls in self.class_context.py__mro__():
                if isinstance(cls, compiled.CompiledObject):
                    if cls.tree_node is not None:
                        # In this case we're talking about a fake object, it
                        # doesn't make sense for normal compiled objects to
                        # search for self variables.
                        yield SelfNameFilter(self.evaluator, self, cls, origin_scope)
                else:
                    yield SelfNameFilter(self.evaluator, self, cls, origin_scope)

        for cls in self.class_context.py__mro__():
            if isinstance(cls, compiled.CompiledObject):
                yield CompiledInstanceClassFilter(self.evaluator, self, cls)
            else:
                yield InstanceClassFilter(self.evaluator, self, cls, origin_scope)

    def py__getitem__(self, index):
        try:
            names = self.get_function_slot_names('__getitem__')
        except KeyError:
            debug.warning('No __getitem__, cannot access the array.')
            return set()
        else:
            index_obj = compiled.create(self.evaluator, index)
            return self.execute_function_slots(names, index_obj)

    def py__iter__(self):
        iter_slot_names = self.get_function_slot_names('__iter__')
        if not iter_slot_names:
            debug.warning('No __iter__ on %s.' % self)
            return

        for generator in self.execute_function_slots(iter_slot_names):
            if isinstance(generator, AbstractInstanceContext):
                # `__next__` logic.
                name = '__next__' if is_py3 else 'next'
                iter_slot_names = generator.get_function_slot_names(name)
                if iter_slot_names:
                    yield LazyKnownContexts(
                        generator.execute_function_slots(iter_slot_names)
                    )
                else:
                    debug.warning('Instance has no __next__ function in %s.', generator)
            else:
                for lazy_context in generator.py__iter__():
                    yield lazy_context

    @abstractproperty
    def name(self):
        pass

    def _create_init_execution(self, class_context, func_node):
        bound_method = BoundMethod(
            self.evaluator, self, class_context, self.parent_context, func_node
        )
        return InstanceFunctionExecution(
            self,
            class_context.parent_context,
            bound_method,
            self.var_args
        )

    def create_init_executions(self):
        for name in self.get_function_slot_names('__init__'):
            if isinstance(name, LazyInstanceName):
                yield self._create_init_execution(name.class_context, name.tree_name.parent)

    @memoize_default()
    def create_instance_context(self, class_context, node):
        if node.parent.type in ('funcdef', 'classdef'):
            node = node.parent
        scope = node.get_parent_scope()
        if scope == class_context.tree_node:
            return class_context
        else:
            parent_context = self.create_instance_context(class_context, scope)
            if scope.type == 'funcdef':
                if scope.name.value == '__init__' and parent_context == class_context:
                    return self._create_init_execution(class_context, scope)
                else:
                    bound_method = BoundMethod(
                        self.evaluator, self, class_context,
                        self.parent_context, scope
                    )
                    return bound_method.get_function_execution()
            else:
                raise NotImplementedError
        return class_context

    def __repr__(self):
        return "<%s of %s(%s)>" % (self.__class__.__name__, self.class_context,
                                   self.var_args)


class CompiledInstance(AbstractInstanceContext):
    def __init__(self, *args, **kwargs):
        super(CompiledInstance, self).__init__(*args, **kwargs)
        # I don't think that dynamic append lookups should happen here. That
        # sounds more like something that should go to py__iter__.
        if self.class_context.name.string_name in ['list', 'set'] \
                and self.parent_context.get_root_context() == self.evaluator.BUILTINS:
            # compare the module path with the builtin name.
            self.var_args = iterable.get_dynamic_array_instance(self)

    @property
    def name(self):
        return compiled.CompiledContextName(self, self.class_context.name.string_name)

    def create_instance_context(self, class_context, node):
        if node.get_parent_scope().type == 'classdef':
            return class_context
        else:
            return super(CompiledInstance, self).create_instance_context(class_context, node)


class TreeInstance(AbstractInstanceContext):
    @property
    def name(self):
        return filters.ContextName(self, self.class_context.name.tree_name)


class AnonymousInstance(TreeInstance):
    def __init__(self, evaluator, parent_context, class_context):
        super(AnonymousInstance, self).__init__(
            evaluator,
            parent_context,
            class_context,
            var_args=None
        )


class CompiledInstanceName(compiled.CompiledName):
    def __init__(self, evaluator, instance, parent_context, name):
        super(CompiledInstanceName, self).__init__(evaluator, parent_context, name)
        self._instance = instance

    def infer(self):
        for result_context in super(CompiledInstanceName, self).infer():
            if isinstance(result_context, er.FunctionContext):
                parent_context = result_context.parent_context
                while parent_context.is_class():
                    parent_context = parent_context.parent_context

                yield BoundMethod(
                    result_context.evaluator, self._instance, self.parent_context,
                    parent_context, result_context.tree_node
                )
            else:
                if result_context.api_type == 'function':
                    yield CompiledBoundMethod(result_context)
                else:
                    yield result_context


class CompiledInstanceClassFilter(compiled.CompiledObjectFilter):
    name_class = CompiledInstanceName

    def __init__(self, evaluator, instance, compiled_object):
        super(CompiledInstanceClassFilter, self).__init__(
            evaluator,
            compiled_object,
            is_instance=True,
        )
        self._instance = instance

    def _create_name(self, name):
        return self.name_class(
            self._evaluator, self._instance, self._compiled_object, name)


class BoundMethod(er.FunctionContext):
    def __init__(self, evaluator, instance, class_context, *args, **kwargs):
        super(BoundMethod, self).__init__(evaluator, *args, **kwargs)
        self._instance = instance
        self._class_context = class_context

    def get_function_execution(self, arguments=None):
        if arguments is None:
            return AnonymousInstanceFunctionExecution(
                self._instance, self.parent_context, self)
        else:
            return InstanceFunctionExecution(
                self._instance, self.parent_context, self, arguments)


class CompiledBoundMethod(compiled.CompiledObject):
    def __init__(self, func):
        super(CompiledBoundMethod, self).__init__(
            func.evaluator, func.obj, func.parent_context, func.tree_node)

    def get_param_names(self):
        return list(super(CompiledBoundMethod, self).get_param_names())[1:]


class InstanceNameDefinition(filters.TreeNameDefinition):
    def infer(self):
        contexts = super(InstanceNameDefinition, self).infer()
        for context in contexts:
            yield context


class LazyInstanceName(filters.TreeNameDefinition):
    """
    This name calculates the parent_context lazily.
    """
    def __init__(self, instance, class_context, tree_name):
        self._instance = instance
        self.class_context = class_context
        self.tree_name = tree_name

    @property
    def parent_context(self):
        return self._instance.create_instance_context(self.class_context, self.tree_name)


class LazyInstanceClassName(LazyInstanceName):
    def infer(self):
        for result_context in super(LazyInstanceClassName, self).infer():
            if isinstance(result_context, er.FunctionContext):
                # Classes are never used to resolve anything within the
                # functions. Only other functions and modules will resolve
                # those things.
                parent_context = result_context.parent_context
                while parent_context.is_class():
                    parent_context = parent_context.parent_context

                yield BoundMethod(
                    result_context.evaluator, self._instance, self.class_context,
                    parent_context, result_context.tree_node
                )
            else:
                for c in er.apply_py__get__(result_context, self._instance):
                    yield c


class InstanceClassFilter(filters.ParserTreeFilter):
    name_class = LazyInstanceClassName

    def __init__(self, evaluator, context, class_context, origin_scope):
        super(InstanceClassFilter, self).__init__(
            evaluator=evaluator,
            context=context,
            node_context=class_context,
            origin_scope=origin_scope
        )
        self._class_context = class_context

    def _equals_origin_scope(self):
        node = self._origin_scope
        while node is not None:
            if node == self._parser_scope or node == self.context:
                return True
            node = node.get_parent_scope()
        return False

    def _access_possible(self, name):
        return not name.value.startswith('__') or name.value.endswith('__') \
            or self._equals_origin_scope()

    def _filter(self, names):
        names = super(InstanceClassFilter, self)._filter(names)
        return [name for name in names if self._access_possible(name)]

    def _convert_names(self, names):
        return [self.name_class(self.context, self._class_context, name) for name in names]


class SelfNameFilter(InstanceClassFilter):
    name_class = LazyInstanceName

    def _filter(self, names):
        names = self._filter_self_names(names)
        if isinstance(self._parser_scope, compiled.CompiledObject) and False:
            # This would be for builtin skeletons, which are not yet supported.
            return list(names)
        else:
            start, end = self._parser_scope.start_pos, self._parser_scope.end_pos
            return [n for n in names if start < n.start_pos < end]

    def _filter_self_names(self, names):
        for name in names:
            trailer = name.parent
            if trailer.type == 'trailer' \
                    and len(trailer.children) == 2 \
                    and trailer.children[0] == '.':
                if name.is_definition() and self._access_possible(name):
                    yield name

    def _check_flows(self, names):
        return names


class ParamArguments(object):
    """
    TODO This seems like a strange class, clean up?
    """
    class LazyParamContext(object):
        def __init__(self, fucking_param):
            self._param = fucking_param

        def infer(self):
            return self._param.infer()

    def __init__(self, class_context, funcdef):
        self._class_context = class_context
        self._funcdef = funcdef

    def unpack(self, func=None):
        params = search_params(
            self._class_context.evaluator,
            self._class_context,
            self._funcdef
        )
        is_first = True
        for p in params:
            # TODO Yeah, here at last, the class seems to be really wrong.
            if is_first:
                is_first = False
                continue
            yield None, self.LazyParamContext(p)


class InstanceVarArgs(object):
    def __init__(self, instance, funcdef, var_args):
        self._instance = instance
        self._funcdef = funcdef
        self._var_args = var_args

    @memoize_method
    def _get_var_args(self):
        if self._var_args is None:
            # TODO this parent_context might be wrong. test?!
            return ParamArguments(self._instance.class_context, self._funcdef)

        return self._var_args

    def unpack(self, func=None):
        yield None, LazyKnownContext(self._instance)
        for values in self._get_var_args().unpack(func):
            yield values

    def get_calling_nodes(self):
        return self._get_var_args().get_calling_nodes()

    def __getattr__(self, name):
        return getattr(self._var_args, name)


class InstanceFunctionExecution(er.FunctionExecutionContext):
    def __init__(self, instance, parent_context, function_context, var_args):
        self.instance = instance
        var_args = InstanceVarArgs(instance, function_context.tree_node, var_args)

        super(InstanceFunctionExecution, self).__init__(
            instance.evaluator, parent_context, function_context, var_args)


class AnonymousInstanceFunctionExecution(InstanceFunctionExecution):
    function_execution_filter = filters.AnonymousInstanceFunctionExecutionFilter

    def __init__(self, instance, parent_context, function_context):
        super(AnonymousInstanceFunctionExecution, self).__init__(
            instance, parent_context, function_context, None)
