import scrapy
import json

class DropRateSpidier(scrapy.Spider):
    name = "droprate"
    start_urls = [
        rf"https://penguin-stats.io/PenguinStats/api/chapter/{ind}/stage"
        for ind in [0, 1, 2, 3, 4, 5]
    ]

    def parse(self, response):
        data = json.loads(response.body_as_unicode())['stages']

        for chapter_data in data:
            api_url = rf"https://penguin-stats.io/PenguinStats/api/result/stage/{chapter_data['id']}/normal"
            yield scrapy.Request(api_url, callback=self.parse_chapter)

    def parse_chapter(self, response):
        data = json.loads(response.body_as_unicode())
        yield data
