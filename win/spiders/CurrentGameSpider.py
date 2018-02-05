from scrapy import Spider
from scrapy_splash import SplashRequest
from win.items import CurrentGameItem
import hashlib
import pymysql

script = """
function main(splash, args)
  assert(splash:go(args.url))
  assert(splash:wait(0.5))
  
  local bt = splash:select('.textCirBtn')
  
  bt:mouse_click()

  local get_dimensions = splash:jsfunc([[
      function () {
		var aElements=document.getElementsByTagName('li');
        var aEle=[];
        for(var i=0;i<aElements.length;i++)
        {
            if(aElements[i].getAttribute('onclick')=='clickScoreType(3)')
                aEle.push( aElements[i] );
        }
          var rect = aEle[0].getClientRects()[0];
          return {'x': rect.left, 'y': rect.top}
      }
  ]])
    splash:set_viewport_full()
    splash:wait(0.1)
    local dimensions = get_dimensions()
    -- FIXME: button must be inside a viewport
    splash:mouse_click(dimensions.x, dimensions.y)

    -- Wait split second to allow event to propagate.
    splash:wait(1)


  return {
    html = splash:html()
  }
end
"""

script1 = """
function main(splash, args)
  assert(splash:go(args.url))
  return {
    html = splash:html(),
  }
end
"""


class CurrentGameSpider(Spider):
    name = 'CurrentGameSpider'
    allowed_domains = ['m.win007.com']
    start_urls = ['http://m.win007.com/']

    game_dict = {}

    handicap_map = {
        '-4': -4.00,
        '-3.5/4': -3.75,
        '-3.5': -3.50,
        '-3/3.5': -3.25,
        '-3': -3.00,
        '-2.5/3': -2.75,
        '-2.5': -2.50,
        '-2/2.5': -2.25,
        '-2': -2.00,
        '-1.5/2': -1.75,
        '-1.5': -1.50,
        '-1/1.5': -1.25,
        '-1': -1.00,
        '-0.5/1': -0.75,
        '-0.5': -0.50,
        '-0/0.5': -0.25,
        '0': 0.00,
        '0/0.5': 0.25,
        '0.5': 0.50,
        '0.5/1': 0.75,
        '1': 1.00,
        '1/1.5': 1.25,
        '1.5': 1.50,
        '1.5/2': 1.75,
        '2': 2.00,
        '2/2.5': 2.25,
        '2.5': 2.50,
        '2.5/3': 2.75,
        '3': 3.00,
        '3/3.5': 3.25,
        '3.5': 3.50,
        '3.5/4': 3.75,
        '4': 4.00,
    }

    def start_requests(self):
        # 打开数据库连接
        db = pymysql.connect(self.settings['MYSQL_HOST'], self.settings['MYSQL_USER'], self.settings['MYSQL_PASSWD'],
                             self.settings['MYSQL_DBNAME'], use_unicode=True, charset='utf8')

        # 使用cursor()方法获取操作游标
        cursor = db.cursor()

        try:
            # 执行SQL语句
            cursor.execute("DELETE FROM current_odds")
            db.commit()

        except:
            print("Error: unable to fetch data")

        # 关闭数据库连接
        db.close()

        for url in self.start_urls:
            yield SplashRequest(url, callback=self.parse, endpoint='execute',
                                args={'lua_source': script})

    def parse(self, response):
        game_matches = response.xpath('//div[@class="match"]')

        for game_match in game_matches:
            date = game_match.xpath('.//div[@class="dateBox"]/text()').extract_first()
            if date is not None:
                match_id = game_match.xpath('@id').extract_first().split('_')[1]
                next_url = 'http://m.win007.com/asian/' + match_id + '.htm'
                self.game_dict[next_url] = {'round': date}
                yield SplashRequest(next_url, callback=self.parse2, endpoint='execute',
                                    args={'lua_source': script1})

    def parse2(self, response):
        odds_matches = response.xpath('//table[@id="hTable"]//tr')

        for odds_match in odds_matches:
            td_matches = odds_match.xpath('.//td')
            if len(td_matches) > 0:
                item = CurrentGameItem()
                item['round'] = self.game_dict[response.url]['round']
                item['companyName'] = td_matches[0].xpath('.//text()').extract_first().strip()
                item['initHostOdds'] = td_matches[1].xpath('./span')[0].xpath('./text()').extract_first().strip()
                item['initHandicap'] = self.handicap_map[
                    td_matches[1].xpath('./span')[1].xpath('./text()').extract_first().strip()]
                item['initGuestOdds'] = td_matches[1].xpath('./span')[2].xpath('./text()').extract_first().strip()
                item['wholeHostOdds'] = td_matches[2].xpath('./span')[0].xpath('./text()').extract_first().strip()
                item['wholeHandicap'] = self.handicap_map[
                    td_matches[2].xpath('./span')[1].xpath('./text()').extract_first().strip()]
                item['wholeGuestOdds'] = td_matches[2].xpath('./span')[2].xpath('./text()').extract_first().strip()
                yield item
