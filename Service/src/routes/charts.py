from datetime import datetime
from flask import Blueprint, jsonify, make_response, request, Response, g
import requests
import simplejson as json
import time
import os

from auth import auth
from request_validator import validator
from request_validator.schemas import charts_schema
from util.error_map import errors

DAY = '1d'
MONTH = '1m'
YEAR = '1y'

IEX_DATETIME_FORMAT = '%Y-%m-%d %H:%M'
IEX_DATE_FORMAT = '%Y-%m-%d'
DATETIME_FORMAT = '%Y-%m-%d %H:%M:%S'

charts_api = Blueprint('charts_api', __name__)

URL_PREFIX = 'https://cloud.iexapis.com/v1/stock/'

CONFIG_FILE_PATH = "Service/src/routes/config.json"

def getConfigFilePath():
   cwd = os.getcwd()
   strIdx = cwd.find('StockDog/')
   return cwd[:strIdx + 9] + CONFIG_FILE_PATH

@charts_api.route('/api/charts', methods=['GET'])
@auth.login_required
@validator.validate_params(charts_schema.fields)
def extract_args():
   ticker = request.args.get('ticker')
   length = request.args.get('length')

   return get_history(ticker, length)


def get_history(ticker, length):
   interval = getInterval(length)
   try:
      configFile = open(getConfigFilePath(), 'r')
      config = json.load(configFile)
      configFile.close()
   except Exception as e:
      raise Exception('The filename was not provided or poorly formatted') 
   requestUrl = URL_PREFIX + ticker + '/chart/' + interval + '?token=' + config["TokenIEX"]
   
   g.log.info('IEX API hitting: ' + requestUrl)
   startTime = time.time()
   rawResponse = requests.get(requestUrl)
   iexTime = time.time() - startTime

   try:
      response = rawResponse.json()
   except:
      return make_response(jsonify(InvalidTicker=errors['unsupportedTicker']), 400)

   data = formatData(response, interval)
   if len(data) == 0:
      return make_response(jsonify(IEXUnavailable=errors['iexUnavailable']), 500)
   
   if length == 'recent':
      data = [data[-1]]
   
   parseTime = time.time() - startTime
   g.log.info('IEX time is: ' + str(iexTime))
   g.log.info('Parsing data time is: ' + str(parseTime))

   return json.dumps(data)


def getSharePrice(ticker):
   return json.loads(get_history(ticker, 'recent'))[0]['price']


def getInterval(length):
   if length == 'recent' or length == 'day':
      return DAY
   elif length == 'week' or length == 'month':
      return MONTH
   elif length == 'year':
      return YEAR


def formatData(jsonData, interval):
   if interval == DAY:
      return formatDataIntraday(jsonData)
   elif interval == MONTH or interval == YEAR:
      return formatDataInterDay(jsonData)

   
def formatDataInterDay(jsonData):
   data = []
   for item in jsonData:

      itemTime = datetime.strptime(item['date'], IEX_DATE_FORMAT)
      data.append({
         'time' : itemTime.strftime(DATETIME_FORMAT),
         'epochTime' : itemTime.timestamp(),
         'price' : item['open']
      })

   data.sort(key=lambda item:item['epochTime'], reverse=False)
   return data


def formatDataIntraday(jsonData):
   data = []
   NoneItemsIEX = 0 
   for item in jsonData:
      if item['average'] is None:
         continue
      if item['average'] < 0:
         continue

      itemTime = datetime.strptime(item['date'] + ' ' + item['minute'], IEX_DATETIME_FORMAT)
      data.append({
         'time' : itemTime.strftime(DATETIME_FORMAT),
         'epochTime' : itemTime.timestamp(),
         'price' : item['average']
      })
   data.sort(key=lambda item:item['epochTime'], reverse=False)
   return data