from scrapy import cmdline

name = 'OddsSpider'
# name = 'GameSpider'
cmd = 'scrapy crawl {0}'.format(name)
cmdline.execute(cmd.split())