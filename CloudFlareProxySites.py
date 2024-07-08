import cloudscraper
import re
from bs4 import BeautifulSoup


class CloudFlareProxySites():
    def __init__(self) -> None:
        self.method = ['http'] #to be replaced by child calsses
        self.scraper = cloudscraper.create_scraper()  # returns a CloudScraper instance
        self.urls = [] #"https://hide.mn/en/proxy-list/#list"
        self.proxies = []
        self.raw_response =''
        self.processed_response =''
        self.pattern = re.compile(r"\d{1,3}(?:\.\d{1,3}){3}(?::\d{1,5})?")
        
    def scrape_url(self, url):
        # print(self.scraper.get(url).text)  # => "<!DOCTYPE html><html><head>..."
        return self.scraper.get(url).text
    
    def response_processor(self,rsp):
        soup = BeautifulSoup(rsp, "html.parser")
        proxies = set()
        # table_div = soup.find("div", attrs={"class": "table_block"})
        # table = table_div.find("table")
        table = soup.find_all("table")[0]
        if not table:
            pass
        for row in table.findAll("tr")[1:]: ## starting from index 1 to skip table header
            count = 0
            proxy = ""
            for cell in row.findAll("td"):
                if count == 0:
                    proxy += cell.text.replace("&nbsp;", "").strip()
                elif count == 1:
                    proxy += ":"+cell.text.replace("&nbsp;", "").strip()
                elif count == 4:
                    mthd = cell.text.replace("&nbsp;", "").strip()
                    if mthd.lower() in self.method:
                        proxies.add(proxy)
                count += 1
        # self.processed_response = "\n".join(proxies)
        return "\n".join(proxies)
    
    def proxy_collector(self):
        for ur in self.urls:
            self.raw_response =self.scrape_url(ur)
            self.processed_response = self.response_processor(self.raw_response)
            self.proxies.extend(re.findall(self.pattern, self.response_processor(self.processed_response)))

cls = CloudFlareProxySites()
cls.urls = ["https://hide.mn/en/proxy-list/#list"]
cls.proxy_collector()
print(cls.proxies)