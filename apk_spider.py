#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import re
from spider import Spider

class ApkSpider(Spider):

    def parse(self, url, html):
        print url
        urls = re.findall(r'http://static.apk.hiapk.com/html/([0-9/]+)\.html', html)
        return ['http://apk.hiapk.com/SoftDetails.aspx?action=GetBaseInfo&apkId=%s' % (url.split('/')[-1]) for url in urls]

if __name__ == '__main__':
    spider = ApkSpider(name = 'hiapk', host = 'apk.hiapk.com', start_url = '/', timeout = 10)
    spider.start()
