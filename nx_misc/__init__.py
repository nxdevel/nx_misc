"Miscellaneous utilities."
import sys
import functools
from datetime import datetime


try:
    from tzlocal import get_localzone
    TZ = get_localzone()
    del get_localzone
except ImportError:
    import pytz
    TZ = pytz.timezone('America/Detroit')
    del pytz


TZ_NORMALIZE = TZ.normalize


TZ_LOCALIZE = TZ.localize


NOW = datetime.now


def localize(dtm):
    "Localize the provided date/time."
    return TZ_NORMALIZE(TZ_LOCALIZE(dtm))


def fetch_now():
    "Retrieve the current time in localized form."
    return TZ_NORMALIZE(TZ_LOCALIZE(NOW()))


def dispatch_when(arg):
    """
    Parse a string incorporating missing information.

    Useful for monotonically increasing stamps.
    """
    when = fetch_now()
    if not arg:
        return when
    if len(arg) == 10:
        template = '%Y-%m-%d'
        args = dict(hour=when.hour, minute=when.minute, second=when.second,
                    microsecond=when.microsecond)
    elif len(arg) == 16:
        template = '%Y-%m-%dT%H:%M'
        args = dict(second=when.second, microsecond=when.microsecond)
    else:
        template = '%Y-%m-%dT%H:%M:%S'
        args = dict(microsecond=when.microsecond)
    return TZ_NORMALIZE(TZ_LOCALIZE(
        datetime.strptime(arg, template).replace(**args)))


def any_duplicates(clct):
    """
    >>> any_duplicates([1, 2, 3])
    False

    >>> any_duplicates([1, 2, 3, 2])
    True

    >>> any_duplicates([])
    False
    """
    return len(clct) != len(set(clct))


def force_run(iterable):
    """
    Run every function in the provided list - left to right - regardless of
    whether any exceptions are thrown. Useful for unwinding.

    >>> a, b = 0, 0
    >>> a == 0 and b == 0
    True
    >>> def x():
    ...     global a
    ...     a = 1
    >>> def y():
    ...     global b
    ...     b = 2
    >>> force_run([x, y])
    >>> a == 1 and b == 2
    True

    >>> a, b = 0, 0
    >>> a == 0 and b == 0
    True
    >>> def x():
    ...     global a
    ...     a = 1
    >>> def y():
    ...     global b
    ...     b = 2
    >>> def z(): raise ValueError
    >>> force_run([x, z, y])
    Traceback (most recent call last):
        ...
    ValueError
    >>> a == 1 and b == 2
    True
    """
    def gen(func1, func2):
        "Generator to run both functions, regardless of exceptions."
        def _():
            try:
                func1()
            finally:
                func2()
        return _
    functools.reduce(gen, iterable)()


def flatten_dict(dct, fields, *, rest_val=None, extras_action='raise',
                 field_set=None):
    """
    >>> flatten_dict({'a': 1, 'b': 2}, ('a', 'b'))
    [1, 2]

    >>> flatten_dict({'a': 1, 'b': 2}, ('a', 'b', 'c'))
    Traceback (most recent call last):
        ...
    KeyError: 'c'

    >>> flatten_dict({'a': 1, 'b': 2}, ('a', 'b', 'c'), rest_val=5)
    [1, 2, 5]

    >>> flatten_dict({'a': 1, 'b': 2, 'c': 5}, ('a', 'b'))
    Traceback (most recent call last):
        ...
    ValueError: ('invalid extra keys', {'c'})

    >>> flatten_dict({'a': 1, 'b': 2, 'c': 5}, ('a', 'b'),
    ...              extras_action='ignore')
    [1, 2]
    """
    if extras_action == 'raise':
        extras = dct.keys() - (field_set or set(fields))
        if extras:
            raise ValueError('invalid extra keys', extras)
    if rest_val is not None:
        return [dct.get(f, rest_val) for f in fields]
    return [dct[f] for f in fields]


def flatten_obj(obj, fields, *, rest_val=None):
    """
    >>> class A: pass
    >>> a = A(); a.a = 1; a.b=2
    >>> flatten_obj(a, ('a', 'b'))
    [1, 2]

    >>> flatten_obj(a, ('a', 'b', 'c'))
    Traceback (most recent call last):
        ...
    AttributeError: 'A' object has no attribute 'c'

    >>> flatten_obj(a, ('a', 'b', 'c'), rest_val=5)
    [1, 2, 5]
    """
    if rest_val is not None:
        return [getattr(obj, f, rest_val) for f in fields]
    return [getattr(obj, f) for f in fields]


class StatusDisplay:
    "Create a status update display."
    _closed = True
    _phases = (' ', '\u258f', '\u258e', '\u258d', '\u258c', '\u258b', '\u258a',
               '\u2589', '\u2588')

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()

    def __del__(self):
        if not self._closed:
            fobj = sys.stderr
            if fobj.isatty():
                print('\x1b[?25h', file=fobj, flush=True)

    def done(self):
        "Call when finished using the display to update the status."
        self.close()

    def close(self):
        "Close the display."
        if not self._closed:
            self._closed = True
            elapsed = NOW() - self._start
            fobj = sys.stderr
            if fobj.isatty():
                line = '\r' + '\x1b[K' + '[' + str(elapsed)[:-4] + '] ' + \
                       self.orig_msg
                count = self.count
                if count:
                    tick = self._tick
                    line += ' [' + str(tick)
                    if tick != count:
                        line += '/' + str(count)
                    line += ']'
                print(line + '\x1b[?25h', file=fobj, flush=True)

    def tick(self):
        "Call when incremental progress has been completed."
        elapsed = NOW() - self._start
        fobj = sys.stderr
        if fobj.isatty():
            line = '\x1b[?25l' + '\r' + '\x1b[K' + '[' + str(elapsed)[:-4] + \
                   '] '
            count = self.count
            if count:
                tick = self._tick + 1
                if tick > count:
                    tick = count
                width = self._width
                phases = self._phases
                phases_length = len(phases)
                wpt = width * tick
                filled_length = int(wpt / count)
                phase = int(phases_length * wpt / count) - \
                        phases_length * filled_length
                current = phases[phase] if phase > 0 else ''
                empty = ' ' * max(0, width - filled_length - len(current))
                line += self.msg + ' |' + phases[-1] * filled_length + \
                        current + empty + '| [' + str(tick) + '/' + \
                        str(count) + ']'
                self._tick = tick

            else:
                line += self.orig_msg
            print(line, end='', file=fobj, flush=True)

    # status is a left-over
    def __init__(self, msg, count=None, status=True): # pylint: disable=unused-argument
        fobj = sys.stderr
        if fobj.isatty():
            self.orig_msg, self.count = msg.strip(), count
            line = '\x1b[?25l' + '[-:--:--.--] ' + self.orig_msg
            print(line, end='', file=fobj, flush=True)
            if len(self.orig_msg) > 39:
                self.msg = self.orig_msg[0:36] + '...'
            else:
                self.msg = self.orig_msg
            self._width = 79 - (len(self.msg) + 38)
            self._tick = 0
            self._start = NOW()
        self._closed = False
