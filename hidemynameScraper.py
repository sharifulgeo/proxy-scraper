import cloudscraper

scraper = cloudscraper.create_scraper()  # returns a CloudScraper instance
# Or: scraper = cloudscraper.CloudScraper()  # CloudScraper inherits from requests.Session
print(scraper.get("https://hide.mn/en/proxy-list/#list").text)  # => "<!DOCTYPE html><html><head>..."