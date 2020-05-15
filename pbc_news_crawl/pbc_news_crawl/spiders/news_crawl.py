# -*- coding: utf-8 -*-
import os
import re
import js2py
import scrapy
from pbc_news_crawl.items import PbcNewsCrawlItem


class NewsCrawlSpider(scrapy.Spider):
    name = 'pbc_news_crawl'
    allowed_domains = ['pbc.gov.cn']
    start_urls = ['http://www.pbc.gov.cn/goutongjiaoliu/113456/113469/11040/index1.html']
    headers = {
        'User-Agent': "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/59.0.3071.115 Safari/537.36",
        "referer": "http://www.pbc.gov.cn/goutongjiaoliu/113456/113469/11040/index1.html"
    }
    url = "http://www.pbc.gov.cn/goutongjiaoliu/113456/113469/11040/index1.html"

    def start_requests(self):
        '''
        重写start_requests
        :return:
        '''
        for url in self.start_urls:
            yield scrapy.Request(url, headers=self.headers, dont_filter=True, callback=self.get_real_cookies)

    def get_real_cookies(self, response):
        res_txt = response.text
        tag_script = re.search(r'<script type="text/javascript">(?P<script>.*)</script>',
                               res_txt,
                               flags=re.DOTALL)
        script_content = tag_script.group('script')
        # 修改js，取得js运行后生成的值
        if "_0x56ae" in script_content:
            js_text = re.sub(r"window\[_0x56ae(.*?)=", "return ", script_content, 1)
            # 模拟运行js
            con = js2py.EvalJs()
            con.execute(js_text)
            dynamicurl = con._0x33f22a()
            # 请求cookies生成页面
            yield scrapy.Request('http://www.pbc.gov.cn/' + dynamicurl, headers=self.headers, dont_filter=True, callback=self.get_real_response)

    def get_real_response(self, response):
        yield scrapy.Request(self.url, headers=self.headers, dont_filter=True, callback=self.get_data)

    def get_data(self, response):
        # print(response.body.decode())
        if "新闻" in response.text:
            news_table = response.xpath('//*[@id="11040"]/div[2]/div[1]/table/tbody/tr[2]/td/table')
            for news_tag in news_table:
                item = PbcNewsCrawlItem()
                title = news_tag.xpath('./tbody/tr/td[2]/font/a/@title').extract_first()
                news_url = news_tag.xpath('./tbody/tr/td[2]/font/a/@href').extract_first()
                news_update_at = news_tag.xpath('./tbody/tr/td[2]/span/text()').extract_first()
                if news_update_at is None:
                    news_update_at = news_tag.xpath('./tbody/tr/td[2]/a/span/text()').extract_first()
                item["title"] = title
                item["news_url"] = 'http://www.pbc.gov.cn/'+news_url
                item["news_updated_at"] = news_update_at
                # print(item)
                yield item
            # 获取下一页链接
            next_page_url = response.xpath('//*[@id="11040"]/div[2]/div[2]/table/tbody/tr/td[1]/a[3]/@tagname').extract_first()
            if next_page_url is not None:
                if next_page_url != "[NEXTPAGE]":
                    next_url = 'http://www.pbc.gov.cn/' + next_page_url
                    yield scrapy.Request(next_url, headers=self.headers, callback=self.get_data)


if __name__ == '__main__':
    # os.system("scrapy crawl pbc_news_crawl -o pbc_news_crawl.csv --nolog")
    os.system("scrapy crawl pbc_news_crawl -o pbc_news_crawl.csv")
