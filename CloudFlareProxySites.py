import cloudscraper
import re


class CloudFlareProxySites:
    def __init__(self) -> None:
        self.scraper = cloudscraper.create_scraper()  # returns a CloudScraper instance
        self.urls = [] #"https://hide.mn/en/proxy-list/#list"
        self.proxies = []
        self.response =''
        self.pattern = re.compile(r"\d{1,3}(?:\.\d{1,3}){3}(?::\d{1,5})?")
        
    def scrape_url(self, url):
        print(self.scraper.get(url).text)  # => "<!DOCTYPE html><html><head>..."
    
    def response_collector(self,urls):
        pass
    
    def proxy_collector(self,urls):
        for ur in urls:
            self.response =self.scrape_url(ur)
            self.proxies.append(re.findall(self.pattern, self.response))