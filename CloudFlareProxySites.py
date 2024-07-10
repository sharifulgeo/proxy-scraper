import cloudscraper
import re
from bs4 import BeautifulSoup
import asyncio
# import aiocfscrape #import CloudflareScraper

proxies_collected = []

class MyException(Exception):
    pass

class CloudFlareProxySitesScraper(MyException):
    def __init__(self,method,url) -> None:
        self.method = method #to be replaced by child classes
        self.scraper = cloudscraper.create_scraper()  # returns a CloudScraper instance
        self.url = url #"https://hide.mn/en/proxy-list/#list"
        self.proxies = []
        self.proxy = ""
        self.raw_response = ''
        self.processed_response =''
        self.pattern = re.compile(r"\d{1,3}(?:\.\d{1,3}){3}(?::\d{1,5})?")
        
    async def scrape_url(self, url) -> str:
        return self.scraper.get(url).text
    
    async def response_processor_hidemn(self,rsp) -> str:
        soup =  BeautifulSoup(rsp, "html.parser")
        proxies = set()
        tables =  soup.find_all("table")
        if  len(tables)<1:
            raise MyException("Extracted no table for IP and Port for site {rsp.url}.")
        else:
            table = tables[0]
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
                
                    if  isinstance(self.method,list):
                        if len(m for m in self.method if m in mthd.lower())>0:
                            proxies.add(proxy)
                    else:
                        if self.method in mthd.lower():
                            proxies.add(proxy)
                    # print(proxy,mthd)          
                count += 1
        # self.processed_response = "\n".join(proxies)
        return "\n".join(proxies)
    
    async def response_processor_sslproxies(self,rsp) -> str:
        soup =  BeautifulSoup(rsp, "html.parser")
        proxies = set()
        tables =  soup.find_all("table")
        if  len(tables)<1:
            raise MyException("Extracted no table for IP and Port for site {rsp.url}.")
        else:
            table = tables[0]
        for row in table.findAll("tr")[1:]: ## starting from index 1 to skip table header
            count = 0
            proxy = ""
            for cell in row.findAll("td"):
                if count == 0:
                    proxy += cell.text.replace("&nbsp;", "").strip()
                elif count == 1:
                    proxy += ":"+cell.text.replace("&nbsp;", "").strip()
                
                if proxy:
                    proxies.add(proxy)
                          
                count += 1
        # self.processed_response = "\n".join(proxies)
        return "\n".join(proxies)
    
    async def proxy_collector(self) -> None:
        print(f"Scraping {self.url} .............")
        self.raw_response= await self.scrape_url(self.url)
        if "hide.mn/en" in self.url:
            self.processed_response = await self.response_processor_hidemn(self.raw_response)
        elif "sslproxies.org" in self.url:
            self.processed_response = await self.response_processor_sslproxies(self.raw_response)
            
        self.proxies.extend(re.findall(self.pattern, self.processed_response))
        # proxies_collected.extend(self.proxies)
        return self.proxies

    
class CloudFlareProxySitesRunner(CloudFlareProxySitesScraper):
    def __init__(self,mthd,ulrs):
        self.method = mthd
        self.urls = ulrs   # to changed by the instance classes
        # super().__init__()
    
    async def runner_(self):
        proxies_collected = asyncio.gather(*(CloudFlareProxySitesScraper(self.method,ur).proxy_collector() for ur in self.urls))
        # proxies_collected.extend(await self.proxies)
        await proxies_collected
        if any([isinstance(prxy,list) for prxy in proxies_collected]):
            prxs = [prxy for sblist in proxies_collected for prxy in sblist]
        else:
            prxs =proxies_collected
        return prxs
        # print(proxies_collected)
        # for ur in self.urls:
        #     result = CloudFlareProxySitesScraper(self.method,ur).proxy_collector()
        #     proxies_collected.extend(result)
        
    def get_url(self):
        return self.urls
    
    async def scrape(self):
        await self.runner_()
        # if any([isinstance(prxy,list) for prxy in proxies_collected]):
        #     prxs = [prxy for sblist in proxies_collected for prxy in sblist]
        # else:
        #     prxs =proxies_collected
        # return prxs
    
    # async def scrape(self):
    #     # coros = [request_async() for _i in range(10)]
    #     results = await asyncio.gather(*(CloudFlareProxySitesScraper(self.method,ur).proxy_collector() for ur in self.urls))
    #     return results
    # loop = asyncio.get_event_loop()
    # results = loop.run_until_complete(scrape(self))

# if __name__ == '__main__':
#     uris = [f"https://hide.mn/en/proxy-list/?start={rnge}#list" for rnge in range(0,12608,64)]
#     asyncio.run(CloudFlareProxySitesRunner('http',uris).runner_())
    
    # with open("output.txt", "w") as f:
    #     f.write("\n".join(proxies_collected))