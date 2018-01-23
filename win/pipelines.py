# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: http://doc.scrapy.org/en/latest/topics/item-pipeline.html
import pymysql
from twisted.enterprise import adbapi
from win.items import GameItem, AsianOddsItem


class WinPipeline(object):

    def __init__(self, dbpool):
        self.dbpool = dbpool

    # pipeline默认调用
    def process_item(self, item, spider):
        query = self.dbpool.runInteraction(self._conditional_insert, item)  # 调用插入的方法
        query.addErrback(self._handle_error, item, spider)  # 调用异常处理方法
        return item

    # 写入数据库中
    def _conditional_insert(self, tx, item):
        if isinstance(item, GameItem):
            sql = "insert into game_info(game_id,home_team,guest_team,score,round,date,time," \
                  "lname,duration,asian_url,finished) values(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,0)"
            params = (item["gameId"], item["homeTeam"], item["guestTeam"], item["score"],
                      item["round"], item["date"], item["time"], item["LName"], item["duration"], item["asianUrl"])
        else:
            sql = "insert into odds(game_id,company_name,init_host_odds,init_handicap," \
                  "init_handicap_string,init_guest_odds,whole_host_odds,whole_handicap," \
                  "whole_handicap_string,whole_guest_odds) values(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s);" \
                  "update game_info set finished = 1 where game_id = %s"

            params = (item["gameId"], item["companyName"], item["initHostOdds"],
                      item["initHandicap"], item["initHandicapString"], item["initGuestOdds"],
                      item["wholeHostOdds"], item["wholeHandicap"], item["wholeHandicapString"],
                      item["wholeGuestOdds"], item["gameId"])
        tx.execute(sql, params)

    @classmethod
    def from_settings(cls, settings):
        '''1、@classmethod声明一个类方法，而对于平常我们见到的则叫做实例方法。
           2、类方法的第一个参数cls（class的缩写，指这个类本身），而实例方法的第一个参数是self，表示该类的一个实例
           3、可以通过类来调用，就像C.f()，相当于java中的静态方法'''
        dbparams = dict(
            host=settings['MYSQL_HOST'],  # 读取settings中的配置
            db=settings['MYSQL_DBNAME'],
            user=settings['MYSQL_USER'],
            passwd=settings['MYSQL_PASSWD'],
            charset='utf8',  # 编码要加上，否则可能出现中文乱码问题
            cursorclass=pymysql.cursors.DictCursor,
            use_unicode=False,
        )
        dbpool = adbapi.ConnectionPool('pymysql', **dbparams)  # **表示将字典扩展为关键字参数,相当于host=xxx,db=yyy....
        return cls(dbpool)  # 相当于dbpool付给了这个类，self中可以得到`

    # 错误处理方法
    def _handle_error(self, failue, item, spider):
        print('--------------database operation exception!!-----------------')
        print('-------------------------------------------------------------')
        print(failue)
