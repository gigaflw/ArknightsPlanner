import scrapy
import re

class OfficialSpidier(scrapy.Spider):
    name = "officials"
    start_urls = [
        r'http://wiki.joyme.com/arknights/%E5%B9%B2%E5%91%98%E6%95%B0%E6%8D%AE%E8%A1%A8'
    ]

    def parse(self, response):
        hrefs = response.xpath('//tr[@data-param1]/td[2]/a')

        names = hrefs.xpath('./text()').extract()
        hrefs = hrefs.xpath('./@href').extract()

        # yield dict(zip(names, hrefs))

        for url in hrefs:
            yield scrapy.Request(response.urljoin(url), callback=self.parse_chara)

    def parse_chara(self, response):
        basic_data = self.parse_basic_data(response.xpath('//div[contains(@class, "tj-bg")]'))

        infos = response.xpath('//div[contains(@class, "tj-bgs")]')

        elite_data = self.parse_elite_data(infos[6])
        skill_upgrade_data = self.parse_skill_upgrade(infos[7])

        yield {
            **basic_data,
            '精英化': elite_data,
            '技能升级': skill_upgrade_data,
        }

    def parse_basic_data(self, data):
        eng_name, name = data[0].xpath('.//td/text()').extract()

        keys = data[1].xpath('.//table//th/text()').extract()
        vals = data[1].xpath('.//table//td/text()').extract()

        keys = [key.strip() for key in keys if key.strip()]
        vals = [val.strip() for val in vals if val.strip()]

        return dict(zip(keys, vals), name=name.strip(), eng_name=eng_name.strip())

    def parse_skill_upgrade(self, data):
        skill_upgrade = data.xpath('./table/tr/*/text()')
        skill_upgrade = [
            data.strip() for data in skill_upgrade.extract()
            if '→' in data or re.match(r'[0-9]+(、[0-9]+)*', data)
        ]

        upgrade_title = skill_upgrade[::2]
        upgrade_item_cnt = skill_upgrade[1::2]
        upgrade_items = data.xpath('.//span[contains(@class, "itemhover")]/div/a/@title').extract()

        upgrade_items_with_cnt = []
        for cnt in upgrade_item_cnt:
            cnt = cnt.split('、')
            items = upgrade_items[:len(cnt)]
            upgrade_items_with_cnt.append({
                k: v for k, v in zip(items, cnt)
            })
            upgrade_items = upgrade_items[len(cnt):]

        upgrade_data = {k: v for k, v in zip(upgrade_title, upgrade_items_with_cnt)}
        return upgrade_data

    def parse_elite_data(self, data):
        elites = {}

        for elite_level in [1, 2]:
            elite_data = data.xpath('.//tr[4]')
            if elite_level > len(elite_data):
                continue

            elite_data = elite_data[elite_level - 1]
            items = elite_data.xpath('.//a/text()').extract()
            item_cnt = elite_data.xpath('./td/text()').extract()
            item_cnt = [cnt.split('】')[1].strip() for cnt in item_cnt if '】' in cnt][1:]
            item_cnt = [int(float(cnt.strip('w')) * 10000) if cnt.endswith('w') else int(cnt) for cnt in item_cnt]
            items = dict(zip(items, item_cnt))

            elites[elite_level] = items

        return elites

