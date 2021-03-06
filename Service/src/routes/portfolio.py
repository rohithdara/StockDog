from datetime import datetime
from flask import Blueprint, request, Response, g, jsonify, make_response
import simplejson as json

from routes import charts
from auth import auth
from request_validator import validator
from request_validator.schemas import portfolio_post_schema, portfolio_get_schema
from util.utility import Utility
from util.error_map import errors

portfolio_api = Blueprint('portfolio_api', __name__)

DEFAULT_BUYPOWER = 10000

@portfolio_api.route('/api/portfolios', methods=['POST'])
@auth.login_required
@validator.validate_body(portfolio_post_schema.fields)
def post_portfolio():
   body = request.get_json()
   buyPower = body.get('buyPower') or DEFAULT_BUYPOWER

   if 'inviteCode' in body:
      return Response(status=405)
   else:
      g.cursor.execute("INSERT INTO Portfolio(name, buyPower, userId) VALUES (%s, %s, %s)",
         [body['name'], buyPower, g.user['id']])
      portfolioId = g.cursor.lastrowid

   return jsonify(id=portfolioId, buyPower=buyPower)


@portfolio_api.route('/api/portfolios', methods=['GET'])
@auth.login_required
@validator.validate_params(portfolio_get_schema.fields)
def get_portfolios():
   leagueId = request.args.get('leagueId')
   if leagueId:
      # validate that user belongs to the league
      # fetch all portfolios that belong to league
      return Response(status=405)
   
   else:
      g.cursor.execute("SELECT id, buyPower, name, userId, leagueId FROM Portfolio " + 
         "WHERE userId = %s", g.user['id'])

      portfolios = g.cursor.fetchall()
      
   for portfolio in portfolios:
      attach_portfolioItems(portfolio)
      attach_portfolio_netWorth(portfolio)

   return json.dumps(portfolios)
   

def attach_portfolioItems(portfolio):
   items = []
   g.cursor.execute("SELECT id, shareCount, avgCost, ticker FROM PortfolioItem WHERE portfolioId = %s", portfolio['id'])
   items = g.cursor.fetchall()

   portfolio['items'] = items


def attach_portfolio_netWorth(portfolio):
   netWorth = float(portfolio['buyPower'])
   for item in portfolio['items']:
         netWorth += float(charts.getSharePrice(item['ticker'])) * item['shareCount']
   
   portfolio['netWorth'] = netWorth


# @portfolio_api.route('/api/portfolio', methods=['POST'])
# def post_portfolio():
#    body = request.get_json()
#    try:
#       result = PortfolioSchema().load(body)
#    except ValidationError as err:
#       return make_response(json.dumps(err.messages), 400)

#    now = datetime.now()

#    if 'leagueId' in body:
      
#       if 'inviteCode' in body:
#          g.cursor.execute("SELECT inviteCode, startPos FROM League WHERE id = %s", body['leagueId'])
#          row = g.cursor.fetchone()

#          if row is None:
#             return make_response(jsonify(error=errors['nonexistentLeague']), 404)
         
#          if body['inviteCode'] == row['inviteCode']:
#             g.cursor.execute("INSERT INTO Portfolio(name, buyPower, userId, leagueId) VALUES (%s, %s, %s, %s)",
#                [body['name'], row['startPos'], body['userId'], body['leagueId']])
#             lastrowid = g.cursor.lastrowid

#             g.cursor.execute("INSERT INTO PortfolioHistory(portfolioId, datetime, value) VALUES (%s, %s, %s)",
#                [g.cursor.lastrowid, str(now), row['startPos']])
#          else:
#             return make_response(jsonify(error=errors['inviteCodeMismatch']), 400)
      
#       else:
#          return Response(errors['missingInviteCode'], status=400)
   
#    else:      
#       g.cursor.execute("INSERT INTO Portfolio(name, buyPower, userId) VALUES (%s, %s, %s)", 
#          [body['name'], body['buyPower'], body['userId']])
#       lastrowid = g.cursor.lastrowid

#       g.cursor.execute("INSERT INTO PortfolioHistory(portfolioId, datetime, value) VALUES (%s, %s, %s)",
#          [g.cursor.lastrowid, str(now), body['buyPower']])

#    return jsonify(id=lastrowid)

# @portfolio_api.route('/api/portfolio', methods=['GET'])
# def get_portfolios():
#    userId = request.args.get('userId')
#    leagueId = request.args.get('leagueId')

#    if userId and leagueId:
#       return make_response(jsonify(error=errors['unsupportedPortfolioGet']), 400)

#    if leagueId:
#       g.cursor.execute("SELECT p.id, p.buyPower, p.name AS nickname, p.userId, " +
#          "l.name AS league, l.id AS leagueId, l.start, l.end, l.startPos " +
#          "FROM Portfolio AS p LEFT JOIN League as l ON p.leagueId = l.id " +
#          "WHERE l.id = %s", leagueId)

#    elif userId:
#       g.cursor.execute("SELECT p.id, p.buyPower, p.name AS nickname, p.userId, " +
#          "l.name AS league, l.id AS leagueId, l.start, l.end, l.startPos " +
#          "FROM Portfolio AS p LEFT JOIN League as l ON p.leagueId = l.id " +
#          "WHERE userId = %s", userId)
#    else:
#       g.cursor.execute("SELECT p.id, p.buyPower, p.name AS nickname, p.userId, " +
#          "l.name AS league, l.id AS leagueId, l.start, l.end, l.startPos " +
#          "FROM Portfolio AS p LEFT JOIN League as l ON p.leagueId = l.id")

#    portfolios = g.cursor.fetchall()
#    portfoliosWithValues = add_portfolio_values(portfolios)

#    return json.dumps(portfoliosWithValues, default=Utility.dateToStr)


# def add_portfolio_values(portfolios):
#    for portfolio in portfolios:
#       portfolio['value'] = get_recent_portfolio_value(portfolio['id'])

#    return portfolios


# def get_recent_portfolio_value(portfolioId):
#    g.cursor.execute("SELECT * FROM PortfolioHistory " + 
#       "WHERE portfolioId = %s ORDER BY datetime DESC LIMIT 1", portfolioId)

#    portfolioValue = g.cursor.fetchone()
#    if portfolioValue:
#       return float(portfolioValue['value'])
#    else:
#       return -1


# @portfolio_api.route('/api/portfolio/<portfolioId>/history/now', methods=['GET'])
# def get_most_recent_portfolio_value(portfolioId):
#    return jsonify(value=get_recent_portfolio_value(portfolioId))


# @portfolio_api.route('/api/portfolio/<portfolioId>', methods=['GET'])
# def get_portfolio(portfolioId):
#    g.cursor.execute("SELECT p.id AS id, ticker, shareCount, avgCost, name, buyPower, leagueId " +
#       "FROM Portfolio AS p LEFT JOIN PortfolioItem as pi ON p.id = pi.portfolioId " + 
#       "WHERE p.id = %s", portfolioId)

#    portfolio = g.cursor.fetchall()
#    portfolioWithValues = add_portfolio_values(portfolio)
#    return json.dumps(portfolioWithValues)


# @portfolio_api.route('/api/portfolio/<portfolioId>/value', methods=['GET'])
# def get_portfolio_value(portfolioId):
#    portfolioItems = json.loads(get_portfolio(portfolioId))
#    value = 0
#    for item in portfolioItems:
#       if item['ticker'] is not None:
#          value += float(json.loads(stock.get_history(item['ticker'], 'now'))['price']) * item['shareCount']

#    return json.dumps({"value": value + float(portfolioItems[0]['buyPower'])})


# @portfolio_api.route('/api/portfolio/<portfolioId>/history', methods=['POST'])
# def post_portfolio_history(portfolioId):
#    body = request.get_json()
#    try:
#       result = PortfolioHistorySchema().load(body)
#    except ValidationError as err:
#       return make_response(json.dumps(err.messages), 400)
   
#    now = datetime.now()

#    g.cursor.execute("INSERT INTO PortfolioHistory(portfolioId, datetime, value) VALUES (%s, %s, %s)",
#       [portfolioId, str(now), body['value']])

#    return Response(status=200)


# @portfolio_api.route('/api/portfolio/<portfolioId>/history', methods=['GET'])
# def get_portfolio_history(portfolioId):

#    g.cursor.execute("SELECT value, datetime FROM Portfolio AS p JOIN PortfolioHistory AS ph ON p.id = ph.portfolioId " +
#       "WHERE portfolioId = %s", portfolioId)

#    portfolio = g.cursor.fetchall()
#    return json.dumps(portfolio, default=str)
