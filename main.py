# Import WSGI server from Gevent
from gevent.pywsgi import WSGIServer
# Import Compress module from Flask-Compress for compress static
# content (HTML, CSS, JS)
from flask_compress import Compress

# Import Monkey module from gevent for monkey-patching
from gevent import monkey
# Monkey-patching standart Python library for async working
monkey.patch_all()

from flask import Flask, render_template, request
import yfinance as yf
from datetime import datetime as dt

app = Flask(__name__)

# Create Compress with default params
compress = Compress()
# Init compress for our Flask app
compress.init_app(app)


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/calc', methods=['GET', 'POST'])
def calculate():
    symbol = request.form['ticker'].upper()
    ticker = yf.Ticker(symbol)
    buyTimeStr = request.form['buyDate']
    print(buyTimeStr)
    buyTime = dt.strptime(buyTimeStr, '%Y-%m-%d')

    #  Silently fail if today or the date of purchase is a weekend or holiday (no stocks available today)
    if buyTime.isoweekday() > 5:  
        return render_template('index.html', log='No stock info available for the date of purchase. Please enter a date that is a weekday and is not a holiday.')
    if dt.now().isoweekday() > 5:  
        return render_template('index.html', log='No stock info available for today. ')
    

    businessName = ticker.info['longName']

    numShares = int(request.form['shares'])
    # print(history.to_string())

    priceAtBuy = yf.download(tickers=symbol, start=buyTime,
                             period='1d')['Close'][0]
    priceNow = yf.download(tickers=symbol, start=dt.now().date(),
                           period='1d')['Close'][-1]

    # print(priceAtBuy, priceNow)

    with open('stock.txt', 'w') as f:
        f.write(str(priceAtBuy) + '\n\n\n\n' + str(priceNow))

    percentIncrease = round(((priceNow / priceAtBuy) - 1) * 100, 2)
    sellThreshold = 5
    buyThreshold = -5

    c = ''
    ud = ''
    if percentIncrease > 0:
        c = 'green'
        ud = 'gone up by'
    elif percentIncrease < 0:
        c = 'red'
        ud = 'gone down by'
    else:
        c = 'white'
        ud = 'stayed at'
        percentIncrease = priceAtBuy

    if percentIncrease > sellThreshold:
        buySell = 'SELL'
    elif percentIncrease < buyThreshold:
        buySell = 'BUY'
    else:
        buySell = ''

    change = f"Since {buyTimeStr}, {businessName} has {ud} {percentIncrease}%"

    if buySell:
        bs = f'It is a good time to {buySell} {businessName} stocks today'
    else:
        bs = f"Keep holding on to your {businessName} stocks today."

    if buySell == 'SELL':
        profitPerShare = f'\nBy selling {businessName} today, you will make ${round(priceNow - priceAtBuy, 2)} per share.'
        totalProfit = f'\nIf you sell all {numShares} of your {businessName} shares, you will make ${round((priceNow - priceAtBuy) * numShares, 2)}.'
        afterTax = f'\nAfter a tax of 10%, your final profit for selling your {businessName} shares is {round((priceNow - priceAtBuy) * numShares * 0.9, 2)}'
    else:
        profitPerShare = totalProfit = afterTax = ''

    return render_template('index.html',
                           upDown=change,
                           buySell=bs,
                           profitPerShare=profitPerShare,
                           totalProfit=totalProfit,
                           afterTax=afterTax)


http_server = WSGIServer(('0.0.0.0', 8080), app)
# Start WSGI server
http_server.serve_forever()
