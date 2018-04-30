from datetime import date, timedelta, datetime
from flask import Blueprint, request, Response, g
import requests
import time
import simplejson as json
from urllib.parse import urlencode

from util import logger

log = logger.Logger(True, True, True)

TODAY = 0
DAY_AGO = 1
WEEK_AGO = 7
MONTH_AGO = 31
YEAR_AGO = 365

EST_HOURS_AHEAD = 3

DATE_FORMAT = '%Y-%m-%d'
DATETIME_FORMAT = '%Y-%m-%d %H:%M:%S'

stock_api = Blueprint('stock_api', __name__)


def get_attr(body, attr):
   try:
      return body[attr]
   except KeyError:
      return None


@stock_api.route('/api/stock/sell/<ticker>', methods=['POST'])
def post_sell_transaction(ticker):
   body = request.get_json()

   g.cursor.execute("SELECT shareCount, avgCost FROM PortfolioItem " +
      "WHERE portfolioId = %s AND ticker = %s",
      [body['portfolioId'], ticker])

   userShares = g.cursor.fetchone()
   if not userShares or body['shareCount'] > userShares['shareCount']:
      return Response('Inadequate shares owned to make sale.', status=400)

   saleValue = body['sharePrice'] * body['shareCount']
   newShareCt = userShares['shareCount'] - body['shareCount']

   g.cursor.execute("INSERT INTO Transaction(sharePrice, shareCount, isBuy, datetime, portfolioId, ticker, leagueId) " +
      "VALUES (%s, %s, %s, %s, %s, %s, %s)",
      [body['sharePrice'], body['shareCount'], 0, datetime.now(), body['portfolioId'], ticker, get_attr(body, 'leagueId')])

   g.cursor.execute("UPDATE Portfolio SET buyPower = buyPower + %s WHERE id = %s",
      [saleValue, body['portfolioId']])

   g.cursor.execute("UPDATE PortfolioItem SET shareCount = %s " 
      "WHERE portfolioId = %s AND ticker = %s",
      [newShareCt, body['portfolioId'], ticker])

   return Response(status=200)


@stock_api.route('/api/stock/buy/<ticker>', methods=['POST'])
def post_buy_transaction(ticker):
   body = request.get_json()

   g.cursor.execute("SELECT buyPower FROM Portfolio WHERE id = %s",
      int(body['portfolioId']))

   userBuyPower = g.cursor.fetchone()['buyPower']
   purchaseCost = body['sharePrice'] * body['shareCount']

   if userBuyPower < purchaseCost:
      return Response('Insufficient buying power to make purchase.', status=400)

   remainingBuyPower = float(userBuyPower) - purchaseCost

   g.cursor.execute("INSERT INTO Transaction(sharePrice, shareCount, isBuy, datetime, portfolioId, ticker, leagueId) " + 
      "VALUES (%s, %s, %s, %s, %s, %s, %s)",
      [body['sharePrice'], body['shareCount'], 1, datetime.now(), body['portfolioId'], ticker, get_attr(body, 'leagueId')])

   g.cursor.execute("UPDATE Portfolio SET buyPower = %s WHERE id = %s",
      [remainingBuyPower, body['portfolioId']])

   g.cursor.execute("SELECT * FROM PortfolioItem WHERE portfolioId = %s AND ticker = %s",
      [body['portfolioId'], ticker])

   portfolioItem = g.cursor.fetchone()
   if portfolioItem:
      newShareCt = portfolioItem['shareCount'] + body['shareCount']
      newAvgCost = ((portfolioItem['avgCost'] * portfolioItem['shareCount']) + purchaseCost) // newShareCt
      g.cursor.execute("UPDATE PortfolioItem SET shareCount = %s, avgCost = %s " +
         "WHERE portfolioId = %s AND ticker = %s",
         [newShareCt, newAvgCost, body['portfolioId'], ticker])
   else:
      g.cursor.execute("INSERT INTO PortfolioItem(shareCount, avgCost, portfolioId, ticker) " +
         "VALUES (%s, %s, %s, %s)",
         [body['shareCount'], body['sharePrice'], body['portfolioId'], ticker])

   return Response(status=200)


@stock_api.route('/api/stock/<ticker>/history/<length>')
def get_history(ticker, length):
   try:
      function = getFunction(length)
      outputSize = getOutputSize(length)
   except Exception as e:
      return Response('Request was formed incorrectly. ' +
         'Valid lengths are day, week, month, year.', status=400)

   interval = getInterval(length)
   apiKey = getApiKey()

   queryParams = {
      'function' : function,
      'symbol' : ticker,
      'outputsize' : outputSize,
      'apikey' : apiKey
   }

   if interval:
      queryParams['interval'] = interval

   alphaVantageApi = 'https://www.alphavantage.co/query?'
   startTime = time.time()
   raw_response = requests.get(alphaVantageApi + urlencode(queryParams))
   response = raw_response.json()
   alphaTime = time.time() - startTime

   log.info('API hitting: ' + alphaVantageApi + urlencode(queryParams))

   if response.get('Error Message'):
      return Response('Request was formed incorrectly. ' +
         'The stock ticker is either invalid or unsupported.', status=400)

   data = formatData(response, interval, length)
   parseTime = time.time() - startTime

   log.info('Alphavantage time is: ' + str(alphaTime))
   log.info('Parsing data time is: ' + str(parseTime))
   
   return json.dumps(data)
    

def getFunction(length):
   if length == 'day' or length == 'week' or length == 'now':
      return 'TIME_SERIES_INTRADAY'
   elif length == 'month' or length == 'year':
      return 'TIME_SERIES_DAILY'
   else:
      raise Exception('Invalid length provided')


def getOutputSize(length):
   if length == 'day' or length == 'month' or length == 'now':
      return 'compact'
   elif length == 'week' or length == 'year':
      return 'full'
   else:
      raise Exception('Invalid length provided') 


def getInterval(length):
   if length == 'now':
      return '1min'
   elif length == 'day':
      return '5min'
   elif length == 'week':
      return '15min'
   elif length == 'month' or length == 'year':
      return ''


def getApiKey():
   return '3UCU111LQLB5581W'


def getStartTime(timeDelta):
   today = datetime.now()
   pastDate = today - timedelta(days=timeDelta)
   startTime = pastDate.replace(hour=8)
   return startTime


def formatData(jsonData, interval, length):
   if not interval:
      interval = 'Daily'

   timeSeriesData = jsonData['Time Series (' + interval + ')']

   slicedTimeSeriesData = []

   if length == 'day':
      startTime = getStartTime(getLastWeekdayDelta())
      slicedTimeSeriesData = formatDataInRange(timeSeriesData, startTime, DATETIME_FORMAT)
   
   elif length == 'week':
      startTime = getStartTime(WEEK_AGO)
      slicedTimeSeriesData = formatDataInRange(timeSeriesData, startTime, DATETIME_FORMAT)
   
   elif length == 'month':
      startTime = getStartTime(MONTH_AGO)
      slicedTimeSeriesData = formatDataInRange(timeSeriesData, startTime, DATE_FORMAT)
   
   elif length == 'year':
      startTime = getStartTime(YEAR_AGO)
      slicedTimeSeriesData = formatDataInRange(timeSeriesData, startTime, DATE_FORMAT)
   
   elif length == 'now':
      slicedTimeSeriesData = getRecentDatum(timeSeriesData, DATETIME_FORMAT)

   else:
      raise Exception('Invalid length provided')

   return slicedTimeSeriesData


def getRecentDatum(timeSeriesData, dateFormat):
   slicedTimeSeriesData = []
   recentDatumKey = sorted(list(timeSeriesData))[-1]

   keyTime = datetime.strptime(recentDatumKey, dateFormat)
   slicedTimeSeriesData.append ({
      'time' : recentDatumKey,
      'epochTime' : keyTime.timestamp(),
      'price' : timeSeriesData[recentDatumKey]['1. open']
   })

   return slicedTimeSeriesData


def getLastWeekdayDelta():
   today = date.today()
   if date.today().weekday() <= 4:
      return TODAY
   else:
      daysAgo = 1
      dayBefore = today - timedelta(days=daysAgo)
      while dayBefore.weekday() > 4:
         daysAgo += 1
         dayBefore -= timedelta(days=daysAgo)

      return daysAgo


def formatDataInRange(timeSeriesData, startTime, dateFormat):
   slicedTimeSeriesData = []

   for (key, value) in timeSeriesData.items():
      keyTime = datetime.strptime(key, dateFormat)
      epochTimeEst = keyTime + timedelta(hours=3)

      if startTime < keyTime:
         slicedTimeSeriesData.append({
            'time' : key,
            'epochTime' : keyTime.timestamp(),
            'price' : value['1. open']
         })

   slicedTimeSeriesData.sort(key=lambda item:item['epochTime'], reverse=False)
   return slicedTimeSeriesData