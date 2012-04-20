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
    f = "%s_upload" % (name)
    with open(f, 'r') as fp:
        for line in fp:
            arr = line.strip().split('\t')
            if len(arr) != 2:
                continue
            path, json = arr
            key = '%s:%s' % (name, path.split('/')[-1])
            data = sj.loads(json)
            doc = data['File']
            fid = doc['path'].split('/')[5]
            size = doc['size']
            md5 = doc['nsp_fid']
            value = {'fid' : fid, 'size' : size, 'md5' : md5}
            r.hmset(key, value)
            print key, fid, size, md5
