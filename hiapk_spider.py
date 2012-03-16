#!/usr/bin/env python
# -*- coding: utf-8 -*-

import re
import time
from spider import Spider

class HiApkSpider(Spider):

    def start(self):
        # 是否是更新抓取
        if self.update == False and self.r.exists('%s_fetched' % (self.name)):
            self.r.rename('%s_fetched' % (self.name), '%s_finished' % (self.name))
        urls = [self.start_url, 1]
        # 抓取入口
        for t in ('games', 'apps', 'necessary'):
            for i in range(200):
                for j in range(50):
                    urls.append('http://%s/%s_%s_1_%s' % (self.host, t, i, j))
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
            self.get(tasks[0], self.parseUrl, None)

    def parseUrl(self, url, html):
        paths = re.findall(r'http://static.apk.hiapk.com/html/([0-9/]+)\.html', html)
        urls = ['http://static.apk.hiapk.com/html/%s.html' % (path) for path in paths]
        scores = [1 for i in range(len(urls))]
        for i, x in enumerate(urls):
            scores.insert(i * 2, x)
        if len(scores) != 0:
            self.r.zadd('%s_detail' % (self.name), *scores)
        return ['http://apk.hiapk.com/SoftDetails.aspx?action=GetBaseInfo&apkId=%s' % (path.split('/')[-1]) for path in paths]

if __name__ == '__main__':
    spider = HiApkSpider(name = 'hiapk', host = 'apk.hiapk.com', path = '/', timeout = 10, update = True)
    spider.start()
