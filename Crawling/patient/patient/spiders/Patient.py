import scrapy
from patient.items import PatientItem
import re
import json
from scrapy.spiders import CrawlSpider, Rule
from scrapy.linkextractors import LinkExtractor
import os

class PatientDiscussionSpider(scrapy.Spider):
    name = 'patient'
    allowed_domains = ['patient.info']
    open("group_profiling.txt", 'w')
    os.makedirs("data")
    def __init__(self):
        # self.file = open('Abdominal_Disorders.jl','a')
        # this line need to be scalable

        self.file_dic = {}
        self.numOfExpectedPages_dic = {}
        self.page_count = 0
        self.temp_dict = {}
        self.profile = {}
        

    def toDigits(self, string):
        result = ""
        for char in string:
            if char >= '0' and char <= '9':
                result += char
        return int(result)
    
    def start_requests(self):
        # start from the target page
        # start_urls = ['https://patient.info/forums/discuss/browse/abdominal-disorders-3321']
        # start_urls = ['https://patient.info/forums/discuss/browse/citalopram-2618']
        # start_urls = ['https://patient.info/forums/discuss/browse/menopause-1411']
        start_urls = []
        seed = "https://patient.info/forums/index-"
        for number in range(97, 123):
            start_urls.append(seed+chr(number))
        for url in start_urls:
            yield scrapy.Request(url=url, callback=self.traversal_pages)
        
    def traversal_pages(self, response):
        # print(response.css("tr[class='row-0']"))
        for href_pair in response.css("tr[class='row-0']"):
            #  get into the main page of specific diseases
            for href in href_pair.css("td a::attr(href)").extract():
                url = "https://patient.info/" + href
                yield scrapy.Request(url=url, callback=self.parse)
        
    def parse(self, response):
        topic = response.css("div[class='masthead'] h1[class='articleHeader__title masthead__title']::text").extract()[0].strip()
        topic = re.sub(r'[^\w\s-]', '', topic)
        name = "_".join(topic.replace("-", " ").split())
        
        if not self.numOfExpectedPages_dic.__contains__(name):
            #  initialize dict to store maximum number of pages for each diseases
            self.numOfExpectedPages_dic[name] = {}
            self.numOfExpectedPages_dic[name]["max_page"] = int(response.css("select[name='page'][class='submit reply__control reply-pagination'] option ::text").extract()[0].split('/')[-1])
            self.numOfExpectedPages_dic[name]["current_page"] = 1
            # record stats of the group
            member = response.css("span[class='label masthead__actions__link'] span[class='label__text'] a::text").extract()[0].strip()
            post = response.css("div[class='masthead__actions col grid'] div span[class='label masthead__actions__link'] span[class='label__text']::text").extract()[-1].strip()
            profile_dict = {"group":name, "member": self.toDigits(member), "post": self.toDigits(post)}
            self.stat_file = open("group_profiling.txt", 'a')
            self.stat_file.write(json.dumps(profile_dict) + '\n')
            self.stat_file.close()
            # create the file to store corresponding diseases discusssion
            current_file = open('data/'+name + '.jl','a')
            self.file_dic[name] = current_file
        else:
            self.numOfExpectedPages_dic[name]["current_page"] += 1
        #  check if it reachs the page at the end
        if self.numOfExpectedPages_dic[name]["current_page"] > self.numOfExpectedPages_dic[name]["max_page"]:
            return

        # follow links to other pages
        for href in response.css("a[rel='discussion'][title='View replies']::attr(href)").extract():
            complet_href = "https://patient.info" + href
            yield scrapy.Request(complet_href, callback=self.disscusion_parse)
            
        # next redirect
        nextPageUrl = response.css("link[rel='next'] ::attr(href)").extract_first()
        if nextPageUrl != None:
            yield scrapy.Request(nextPageUrl, callback=self.parse)  
    
    def disscusion_parse(self, response): 
        if response.url.find("patient.info/forums/discuss/") != -1:

            item = PatientItem() 
            # content id
            content_id = response.css("meta[property='og:url']::attr(content)").extract()[0][-6:]
            item['group'] = response.css("div[class='container articleHeader__tools'] ol[class='breadcrumbs'] li[class='breadcrumb-item'] a span::text").extract()[-1].strip()
            item['content_id'] = content_id 
            item['url'] = response.url

            # writer part
            writer = response.css("div[class='author'] h5[class='author__info'] a::text").extract()[0]
            post = response.xpath("//div[@id='post_content'][@class='post__content']/p//text()").extract()

            post_content =  " ".join(line for line in post[:-1])
            post_timestamp  = response.css("div[id='topic'][class='post__main'] p[class='post__stats'] time[class='fuzzy']::attr(datetime)").extract_first()
            dict_post = {'poster':writer, 'text':post_content, 'timestamp':post_timestamp}
            item['post'] = dict_post

            # replies part
            dict_reply = {}
            reply = response.css("ul[class='comments'] li[class='comment'] article[class='post post__root']")
            count = 0
            for i in range(len(reply)):
                responsers = reply[i].css("div[class='post__header'] h5[class='author__info'] a[rel='nofollow author']::text").extract_first()
                response_time = reply[i].css("div[class='post__header'] p[class='post__stats'] time[class='fuzzy']::attr(datetime)").extract_first()
                response_text_list = reply[i].xpath("div[@class='post__content break-word'][@itemprop='text']/p//text()").extract()

                pattern = re.compile("\s*x+\s*")
                if len(response_text_list) > 0 and re.search(pattern, response_text_list[-1]) != None:
                    response_text_list = response_text_list[:-1]
                elif len(response_text_list) > 1 and re.search(pattern, response_text_list[-2]) != None:
                    response_text_list = response_text_list[:-2]
                response_text = " ".join(response_text_list).strip().replace('\r\n','')
                
                # if responsers == writer:
                #     post_content.join(response_text)
                # else:
                if response_text != "":
                    count += 1
                    dict_reply[count] = {'poster':responsers, 'text':response_text, 'timestamp':response_time}

                nested_reply = reply[i].css("ul[class='comments comments--nested'] li[class='comment comment--nested'] article[class='post']")

                for m in range(len(nested_reply)):
                    nested_responsers = nested_reply[m].css("div[class='post__header'] h5[class='author__info'] a[rel='nofollow author']::text").extract_first()
                    nested_response_time = nested_reply[m].css("div[class='post__header'] p[class='post__stats'] time[class='fuzzy']::attr(datetime)").extract_first()
                    nested_response_text_list = nested_reply[m].xpath("div[@class='post__content break-word'][@itemprop='text']/p//text()").extract()
                    pattern = re.compile("\s*x+\s*")
                    if len(nested_response_text_list) > 0 and re.search(pattern, nested_response_text_list[-1]) != None:
                        nested_response_text_list = nested_response_text_list[:-1]
                    elif len(nested_response_text_list) > 1 and re.search(pattern, nested_response_text_list[-2]) != None:
                        nested_response_text_list = nested_response_text_list[:-2]
                    nested_response_text = " ".join(nested_response_text_list).strip().replace('\r\n','')

                    # if nested_responsers == writer:
                    #     post_content.join(nested_response_text)
                    # else:
                    if nested_response_text != "": 
                        count += 1
                        dict_reply[count] = {'poster':nested_responsers, 'text':nested_response_text, 'timestamp':nested_response_time}
                
            item['reply'] = dict_reply

            # next reply page
            nextPageUrl = response.css("a[class='reply__control reply-ctrl-last link']::attr(href)").extract_first()
            if nextPageUrl != None:
                yield scrapy.Request(nextPageUrl, callback=self.disscusion_parse)
            
            item['group'] = re.sub(r'[^\w\s-]', '', item['group'])
            name = "_".join(item['group'].replace("-", " ").split())
            
            self.file_dic[name].write(json.dumps(dict(item))+ '\n')

 
