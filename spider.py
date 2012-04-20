#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import gzip
import redis
import StringIO
import cookielib
import simplejson as sj
from urllib import urlencode
from urllib2 import build_opener, HTTPCookieProcessor, HTTPError, URLError
from datetime import datetime

class Spider(object):

    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)
        # 设置名称
        if not getattr(self, 'name', None):
            raise ValueError("%s must have a name" % type(self).__name__)
        # 设置host
        if not getattr(self, 'host', None):
            raise ValueError("%s must have a host" % type(self).__name__)
        # 设置入口路径
        if not getattr(self, 'path', None):
            raise ValueError("%s must have a path" % type(self).__name__)
        # 入口url
        self.start_url = 'http://%s%s' % (self.host, self.path)
        # 设置链接超时时间
        if not getattr(self, 'timeout', None):
            self.timeout = 10
        self.cookie = cookielib.CookieJar()
        self.GMT_FORMAT = '%a, %d %b %Y %H:%M:%S GMT'
        # redis
        pool = redis.ConnectionPool(host='localhost', port=6379, db=0)
        self.r = redis.Redis(connection_pool=pool)
        # 本次需要抓取
        unfetch = list()
        # 本次已经抓取或者不需要抓取
        fetched = dict()
        # 获取上次的抓取结果
        keys = self.r.hkeys('%s_finished' % (self.name))
        values = []
        if len(keys) != 0:
            values = self.r.hmget('%s_finished' % (self.name), keys)
        self.finished = dict(zip(keys, [sj.loads(v) for v in values]))
        for url in self.finished:
            last_modified = self.finished[url]['last_modified']
            expires = self.finished[url]['expires']
            etag = self.finished[url]['etag']
            last_modified = datetime.strptime(last_modified, self.GMT_FORMAT)
            expires = datetime.strptime(expires, self.GMT_FORMAT)
            # 已经过期
            if expires <= datetime.now():
                unfetch.append(url)
                unfetch.append(1)
            # 没有过期
            else:
                fetched[url] = sj.dumps({'last_modified' : self.finished[url]['last_modified'], 'expires' : self.finished[url]['expires'], 'etag' : self.finished[url]['etag']})
        if len(unfetch) != 0:
            self.r.zadd('%s_unfetch' % (self.name), *unfetch)
        if len(fetched) != 0:
            self.r.hmset('%s_fetched' % (self.name), **fetched)

    # 抓取页面
    def get(self, url, parseUrl = None, saveHtml = None):
        try:
            # 如果已经抓取过
            if self.r.hexists('%s_fetched' % (self.name), url):
                self.r.zrem('%s_unfetch' % (self.name), url)
                return
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
                ('User-Agent', 'Mozilla/5.0 (X11; Linux i686) AppleWebKit/535.19 (KHTML, like Gecko) Chrome/18.0.1025.162 Safari/535.19')
            ]

            # 如果不是入口url设置Referer
            if url != self.start_url:
                self.opener.addheaders.append(('Referer', self.start_url))

            # 判断当前url是否曾经抓取过
            if url in self.finished:
                # 获取当前页面的上次修改时间
                last_modified = self.finished[url]['last_modified']
                # 设置If-Modified-Since
                self.opener.addheaders.append(('If-Modified-Since', last_modified))
                # 获取当前页面的内容hash
                etag = self.finished[url]['etag']
                # 设置If-None-Match
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
            # 获取页面的编码方式
            vary = info['Vary'] if 'Vary' in info else None
            data = response.read()
            temp = None
            try :
                data = data.decode('utf-8')
            except UnicodeDecodeError, e:
                os.popen('wget -q -O /tmp/%s %s' % (self.name, url))
                temp = '/tmp/%s' % (self.name)
            if temp is None:
                data = data.encode('utf-8')
            # gzip解压缩
            if vary is not None and vary == 'Accept-Encoding':
                s = StringIO.StringIO(data)
                gzipper = gzip.GzipFile(fileobj = s)
                data = gzipper.read()
            # 是否需要分析页面继续解析url
            if parseUrl is not None:
                # 分析页面获取url
                urls = parseUrl(url, data)
                for new_url in urls:
                    # 新的url或者本次需要抓取
                    if not self.r.hexists('%s_fetched' % (self.name), new_url):
                        self.r.zincrby('%s_unfetch' % (self.name), new_url, 1)
            # 是否需要保存数据
            if saveHtml is not None:
                saveHtml(url, data, temp)
            # 更新本次已经抓取
            self.r.hset('%s_fetched' % (self.name), url, sj.dumps({'last_modified' : last_modified.strftime(self.GMT_FORMAT), 'expires' : expires.strftime(self.GMT_FORMAT), 'etag' : etag}))
            # 删除本次需要抓取
            self.r.zrem('%s_unfetch' % (self.name), url)
            # print '200\t%s' % (url)
        except HTTPError, e:
            # 如果页面没有改动
            if e.code == 304:
                # 更新本次已经抓取
                self.r.hset('%s_fetched' % (self.name), url, sj.dumps(self.finished[url]))
                # 删除本次需要抓取
                self.r.zrem('%s_unfetch' % (self.name), url)
                # print '304\t%s' % (url)
            elif e.code == 404:
                # 删除本次需要抓取
                self.r.zrem('%s_unfetch' % (self.name), url)
                # print '404\t%s' % (url)
            else:
                print e, url
        except URLError, e:
            print e, url

    def start(self):
        raise NotImplementedError

    def parseUrl(self, url, html):
        raise NotImplementedError

    def saveHtml(self, url, html, temp=None):
        raise NotImplementedError

