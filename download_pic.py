#! /usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import with_statement
import os
import os.path
import sys
import redis
import simplejson as sj
import urllib2
import urlparse
import cookielib
from urllib2 import build_opener, HTTPCookieProcessor, HTTPError, URLError

def get(url, referer):
    try:
        cookie = cookielib.CookieJar()
        opener = build_opener(HTTPCookieProcessor(cookie))
        opener.addheaders = [
            ('Accept', 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'),
            ('Accept-Charset', 'GBK,utf-8;q=0.7,*;q=0.3'),
            ('Accept-Encoding', 'gzip,deflate,sdch'),
            ('Accept-Language', 'zh-CN,zh;q=0.8'),
            ('Connection', 'keep-alive'),
            ('User-Agent', 'Mozilla/5.0 (X11; Linux i686) AppleWebKit/535.19 (KHTML, like Gecko) Chrome/18.0.1025.162 Safari/535.19'),
            ('Referer', referer)
            ]
        response = opener.open(url, timeout = 10)
        info = response.info()
        data = response.read()
        return data
    except HTTPError, e:
        print e, url
    except URLError, e:
        print e, url
    return None

if __name__ == '__main__':
    if len(sys.argv) < 2:
        sys.exit()
    name = sys.argv[1]
    pool = redis.ConnectionPool(host='localhost', port=6379, db=1)
    r = redis.Redis(connection_pool=pool)
    keys = r.keys('*');
    for key in keys:
        print key
        if key[-3:] == 'pic':
            pics = r.lrange(key, 0, -1)
            dirname = '/disk2/%s/%s/pics' % (name, key.split('/')[-1][0:-9])
            if not os.path.exists(dirname):
                os.makedirs(dirname)
            for index, pic in enumerate(pics):
                filename = urlparse.urlparse(pic).path.split('/')[-1]
                if filename.find('.') == -1:
                    filename = '%s.%s' % (filename[:len(filename)-3], filename[len(filename) - 3:])
                if not os.path.exists('%s/%s' % (dirname, filename)):
                    data = get(pic, key.split('_')[0])
                    if data is not None and len(data) != 0:
                        open('%s/%s' % (dirname, filename), 'wb+').write(data)
        elif key[-6:] == 'avatar':
            avatar = r.get(key)
            dirname = '/disk2/%s/%s' % (name, key.split('/')[-1][0:-12])
            if not os.path.exists(dirname):
                os.makedirs(dirname)
            filename = urlparse.urlparse(avatar).path.split('/')[-1]
            if filename.find('.') == -1:
                filename = '%s.%s' % (filename[:len(filename)-3], filename[len(filename) - 3:])
            if not os.path.exists('%s/avatar_%s' % (dirname, filename)):
                data = get(avatar, key.split('_')[0])
                if data is not None and len(data) != 0:
                    open('%s/avatar_%s' % (dirname, filename), 'wb+').write(data)
