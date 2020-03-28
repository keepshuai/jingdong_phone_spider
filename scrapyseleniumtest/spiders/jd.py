# -*- coding: utf-8 -*-
from scrapy import Request, Spider
from urllib.parse import quote
from bs4 import BeautifulSoup


class JdSpider(Spider):
    name = 'jd'
    allowed_domains = ['www.jd.com']
    base_url = 'https://search.jd.com/Search?keyword='

    def start_requests(self):
        for keyword in self.settings.get('KEYWORDS'):
            for page in range(1, self.settings.get('MAX_PAGE') + 1):
                url = self.base_url + quote(keyword)
                # dont_filter = True  不去重
                yield Request(url=url, callback=self.parse, meta={'page': page}, dont_filter=True)

    def parse(self, response):
        soup = BeautifulSoup(response.text, 'lxml')
        lis = soup.find_all(name='li', class_="gl-item")
        for li in lis:
            proc_dict = {}
            dp = li.find(name='span', class_="J_im_icon")
            if dp:
                proc_dict['dp'] = dp.get_text().strip()
            else:
                continue
            id = li.attrs['data-sku']
            title = li.find(name='div', class_="p-name p-name-type-2")
            proc_dict['title'] = title.get_text().strip()
            price = li.find(name='strong', class_="J_" + id)
            proc_dict['price'] = price.get_text()
            comment = li.find(name='a', id="J_comment_" + id)
            proc_dict['comment'] = comment.get_text() + '条评论'
            url = 'https://item.jd.com/' + id + '.html'
            proc_dict['url'] = url
            proc_dict['type'] = 'JINGDONG'
            yield proc_dict