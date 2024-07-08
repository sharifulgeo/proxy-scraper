import argparse
import asyncio
import base64
import platform
import re
import sys
import time
import httpx
import io
from bs4 import BeautifulSoup
print(sys.executable)
try:
    import Image # type: ignore
except ImportError:
    from PIL import Image
import pytesseract  # noqa: E402


class Scraper():
    if platform.system() == 'Windows':
        pytesseract.pytesseract.tesseract_cmd = r"C:\\Program Files\\Tesseract-OCR\\tesseract.exe"
    else:
        pytesseract.pytesseract.tesseract_cmd = r"/opt/homebrew/Cellar/tesseract/5.4.1/bin/tesseract"
    def __init__(self, method, _url):
        self.method = method
        self._url = _url
        self.__url = []
        self.proxies_ = []
        self.headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36'}

    def get_url(self, **kwargs):
        if isinstance(self._url,list):
            for u_ in self._url:
                self.__url.append(u_.format(**kwargs, method=self.method))
        else:
            self.__url =  self._url.format(**kwargs, method=self.method)
        return self.__url

    async def get_response(self,url_, client):
        return await client.get(url_,headers=self.headers)

    async def handle(self, response):
        return response.text

    async def scrape(self, client):
        pattern = re.compile(r"\d{1,3}(?:\.\d{1,3}){3}(?::\d{1,5})?")
        if isinstance(self._url,list):
            N=len(self._url)
            mylist = [self.__url[(i*len(self.__url))//N:((i+1)*len(self.__url))//N] for i in range(N)]
            for u_ in mylist:
                for um_ in u_:
                    response = await self.get_response(um_,client)
                    self.proxies_.append(await self.handle(response))
        else:
            response = await self.get_response(self._url,client)
            self.proxies_.append(await self.handle(response))
        return re.findall(pattern, ''.join(self.proxies_))


# From spys.me
class SpysMeScraper(Scraper):

    def __init__(self, method):
        super().__init__(method, "https://spys.me/{mode}.txt")

    def get_url(self, **kwargs):
        mode = "proxy" if self.method == "http" else "socks" if self.method == "socks" else "unknown"
        if mode == "unknown":
            raise NotImplementedError
        return super().get_url(mode=mode, **kwargs)


# From proxyscrape.com
class ProxyScrapeScraper(Scraper):

    def __init__(self, method, timeout=1000, country="All"):
        self.timout = timeout
        self.country = country
        super().__init__(method,
                         "https://api.proxyscrape.com/?request=getproxies"
                         "&proxytype={method}"
                         "&timeout={timout}"
                         "&country={country}")

    def get_url(self, **kwargs):
        return super().get_url(timout=self.timout, country=self.country, **kwargs)

# From geonode.com - A little dirty, grab http(s) and socks but use just for socks
class GeoNodeScraper(Scraper):

    def __init__(self, method, limit="500", page="1", sort_by="lastChecked", sort_type="desc"):
        self.limit = limit
        self.page = page
        self.sort_by = sort_by
        self.sort_type = sort_type
        super().__init__(method,
                         "https://proxylist.geonode.com/api/proxy-list?"
                         "&limit={limit}"
                         "&page={page}"
                         "&sort_by={sort_by}"
                         "&sort_type={sort_type}")

    def get_url(self, **kwargs):
        return super().get_url(limit=self.limit, page=self.page, sort_by=self.sort_by, sort_type=self.sort_type, **kwargs)

# From proxy-list.download
class ProxyListDownloadScraper(Scraper):

    def __init__(self, method, anon):
        self.anon = anon
        super().__init__(method, "https://www.proxy-list.download/api/v1/get?type={method}&anon={anon}")

    def get_url(self, **kwargs):
        return super().get_url(anon=self.anon, **kwargs)


# For websites using table in html
class GeneralTableScraper(Scraper):

    async def handle(self, response):
        soup = BeautifulSoup(response.text, "html.parser")
        proxies = set()
        table = soup.find("table", attrs={"class": "table table-striped table-bordered"})
        for row in table.findAll("tr"):
            count = 0
            proxy = ""
            for cell in row.findAll("td"):
                if count == 1:
                    proxy += ":" + cell.text.replace("&nbsp;", "")
                    proxies.add(proxy)
                    break
                proxy += cell.text.replace("&nbsp;", "")
                count += 1
        return "\n".join(proxies)

# For websites using div in html
class LunaProxyScraper(Scraper):

    async def handle(self, response):
        soup = BeautifulSoup(response.text, "html.parser")
        proxies = set()
        table = soup.find("div", attrs={"class": "list"})
        for row in table.findAll("div"):
            count = 0
            proxy = ""
            for cell in row.findAll("div", attrs={"class": "td"}):
                if count == 2:
                    break
                proxy += cell.text+":"
                count += 1
            proxy = proxy.rstrip(":")
            if proxy:
                proxies.add(proxy)
        return "\n".join(proxies)
    
# For scraping live proxylist from github
class ProtoPlainResponseScraper(Scraper):
            
    async def handle(self, response):
        tempproxies = response.text.split("\n")
        proxies = set()
        for prxy in tempproxies:
            if self.method in prxy:
                proxies.add(prxy.split("//")[-1])

        return "\n".join(proxies)
    
# For scraping live proxylist from other site with not protocol mentioned
class NoProtoPlainResponseScraper(Scraper):
            
    async def handle(self, response):
        proxies = set(response.text.split("\n"))
        return "\n".join(proxies)
    
    
# From https://advanced.name/freeproxy?type=socks4
class AdvanceNameScraper(Scraper):

    def __init__(self, method):
        super().__init__(method,
                         "https://advanced.name/freeproxy?"
                         "type={method}")

    def get_url(self, **kwargs):
        return super().get_url(**kwargs)

    async def handle(self, response):
        soup = BeautifulSoup(response.text, "html.parser")
        proxies = set()
        table = soup.find("table", attrs={"id": "table_proxies"})
        for row in table.findAll("tr"):
            count = 0
            proxy = ""
            for cell in row.findAll("td"):
                if count == 1:
                    proxy += base64.b64decode(cell.attrs['data-ip']).decode('utf-8')
                if count == 2:
                    proxy += ":"+base64.b64decode(cell.attrs['data-port']).decode('utf-8')
                count += 1
            if proxy:
                proxies.add(proxy)
        return "\n".join(proxies)

#From "https://www.freeproxy.world/?type=https&anonymity=&country=&speed=&port=&page=1"
class FreeProxyWorldScraper(Scraper):

    def __init__(self, method):
        super().__init__(method,
                         "https://www.freeproxy.world/?type="
                         "{method}&anonymity=&country=&speed=&port=&page=1")

    def get_url(self, **kwargs):
        return super().get_url(**kwargs)

    async def handle(self, response):
        soup = BeautifulSoup(response.text, "html.parser")
        proxies = set()
        table = soup.find("table", attrs={"class": "layui-table"})
        for row in table.findAll("tr"):
            count = 0
            proxy = ""
            for cell in row.findAll("td"):
                if count == 0:
                    proxy += cell.text.replace("\n", "")
                if count == 1:
                    proxy += ":"+cell.text.replace("\n", "")
                count += 1
            if proxy:
                proxies.add(proxy)
        return "\n".join(proxies)

#From "https://proxy-list.org/english/search.php?search=ssl-no&country=any&type=any&port=any&ssl=no"
class ProxyListOrgScraper(Scraper):

    def __init__(self, method):
        self.rsp = httpx.get("https://proxy-list.org/english/search.php",headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36'})
        self.pagersoup = BeautifulSoup(self.rsp , "html.parser")
        self.page_total = int(self.pagersoup.find_all('a',attrs={'class':'item'})[-1].text)
        if method == 'http':
            self.search = "ssl-no"
            self.ssl = "no"
        elif method == 'https':
            self.search = "ssl-yes"
            self.ssl = "yes"
        self.url = [f"https://proxy-list.org/english/search.php?search={self.search}&country=any&type=any&port=any&ssl={self.ssl}&p={pg}" for pg in range(1,self.page_total+1)]
        
        super().__init__(method,self.url)

    def get_url(self, **kwargs):
        return super().get_url(**kwargs)

    async def handle(self, response):
        print(f"Scraping {response.url} / {self.page_total}......")
        soup = BeautifulSoup(response.text, "html.parser")
        proxies = set()
        table = soup.find("div", attrs={"class": "table"})
        for row in table.findAll("ul"):
            count = 0
            proxy = ""
            for cell in row.findAll("li", attrs={"class": "proxy"}):
                proxy = base64.b64decode(re.findall("\\(\\'(.*)\\'\\)",str(cell))[0]).decode('utf-8')
                count += 1
            if proxy:
                proxies.add(proxy)
        # print(proxies,"From ProxyListOrgScraper ----------/////////////")
        return "\n".join(proxies)

#From "https://free.proxy-sale.com/en/https/"
class FreeProxySaleScraper(Scraper):
        
    def __init__(self, method):
        self.rsp = httpx.get("https://free.proxy-sale.com/ru/",headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36'})
        self.pagersoup = BeautifulSoup(self.rsp , "html.parser")
        self.page_total = int(self.pagersoup.find_all('button',attrs={'class':'pagination__item'})[-1].text)
        self.url = [f"https://free.proxy-sale.com/ru/?page={p}"for p in range(1,self.page_total+2)]
        super().__init__(method,self.url)

    def get_url(self, **kwargs):
        return super().get_url(**kwargs)

    async def handle(self, response):
        soup = BeautifulSoup(response.text, "html.parser")
        table = soup.find_all("div", attrs={"class": "css-ckmntm"})
        proxiess = []
        print(f"Scraping {response.url} / {self.page_total+1}......")
        for row in table:
            count = 0
            proxy = ""
            for cell in row.find_all('div'):
                async with httpx.AsyncClient(follow_redirects=True,timeout=10) as portclient:
                    if count>2:
                        break
                    elif count ==0:
                        proxy += cell.text
                    elif count==1:
                        port_image_url = response.url.scheme+"://"+response.url.host+cell.find('img').attrs['src']
                        r = await portclient.get(port_image_url)
                        img = Image.open(io.BytesIO(r.content))
                        proxy +=":"+ pytesseract.image_to_string(img)
                    count += 1
            if proxy:
                proxy = proxy.rstrip('\n')
                proxy_type = row.find('a',attrs={'class':'css-qdp10g'}).text.lower()
                if proxy_type in [self.method.lower()]:
                    proxiess.append(proxy)
            proxy = ""
                # print(proxy,"From FreeProxySaleScraper ----------/////////////")
        return "\n".join(proxiess)


scrapers = [
    SpysMeScraper("http"),
    SpysMeScraper("socks"),
    ProxyScrapeScraper("http"),
    ProxyScrapeScraper("socks4"),
    ProxyScrapeScraper("socks5"),
    GeoNodeScraper("socks"),
    ProxyListDownloadScraper("https", "elite"),
    ProxyListDownloadScraper("http", "elite"),
    ProxyListDownloadScraper("http", "transparent"),
    ProxyListDownloadScraper("http", "anonymous"),
    GeneralTableScraper("https", "http://sslproxies.org"),
    GeneralTableScraper("http", "http://free-proxy-list.net"),
    GeneralTableScraper("http", "http://us-proxy.org"),
    GeneralTableScraper("socks", "http://socks-proxy.net"),
    LunaProxyScraper("http", "https://freeproxy.lunaproxy.com/"),
    ProtoPlainResponseScraper("http", "https://raw.githubusercontent.com/proxifly/free-proxy-list/main/proxies/all/data.txt"),
    ProtoPlainResponseScraper("socks", "https://raw.githubusercontent.com/proxifly/free-proxy-list/main/proxies/all/data.txt"),
    ProtoPlainResponseScraper("http", "https://raw.githubusercontent.com/monosans/proxy-list/main/proxies/all.txt"),
    ProtoPlainResponseScraper("socks", "https://raw.githubusercontent.com/monosans/proxy-list/main/proxies/all.txt"),
    NoProtoPlainResponseScraper("http", "https://yakumo.rei.my.id/HTTP"),
    NoProtoPlainResponseScraper("socks4", "https://yakumo.rei.my.id/SOCKS4"),
    NoProtoPlainResponseScraper("socks5", "https://yakumo.rei.my.id/SOCKS5"),
    NoProtoPlainResponseScraper("http", "https://raw.githubusercontent.com/vakhov/fresh-proxy-list/master/http.txt"),
    NoProtoPlainResponseScraper("https", "https://raw.githubusercontent.com/vakhov/fresh-proxy-list/master/https.txt"),
    NoProtoPlainResponseScraper("socks4", "https://raw.githubusercontent.com/vakhov/fresh-proxy-list/master/socks4.txt"),
    NoProtoPlainResponseScraper("socks5", "https://raw.githubusercontent.com/vakhov/fresh-proxy-list/master/socks5.txt"),
    NoProtoPlainResponseScraper("http", "https://raw.githubusercontent.com/TheSpeedX/SOCKS-List/master/http.txt"),
    NoProtoPlainResponseScraper("socks4", "https://raw.githubusercontent.com/TheSpeedX/SOCKS-List/master/socks4.txt"),
    NoProtoPlainResponseScraper("socks5", "https://raw.githubusercontent.com/TheSpeedX/SOCKS-List/master/socks5.txt"),
    NoProtoPlainResponseScraper("http", "https://raw.githubusercontent.com/TheSpeedX/SOCKS-List/master/http.txt"),
    NoProtoPlainResponseScraper("socks4", "https://raw.githubusercontent.com/TheSpeedX/SOCKS-List/master/socks4.txt"),
    NoProtoPlainResponseScraper("socks5", "https://raw.githubusercontent.com/TheSpeedX/SOCKS-List/master/socks5.txt"),
    AdvanceNameScraper("http"),
    AdvanceNameScraper("https"),
    AdvanceNameScraper("socks4"),
    AdvanceNameScraper("socks5"),

    FreeProxyWorldScraper("http"),
    FreeProxyWorldScraper("https"),
    FreeProxyWorldScraper("socks4"),
    FreeProxyWorldScraper("socks5"),

    ProxyListOrgScraper("http"),
    ProxyListOrgScraper("https"),

    FreeProxySaleScraper("http"),
    FreeProxySaleScraper("https"),
    FreeProxySaleScraper("socks4"),
    FreeProxySaleScraper("socks5"),



    #"http://free-proxy.cz/en/proxylist/country/all/https/ping/all"   very slow so not implemented
    #"https://proxydb.net/?protocol=http"   uses js to render so tough so not implemented
    #"https://www.freeproxy.world/?type=https&anonymity=&country=&speed=&port=&page=1" done---- but no pagination
    #"https://proxy-list.org/english/search.php?search=ssl-no&country=any&type=any&port=any&ssl=no" done---- but no pagination
    #"https://free.proxy-sale.com/en/" done with pagination but slow
    #"https://hide.mn/en/proxy-list/"
    #"https://www.proxyrack.com/free-proxy-list/"
    #"https://www.lumiproxy.com/free-proxy/"
    #"https://proxy-tools.com/proxy"
    #"https://www.uvm.edu/~bmcelvan/docs/Free Proxy List – Fast & High Only Public Proxy Servers (IP PORT) – Hide My Ass! - Custom search #1292985.htm"
    #"https://www.experte.com/proxy-server"
    #"https://fineproxy.org/free-proxies/europe/germany/"
    #"https://premproxy.com/list/type-01.htm"
    #"https://tools.proxy-solutions.net/en/free-proxy"
    #"https://proxy-port.com/en/free-proxy-list"
    #"https://www.pyproxy.com/proxyfree/"
    #"https://www.proxydocker.com/en/proxylist/country/All"


]


def verbose_print(verbose, message):
    if verbose:
        print(message)


async def scrape(method, output, verbose):
    now = time.time()
    methods = [method]
    if method == "socks":
        methods += ["socks4", "socks5"]
    proxy_scrapers = [s for s in scrapers if s.method in methods]
    if not proxy_scrapers:
        raise ValueError("Method not supported")
    verbose_print(verbose, "Scraping proxies...")
    proxies = []

    tasks = []
    client = httpx.AsyncClient(follow_redirects=True,timeout=20)

    async def scrape_scraper(scraper):
        try:
            verbose_print(verbose, f"Looking {scraper.get_url()}...\n")
            proxies.extend(await scraper.scrape(client))
        except Exception:
            pass

    for scraper in proxy_scrapers[:]:
        tasks.append(asyncio.ensure_future(scrape_scraper(scraper)))

    await asyncio.gather(*tasks)
    await client.aclose()

    proxies = set(proxies)
    verbose_print(verbose, f"Writing {len(proxies)} proxies to file...")
    with open(output, "w") as f:
        f.write("\n".join(proxies))
    verbose_print(verbose, "Done!")
    verbose_print(verbose, f"Took {time.time() - now} seconds")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-p",
        "--proxy",
        help="Supported proxy type: " + ", ".join(sorted(set([s.method for s in scrapers]))),
        required=True,
    )
    parser.add_argument(
        "-o",
        "--output",
        help="Output file name to save .txt file",
        default="output.txt",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        help="Increase output verbosity",
        action="store_true",
    )
    # args = parser.parse_args()

    class args_():
        
        def __init__(self):
            self.proxy = 'http'
            self.output = "output.txt"
            self.verbose = True    
    
    args = args_()
    
    if sys.version_info >= (3, 7) and platform.system() == 'Windows':
        loop = asyncio.get_event_loop()
        loop.run_until_complete(scrape(args.proxy, args.output, args.verbose))
        loop.close()
    elif sys.version_info >= (3, 7):
        asyncio.run(scrape(args.proxy, args.output, args.verbose))
    else:
        loop = asyncio.get_event_loop()
        loop.run_until_complete(scrape(args.proxy, args.output, args.verbose))
        loop.close()
