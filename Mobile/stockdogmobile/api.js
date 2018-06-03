import React, { Component } from 'react';
import { AsyncStorage } from 'react-native';


export default class Api {

  constructor () {
     this.baseurl = "http://localhost:5005";
    //this.baseurl = "http://198.199.100.209:5005";
    this.headers = {
        'Content-Type': 'application/json'
    }
  }

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
      callback(error);
    })
  };

  logout = (callback) => {
    AsyncStorage.getItem('userid')
      .then((userid) => {
        AsyncStorage.getItem('token')
          .then((token) => {
            console.log(userid, token);
            fetch(this.baseurl + '/api/logout', {
              method: 'DELETE',
              headers: {
                'Content-Type': 'application/json'
              },
              body: JSON.stringify({
                token: token,
                userId: userid
              })
            }).then((response) => {
              console.log('logged out.');
              AsyncStorage.removeItem('userid', () => {
                AsyncStorage.removeItem('token', () => {
                  console.log('removed items.');
                  callback();
                }); 
              });
            })
          })
      })
  }

  //--------------------------- Portfolio Methods -------------------------//
  getPortfolios = (callback) => {
    var uid;
    AsyncStorage.getItem('userid')
      .then((userid) => {
        uid = userid;
        fetch(this.baseurl + '/api/portfolio?userId=' + uid, {
          method: 'GET'
          }).then((response) => response.json())
          .then((responseJson) => {
            AsyncStorage.setItem('portfolios', JSON.stringify(responseJson));
            callback(responseJson);
          })
          .catch(
            (error) => console.log(error)
          );
      });
  };

  createNewLeague = (lname, lbuypower, lstartDate, lendDate, callback) => {
    var uid;
    AsyncStorage.getItem('userid')
      .then((userid) => {
        uid = parseInt(userid);
        bp = parseFloat(lbuypower);
        fetch(this.baseurl + '/api/league', {
          method: 'POST',
          headers: this.headers,
          body: JSON.stringify({
            ownerId: uid,
            name: lname,
            start: lstartDate,
            end: lendDate,
            startPos: bp
          })
        }).then((response) => response.json())
        .then((responseJson) => {
          callback(responseJson);
        })
        .catch((error) => console.log(error));
      });
  };

  isValidInviteCode = (inviteCode, callback) => {
    fetch(this.baseurl + '/api/league?invite=' + inviteCode, {
      method: 'GET',
      headers: this.headers,
    }).then((response) => response.json())
    .then((responseJson) => {
      var valid = responseJson.length > 0;
      if (valid) {
        callback({valid: true, league: responseJson[0]});
      }
      else {
        callback({valid: false});
      }
    })
    .catch((error) => console.log(error));
  };

  joinLeague = (pname, leagueId, code, callback) => {
    var uid;
    AsyncStorage.getItem('userid')
      .then((userid) => {
        uid = userid;
        fetch(this.baseurl + '/api/portfolio', {
          method: 'POST',
          headers: this.headers,
          body: JSON.stringify({
            userId: uid,
            buyPower: 600,  // ********************* wrong
            name: pname,
            inviteCode: code,
            leagueId: leagueId
          }),
        }).then((response) => {return response.json()})
        .then((res) => callback(res))
        .catch((error) => console.log(error));
      });
  }

  createNewPortfolio = (pname, lid, invitecode, callback) => {
    var uid;
    AsyncStorage.getItem('userid')
      .then((userid) => {
        uid = userid;
        fetch(this.baseurl + '/api/portfolio', {
          method: 'POST',
          headers: this.headers,
          body: JSON.stringify({
            userId: uid,
            buyPower: 600,
            name: pname,
            leagueId: lid,
            inviteCode: invitecode
          }),
        }).then((response) => {return response.json()})
        .then((res) => callback(res))
        .catch((error) => console.log(error));
      });
  };

  getPortfolioStocks = (id, callback) => {
    fetch(this.baseurl + '/api/portfolio/' + id, {
      method: 'GET',
      headers: this.headers
    }).then((response) => response.json())
    .then((responseJson) => {
      // if (responseJson[0].ticker === null) {
      //   callback([]);
      // }
      // else 
        callback(responseJson);
    })
    .catch((error) => console.log(error));
  };

  getPortfolioData = (callback) => {
    AsyncStorage.getItem('currPortfolio')
      .then((response) => {
        return JSON.parse(response);
      })
      .then((pid) => {
        var newXData = [];
        var newYData = [];
        var url = this.baseurl + '/api/portfolio/' + pid + '/history';
        fetch(url, {
          method: 'GET'
        }).then((response) => response.json())
        .then((responseJson) => {
          responseJson.forEach(element => {
            var str = element.datetime;
            var date = "";
            str = element.datetime.split(" ")[1];
            date = str.split(":")[0] + ":" + str.split(":")[1];
            newXData.push(date);
            newYData.push(element.value);
          })
          callback(newXData, newYData);
        }).catch((error) => console.error(error));
      });
  };

  //--------------------------- Buy/Sell Stock Methods -------------------------//
  // Buys or sells a stock
  manageStock = (type, ticker, numShares, callback) => {
    AsyncStorage.getItem('currPortfolio')
      .then((response) => {
        return JSON.parse(response);
      })
      .then((pid) => {
        fetch(this.baseurl + '/api/stock/' + type + '/' + ticker, {
          method: 'POST',
          headers: this.headers,
          body: JSON.stringify({
            shareCount: numShares,
            portfolioId: pid
          })
        }).then((response) => {
          if (response.status === 400) {
            callback({status_code: 400, message: response._bodyInit});
          }
          else {
            callback(response);
          }
        })
        .catch((error) => console.log(error));
    });
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
    AsyncStorage.getItem('currPortfolio')
      .then((response) => {
        return JSON.parse(response);
      })
      .then((pid) => {
        var url = this.baseurl + '/api/watchlist';
        fetch(url, {
          method: 'POST',
          headers: this.headers,
          body: JSON.stringify({
            portfolioId: pid,
            ticker: ticker
          })
        }).then((response) => callback(response))
        .catch((error) => console.log(error));
      });
  };

  removeFromWatchlist = (watchlistid, callback) => {
    var portfolios = [];
    AsyncStorage.getItem('currPortfolio')
      .then((response) => {
        return JSON.parse(response);
      })
      .then((pid) => {
        var url = this.baseurl + '/api/watchlist/' + watchlistid;
        fetch(url, {
          method: 'DELETE',
          headers: this.headers
        }).then((response) => callback(response))
        .catch((error) => console.log(error));
      });
  };

  getWatchlistStocks = (callback) => {
    AsyncStorage.getItem('currPortfolio')
    .then((response) => {return JSON.parse(response);})
    .then((pid) => {
      var url = this.baseurl + '/api/watchlist?portfolioId=' + pid;
      fetch(url, {
        method: 'GET',
        headers: this.headers
      }).then((response) => response.json())
      .then((responseJson) => callback(responseJson))
      .catch((error) => console.log(error));
    });
  };

  getTransactions = (callback) => {
    AsyncStorage.getItem('currPortfolio')
    .then((response) => {return JSON.parse(response);})
    .then((pid) => {
      var url = this.baseurl + '/api/portfolio/' + pid;
      fetch(url, {
        method: 'GET',
        headers: this.headers
      }).then((response) => response.json())
      .then((responseJson) => {
        if (responseJson) {
          url = this.baseurl + '/api/transaction?leagueId=' + responseJson[0].leagueId;
          fetch(url, {
            method: 'GET',
            headers: this.headers
          }).then((response) => response.json())
          .then((responseJson) => {
            callback(responseJson)
          })
          .catch((error) => console.log(error));
        }
        else {
          callback([]);
        }
      })
      .catch((error) => console.log(error));
    });
  };

  addInitialPortfolioValue = (pid, buypower, callback) => {
    var url = this.baseurl + '/api/portfolio/' + pid + '/history';
    fetch(url, {
      method: 'POST',
      headers: this.headers,
      body: JSON.stringify({
        value: buypower
      })
    }).then((response) => callback(response))
    .catch((error) => console.log(error));
  }
  
  //------------------------------- League Page ----------------------------------------//
  getLeagueMembers = (callback) => {
    AsyncStorage.getItem('currPortfolio')
    .then((response) => {return JSON.parse(response);})
    .then((pid) => {
      var url = this.baseurl + '/api/portfolio/' + pid;
      fetch(url, {
        method: 'GET',
        headers: this.headers
      }).then((response) => response.json())
      .then((responseJson) => {
        var lid = responseJson[0].leagueId;
        console.log('lid: ', lid);
        url = this.baseurl + '/api/league/' + lid + '/members';
        fetch(url, {
          method: 'GET',
          headers: this.headers
        }).then((response) => response.json())
        .then((responseJson) => {
          callback(responseJson)
        })
        .catch((error) => console.log(error));
      })
      .catch((error) => console.log(error));
    });
  };

getLeagueInfo = (callback) => {
  AsyncStorage.getItem('currPortfolio')
    .then((response) => {return JSON.parse(response);})
    .then((pid) => {
      var url = this.baseurl + '/api/portfolio/' + pid;
      fetch(url, {
        method: 'GET',
        headers: this.headers
      }).then((response) => response.json())
      .then((responseJson) => {
        var lid = responseJson[0].leagueId;
        url = this.baseurl + '/api/league/' + lid;
        fetch(url, {
          method: 'GET',
          headers: this.headers
        }).then((response) => {console.log('response: ', response); return response.json();})
        .then((responseJson) => {
          console.log('responseJson: ', responseJson);
          callback(responseJson)
        })
        .catch((error) => console.log(error));
      })
      .catch((error) => console.log(error));
    });
  }

}