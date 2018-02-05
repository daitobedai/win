from scrapy import Spider
from scrapy.selector import Selector
from win.items import GameItem
from scrapy_splash import SplashRequest
import hashlib
import pymysql

script = """
function main(splash, args)
  assert(splash:go(args.url))
  return {
    html = splash:html(),
  }
end
"""

script2 = """
treat = require("treat")
function main(splash, args)
    assert (splash:go(args.url))
    assert (splash:wait(0.5))

    local buttons = splash:select_all('.lsm2')

    local htmls = {}
    [onclick|="clickScoreType(3)"]
    for i, button in ipairs(buttons) do
        button: mouse_click()
        htmls[i] = splash:html()
    end
return treat.as_array(htmls)
end
"""

script3 = """
function main(splash, args)
  assert(splash:go(args.url))
  assert (splash:wait(0.5))
  return {
    html = splash:html(),
  }
end
"""


class GameSpider(Spider):
    allowed_league = {'英超', '西甲', '德甲', '法甲', '意甲', '葡超', '韩K联', '日职联', '英冠',
                      '德乙', '法乙', '荷甲', '比甲'}
    allowed_duration = {'2017-2018', '2016-2017', '2015-2016'}

    name = 'GameSpider'
    allowed_domains = ['zq.win007.com', 'vip.win007.com']
    start_urls = ['http://zq.win007.com/info/index_cn.htm']

    duration_dict = {}
    game_dict = {}
    exist_id = set()

    def start_requests(self):
        # 打开数据库连接
        db = pymysql.connect(self.settings['MYSQL_HOST'], self.settings['MYSQL_USER'], self.settings['MYSQL_PASSWD'],
                             self.settings['MYSQL_DBNAME'], use_unicode=True, charset='utf8')

        # 使用cursor()方法获取操作游标
        cursor = db.cursor()

        try:
            # 执行SQL语句
            cursor.execute("SELECT * FROM game_info")
            # 获取所有记录列表
            results = cursor.fetchall()

            for res in results:
                self.exist_id.add(res[0])

            for url in self.start_urls:
                yield SplashRequest(url, callback=self.parse, endpoint='execute',
                                    args={'lua_source': script})
        except:
            print("Error: unable to fetch data")

        # 关闭数据库连接
        db.close()

    def parse(self, response):
        country_matches = response.xpath('//div[@class="gameList"]//div[@class="divList"]')
        for country_match in country_matches:
            country_id = country_match.xpath('./@id').extract_first()

            league_matches = response.xpath(
                '//div[@id="' + country_id + 'div"]//ul[@class="div_inner_bottom_span_ul"]/li')

            for league_match in league_matches:
                league_name = ''.join(league_match.xpath('./a/text()').extract()).strip()
                if self.allowed_league.issuperset({league_name}):
                    duration_matches = league_match.xpath('./ul/li/a')
                    for duration_match in duration_matches:
                        duration = duration_match.xpath('./text()').extract_first()
                        duration_url = 'http://' + self.allowed_domains[0] + duration_match.xpath(
                            './@href').extract_first()

                        if self.allowed_duration.issuperset({duration}):
                            self.duration_dict[duration_url] = {'LName': league_name, 'duration': duration}
                            yield SplashRequest(duration_url, callback=self.parse2, endpoint='execute',
                                                args={'lua_source': script2})

    def parse2(self, response):
        duration = self.duration_dict[response.url]

        for html in response.data:
            selector = Selector(text=html)
            game_matches = selector.xpath('//div[@class="tdsolid"]//tr[@align="center"]')

            for game_match in game_matches:
                game_infos = game_match.xpath('./td')

                item = GameItem()

                item['score'] = game_infos[3].xpath('.//strong/text()').extract_first()
                if item['score'] is not None and item['score'] != '腰斩' and item['score'] != '推迟':
                    single_scores = item['score'].split('-')
                    if int(single_scores[0]) == int(single_scores[1]):
                        item['res'] = 1
                    elif int(single_scores[0]) > int(single_scores[1]):
                        item['res'] = 3
                    else:
                        item['res'] = 0
                    item['LName'] = duration['LName']
                    item['duration'] = duration['duration']
                    item['round'] = game_infos[0].xpath('./text()').extract_first()
                    item['date'] = game_infos[1].xpath('./text()').extract()[0]
                    item['time'] = game_infos[1].xpath('./text()').extract()[1]
                    item['homeTeam'] = game_infos[2].xpath('./a/text()').extract_first()
                    item['guestTeam'] = game_infos[4].xpath('./a/text()').extract_first()
                    item['asianUrl'] = game_infos[9].xpath('./a[text()="[亚]"]/@href').extract_first()

                    data = item['LName'] + item['duration'] + item['round'] + item['homeTeam'] + item['guestTeam']

                    item['gameId'] = hashlib.md5(data.encode(encoding='gb2312')).hexdigest()
                    if self.exist_id.isdisjoint({item['gameId']}):
                        yield item


