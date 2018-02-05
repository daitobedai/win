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
    allowed_company = {'ManbetX', 'Crown', 'Bet365', '立博', '韦德', '易胜博', '明陞', '澳门', '10BET', '金宝博', '12bet', '利记', '盈禾',
                       '18Bet'}
    allowed_domains = ['zq.win007.com', 'vip.win007.com']

    handicap_map = {
        '受让四球': -4.00,
        '受让三球半/四球': -3.75,
        '受让三球半': -3.50,
        '受让三球/三球半': -3.25,
        '受让三球': -3.00,
        '受让两球半/三球': -2.75,
        '受让两球半': -2.50,
        '受让两球/两球半': -2.25,
        '受让两球': -2.00,
        '受让球半/两球': -1.75,
        '受让球半': -1.50,
        '受让一球/球半': -1.25,
        '受让一球': -1.00,
        '受让半球/一球': -0.75,
        '受让半球': -0.50,
        '受让平手/半球': -0.25,
        '平手': 0.00,
        '平手/半球': 0.25,
        '半球': 0.50,
        '半球/一球': 0.75,
        '一球': 1.00,
        '一球/球半': 1.25,
        '球半': 1.50,
        '球半/两球': 1.75,
        '两球': 2.00,
        '两球/两球半': 2.25,
        '两球半': 2.50,
        '两球半/三球': 2.75,
        '三球': 3.00,
        '三球/三球半': 3.25,
        '三球半': 3.50,
        '三球半/四球': 3.75,
        '四球': 4.00,
    }

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
        odds_matches = response.xpath('//table[@id="odds"]//tr')

        # if not odds_matches:
        #     yield SplashRequest(response.url, callback=self.parse3, endpoint='execute',
        #                         args={'lua_source': script3})

        for odds_match in odds_matches:
            td_matches = odds_match.xpath('./td')
            company_name = td_matches[0].xpath('./text()').extract_first()
            if company_name is not None and self.allowed_company.issuperset({company_name.strip()}):
                item = AsianOddsItem()
                item['gameId'] = self.game_id_dict[response.url]
                item['companyName'] = company_name.strip()
                if td_matches[2].xpath('./text()').extract_first() is not None:
                    item['initHostOdds'] = td_matches[2].xpath('./text()').extract_first().strip()
                    item['initHandicapString'] = td_matches[3].xpath('./text()').extract_first().strip()
                    item['initHandicap'] = self.handicap_map[item['initHandicapString']]
                    item['initGuestOdds'] = td_matches[4].xpath('./text()').extract_first().strip()
                    item['wholeHostOdds'] = td_matches[8].xpath('./text()').extract_first().strip()
                    item['wholeHandicapString'] = td_matches[9].xpath('./text()').extract_first().strip()
                    item['wholeHandicap'] = self.handicap_map[item['wholeHandicapString']]
                    item['wholeGuestOdds'] = td_matches[10].xpath('./text()').extract_first().strip()
                    items.append(item)
                    yield item
