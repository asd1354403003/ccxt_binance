import smtplib
import sys
import time
import config
import ccxt
import datetime
import pandas as pd

print('Binance')

def send_email(subject, msg):
    try:
        server = smtplib.SMTP('smtp.gmail.com:587')
        server.ehlo()
        server.starttls()
        server.login(config.EMAIL_ADDRESS, config.PASSWORD)
        message = 'Subject: {}\n\n{}'.format(subject, msg)
        server.sendmail(config.EMAIL_ADDRESS, config.EMAIL_ADDRESS, message)
        server.quit()
        print("Success: Email sent!")

    except:

        print("Email failed to send.")


def md(df, i):
    df['ma1'] = df.loc[:, 'Close'].rolling(1).mean()
    df['ma5'] = df.loc[:, 'Close'].rolling(5).mean()
#    print(df)
    gd = df.iloc[-2:, -2:]
#    print(gd)

    ticker = i + '/USDT'

    buy_money = exchange.fetch_balance()['free']['USDT']/2

    minimal_trade_number = exchange.markets[ticker]['limits']['amount']['min']
    if (gd.iloc[0, 0] < gd.iloc[0, 1] and gd.iloc[1, 0] >= gd.iloc[1, 1]):
        try:
            buy_number = buy_money / exchange.fetchTicker(ticker)['ask']

            if buy_number >= minimal_trade_number:
                if exchange.fetch_balance()['free']['USDT'] > 0:
                    try:
                        exchange.create_market_buy_order(ticker, buy_number)

                        g_c_subject = "Golden Cross"
                        g_c_msg = 'buy' + str(ticker), str(buy_number)
                        send_email(g_c_subject, g_c_msg)
                    except:
                        print(i, '??????')
                        pass
            else:
                pass
        except:
            pass
        return 'Golden Cross'

    elif gd.iloc[0, 0] > gd.iloc[0, 1] and gd.iloc[1, 0] <= gd.iloc[1, 1]:
        if i in exchange.fetch_balance()['total']:
            have_number = exchange.fetch_balance()['free'][i]
            if have_number >= minimal_trade_number:
                try:
                    exchange.create_market_sell_order(ticker, have_number)

                    g_c_subject = "Death Cross"
                    g_c_msg = 'sell' + str(ticker)
                    send_email(g_c_subject, g_c_msg)
                except:
                    print('??????')
                    pass
        return 'Death Cross'

    else:
        print('Nothing Happen')
        return 'Nothing Happen'


def check_account(exchange):
    total = exchange.fetch_balance()['total']
    total = {k: v for k, v in total.items() if v > 0}
    total_money = 0

    for i in total:
        if i != 'USDT':
            try:
                price = exchange.fetchTicker(i + '/USDT')['bid']
                money = price * total[i]
                total_money += money
            except:
                pass
        else:
            total_money += total[i]

    initial_money = 1500
    inital_date = datetime.date(2021, 12, 29)
    today = datetime.date.today()
    m = (today - inital_date).days / 365
    r = (total_money - initial_money) / initial_money
    print(r, m)
    effective_ar = (1 + r) ** m - 1
    print(effective_ar)

    say = 'Now money: ' + str(total_money) + '.  EAR: ' + str(effective_ar)
    return say


def check_md(df, first_money):
    # data = data[:100]

    df['ma1'] = df.loc[:, 'Close'].rolling(1).mean()
    df['ma5'] = df.loc[:, 'Close'].rolling(5).mean()
    sr1 = df['ma1'] < df['ma5']
    sr2 = df['ma1'] >= df['ma5']

    death_cross = df[sr1 & sr2.shift(1)].index
    golden_cross = df[-(sr1 | sr2.shift(1))].index

    money = first_money
    hold = 0
    now_situation = []

    sr1 = pd.Series(1, index=golden_cross)
    sr2 = pd.Series(0, index=death_cross)
    sr = sr1.append(sr2)
    sr = sr.sort_index()

    for i in range(0, len(sr)):
        price = df['Open'][sr.index[i]]
        if sr.iloc[i] == 1:
            buy = money / price
            hold += buy
            money -= buy * price

        else:
            money += hold * price
            hold = 0

        now_money = hold * price + money
        now_situation.append(now_money)

    return now_money - first_money


exchange = ccxt.binance()
exchange.apiKey = ""
exchange.secret = ""


while True:

    a_l = list(exchange.fetch_balance()['free'].keys())

    sys.exit()
    rank = []
    name = []
    for i in a_l:
        try:
            df = exchange.fetch_ohlcv(i + '/USDT', '15m', limit=10)
            df = pd.DataFrame(df, columns=['Timestamp', 'Open', 'High', 'Low', 'Close', 'Volume'], index=None)
            money = check_md(df, 1000)
            rank.append(money)
            name.append(i)
        except:
            pass
    d = dict(zip(name, rank))
    sort_dic = sorted(d.items(), key=lambda x: x[1], reverse=True)
    sort_dic = dict(sort_dic)
    real_dic = {k: v for k, v in sort_dic.items() if v > 0 and k[-4:] != 'DOWN'}
    asset_list = list(real_dic.keys())

    today_list = []
    for i in asset_list:
        print(i)
        df = exchange.fetch_ohlcv(i + '/USDT', '15m', limit=6)
        df = pd.DataFrame(df, columns=['Timestamp', 'Open', 'High', 'Low', 'Close', 'Volume'], index=None)
        today_list.append(md(df, i))
        print('______________________________________________')



    now = datetime.time(datetime.datetime.now().hour, datetime.datetime.now().minute)

    if now <= datetime.time(20, 0, 0) and now >= datetime.time(19, 0, 0):
        subject = "Biance Daily Move"
        msg = check_account(exchange) + '  \n' + str(dict(zip(asset_list, today_list)))
        send_email(subject, msg)

    else:
        pass
    time.sleep(15*60)
