import re


class PyvnResolver(object):

    _method_name_re = re.compile('^(.+)_v(\d+)$')

    def __init__(self, parent):
        self.parent = parent
        self.methods = {}

    def __repr__(self):
        available = ', '.join(self.get_names()) or 'None'
        return 'pyvn resolver: %s' % available

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
        for (name, version) in method._pyvn_data:
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
        match = self._method_name_re.match(name)
        if match:
            pyvn_name, pyvn_version = match.groups()
            if pyvn_name in self.methods:
                best_method = self.get_best_version(pyvn_name, int(pyvn_version))
                real_method = getattr(obj, best_method)
                return real_method
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
        raise AttributeError('%r object has no attribute %r' % (obj.__class__.__name__, name))

    def sort(self):
        """Sort the methods so that the newest versions come first."""
        for methods in self.methods.values():
            if hasattr(methods, 'sort'):
                methods.sort(reverse=True)


class PyvnType(type):

    def __new__(cls, name, bases, dct):

        # Create the new class as normal.
        new_cls = super(PyvnType, cls).__new__(cls, name, bases, dct)

        # Create a resolver and register all @pyvn decorated methods.
        resolver = PyvnResolver(new_cls)
        for method_name, method in new_cls.__dict__.iteritems():

            if isinstance(method, property):
                method = method.fget
            elif isinstance(method, (staticmethod, classmethod)):
                if hasattr(method, '__func__'):
                    method = method.__func__
                else:
                    # Try to work with older versions of python.
                    # Who knows if this will work!
                    try:
                        method = method.__get__(1).__func__
                    except Exception:
                        try:
                            method = method.__get__(1).im_func
                        except Exception:
                            continue

            if hasattr(method, '_pyvn_data'):
                resolver.register(method, method_name)

        # Sort the resolver here, rather than each time it resolves a name.
        resolver.sort()

        # Return the new class with the resolver attached.
        new_cls._pyvn_resolver = resolver
        return new_cls

    def __getattr__(cls, name):
        return cls._pyvn_resolver.resolve(name)


class PyvnClass(object):

    __metaclass__ = PyvnType

    def __getattr__(self, name):
        if name == '_pyvn_resolver':
            raise AttributeError('%r not found' % name)
        try:
            return self._pyvn_resolver.resolve(name, self)
        except AttributeError:
            other = super(PyvnClass, self)
            if hasattr(other, '__getattr__'):
                return other.__getattr__(name)
            else:
                raise


def pyvn(name, version):
    """Registers a method with pyvn."""
    def decorator(method):
        if not hasattr(method, '_pyvn_data'):
            method._pyvn_data = set()
        method._pyvn_data.add((name, int(version)))
        return method
    return decorator


# Make the PyvnClass easy to acess via the decorator,
# making pyvn only require a single import.
pyvn.Class = PyvnClass
