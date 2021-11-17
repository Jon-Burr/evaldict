import six

if six.PY3:
  from collections.abc import MutableMapping
else:
  from collections import MutableMapping
from memoclass.memoclass import MemoClass, mutates
from memoclass.memoize import memomethod
import string

class EvalDict(MemoClass, MutableMapping):
    """ Dictionary that supports evaluating variables

        This supports key, value pairs where the values can depend on what is
        stored under *other* keys.

        Interpreting these relationships is done using a formatter class. The
        formatter used works as follows

        - If the value has a '_formatter' member variable, that will be used
        - If the EvalDict object has a '_formatter' member variable, that will
          be used
        - Otherwise, string.Formatter will be used
    """

    # TODO - I need to do some fixes to memoclass - for some reason it's making
    # these hacks necessary :(
    def __hash__(self):
        return id(self)

    def __eq__(self, other):
        return id(self) == id(other)

    def __init__(self):
        self._values = {}
        super(EvalDict, self).__init__()

    def __iter__(self):
        return iter(self._values)

    def __contains__(self, key):
        return key in self._values

    def __len__(self):
        return len(self._values)

    @mutates
    def __setitem__(self, key, value):
        self._values[key] = value

    def __getitem__(self, key):
        """ When getting an item, it is automatically formatted using eval
        
            To retrieve the unformatted expression instead, use get_uneval
        """
        return self.eval(key)

    def get_uneval(self, key):
        return self._values[key]

    @mutates
    def __delitem__(self, key):
        del self._values[key]

    def eval(self, key):
        return self.eval_expr(self.get_uneval(key) )

    def get_formatter(self, value):
        """ Get the formatter associated to a value """
        try:
            return value._formatter
        except AttributeError:
            pass
        try:
            return self._formatter
        except AttributeError:
            pass
        return string.Formatter()

    @memomethod
    def eval_expr(self, expression):
        """ Evaluate an expression """
        f = self.get_formatter(expression)
        used_vars = self.get_used_variables(expression, f)
        return f.format(expression, **{k : self[k] for k in used_vars})

    def get_used_variables(self, expression, formatter=None, seen=None):
        """ Get a set of variables used by an expression

            Will throw a value error

            :param expression: the expression to use
            :param formatter:
                the formatter to use, if not provided, get_formatter will be
                used.
            :param seen:
                Any variables used so far, used to detect cyclic dependencies.
                Any cyclic dependencies result in a ValueError

            Internally, this uses the string.Formatter.parse method which
            returns an iterable of tuples (literal_text, field_name,
            format_spec, conversion), with an entry for each replacement field.
            The format_spec is allowed to contain variables as well, so if that
            is not None, it will also be parsed (recursively) using the same
            formatter as the original expression.
        """
        if seen is None:
            seen = set()
        if formatter is None:
            formatter = self.get_formatter(expression)
        def get_vars(field_name, format_spec):
            if field_name is None:
                return set()
            if format_spec is None:
                ret = set([field_name])
            else:
                ret = set([field_name]) | self.get_used_variables(
                        format_spec, formatter, seen | set([field_name]) )
            if ret & seen:
                raise ValueError(
                    "Cyclic dependency detected on variables: '{0}'!".format(
                        ", ".join(ret & seen) ) )
            return ret

        return set(f for _, field, spec, _ in formatter.parse(expression)
                     for f in get_vars(field, spec) )

if __name__ == "__main__":
    d = EvalDict()
    d["fill"] = " "
    d["align"] = ">"
    d["pad"] = "20"
    d["message"] = "Hello World!"
    d["val"] = "{message:{fill}{align}{pad}}"
    print(d["val"])
