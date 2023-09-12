import requests
from requests.structures import CaseInsensitiveDict
from lxml import etree
import json
import typing
from datetime import datetime, timedelta
import websocket
import time
from pyotp import TOTP

from classes.ExecutionStatusResponse import ExecutionStatusResponse
from classes.Order import Order
from classes.SearchResult import SearchResult
from classes.OrderResponse import OrderResponse
from classes.Portfolio import Portfolio
from classes.PortfolioUnderlying import PortfolioUnderlying
from classes.Trader import Trader
from classes.PriceInformation import PriceInformation

class Wikifolio:
    cookie = None
    name = None
    wikifolio_id = None
    rawData = None
    twoFA_key = None

    def __init__(self, username: str, password: str, wikifolio_name: str, twoFA_key = None) -> None:
        params = {
            "email": username,
            "password": password,
            "keepLoggedIn": True
        }
        r = requests.post(
            "https://www.wikifolio.com/api/login?country=de&language=de",
            data=params,
        )
        r.raise_for_status()
        self.cookie = r.cookies
        self.name = wikifolio_name
        self._get_wikifolio_id(wikifolio_name)
        self.twoFA_key = twoFA_key

    def _get_wikifolio_id(self, name: str) -> None:
        r = requests.get(
            "https://www.wikifolio.com/de/de/w/{}".format(name),
            cookies=self.cookie,
        )
        r.raise_for_status()
        save_text = r.text.replace ('&', '&amp;')
        html = etree.fromstring(save_text)
        # html = etree.fromstring(r.text)
        result = json.loads(html.xpath('//*[@id="__NEXT_DATA__"]/text()')[0])
        self.wikifolio_id = result["props"]["pageProps"]["data"]["wikifolio"]["id"]
        self.rawData = result

    def _get_wikifolio_key_figure(self, metric, submetric = 0, section = "kpis") -> typing.Optional[float]:
        try:
            key_figures = self.rawData["props"]["pageProps"]["data"]["keyFigures"]
            
            if metric == "totalInvestments" or metric == "tradingVolume" or metric == "liquidationFigure":
                return key_figures[metric]["ranking"]["value"]
            else:
                return key_figures[section][metric]["rankings"][submetric]["ranking"]["value"]
        except Exception as e:
            print("Error at _get_wikifolio_key_figure -> Open a issue on GitHub: " + str(e))
            return None

    def _get_wikifolio_data(self, metric):
        try:
            key_figures = self.rawData["props"]["pageProps"]["data"]["wikifolio"]
            return key_figures[metric]
        except Exception as e:
            print("Error at _get_wikifolio_data -> Open a issue on GitHub: " + str(e))
            return None

    def _get_wikifolio_universes(self, universe, subuniverse) -> typing.Optional[bool]:
        try:
            allowed = not self.rawData["props"]["pageProps"]["data"]["investmentUniverseData"]["universeGroups"][universe]["universes"][subuniverse]["isCrossedOut"]
        except Exception as e:
            print("Error at _get_wikifolio_universes -> Open a issue on GitHub: " + str(e))
            allowed = False
        return allowed

    def _get_wikifolio_master_data(self, metric):
        key_figures = self.rawData["props"]["pageProps"]["data"]["masterData"]
        try:
            if key_figures[metric] is None:
                return None
            else:
                return key_figures[metric]["value"]
        except Exception as e:
            print("Error at _get_wikifolio_master_data -> Open a issue on GitHub: " + str(e))
            return None
        
    def _get_wikifolio_certificates(self, metric):
        try:
            key_figures = self.rawData["props"]["pageProps"]["data"]["certificates"][0]
            return key_figures[metric]
        except Exception as e:
            print("Error at _get_wikifolio_certificates -> Open a issue on GitHub: " + str(e))
            return None

    @property
    def performance_since_emission(self) -> typing.Optional[float]:
        return self._get_wikifolio_key_figure(2, 1)

    @property
    def performance_ever(self) -> typing.Optional[float]:
        return self._get_wikifolio_key_figure(2, 0)

    @property
    def performance_one_year(self) -> typing.Optional[float]:
        return self._get_wikifolio_key_figure(0, 3)
    
    @property
    def volatility_one_year(self) -> typing.Optional[float]:
        return self._get_wikifolio_key_figure(0, 7)

    @property
    def performance_ytd(self) -> typing.Optional[float]:
        return self._get_wikifolio_key_figure(2, 2)

    @property
    def performance_annualized_ever(self) -> typing.Optional[float]:
        return self._get_wikifolio_key_figure(0, 0)
    
    @property
    def performance_annualized_five_years(self) -> typing.Optional[float]:
        return self._get_wikifolio_key_figure(0, 1)
    
    @property
    def performance_annualized_three_years(self) -> typing.Optional[float]:
        return self._get_wikifolio_key_figure(0, 2)
    
    @property
    def volatility_annualized_ever(self) -> typing.Optional[float]:
        return self._get_wikifolio_key_figure(0, 4)
    
    @property
    def volatility_annualized_five_years(self) -> typing.Optional[float]:
        return self._get_wikifolio_key_figure(0, 5)
    
    @property
    def volatility_annualized_three_years(self) -> typing.Optional[float]:
        return self._get_wikifolio_key_figure(0, 6)
    
    @property
    def performance_seven_days(self) -> typing.Optional[float]:
        return self._get_wikifolio_key_figure(2, 7)

    @property
    def performance_one_month(self) -> typing.Optional[float]:
        return self._get_wikifolio_key_figure(2, 6)
    
    @property
    def performance_three_months(self) -> typing.Optional[float]:
        return self._get_wikifolio_key_figure(2, 5)

    @property
    def performance_six_months(self) -> typing.Optional[float]:
        return self._get_wikifolio_key_figure(2, 4)

    @property
    def performance_intraday(self) -> typing.Optional[float]:
        return self._get_wikifolio_key_figure(2, 3)

    @property
    def max_loss_ever(self) -> typing.Optional[float]:
        return self._get_wikifolio_key_figure(0, 0, "otherKeyRiskIndicators")

    @property
    def risk_ever(self) -> typing.Optional[float]:
        return self._get_wikifolio_key_figure(0, 1, "otherKeyRiskIndicators")

    @property
    def sharp_ratio_ever(self) -> typing.Optional[float]:
        return self._get_wikifolio_key_figure(0, 2, "otherKeyRiskIndicators")
    
    @property
    def sortino_ratio_ever(self) -> typing.Optional[float]:
        return self._get_wikifolio_key_figure(0, 3, "otherKeyRiskIndicators")
    
    @property
    def max_loss_five_years(self) -> typing.Optional[float]:
        return self._get_wikifolio_key_figure(1, 0, "otherKeyRiskIndicators")

    @property
    def risk_five_years(self) -> typing.Optional[float]:
        return self._get_wikifolio_key_figure(1, 1, "otherKeyRiskIndicators")

    @property
    def sharp_ratio_five_years(self) -> typing.Optional[float]:
        return self._get_wikifolio_key_figure(1, 2, "otherKeyRiskIndicators")
    
    @property
    def sortino_ratio_five_years(self) -> typing.Optional[float]:
        return self._get_wikifolio_key_figure(1, 3, "otherKeyRiskIndicators")
    
    @property
    def max_loss_three_years(self) -> typing.Optional[float]:
        return self._get_wikifolio_key_figure(2, 0, "otherKeyRiskIndicators")

    @property
    def risk_three_years(self) -> typing.Optional[float]:
        return self._get_wikifolio_key_figure(2, 1, "otherKeyRiskIndicators")

    @property
    def sharp_ratio_three_years(self) -> typing.Optional[float]:
        return self._get_wikifolio_key_figure(2, 2, "otherKeyRiskIndicators")
    
    @property
    def sortino_ratio_three_years(self) -> typing.Optional[float]:
        return self._get_wikifolio_key_figure(2, 3, "otherKeyRiskIndicators")
    
    @property
    def max_loss_one_year(self) -> typing.Optional[float]:
        return self._get_wikifolio_key_figure(3, 0, "otherKeyRiskIndicators")

    @property
    def risk_one_year(self) -> typing.Optional[float]:
        return self._get_wikifolio_key_figure(3, 1, "otherKeyRiskIndicators")

    @property
    def sharp_ratio_one_year(self) -> typing.Optional[float]:
        return self._get_wikifolio_key_figure(3, 2, "otherKeyRiskIndicators")
    
    @property
    def sortino_ratio_one_year(self) -> typing.Optional[float]:
        return self._get_wikifolio_key_figure(3, 3, "otherKeyRiskIndicators")

    @property
    def ranking_place(self) -> typing.Optional[float]:
        return self._get_wikifolio_key_figure(1, 0)
    
    @property
    def watchlistings(self) -> typing.Optional[float]:
        return self._get_wikifolio_key_figure(1, 1)

    @property
    def total_investments(self) -> typing.Optional[float]:
        return self._get_wikifolio_key_figure("totalInvestments")

    @property
    def liquidation_figure(self) -> typing.Optional[float]:
        return self._get_wikifolio_key_figure("liquidationFigure")
    
    @property
    def trading_volume(self) -> typing.Optional[float]:
        return self._get_wikifolio_key_figure("tradingVolume")

    @property
    def id(self) -> typing.Optional[str]:
        return self._get_wikifolio_data("id")

    @property
    def full_name(self) -> typing.Optional[str]:
        return self._get_wikifolio_data("fullName")

    @property
    def short_description(self) -> typing.Optional[str]:
        return self._get_wikifolio_data("shortDescription")

    @property
    def symbol(self) -> typing.Optional[str]:
        return self._get_wikifolio_data("symbol")

    @property
    def description(self) -> typing.Optional[str]:
        return self._get_wikifolio_data("description")["content"]

    @property
    def status(self) -> typing.Optional[int]:
        return self._get_wikifolio_data("status")

    @property
    def is_on_watchlist(self) -> typing.Optional[bool]:
        return self._get_wikifolio_data("isOnWatchlist")
    
    @property
    def emission_date(self) -> typing.Optional[str]:
        return self._get_wikifolio_certificates("emissionDate")

    @property
    def chart_image_url(self) -> typing.Optional[str]:
        return self._get_wikifolio_data("chartImageUrl")

    @property
    def daily_fee(self) -> typing.Optional[float]:
        return self._get_wikifolio_data("dailyFee")

    @property
    def performance_fee(self) -> typing.Optional[float]:
        return self._get_wikifolio_data("performanceFee")

    @property
    def intended_investment(self):
        return self._get_wikifolio_data("intendedInvestment")

    @property
    def contains_leverage_products(self) -> typing.Optional[bool]:
        return self._get_wikifolio_data("containsLeverageProducts")

    @property
    def currency(self) -> typing.Optional[str]:
        return self._get_wikifolio_data("currency")

    @property
    def trader(self) -> typing.Optional[Trader]:
        return Trader(**self.rawData["props"]["pageProps"]["data"]["trader"])

    @property
    def shares_dax(self) -> typing.Optional[bool]:
        return self._get_wikifolio_universes(0,0)

    @property
    def shares_sdax(self) -> typing.Optional[bool]:
        return self._get_wikifolio_universes(0,1)

    @property
    def shares_tecdax(self) -> typing.Optional[bool]:
        return self._get_wikifolio_universes(0,2)

    @property
    def shares_other(self) -> typing.Optional[bool]:
        return self._get_wikifolio_universes(0,3)

    @property
    def shares_mdax(self) -> typing.Optional[bool]:
        return self._get_wikifolio_universes(0,4)

    @property
    def shares_europe_select(self) -> typing.Optional[bool]:
        return self._get_wikifolio_universes(1,0)

    @property
    def shares_dow_jones(self) -> typing.Optional[bool]:
        return self._get_wikifolio_universes(2,0)

    @property
    def shares_usa_select(self) -> typing.Optional[bool]:
        return self._get_wikifolio_universes(2,1)

    @property
    def shares_nasdaq_100_select(self) -> typing.Optional[bool]:
        return self._get_wikifolio_universes(2,2)

    @property
    def shares_hot_stocks(self) -> typing.Optional[bool]:
        return self._get_wikifolio_universes(3,0)

    @property
    def shares_easteurope_select(self) -> typing.Optional[bool]:
        return self._get_wikifolio_universes(4,0)

    @property
    def shares_japan_select(self) -> typing.Optional[bool]:
        return self._get_wikifolio_universes(4,1)

    @property
    def shares_international(self) -> typing.Optional[bool]:
        return self._get_wikifolio_universes(4,2)

    @property
    def etf_latin_southamerica(self) -> typing.Optional[bool]:
        return self._get_wikifolio_universes(5,0)

    @property
    def etf_emerging_markets(self) -> typing.Optional[bool]:
        return self._get_wikifolio_universes(5,1)

    @property
    def etf_coutries_of_europe(self) -> typing.Optional[bool]:
        return self._get_wikifolio_universes(5,2)

    @property
    def etf_northamerica(self) -> typing.Optional[bool]:
        return self._get_wikifolio_universes(5,3)

    @property
    def etf_other_bonds(self) -> typing.Optional[bool]:
        return self._get_wikifolio_universes(5,4)

    @property
    def etf_world(self) -> typing.Optional[bool]:
        return self._get_wikifolio_universes(5,5)

    @property
    def etf_commodities_etcs(self) -> typing.Optional[bool]:
        return self._get_wikifolio_universes(5,6)

    @property
    def etf_germany(self) -> typing.Optional[bool]:
        return self._get_wikifolio_universes(5,7)

    @property
    def etf_countries_other(self) -> typing.Optional[bool]:
        return self._get_wikifolio_universes(5,8)

    @property
    def etf_dax(self) -> typing.Optional[bool]:
        return self._get_wikifolio_universes(5,9)

    @property
    def etf_induboolies(self) -> typing.Optional[bool]:
        return self._get_wikifolio_universes(5,10)

    @property
    def etf_eurostoxx(self) -> typing.Optional[bool]:
        return self._get_wikifolio_universes(5,11)

    @property
    def etf_asia(self) -> typing.Optional[bool]:
        return self._get_wikifolio_universes(5,12)

    @property
    def etf_europe_bonds(self) -> typing.Optional[bool]:
        return self._get_wikifolio_universes(5,13)

    @property
    def etf_europe_complete(self) -> typing.Optional[bool]:
        return self._get_wikifolio_universes(5,14)

    @property
    def etf_basic_resources(self) -> typing.Optional[bool]:
        return self._get_wikifolio_universes(5,15)

    @property
    def etf_other(self) -> typing.Optional[bool]:
        return self._get_wikifolio_universes(5,16)

    @property
    def fund_properties(self) -> typing.Optional[bool]:
        return self._get_wikifolio_universes(6,0)

    @property
    def fund_bonds(self) -> typing.Optional[bool]:
        return self._get_wikifolio_universes(6,1)

    @property
    def fund_shares(self) -> typing.Optional[bool]:
        return self._get_wikifolio_universes(6,2)

    @property
    def fund_finance_market(self) -> typing.Optional[bool]:
        return self._get_wikifolio_universes(6,3)

    @property
    def fund_dab(self) -> typing.Optional[bool]:
        return self._get_wikifolio_universes(6,4)

    @property
    def fund_mix(self) -> typing.Optional[bool]:
        return self._get_wikifolio_universes(6,5)

    @property
    def discount_certificates(self) -> typing.Optional[bool]:
        return self._get_wikifolio_universes(7,0)

    @property
    def bonus_certificates(self) -> typing.Optional[bool]:
        return self._get_wikifolio_universes(7,1)

    @property
    def other_investment_certificates(self) -> typing.Optional[bool]:
        return self._get_wikifolio_universes(7,2)

    @property
    def knock_out_products(self) -> typing.Optional[bool]:
        return self._get_wikifolio_universes(8,0)

    @property
    def warrants(self) -> typing.Optional[bool]:
        return self._get_wikifolio_universes(8,1)

    @property
    def other_leverage_products(self) -> typing.Optional[bool]:
        return self._get_wikifolio_universes(8,2)

    @property
    def creation_date(self) -> typing.Optional[str]:
        return self._get_wikifolio_master_data("creationDate")

    @property
    def high_watermark(self) -> typing.Optional[str]:
        return self._get_wikifolio_master_data("highWatermark")
    
    @property
    def has_blocked_reason(self) -> typing.Optional[bool]:
        return self._get_wikifolio_certificates("hasBlockedReason")
    
    @property
    def wikifolio_security_id(self) -> typing.Optional[str]:
        return self._get_wikifolio_certificates("wikifolioSecurityId")
    
    @property
    def isin(self) -> typing.Optional[str]:
        return self._get_wikifolio_certificates("isin")
    
    @property
    def is_licensed(self) -> typing.Optional[bool]:
        return self._get_wikifolio_certificates("isLicensed")
    
    @property
    def exchange_ratio_multiplier(self) -> typing.Optional[float]:
        return self._get_wikifolio_certificates("exchangeRatioMultiplier")
    
    @property
    def wkn(self) -> typing.Optional[str]:
        return self._get_wikifolio_certificates("wkn")
    
    @property
    def is_primary(self) -> typing.Optional[bool]:
        return self._get_wikifolio_certificates("isPrimary")
    
    @property
    def is_hidden(self) -> typing.Optional[bool]:
        return self._get_wikifolio_certificates("isHidden")
    
    def get_tags(self) -> typing.List[str]:
        tags = []
        # basics
        for tag in self.rawData["props"]["pageProps"]["data"]["tagsData"]["basics"]:
            tags.append(tag["label"])
        # tradings
        for tag in self.rawData["props"]["pageProps"]["data"]["tagsData"]["tradings"]:
            tags.append(tag["label"])
        # rewards
        for tag in self.rawData["props"]["pageProps"]["data"]["tagsData"]["rewards"]:
            tags.append(tag["label"])
        return tags

    def buy_limit(
            self,
            amount: int,
            isin: str,
            limit_price: float,
            valid_until: typing.Optional[str] = None
    ) -> OrderResponse:
        if not valid_until:
            valid_until = datetime.strftime(
                datetime.now() + timedelta(days=1), "%Y-%m-%dT%X.%fZ"
            )
        
        params = {
            "amount": amount,
            "buysell": "buy",
            "limitPrice": limit_price,
            "orderType": "limit",
            "stopLossLimitPrice": "",
            "stopLossStopPrice": "",
            "stopPrice": 0,
            "takeProfitLimitPrice": "",
            "underlyingIsin": isin,
            "validUntil": valid_until,
            "wikifolioId": self.wikifolio_id,
        }
        r = requests.post(
            "https://www.wikifolio.com/api/virtualorder/placeorder",
            data=params,
            cookies=self.cookie,
        )
        r.raise_for_status()
        print(self.cookie)
        print(r.text)
        raw_json = r.json()
        return OrderResponse(**raw_json)

    def sell_limit(
            self,
            amount: int,
            isin: str,
            limit_price: float,
            valid_until: typing.Optional[str] = None
    ) -> OrderResponse:
        if not valid_until:
            valid_until = datetime.strftime(
                datetime.now() + timedelta(days=1), "%Y-%m-%dT%X.%fZ"
            )
        params = {
            "amount": amount,
            "buysell": "sell",
            "limitPrice": limit_price,
            "orderType": "limit",
            "stopLossLimitPrice": "",
            "stopLossStopPrice": "",
            "stopPrice": 0,
            "takeProfitLimitPrice": "",
            "underlyingIsin": isin,
            "validUntil": valid_until,
            "wikifolioId": self.wikifolio_id,
        }
        r = requests.post(
            "https://www.wikifolio.com/api/virtualorder/placeorder",
            data=params,
            cookies=self.cookie,
        )
        r.raise_for_status()
        raw_json = r.json()
        return OrderResponse(**raw_json)

    def trade_execution_status(self, order_uuid: str) -> ExecutionStatusResponse:
        params = {
            "order": order_uuid,
        }
        r = requests.get(
            "https://www.wikifolio.com/api/virtualorder/tradeexecutionstatus",
            params=params,
            cookies=self.cookie,
        )
        r.raise_for_status()
        raw_json = r.json()
        return ExecutionStatusResponse(**raw_json)

    def search(self, term: str) -> typing.List[SearchResult]:
        params = {
            "term": term,
            "wikifolio": self.wikifolio_id,
        }
        r = requests.post(
            "https://www.wikifolio.com/dynamic/de/de/publish/autocompleteunderlyings",
            data=params,
            cookies=self.cookie,
        )
        r.raise_for_status()
        raw_json = r.json()
        return [SearchResult(**raw_search_result) for raw_search_result in raw_json]

    def get_content(self) -> Portfolio:
        header = {
            "accept": "application/json",
        }
        params = {
            "includeportfolio": True,
            "country": "de",
            "language": "de",
        }
        r = requests.get(
            "https://www.wikifolio.com/api/chart/{}/data".format(self.wikifolio_id),
            params=params,
            headers=header,
        )
        r.raise_for_status()
        raw_json = r.json()
        portfolio = raw_json["portfolio"]
        return Portfolio(**portfolio)

    def get_trade_history(self, page: int = 0, page_size: int = 10) -> typing.List[Order]:
        header = {
            "accept": "application/json",
        }
        params = {
            "page": page,
            "pagesize": page_size,
            "country": "de",
            "language": "de",
        }
        r = requests.get(
            "https://www.wikifolio.com/api/wikifolio/{}/tradehistory".format(self.wikifolio_id),
            params=params,
            headers=header,
            cookies=self.cookie,
        )
        r.raise_for_status()
        raw_json = r.json()
        orders = raw_json["tradeHistory"]["orders"]
        return [Order(**raw_order) for raw_order in orders]

    def buy_quote(self, amount: int, isin: str) -> OrderResponse:
        i = 1
        while True:
            print(i)
            i += 1
            try:
                params = {
                    "clientProtocol": 1.5, 
                    "connectionData": [
                        {"name":"livehub"},
                        {"name":"quotehub"}
                    ],
                    "_": int(time.time() * 1000),
                }
                r = requests.get(
                    "https://www.wikifolio.com/de/de/signalr/negotiate",
                    data = params,
                    cookies = self.cookie
                )
                r.raise_for_status()
                connection_token = r.json()["ConnectionToken"]
                protocol_version = r.json()["ProtocolVersion"]

                ws = websocket.WebSocket()
                tid = 1 # random.randint(1, 10)
                socket = f'wss://www.wikifolio.com/de/de/signalr/connect?transport=webSockets&clientProtocol={protocol_version}&connectionToken={connection_token}&connectionData=%5B%7B%22name%22%3A%22livehub%22%7D%2C%7B%22name%22%3A%22quotehub%22%7D%5D&tid={tid}'
                ws.connect(socket)

                wiki_id = self.wikifolio_id
                trade_data = {
                    'H': "quotehub", 
                    'M': "GetQuote", 
                    'A': [wiki_id, isin, f"{amount}", 910], #Vorletzte Ziffer Menge; 910 Buy Order, 920 Sell Order
                    'I': 1 #Anzahl der x-Anfrage an den Server
                    }

                ws.recv_data()
                ws.send(json.dumps(trade_data))

                quoteId = ws.recv_data()
                quoteId = json.loads(quoteId[1].decode('utf-8'))['M'][0]['A'][0]['QuoteId']
                ws.close()

                if self.twoFA_key != None:
                    totp = TOTP(self.twoFA_key)
                    auth = requests.post('https://www.wikifolio.com/api/totp/verify', data = totp.now(), cookies = self.cookie)
                    cookies = auth.cookies
                else: 
                    cookies = self.cookie

                order = {
                    'amount': amount,
                    'buysell': "buy",
                    'limitPrice': "",
                    'orderType': "quote",
                    'quoteId': quoteId,
                    'stopLossLimitPrice': "",
                    'stopLossStopPrice': "",
                    'stopPrice': "",
                    'takeProfitLimitPrice': "",
                    'underlyingIsin': isin,
                    'validUntil': "",
                    'wikifolioId': wiki_id
                    }

                r = requests.post(
                    "https://www.wikifolio.com/api/virtualorder/placeorder",
                    data = order,
                    cookies = cookies
                )
                r.raise_for_status()
                return OrderResponse(**r.json())
            except:
                pass

    def sell_quote(self, amount: int, isin: str) -> OrderResponse:
        i = 1
        while True:
            print(i)
            i += 1
            try:
                params = {
                    "clientProtocol": 1.5, 
                    "connectionData": [
                        {"name":"livehub"},
                        {"name":"quotehub"}
                    ],
                    "_": int(time.time() * 1000),
                }
                r = requests.get(
                    "https://www.wikifolio.com/de/de/signalr/negotiate",
                    data = params,
                    cookies = self.cookie
                )
                r.raise_for_status()
                connection_token = r.json()["ConnectionToken"]
                protocol_version = r.json()["ProtocolVersion"]

                params = {
                    "clientProtocol": 1.5, 
                    "connectionData": [
                        {"name":"livehub"},
                        {"name":"quotehub"}
                    ],
                    "_": int(time.time() * 1000),
                    "transport": "webSockets",
                    "connectionToken": connection_token
                }
                r = requests.get(
                    "https://www.wikifolio.com/de/de/signalr/start",
                    data = params,
                    cookies = self.cookie
                )
                r.raise_for_status()

                ws = websocket.WebSocket()
                tid = 1 # random.randint(1, 10)
                socket = f'wss://www.wikifolio.com/de/de/signalr/connect?transport=webSockets&clientProtocol={protocol_version}&connectionToken={connection_token}&connectionData=%5B%7B%22name%22%3A%22livehub%22%7D%2C%7B%22name%22%3A%22quotehub%22%7D%5D&tid={tid}'
                ws.connect(socket)

                wiki_id = self.wikifolio_id
                trade_data = {
                    'H': "quotehub", 
                    'M': "GetQuote", 
                    'A': [wiki_id, isin, f"{amount}", 920], #Vorletzte Ziffer Menge; 910 Buy Order, 920 Sell Order
                    'I': 1 #Anzahl der x-Anfrage an den Server
                    }

                ws.recv_data()
                ws.send(json.dumps(trade_data))

                quoteId = ws.recv_data()
                quoteId = json.loads(quoteId[1].decode('utf-8'))['M'][0]['A'][0]['QuoteId']
                ws.close()

                if self.twoFA_key != None:
                    totp = TOTP(self.twoFA_key)
                    auth = requests.post('https://www.wikifolio.com/api/totp/verify', data = totp.now(), cookies = self.cookie)
                    cookies = auth.cookies
                else: 
                    cookies = self.cookie

                order = {
                    'amount': amount,
                    'buysell': "sell",
                    'limitPrice': "",
                    'orderType': "quote",
                    'quoteId': quoteId,
                    'stopLossLimitPrice': "",
                    'stopLossStopPrice': "",
                    'stopPrice': "",
                    'takeProfitLimitPrice': "",
                    'underlyingIsin': isin,
                    'validUntil': "",
                    'wikifolioId': wiki_id
                    }

                r = requests.post(
                    "https://www.wikifolio.com/api/virtualorder/placeorder",
                    data = order,
                    cookies = cookies
                )
                r.raise_for_status()
                return OrderResponse(**r.json())
            except:
                pass

    def get_price_information(self) -> PriceInformation:
        headers = {"Accept": "application/json"}
        params = {"country": "de", "language": "de"}
        r = requests.get(
            "https://www.wikifolio.com/api/wikifolio/{}/price".format(self.wikifolio_id),
            params = params,
            headers = headers
        )
        r.raise_for_status()
        return PriceInformation(**r.json())

    
    # ! bad style to return "False, 0" etc.
    def is_in_portfolio(self, isin: str) -> typing.Tuple[bool, int]:
        """
        Returns for a given ISIN if the asset is in the portfolio and the current value of the asset.
        """
        content = {}
        for underlying in self.get_content().underlyings:
            results = self.search(underlying.name)#[0].Isin
            for result in results:
                if isin in result.Isin:
                    _isin = result.Isin
                    content[_isin] = underlying.amount
        
        if isin in content:
            return True, content[isin]
        else:
            return False, 0

    
    # added by Quantomas
    def remove_order(self, order_uuid: str):
        params = {
            "order": order_uuid,
        }
        r = requests.post(
            "https://www.wikifolio.com/dynamic/de/de/publish/removevirtualorder",
            data=params,
            cookies=self.cookie,
        )
        r.raise_for_status()
        raw_json = r.json()
        return raw_json
