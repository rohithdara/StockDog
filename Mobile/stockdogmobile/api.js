import React, { Component } from 'react';
import { AsyncStorage } from 'react-native';
import Main from './screens/main';


export default class Api {

    constructor () {
      // this.baseurl = "http://localhost:5005";
      this.baseurl = "http://198.199.100.209:5005";
      this.headers = {
         'Content-Type': 'application/json'
      }
    }
   
    createDrawers = (callback) => {
      fetch(this.baseurl + '/api/portfolio?userId=' + this.userid, {
         method: 'GET'
      }).then((response) => response.json())
      .then((responseJson) => {
         return callback({
            Portfolio: {
              screen: Main,
              navigationOptions: {
                header: null
              }
            }
          });
      })
      .catch(
         (error) => console.log(error)
      );
    };

    //--------------------------- User Mgmt Methods -------------------------//
    register = (firstname, lastname, email, password, callback) => {
      var url = this.baseurl + '/api/user';
      fetch(url, {
         method: 'POST',
         headers: {
         'Content-Type': 'application/json'
         },
         body: JSON.stringify({
         firstName: firstname,
         lastName: lastname,
         email: email,
         password: password
         })
      }).then((response) => {
         callback(email);
      })
      .catch((error) => {
         console.log(error);
      })
    };

    login = (email, password, callback) => {
      var id;
      var url = this.baseurl + '/api/login';
      fetch(url, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          email: email,
          password: password
        })
      }).then((response) => {
        return response.json();
      })
      .then((responseJson) => {
        AsyncStorage.setItem('userid', '' + responseJson.userId);
        AsyncStorage.setItem('token', responseJson.token);
        callback();
      })
      .catch((error) => {
        console.log(error);
      })
    };

    //--------------------------- Portfolio Methods -------------------------//
    getPortfolios = (callback) => {
      var uid = 1;
      AsyncStorage.getItem('userid')
        .then((userid) => {uid = userid});
      fetch(this.baseurl + '/api/portfolio?userId=' + uid, {
         method: 'GET'
      }).then((response) => response.json())
      .then((responseJson) => {
        console.log(responseJson);
        AsyncStorage.setItem('portfolios', JSON.stringify(responseJson));
        callback(responseJson);
      })
      .catch(
        (error) => console.log(error)
      );
   };

    createNewPortfolio = (pname, callback) => {
      var uid = 1;
      AsyncStorage.getItem('userid')
        .then((userid) => {uid = userid});
      fetch(this.baseurl + '/api/portfolio', {
        method: 'POST',
        headers: this.headers,
        body: JSON.stringify({
          userId: uid,
          buyPower: 600,
          name: pname
        }),
      }).then((response) => callback(response))
      .catch((error) => console.log(error));
    };

    getPortfolioStocks = (id, callback) => {
      fetch(this.baseurl + '/api/portfolio/' + id, {
        method: 'GET',
        headers: this.headers
      }).then((response) => response.json())
      .then((responseJson) => {
        callback(responseJson);
      })
      .catch((error) => console.log(error));
    };

    getPortfolioData = (callback) => {
      AsyncStorage.getItem('portfolios')
        .then((response) => {
          return JSON.parse(response);
        })
        .then((portfolios) => {
          var newXData = [];
          var newYData = [];
          var url = this.baseurl + '/api/portfolio/' + portfolios[0].id + '/history';
          fetch(url, {
            method: 'GET'
          }).then((response) => response.json())
          .then((responseJson) => {
            responseJson.forEach(element => {
              var str = element.time;
              var d = new Date(str);
              var month = d.toLocaleString("en-us", {month: "short"});
              var day = d.toLocaleString("en-us", {day: "numeric"});
              var date = month + " " + day;
              newXData.push(date);
              newYData.push(parseFloat(element.value));
            })
            callback(newXData, newYData);
          }).catch((error) => console.error(error));
        });
      
    };

    //--------------------------- Buy/Sell Stock Methods -------------------------//
    // Buys or sells a stock
    manageStock = (type, ticker, numShares, price, id, callback) => {
      fetch(this.baseurl + '/api/stock/' + type + '/' + ticker, {
        method: 'POST',
        headers: this.headers,
        body: JSON.stringify({
          shareCount: numShares,
          sharePrice: price,
          portfolioId: id
        })
      }).then((response) => callback(response))
      .catch((error) => console.log(error));
    };

    getChartData = (ticker, range, callback) => {
      var newXData = [];
      var newYData = [];
      var url = this.baseurl + '/api/stock/' + ticker + '/history/' + range;
      fetch(url, {
        method: 'GET'
      }).then((response) => response.json())
      .then((responseJson) => {
        responseJson.forEach(element => {
          var str = element.time;
          var date = "";
          if (range == 'day') {
            str = element.time.split(" ")[1];
            date = str.split(":")[0] + ":" + str.split(":")[1];
          }
          else if (range == 'week') {
            var d = new Date(str.split(" ")[0]);
            var mo = d.toLocaleString("en-us", {month: "short"});
            var day = d.toLocaleString("en-us", {day: "numeric"});
            var time = str.split(" ")[1];
            date = mo + " " + day + " " + time;
          }
          else {
            var d = new Date(element.time);
            var month = d.toLocaleString("en-us", {month: "short"});
            var day = d.toLocaleString("en-us", {day: "numeric"});
            date = month + " " + day;
          }
          newXData.push(date);
          newYData.push(parseFloat(element.price));
        })
        callback(newXData, newYData);
      }).catch((error) => console.error(error));
    };

    addToWatchlist = (ticker, callback) => {
      var portfolios = [];
      AsyncStorage.getItem('portfolios')
        .then((response) => {
          return JSON.parse(response);
        })
        .then((res) => {
          portfolios = res;
          var url = this.baseurl + '/api/watchlist';
          fetch(url, {
            method: 'POST',
            headers: this.headers,
            body: JSON.stringify({
              portfolioId: portfolios[0].id,
              ticker: ticker
            })
          }).then((response) => callback(response))
          .catch((error) => console.log(error));
        });
    };

    getWatchlistStocks = (callback) => {
      AsyncStorage.getItem('portfolios')
      .then((response) => {return JSON.parse(response);})
      .then((portfolios) => {
        var url = this.baseurl + '/api/watchlist?portfolioId=' + portfolios[0].id;
        fetch(url, {
          method: 'GET',
          headers: this.headers
        }).then((response) => response.json())
        .then((responseJson) => callback(responseJson))
        .catch((error) => console.log(error));
      });
    }

}