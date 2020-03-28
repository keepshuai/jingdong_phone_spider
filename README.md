# jingdong_phone_spider
### 爬取目标：

***使用scrapy和selenium爬取京东商城手机详情***

### 项目准备：

**pycharm**:scrapy, urllib, bs4, selenium等第三方库

[pycharm和python安装教程](https://www.runoob.com/w3cnote/pycharm-windows-install.html)

**mongodb**

[windows下安装Mongdb](https://www.runoob.com/mongodb/mongodb-window-install.html)

[linux下安装MongoDB](https://www.runoob.com/mongodb/mongodb-linux-install.html)



### 项目流程：

1、新建项目

2、定义item

3、对接selenium

4、解析爬虫

5、存储结果

6、配置setting文件

7、执行爬虫

#### 1 新建项目（终端CMD输入）

新建一个项目：

```
scrapy startproject scrapyseleniumtest
```

新建一个spider：

```
cd scrapyseleniuntest
scrapy genspider jd www.jd.com
```

#### 2 定义item

暂时先不定义item

##### 初步实现Spider的start _requests()方法。

```
def start_requests(self):
        for keyword in self.settings.get('KEYWORDS'):
            for page in range(1, self.settings.get('MAX_PAGE') + 1):
                url = self.base_url + quote(keyword)
                # dont_filter = True  不去重
                yield Request(url=url, callback=self.parse, meta={'page': page}, dont_filter=True)
```

#### 3 scrapy对接selenium

接下来我们需要处理这些请求的抓取。这次我们对接Selenium进行抓取，采用Downloader Middleware来实现。在Middleware中对接selenium，输出源代码之后，构造htmlresponse对象，直接返回给spider解析页面，提取数据，并且也不在执行下载器下载页面动作。

```python
# -*- coding: utf-8 -*-

class SeleniumMiddleware(object):
    # Not all methods need to be defined. If a method is not defined,
    # scrapy acts as if the downloader middleware does not modify the
    # passed objects.
 
    def __init__(self,timeout=None):
        self.logger=getLogger(__name__)
        self.timeout = timeout
        self.browser = webdriver.Chrome()
        self.browser.set_window_size(1400,700)
        self.browser.set_page_load_timeout(self.timeout)
        self.wait = WebDriverWait(self.browser,self.timeout)
    def __del__(self):
        self.browser.close()
    @classmethod
    def from_crawler(cls, crawler):
        # This method is used by Scrapy to create your spiders.
        return cls(timeout=crawler.settings.get('SELENIUM_TIMEOUT'))
    def process_request(self, request, spider):
        '''
        在下载器中间件中对接使用selenium，输出源代码之后，构造htmlresponse对象，直接返回
        给spider解析页面，提取数据
        并且也不在执行下载器下载页面动作
        htmlresponse对象的文档：
        :param request:
        :param spider:
        :return:
        '''
 
        print('PhantomJS is Starting')
        page = request.meta.get('page', 1)
        self.wait = WebDriverWait(self.browser, self.timeout)
        # self.browser.set_page_load_timeout(30)
        # self.browser.set_script_timeout(30)
        try:
            self.browser.get(request.url)
            if page > 1:
                input = self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '#J_bottomPage > span.p-skip > input')))
                input.clear()
                input.send_keys(page)
                time.sleep(5)
                # 将网页中输入跳转页的输入框赋值给input变量 EC.presence_of_element_located，判断输入框已经被加载出来
                input = self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '#J_bottomPage > span.p-skip > input')))
                # 将网页中调准页面的确定按钮赋值给submit变量，EC.element_to_be_clickable 判断此按钮是可点击的
                submit = self.wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, '#J_bottomPage > span.p-skip > a')))
                input.clear()
                input.send_keys(page)
                submit.click()  # 点击按钮
                time.sleep(5)
                # 判断当前页码出现在了输入的页面中，EC.text_to_be_present_in_element 判断元素在指定字符串中出现
                self.wait.until(EC.text_to_be_present_in_element((By.CSS_SELECTOR, '#J_bottomPage > span.p-num > a.curr'),str(page)))
                # 等待 #J_goodsList 加载出来，为页面数据，加载出来之后，在返回网页源代码
                self.wait.until(EC.text_to_be_present_in_element((By.CSS_SELECTOR, '#J_bottomPage > span.p-num > a.curr'),str(page)))
            return HtmlResponse(url=request.url, body=self.browser.page_source, request=request, encoding='utf-8',status=200)
        except TimeoutException:
            return HtmlResponse(url=request.url, status=500, request=request)
    def process_response(self, request, response, spider):
        # Called with the response returned from the downloader.
 
        # Must either;
        # - return a Response object
        # - return a Request object
        # - or raise IgnoreRequest
        return response
    def process_exception(self, request, exception, spider):
        # Called when a download handler or a process_request()
        # (from other downloader middleware) raises an exception.
 
        # Must either:
        # - return None: continue processing this exception
        # - return a Response object: stops process_exception() chain
        # - return a Request object: stops process_exception() chain
        pass
 
    def spider_opened(self, spider):
        spider.logger.info('Spider opened: %s' % spider.name)
```

首先我在__init__()里对一些对象进行初始化，包括WebDriverWait等对象，同时设置页面大小和页面加载超时时间。在process_request()方法中，我们通过Request的meta属性获取当前需要爬取的页码，将页码赋值给input变量，再将翻页的点击按钮框赋值给submit变量，然后在数据框中输入页码，等待页面加载，直接返回htmlresponse给spider解析，这里我们没有经过下载器下载，直接构造response的子类htmlresponse返回。(当下载器中间件返回response对象时，更低优先级的process_request将不在执行，转而执行其他的process_response()方法，本例中没有其他的process_response(),所以直接将结果返回给spider解析。)

#### 4 解析页面

Response对象就会回传给Spider内的回调函数进行解析。所以下一步我们就实现其回调函数，对网页来进行解析。

```python
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
```

这里我们采用BeautifulSoup进行解析，匹配所有商品，随后对结果进行遍历，依次选取商品的各种信息。



#### 5 存储结果

提取完页面数据之后，数据会发送到item pipeline处进行数据处理，清洗，入库等操作，所以我们此时当然需要定义项目管道了，在此我们将数据存储在mongodb数据库中。

```
# -*- coding: utf-8 -*-
 
# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://doc.scrapy.org/en/latest/topics/item-pipeline.html
import pymongo
class MongoPipeline(object):
    def __init__(self,mongo_url,mongo_db,collection):
        self.mongo_url = mongo_url
        self.mongo_db = mongo_db
        self.collection = collection
    @classmethod
    #from_crawler是一个类方法，由 @classmethod标识，是一种依赖注入的方式，它的参数就是crawler
    #通过crawler我们可以拿到全局配置的每个配置信息，在全局配置settings.py中的配置项都可以取到。
    #所以这个方法的定义主要是用来获取settings.py中的配置信息
    def from_crawler(cls,crawler):
        return cls(
            mongo_url=crawler.settings.get('MONGO_URL'),
            mongo_db = crawler.settings.get('MONGO_DB'),
            collection = crawler.settings.get('COLLECTION')
        )
    def open_spider(self,spider):
        self.client = pymongo.MongoClient(self.mongo_url)
        self.db = self.client[self.mongo_db]
    def process_item(self,item, spider):
        # name = item.__class__.collection
        name = self.collection
        self.db[name].insert(dict(item))
        return item
    def close_spider(self,spider):
        self.client.close()
```



#### 6 配置settings文件

配置settings文件，将项目中使用到的配置项在settings文件中配置，本项目中使用到了KEYWORDS,MAX_PAGE,SELENIUM_TIMEOUT(页面加载超时时间)，MONGOURL,MONGODB,COLLECTION。

```
KEYWORDS=['iPad']
MAX_PAGE=2
MONGO_URL = 'localhost'
MONGO_DB = 'test'
COLLECTION = 'ProductItem'
SELENIUM_TIMEOUT = 30
```

以及打开激活下载中间件和item pipeline

```
DOWNLOADER_MIDDLEWARES = {
   'scrapyseleniumtest.middlewares.SeleniumMiddleware': 543,
}
ITEM_PIPELINES = {
   'scrapyseleniumtest.pipelines.MongoPipeline': 300,
}
```



#### 7 运行爬虫，mongodb数据库查看结果

![1585370153398](C:\Users\Sheldon\AppData\Roaming\Typora\typora-user-images\1585370153398.png)

运行项目之后，在mongodb中查看数据，已经执行成功。

![img](https://img2018.cnblogs.com/i-beta/1823516/202001/1823516-20200104230507381-1107809043.png)

