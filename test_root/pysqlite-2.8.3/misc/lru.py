#-*- coding: ISO-8859-1 -*-
# lru.py - a simple LRU cache, which will be rewritten in C later
#
# Copyright (C) 2004-2015 Gerhard Häring <gh@ghaering.de>
#
# This file is part of pysqlite.
#
# This software is provided 'as-is', without any express or implied
# warranty.  In no event will the authors be held liable for any damages
# arising from the use of this software.
#
# Permission is granted to anyone to use this software for any purpose,
# including commercial applications, and to alter it and redistribute it
# freely, subject to the following restrictions:
#
# 1. The origin of this software must not be misrepresented; you must not
#    claim that you wrote the original software. If you use this software
#    in a product, an acknowledgment in the product documentation would be
#    appreciated but is not required.
# 2. Altered source versions must be plainly marked as such, and must not be
#    misrepresented as being the original software.
# 3. This notice may not be removed or altered from any source distribution.

class Node:
    def __init__(self, key, data):
        self.key = key
        self.data = data
        self.count = 1
        self.prev, self.next = None, None

class Cache:
    def __init__(self, factory, maxlen):
        self.first, self.last = None, None
        self.maxlen = maxlen
        self.mapping = {}
        self.factory = factory

    def get(self, key):
        if key in self.mapping:
            nd = self.mapping[key]
            nd.count += 1

            if nd.prev and nd.count > nd.prev.count:
                ptr = nd.prev
                while ptr.prev is not None and nd.count > ptr.prev.count:
                    ptr = ptr.prev

                # Move nd before ptr
                if nd.next:
                    nd.next.prev = nd.prev
                else:
                    self.last = nd.prev
                if nd.prev:
                    nd.prev.next = nd.next
                if ptr.prev:
                    ptr.prev.next = nd
                else:
                    self.first = nd

                save = nd.next
                nd.next = ptr
                nd.prev = ptr.prev
                if nd.prev is None:
                    self.first = nd
                ptr.prev = nd
                #ptr.next = save
        else:
            if len(self.mapping) == self.maxlen:
                if self.last:
                    nd = self.last
                    self.mapping[self.last.key] = None
                    del self.mapping[self.last.key]
                    if nd.prev:
                        nd.prev.next = None
                    self.last = nd.prev
                    nd.prev = None

            obj = self.factory(key)
            nd = Node(key, obj)
            nd.prev = self.last
            nd.next = None
            if self.last:
                self.last.next = nd
            else:
                self.first = nd
            self.last = nd
            self.mapping[key] = nd
        return nd.data

    def display(self):
        nd = self.first
        while nd:
            prevkey, nextkey = None, None
            if nd.prev: prevkey = nd.prev.key
            if nd.next: nextkey = nd.next.key
            print "%4s <- %4s -> %s\t(%i)" % (prevkey, nd.key, nextkey, nd.count)
            nd = nd.next

if __name__ == "__main__":
    def create(s):
        return s

    import random
    cache = Cache(create, 5)
    if 1:
        chars = list("abcdefghijklmnopqrstuvwxyz")
        lst = []
        for i in range(100):
            idx = random.randint(0, len(chars) - 1)
            what = chars[idx]
            lst.append(what)
            cache.get(chars[idx])
        cache.display()
        #print "-" * 50
        #print lst
        #print "-" * 50
    else:
        lst = \
            ['y', 'y', 'b', 'v', 'x', 'f', 'h', 'n', 'g', 'k', 'o', 'q', 'p', 'e', 'm', 'c', 't', 'y', 'c', 's', 'p', 's', 'j', 'm', \
             'u', 'f', 'z', 'x', 'v', 'r', 'w', 'e', 'm', 'd', 'w', 's', 'b', 'r', 'd', 'e', 'h', 'g', 'e', 't', 'p', 'b', 'e', 'i', \
             'g', 'n']
        #lst = ['c', 'c', 'b', 'b', 'd', 'd', 'g', 'c', 'c', 'd'] 
        for item in lst:
            cache.get(item)
        cache.display()


