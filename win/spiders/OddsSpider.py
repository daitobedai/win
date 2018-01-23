from scrapy import Spider
from win.items import AsianOddsItem
from scrapy_splash import SplashRequest
from twisted.enterprise import adbapi
import pymysql

script = """
function main(splash, args)
  assert(splash:go(args.url))
  assert (splash:wait(0.5))
  return {
    html = splash:html(),
  }
end
"""


class OddsSpider(Spider):
    name = 'OddsSpider'
    allowed_domains = ['zq.win007.com', 'vip.win007.com']

    game_id_dict = {}

    def start_requests(self):
        # 打开数据库连接
        db = pymysql.connect(self.settings['MYSQL_HOST'], self.settings['MYSQL_USER'], self.settings['MYSQL_PASSWD'],
                             self.settings['MYSQL_DBNAME'], use_unicode=True, charset='utf8')

        # 使用cursor()方法获取操作游标
        cursor = db.cursor()

        try:
            # 执行SQL语句
            cursor.execute("SELECT * FROM game_info WHERE finished = 0")
            # 获取所有记录列表
            results = cursor.fetchall()
            for game_info in results:
                self.game_id_dict[game_info[9]] = game_info[0]
                yield SplashRequest(game_info[9], callback=self.parse, endpoint='execute',
                                    args={'lua_source': script})
        except:
            print("Error: unable to fetch data")

        # 关闭数据库连接
        db.close()

    def parse(self, response):
        items = []
        odds_matches = response.xpath('//table[@id="odds"]//tr[@bgcolor="#F5F5F5"]')

        # if not odds_matches:
        #     yield SplashRequest(response.url, callback=self.parse3, endpoint='execute',
        #                         args={'lua_source': script3})

        for odds_match in odds_matches:
            td_matches = odds_match.xpath('./td')
            company_name = td_matches[0].xpath('./text()').extract_first()
            if company_name is not None:
                item = AsianOddsItem()
                item['gameId'] = self.game_id_dict[response.url]
                item['companyName'] = company_name.strip()
                if td_matches[2].xpath('./text()').extract_first() is not None:
                    item['initHostOdds'] = td_matches[2].xpath('./text()').extract_first().strip()
                    item['initHandicap'] = td_matches[3].xpath('./@goals').extract_first()
                    item['initHandicapString'] = td_matches[3].xpath('./text()').extract_first().strip()
                    item['initGuestOdds'] = td_matches[4].xpath('./text()').extract_first().strip()
                    item['wholeHostOdds'] = td_matches[8].xpath('./text()').extract_first().strip()
                    item['wholeHandicap'] = td_matches[9].xpath('./@goals').extract_first()
                    item['wholeHandicapString'] = td_matches[9].xpath('./text()').extract_first().strip()
                    item['wholeGuestOdds'] = td_matches[10].xpath('./text()').extract_first().strip()
                    items.append(item)
                    yield item
