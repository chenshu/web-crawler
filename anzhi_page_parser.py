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
import urllib

class AnzhiPageParser(HTMLParser):

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
                if k == 'class' and v == 'd_img l':
                    self.img = 1
                    break
                elif k == 'class' and v == 'titleline':
                    self.recoding = 1
                    break
                elif k == 'class' and v == 'des':
                    self.recoding = 1
                elif k == 'class' and v == 'imgoutbox':
                    self.pic = 1
                    break
        elif tag == 'img' and self.img == 1:
            for k, v in attrs:
                if k == 'src':
                    self.url = v
                    break
        elif tag == 'img' and self.pic == 1:
            for k, v in attrs:
                if k == 'src':
                    self.urls.append(v)
                    break

    def handle_endtag(self, tag):
        if tag == 'div' and self.img == 1:
            self.img = 0
        elif tag == 'div' and self.recoding == 1:
            self.recoding = 0
        elif tag == 'div' and self.pic == 1:
            self.pic = 0

    def handle_data(self, data):
        if self.recoding == 1:
            data = data.strip().replace('\n', '\t')
            data = data.strip().replace('\r', '\t')
            if data != '':
                sys.stdout.write('\t%s' % (data.encode('utf-8')))

if __name__ == '__main__':
    pool = redis.ConnectionPool(host='localhost', port=6379, db=2)
    r = redis.Redis(connection_pool=pool)
    parser = AnzhiPageParser()
    '''
    for f in ['www.anzhi.com/soft_71963.html', 'www.anzhi.com/soft_60877.html', 'www.anzhi.com/soft_151594.html']:
        with codecs.open(f, 'r', 'utf-8') as fp:
            #with codecs.open('www.anzhi.com/soft_108812.html', 'r', 'utf-8') as fp:
            data = fp.read().replace(u'<div id="line1"><input  type="radio" value="5" name="feedbacktype"/ class="other">其他举报理由</div>', '').replace(u'//document.write(\'<script language="javascript" type="text/javascript" src="/user.php?rand=\'+Math.random()+\'"><\/script>\');', '').replace('\\', '')
            regex = re.compile(r'<([A-Za-z0-9/=!\-_" #\.:/;]*[^<>A-Za-z0-9/=!\-_" #\.:/;]+?[A-Za-z0-9/=!\-_" #\.:/;]*)>')
            s = re.findall(regex, data)
            print len(s)
            print s
            data = re.sub(regex, '\\1', data)
            regex = re.compile(r'name="([^ ]*"+[^ ]*)" ')
            s = re.findall(regex, data)
            print len(s)
            print s
            data = re.sub(regex, 'name="%s" ' % (urllib.quote('\\1')), data)
            #print data.encode('utf-8')
            data = parser.unescape(data)
            parser.feed(data)
            sys.stdout.write('\n')
    parser.close()
    sys.exit()
    '''
    host = 'www.anzhi.com'
    dirname = '%s/%s' % (os.path.dirname(os.path.realpath(__file__)), host)
    files = os.listdir('%s' % (dirname))
    for filename in files:
        apk_id = filename.split('.')[0].split('_')[1]
        referer = 'http://%s/%s' % (host, filename)
        sys.stdout.write('%s\t%s' % (apk_id, referer))
        with codecs.open('%s/%s' % (dirname, filename), 'r', 'utf-8') as fp:
            data = fp.read().replace(u'<div id="line1"><input  type="radio" value="5" name="feedbacktype"/ class="other">其他举报理由</div>', '').replace(u'//document.write(\'<script language="javascript" type="text/javascript" src="/user.php?rand=\'+Math.random()+\'"><\/script>\');', '').replace('\\', '')
            regex = re.compile(r'<([A-Za-z0-9/=!\-_" #\.:/;]*[^<>A-Za-z0-9/=!\-_" #\.:/;]+?[A-Za-z0-9/=!\-_" #\.:/;]*)>')
            data = re.sub(regex, '\\1', data)
            regex = re.compile(r'name="([^ ]*"+[^ ]*)" ')
            data = re.sub(regex, 'name="%s" ' % (urllib.quote('\\1')), data)
            data = parser.unescape(data)
            parser.feed(data)
            sys.stdout.write('\n')
            if parser.url is not None and parser.url != '':
                r.set('%s_avatar' % (referer), parser.url)
            if len(parser.urls) != 0:
                r.rpush('%s_pic' % (referer), *parser.urls)
            del parser.urls[:]
    parser.close()
