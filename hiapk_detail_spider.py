#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import with_statement
import os
import os.path
import sys
import re
import time
import shutil
from spider import Spider

class HiApkDetailSpider(Spider):

    def start(self):
        # 是否是更新抓取
        if self.update == False and self.r.exists('%s_fetched' % (self.name)):
            self.r.rename('%s_fetched' % (self.name), '%s_finished' % (self.name))
        else:
            urls = self.r.zrange('%s' % (self.name), 0, -1)
            scores = [1 for i in range(len(urls))]
            for i, x in enumerate(urls):
                scores.insert(i * 2, x)
            self.r.zadd('%s_unfetch' % (self.name), *scores)

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
            self.get(tasks[0], None, self.saveHtml)

    def saveHtml(self, url, html, temp=None):
        path = re.findall(r'http://static.apk.hiapk.com/html/([0-9/]+)\.html', url)[0]
        dirname = '%s/static.apk.hiapk.com/html/%s' % (os.path.dirname(os.path.realpath(__file__)), '/'.join(path.split('/')[0:-1]))
        if not os.path.exists(dirname):
            os.makedirs(dirname)
        if temp is None:
            with open('%s/%s.html' % (dirname, path.split('/')[-1]), 'w+') as fp:
                fp.write(html)
        else:
            shutil.move(temp, '%s/%s.html' % (dirname, path.split('/')[-1]))

if __name__ == '__main__':
    spider = HiApkDetailSpider(name = 'hiapk_detail', host = 'apk.hiapk.com', path = '/', timeout = 10, update = True)
    spider.start()
