#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import os.path
from urllib import urlencode
from urllib2 import urlopen, Request, build_opener, HTTPCookieProcessor, HTTPError
import cookielib
import StringIO
import gzip
from collections import defaultdict
from datetime import datetime
import time

class Spider(object):

    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)
        # 设置名称
        if not getattr(self, 'name', None):
            raise ValueError("%s must have a name" % type(self).__name__)
        # 设置host
        if not getattr(self, 'host', None):
            raise ValueError("%s must have a host" % type(self).__name__)
        # 设置入口url
        if not getattr(self, 'start_url', None):
            raise ValueError("%s must have a start_url" % type(self).__name__)
        # 设置链接超时时间
        if not getattr(self, 'timeout', None):
            self.timeout = 10
        self.GMT_FORMAT = '%a, %d %b %Y %H:%M:%S GMT'
        self.cookie = cookielib.CookieJar()
        # 已经抓取的页面保存到文件中
        self.filename = '%s/%s_urls' % (os.path.dirname(os.path.realpath(__file__)), self.name)
        if not os.path.exists(self.filename):
            self.fp = open(self.filename, 'a+')
        else:
            self.fp = open(self.filename, 'r')
        # 已经抓取了多少页面
        self.finished = defaultdict(dict)
        for line in self.fp:
            data = line.strip().split('\t')
            url = data[0]
            last_modified = data[1]
            expires = data[2]
            etag = ''
            if len(data) > 3:
                etag = data[3]
            self.finished[url]['last_modified'] = datetime.strptime(last_modified, self.GMT_FORMAT)
            self.finished[url]['expires'] = datetime.strptime(expires, self.GMT_FORMAT)
            self.finished[url]['etag'] = etag
        self.fp.close()
        self.newed = set()

    def get(self, url, callback = None):
        if len(self.newed) % 10 == 0:
            time.sleep(1)
        try:
            if url in self.newed:
                return None
            if url in self.finished and datetime.now() < self.finished[url]['expires']:
                return None
            print url
            # 绑定cookie
            self.opener = build_opener(HTTPCookieProcessor(self.cookie))
            # 设置http header
            self.opener.addheaders = [
                ('Accept', 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'),
                ('Accept-Charset', 'GBK,utf-8;q=0.7,*;q=0.3'),
                ('Accept-Encoding', 'gzip,deflate,sdch'),
                ('Accept-Language', 'zh-CN,zh;q=0.8'),
                ('Connection', 'keep-alive'),
                ('Host', self.host),
                ('User-Agent', 'Mozilla/5.0 (Windows NT 5.1) AppleWebKit/535.7 (KHTML, like Gecko) Chrome/16.0.912.63 Safari/535.7')
            ]
            # 获取当前页面的上次修改时间
            last_modified = self.finished[url]['last_modified'] if url in self.finished else None
            # 获取当前页面的内容hash
            etag = self.finished[url]['etag'] if url in self.finished else None
            # 设置If-Modified-Since
            if last_modified is not None:
                self.opener.addheaders.append(('If-Modified-Since', last_modified.strftime(self.GMT_FORMAT)))
            # 设置If-None-Match
            if etag is not None:
                self.opener.addheaders.append(('If-None-Match', etag))
            # 抓取页面
            response = self.opener.open(url, timeout = self.timeout)
            info = response.info()
            # 获取页面的上次修改时间
            self.finished[url]['last_modified'] = datetime.strptime(info['Last-Modified'], self.GMT_FORMAT) if 'Last-Modified' in info else datetime.now()
            # 获取页面的过期时间
            self.finished[url]['expires'] = datetime.strptime(info['Expires'], self.GMT_FORMAT) if 'Expires' in info else datetime.now()
            # 获取页面的内容hash
            self.finished[url]['etag'] = info['ETag'] if 'ETag' in info else ''
            self.newed.add(url)
            # gzip解压缩
            data = StringIO.StringIO(response.read())
            gzipper = gzip.GzipFile(fileobj = data)
            if callback is not None:
                callback(gzipper.read())
        except HTTPError, e:
            # 如果返回304
            if e.code != 304:
                print e
        return None

    def start(self):
        # 抓取页面
        url = 'http://%s%s' % (self.host, self.start_url)
        self.get(url, self.parse)
        # 更新抓取列表
        self.f = open('%s_new' % (self.filename), 'w+')
        self.f.writelines(['%s\t%s\t%s\t%s%s' % (url, self.finished[url]['last_modified'].strftime(self.GMT_FORMAT), self.finished[url]['expires'].strftime(self.GMT_FORMAT), self.finished[url]['etag'], os.linesep) for url in self.finished])
        self.f.close()
        # 替换旧列表
        os.rename('%s_new' % self.filename, self.filename)

    def parse(self, html):
        raise NotImplementedError

