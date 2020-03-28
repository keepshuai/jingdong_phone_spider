# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://doc.scrapy.org/en/latest/topics/item-pipeline.html
import pymongo


class MongoPipeline(object):
    def __init__(self, mongo_url, mongo_db, collection):
        self.mongo_url = mongo_url
        self.mongo_db = mongo_db
        self.collection = collection

    @classmethod
    # from_crawler是一个类方法，由 @classmethod标识，是一种依赖注入的方式，它的参数就是crawler
    # 通过crawler我们可以拿到全局配置的每个配置信息，在全局配置settings.py中的配置项都可以取到。
    # 所以这个方法的定义主要是用来获取settings.py中的配置信息
    def from_crawler(cls, crawler):
        return cls(
            mongo_url=crawler.settings.get('MONGO_URL'),
            mongo_db=crawler.settings.get('MONGO_DB'),
            collection=crawler.settings.get('COLLECTION')
        )

    def open_spider(self, spider):
        self.client = pymongo.MongoClient(self.mongo_url)
        self.db = self.client[self.mongo_db]

    def process_item(self, item, spider):
        # name = item.__class__.collection
        name = self.collection
        self.db[name].insert(dict(item))
        return item

    def close_spider(self, spider):
        self.client.close()