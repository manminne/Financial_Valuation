import yahoo_fin.stock_info as si
import pandas as pd
import requests_html
from datetime import datetime, timedelta
import time
from decimal import *
import matplotlib.pyplot as plt
import random
import numpy as np
import math

import finnhub

lukas="cool"

# Setup client
tickerlist = si.tickers_nasdaq()
jona = "sandbox_buql2av48v6s4fu1gq10"
boss = "sandbox_buo1gon48v6vd0a73mkg"
fclient = finnhub.Client(api_key=jona)

print(fclient.recommendation_trends("tsla"))

tickerlist_short = ["AACG","AACQ","AACQU","AAL"]

def number_encoder(inputstring):
    if inputstring[-1] == "K":
        return Decimal(inputstring[:-1]) * 1000

    elif inputstring[-1] == "M":
        return Decimal(inputstring[:-1]) * 1000000

    elif inputstring[-1] == "B":
        return Decimal(inputstring[:-1]) * 1000000000

    else:
        return Decimal(inputstring)


def fair_value(ticker, years=1, wish_return=0.4):
    netincome = Decimal(si.get_income_statement(ticker)[si.get_income_statement(ticker).columns[0]].netIncome)

    shares_outstanding = number_encoder(str(si.get_stats(ticker)["Value"][9]))

    current_eps = netincome / shares_outstanding

    all_growth_rates = [Decimal(x[:-1]) for x in si.get_analysts_info(ticker)["Revenue Estimate"][
                                                     si.get_analysts_info(ticker)["Revenue Estimate"].columns[
                                                     :-2]].iloc[5][1:].dropna()]

    growth_rate = sum(all_growth_rates) / len(all_growth_rates) / 100

    projected_eps = current_eps * (1 + growth_rate) ** years

    projected_pe_ratio = Decimal(si.get_live_price(ticker)) / projected_eps

    forwarded_pe_ratio = Decimal(si.get_stats_valuation(ticker)[si.get_stats_valuation(ticker).columns[1]][2]) * (
                1 + growth_rate) ** (years - 1)

    return (forwarded_pe_ratio * projected_eps) / Decimal(1 + wish_return)


def new_fair_value(ticker, exp_return=0.2):
    current_eps = Decimal(fclient.company_earnings(ticker)[0]["actual"])

    fut_eps = Decimal(fclient.company_eps_estimates(ticker, freq='annually')["data"][0]["epsAvg"])

    curr_pe = Decimal(fclient.company_basic_financials(ticker, 'all')["metric"]["peExclExtraAnnual"])

    curr_price = Decimal(fclient.quote(ticker)["c"])

    fut_pe = Decimal(fclient.company_basic_financials(ticker, 'all')["metric"]["peExclExtraTTM"])

    return (fut_pe * fut_eps) / Decimal((1 + exp_return))


def fv_estimator(ticker):
    if fclient.company_basic_financials(ticker, 'all')["metric"]["epsGrowthTTMYoy"] != None:
        eps_growth = Decimal(fclient.company_basic_financials(ticker, 'all')["metric"]["epsGrowthTTMYoy"])
    else:
        eps_growth = Decimal(0)

    if fclient.company_basic_financials(ticker, 'all')["metric"]["dividendYieldIndicatedAnnual"] != None:
        div_yield = Decimal(fclient.company_basic_financials(ticker, 'all')["metric"]["dividendYieldIndicatedAnnual"])
    else:
        div_yield = Decimal(0)
    if fclient.company_basic_financials(ticker, 'all')["metric"]["peBasicExclExtraTTM"] != None:
        pe_ratio = Decimal(fclient.company_basic_financials(ticker, 'all')["metric"]["peBasicExclExtraTTM"])
    else:
        pe_ratio = Decimal(0)

    return (eps_growth + div_yield) / pe_ratio

def fv_classify(fv_estimator):
    if fv_estimator < Decimal(1.5):
        return "Overvalued",fv_estimator
    elif fv_estimator >= Decimal(1.5) and fv_estimator < Decimal(2):
        return "Fairly priced",fv_estimator
    elif fv_estimator >= Decimal(2) and fv_estimator < Decimal(3):
        return "Undervalued",fv_estimator
    elif fv_estimator >= Decimal(3):
        return "Very undervalued",fv_estimator
    else:
        return "Valuation not possible",fv_estimator


def recommendations_past(ticker):
    try:
        stock = fclient.recommendation_trends(ticker)[22]
    except:
        return 0
    recommendations = [stock["strongBuy"], stock["buy"], stock["hold"], stock["sell"], stock["strongSell"]]
    return round(sum([x*(index+1) for index,x in enumerate(recommendations)])/sum(recommendations),4)


def recommendations(ticker):
    try:
        stock = fclient.recommendation_trends(ticker)[0]
    except:
        return 0
    recommendations = [stock["strongBuy"], stock["buy"], stock["hold"], stock["sell"], stock["strongSell"]]
    return round(sum([x*(index+1) for index,x in enumerate(recommendations)])/sum(recommendations),4)


def market_screen_past(ticker_list):
    df = pd.DataFrame()
    df["tickerlist"] = ticker_list
    grade_list = []
    past_price = []
    timestamps =[]
    current_prices = []
    for x in ticker_list:
        try:
            mytime = pd.Timestamp(fclient.recommendation_trends(x)[22]["period"])+pd.Timedelta(days=1)
            past_price.append(Decimal(si.get_data(x).where(si.get_data(x).index.to_series()== mytime).dropna()["close"]))

            grade_list.append(recommendations_past(x))
            current_prices.append(si.get_live_price(x))
            timestamps.append(mytime)
        except:
            
            timestamps.append(math.nan)
            past_price.append(math.nan)
            grade_list.append(math.nan)
            current_prices.append(math.nan)
    df["invest_grades"] = grade_list
    df["timestamps"] = timestamps
    df["past_price"] = past_price
    df["current_price"] = current_prices
    return df


def market_screen(ticker_list):
    df = pd.DataFrame()
    df["tickerlist"] = ticker_list
    grade_list = []
    for x in ticker_list:
        grade_list.append(recommendations(x))
    df["invest_grades"] = grade_list
    return df


past_ticker_table = market_screen_past(tickerlist_short)

past_ticker_table.to_csv("short_ticker_table.csv")

