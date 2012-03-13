#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import with_statement
import os
import sys
import os.path
import cookielib
from urllib import urlencode
from urllib2 import urlopen, Request, build_opener, HTTPCookieProcessor, HTTPError
import gzip
import StringIO
from collections import defaultdict
from datetime import datetime
import time

class Spider(object):

    count = 0

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
        self.cookie = cookielib.CookieJar()
        self.GMT_FORMAT = '%a, %d %b %Y %H:%M:%S GMT'
        # 本次已经抓取或者不需要抓取的页面
        self.last = defaultdict(dict)
        # 本次需要抓取的页面
        self.now = defaultdict(int)
        # 上次已经抓取的页面
        self.finished = defaultdict(dict)
        self.filename = '%s/%s_urls' % (os.path.dirname(os.path.realpath(__file__)), self.name)
        if os.path.exists(self.filename):
            with open(self.filename, 'r') as fp:
                for line in fp:
                    url, last_modified, expires, etag = line.strip().split('\t')
                    last_modified = datetime.strptime(last_modified, self.GMT_FORMAT)
                    expires = datetime.strptime(expires, self.GMT_FORMAT)
                    self.finished[url]['last_modified'] = last_modified
                    self.finished[url]['expires'] = expires
                    self.finished[url]['etag'] = etag
                    # 已经过期
                    if expires <= datetime.now():
                        self.now[url] = 1
                    # 没有过期
                    else:
                        self.last[url] = self.finished[url]

    # 抓取页面，并进行页面分析
    def get(self, url, callback = None):
        self.count += 1
        if (self.count % 10 == 0):
            #print '%s\t%s\t%s' % (len(self.finished), len(self.now), len(self.last))
            time.sleep(5)
        try:
            # 是否需要抓取
            if url in self.last:
                return None

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
            # 设置If-Modified-Since
            if last_modified is not None:
                self.opener.addheaders.append(('If-Modified-Since', last_modified.strftime(self.GMT_FORMAT)))
            # 获取当前页面的内容hash
            etag = self.finished[url]['etag'] if url in self.finished else None
            # 设置If-None-Match
            if etag is not None:
                self.opener.addheaders.append(('If-None-Match', etag))

            # 抓取页面
            response = self.opener.open(url, timeout = self.timeout)
            info = response.info()
            # 获取页面的上次修改时间
            last_modified = datetime.strptime(info['Last-Modified'], self.GMT_FORMAT) if 'Last-Modified' in info else datetime.now()
            # 获取页面的过期时间
            expires = datetime.strptime(info['Expires'], self.GMT_FORMAT) if 'Expires' in info else datetime.now()
            # 获取页面的内容hash
            etag = info['ETag'] if 'ETag' in info else None

            # gzip解压缩
            data = StringIO.StringIO(response.read())
            gzipper = gzip.GzipFile(fileobj = data)
            if callback is not None:
                # 分析页面获取url
                urls = callback(url, gzipper.read())
                for new_url in urls:
                    # 新的url
                    if not new_url in self.last:
                        self.now[new_url] = self.now[new_url] + 1 if new_url in self.now else 1
            # 更新本次已经抓取
            self.last[url]['last_modified'] = last_modified
            self.last[url]['expires'] = expires
            self.last[url]['etag'] = etag
            # 删除本次需要抓取
            del self.now[url]
            #print '200\t%s' % (url)
        except HTTPError, e:
            # 如果返回304
            if e.code == 304:
                # 更新本次已经抓取
                self.last[url] = self.finished[url]
                # 删除本次需要抓取
                del self.now[url]
                #print '304\t%s' % (url)
            else:
                print e
        # 筛选引用数最多的页面
        self.get(sorted(self.now.items(), lambda x, y : cmp(x[1], y[1]), reverse = True)[1][0], self.parse)
        return None

    def start(self):
        # 抓取页面
        url = 'http://%s%s' % (self.host, self.start_url)
        self.now[url] = 1
        self.get(url, self.parse)

        # 更新抓取列表
        self.f = open('%s_new' % (self.filename), 'w+')
        self.f.writelines(['%s\t%s\t%s\t%s%s' % (url, self.last[url]['last_modified'].strftime(self.GMT_FORMAT), self.last[url]['expires'].strftime(self.GMT_FORMAT), self.last[url]['etag'], os.linesep) for url in self.last])
        self.f.close()
        # 替换旧列表
        os.rename('%s_new' % self.filename, self.filename)

    def parse(self, url, html):
        raise NotImplementedError

