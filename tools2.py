#! /usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import with_statement
import os
import sys
import redis
import simplejson as sj

if __name__ == '__main__':
    if len(sys.argv) < 2:
        sys.exit()
    pool = redis.ConnectionPool(host='localhost', port=6379, db=3)
    r = redis.Redis(connection_pool=pool)
    name = sys.argv[1]
    f = "%s_pic_upload" % (name)
    lastid = None
    lastattr = dict()
    nowid = None
    nowattr = dict()
    with open(f, 'r') as fp:
        for line in fp:
            arr = line.strip().split('\t')
            if len(arr) != 2:
                continue
            path, json = arr
            paths = path.split('/')
            if len(paths) == 5:
                nowid = paths[3]
                if lastid != nowid:
                    nowattr.clear()
                nowattr['avatar'] = sj.loads(json)
            elif len(paths) == 6:
                nowid = paths[3]
                if lastid != nowid:
                    nowattr.clear()
                nowattr.setdefault('pics', []).append(sj.loads(json))
            else:
                print 'error'
                sys.exit()
            if lastid != None:
                if lastid != nowid:
                    key = '%s:%s' % (name, lastid)
                    value = dict()
                    if 'avatar' in lastattr:
                        value['avatar'] = sj.dumps(lastattr['avatar'])
                    if 'pics' in lastattr:
                        value['pics'] = sj.dumps(lastattr['pics'])
                    r.hmset(key, value)
                    print "%s\t%s" % (key, value)
                    lastattr.clear()
            lastid = nowid
            lastattr.update(nowattr)
        key = '%s:%s' % (name, lastid)
        value = dict()
        if 'avatar' in lastattr:
            value['avatar'] = sj.dumps(lastattr['avatar'])
        if 'pics' in lastattr:
            value['pics'] = sj.dumps(lastattr['pics'])
        r.hmset(key, value)
        print "%s\t%s" % (key, value)
