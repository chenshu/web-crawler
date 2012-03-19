#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import os.path
import time
import cookielib
from urllib import urlencode
from urllib2 import build_opener, HTTPCookieProcessor, HTTPError, URLError

count = 0

def download(url, apk_id, host, referer):
    global count
    count = count + 1
    if count % 10 == 0:
        time.sleep(5)
    try:
        cookie = cookielib.CookieJar()
        opener = build_opener(HTTPCookieProcessor(cookie))
        opener.addheaders = [
            ('Accept', 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'),
            ('Accept-Charset', 'GBK,utf-8;q=0.7,*;q=0.3'),
            ('Accept-Encoding', 'gzip,deflate,sdch'),
            ('Accept-Language', 'zh-CN,zh;q=0.8'),
            ('Connection', 'keep-alive'),
            ('Host', host),
            ('Referer', referer),
            ('User-Agent', 'Mozilla/5.0 (Windows NT 5.1) AppleWebKit/535.7 (KHTML, like Gecko) Chrome/16.0.912.63 Safari/535.7')
        ]
        response = opener.open('%s%s' % (url, apk_id), timeout = 10)
        info = response.info()
        content_type = info['Content-Type'] if 'Content-Type' in info else None
        content_length = info['Content-Length'] if 'Content-Length'in info else None
        if content_type == 'application/vnd.android.package-archive' and content_length > 0:
            data = response.read()
            if len(data) == int(content_length):
                return data
            else:
                print 'error\tsize\t', apk_id
        else:
            print 'error\ttype\t', apk_id
    except HTTPError, e:
        print e
    except URLError, e:
        print e
    return None

def save(data, apk_id, dirname):
    with open('%s/%s' % (dirname, apk_id), 'w+') as fp:
        fp.write(data)

if __name__ == '__main__':
    host = 'static.apk.hiapk.com'
    path = 'html'
    dirname = '%s/%s/%s' % (os.path.dirname(os.path.realpath(__file__)), host, path)
    dirname_apk = '%s/%s_apk' % (os.path.dirname(os.path.realpath(__file__)), host)
    if not os.path.exists(dirname_apk):
        os.makedirs(dirname_apk)
    years = os.listdir(dirname)
    for year in years:
        months = os.listdir('%s/%s' % (dirname, year))
        for month in months:
            files = os.listdir('%s/%s/%s' % (dirname, year, month))
            for filename in files:
                url = 'http://apk.hiapk.com/Download.aspx?aid='
                referer = 'http://%s/%s/%s/%s/%s' % (host, path, year, month, filename)
                apk_id = filename.split('.')[0]
                if os.path.exists('%s/%s' % (dirname_apk, apk_id)):
                    continue
                data = download(url, apk_id, host, referer)
                if data is not None:
                    save(data, apk_id, dirname_apk)
                else:
                    print 'error\t%s\t%s' % (apk_id, referer)
