from scrapy import Item, Field


# 联赛
class LeagueItem(Item):

    # 联赛名称
    LName = Field()
    # 日期区间
    durations = Field()


class CurrentGameItem(Item):

    round = Field()
    # 博彩公司
    companyName = Field()
    # 初始主队赔率
    initHostOdds = Field()
    # 初始客队赔率
    initGuestOdds = Field()
    # 初始盘口
    initHandicap = Field()
    # 终盘主队赔率
    wholeHostOdds = Field()
    # 终盘客队赔率
    wholeGuestOdds = Field()
    # 终盘盘口
    wholeHandicap = Field()


# 比赛
class GameItem(Item):

    # 比赛id
    gameId = Field()
    # 客队
    guestTeam = Field()
    # 主队
    homeTeam = Field()
    # 比赛
    score = Field()
    # 轮数
    round = Field()
    # 日期
    date = Field()
    # 时间
    time = Field()
    # 联赛名称
    LName = Field()
    # 日期区间
    duration = Field()
    # 亚赔url
    asianUrl = Field()
    # 胜负 0:平 1:胜 3:负
    res = Field()


class AsianOddsItem(Item):

    # 比赛的id
    gameId = Field()
    # 博彩公司
    companyName = Field()
    # 初始主队赔率
    initHostOdds = Field()
    # 初始客队赔率
    initGuestOdds = Field()
    # 初始盘口
    initHandicap = Field()
    # 初始盘口中文
    initHandicapString = Field()
    # 终盘主队赔率
    wholeHostOdds = Field()
    # 终盘客队赔率
    wholeGuestOdds = Field()
    # 终盘盘口
    wholeHandicap = Field()
    # 终盘盘口中文
    wholeHandicapString = Field()

