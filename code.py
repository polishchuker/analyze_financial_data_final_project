import yfinance as yf
import pandas as pd
import numpy as np
from math import log
import random
import matplotlib.pyplot as plt
import cvxopt as opt
from cvxopt import blas, solvers


'''Part 1 Import Data'''

#get ticker
aapl = yf.Ticker("AAPL")
msft = yf.Ticker("MSFT")
dis = yf.Ticker("DIS")
voo = yf.Ticker("VOO")

#get data
aapl_data =aapl.history(start="2019-01-01", end="2020-02-01")
msft_data =msft.history(start="2019-01-01", end="2020-02-01")
dis_data =dis.history(start="2019-01-01", end="2020-02-01")
voo_data =voo.history(start="2019-01-01", end="2020-02-01")

#clean data
aapl_data = pd.DataFrame(aapl_data.Close.reset_index())
msft_data = pd.DataFrame(msft_data.Close.reset_index())
dis_data = pd.DataFrame(dis_data.Close.reset_index())
voo_data = pd.DataFrame(voo_data.Close.reset_index())

# prices
aapl_prices = []
msft_prices = []
dis_prices = []
voo_prices = []


for i in range(len(aapl_data.Close)):
    aapl_prices.append(aapl_data.Close.iloc[i])


for i in range(len(msft_data.Close)):
    msft_prices.append(msft_data.Close.iloc[i])

for i in range(len(dis_data.Close)):
    dis_prices.append(dis_data.Close.iloc[i])

for i in range(len(voo_data.Close)):
    voo_prices.append(voo_data.Close.iloc[i])


# print(voo_prices)


'''Part 2 Calculate Financial Statistics'''

#calculate mean
aapl_mean = np.mean(aapl_data)
msft_mean = np.mean(aapl_data)
dis_mean = np.mean(aapl_data)
voo_mean = np.mean(aapl_data)

#calculate variance

aapl_var = np.var(aapl_data)
msft_var = np.var(msft_data)
dis_var = np.var(dis_data)
voo_var = np.var(voo_data)

#calculate std

aapl_std = np.std(aapl_data)
msft_std = np.std(msft_data)
dis_std = np.std(dis_data)
voo_std = np.std(voo_data)

#simple rate of return function not used

def simple_return(start_price, end_price, dividend = 0):
    r = (end_price - start_price +dividend) / start_price
    return r

#log return function
def calculate_log_return(start_price,end_price):
    return log(end_price / start_price)

# get returns
def get_log_returns(prices):
    returns = []
    for i in range(len(prices)):
        start_price = prices[i-1]
        end_price = prices[i]
        r = calculate_log_return(start_price,end_price)
        returns.append(r)
    return returns


#log returns

aapl_log_returns = get_log_returns(aapl_prices)
msft_log_returns = get_log_returns(msft_prices)
dis_log_returns = get_log_returns(dis_prices)
voo_log_returns = get_log_returns(voo_prices)

#print(aapl_log_returns)





#calculate correlation matrix

stock_correlations = np.corrcoef([aapl_log_returns,msft_log_returns,dis_log_returns,voo_log_returns])
# print(stock_correlations)

'''Part 3 Optimize Portfolio'''

#create dataframe

price_df = pd.DataFrame()
price_df['AAPL'] = aapl_data.Close
price_df['MSFT'] = msft_data.Close
price_df['DIS'] = dis_data.Close
price_df['VOO'] = voo_data.Close


# period returns
period_returns = price_df.pct_change()

#expected returns
expected_returns_avg = period_returns.mean()

#covariance matrix
period_cov = period_returns.cov()

#print(period_returns)
print(expected_returns_avg)
#print(period_cov)


#return portfoilio function
#The function returns a DataFrame with 5,000 portfolios of random asset weights.

def return_portfolios(expected_returns, cov_matrix):
    np.random.seed(1)
    port_returns = []
    port_volatility = []
    stock_weights = []

    selected = (expected_returns.axes)[0]

    num_assets = len(selected)
    num_portfolios = 5000

    for single_portfolio in range(num_portfolios):
        weights = np.random.random(num_assets)
        weights /= np.sum(weights)
        returns = np.dot(weights, expected_returns)
        volatility = np.sqrt(np.dot(weights.T, np.dot(cov_matrix, weights)))
        port_returns.append(returns)
        port_volatility.append(volatility)
        stock_weights.append(weights)

        portfolio = {'Returns': port_returns,
                     'Volatility': port_volatility}

    for counter, symbol in enumerate(selected):
        portfolio[symbol + ' Weight'] = [Weight[counter] for Weight in stock_weights]

    df = pd.DataFrame(portfolio)

    column_order = ['Returns', 'Volatility'] + [stock + ' Weight' for stock in selected]

    df = df[column_order]

    return df





#test return_portfolios

random_portfolios = return_portfolios(expected_returns_avg,period_cov)

# plot random_portfolios
'''
random_portfolios.plot.scatter(x = 'Volatility', y= 'Returns')
plt.xlabel('Volatility (Std. Deviation)')
plt.ylabel('Expected Returns')
plt.title('Efficient Frontier')
plt.show()
'''
#function determines optimal portfolio

def optimal_portfolio(returns):
    n = returns.shape[1]
    returns = np.transpose(returns.to_numpy()) # originally as_matrix changed to values

    N = 100
    mus = [10**(5.0 * t/N - 1.0) for t in range(N)]

    # Convert to cvxopt matrices
    S = opt.matrix(np.cov(returns))
    pbar = opt.matrix(np.mean(returns, axis=1))

    # Create constraint matrices
    G = -opt.matrix(np.eye(n))   # negative n x n identity matrix
    h = opt.matrix(0.0, (n ,1))
    A = opt.matrix(1.0, (1, n))
    b = opt.matrix(1.0)

    # Calculate efficient frontier weights using quadratic programming
    portfolios = [solvers.qp(mu*S, -pbar, G, h, A, b)['x']
                  for mu in mus]
    ## CALCULATE RISKS AND RETURNS FOR FRONTIER
    returns = [blas.dot(pbar, x) for x in portfolios]
    risks = [np.sqrt(blas.dot(x, S*x)) for x in portfolios]
    ## CALCULATE THE 2ND DEGREE POLYNOMIAL OF THE FRONTIER CURVE
    m1 = np.polyfit(returns, risks, 2)
    x1 = np.sqrt(m1[2] / m1[0])
    # CALCULATE THE OPTIMAL PORTFOLIO
    wt = solvers.qp(opt.matrix(x1 * S), -pbar, G, h, A, b)['x']
    return np.asarray(wt), returns, risks


# ploting optimal portfolio
weights,returns,risks = optimal_portfolio(period_returns[1:])

random_portfolios.plot.scatter(x='Volatility', y='Returns', fontsize=12)

plt.plot(risks, returns, 'y-o')
plt.ylabel('Expected Daily Returns',fontsize=12)
plt.xlabel('Volatility (Std. Deviation)',fontsize=12)
plt.title('Efficient Frontier', fontsize=24)
plt.show()

# Portfolio recomendation

# random portfolios generated
print(random_portfolios.head())


#find minimal and max volatitlity
min_volatility = random_portfolios.Volatility.min()
max_volatility = random_portfolios.Volatility.max()

# find min and max return
min_returns = random_portfolios.Returns.min()
max_returns = random_portfolios.Returns.max()


#calculate the portfolio with the minimal volatility
portfolio_min_volatility = [random_portfolios.iloc[[i]] for i in range(5000) if (random_portfolios.Volatility[i] == min_volatility) and (random_portfolios.Returns[i] > min_returns)]
print(len(portfolio_min_volatility))

# print the minimal volatility portfolio
if len(portfolio_min_volatility) < 6:
    print(portfolio_min_volatility)
else: print(portfolio_min_volatility.head())


#calculate the portfolio with the max return
portfolio_max_volatility = [random_portfolios.iloc[[i]] for i in range(5000) if (random_portfolios.Volatility[i] > min_volatility) and (random_portfolios.Returns[i] == max_returns)]

if len(portfolio_max_volatility) < 6:
    print(portfolio_max_volatility)
else: print(portfolio_max_volatility.head())


# calculate portfolio with volatility tolerance
print()
print(weights)
