#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import with_statement
import os
import os.path
import sys
import re
import time
from spider import Spider

class AnzhiSpider(Spider):

    def start(self):
        # 是否是更新抓取
        if self.update == False and self.r.exists('%s_fetched' % (self.name)):
            self.r.rename('%s_fetched' % (self.name), '%s_finished' % (self.name))
        urls = [self.start_url, 1]
        # 抓取入口
        for i in range(2):
            for j in range(3000):
                urls.append('http://%s/sort_%s_%s_hot.html' % (self.host, i, j))
                urls.append(1)
        self.r.zadd('%s_unfetch' % (self.name), *urls)
        self.r.hdel('%s_fetched' % (self.name), self.start_url)

        count = 0
        while True:
            count = count + 1
            if count % 10 == 0:
                time.sleep(5)
            # 筛选引用数最多的url
            tasks = self.r.zrevrange('%s_unfetch' % self.name, 0, 0)
            # 没有抓取任务
            if tasks is None or len(tasks) == 0:
                break
            self.get(tasks[0], self.parseUrl, self.saveHtml)

    def parseUrl(self, url, html):
        paths = re.findall(r'/soft_([0-9]+)\.html', html)
        urls = ['http://%s/soft_%s.html' % (self.host, path) for path in paths]
        return urls

    def saveHtml(self, url, html):
        paths = re.findall(r'/soft_([0-9]+)\.html', url)
        if paths is not None and len(paths) > 0:
            dirname = '%s/www.anzhi.com' % (os.path.dirname(os.path.realpath(__file__)))
            if not os.path.exists(dirname):
                os.makedirs(dirname)
            with open('%s/soft_%s.html' % (dirname, paths[0]), 'w+') as fp:
                fp.write(html)

if __name__ == '__main__':
    spider = AnzhiSpider(name = 'anzhi', host = 'www.anzhi.com', path = '/', timeout = 10, update = True)
    spider.start()
