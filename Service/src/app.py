import argparse
from util import logger

from flask import Flask, request, jsonify
from flask_cors import CORS

from user import user_api
from login import Login
from session import session_api
from stock import stock_api
from portfolio import portfolio_api
from watchlist import watchlist_api
from seed import seed_api
from nuke import nuke_api
from logout import logout_api

app = Flask(__name__)

CORS(app)

login = Login(app)
app.register_blueprint(user_api)
app.register_blueprint(login.login_api)
app.register_blueprint(session_api)
app.register_blueprint(stock_api)
app.register_blueprint(portfolio_api)
app.register_blueprint(watchlist_api)
app.register_blueprint(seed_api)
app.register_blueprint(nuke_api)
app.register_blueprint(logout_api)

log = logger.Logger(True, True, True)

@app.route('/')
@app.route('/api/v1.0')
def index():
   return "What's good StockDog!"


@app.errorhandler(404)
def not_found(error):
   return jsonify({'error': 'Not found'}), 404


def getPortNum(defaultPort=5005):
   parser = argparse.ArgumentParser()
   parser.add_argument('-p','--port', type=int, help='specify the port number')
   args = parser.parse_args()
   return args.port or defaultPort 

if __name__ == '__main__':
   app.run(debug=True, port=getPortNum(), host='0.0.0.0')
