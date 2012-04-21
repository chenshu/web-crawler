#! /usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import with_statement
import re
import os
import sys
import os.path
from HTMLParser import HTMLParser
import redis
import codecs

class HiApkPageParser(HTMLParser):

    def __init__(self):
        HTMLParser.__init__(self)
        self.img = 0
        self.url = ''
        self.recoding = 0
        self.pic = 0
        self.urls = []

    def handle_starttag(self, tag, attrs):
        if tag == 'div':
            for k, v in attrs:
                if k == 'class' and v == 's_name':
                    self.img = 1
                    break
        elif tag == 'img' and self.img == 1:
            for k, v in attrs:
                if k == 'src':
                    self.url = v
                    break
        elif tag == 'label' and len(attrs) == 1:
            for k, v in attrs:
                if k == 'id' and v != 'Apk_Download' and v != 'Apk_ObserverNums':
                    self.recoding = 1
                    break
        elif tag == 'a':
            for k, v in attrs:
                if k == 'rel' and v == 'prettyPhoto[gallery]':
                    self.pic = 1
                    break
        elif tag == 'img' and self.pic == 1:
            for k, v in attrs:
                if k == 'src':
                    self.urls.append(v)
                    break

    def handle_endtag(self, tag):
        if tag == 'div' and self.img == 1:
            self.img = 0
        elif tag == 'label' and self.recoding == 1:
            self.recoding = 0
        elif tag == 'a' and self.pic == 1:
            self.pic = 0

    def handle_data(self, data):
        if self.recoding == 1:
            data = data.strip().replace('\n', '\t')
            data = data.strip().replace('\r', '\t')
            if data != '':
                sys.stdout.write('\t%s' % (data.encode('utf-8')))

if __name__ == '__main__':
    pool = redis.ConnectionPool(host='localhost', port=6379, db=1)
    r = redis.Redis(connection_pool=pool)
    parser = HiApkPageParser()
    '''
    with codecs.open('static.apk.hiapk.com/html/2009/09/21.html', 'r', 'utf-8') as fp:
        data = fp.read()
        parser.feed(data)
        sys.stdout.write('\n')
        referer = 'http://static.apk.hiapk.com/html/2009/09/21.html'
        if parser.url is not None and parser.url != '':
            pass
            #r.set('%s_avatar' % (referer), parser.url)
        if len(parser.urls) != 0:
            pass
            #r.rpush('%s_pic' % (referer), *parser.urls)
        del parser.urls[:]
    parser.close()
    sys.exit()
    '''
    host = 'static.apk.hiapk.com'
    path = 'html'
    dirname = '%s/%s/%s' % (os.path.dirname(os.path.realpath(__file__)), host, path)
    years = os.listdir(dirname)
    for year in years:
        months = os.listdir('%s/%s' % (dirname, year))
        for month in months:
            files = os.listdir('%s/%s/%s' % (dirname, year, month))
            for filename in files:
                apk_id = filename.split('.')[0]
                referer = 'http://%s/%s/%s/%s/%s' % (host, path, year, month, filename)
                sys.stdout.write('%s\t%s' % (apk_id, referer))
                with codecs.open('%s/%s/%s/%s' % (dirname, year, month, filename), 'r', 'utf-8') as fp:
                    data = fp.read()
                    parser.feed(data)
                    sys.stdout.write('\n')
                    if parser.url is not None and parser.url != '':
                        r.set('%s_avatar' % (referer), parser.url)
                    if len(parser.urls) != 0:
                        r.rpush('%s_pic' % (referer), *parser.urls)
                    del parser.urls[:]
    parser.close()
