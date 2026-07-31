"""
KeepNote
OrderDict module
"""

#
#  KeepNote
#  Copyright (c) 2008-2011 Matt Rasmussen
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


class OrderDict(dict):
    """
    An ordered dict
    """

    def __init__(self, *args, **kargs):
        dict.__init__(self)
        self._order = []
        if len(args) > 0:
            for k, v in args[0]:
                if k not in self:
                    self._order.append(k)
                dict.__setitem__(self, k, v)
        else:
            for k in kargs:
                self._order.append(k)
            dict.__init__(self, *args, **kargs)

    # The following methods keep names in sync with dictionary keys
    def __setitem__(self, key, value):
        if key not in self:
            self._order.append(key)
        dict.__setitem__(self, key, value)

    def __delitem__(self, key):
        self._order.remove(key)
        dict.__delitem__(self, key)

    def update(self, dct):
        for key in dct:
            if key not in self:
                self._order.append(key)
        dict.update(self, dct)

    def setdefault(self, key, value):
        if key not in self:
            self._order.append(key)
        return dict.setdefault(self, key, value)

    def clear(self):
        self._order = []
        dict.clear(self)

    # keys are always sorted in order added
    def keys(self):
        return list(self._order)

    def values(self):
        return [self[key] for key in self._order]

    def items(self):
        return [(key, self[key]) for key in self._order]

    def __iter__(self):
        return iter(self._order)
