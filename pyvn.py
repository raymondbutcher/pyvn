import re

_pyvn_method_name_re = re.compile('^(.+)_v(\d+)$')


def pyvn(*args):
    """
    A decorator for adding pyvn support to classes and their methods.

    Setting up a class:

        @pyvn
        class SomeClass(object):

            @pyvn('get_data', 1):
            def some_method(self):
                return 'old data'

            @pyvn('get_data', 2):
            def another_method(self):
                return 'current/new data'

    Using the methods:

        >>> some_object = SomeClass()
        >>> print some_object.get_data_v1()
        'old data'
        >>> print some_object.get_data_v2()
        'current/new data'

    """

    if len(args) == 1:
        return _pyvn_class(args[0])
    elif len(args) == 2:
        return _pyvn_method(*args)
    else:
        raise Exception('Incorrect usage of pyvn decorator.')


def _update_getattr(cls):
    """Wrap the __getattr__ method of a class to check the resolver."""

    if hasattr(cls, '__getattr__'):
        original_getattr = cls.__getattr__
    else:
        original_getattr = None

    def pyvn_getattr(self, name):
        try:
            return self._pyvn_resolver.resolve(name, self)
        except AttributeError:
            if original_getattr:
                return original_getattr(self, name)
            else:
                raise

    cls.__getattr__ = pyvn_getattr


def _pyvn_class(cls):
    """Enables a class to use pyvn methods."""

    # Create a resolver for this class once.
    if not hasattr(cls, '_pyvn_resolver'):
        cls._pyvn_resolver = PyvnResolver(cls)
        _update_getattr(cls)

    # Register all @pyvn decorated methods with the resolver.
    for method_name, method in cls.__dict__.iteritems():

        #if method_name.startswith('_pyvn'):
        #    continue
        #
        #if isinstance(method, (staticmethod, classmethod)):
        #    if hasattr(method, '__func__'):
        #        method = method.__func__
        #    else:
        #        try:
        #            method = method.__get__(1).__func__
        #        except Exception:
        #            try:
        #                method = method.__get__(1).im_func
        #            except Exception:
        #                continue

        if hasattr(method, '_pyvn_name'):
            cls._pyvn_resolver.register(method, method_name)

    # Sort the resolver methods here rather than when resolving each name.
    cls._pyvn_resolver.sort()

    return cls


def _pyvn_method(name, version):
    """Registers a method with pyvn using a name and version."""
    def decorator(method):
        method._pyvn_name = name
        method._pyvn_version = int(version)
        return method
    return decorator


class PyvnResolver(object):

    def __init__(self, parent):
        self.parent = parent
        self.methods = {}

    def __repr__(self):
        return 'pyvn: %s' % ', '.join(sorted(self.get_names()))

    def __getattr__(self, name):
        return self.resolve(name)

    def get_best_version(self, name, max_version):
        """Find the highest useable version for the requested method name."""
        available_methods = self.methods[name]
        for method_version, real_method_name in available_methods:
            if method_version <= max_version:
                return real_method_name
        else:
            min_version = min(available_methods)[0]
            raise NotImplementedError("Method '%s_v%d' not implemented. Try '%s_v%d' or above." % (name, max_version, name, min_version))

    def get_names(self):
        """Get the valid names that can be accessed."""
        for name, methods in self.methods.iteritems():
            if name.startswith(':'):
                yield name
            else:
                for version, method_name in methods:
                    yield '%s_v%d' % (name, version)

    def register(self, method, real_method_name):
        """Registers a method with this resolver."""
        name = method._pyvn_name
        version = method._pyvn_version
        target = self.methods
        while '.' in name:
            namespace, name = name.split('.', 1)
            namespace = ':%s' % namespace
            target.setdefault(namespace, {})
            target = target[namespace]
        target.setdefault(name, [])
        target[name].append((version, real_method_name))

    def resolve(self, name, obj=None):
        """
        Tries to return the best method version, or a new resolver if there
        is a namespace for it.

        """
        if obj is None:
            obj = self.parent
        match = _pyvn_method_name_re.match(name)
        if match:
            pyvn_name, pyvn_version = match.groups()
            if pyvn_name in self.methods:
                best_method = self.get_best_version(pyvn_name, int(pyvn_version))
                return getattr(obj, best_method)
        else:
            namespace = ':%s' % name
            if namespace in self.methods:
                if not isinstance(self.methods[namespace], self.__class__):
                    # Build a new resolver for this namespace.
                    resolver = self.__class__(obj)
                    resolver.methods = self.methods[namespace]
                    resolver.sort()
                    self.methods[namespace] = resolver
                return self.methods[namespace]
        raise AttributeError('%r not found. Available: %s' % (name, ', '.join(self.names)))

    def sort(self):
        """Sort the methods so that the newest versions come first."""
        for methods in self.methods.values():
            if hasattr(methods, 'sort'):
                methods.sort(reverse=True)
