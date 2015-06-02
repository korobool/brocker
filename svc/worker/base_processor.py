class BaseProcessor:

    EXEC_TIMEOUT = 5

    def __init__(self, loop=None):
        self.loop = loop
        self.exposed_methods = []
        for method in dir(self):
            # TODO: Should use smarter approach for method list collecting.
            #       Decorators?
            attribute = getattr(self, method)
            if hasattr(attribute, '__call__') and not method.startswith('_'):
                self.exposed_methods.append(method)

