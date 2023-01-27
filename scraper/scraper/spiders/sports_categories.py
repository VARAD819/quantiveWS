import scrapy
import json
from urllib.parse import urljoin, urlencode, urlparse
from scrapy_playwright.page import PageMethod


class SportsCategoriesSpider(scrapy.Spider):
    name = 'sports-categories'

    def start_requests(self):
        yield scrapy.Request("https://www.e.leclerc/api/rest/live-api/categories-tree-by-code/NAVIGATION_sport-loisirs?pageType=NAVIGATION", meta={
            "playwright": False,
        })

    def parse(self, response):
        data = json.loads(response.text)

        for category in data["children"]:
            base = "https://www.e.leclerc/cat/"
            category = category["code"].split("_")[1]
            params = {"page": "1", "code": "NAVIGATION_"+category}
            nexturl = urljoin(base, category) + "?" + urlencode(params)
            yield scrapy.Request(nexturl, callback=self.parse_product, meta=dict(
                playwright=True,
                playwright_page_methods=[
                    PageMethod("wait_for_selector", '.pagination-next'),
                    PageMethod("wait_for_selector", '.search-results'),
                ]
            ))

    def parse_product(self, response):
        product_selector = response.css("div.product")
        next_page_disabled = response.css(".pagination-next.disabled")
        url_components = urlparse(response.url)
        page = int(url_components.query.split("&")[0].split("=")[1])
        category = url_components.path.split("/")[-1]
        if len(next_page_disabled) > 0:
            return
        else:
            for product in product_selector:
                yield {
                    "product": product.css(".product-label ::Text").get(),
                    "price": product.css("#price ::Text").get(),
                    "category": category,
                    "page": page
                }
        params = {"page": str(page+1), "code": "NAVIGATION_"+category}
        next_url = url_components.scheme + "://" + url_components.netloc + \
            url_components.path + "?" + urlencode(params)
        yield response.follow(next_url, callback=self.parse_product, meta=dict(
            playwright=True,
            playwright_page_methods=[
                PageMethod("wait_for_selector", '.pagination-next'),
                PageMethod("wait_for_selector", '.search-results'),
            ]
        ))
