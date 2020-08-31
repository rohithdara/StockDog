from flask import Blueprint, jsonify, make_response, request, Response, g
import simplejson as json

from auth import auth
from .charts import getSharePrice
from request_validator import validator
from request_validator.schemas import transaction_schema
from util.utility import Utility
from util.error_map import errors

transaction_api = Blueprint('transaction_api', __name__)


@transaction_api.route('/api/transactions', methods=['POST'])
@auth.login_required
@validator.validate_body(transaction_schema.fields)
def post_transaction():
   body = request.get_json()
   if not auth.portfolio_belongsTo_user(body['portfolioId']):
      return Response(status=403)

   try:
      sharePrice = getSharePrice(body['ticker'])
   except TypeError:
      return make_response(jsonify(UnsupportedTicker=errors['unsupportedTicker']), 400)

   if body['action'] == 'BUY':
      return buy(sharePrice, body)
   else:
      return sell(sharePrice, body)


def buy(sharePrice, requestBody):
   g.cursor.execute("SELECT leagueId, buyPower FROM Portfolio WHERE id = %s", int(requestBody['portfolioId']))
   portfolio = g.cursor.fetchone()
   if not portfolio:
      return make_response(jsonify(NonexistentPortfolio=errors['nonexistentPortfolio']), 400)
   
   purchaseCost = sharePrice * requestBody['shareCount']
   
   if portfolio['buyPower'] < purchaseCost:
      return make_response(jsonify(InsufficientBuyPower=errors['insufficientBuyPower']), 400)
   
   remainingBuyPower = float(portfolio['buyPower']) - purchaseCost
   g.cursor.execute("INSERT INTO Transaction(sharePrice, shareCount, action, portfolioId, ticker, leagueId) " +
      "VALUES (%s, %s, %s, %s, %s, %s)",
      [sharePrice, requestBody['shareCount'], "BUY", requestBody['portfolioId'], requestBody['ticker'], portfolio['leagueId']])
   transactionId = g.cursor.lastrowid

   g.cursor.execute("UPDATE Portfolio SET buyPower = %s WHERE id = %s",
      [remainingBuyPower, requestBody['portfolioId']])
   
   g.cursor.execute("SELECT * FROM PortfolioItem WHERE portfolioId = %s AND ticker = %s",
      [requestBody['portfolioId'], requestBody['ticker']])

   portfolioItem = g.cursor.fetchone()
   if portfolioItem:
      newShareCt = portfolioItem['shareCount'] + requestBody['shareCount']
      newAvgCost = (float((portfolioItem['avgCost']) * portfolioItem['shareCount']) + purchaseCost) // newShareCt
      g.cursor.execute("UPDATE PortfolioItem SET shareCount = %s, avgCost = %s " +
         "WHERE portfolioId = %s AND ticker = %s",
         [newShareCt, newAvgCost, requestBody['portfolioId'], requestBody['ticker']])
   else:
      g.cursor.execute("INSERT INTO PortfolioItem(shareCount, avgCost, portfolioId, ticker) " +
         "VALUES (%s, %s, %s, %s)",
         [requestBody['shareCount'], sharePrice, requestBody['portfolioId'], requestBody['ticker']])

   return jsonify(id=transactionId)


def sell(sharePrice, requestBody):
   g.cursor.execute("SELECT shareCount, avgCost FROM PortfolioItem " +
      "WHERE portfolioId = %s AND ticker = %s",
      [requestBody['portfolioId'], requestBody['ticker']])
   
   userShares = g.cursor.fetchone()
   if not userShares or requestBody['shareCount'] > userShares['shareCount']:
      return make_response(jsonify(InsufficientShares=errors['insufficientShares']), 400)
   
   saleValue = sharePrice * requestBody['shareCount']
   newShareCt = userShares['shareCount'] - requestBody['shareCount']

   g.cursor.execute("SELECT leagueId FROM Portfolio WHERE id = %s",
      int(requestBody['portfolioId']))

   portfolio = g.cursor.fetchone()
   if not portfolio:
      return make_response(jsonify(NonexistentPortfolio=errors['nonexistentPortfolio']))
   
   g.cursor.execute("INSERT INTO Transaction" +
      "(sharePrice, shareCount, action, portfolioId, ticker, leagueId) " +
      "VALUES (%s, %s, %s, %s, %s, %s)",
      [sharePrice, requestBody['shareCount'], "SELL", requestBody['portfolioId'], requestBody['ticker'], portfolio['leagueId']])
   transactionId = g.cursor.lastrowid

   g.cursor.execute("UPDATE Portfolio SET buyPower = buyPower + %s WHERE id = %s",
      [saleValue, requestBody['portfolioId']]) 

   g.cursor.execute("UPDATE PortfolioItem SET shareCount = %s "
      "WHERE portfolioId = %s AND ticker = %s",
      [newShareCt, requestBody['portfolioId'], requestBody['ticker']])

   g.cursor.execute("DELETE FROM PortfolioItem WHERE shareCount = 0")

   return jsonify(id=transactionId)


@transaction_api.route('/api/transaction', methods=['GET'])
def get_transactions():
   portfolioId = request.args.get('portfolioId')
   leagueId = request.args.get('leagueId')

   if portfolioId:
      g.cursor.execute("SELECT t.id, sharePrice, shareCount, isBuy, datetime, portfolioId, " +
         "ticker, t.leagueId, p.name as nickname " +
         "FROM Transaction AS t JOIN Portfolio AS p ON t.portfolioId = p.id " +
         "WHERE t.portfolioId = %s", portfolioId)
   else:
      if leagueId:
         g.cursor.execute("SELECT t.id, sharePrice, shareCount, isBuy, datetime, portfolioId, " +
            "ticker, t.leagueId, p.name as nickname " +
            "FROM Transaction AS t JOIN Portfolio AS p ON t.portfolioId = p.id " + 
            "WHERE t.leagueId = %s", leagueId)
      else:
         g.cursor.execute("SELECT t.id, sharePrice, shareCount, isBuy, datetime, portfolioId, " +
            "ticker, t.leagueId, p.name as nickname " +
            "FROM Transaction AS t JOIN Portfolio AS p ON t.portfolioId = p.id")

   transactions = g.cursor.fetchall()
   return json.dumps(transactions, default=Utility.dateToStr)
