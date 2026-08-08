"""

KeepNote
utilities

"""

#
#  KeepNote
#  Copyright (c) 2008-2009 Matt Rasmussen
#  Author: Matt Rasmussen <rasmus@alum.mit.edu>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; version 2 of the License.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA 02110-1301, USA.
#


class PushIter(object):
    """
    Wrap an iterator in another iterator that allows one to push new
    items onto the front of the iteration stream
    """

    def __init__(self, it):
        self._it = iter(it)
        self._queue = []

    def __iter__(self):
        return self

    def __next__(self):
        if len(self._queue) > 0:
            return self._queue.pop()
        else:
            return next(self._it)

    def push(self, item):
        """Push a new item onto the front of the iteration stream"""
        self._queue.append(item)


# FIX: Thread-safe UI helper for GTK background thread updates (KEEP-PLAN-4.1)


def gtk_safe_call(func, *args, **kwargs):
    """
    Safely call a GTK function from a background thread.
    Uses GLib.idle_add to schedule the call on the main thread.

    Usage:
        # In worker thread:
        gtk_safe_call(widget.set_text, "Updated text")

    Parameters:
        func: GTK function to call
        *args: Arguments to pass to func
        **kwargs: Keyword arguments to pass to func

    Returns:
        None (call is queued, not executed immediately)
    """
    try:
        from gi.repository import GLib
    except ImportError:
        # Fallback: if GLib is not available, call directly (not thread-safe)
        func(*args, **kwargs)
        return

    def wrapper():
        func(*args, **kwargs)
        return False  # Stop after one execution
    GLib.idle_add(wrapper)


class ThreadSafeUIUpdater(object):
    """Helper class for batching UI updates from worker threads."""

    def __init__(self):
        self._pending_updates = []
        self._scheduled = False

    def queue_update(self, func, *args):
        """Queue a UI update to be executed on the main thread."""
        self._pending_updates.append((func, args))
        if not self._scheduled:
            self._scheduled = True
            try:
                from gi.repository import GLib
                GLib.idle_add(self._flush_updates)
            except ImportError:
                self._flush_updates()

    def _flush_updates(self):
        """Execute all pending updates."""
        for func, args in self._pending_updates:
            try:
                func(*args)
            except Exception as e:
                import logging
                logging.error(f"UI update failed: {e}")
        self._pending_updates = []
        self._scheduled = False
        return False


def compose2(f, g):
    """
    Compose two functions into one

    compose2(f, g)(x) <==> f(g(x))
    """
    return lambda *args, **kargs: f(g(*args, **kargs))


def compose(*funcs):
    """Composes two or more functions into one function

    example:
    compose(f,g)(x) <==> f(g(x))
    """
    funcs = reversed(funcs)
    f = next(funcs)
    for g in funcs:
        f = compose2(g, f)
    return f
