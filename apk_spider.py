#!/usr/bin/env python
# -*- coding: utf-8 -*-

import StringIO
import gzip
import re
from spider import Spider
from collections import defaultdict

class ApkSpider(Spider):

    def parse(self, html):
        urls = re.findall(r'http://static.apk.hiapk.com/html/([0-9/]+)\.html', html)
        for url in urls:
            url_id = url.split('/')[-1]
            new_url = 'http://apk.hiapk.com/SoftDetails.aspx?action=GetBaseInfo&apkId=%s' % (url_id)
            self.get(new_url, self.parse)

if __name__ == '__main__':
    spider = ApkSpider(name = 'hiapk', host = 'apk.hiapk.com', start_url = '/', timeout = 10)
    spider.start()
