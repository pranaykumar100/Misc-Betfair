#!/usr/bin/python

"""Simple python enabler for Betfair API.

Note this documentation is based on the documentation found at
http://bdp.betfair.com/apidocumentation.php and may be slightly out-of-date at
any time. For the most up-to-date information visit the official site.

You can run this module from the command line to exercise a number of tests. To
view help, type: python pybetfair.py --help

Copyright (C) 2006-9 Russ Gray russgray@shinyhead.me.uk

This program is free software; you can redistribute it and/or modify it under
the terms of the GNU General Public License as published by the Free Software
Foundation; either version 2 of the License, or (at your option) any later
version.

This program is distributed in the hope that it will be useful, but WITHOUT ANY
WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A
PARTICULAR PURPOSE. See the GNU General Public License for more details.

You should have received a copy of the GNU General Public License along with
this program; if not, write to the Free Software Foundation, Inc., 51 Franklin
Street, Fifth Floor, Boston, MA 02110-1301, USA.

"""
try:
    import httplib2
except ImportError:
    from httplib import HTTPConnection, HTTPSConnection
    httplib2 = None
    
from xml.dom.minidom import parseString
from time import strptime, mktime
from datetime import datetime, timedelta
from math import floor
from decimal import Decimal, negInf, Inf, NaN
#import decimal 
from gzip import GzipFile
from StringIO import StringIO
from urlparse import urljoin

_VERSION = '0.72beta'
_EXCHANGE_SOAP_NAMESPACE = 'http://www.betfair.com/publicapi/v5/BFExchangeService/'
_GLOBAL_SOAP_NAMESPACE = 'http://www.betfair.com/publicapi/v3/BFGlobalService/'

LIVE_UK_EXCHANGE_HOST = "api.betfair.com"
LIVE_AUS_EXCHANGE_HOST = "api-au.betfair.com"

def _convert_iso_time(timeStr):
    tm = strptime(timeStr[:19], "%Y-%m-%dT%H:%M:%S")
    return datetime.fromtimestamp(mktime(tm))
    
def _is_horse_race(eventTypeId):
    """Return True if the specified event type ID represents a horse race.
    
    >>> _is_horse_race(7)
    True
    >>> _is_horse_race(13)
    True
    >>> _is_horse_race(1)
    False
    >>> _is_horse_race(9999999999999999999999)
    False
    
    """
    return eventTypeId in [7, 13]
    
def _is_greyhound_race(eventTypeId):
    """Return True if the specified event type ID represents a greyhound race.
    
    >>> _is_greyhound_race(4339)
    True
    >>> _is_greyhound_race(15)
    True
    >>> _is_greyhound_race(1)
    False
    >>> _is_greyhound_race(9999999999999999999999)
    False
    
    """
    return eventTypeId in [4339, 15]

def _get_double_line_ah_selection_name(name, handicap):
    """Return a selection name including handicap annotations.
    
    Using the supplied name and handicap, works out the appropriate display
    name. Ported from code taken from Helpers.js in exchange-web source.

    >>> _get_double_line_ah_selection_name("Charlton", -1.75)
    'Charlton -1.5&-2.0'
    >>> _get_double_line_ah_selection_name("Charlton", -1.5)
    'Charlton -1.5'
    >>> _get_double_line_ah_selection_name("Charlton", -0.0)
    'Charlton -0'
    >>> _get_double_line_ah_selection_name("Charlton", 0.0)
    'Charlton -0'
    >>> _get_double_line_ah_selection_name("Charlton", 0.25)
    'Charlton +0&+0.5'
    >>> _get_double_line_ah_selection_name("Charlton", 0.5)
    'Charlton +0.5'
    
    """
    absoluteAmount = abs(handicap)
    bottomNum = floor(absoluteAmount)
    sign = handicap > 0 and '+' or '-'
    
    if absoluteAmount == bottomNum or absoluteAmount == bottomNum + 0.5:
        newAmount = sign + _round_asian_handicap(absoluteAmount)
    else:
        newAmount = "%s&%s" % \
            (sign + _round_asian_handicap(absoluteAmount - 0.25),
            sign + _round_asian_handicap(absoluteAmount + 0.25))
        
    return name + " " + newAmount
            
def _round_asian_handicap(handicap):
    """Helper function for formatting Asian Handicap runner names.
    
    Used by _get_double_line_ah_selection_name, which always passes in
    absolute (i.e. non-negative) handicap values. Based on code taken from
    Helpers.js in exchange-web source.
    
    >>> _round_asian_handicap(0)
    '0'
    >>> _round_asian_handicap(1)
    '1.0'
    >>> _round_asian_handicap(1.5)
    '1.5'
    
    """
    if handicap == 0: return '0'
    elif handicap == floor(handicap): return "%.1f" % (handicap,)
    else: return str(handicap)
    
def _format_double_line_profit(from_, to, unit):
    """Helper function for formatting Asian Handicap profit and loss data.
    
    >>> _format_double_line_profit(Decimal("-INF"), Decimal("-4"), "goal")
    'lose by more than 3 goals'
    >>> _format_double_line_profit(Decimal("-INF"), Decimal("-1"), "goal")
    'lose'
    >>> _format_double_line_profit(Decimal("-INF"), Decimal("0.0"), "goal")
    'lose or draw'
    >>> _format_double_line_profit(Decimal("-INF"), Decimal("2"), "goal")
    'do not win by 3 goals or more'
    >>> _format_double_line_profit(Decimal("0"), Decimal("INF"), "goal")
    'win or draw'
    >>> _format_double_line_profit(Decimal("1"), Decimal("INF"), "goal")
    'win'
    >>> _format_double_line_profit(Decimal("3"), Decimal("INF"), "goal")
    'win by at least 3 goals'
    >>> _format_double_line_profit(Decimal("0"), Decimal("0"), "goal")
    'draw'
    >>> _format_double_line_profit(Decimal("2"), Decimal("2"), "goal")
    'win by 2 goals'
    >>> _format_double_line_profit(Decimal("-1"), Decimal("-1"), "goal")
    'lose by 1 goal'
    
    """
    result = ""
    if from_ == negInf:
        handicap = abs(to + 1).to_integral()
        myUnit = handicap == 1 and unit or unit + "s"
        if to < 0:
            if handicap > 0:
                result = "lose by more than %i %s" % (handicap, myUnit)
            else:
                result = "lose"
        elif to == 0: result = "lose or draw"
        else: result = "do not win by %i %s or more" % (handicap, myUnit)
    elif to == Inf:
        if from_ == 0: result = "win or draw"
        elif from_ == 1: result = "win"
        else:
            handicap = abs(from_).to_integral()
            myUnit = handicap == 1 and unit or unit + "s"
            result = "win by at least %i %s" % (handicap, myUnit)
    elif from_ == to:
        handicap = abs(to).to_integral()
        myUnit = handicap == 1 and unit or unit + "s"
        if from_ == 0: result = "draw"
        elif from_ > 0: result = "win by %i %s" % (handicap, myUnit)
        elif from_ < 0: result = "lose by %i %s" % (handicap, myUnit)
    
    return result
    
    
class HttpHelper:
    def __init__(self, debuglevel=0, hostname='api.betfair.com', secure=True,
                compressed=False):
        self.debuglevel = debuglevel
        self.hostname = hostname
        self.secure = secure
        self.compressed = compressed
        
        # if we have httplib2, we want to take advantage of HTTP persistence
        # so we create a connection object to reuse. If we don't have httplib2
        # we'll just create a new connection each time (painful)
        if httplib2:
            httplib2.debuglevel = debuglevel
            self.conn = None
        
    def makeRequest(self, url, envelope, action):
        """Post specified SOAP envelope to Betfair.
        
        Creates an HTTP(S) connection to the configured hostname and
        performs an HTTP POST to submit the envelope. Returns the server
        response parsed into an xml doc.
        
        env    -- the SOAP envelope to post
        action -- the SOAP action being performed
        
        """
        # headers
        headers = {
            'Content-Type':'text/xml',
            'SOAPAction':'urn:%s' % (action,),
            'User-Agent':'pybetfair/%s' % (_VERSION,),
        }
        if self.compressed: headers['Accept-Encoding'] = 'gzip, deflate'
        
        # create connection (secure if necessary)
        if httplib2:
            if not self.conn: self.conn = httplib2.Http()
            requestUrl = urljoin((self.secure and "https://" or "http://") +
                                                            self.hostname, url)
            resp, responseBody = self.conn.request(requestUrl, "POST", 
                                                            envelope, headers)
        else:
            conn = self.secure and HTTPSConnection(self.hostname) or \
                                    HTTPConnection(self.hostname)
            conn.debuglevel = self.debuglevel
            
            # post the envelope
            conn.request("POST", url, envelope, headers)
            
            # parse and return the server response, and close the connection
            response = conn.getresponse()
            responseBody = response.read()
    
            # decompress if necessary
            if response.getheader('Content-Encoding') == "gzip":
                compressedStream = StringIO(responseBody)
                gzipper = GzipFile(fileobj=compressedStream)
                responseBody = gzipper.read()
                
            conn.close()
                
        # create XML doc from response string
        if self.debuglevel > 2: print responseBody
        x = parseString(responseBody)
        return x
    
class BFGlobalService:
    
    """Proxy class for the Betfair Global API.
    
    This class provides a simple proxy that wraps the Betfair API global
    services. The global API provides services that are not specific to
    a particular exchange, such as retrieving account funds or profile info.
    
    """
    
    def __init__(self, debuglevel=0, hostname='api.betfair.com',
                url='/global/v3/BFGlobalService', secure=True, 
                compressed=False):
                    
        # connection info
        self.http_helper = HttpHelper(debuglevel, hostname, secure, compressed)
        self.url = url
        
        # SOAP request envelopes
        self._getActiveEventTypesEnvelope = '''
            <SOAP-ENV:Envelope 
            xmlns:SOAP-ENV="http://schemas.xmlsoap.org/soap/envelope/" 
            xmlns:SOAP-ENC="http://schemas.xmlsoap.org/soap/encoding/" 
            xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" 
            xmlns:xsd="http://www.w3.org/2001/XMLSchema">
                <SOAP-ENV:Body>
                    <m:getActiveEventTypes xmlns:m="%s">
                        <m:request>
                            <header>
                                <clientStamp>0</clientStamp>
                                <sessionToken>%s</sessionToken>
                            </header>
                            <locale>%s</locale>
                        </m:request>
                    </m:getActiveEventTypes>
                </SOAP-ENV:Body>
            </SOAP-ENV:Envelope>'''

        self._getEventsEnvelope = '''
            <SOAP-ENV:Envelope 
            xmlns:SOAP-ENV="http://schemas.xmlsoap.org/soap/envelope/" 
            xmlns:SOAP-ENC="http://schemas.xmlsoap.org/soap/encoding/" 
            xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" 
            xmlns:xsd="http://www.w3.org/2001/XMLSchema">
                <SOAP-ENV:Body>
                    <m:getEvents xmlns:m="%s">
                        <m:request>
                            <header>
                                <clientStamp>0</clientStamp>
                                <sessionToken>%s</sessionToken>
                            </header>
                            <eventParentId>%i</eventParentId>
                            <locale>%s</locale>
                        </m:request>
                    </m:getEvents>
                </SOAP-ENV:Body>
            </SOAP-ENV:Envelope>'''
        
        self._keepAliveEnvelope = '''
            <SOAP-ENV:Envelope 
            xmlns:SOAP-ENV="http://schemas.xmlsoap.org/soap/envelope/" 
            xmlns:SOAP-ENC="http://schemas.xmlsoap.org/soap/encoding/" 
            xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" 
            xmlns:xsd="http://www.w3.org/2001/XMLSchema">
                <SOAP-ENV:Body>
                    <m:keepAlive xmlns:m="%s">
                        <m:request>
                            <header>
                                <clientStamp>0</clientStamp>
                                <sessionToken>%s</sessionToken>
                            </header>
                        </m:request>
                    </m:keepAlive>
                </SOAP-ENV:Body>
            </SOAP-ENV:Envelope>'''

        self._loginEnvelope = '''
            <SOAP-ENV:Envelope 
            xmlns:SOAP-ENV="http://schemas.xmlsoap.org/soap/envelope/" 
            xmlns:SOAP-ENC="http://schemas.xmlsoap.org/soap/encoding/" 
            xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" 
            xmlns:xsd="http://www.w3.org/2001/XMLSchema">
                <SOAP-ENV:Body>
                    <m:login xmlns:m="%s">
                        <m:request>
                            <locationId>0</locationId>
                            <password>%s</password>
                            <productId>%i</productId>
                            <username>%s</username>
                            <vendorSoftwareId>0</vendorSoftwareId>
                        </m:request>
                    </m:login>
                </SOAP-ENV:Body>
            </SOAP-ENV:Envelope>'''

        self._getSubscriptionInfoEnvelope = '''
            <SOAP-ENV:Envelope 
            xmlns:SOAP-ENV="http://schemas.xmlsoap.org/soap/envelope/" 
            xmlns:SOAP-ENC="http://schemas.xmlsoap.org/soap/encoding/" 
            xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" 
            xmlns:xsd="http://www.w3.org/2001/XMLSchema">
                <SOAP-ENV:Body>
                    <m:getSubscriptionInfo xmlns:m="%s">
                        <m:request>
                            <header>
                                <clientStamp>0</clientStamp>
                                <sessionToken>%s</sessionToken>
                            </header>
                        </m:request>
                    </m:getSubscriptionInfo>
                </SOAP-ENV:Body>
            </SOAP-ENV:Envelope>'''

    def getActiveEventTypes(self, sessionToken, locale="en_GB"):
        """Retrieve all sports which have at least one associated active or 
        suspended market.
        
        Performs a getActiveEventTypes call against the Betfair API, and returns
        a GetEventTypesResp object. Event types form the top level of the
        Betfair event hierarchy, e.g. Soccer, Horse Racing, etc.
        
        sessionToken -- session identifier
        locale       -- controls the output language (default en_GB)
        
        """
        # configure the template envelope and make the request
        env = self._getActiveEventTypesEnvelope % (_EXCHANGE_SOAP_NAMESPACE, 
                                                   sessionToken, 
                                                   locale)
        response = self.http_helper.makeRequest(self.url, env, 
                                                'getActiveEventTypes')
        return GetEventTypesResp(response)

    def getEvents(self, sessionToken, eventParentId, locale="en_GB"):
        """Retrieve all events or markets which have the input event id as a parent.
        
        Performs a getEvents call against the Betfair API, and returns a
        GetEventsResp object.
        
        sessionToken  -- session identifier
        eventParentId -- either an event ID or a event type (sport) ID
        locale        -- controls the output language (default en_GB)
        
        """
        # configure the template envelope and make the request
        env = self._getEventsEnvelope % (_EXCHANGE_SOAP_NAMESPACE,
                                         sessionToken,
                                         eventParentId,
                                         locale)
        response = self.http_helper.makeRequest(self.url, env, 
                                                'getEvents')
        return GetEventsResp(response)

    def keepAlive(self, sessionToken):
        """Sends a heartbeat to prevent a login session expiring.
        
        Performs a keepAlive call against the Betfair API, and returns a
        KeepAliveResp object.
        
        sessionToken -- session identifier
        
        """
        # configure the template envelope and make the request
        env = self._keepAliveEnvelope % (_EXCHANGE_SOAP_NAMESPACE, sessionToken,)
        response = self.http_helper.makeRequest(self.url, env, 
                                                'keepAlive')
        return KeepAliveResp(response)
        
    def login(self, username, password, productId=82):
        """Logs in to the API service and initiates a secure session for the 
        user. 
        
        Performs a login call against the Betfair API, and returns a LoginResp
        object. Users can have multiple sessions 'alive' at any point in time.
        
        username  -- account username
        password  -- account password
        productId -- the API product ID with which to login to the API for a 
                     new session. This is provided when you sign up
        """
        # configure the template envelope and make the request
        env = self._loginEnvelope % (_EXCHANGE_SOAP_NAMESPACE,
                                     password,
                                     productId,
                                     username)
        response = self.http_helper.makeRequest(self.url, env, 
                                                'login')
        return LoginResp(response)

    def getSubscriptionInfo(self, sessionToken):
        """Retrieves information on your API subscription.
        
        Performs a getSubscriptionInfo call against the Betfair API, and returns
        a GetSubscriptionInfoResp object.
        
        sessionToken -- session identifier
        
        """
        # configure the template envelope and make the request
        env = self._getSubscriptionInfoEnvelope % (_EXCHANGE_SOAP_NAMESPACE,
                                                   sessionToken,)
        response = self.http_helper.makeRequest(self.url, env, 
                                                'getSubscriptionInfo')
        return GetSubscriptionInfoResp(response)
        
class BFExchangeService:
    
    """Proxy class for the Betfair API.
    
    This class provides a simple proxy that wraps a subset (more coming soon!)
    of the Betfair API exchange services. For more information on the API, read
    the docs at http://bdp.betfair.com/apidocumentation.php
    
    """
    
    def __init__(self, debuglevel=0, hostname='api.betfair.com', 
                url='/exchange/v5/BFExchangeService', secure=True,
                compressed=False):
        """Initialises an http(s) connection to the Betfair API.
        
        debuglevel -- configures httplib's wiredump (default 0)
        hostname   -- the server to connect to (default api.betfair.com)
        url        -- the relative path to the service
        secure     -- use https (default True)
        compressed -- use gzip compression to reduce bandwidth (defaults to
                      False, but it is recommended you switch it on in 
                      production code)
        
        """
        # connection info
        self.http_helper = HttpHelper(debuglevel, hostname, secure, compressed)
        self.url = url
        
        # SOAP request envelopes
        self._getMarketEnvelope = '''
            <SOAP-ENV:Envelope 
            xmlns:SOAP-ENV="http://schemas.xmlsoap.org/soap/envelope/" 
            xmlns:SOAP-ENC="http://schemas.xmlsoap.org/soap/encoding/" 
            xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" 
            xmlns:xsd="http://www.w3.org/2001/XMLSchema">
                <SOAP-ENV:Body>
                    <m:getMarket xmlns:m="%s">
                        <m:request>
                            <header>
                                <clientStamp>0</clientStamp>
                                <sessionToken>%s</sessionToken>
                            </header>
                            <locale>%s</locale>
                            <marketId>%i</marketId>
                        </m:request>
                    </m:getMarket>
                </SOAP-ENV:Body>
            </SOAP-ENV:Envelope>'''

        self._getMarketPricesEnvelope = '''
            <SOAP-ENV:Envelope 
            xmlns:SOAP-ENV="http://schemas.xmlsoap.org/soap/envelope/" 
            xmlns:SOAP-ENC="http://schemas.xmlsoap.org/soap/encoding/" 
            xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" 
            xmlns:xsd="http://www.w3.org/2001/XMLSchema">
                <SOAP-ENV:Body>
                    <m:getMarketPrices xmlns:m="%s">
                        <m:request>
                            <header>
                                <clientStamp>0</clientStamp>
                                <sessionToken>%s</sessionToken>
                            </header>
                            <currencyCode>%s</currencyCode>
                            <marketId>%i</marketId>
                        </m:request>
                    </m:getMarketPrices>
                </SOAP-ENV:Body>
            </SOAP-ENV:Envelope>'''

        self._getMarketPricesCompressedEnvelope = '''
            <SOAP-ENV:Envelope 
            xmlns:SOAP-ENV="http://schemas.xmlsoap.org/soap/envelope/" 
            xmlns:SOAP-ENC="http://schemas.xmlsoap.org/soap/encoding/" 
            xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" 
            xmlns:xsd="http://www.w3.org/2001/XMLSchema">
                <SOAP-ENV:Body>
                    <m:getMarketPricesCompressed xmlns:m="%s">
                        <m:request>
                            <header>
                                <clientStamp>0</clientStamp>
                                <sessionToken>%s</sessionToken>
                            </header>
                            <currencyCode>%s</currencyCode>
                            <marketId>%i</marketId>
                        </m:request>
                    </m:getMarketPricesCompressed>
                </SOAP-ENV:Body>
            </SOAP-ENV:Envelope>'''

        self._getCompleteMarketPricesCompressedEnvelope = '''
            <SOAP-ENV:Envelope 
            xmlns:SOAP-ENV="http://schemas.xmlsoap.org/soap/envelope/" 
            xmlns:SOAP-ENC="http://schemas.xmlsoap.org/soap/encoding/" 
            xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" 
            xmlns:xsd="http://www.w3.org/2001/XMLSchema">
                <SOAP-ENV:Body>
                    <m:getCompleteMarketPricesCompressed xmlns:m="%s">
                        <m:request>
                            <header>
                                <clientStamp>0</clientStamp>
                                <sessionToken>%s</sessionToken>
                            </header>
                            <currencyCode>%s</currencyCode>
                            <marketId>%i</marketId>
                        </m:request>
                    </m:getCompleteMarketPricesCompressed>
                </SOAP-ENV:Body>
            </SOAP-ENV:Envelope>'''

        self._getSilksEnvelope = '''
            <SOAP-ENV:Envelope 
            xmlns:SOAP-ENV="http://schemas.xmlsoap.org/soap/envelope/" 
            xmlns:SOAP-ENC="http://schemas.xmlsoap.org/soap/encoding/" 
            xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" 
            xmlns:xsd="http://www.w3.org/2001/XMLSchema">
                <SOAP-ENV:Body>
                    <m:getSilks xmlns:m="%s">
                        <m:request>
                            <header>
                                <clientStamp>0</clientStamp>
                                <sessionToken>%s</sessionToken>
                            </header>
                            <locale>%s</locale>
                            <markets xmlns="">
                                %s
                            </markets>
                        </m:request>
                    </m:getSilks>
                </SOAP-ENV:Body>
            </SOAP-ENV:Envelope>'''

        self._getSilksV2Envelope = self._getSilksEnvelope.replace('getSilks',
                'getSilksV2')

        self._getMarketPricesCompressedEnvelope = '''
            <SOAP-ENV:Envelope 
            xmlns:SOAP-ENV="http://schemas.xmlsoap.org/soap/envelope/" 
            xmlns:SOAP-ENC="http://schemas.xmlsoap.org/soap/encoding/" 
            xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" 
            xmlns:xsd="http://www.w3.org/2001/XMLSchema">
                <SOAP-ENV:Body>
                    <m:getMarketPricesCompressed xmlns:m="%s">
                        <m:request>
                            <header>
                                <clientStamp>0</clientStamp>
                                <sessionToken>%s</sessionToken>
                            </header>
                            <currencyCode>%s</currencyCode>
                            <marketId>%i</marketId>
                        </m:request>
                    </m:getMarketPricesCompressed>
                </SOAP-ENV:Body>
            </SOAP-ENV:Envelope>'''

        self._getCompleteMarketPricesCompressedEnvelope = '''
            <SOAP-ENV:Envelope 
            xmlns:SOAP-ENV="http://schemas.xmlsoap.org/soap/envelope/" 
            xmlns:SOAP-ENC="http://schemas.xmlsoap.org/soap/encoding/" 
            xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" 
            xmlns:xsd="http://www.w3.org/2001/XMLSchema">
                <SOAP-ENV:Body>
                    <m:getCompleteMarketPricesCompressed xmlns:m="%s">
                        <m:request>
                            <header>
                                <clientStamp>0</clientStamp>
                                <sessionToken>%s</sessionToken>
                            </header>
                            <currencyCode>%s</currencyCode>
                            <marketId>%i</marketId>
                        </m:request>
                    </m:getCompleteMarketPricesCompressed>
                </SOAP-ENV:Body>
            </SOAP-ENV:Envelope>'''

        self._getCurrentBetsEnvelope = '''
            <SOAP-ENV:Envelope 
            xmlns:SOAP-ENV="http://schemas.xmlsoap.org/soap/envelope/" 
            xmlns:SOAP-ENC="http://schemas.xmlsoap.org/soap/encoding/" 
            xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" 
            xmlns:xsd="http://www.w3.org/2001/XMLSchema">
                <SOAP-ENV:Body>
                    <m:getCurrentBets xmlns:m="%s">
                        <m:request>
                            <header>
                                <clientStamp>0</clientStamp>
                                <sessionToken>%s</sessionToken>
                            </header>
                            <betStatus>%s</betStatus>
                            <detailed>%i</detailed>
                            <locale>%s</locale>
                            <timezone>%s</timezone>
                            <marketId>%i</marketId>
                            <orderBy>%s</orderBy>
                            <recordCount>%i</recordCount>
                            <startRecord>%i</startRecord>
                            <noTotalRecordCount>%i</noTotalRecordCount>
                        </m:request>
                    </m:getCurrentBets>
                </SOAP-ENV:Body>
            </SOAP-ENV:Envelope>'''

        self._getMUBetsEnvelope = '''
            <SOAP-ENV:Envelope 
            xmlns:SOAP-ENV="http://schemas.xmlsoap.org/soap/envelope/" 
            xmlns:SOAP-ENC="http://schemas.xmlsoap.org/soap/encoding/" 
            xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" 
            xmlns:xsd="http://www.w3.org/2001/XMLSchema">
                <SOAP-ENV:Body>
                    <m:getMUBets xmlns:m="%s">
                        <m:request>
                            <header>
                                <clientStamp>0</clientStamp>
                                <sessionToken>%s</sessionToken>
                            </header>
                            <betStatus>%s</betStatus>
                            <marketId>%i</marketId>
                            <betIds>
                                %s
                            </betIds>
                            <orderBy>%s</orderBy>
                            <sortOrder>%s</sortOrder>
                            <recordCount>%i</recordCount>
                            <startRecord>%i</startRecord>
                            <matchedSince>%s</matchedSince>
                        </m:request>
                    </m:getMUBets>
                </SOAP-ENV:Body>
            </SOAP-ENV:Envelope>'''

        self._getMarketProfitAndLossEnvelope = '''
            <SOAP-ENV:Envelope 
            xmlns:SOAP-ENV="http://schemas.xmlsoap.org/soap/envelope/" 
            xmlns:SOAP-ENC="http://schemas.xmlsoap.org/soap/encoding/" 
            xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" 
            xmlns:xsd="http://www.w3.org/2001/XMLSchema">
                <SOAP-ENV:Body>
                    <m:getMarketProfitAndLoss xmlns:m="%s">
                        <m:request>
                            <header>
                                <clientStamp>0</clientStamp>
                                <sessionToken>%s</sessionToken>
                            </header>
                            <includeSettledBets>%i</includeSettledBets>
                            <marketID>%i</marketID>
                            <netOfCommission>%i</netOfCommission>
                        </m:request>
                    </m:getMarketProfitAndLoss>
                </SOAP-ENV:Body>
            </SOAP-ENV:Envelope>'''
            
        self._getMarketTradedVolumeEnvelope = '''
            <SOAP-ENV:Envelope 
            xmlns:SOAP-ENV="http://schemas.xmlsoap.org/soap/envelope/" 
            xmlns:SOAP-ENC="http://schemas.xmlsoap.org/soap/encoding/" 
            xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" 
            xmlns:xsd="http://www.w3.org/2001/XMLSchema">
                <SOAP-ENV:Body>
                    <m:getMarketTradedVolume xmlns:m="%s">
                        <m:request>
                            <header>
                                <clientStamp>0</clientStamp>
                                <sessionToken>%s</sessionToken>
                            </header>
                            <asianLineId>%i</asianLineId>
                            <currencyCode>%s</currencyCode>
                            <marketId>%i</marketId>
                            <selectionId>%i</selectionId>
                        </m:request>
                    </m:getMarketTradedVolume>
                </SOAP-ENV:Body>
            </SOAP-ENV:Envelope>'''

        self._getAccountFundsEnvelope = '''
            <SOAP-ENV:Envelope 
            xmlns:SOAP-ENV="http://schemas.xmlsoap.org/soap/envelope/" 
            xmlns:SOAP-ENC="http://schemas.xmlsoap.org/soap/encoding/" 
            xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" 
            xmlns:xsd="http://www.w3.org/2001/XMLSchema">
                <SOAP-ENV:Body>
                    <m:getAccountFunds xmlns:m="%s">
                        <m:request>
                            <header>
                                <clientStamp>0</clientStamp>
                                <sessionToken>%s</sessionToken>
                            </header>
                        </m:request>
                    </m:getAccountFunds>
                </SOAP-ENV:Body>
            </SOAP-ENV:Envelope>'''
            
        self._getBetHistoryEnvelope = '''
            <SOAP-ENV:Envelope 
            xmlns:SOAP-ENV="http://schemas.xmlsoap.org/soap/envelope/" 
            xmlns:SOAP-ENC="http://schemas.xmlsoap.org/soap/encoding/" 
            xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" 
            xmlns:xsd="http://www.w3.org/2001/XMLSchema" 
            xmlns:m0="http://www.betfair.com/publicapi/types/">
                <SOAP-ENV:Body>
                    <m:getBetHistory xmlns:m="%s">
                        <m:request>
                            <header>
                                <clientStamp>0</clientStamp>
                                <sessionToken>%s</sessionToken>
                            </header>
                            <betTypesIncluded>%s</betTypesIncluded>
                            <detailed>%i</detailed>
                            <eventTypeIds>
                                %s
                            </eventTypeIds>
                            <marketId>%i</marketId>
                            <locale>%s</locale>
                            <timezone>%s</timezone>
                            <marketTypesIncluded>
                                %s
                            </marketTypesIncluded>
                            <placedDateFrom>%s</placedDateFrom>
                            <placedDateTo>%s</placedDateTo>
                            <recordCount>%i</recordCount>
                            <sortBetsBy>%s</sortBetsBy>
                            <startRecord>%i</startRecord>
                        </m:request>
                    </m:getBetHistory>
                </SOAP-ENV:Body>
            </SOAP-ENV:Envelope>'''
        
        self._getAccountStatementEnvelope = '''
            <SOAP-ENV:Envelope 
            xmlns:SOAP-ENV="http://schemas.xmlsoap.org/soap/envelope/" 
            xmlns:SOAP-ENC="http://schemas.xmlsoap.org/soap/encoding/" 
            xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" 
            xmlns:xsd="http://www.w3.org/2001/XMLSchema">
                <SOAP-ENV:Body>
                    <m:getAccountStatement xmlns:m="%s">
                        <m:req>
                            <header>
                                <clientStamp>0</clientStamp>
                                <sessionToken>%s</sessionToken>
                            </header>
                            <endDate>%s</endDate>
                            <itemsIncluded>%s</itemsIncluded>
                            <recordCount>%i</recordCount>
                            <startDate>%s</startDate>
                            <startRecord>%i</startRecord>
                            <locale>%s</locale>
                        </m:req>
                    </m:getAccountStatement>
                </SOAP-ENV:Body>
            </SOAP-ENV:Envelope>'''
        
        self._placeBetsEnvelope = '''
            <SOAP-ENV:Envelope xmlns:SOAP-ENV="http://schemas.xmlsoap.org/soap/envelope/" 
            xmlns:SOAP-ENC="http://schemas.xmlsoap.org/soap/encoding/" 
            xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" 
            xmlns:xsd="http://www.w3.org/2001/XMLSchema" 
            xmlns:m0="http://www.betfair.com/publicapi/types/">
                <SOAP-ENV:Body>
                    <m:placeBets xmlns:m="%s">
                        <m:request>
                            <header>
                                <clientStamp>0</clientStamp>
                                <sessionToken>%s</sessionToken>
                            </header>
                            <bets>
                                %s
                            </bets>
                        </m:request>
                    </m:placeBets>
                </SOAP-ENV:Body>
            </SOAP-ENV:Envelope>'''
            
        self._cancelBetsEnvelope = '''
            <SOAP-ENV:Envelope 
            xmlns:SOAP-ENV="http://schemas.xmlsoap.org/soap/envelope/" 
            xmlns:SOAP-ENC="http://schemas.xmlsoap.org/soap/encoding/" 
            xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" 
            xmlns:xsd="http://www.w3.org/2001/XMLSchema" 
            xmlns:m0="http://www.betfair.com/publicapi/types/">
                <SOAP-ENV:Body>
                    <m:cancelBets xmlns:m="%s">
                        <m:request>
                            <header>
                                <clientStamp>0</clientStamp>
                                <sessionToken>%s</sessionToken>
                            </header>
                            <bets>
                                %s
                            </bets>
                        </m:request>
                    </m:cancelBets>
                </SOAP-ENV:Body>
            </SOAP-ENV:Envelope>'''

        self._updateBetsEnvelope = '''
            <SOAP-ENV:Envelope 
            xmlns:SOAP-ENV="http://schemas.xmlsoap.org/soap/envelope/" 
            xmlns:SOAP-ENC="http://schemas.xmlsoap.org/soap/encoding/" 
            xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" 
            xmlns:xsd="http://www.w3.org/2001/XMLSchema" 
            xmlns:m0="http://www.betfair.com/publicapi/types/">
                <SOAP-ENV:Body>
                    <m:updateBets xmlns:m="%s">
                        <m:request>
                            <header>
                                <clientStamp>0</clientStamp>
                                <sessionToken>%s</sessionToken>
                            </header>
                            <bets>
                                %s
                            </bets>
                        </m:request>
                    </m:updateBets>
                </SOAP-ENV:Body>
            </SOAP-ENV:Envelope>'''
            
        self._getBetEnvelope = '''
            <SOAP-ENV:Envelope 
            xmlns:SOAP-ENV="http://schemas.xmlsoap.org/soap/envelope/" 
            xmlns:SOAP-ENC="http://schemas.xmlsoap.org/soap/encoding/" 
            xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" 
            xmlns:xsd="http://www.w3.org/2001/XMLSchema">
                <SOAP-ENV:Body>
                    <m:getBet xmlns:m="%s">
                        <m:request>
                            <header>
                                <clientStamp>0</clientStamp>
                                <sessionToken>%s</sessionToken>
                            </header>
                            <betId>%i</betId>
                        </m:request>
                    </m:getBet>
                </SOAP-ENV:Body>
            </SOAP-ENV:Envelope>'''
        
    def getAccountFunds(self, sessionToken):
        """Retrieve financial information about an account.
        
        Performs a getAccountFunds call against the Betfair API, and returns
        a GetAccountFundsResp object.
        
        sessionToken -- session identifier
        
        """
        # configure the template envelope and make the request
        env = self._getAccountFundsEnvelope % (_EXCHANGE_SOAP_NAMESPACE, sessionToken,)
        response = self.http_helper.makeRequest(self.url, env, 
                                                'getAccountFunds')
        return GetAccountFundsResp(response)
        
    def getAccountStatement(self, 
                            sessionToken, 
                            itemsIncluded="ALL",
                            locale="en_GB",
                            startDate=datetime.now() - timedelta(days=30),
                            endDate=datetime.now(), 
                            startRecord=0,
                            recordCount=10):
        """Retrieve information on account transactions.
        
        Performs a getAccountStatement call against the Betfair API, and returns
        a GetAccountStatementResp object.
        
        sessionToken  -- session identifier
        itemsIncluded -- 'ALL', 'DEPOSITS_WITHDRAWALS', 'EXCHANGE', 'POKER_ROOM'
        locale        -- controls the output language (default en_GB)
        startDate     -- records on or after this date (default 30 days ago)
        endDate       -- records on or before this date (default today)
        startRecord   -- first record number to return (supports paging)
        recordCount   -- maximum number of records to return
        
        """
        # configure the template envelope and make the request
        env = self._getAccountStatementEnvelope % (_EXCHANGE_SOAP_NAMESPACE, 
                                                   sessionToken, 
                                                   endDate.isoformat(), 
                                                   itemsIncluded, 
                                                   recordCount, 
                                                   startDate.isoformat(), 
                                                   startRecord,
                                                   locale)
        response = self.http_helper.makeRequest(self.url, env, 
                                                'getAccountStatement')
        return GetAccountStatementResp(response)
        
    def getBetHistory(self, 
                      sessionToken,
                      betTypesIncluded="S", 
                      detailed=False,
                      eventTypeIds=[1],
                      marketId=0,
                      locale="en_GB",
                      timezone="GMT",
                      marketTypesIncluded=["O"], 
                      placedDateFrom=datetime.now() - timedelta(days=30), 
                      placedDateTo=datetime.now(),
                      recordCount=10, 
                      sortBetsBy="NONE",
                      startRecord=0):
        """Retrieve historical betting data for an account.
        
        Retrieve information about bets that have been placed. Each request can 
        only retrieve bets of the same status (MATCHED/UNMATCHED etc)
        Pagination through the result set is supported using the startRecord and 
        recordCount parameters.
        
        sessionToken        -- session identifier
        betTypesIncluded    -- ('C')ancelled, ('L')apsed, ('M')atched, 
                               ('S')ettled, ('U')nmatched, ('V')oided
        detailed            -- show details of all the matches on a single bet
        eventTypeIds        -- list of event types (sports) to return
        marketId            -- id of the market
        locale              -- controls the output language (default en_GB)
        timezone            -- adjusts times/dates for specified timezone
        marketTypesIncluded -- list of ('A')sian Handicap, ('L')ine, ('O')dds,
                               ('R')ange
        placedDateFrom      -- records on or after this date (default 30 days 
                               ago)
        placedDateTo        -- records on or before this date (default today)
        recordCount         -- maximum number of records to return
        sortBetsBy          -- 'BET_ID', 'CANCELLED_DATE', 'MARKET_NAME', 
                               'NONE', 'PLACED_DATE'
        startRecord         -- first record number to return (supports paging)
        
        """
        # create elements for the required sports
        sports = ''
        for eventTypeId in eventTypeIds:
            sports = sports + "<m0:int>%i</m0:int>" % (eventTypeId,)
            
        # send 1 or 0 instead of true/false
        includeDetail = detailed and 1 or 0
        
        # create elements for the required market types
        marketTypes = ''
        for marketType in marketTypesIncluded:
            marketTypes = marketTypes + \
                "<m0:MarketTypeEnum>%s</m0:MarketTypeEnum>" % (marketType,)
            
        # configure the template envelope and make the request
        env = self._getBetHistoryEnvelope % (_EXCHANGE_SOAP_NAMESPACE,
                                             sessionToken,
                                             betTypesIncluded,
                                             includeDetail,
                                             sports,
                                             language,
                                             marketTypes, 
                                             placedDateFrom.isoformat(),
                                             placedDateTo.isoformat(), 
                                             recordCount,
                                             sortBetsBy,
                                             startRecord)
        response = self.http_helper.makeRequest(self.url, env, 
                                                'getBetHistory')
        return GetBetHistoryResp(response)
        
    def getCurrentBets(self,
                       sessionToken,
                       betStatus="U",
                       detailed=False, 
                       locale="en_GB",
                       timezone="GMT",
                       marketId=0,
                       orderBy="NONE", 
                       recordCount=10,
                       startRecord=0,
                       noTotalRecordCount=False):
        """Retrieve information about bets that have been placed. 
        
        Information can be retrieved from either a single market or across all 
        markets (specify marketId=0 for all markets).
        
        sessionToken        -- session identifier
        betStatus           -- ('C')ancelled, ('L')apsed, ('M')atched,
                               ('S')ettled, ('U')nmatched, ('V')oided
        detailed            -- show details of all the matches on a single bet
        locale              -- controls the output language (default en_GB)
        timezone            -- adjusts times/dates for specified timezone
        marketId            -- id of the market
        orderBy             -- 'BET_ID', 'CANCELLED_DATE', 'MARKET_NAME',
                               'NONE', 'PLACED_DATE'
        recordCount         -- maximum number of records to return
        startRecord         -- first record number to return (supports paging)
        noTotalRecordCount  -- exclude total record count field in response
                               (faster if you do not need it for paging)
        """
        # send 1 or 0 instead of true/false
        detail_ = detailed and 1 or 0
        noTotalRecordCount_ = noTotalRecordCount and 1 or 0
        
        # configure the template envelope and make the request
        env = self._getCurrentBetsEnvelope % (_EXCHANGE_SOAP_NAMESPACE,
                                              sessionToken,
                                              betStatus,
                                              detail_,
                                              locale,
                                              timezone,
                                              marketId,
                                              orderBy, 
                                              recordCount,
                                              startRecord,
                                              noTotalRecordCount_)
        response = self.http_helper.makeRequest(self.url, env, 
                                                'getCurrentBets')
        return GetCurrentBetsResp(response)
        
    def getMUBets(self,
                  sessionToken,
                  betStatus="U",
                  marketId=0,
                  betIds=None,
                  orderBy="NONE", 
                  sortOrder="DESC",
                  recordCount=10,
                  startRecord=0,
                  matchedSince=datetime(1, 1, 1, 0, 0, 0)):
        """Retrieve information about bets that have been placed. 
        
        Information can be retrieved from either a single market or across all 
        markets (specify marketId=0 for all markets).
        
        sessionToken -- session identifier
        betStatus    -- ('C')ancelled, ('L')apsed, ('M')atched, ('S')ettled, 
                        ('U')nmatched, ('V')oided
        marketId     -- id of the market
        betIds       -- the bets to retreive data for
        orderBy      -- 'BET_ID', 'CANCELLED_DATE', 'MARKET_NAME', 'NONE', 
                        'PLACED_DATE'
        sortOrder    -- 'DESC', 'ASC'
        recordCount  -- maximum number of records to return
        startRecord  -- first record number to return (supports paging)
        matchedSince -- return only bets matched since this time
        """
        
        betIds_ = ""
        if betIds != None:
            for betId in betIds:
                betIds_ = betIds_ + "<betId>%i</betId>" % (betId,)
            
        # configure the template envelope and make the request
        env = self._getMUBetsEnvelope % (_EXCHANGE_SOAP_NAMESPACE,
                                         sessionToken,
                                         betStatus,
                                         marketId,
                                         betIds_,
                                         orderBy,
                                         sortOrder,
                                         recordCount,
                                         startRecord,
                                         matchedSince.isoformat())
        response = self.http_helper.makeRequest(self.url, env, 
                                                'getMUBets')
        return GetMUBetsResp(response)
        
    def getMarket(self, sessionToken, marketId, locale="en_GB"):
        """Retrieve all static market data for the specified market.
        
        Performs a getMarket call against the Betfair API, and returns a
        GetMarketResp object. The Market object is suitable for caching as it 
        contains data about the market that does not change. See getMarketPrices 
        for dynamic data.
        
        sessionToken -- session identifier
        marketId     -- the market ID
        locale       -- controls the output language (default en_GB)

        """
        # configure the template envelope and make the request
        env = self._getMarketEnvelope % (_EXCHANGE_SOAP_NAMESPACE,
                                         sessionToken,
                                         locale,
                                         marketId)
        response = self.http_helper.makeRequest(self.url, env, 
                                                'getMarket')
        return GetMarketResp(response)

    def getMarketPrices(self,
                        sessionToken,
                        marketId,
                        currencyCode="GBP"):
        """Retrieve dynamic market data for the specified market.
        
        Performs a getMarketPrices call against the Betfair API, and returns a
        GetMarketPricesResp object. The MarketPrices object contains dynamic 
        data forthe market, e.g. prices, amounts available, bet delay etc. For 
        static data such as market name and runner names, see getMarket.
        
        sessionToken -- session identifier
        marketId     -- the market ID
        locale       -- controls the output language (default en_GB)

        """
        # configure the template envelope and make the request
        env = self._getMarketPricesEnvelope % (_EXCHANGE_SOAP_NAMESPACE,
                                               sessionToken,
                                               currencyCode,
                                               marketId)
        response = self.http_helper.makeRequest(self.url, env, 
                                                'getMarketPrices')
        return GetMarketPricesResp(response)

    def getMarketPricesCompressed(self,
                        sessionToken,
                        marketId,
                        currencyCode="GBP"):
        """Retrieve dynamic market data for the specified market.
        
        Performs a getMarketPricesCompressed call against the Betfair API, and returns a
        GetMarketPricesCompressedResp object. The MarketPrices object contains dynamic 
        data for the market, e.g. prices, amounts available, bet delay etc. For 
        static data such as market name and runner names, see getMarket.
        
        sessionToken -- session identifier
        marketId     -- the market ID
        locale       -- controls the output language (default en_GB)

        """
        # configure the template envelope and make the request
        env = self._getMarketPricesCompressedEnvelope % (_EXCHANGE_SOAP_NAMESPACE,
                                               sessionToken,
                                               currencyCode,
                                               marketId)
        response = self.http_helper.makeRequest(self.url, env, 
                                                'getMarketPricesCompressed')
        return GetMarketPricesCompressedResp(response)

    def getCompleteMarketPricesCompressed(self,
                        sessionToken,
                        marketId,
                        currencyCode="GBP"):
        """Retrieve dynamic market data for the specified market.
        
        Performs a getCompleteMarketPricesCompressed call against the Betfair API, and returns a
        GetCompleteMarketPricesCompressedResp object. The MarketPrices object contains dynamic 
        data for the market, e.g. prices, amounts available, bet delay etc. For 
        static data such as market name and runner names, see getMarket.
        
        sessionToken -- session identifier
        marketId     -- the market ID
        locale       -- controls the output language (default en_GB)

        """
        # configure the template envelope and make the request
        env = self._getCompleteMarketPricesCompressedEnvelope % (_EXCHANGE_SOAP_NAMESPACE,
                                                       sessionToken,
                                                       currencyCode,
                                                       marketId)
        response = self.http_helper.makeRequest(self.url, env, 
                                                'getCompleteMarketPricesCompressed')
        return GetCompleteMarketPricesCompressedResp(response)

    def getSilks(self, sessionToken, marketIds, locale="en"):
        """Retrieve static runner data for the specified market.
        
        Performs a getSilks call against the Betfair API, and returns a
        GetSilksResp object. The racingSilks object contains static 
        data for all selections in a market, e.g. Silks description, Trainer Name,
        Age and Weight, Form, etc.
        
        sessionToken -- session identifier
        marketId     -- the market ID
        locale       -- controls the output language (default en_GB)

        """

        ids = ''
        for marketId in marketIds:
            ids = ids + '''
                <int xmlns="http://www.betfair.com/publicapi/types/exchange/v5/">
                    %i
                </int>
            ''' % (marketId,)
        # configure the template envelope and make the request
        env = self._getSilksEnvelope % (_EXCHANGE_SOAP_NAMESPACE,
                                        sessionToken,
                                        locale,
                                        ids)
        response = self.http_helper.makeRequest(self.url, env, 
                                                'getSilks')
        return GetSilksResp(response)

    def getSilksV2(self, sessionToken, marketIds, locale="en"):
        """Retrieve static runner data for the specified market.
        
        Performs a getSilksV2 call against the Betfair API, and returns a
        GetSilksResp object. The racingSilks object contains static 
        data for all selections in a market, e.g. Silks description, Trainer Name,
        Age and Weight, Form, etc, plus extended information including
        dam/sire.
        
        sessionToken -- session identifier
        marketId     -- the market ID
        locale       -- controls the output language (default en_GB)

        """
        ids = ''
        for marketId in marketIds:
            ids = ids + '''
            <int xmlns="http://www.betfair.com/publicapi/types/exchange/v5/">
            %i
            </int>
            ''' % (marketId,)
        env = self._getSilksV2Envelope % (_EXCHANGE_SOAP_NAMESPACE,
                                          sessionToken,
                                          locale,
                                          ids)
        response = self.http_helper.makeRequest(self.url, env, 
                                                'getSilksV2')
        return GetSilksResp(response)

    def getMarketPricesCompressed(self,
                        sessionToken,
                        marketId,
                        currencyCode="GBP"):
        """Retrieve dynamic market data for the specified market.
        
        Performs a getMarketPricesCompressed call against the Betfair API, and returns a
        GetMarketPricesCompressedResp object. The MarketPrices object contains dynamic 
        data for the market, e.g. prices, amounts available, bet delay etc. For 
        static data such as market name and runner names, see getMarket.
        
        sessionToken -- session identifier
        marketId     -- the market ID
        locale       -- controls the output language (default en_GB)

        """
        # configure the template envelope and make the request
        env = self._getMarketPricesCompressedEnvelope % (_EXCHANGE_SOAP_NAMESPACE,
                                               sessionToken,
                                               currencyCode,
                                               marketId)
        response = self.http_helper.makeRequest(self.url, env, 
                                                'getMarketPricesCompressed')
        return GetMarketPricesCompressedResp(response)

    def getCompleteMarketPricesCompressed(self,
                        sessionToken,
                        marketId,
                        currencyCode="GBP"):
        """Retrieve dynamic market data for the specified market.
        
        Performs a getCompleteMarketPricesCompressed call against the Betfair API, and returns a
        GetCompleteMarketPricesCompressedResp object. The MarketPrices object contains dynamic 
        data for the market, e.g. prices, amounts available, bet delay etc. For 
        static data such as market name and runner names, see getMarket.
        
        sessionToken -- session identifier
        marketId     -- the market ID
        locale       -- controls the output language (default en_GB)

        """
        # configure the template envelope and make the request
        env = self._getCompleteMarketPricesCompressedEnvelope % (_EXCHANGE_SOAP_NAMESPACE,
                                                       sessionToken,
                                                       currencyCode,
                                                       marketId)
        response = self.http_helper.makeRequest(self.url, env, 
                                                'getCompleteMarketPricesCompressed')
        return GetCompleteMarketPricesCompressedResp(response)

    def getMarketProfitAndLoss(self,
                               sessionToken,
                               marketId, 
                               includeSettledBets=False,
                               netOfCommission=False):
        """Retrieve profit & loss information for the user account in the 
        specified market.
        
        Performs a getMarketProfitAndLoss call against the Betfair API, and
        returns a GetMarketProfitAndLossResp object.
        
        sessionToken       -- session identifier
        marketId           -- the market ID
        includeSettledBets -- bets that have already been settled will be 
                              returned as part of P&L (default False)
        netOfCommission    -- return P&L net of user's current commission rate 
                              for this market including any special tariffs
                              (default False)
        
        """
        # send 1 or 0 instead of true/false
        settled = includeSettledBets and 1 or 0
        comm = netOfCommission and 1 or 0

        # configure the template envelope and make the request
        env = self._getMarketProfitAndLossEnvelope % (_EXCHANGE_SOAP_NAMESPACE,
            sessionToken, settled, marketId, comm)
        response = self.http_helper.makeRequest(self.url, env, 
                                                'getMarketProfitAndLoss')
        return GetMarketProfitAndLossResp(response)
        
    def getMarketTradedVolume(self,
                              sessionToken,
                              marketId,
                              asianLineId, 
                              selectionId,
                              currencyCode="GBP"):
        """Retrieve all the current odds and matched amounts on the runners in
        the specified market.
        
        Performs a getMarketTradedVolume call against the Betfair API, and
        returns a GetMarketTradedVolumeResp object.
        
        sessionToken -- session identifier
        marketId     -- the market ID
        asianLineId  -- mandatory if the market specified by marketId is an 
                        Asian Handicap market, otherwise optional
        selectionId  -- the desired runner id
        currencyCode -- three letter ISO 4217 code (default GBP)
        
        """
        # configure the template envelope and make the request
        env = self._getMarketTradedVolumeEnvelope % (_EXCHANGE_SOAP_NAMESPACE,
                                                     sessionToken,
                                                     asianLineId,
                                                     currencyCode,
                                                     marketId,
                                                     selectionId)
        response = self.http_helper.makeRequest(self.url, env, 
                                                'getMarketTradedVolume')
        return GetMarketTradedVolumeResp(response)
        
    def placeBets(self, sessionToken, bets):
        """Allows you to place multiple (1 to 60) bets on a single market. 
        
        Performs a placeBets call against the Betfair API, and returns a
        PlaceBetsResp object. There is an instance of BetPlacementResult
        returned in the output for each instance of PlaceBet in the input. The
        success or failure of the individual bet placement operation is
        indicated by the success flag.
        
        sessionToken -- session identifier
        bets         -- list of PlaceBet objects
        
        """
        # create elements for the new bets
        newBets = ''
        for bet in bets:
            newBets = newBets + '''
                <m0:PlaceBets>
                    <asianLineId>%i</asianLineId>
                    <betType>%s</betType>
                    <marketId>%i</marketId>
                    <price>%.2f</price>
                    <selectionId>%i</selectionId>
                    <size>%.2f</size>
                </m0:PlaceBets>''' % (bet.asianLineId,
                                      bet.betType,
                                      bet.marketId,
                                      bet.price,
                                      bet.selectionId,
                                      bet.size)
        
        # configure the template envelope and make the request
        env = self._placeBetsEnvelope % (_EXCHANGE_SOAP_NAMESPACE,
                                         sessionToken,
                                         newBets)
        response = self.http_helper.makeRequest(self.url, env, 
                                                'placeBets')
        return PlaceBetsResp(response)

    def updateBets(self, sessionToken, bets):
        """Allows you to edit multiple (1 to 15) bets on a single market.
        
        Performs a updateBets call against the Betfair API, and returns an
        UpdateBetsResp object. There is an instance of UpdateBetsResp returned
        in the output for each instance of UpdateBetsResult in the input. The
        success or failure of the individual bet editing operation is indicated
        by the success flag.
        
        sessionToken -- session identifier
        bets         -- list of UpdateBets objects
        
        """
        # create elements for the update requests
        updates = ''
        for bet in bets:
            updates = updates + '''
                <m0:UpdateBets>
                    <betId>%i</betId>
                    <newPrice>%.2f</newPrice>
                    <newSize>%.2f</newSize>
                    <oldPrice>%.2f</oldPrice>
                    <oldSize>%.2f</oldSize>
                </m0:UpdateBets>''' % (bet.betId,
                                       bet.newPrice,
                                       bet.newSize, 
                                       bet.oldPrice,
                                       bet.oldSize)

        # configure the template envelope and make the request
        env = self._updateBetsEnvelope % (_EXCHANGE_SOAP_NAMESPACE,
                                          sessionToken,
                                          updates)
        response = self.http_helper.makeRequest(self.url, env, 
                                                'updateBets')
        return UpdateBetsResp(response)
        
    def cancelBets(self, sessionToken, bets):
        """Allows you to cancel multiple (1 to 40) bets placed on a single market.
        
        Performs a cancelBets call against the Betfair API, and returns an
        CancelBetsResp object. There is an instance of CancelBetsResult returned
        in the output for each betId in the input. The success or failure of the
        individual bet cancellation operation will indicated by the success
        flag. If a portion of the original bet is already matched, cancelBet
        cancels the unmatched portion of the bet.
        
        sessionToken -- session identifier
        bets         -- list of betIds
        
        """
        # create elements for the cancel requests
        cancellations = ''
        for betId in bets:
            cancellations = cancellations + '''
                <m0:CancelBets>
                    <betId>%i</betId>
                </m0:CancelBets>''' % (betId,)

        # configure the template envelope and make the request
        env = self._cancelBetsEnvelope % (_EXCHANGE_SOAP_NAMESPACE,
                                          sessionToken,
                                          cancellations)
        response = self.http_helper.makeRequest(self.url, env, 
                                                'cancelbets')
        return CancelBetsResp(response)
        
    def getBet(self, sessionToken, betId):
        """Retrieves a single bet.
        
        Performs a getBet call against the Betfair API, and returns a GetBetResp
        object. Each request will retrieve all components of the desired bet.
        
        """
        # configure the template envelope and make the request
        env = self._getBetEnvelope % (_EXCHANGE_SOAP_NAMESPACE, sessionToken, betId)
        response = self.http_helper.makeRequest(self.url, env, 
                                                'getBet')
        return GetBetResp(response)
        
class APIResponseHeader:
    
    """The APIResponseHeader contains the user's session token and client stamp
    which uniquely identify each call/session. There is an instance of
    APIResponseHeader returned in the output for each service call.
    
    Attributes:
        errorCode      -- if not 'OK', indicates a non service specific error 
                          has occurred
        minorErrorCode -- reserved for future use - currently always null
        sessionToken   -- unique identifier for next request in this session. 
                          This token must be passed to the next service invoked.
        timestamp      -- the time at which the response was returned from the 
                          server
    
    """
    
    def __init__(self, node):
        """Initialise a new instance.
        
        node -- the Xml node to initialise from
        
        """
        
        # store the xml in case we want to see the raw data
        self.node = node
        
        tag = self.node.getElementsByTagName
                    
        self.errorCode = tag('errorCode')[0].childNodes[0].nodeValue

        # minor error code (might be null)
        minorErrorCode = tag('minorErrorCode')[0]
        self.minorErrorCode = minorErrorCode.hasChildNodes() \
            and minorErrorCode.childNodes[0].nodeValue \
            or None
        
        # session token (might be null if an operation fails)
        sessionToken = tag('sessionToken')[0]
        self.sessionToken = sessionToken.hasChildNodes() \
            and sessionToken.childNodes[0].nodeValue \
            or None
            
        self.timestamp = _convert_iso_time(
            tag('timestamp')[0].childNodes[0].nodeValue)
            
    def __repr__(self):
        """Returns formatted XML representing the object."""
        return self.node.toprettyxml()
        
    def __str__(self):
        return '(%s, %s, %s)' % (self.errorCode, self.sessionToken, 
                                                    self.timestamp.isoformat())
        
class LoginResp:
    
    """Encapsulates a login response from the API.
    
    Attributes:
        header         -- APIResponseHeader
        currency       -- currency used by account
        errorCode      -- if not 'OK', indicates a non service specific error 
                          has occurred. See below.
        minorErrorCode -- reserved for future use - currently always null
        validUntil     -- logins will succeed until this date, after which 
                          time they will be rejected unless help desk is 
                          contacted.
        
    Error codes:
        ACCOUNT_CLOSED
            Account closed - please contact BDP support.
        ACCOUNT_SUSPENDED
            Account suspended - please contact BDP support.
        API_ERROR
            General API Error
        FAILED_MESSAGE
            The user cannot login until they acknowledge a message from Betfair.
        INVALID_LOCATION
            Invalid locationID
        INVALID_PRODUCT
            Invalid productID entered
        INVALID_USERNAME_OR_PASSWORD
            Incorrect username and/or password supplied.
        INVALID_VENDOR_SOFTWARE_ID
            Invalid vendorSoftwareId supplied
        LOGIN_FAILED_ACCOUNT_LOCKED
            Account locked due to too many failed login attempts
        LOGIN_REQUIRE_TERMS_AND_CONDITIONS_ACCEPTANCE
            Account locked, has T&C to agree to
        LOGIN_RESTRICTED_LOCATION
            Login origin from a restricted country
        LOGIN_UNAUTHORIZED
            User has not been permissioned to use API login
        OK_MESSAGES
            There are additional messages on your account. Please log in to the 
            web site to view them
        POKER_T_AND_C_ACCEPTANCE_REQUIRED
            Account locked, Please login to the Betfair Poker website and 
            assent to the terms and conditions
        T_AND_C_ACCEPTANCE_REQUIRED
            Account locked, Please login to the Betfair website and assent to 
            the terms and conditions.
        USER_NOT_ACCOUNT_OWNER
            The specified account is not a trading account and therefore cannot 
            be used for API access.
    
    """
    
    def __init__(self, doc):
        """Initialise a new instance.
        
        doc -- the Xml doc to initialise from
        
        """
        # store the xml in case we want to see the raw data
        self.node = doc.getElementsByTagNameNS( 
            _GLOBAL_SOAP_NAMESPACE, 
            'loginResponse')[0]
            
        tag = self.node.getElementsByTagName
                    
        self.header = APIResponseHeader(tag('header')[0])
        
        # currency (might be null if login fails)
        currency = tag('currency')[0]
        self.currency = currency.hasChildNodes() \
            and currency.childNodes[0].nodeValue \
            or None
            
        self.errorCode = tag('errorCode')[0].childNodes[0].nodeValue
        
        # minor error code (might be null)
        minorErrorCode = tag('minorErrorCode')[0]
        self.minorErrorCode = minorErrorCode.hasChildNodes() \
            and minorErrorCode.childNodes[0].nodeValue \
            or None
        
        self.validUntil = _convert_iso_time(
            tag('validUntil')[0].childNodes[0].nodeValue)
        
    def __repr__(self):
        return self.node.toprettyxml()
        
    def __str__(self):
        return '''LoginResp
            header: %s
            currency %s
            errorCode %s
            validUntil %s
            ''' % (str(self.header), self.currency, self.errorCode,
                    self.validUntil.isoformat())
        
class GetEventTypesResp:
    
    """Encapsulates a getActiveEventTypes response from the API.
    
    Attributes:
        header         -- APIResponseHeader
        errorCode      -- if not 'OK', indicates a non service specific error 
                          has occurred. See below.
        eventTypeItems -- list of EventType
        minorErrorCode -- reserved for future use - currently always null

    Error codes:
        API_ERROR
            General API Error
        INVALID_EVENT_ID
            The parent id is either not valid or the parent does not have any 
            event children
        INVALID_LOCALE_DEFAULTING_TO_ENGLISH
            The locale string was not recognized. Returned results are in 
            English
        NO_RESULTS
            No data available to return  
        
    """
    
    def __init__(self, doc):
        """Initialise a new instance.
        
        doc -- the Xml doc to initialise from
        
        """
        
        # store the xml in case we want to see the raw data
        self.doc = doc
        self.node = doc.getElementsByTagNameNS( 
            _GLOBAL_SOAP_NAMESPACE, 
            'getActiveEventTypesResponse')[0]
            
        tag = self.node.getElementsByTagName
                    
        self.header = APIResponseHeader(tag('header')[0])
        
        # event types (might be null)
        eventTypeItems = tag('eventTypeItems')[0]
        self.eventTypeItems = eventTypeItems.hasChildNodes() \
            and [ EventType(node) for node in eventTypeItems.childNodes ] \
            or []
        
        self.errorCode = tag('errorCode')[0].childNodes[0].nodeValue
        
        # minor error code (might be null)
        minorErrorCode = tag('minorErrorCode')[0]
        self.minorErrorCode = minorErrorCode.hasChildNodes() \
            and minorErrorCode.childNodes[0].nodeValue \
            or None
        
    def __repr__(self):
        """Returns formatted XML representing the object."""
        return self.node.toprettyxml()
        
    def __str__(self):
        return '''GetEventTypesResp
            header: %s
            eventTypeItems: %s
            errorCode: %s
            ''' % (str(self.header), 
                    [ str(item) for item in self.eventTypeItems ], 
                    self.errorCode)
        
    def getEventTypeIds(self):
        return [ item.id for item in self.eventTypeItems ]
        
class GetEventsResp:
    
    """Encapsulates a getEvents response from the API.
    
    Attributes:
        header         -- APIResponseHeader
        errorCode      -- if not 'OK', indicates a non service specific error 
                          has occurred. See below.
        eventItems     -- list of BFEvent
        eventParentId  -- either an event ID or a event type (sport) ID
        marketItems    -- list of MarketSummary
        minorErrorCode -- reserved for future use - currently always null

    Error codes:        
        API_ERROR
            General API Error
        INVALID_EVENT_ID
            The parent id is either not valid or the parent does not have any 
            event children
        INVALID_LOCALE_DEFAULTING_TO_ENGLISH
            The locale string was not recognized. Returned results are in 
            English
        NO_RESULTS
            No data available to return  

    """

    def __init__(self, doc):
        """Initialise a new instance.
        
        doc -- the Xml doc to initialise from
        
        """
        
        # store the xml in case we want to see the raw data
        self.node = doc.getElementsByTagNameNS( 
            _GLOBAL_SOAP_NAMESPACE, 
            'getEventsResponse')[0]
                    
        tag = self.node.getElementsByTagName
                    
        self.header = APIResponseHeader(tag('header')[0])
        self.errorCode = tag('errorCode')[0].childNodes[0].nodeValue
        
        # events (might be null)
        eventItems = tag('eventItems')[0]
        self.eventItems = eventItems.hasChildNodes() \
            and [ BFEvent(node) for node in eventItems.childNodes ] \
            or []
            
        # sort events
        self.eventItems.sort(lambda x, y: x.orderIndex - y.orderIndex)
            
        self.eventParentId = int(tag('eventParentId')[0] \
            .childNodes[0].nodeValue)
        
        # markets (might be null)
        marketItems = tag('marketItems')[0]
        self.marketItems = marketItems.hasChildNodes() \
            and [ MarketSummary(node) for node in marketItems.childNodes ] \
            or []
            
        # sort markets
        self.marketItems.sort(lambda x, y: x.orderIndex - y.orderIndex)
        
        # minor error code (might be null)
        minorErrorCode = tag('minorErrorCode')[0]
        self.minorErrorCode = minorErrorCode.hasChildNodes() \
            and minorErrorCode.childNodes[0].nodeValue \
            or None
        
    def __repr__(self):
        """Returns formatted XML representing the object."""
        return self.node.toprettyxml()
        
    def __str__(self):
        return '''GetEventsResp
            header: %s
            eventItems: %s
            marketItems %s
            errorCode: %s
            ''' % (str(self.header), \
                    [ str(item) for item in self.eventItems ], \
                    [ str(item) for item in self.marketItems ], \
                    self.errorCode)

class GetMarketResp:
    
    """Encapsulates a getMarket response from the API.
    
    Attributes:
        header         -- APIResponseHeader
        errorCode      -- if not 'OK', indicates a non service specific error 
                          has occurred. See below.
        market         -- Market
        minorErrorCode -- reserved for future use - currently always null

    Error codes:        
        API_ERROR
            General API Error
        INVALID_LOCALE_DEFAULTING_TO_ENGLISH
            The locale string was not recognized. Returned results are in 
            English
        INVALID_MARKET
            Invalid market ID supplied
        MARKET_TYPE_NOT_SUPPORTED
            The market ID supplied refers to a market that is not supported by
            the API. Currently, this includes Line and Range markets.

    """

    def __init__(self, doc):
        """Initialise a new instance.
        
        doc -- the Xml doc to initialise from
        
        """
        
        # store the xml in case we want to see the raw data
        self.node = doc.getElementsByTagNameNS(_EXCHANGE_SOAP_NAMESPACE,
                                               'getMarketResponse')[0]
                    
        tag = self.node.getElementsByTagName
                    
        self.header = APIResponseHeader(tag('header')[0])
        self.errorCode = tag('errorCode')[0].childNodes[0].nodeValue
        
        market = tag('market')[0]
        self.market = market.hasChildNodes() and Market(market) or None
        
        # minor error code (might be null)
        minorErrorCode = tag('minorErrorCode')[0]
        self.minorErrorCode = minorErrorCode.hasChildNodes() \
            and minorErrorCode.childNodes[0].nodeValue \
            or None
        
    def __repr__(self):
        """Returns formatted XML representing the object."""
        return self.node.toprettyxml()

    def __str__(self):
        return '''GetMarketResp
            header: %s
            market: %s
            errorCode: %s
            ''' % (str(self.header), str(self.market), self.errorCode)
            
class GetMarketPricesResp:
    
    """Encapsulates a getMarketPrices response from the API.
    
    Attributes:
        header         -- APIResponseHeader
        errorCode      -- if not 'OK', indicates a non service specific error 
                          has occurred. See below.
        marketPrices   -- MarketPrices
        minorErrorCode -- reserved for future use - currently always null

    Error codes:        
        API_ERROR
            General API Error
        INVALID_CURRENCY
            Currency code not a valid 3 letter ISO 4217 currency abbreviation
        INVALID_MARKET
            Invalid market ID supplied
        MARKET_TYPE_NOT_SUPPORTED
            The market ID supplied refers to a market that is not supported by
            the API. Currently, this includes Line and Range markets.

    """

    def __init__(self, doc):
        """Initialise a new instance.
        
        doc -- the Xml doc to initialise from
        
        """
        
        # store the xml in case we want to see the raw data
        self.node = doc.getElementsByTagNameNS(_EXCHANGE_SOAP_NAMESPACE,
                                               'getMarketPricesResponse')[0]
            
        tag = self.node.getElementsByTagName

        self.header = APIResponseHeader(tag('header')[0])
        self.errorCode = tag('errorCode')[0].childNodes[0].nodeValue
        
        # market prices (might be null)
        marketPrices = tag('marketPrices')[0]
        self.marketPrices = marketPrices.hasChildNodes() \
            and MarketPrices(marketPrices) \
            or None
        
        # minor error code (might be null)
        minorErrorCode = tag('minorErrorCode')[0]
        self.minorErrorCode = minorErrorCode.hasChildNodes() \
            and minorErrorCode.childNodes[0].nodeValue \
            or None
        
    def __repr__(self):
        """Returns formatted XML representing the object."""
        return self.node.toprettyxml()
        
    def __str__(self):
        return '''GetMarketPricesResp
            header: %s
            marketPrices: %s
            errorCode: %s
            ''' % (str(self.header), str(self.marketPrices), self.errorCode)
            
class GetMarketPricesCompressedResp:
    
    """Encapsulates a getMarketPricesCompressed response from the API.
    
    Attributes:
        header         -- APIResponseHeader
        errorCode      -- if not 'OK', indicates a non service specific error 
                          has occurred. See below.
        marketPrices   -- MarketPrices
        minorErrorCode -- reserved for future use - currently always null

    Error codes:        
        API_ERROR
            General API Error
        INVALID_CURRENCY
            Currency code not a valid 3 letter ISO 4217 currency abbreviation
        INVALID_MARKET
            Invalid market ID supplied
        MARKET_TYPE_NOT_SUPPORTED
            The market ID supplied refers to a market that is not supported by
            the API. Currently, this includes Line and Range markets.

    """

    def __init__(self, doc):
        """Initialise a new instance.
        
        doc -- the Xml doc to initialise from
        
        """
        
        # store the xml in case we want to see the raw data
        self.node = doc.getElementsByTagNameNS(_EXCHANGE_SOAP_NAMESPACE,
                                               'getMarketPricesCompressedResponse')[0]
            
        tag = self.node.getElementsByTagName

        self.header = APIResponseHeader(tag('header')[0])
        self.errorCode = tag('errorCode')[0].childNodes[0].nodeValue
        
        # market prices (might be null)
        marketPrices = tag('marketPrices')[0].childNodes[0].nodeValue or None
        self.marketPrices = str(marketPrices)
        
        # minor error code (might be null)
        minorErrorCode = tag('minorErrorCode')[0]
        self.minorErrorCode = minorErrorCode.hasChildNodes() \
            and minorErrorCode.childNodes[0].nodeValue \
            or None
        
    def __repr__(self):
        """Returns formatted XML representing the object."""
        return self.node.toprettyxml()
        
    def __str__(self):
        return '''GetMarketPricesCompressedResp
            header: %s
            marketPrices: %s
            errorCode: %s
            ''' % (str(self.header), str(self.marketPrices), self.errorCode)

class GetCompleteMarketPricesCompressedResp:
    
    """Encapsulates a getCompleteMarketPricesCompressed response from the API.
    
    Attributes:
        header                 -- APIResponseHeader
        errorCode              -- if not 'OK', indicates a non service specific error 
                                  has occurred. See below.
        completeMarketPrices   -- CompleteMarketPrices
        minorErrorCode         -- reserved for future use - currently always null

    Error codes:        
        API_ERROR
            General API Error
        INVALID_CURRENCY
            Currency code not a valid 3 letter ISO 4217 currency abbreviation
        INVALID_MARKET
            Invalid market ID supplied
        MARKET_TYPE_NOT_SUPPORTED
            The market ID supplied refers to a market that is not supported by
            the API. Currently, this includes Line and Range markets.
        EVENT_CLOSED
            The market has closed.
        EVENT_SUSPENDED
            The market is suspended.
        EVENT_INACTIVE
            The market is inactive.

    """

    def __init__(self, doc):
        """Initialise a new instance.
        
        doc -- the Xml doc to initialise from
        
        """
        
        # store the xml in case we want to see the raw data
        self.node = doc.getElementsByTagNameNS(_EXCHANGE_SOAP_NAMESPACE,
                                               'getCompleteMarketPricesCompressedResponse')[0]
            
        tag = self.node.getElementsByTagName

        self.header = APIResponseHeader(tag('header')[0])
        self.errorCode = tag('errorCode')[0].childNodes[0].nodeValue
        
        # market prices (might be null)
        marketPrices = tag('completeMarketPrices')[0].childNodes[0].nodeValue or None
        self.marketPrices = str(marketPrices)
        
        # minor error code (might be null)
        minorErrorCode = tag('minorErrorCode')[0]
        self.minorErrorCode = minorErrorCode.hasChildNodes() \
            and minorErrorCode.childNodes[0].nodeValue \
            or None
        
    def __repr__(self):
        """Returns formatted XML representing the object."""
        return self.node.toprettyxml()
        
    def __str__(self):
        return '''GetCompleteMarketPricesCompressedResp
            header: %s
            marketPrices: %s
            errorCode: %s
            ''' % (str(self.header), str(self.marketPrices), self.errorCode)

class GetSilksResp:
    
    """Encapsulates a getSilks response from the API.
    
    Attributes:
        header                 -- APIResponseHeader
        errorCode              -- if not 'OK', indicates a non service specific error 
                                  has occurred. See below.
        marketDisplayDetails   -- the market data
        minorErrorCode         -- reserved for future use - currently always null

    Error codes:        
        API_ERROR
            General API Error
        INVALID_LOCALE
            The local string was not recognized
        INVALID_NUMBER_OF_MARKETS
            You have specified no markets, or more than 40 markets.

    """

    def __init__(self, doc):
        """Initialise a new instance.
        
        doc -- the Xml doc to initialise from
        
        """
        
        # store the xml in case we want to see the raw data.
        # For this response, distinguish between v1 and v2 responses
        elements = doc.getElementsByTagNameNS(_EXCHANGE_SOAP_NAMESPACE,
                                               'getSilksV2Response')
        if len(elements) != 0:
            self.node = elements[0]
        else:
            self.node = doc.getElementsByTagNameNS(
                                                _EXCHANGE_SOAP_NAMESPACE,
                                                'getSilksResponse')[0]
                    
        tag = self.node.getElementsByTagName
                    
        self.header = APIResponseHeader(tag('header')[0])
        self.errorCode = tag('errorCode')[0].childNodes[0].nodeValue
        
        details = tag('marketDisplayDetails')[0]
        self.marketDisplayDetails = details.hasChildNodes() \
            and [ MarketDisplayDetail(node) for node in details.childNodes ] \
            or []
       
        # minor error code (might be null)
        minorErrorCode = tag('minorErrorCode')[0]
        self.minorErrorCode = minorErrorCode.hasChildNodes() \
            and minorErrorCode.childNodes[0].nodeValue \
            or None
        
    def __repr__(self):
        """Returns formatted XML representing the object."""
        return self.node.toprettyxml()

    def __str__(self):
        return '''GetSilksResp
            header: %s
            marketDisplayDetails: %s
            errorCode: %s
            ''' % (str(self.header), self.marketDisplayDetails, self.errorCode)

class GetCurrentBetsResp:
    
    """Encapsulates a getCurrentBets response from the API.
    
    Attributes:
        header           -- APIResponseHeader
        bets             -- list of Bet
        errorCode        -- if not 'OK', indicates a non service specific error 
                            has occurred. See below.
        minorErrorCode   -- reserved for future use - currently always null
        totalRecordCount -- total number of records available

    Error codes:        
        API_ERROR
            General API Error
        INVALID_START_RECORD
            Start record is not supplied or is invalid
        INVALID_BET_STATUS
            Status is not valid
        INVALID_BET_STATUS_FOR_MARKET
            Market ID is present and status is VOIDED, LAPSED or CANCELLED
        INVALID_MARKET_ID
            Market ID is negative or does not exist
        INVALID_ORDER_BY_FOR_STATUS
            Ordering is not NONE and:
                1. Bet Status is MATCHED and Ordering is neither MATCHED_DATE 
                   or PLACED_DATE
                2. Bet Status is UNMATCHED and ordering isn't PLACED_DATE
                3. Bet Status is LAPSED or VOIDED and Ordering is not 
                   PLACED_DATE
                4. Bet Status is CANCELLED and Ordering is not CANCELLED_DATE
        INVALID_RECORD_COUNT
            Record Count is negative
        NO_RESULT

    """

    def __init__(self, doc):
        """Initialise a new instance.
        
        doc -- the Xml doc to initialise from
        
        """
        
        # store the xml in case we want to see the raw data
        self.node = doc.getElementsByTagNameNS(_EXCHANGE_SOAP_NAMESPACE, \
                                               'getCurrentBetsResponse')[0]
            
        tag = self.node.getElementsByTagName

        self.header = APIResponseHeader(tag('header')[0])
        
        # bets (might be null)
        bets = tag('bets')[0]
        self.bets = bets.hasChildNodes() \
            and [ Bet(node) for node in bets.childNodes ] \
            or []
            
        self.errorCode = tag('errorCode')[0].childNodes[0].nodeValue
        
        # minor error code (might be null)
        minorErrorCode = tag('minorErrorCode')[0]
        self.minorErrorCode = minorErrorCode.hasChildNodes() \
            and minorErrorCode.childNodes[0].nodeValue \
            or None
            
        self.totalRecordCount = int(tag('totalRecordCount')[0] \
            .childNodes[0].nodeValue)
       
    def __repr__(self):
        """Returns formatted XML representing the object."""
        return self.node.toprettyxml()
        
    def __str__(self):
        return '''GetCurrentBetsResp
            header: %s
            totalRecordCount: %i
            bets: %s
            errorCode: %s
            ''' % (str(self.header), self.totalRecordCount, \
                    [ str(bet) for bet in self.bets ], \
                    self.errorCode)
                    
class GetMUBetsResp:
    """Encapsulates a getMUBets response from the API.
    
    Attributes:
        header           -- APIResponseHeader
        bets             -- list of MUBet
        errorCode        -- if not 'OK', indicates a non service specific error 
                            has occurred. See below.
        minorErrorCode   -- reserved for future use - currently always null
        totalRecordCount -- total number of records available

    Error codes:        
        API_ERROR
            General API Error
        INVALID_START_RECORD
            Start record is not supplied or is invalid
        INVALID_BET_STATUS
            Status is not valid
        INVALID_MARKET_ID
            Market ID is negative or does not exist
        INVALID_ORDER_BY_FOR_STATUS
            Ordering is not NONE and:
                1. Bet Status is MATCHED and Ordering is neither MATCHED_DATE 
                   or PLACED_DATE
                2. Bet Status is UNMATCHED and ordering isn't PLACED_DATE
                3. Bet Status is LAPSED or VOIDED and Ordering is not 
                   PLACED_DATE
                4. Bet Status is CANCELLED and Ordering is not CANCELLED_DATE
        INVALID_RECORD_COUNT
            Record Count is negative
        NO_RESULT

    """

    def __init__(self, doc):
        """Initialise a new instance.
        
        doc -- the Xml doc to initialise from
        
        """
        
        # store the xml in case we want to see the raw data
        self.node = doc.getElementsByTagNameNS(_EXCHANGE_SOAP_NAMESPACE,
                                               'getMUBetsResponse')[0]
            
        tag = self.node.getElementsByTagName

        self.header = APIResponseHeader(tag('header')[0])
        
        # bets (might be null)
        bets = tag('bets')[0]
        self.bets = bets.hasChildNodes() \
            and [ MUBet(node) for node in bets.childNodes ] \
            or []
            
        self.errorCode = tag('errorCode')[0].childNodes[0].nodeValue
        
        # minor error code (might be null)
        minorErrorCode = tag('minorErrorCode')[0]
        self.minorErrorCode = minorErrorCode.hasChildNodes() \
            and minorErrorCode.childNodes[0].nodeValue \
            or None
            
        self.totalRecordCount = int(tag('totalRecordCount')[0] \
            .childNodes[0].nodeValue)
       
    def __repr__(self):
        """Returns formatted XML representing the object."""
        return self.node.toprettyxml()
        
    def __str__(self):
        return '''GetMUBetsResp
            header: %s
            totalRecordCount: %i
            bets: %s
            errorCode: %s
            ''' % (str(self.header), self.totalRecordCount, \
                    [ str(bet) for bet in self.bets ], \
                    self.errorCode)
                    
class GetMarketProfitAndLossResp:
    
    """Encapsulates a getMarketProfitAndLoss response from the API.
    
    Attributes:
        header              -- APIResponseHeader
        annotations         -- list of ProfitAndLoss
        commissionApplied   -- commission rate applied to the P&L numbers. If 0,
                               this implies that no commission has been deducted
                               from the P&L returned.
        currencyCode        -- currency for all amounts returned (this is the
                               account currency)
        errorCode           -- if not 'OK', indicates a non service specific 
                               error has occurred. See below.
        includesSettledBets -- True if and only if any settled bets are included 
                               in the P&L position (regardless of the Settled 
                               Bets input)
        marketId            -- The market ID for which the profit and loss for 
                               the user is to be returned
        marketName          -- name of the market
        marketStatus        -- status of the market        
        minorErrorCode      -- reserved for future use - currently always null

    Error codes:
        API_ERROR
            General API Error
        INVALID_MARKET_ID
            Market ID is negative or does not exist
        UNSUPPORTED_MARKET_TYPE
            Profit/Loss calculations are only currently supported for Odds and Asian Handicap markets
        MARKET_CLOSED
            The specified market is closed
            
    """

    def __init__(self, doc):
        """Initialise a new instance.
        
        doc -- the Xml doc to initialise from
        
        """
        
        # store the xml in case we want to see the raw data
        self.node = doc.getElementsByTagNameNS(_EXCHANGE_SOAP_NAMESPACE,
                                           'getMarketProfitAndLossResponse')[0]
            
        tag = self.node.getElementsByTagName

        self.header = APIResponseHeader(tag('header')[0])
        
        # annotations (might be null)
        annotations = tag('annotations')[0]
        self.annotations = annotations.hasChildNodes() \
            and [ ProfitAndLoss(node) for node in annotations.childNodes ] \
            or []
            
        self.commissionApplied = float(tag('commissionApplied')[0] \
            .childNodes[0].nodeValue)
        self.currencyCode = tag('currencyCode')[0].childNodes[0].nodeValue
        self.errorCode = tag('errorCode')[0].childNodes[0].nodeValue
        self.includesSettledBets = tag('includesSettledBets')[0] \
            .childNodes[0].nodeValue == "true"
        self.marketId = int(tag('marketId')[0].childNodes[0].nodeValue)
        self.marketName = tag('marketName')[0].childNodes[0].nodeValue
        self.marketStatus = tag('marketStatus')[0].childNodes[0].nodeValue
        
        # minor error code (might be null)
        minorErrorCode = tag('minorErrorCode')[0]
        self.minorErrorCode = minorErrorCode.hasChildNodes() \
            and minorErrorCode.childNodes[0].nodeValue \
            or None
            
        self.unit = tag('unit')[0].childNodes[0].nodeValue
            
    def __repr__(self):
        """Returns formatted XML representing the object."""
        return self.node.toprettyxml()
        
    def __str__(self):
        return '''GetMarketProfitAndLossResp
            header: %s
            annotations: %s
            errorCode: %s
            ''' % (str(self.header), [ str(pl) for pl in self.annotations ], \
                    self.errorCode)
                    
class KeepAliveResp:
    
    """Encapsulates a keepAlive response from the API.
    
    Attributes:
        header         -- APIResponseHeader
        apiVersion     -- list of ProfitAndLoss
        minorErrorCode -- reserved for future use - currently always null
                               
    """
    
    def __init__(self, doc):
        """Initialise a new instance.
        
        doc -- the Xml doc to initialise from
        
        """
        
        # store the xml in case we want to see the raw data
        self.node = doc.getElementsByTagNameNS(_GLOBAL_SOAP_NAMESPACE,
                                               'keepAliveResponse')[0]
            
        tag = self.node.getElementsByTagName

        self.header = APIResponseHeader(tag('header')[0])
        
        # api version (might be null)
        apiVersion = tag('apiVersion')[0]
        self.apiVersion = apiVersion.hasChildNodes() \
            and apiVersion.childNodes[0].nodeValue \
            or None
            
        # minor error code (might be null)
        minorErrorCode = tag('minorErrorCode')[0]
        self.minorErrorCode = minorErrorCode.hasChildNodes() \
            and minorErrorCode.childNodes[0].nodeValue \
            or None
            
    def __repr__(self):
        """Returns formatted XML representing the object."""
        return self.node.toprettyxml()
        
    def __str__(self):
        return '''KeepAliveResp
            header: %s
            apiVersion: %s
            ''' % (str(self.header), self.apiVersion)

class GetMarketTradedVolumeResp:
    
    """Encapsulates a getMarketTradedVolume response from the API.
    
    Attributes:
        header         -- APIResponseHeader
        errorCode      -- if not 'OK', indicates a non service specific 
                          error has occurred. See below.
        minorErrorCode -- reserved for future use - currently always null
        priceItems     -- list of VolumeInfo

    Error codes:
        API_ERROR
            General API Error
        NO_RESULTS
            No results where returned for the request arguments
        INVALID_MARKET
            The market ID specified does not exist
        INVALID_RUNNER
            The runner ID specified does not exist
        INVALID_ASIAN_LINE
            The asian line specified does not exist
        MARKET_CLOSED
            Market closed
        MARKET_TYPE_NOT_SUPPORTED
            The specified market ID corresponds to a market that is not 
            supported for this service
        INVALID_CURRENCY
            The currency code is not valid
    
    """

    def __init__(self, doc):
        """Initialise a new instance.
        
        doc -- the Xml doc to initialise from
        
        """
        
        # store the xml in case we want to see the raw data
        self.node = doc.getElementsByTagNameNS(_EXCHANGE_SOAP_NAMESPACE,
                                             'getMarketTradedVolumeResponse')[0]
            
        tag = self.node.getElementsByTagName

        self.header = APIResponseHeader(tag('header')[0])
        self.errorCode = tag('errorCode')[0].childNodes[0].nodeValue
        
        # minor error code (might be null)
        minorErrorCode = tag('minorErrorCode')[0]
        self.minorErrorCode = minorErrorCode.hasChildNodes() \
            and minorErrorCode.childNodes[0].nodeValue \
            or None
            
        # prices (might be null)
        priceItems = tag('priceItems')[0]
        self.priceItems = priceItems.hasChildNodes() \
            and [ VolumeInfo(price) for price in priceItems.childNodes ] \
            or []
    
    def __repr__(self):
        """Returns formatted XML representing the object."""
        return self.node.toprettyxml()
        
    def __str__(self):
        return '''GetMarketTradedVolumeResp
            header: %s
            priceItems: %s
            ''' % (str(self.header), [ str(item) for item in self.priceItems ])

class GetAccountFundsResp:
    
    """Encapsulates a getAccountFunds response from the API.
    
    Attributes:
        header               -- APIResponseHeader
        availbalance         -- current balance less exposure and retained 
                                commission
        balance              -- current balance
        commissionRetain     -- commission potentially due on markets which 
                                have not been fully settled
        creditLimit          -- amount of credit available
        currentBetfairPoints -- total of Betfair Points awarded based on 
                                commissions or implied commissions paid
        expoLimit            -- total exposure allowed
        exposure             -- total funds tied up with current bets
        holidaysAvailable    -- Betfair Holidays to be used to prevent the 
                                weekly decay of Betfair Points. Up to 4 maximum
        minorErrorCode       -- reserved for future use - currently always null
        nextDiscount         -- rate applied towards the Market Base Rate which 
                                determines level of commission paid in a market
        withdrawBalance      -- balance available for withdrawal

    Error codes:
        API_ERROR
            General API Error
            
    """
    
    def __init__(self, doc):
        """Initialise a new instance.
        
        doc -- the Xml doc to initialise from
        
        """
        
        # store the xml in case we want to see the raw data
        self.node = doc.getElementsByTagNameNS(_EXCHANGE_SOAP_NAMESPACE,
                                               'getAccountFundsResponse')[0]
            
        tag = self.node.getElementsByTagName

        self.header = APIResponseHeader(tag('header')[0])
        self.errorCode = tag('errorCode')[0].childNodes[0].nodeValue
        self.availBalance = float(tag('availBalance')[0] \
            .childNodes[0].nodeValue)
        self.balance = float(tag('balance')[0].childNodes[0].nodeValue)
        self.commissionRetain = float(tag('commissionRetain')[0] \
            .childNodes[0].nodeValue)
        self.creditLimit = float(tag('creditLimit')[0].childNodes[0].nodeValue)
        self.currentBetfairPoints = int(tag('currentBetfairPoints')[0] \
            .childNodes[0].nodeValue)
        self.expoLimit = float(tag('expoLimit')[0].childNodes[0].nodeValue)
        self.exposure = float(tag('exposure')[0].childNodes[0].nodeValue)
        self.holidaysAvailable = int(tag('holidaysAvailable')[0] \
            .childNodes[0].nodeValue)
        
        # minor error code (might be null)
        minorErrorCode = tag('minorErrorCode')[0]
        self.minorErrorCode = minorErrorCode.hasChildNodes() \
            and minorErrorCode.childNodes[0].nodeValue \
            or None
            
        self.nextDiscount = float(tag('nextDiscount')[0] \
            .childNodes[0].nodeValue)
        self.withdrawBalance = float(tag('withdrawBalance')[0] \
            .childNodes[0].nodeValue)
            
    def __repr__(self):
        """Returns formatted XML representing the object."""
        return self.node.toprettyxml()
        
    def __str__(self):
        return '''GetAccountFundsResp
            header: %s
            availBalance %.2f, exposure %.2f
            ''' % (str(self.header), self.availBalance, self.exposure)
        
class GetSubscriptionInfoResp:
    
    """Encapsulates a getAccountFunds response from the API.
    
    Attributes:
        header         -- APIResponseHeader
        minorErrorCode -- reserved for future use - currently always null
        subscription   -- list of Subscription

    Error codes:
        API_ERROR
            General API Error
            
    """
    
    def __init__(self, doc):
        """Initialise a new instance.
        
        doc -- the Xml doc to initialise from
        
        """
        
        # store the xml in case we want to see the raw data
        self.node = doc.getElementsByTagNameNS(_GLOBAL_SOAP_NAMESPACE,
                                               'getSubscriptionInfoResponse')[0]
            
        tag = self.node.getElementsByTagName

        self.header = APIResponseHeader(tag('header')[0])
        self.errorCode = tag('errorCode')[0].childNodes[0].nodeValue
        
        # minor error code (might be null)
        minorErrorCode = tag('minorErrorCode')[0]
        self.minorErrorCode = minorErrorCode.hasChildNodes() \
            and minorErrorCode.childNodes[0].nodeValue \
            or None
            
        # subscriptions (might be null)
        subscriptions = tag('subscriptions')[0]
        self.subscriptions = subscriptions.hasChildNodes() \
            and [ Subscription(node) for node in subscriptions.childNodes ] \
            or []
            
    def __repr__(self):
        """Returns formatted XML representing the object."""
        return self.node.toprettyxml()
        
    def __str__(self):
        return '''GetSubscriptionInfoResp
            header: %s
            subscriptions: %s
            errorCode: %s
            ''' % (str(self.header), \
                [ str(sub) for sub in self.subscriptions ], self.errorCode)
    
class GetAccountStatementResp:
    
    """Encapsulates a getAccountStatement response from the API.
    
    Attributes:
        header           -- APIResponseHeader
        errorCode        -- if not 'OK', indicates a non service specific 
                            error has occurred. See below.
        items            -- list of AccountStatementItem
        minorErrorCode   -- reserved for future use - currently always null
        totalRecordCount -- total number of records matching the selection 
                            criteria

    Error codes:
        API_ERROR
            General API Error
        INVALID_END_DATE
            End date is not supplied or is invalid
        INVALID_LOCALE_DEFAULTING_TO_ENGLISH
            The locale string was not recognized. Returned results are in 
            English.
        INVALID_RECORD_COUNT
            Max Records < 0 or > 100
        INVALID_START_DATE
            Start date is not supplied or is invalid
        INVALID_START_RECORD
            Start record is not supplied or is invalid
        NO_RESULTS
            No transactions meet the specified criteria
            
    """
    
    def __init__(self, doc):
        """Initialise a new instance.
        
        doc -- the Xml doc to initialise from
        
        """
        
        # store the xml in case we want to see the raw data
        self.node = doc.getElementsByTagNameNS(_EXCHANGE_SOAP_NAMESPACE,
                                               'getAccountStatementResponse')[0]
            
        tag = self.node.getElementsByTagName

        self.header = APIResponseHeader(tag('header')[0])
        
        items = tag('items')[0]
        self.items = items.hasChildNodes() \
            and [ AccountStatementItem(node) for node in items.childNodes ] \
            or []
            
        self.errorCode = tag('errorCode')[0].childNodes[0].nodeValue
        
        # minor error code (might be null)
        minorErrorCode = tag('minorErrorCode')[0]
        self.minorErrorCode = minorErrorCode.hasChildNodes() \
            and minorErrorCode.childNodes[0].nodeValue \
            or None
            
    def __repr__(self):
        """Returns formatted XML representing the object."""
        return self.node.toprettyxml()
        
    def __str__(self):
        return '''GetAccountStatementResp
            header: %s
            items: %s
            errorCode: %s
            ''' % (str(self.header), [ str(item) for item in self.items ], \
                self.errorCode)
    
class GetBetHistoryResp:
    
    """Encapsulates a getBetHistory response from the API.
    
    Attributes:
        header           -- APIResponseHeader
        betHistoryItems  -- list of Bet
        errorCode        -- if not 'OK', indicates a non service specific 
                            error has occurred. See below.
        minorErrorCode   -- reserved for future use - currently always null
        totalRecordCount -- total number of records matching the selection 
                            criteria

    Error codes:
        API_ERROR
            General API Error
        INVALID_BET_STATUS
            Bet Status is not supplied
        INVALID_EVENT_TYPE_ID
            Event Types not supplied
        INVALID_LOCAL_DEFAULTING_TO_ENGLIGH
            The language string was not recognised
        INVALID_MARKET_TYPE
            Market Types is not supplied
        INVALID_ORDER_BY
            Order is not supplied
        INVALID_RECORD_COUNT
            Max Records < 0 or > 100
        INVALID_START_RECORD
            Start record is not supplied or is invalid
        NO_RESULTS
            No bets meet the specified criteria   
            
    """
    
    def __init__(self, doc):
        """Initialise a new instance.
        
        doc -- the Xml doc to initialise from
        
        """
        
        # store the xml in case we want to see the raw data
        self.node = doc.getElementsByTagNameNS(_EXCHANGE_SOAP_NAMESPACE,
                                               'getBetHistoryResponse')[0]
            
        tag = self.node.getElementsByTagName

        self.header = APIResponseHeader(tag('header')[0])
        self.errorCode = tag('errorCode')[0].childNodes[0].nodeValue
        
        # betHistoryItems (might be null)
        betHistoryItems = tag('betHistoryItems')[0]
        self.betHistoryItems = betHistoryItems.hasChildNodes() \
            and [ Bet(node) for node in betHistoryItems.childNodes ] \
            or []
            
        self.errorCode = tag('errorCode')[0].childNodes[0].nodeValue
        # minor error code (might be null)
        minorErrorCode = tag('minorErrorCode')[0]
        self.minorErrorCode = minorErrorCode.hasChildNodes() \
            and minorErrorCode.childNodes[0].nodeValue \
            or None
            
        self.totalRecordCount = int(tag('totalRecordCount')[0] \
            .childNodes[0].nodeValue)
       
    def __repr__(self):
        """Returns formatted XML representing the object."""
        return self.node.toprettyxml()
        
    def __str__(self):
        return '''GetBetHistoryResp
            header: %s
            totalRecordCount: %i
            bets: %s
            errorCode: %s
            ''' % (str(self.header), self.totalRecordCount, \
                [ str(bet) for bet in self.betHistoryItems ], \
                self.errorCode)
    
class PlaceBetsResp:
    
    """Encapsulates a placeBets response from the API.
    
    Attributes:
        header           -- APIResponseHeader
        betResults       -- list of BetPlacementResult
        errorCode        -- if not 'OK', indicates a non service specific 
                            error has occurred. See below.
        minorErrorCode   -- reserved for future use - currently always null

    Error codes:
        API_ERROR
            General API Error
        ACCOUNT_CLOSED
            Account is closed - please contact BDP support
        ACCOUNT_SUSPENDED
            Account has been suspended - please contact BDP support
        API_ERROR
            General API error
        AUTHORISATION_PENDING
            Account is pending authorisation. If the PlaceBetsResultEnum is also
            CANNOT_ACCEPT_BET, this means the market is under the Australian 
            Gaming Commission rules and the account holder's identity has not 
            been verified
        BACK_LAY_COMBINATION
            Bets contains a Back and a Lay on the same runner
        BETWEEN_1_AND_60_BETS_REQUIRED
            Number of BetPlacement less than 1 or greater than 60
        DIFFERING_MARKETS
            All bets not all for the same market
        EVENT_CLOSED
            Market has already closed
        EVENT_INACTIVE
            Market is not active
        EVENT_SUSPENDED
            Market is suspended
        FROM_COUNTRY_FORBIDDEN
            Bet origin from a restricted country
        INTERNAL_ERROR
            Internal error occurred
        INVALID_MARKET
            Market ID doesn't exist
        MARKET_TYPE_NOT_SUPPORTED
            Market type is invalid or does not exist
        SITE_UPGRADE
            Site is currently being upgraded
    
    """
    
    def __init__(self, doc):
        """Initialise a new instance.
        
        doc -- the Xml doc to initialise from
        
        """
        
        # store the xml in case we want to see the raw data
        self.node = doc.getElementsByTagNameNS(_EXCHANGE_SOAP_NAMESPACE,
                                               'placeBetsResponse')[0]
            
        tag = self.node.getElementsByTagName

        self.header = APIResponseHeader(tag('header')[0])
        
        betResults = tag('betResults')[0]
        self.betResults = betResults.hasChildNodes() \
            and [ BetPlacementResult(node) for node in betResults.childNodes ] \
            or []
            
        self.errorCode = tag('errorCode')[0].childNodes[0].nodeValue
        
        # minor error code (might be null)
        minorErrorCode = tag('minorErrorCode')[0]
        self.minorErrorCode = minorErrorCode.hasChildNodes() \
            and minorErrorCode.childNodes[0].nodeValue \
            or None
            
    def __repr__(self):
        """Returns formatted XML representing the object."""
        return self.node.toprettyxml()
        
class CancelBetsResp:
    
    """Encapsulates a cancelBets response from the API.
    
    Attributes:
        header           -- APIResponseHeader
        betResults       -- list of CancelBetsResult
        errorCode        -- if not 'OK', indicates a non service specific 
                            error has occurred. See below.
        minorErrorCode   -- reserved for future use - currently always null

    Error codes:
        API_ERROR
            General API Error
        INVALID_MARKET_ID
            The bets were not all from the same market
        INVALID_NUMER_OF_CANCELLATIONS
            Number of bets < 1 or > 40
        MARKET_IDS_DONT_MATCH
            Bet ID does not exist
        MARKET_STATUS_INVALID
            The status of the market is invalid for this action. The market 
            may be suspended or closed
        MARKET_TYPE_NOT_SUPPORTED
            Invalid market type
    
    """
    
    def __init__(self, doc):
        """Initialise a new instance.
        
        doc -- the Xml doc to initialise from
        
        """
        
        # store the xml in case we want to see the raw data
        self.node = doc.getElementsByTagNameNS(_EXCHANGE_SOAP_NAMESPACE,
                                               'cancelBetsResponse')[0]
            
        tag = self.node.getElementsByTagName

        self.header = APIResponseHeader(tag('header')[0])
        
        betResults = tag('betResults')[0]
        self.betResults = betResults.hasChildNodes() \
            and [ CancelBetsResult(node) for node in betResults.childNodes ] \
            or []
            
        self.errorCode = tag('errorCode')[0].childNodes[0].nodeValue
        
        # minor error code (might be null)
        minorErrorCode = tag('minorErrorCode')[0]
        self.minorErrorCode = minorErrorCode.hasChildNodes() \
            and minorErrorCode.childNodes[0].nodeValue \
            or None
            
    def __repr__(self):
        """Returns formatted XML representing the object."""
        return self.node.toprettyxml()
        
class UpdateBetsResp:
    
    """Encapsulates an updateBets response from the API.
    
    Attributes:
        header           -- APIResponseHeader
        betResults       -- list of UpdateBetsResult
        errorCode        -- if not 'OK', indicates a non service specific 
                            error has occurred. See below.
        minorErrorCode   -- reserved for future use - currently always null

    Error codes:
        API_ERROR
            General API Error
        ACCOUNT_CLOSED
            The user's account is closed
        ACCOUNT_PENDING
            The user's account is pending authorisation
        ACCOUNT_SUSPENDED
            The user's account is suspended
        FROM_COUNTRY_FORBIDDEN
            Update request from restricted country
        INVALID_MARKET_ID
            Not used
        INVALID_NUMBER_OF_BETS
            Number of bets not between 0 and 15
        MARKET_STATUS_INVALID
            The status of the market is invalid for this action. The market may 
            be suspended or closed
        MARKET_TYPE_NOT_SUPPORTED
            The market ID supplied refers to a market that is not supported by 
            the API. Currently, this includes Line and Range markets
    
    """
    
    def __init__(self, doc):
        """Initialise a new instance.
        
        doc -- the Xml doc to initialise from
        
        """
        
        # store the xml in case we want to see the raw data
        self.node = doc.getElementsByTagNameNS(_EXCHANGE_SOAP_NAMESPACE,
                                               'updateBetsResponse')[0]
            
        tag = self.node.getElementsByTagName

        self.header = APIResponseHeader(tag('header')[0])
        
        betResults = tag('betResults')[0]
        self.betResults = betResults.hasChildNodes() \
            and [ UpdateBetsResult(node) for node in betResults.childNodes ] \
            or []
            
        self.errorCode = tag('errorCode')[0].childNodes[0].nodeValue
        
        # minor error code (might be null)
        minorErrorCode = tag('minorErrorCode')[0]
        self.minorErrorCode = minorErrorCode.hasChildNodes() \
            and minorErrorCode.childNodes[0].nodeValue \
            or None
            
    def __repr__(self):
        """Returns formatted XML representing the object."""
        return self.node.toprettyxml()
        
class GetBetResp:
    
    """Encapsulates a getBet response from the API.
    
    Attributes:
        header           -- APIResponseHeader
        bet              -- a Bet
        errorCode        -- if not 'OK', indicates a non service specific error 
                            has occurred. See below.

    Error codes:        
        API_ERROR
            General API Error
        BET_ID_INVALID
            Bet ID is invalid or does not exist
        MARKET_TYPE_NOT_SUPPORTED
            Market type is invalid or does not exist
        NO_RESULT

    """

    def __init__(self, doc):
        """Initialise a new instance.
        
        doc -- the Xml doc to initialise from
        
        """
        
        # store the xml in case we want to see the raw data
        self.node = doc.getElementsByTagNameNS(_EXCHANGE_SOAP_NAMESPACE, \
                                               'getBetResponse')[0]
            
        tag = self.node.getElementsByTagName

        self.header = APIResponseHeader(tag('header')[0])
        
        # bet (might be null)
        bet = tag('bet')[0]
        self.bet = bet.hasChildNodes() and Bet(bet) or None
            
        self.errorCode = tag('errorCode')[0].childNodes[0].nodeValue
       
    def __repr__(self):
        """Returns formatted XML representing the object."""
        return self.node.toprettyxml()
        
    def __str__(self):
        return '''GetBetResp
            header: %s
            bet: %s
            errorCode: %s
            ''' % (str(self.header), str(self.bet), self.errorCode)
                    
class EventType:
    
    """Represents an event type (sport, or top-level event) on Betfair.
    
    Attributes:
        id   -- the id of the event type
        name -- the name of the event type
        
    """
    def __init__(self, node):
        # store the xml in case we want to see the raw data
        self.node = node
        
        tag = self.node.getElementsByTagName
        self.id = int(tag('id')[0].childNodes[0].nodeValue)
        self.name = tag('name')[0].childNodes[0].nodeValue
        
    def __repr__(self):
        """Returns formatted XML representing the object."""
        return self.node.toprettyxml()

    def __str__(self):
        return '(%i: %s)' % (self.id, self.name)
        
class BFEvent:
    
    """Represents an event on Betfair.
    
    Attributes:
        eventId     -- the id of the event
        eventName   -- the name of the event
        eventTypeId -- the id of the top-level sport for this event
        menuLevel   -- the depth of the event within the menu
        orderIndex  -- the order in which the event is displayed
        startTime   -- the start time of the event
        timezone    -- the timezone for where the event takes place
        
    """
    def __init__(self, node):
        # store the xml in case we want to see the raw data
        self.node = node
        
        tag = self.node.getElementsByTagName 
                    
        self.eventId = int(tag('eventId')[0].childNodes[0].nodeValue)
        self.eventName = tag('eventName')[0].childNodes[0].nodeValue
        self.eventTypeId = int(tag('eventTypeId')[0].childNodes[0].nodeValue)
        self.menuLevel = int(tag('menuLevel')[0].childNodes[0].nodeValue)
        self.orderIndex = int(tag('orderIndex')[0].childNodes[0].nodeValue)
        self.startTime = _convert_iso_time(
            tag('startTime')[0].childNodes[0].nodeValue)
        self.timezone = tag('timezone')[0].childNodes[0].nodeValue
                    
    def __repr__(self):
        """Returns formatted XML representing the object."""
        return self.node.toprettyxml()
    
    def __str__(self):
        return '(%i, %s)' % (self.eventId, self.eventName)
        
class MarketSummary:
    
    """Contains a subset of information for a market on Betfair.
    
    Attributes:
        eventTypeId -- the id of the top-level sport for this market
        exchangeId  -- the id of the exchange server that hosts this market
        marketId    -- the id of the market
        marketName  -- the name of the market
        marketType  -- (O)dds, (A)sian Handicap
        menuLevel   -- the depth of the market within the menu
        orderIndex  -- the order in which the market is displayed
        startTime   -- the start time of the market
        timezone    -- the timezone for where the market takes place
    """
    def __init__(self, node):
        # store the xml in case we want to see the raw data
        self.node = node
            
        tag = self.node.getElementsByTagName 
                    
        self.eventTypeId = int(tag('eventTypeId')[0].childNodes[0].nodeValue)
        self.exchangeId = int(tag('exchangeId')[0].childNodes[0].nodeValue)
        self.marketId = int(tag('marketId')[0].childNodes[0].nodeValue)
        self.marketName = tag('marketName')[0].childNodes[0].nodeValue
        self.marketType = tag('marketType')[0].childNodes[0].nodeValue
        self.menuLevel = int(tag('menuLevel')[0].childNodes[0].nodeValue)
        self.orderIndex = int(tag('orderIndex')[0].childNodes[0].nodeValue)
        self.startTime = _convert_iso_time(
            tag('startTime')[0].childNodes[0].nodeValue)
        self.timezone = tag('timezone')[0].childNodes[0].nodeValue
        
        # some additional bonus attributes
        self.isHorseRace = _is_horse_race(self.eventTypeId)
        self.isGreyhoundRace = _is_greyhound_race(self.eventTypeId)

    def __repr__(self):
        """Returns formatted XML representing the object."""
        return self.node.toprettyxml()

    def __str__(self):
        return '(%i, %s, %s)' % (self.marketId, 
                                 self.exchangeId == 1 and "UK" or "AUS",
                                 self.marketName)
        
class Market:
    
    """Contains static information for a market on Betfair.
    
    Attributes:
        countryISO3       -- ISO code for the country in which the market takes
                             place
        discountAllowed   -- indicates whether or not the user's discount rate
                             is taken into account on this market. If 'false'
                             all users will be charged the same commission rate,
                             regardless of discount rate
        eventTypeId       -- the id of the top-level sport for this market
        lastRefresh       -- the time the market information was last read from
                             the database, expressed as the number of
                             milliseconds since Jan. 1, 1970 GMT (unix epoch)
        marketBaseRate    -- this will indicate the commission price set for
                             each market
        marketDescription -- the text associated with the market containing
                             market specific information and rules
        marketDisplayTime -- the time used to refer to the market - normally
                             relevant for horse race - e.g. the 3:30 Haydock
        marketId          -- the id of the market
        marketStatus      -- ACTIVE, CLOSED, INACTIVE, SUSPENDED
        marketSuspendTime -- the time the market will next be suspended
        marketTime        -- the expected start time of the market
        marketType        -- (O)dds, (A)sian Handicap
        menuPath          -- the detailed path through the Betfair menu to reach
                             this market
        name              -- the name of the market
        numberOfWinners   -- how many winners there are in this market (e.g. 1
                             for win markets, but 2,3 or 4 for place markets)
        parentEventId     -- id of the parent event type (currently not
                             populated)
        runners           -- details of the runners in the market. Is empty for
                             settled markets
        runnersMayBeAdded -- true if and only if new runners may be subsequently
                             added to the market
        timezone          -- the timezone for where the market takes place
        isHorseRace       -- true if the market is a horse racing market
        isGreyhoundRace   -- true if the market is a greyhound racing market
    """
    def __init__(self, node):
        # store the xml in case we want to see the raw data
        self.node = node
        
        tag = self.node.getElementsByTagName 
                    
        self.countryISO3 = tag('countryISO3')[0].childNodes[0].nodeValue            
        self.discountAllowed = tag('discountAllowed')[0] \
            .childNodes[0].nodeValue == "true"                    
        self.eventTypeId = int(tag('eventTypeId')[0].childNodes[0].nodeValue)
        self.lastRefresh = int(tag('lastRefresh')[0].childNodes[0].nodeValue)
        self.marketBaseRate = float(tag('marketBaseRate')[0] \
            .childNodes[0].nodeValue)
        self.marketDescription = tag('marketDescription')[0] \
            .childNodes[0].nodeValue
        self.displayTime = _convert_iso_time(
            tag('marketDisplayTime')[0].childNodes[0].nodeValue)
        self.marketId = int(tag('marketId')[0].childNodes[0].nodeValue)
        self.marketStatus = tag('marketStatus')[0].childNodes[0].nodeValue
        self.marketSuspendTime = _convert_iso_time(
            tag('marketSuspendTime')[0].childNodes[0].nodeValue)
        self.marketTime = _convert_iso_time(
            tag('marketTime')[0].childNodes[0].nodeValue)
        self.marketType = tag('marketType')[0].childNodes[0].nodeValue            
        self.menuPath = tag('menuPath')[0].childNodes[0].nodeValue            
        self.name = tag('name')[0].childNodes[0].nodeValue
        self.numberOfWinners = int(tag('numberOfWinners')[0] \
            .childNodes[0].nodeValue)
        self.parentEventId = int(tag('parentEventId')[0] \
            .childNodes[0].nodeValue)
        self.runners = [ Runner(node) for node in tag('runners')[0].childNodes ]
        self.runnersMayBeAdded = tag('runnersMayBeAdded')[0] \
            .childNodes[0].nodeValue == "true"                    
        self.timezone = tag('timezone')[0].childNodes[0].nodeValue
        
        # some additional bonus attributes
        self.isHorseRace = _is_horse_race(self.eventTypeId)
        self.isGreyhoundRace = _is_greyhound_race(self.eventTypeId)

    def __repr__(self):
        """Returns formatted XML representing the object."""
        return self.node.toprettyxml()
        
    def __str__(self):
        return '(%i, %s, %s, %s)' % (self.marketId, self.name, \
            self.marketStatus, [ str(runner) for runner in self.runners ])
        
    def findRunner(self, selectionId, asianLineId):
        for runner in self.runners:
            if runner.selectionId == selectionId \
                and runner.asianLineId == asianLineId:
                return runner
    
class Runner:
    
    """Represents a runner in a Betfair market.
    
    Attributes:
        asianLineId         -- id of the selection (this will be the same for 
                               the same selection across markets)
        handicap            -- handicap of the market (applicable to Asian 
                               Handicap markets)
        name                -- runner name
        asianDoubleLineName -- runner name formatted with handicap (only useful
                               for double line AH markets)
        selectionId         -- runner id
        
    """
    def __init__(self, node):
        # store the xml in case we want to see the raw data
        self.node = node
        
        tag = self.node.getElementsByTagName
                    
        self.asianLineId = int(tag('asianLineId')[0].childNodes[0].nodeValue)
        self.handicap = float(tag('handicap')[0].childNodes[0].nodeValue)
        self.name = tag('name')[0].childNodes[0].nodeValue
        
        # only use this attribute for Asian Handicap double line markets
        # where's the MarketTypeVariant enum? 
        self.asianDoubleLineName = \
            _get_double_line_ah_selection_name(self.name, self.handicap)
            
        self.selectionId = int(tag('selectionId')[0].childNodes[0].nodeValue)
            
    def __repr__(self):
        """Returns formatted XML representing the object."""
        return self.node.toprettyxml()
        
    def __str__(self):
        return '(%i-%i, %s)' % (self.asianLineId, self.selectionId, self.name)
        
class MarketPrices:
    
    """Contains dynamic information for a market on Betfair.
    
    Attributes:
        currencyCode    -- three letter ISO 4217 code
        delay           -- the number of seconds delay between submission and a
                           bet actually getting placed. This is greater than 0 
                           if and only if the market is in-play
        discountAllowed -- indicates whether or not the user's discount rate is
                           taken into account on this market. If 'false' all 
                           users will be charged the same commission rate, 
                           regardless of discount rate
        lastRefresh     -- the time the market information was last read from 
                           the database
        marketBaseRate  -- commission price set for each market
        marketId        -- id of the market
        marketInfo      -- the text associated with the market containing market
                           specific information and rules. This part of the text
                           contains dynamic information such as non-runners
        marketStatus    -- ACTIVE, CLOSED, INACTIVE, SUSPENDED
        numberOfWinners -- how many winners there are in this market (e.g. 1
                           for win markets, but 2,3 or 4 for place markets)
        runnerPrices    -- list of RunnerPrices, empty if market is not active
        
    """
    def __init__(self, node):
        # store the xml in case we want to see the raw data
        self.node = node
        
        tag = self.node.getElementsByTagName
        
        self.currencyCode = tag('currencyCode')[0].childNodes[0].nodeValue
        self.delay = int(tag('delay')[0].childNodes[0].nodeValue)
        self.discountAllowed = tag('discountAllowed')[0] \
            .childNodes[0].nodeValue == "true"                    
        self.lastRefresh = int(tag('lastRefresh')[0].childNodes[0].nodeValue)
        self.marketBaseRate = float(tag('marketBaseRate')[0] \
            .childNodes[0].nodeValue)
        self.marketId = int(tag('marketId')[0].childNodes[0].nodeValue)
        
        # info (might be null)
        marketInfo = tag('marketInfo')[0]
        self.marketInfo = marketInfo.hasChildNodes() \
            and marketInfo.childNodes[0].nodeValue \
            or None
        
        self.marketStatus = tag('marketStatus')[0].childNodes[0].nodeValue
        self.numberOfWinners = int(tag('numberOfWinners')[0] \
            .childNodes[0].nodeValue)
        self.runnerPrices = [ RunnerPrices(node) for node \
            in tag('runnerPrices')[0].childNodes ]
        
        # sort runner list
        self.runnerPrices.sort(lambda x,y: x.sortOrder - y.sortOrder)
                
    def getRunnerPrices(self, selectionId, asianLineId=0):
        for runnerPrices in self.runnerPrices:
            if runnerPrices.asianLineId == asianLineId \
                                and runnerPrices.selectionId == selectionId:
                return runnerPrices
        return None
        
    def __repr__(self):
        """Returns formatted XML representing the object."""
        return self.node.toprettyxml()
        
    def __str__(self):
        return '(%i, %s, %s)' % (self.marketId, self.marketStatus, \
            [ str(price) for price in self.runnerPrices ])
            
    def calculateTotalMatched(self):
        return sum([price.totalAmountMatched for price in self.runnerPrices])
        
    def calculateOverrounds(self):
        """
        Calculates the back and lay overrounds for the market.
        
        Returns a (backOverround, layOverround) tuple, e.g. (101.2, 99.8)
        
        """
        # TypeError will be thrown if any of the percentage calculations
        # return None (which will happen if there is no money available for
        # a bet type on a runner)
        try:
            back = sum([ price.backPricePercentage() for price 
                            in self.runnerPrices ])
        except TypeError:
            back = None
        
        try:
            lay = sum([ price.layPricePercentage() for price 
                            in self.runnerPrices ])
        except TypeError:
            lay = None
            
        return (back, lay)
        
class RunnerPrices:
    
    """Represents the prices available on a runner.
    
    Attributes:
        asianLineId        -- id of the selection (this will be the same for the
                              same selection across markets)
        bestPricesToBack   -- best available back prices
        bestPricesToLay    -- best available lay prices
        handicap           -- handicap of the market (applicable to Asian 
                              Handicap markets)
        lastPriceMatched   -- last price at which this selection was matched
        reductionFactor    -- reduction in the odds that applies in case this 
                              runner does not participate
        selectionId        -- id of the selection (this will be the same for the
                              same selection across markets)
        sortOrder          -- order in which the items are displayed on Betfair
        totalAmountMatched -- total amount matched on this selection (regardless
                              of price)
        vacant             -- used to indicate a Vacant Trap for withdrawn 
                              runners in greyhound markets

    """
    def __init__(self, node):
        # store the xml in case we want to see the raw data
        self.node = node
        
        tag = self.node.getElementsByTagName
        
        self.asianLineId = int(tag('asianLineId')[0].childNodes[0].nodeValue)
            
        # back prices (might be null)
        bestPricesToBack = tag('bestPricesToBack')[0]
        self.bestPricesToBack = bestPricesToBack.hasChildNodes() \
            and [ Price(node) for node in bestPricesToBack.childNodes ] \
            or []
        count = len(self.bestPricesToBack)
        while count < 3:
            self.bestPricesToBack.append(Price(depth=count+1, betType="B"))
            count = len(self.bestPricesToBack)
        
        # lay prices (might be null)
        bestPricesToLay = tag('bestPricesToLay')[0]
        self.bestPricesToLay = bestPricesToLay.hasChildNodes() \
            and [ Price(node) for node in bestPricesToLay.childNodes ] \
            or []
        count = len(self.bestPricesToLay)
        while count < 3:
            self.bestPricesToLay.append(Price(depth=count+1, betType="L"))
            count = len(self.bestPricesToLay)
            
        self.handicap = float(tag('handicap')[0].childNodes[0].nodeValue)
        self.lastPriceMatched = float(tag('lastPriceMatched')[0] \
            .childNodes[0].nodeValue)
        self.reductionFactor = float(tag('reductionFactor')[0] \
            .childNodes[0].nodeValue)
        self.selectionId = int(tag('selectionId')[0].childNodes[0].nodeValue)
        self.sortOrder = int(tag('sortOrder')[0].childNodes[0].nodeValue)
        self.totalAmountMatched = float(tag('totalAmountMatched')[0] \
            .childNodes[0].nodeValue)
        self.vacant = tag('vacant')[0].childNodes[0].nodeValue == "true"
            
    def __repr__(self):
        """Returns formatted XML representing the object."""
        return self.node.toprettyxml()
        
    def __str__(self):
        return '(%i-%i, backPrices %s, layPrices %s)' % \
            (self.asianLineId, self.selectionId, \
            [ str(price) for price in self.bestPricesToBack ], \
            [ str(price) for price in self.bestPricesToLay ])
            
    def backPricePercentage(self):
        """Return the best available back price as a percentage chance of the 
        runner being settled as a winner.
        
        For example, if the best available back price is 1.01, the percentage
        is calculated as 100/1.01 == 99% chance of victory. Returns 0 if
        there is no money available to back.
        
        """
        if self.bestPricesToBack[0].amountAvailable == 0: return 0
        else: return 100 / self.bestPricesToBack[0].price
        
    def layPricePercentage(self):
        """Return the best available lay price as a percentage chance of the 
        runner being settled as a winner.
        
        For example, if the best available lay price is 5, the percentage
        is calculated as 100/5 == 20% chance of victory. Returns 0 if there 
        is no money available to lay
        
        """
        if self.bestPricesToLay[0].amountAvailable == 0: return 0
        else: return 100 / self.bestPricesToLay[0].price
        
class Price:
    
    """Represents a single price (back or lay) on a runner.
    
    Attributes:
        amountAvailable -- amount available at the odds specified.
        betType         -- (B)ack or (L)ay
        depth           -- the order, from best to worst, of the price (1 is 
                           best available, 3 is the worst)
        price           -- odds

    """
    def __init__(self, node=None, betType="B", depth=1):
        # store the xml in case we want to see the raw data
        self.node = node
        
        if node:
            tag = self.node.getElementsByTagName
            
            self.amountAvailable = float(tag('amountAvailable')[0] \
                .childNodes[0].nodeValue)
            self.betType = tag('betType')[0].childNodes[0].nodeValue
            self.depth = int(tag('depth')[0].childNodes[0].nodeValue)
            self.price = float(tag('price')[0].childNodes[0].nodeValue)
        else:
            self.amountAvailable = 0.0
            self.betType = betType
            self.depth = depth
            self.price = 0.0
            
    def __repr__(self):
        """Returns formatted XML representing the object."""
        if self.node:
            return self.node.toprettyxml()
        else: return ""
            
    def __str__(self):
        return '(%.2f @ %.2f)' % (self.amountAvailable, self.price)
        
class Bet:
    """Represents a single bet on Betfair.
    
    Attributes:
        asianLineId    -- id of the specific Asian handicap line
        avgPrice       -- average matched price of the bet (null if no part has
                          been matched)
        betId          -- unique identifier generated for every bet placement
        betStatus      -- (C)ancelled, (L)apsed, (M)atched, (S)ettled, 
                          (U)nmatched, (V)oided
        betType        -- (B)ack or (L)ay
        cancelledDate  -- date and time that the bet was cancelled (null if not
                          applicable)
        lapsedDate     -- date and time that the bet was lapsed (null if not 
                          applicable)
        marketId       -- id of the market
        marketName     -- name of the market
        marketType     -- (O)dds or (A)sian Handicap
        matchedDate    -- date and time that the bet was matched (null if not 
                          applicable)
        matchedSize    -- amount matched
        matches        -- list of Match (only if detailed set to true in 
                          request)
        placedDate     -- date and time of bet placement
        price          -- price of the remaining bet
        profitAndLoss  -- net result of bet
        selectionId    -- id of the selection (this will be the same for the 
                          same selection across markets)
        selectionName  -- name of the selection
        settledDate    -- date and time of bet settlement
        remainingSize  -- remaining unmatched, lapsed or cancelled amount of the
                          bet
        requestedSize  -- original stake amount of the bet
        voidedDate     -- date and time that the bet was voided (null if not 
                          applicable)

    """
    def __init__(self, node):
        # store the xml in case we want to see the raw data
        self.node = node
        
        tag = self.node.getElementsByTagName
        
        self.asianLineId = int(tag('asianLineId')[0].childNodes[0].nodeValue)
        self.avgPrice = float(tag('avgPrice')[0].childNodes[0].nodeValue)
        self.betId = int(tag('betId')[0].childNodes[0].nodeValue)
        self.betStatus = tag('betStatus')[0].childNodes[0].nodeValue
        self.betType = tag('betType')[0].childNodes[0].nodeValue
        self.cancelledDate = _convert_iso_time(
            tag('cancelledDate')[0].childNodes[0].nodeValue)
        self.lapsedDate = _convert_iso_time(
            tag('lapsedDate')[0].childNodes[0].nodeValue)
        self.marketId = int(tag('marketId')[0].childNodes[0].nodeValue)
        self.marketName = tag('marketName')[0].childNodes[0].nodeValue
        self.marketType = tag('marketType')[0].childNodes[0].nodeValue
        self.matchedDate = _convert_iso_time(
            tag('matchedDate')[0].childNodes[0].nodeValue)
        self.matchedSize = float(tag('matchedSize')[0].childNodes[0].nodeValue)
        
        # detailed match info (might be null)
        matches = tag('matches')[0]
        self.matches = matches.hasChildNodes() \
            and [ Match(node) for node in matches.childNodes ] \
            or []
        
        self.placedDate = _convert_iso_time(
            tag('placedDate')[0].childNodes[0].nodeValue)
        self.price = float(tag('price')[0].childNodes[0].nodeValue)
        self.profitAndLoss = float(tag('profitAndLoss')[0] \
            .childNodes[0].nodeValue)
        self.selectionId = int(tag('selectionId')[0].childNodes[0].nodeValue)
        self.selectionName = tag('selectionName')[0].childNodes[0].nodeValue
        self.settledDate = _convert_iso_time(
            tag('settledDate')[0].childNodes[0].nodeValue)
        self.remainingSize = float(tag('remainingSize')[0] \
            .childNodes[0].nodeValue)
        self.requestedSize = float(tag('requestedSize')[0] \
            .childNodes[0].nodeValue)
        self.voidedDate = _convert_iso_time(
            tag('voidedDate')[0].childNodes[0].nodeValue)
        
    def __repr__(self):
        """Returns formatted XML representing the object."""
        return self.node.toprettyxml()
            
    def __str__(self):
        if self.betStatus == "S":
            return '%i (%i %s %s, %.2f)' % (self.betId, self.marketId,
                        self.betType, self.selectionName, self.profitAndLoss)
                        
        elif self.betStatus in ["M", "U"]:
            return '%i (m%i s%i a%i) %s %s, %.2f @ %.2f' % (self.betId, 
                self.marketId,
                self.selectionId,
                self.asianLineId,
                self.betType,
                self.selectionName,
                self.betStatus == "M" and self.matchedSize \
                    or self.requestedSize,
                self.betStatus == "M" and self.avgPrice \
                    or self.price)
                
        else:
            return '%i (%i %s %s)' % (self.betId, self.marketId, self.betType, 
                                        self.selectionName)
     
class Match:
    """Represents a matched portion of a bet.
    
    Attributes:
        betStatus     -- (C)ancelled, (L)apsed, (M)atched, (S)ettled,
                         (U)nmatched, (V)oided
        matchedDate   -- date and time at the bet portion was matched
        priceMatched  -- price at which this portion was matched
        profitLoss    -- profit/loss on this bet portion (null for unsettled
                         bets)
        settledDate   -- date and time at the bet portion was settled (null for
                         unsettled bets)
        sizeMatched   -- size matched in this portion
        transactionId -- unique identifier for the individual transaction
        voidedDate    -- date and time that the bet was voided (null if not 
                         applicable)

    """
    def __init__(self, node):
        self.node = node
        
        tag = self.node.getElementsByTagName
        
        self.betStatus = tag('betStatus')[0].childNodes[0].nodeValue
        self.matchedDate = _convert_iso_time(
            tag('matchedDate')[0].childNodes[0].nodeValue)
        self.priceMatched = float(tag('priceMatched')[0].childNodes[0].nodeValue)
        self.profitLoss = float(tag('profitLoss')[0].childNodes[0].nodeValue)
        self.settledDate = _convert_iso_time(
            tag('settledDate')[0].childNodes[0].nodeValue)
        self.sizeMatched = float(tag('sizeMatched')[0].childNodes[0].nodeValue)
        self.transactionId = int(tag('transactionId')[0].childNodes[0].nodeValue)
        self.voidedDate = _convert_iso_time(
            tag('voidedDate')[0].childNodes[0].nodeValue)
        
    def __repr__(self):
        """Returns formatted XML representing the object."""
        return self.node.toprettyxml()
        
    def __str__(self):
        return '(%i, %s)' % (self.transactionId, self.betStatus)
        
class MUBet:
    """Represents a matched or unmatched on Betfair.
    
    Attributes:
        asianLineId    -- id of the specific Asian handicap line
        betId          -- unique identifier generated for every bet placement
        betStatus      -- (C)ancelled, (L)apsed, (M)atched, (S)ettled, 
                          (U)nmatched, (V)oided
        betType        -- (B)ack or (L)ay
        marketId       -- id of the market
        matchedDate    -- date and time that the bet was matched (null if not 
                          applicable)
        size           -- value of bet
        placedDate     -- date and time of bet placement
        price          -- bet price
        selectionId    -- id of the selection (this will be the same for the 
                          same selection across markets)
        handicap       -- handicap applied to the selection on which the bet is 
                          placed

    """
    def __init__(self, node):
        # store the xml in case we want to see the raw data
        self.node = node
        
        tag = self.node.getElementsByTagName
        
        self.asianLineId = int(tag('asianLineId')[0].childNodes[0].nodeValue)
        self.betId = int(tag('betId')[0].childNodes[0].nodeValue)
        self.betStatus = tag('betStatus')[0].childNodes[0].nodeValue
        self.betType = tag('betType')[0].childNodes[0].nodeValue
        self.marketId = int(tag('marketId')[0].childNodes[0].nodeValue)
        self.matchedDate = _convert_iso_time(
            tag('matchedDate')[0].childNodes[0].nodeValue)
        self.size = float(tag('size')[0].childNodes[0].nodeValue)
        self.placedDate = _convert_iso_time(
            tag('placedDate')[0].childNodes[0].nodeValue)
        self.price = float(tag('price')[0].childNodes[0].nodeValue)
        self.selectionId = int(tag('selectionId')[0].childNodes[0].nodeValue)
        self.handicap = float(tag('handicap')[0].childNodes[0].nodeValue)
        
    def __repr__(self):
        """Returns formatted XML representing the object."""
        return self.node.toprettyxml()
            
    def __str__(self):
        return '(%i %s %s, %.2f @ %.2f)' % (self.marketId, self.betType,
                                    self.selectionId, self.size,
                                    self.price)
        
class ProfitAndLoss:
    """Represents a profit and loss annotation.
    
    Attributes:
        futureIfWin    -- not used
        ifWin          -- profit and loss assuming this selection were to win
        selectionID    -- the selection ID
        selectionName  -- the selection Name
        worstCaseIfWin -- for Asian Handicap markets, this is the worst outcome
                          possible if the if the selection were to win. This
                          takes unmatched bets into account, e.g. if the 
                          selection were to win, your worst case would be that
                          unmatched back bets lapsed, and unmatched lay bets
                          were taken.
        from_          -- the from value; includes -infinity
        to             -- the to value; includes +infinity

    """
    def __init__(self, node):
        # store the xml in case we want to see the raw data
        self.node = node
        
        tag = self.node.getElementsByTagName
        
        self.futureIfWin = Decimal(tag('futureIfWin')[0].childNodes[0].nodeValue)
        self.ifWin = float(tag('ifWin')[0].childNodes[0].nodeValue)
        self.selectionId = int(tag('selectionId')[0].childNodes[0].nodeValue)
        self.selectionName = tag('selectionName')[0].childNodes[0].nodeValue
        self.worstCaseIfWin = Decimal(tag('worstcaseIfWin')[0] \
            .childNodes[0].nodeValue)
        if len(tag('from')) > 0:
            self.from_ = Decimal(tag('from')[0].childNodes[0].nodeValue)
        if len(tag('to')) > 0:
            self.to = Decimal(tag('to')[0].childNodes[0].nodeValue)

    def __repr__(self):
        """Returns formatted XML representing the object."""
        return self.node.toprettyxml()
            
    def __str__(self):
        return '(%i, %s, %.2f)' % (self.selectionId, self.selectionName, \
                                    self.ifWin)
            
    def getDoubleLineFormattedString(self, unit):
        """Appropriately formats the annotation for double line markets.
        
        Example usage:
            pl = proxy.getMarketProfitAndLoss(session, myAHMarketID)
            print "If %s: " % (pl.annotations[0].selectionName)
            for annotation in pl.annotations:
                print "    %s: %.2f" % (
                    annotation.getDoubleLineFormattedString(pl.unit),
                    annotation.ifWin)
                
        Output (assuming a lay bet on Liverpool -2):
            If Liverpool:
                do not win by 2 goals or more: 2.00
                win by 2 goals: 0.00
                win by at least 3 goals: -2.00
                
        """
        return _format_double_line_profit(self.from_, self.to, unit)
        
class VolumeInfo:
    """Represents information about volume of money traded on a selection.
    
    Attributes:
        odds               -- odds on the selection
        totalMatchedAmount -- total amount matched for the given odds
        
    """
    def __init__(self, node):
        # store the xml in case we want to see the raw data
        self.node = node
        
        tag = self.node.getElementsByTagName
        #print tag('odds')
        odds = tag('odds')[0].childNodes[0].nodeValue
        
        # Handle possibility of NaN, introduced by Betfair SP
        if odds == "NaN":
            # On Windows, underlying use of atof breaks if NaN is passed in.
            # The following alternative is recommended
            # http://objectmix.com/python/631451-numpy-handling-float-nan-different-xp-vs-linux.html#post2225180
            self.odds = 1e1000 / 1e1000
        else:
            self.odds = float(odds)
            
        self.totalMatchedAmount = float(tag('totalMatchedAmount')[0] \
            .childNodes[0].nodeValue)
        
    def __repr__(self):
        """Returns formatted XML representing the object."""
        return self.node.toprettyxml()
            
    def __str__(self):
        return '(%.2f @ %.2f)' % (self.totalMatchedAmount, self.odds)
                                    
class Subscription:
    """Represents information on your API subscription.
    
    Attributes:
        billingAmount     -- subscription payment amount
        billingDate       -- next billing date
        billingPeriod     -- WEEKLY, MONTHLY, QUARTERLY, ANNUALLY
        productId         -- product ID
        productName       -- the name of the subscription product
        services          -- list of ServiceCall
        setupChargeActive -- if true there will be a setup charge
        setupCharge       -- amount of setup charge
        status            -- ACTIVE, INACTIVE, SUSPENDED
        subscribedDate    -- date the subscription was enabled
        vatEnabled        -- if true, VAT will be added on top of the billing 
                             amount
                             
    """
    def __init__(self, node):
        self.node = node
        
        tag = self.node.getElementsByTagName
        
        self.billingAmount = float(tag('billingAmount')[0] \
            .childNodes[0].nodeValue)
        self.billingDate = _convert_iso_time(
            tag('billingDate')[0].childNodes[0].nodeValue)
        self.billingPeriod = tag('billingPeriod')[0].childNodes[0].nodeValue
        self.productId = int(tag('productId')[0].childNodes[0].nodeValue)
        self.productName = tag('productName')[0].childNodes[0].nodeValue
        
        # services (might be null)
        services = tag('services')[0]
        self.services = services.hasChildNodes() \
            and [ ServiceCall(node) for node in services.childNodes ] \
            or []
        
        self.setupCharge = float(tag('setupCharge')[0].childNodes[0].nodeValue)
        self.setupChargeActive = tag('setupChargeActive')[0] \
            .childNodes[0].nodeValue == "true"
        self.status = tag('status')[0].childNodes[0].nodeValue
        self.subscribedDate = _convert_iso_time(
            tag('subscribedDate')[0].childNodes[0].nodeValue)
        self.vatEnabled = tag('vatEnabled')[0] \
            .childNodes[0].nodeValue == "true"
        
    def __repr__(self):
        """Returns formatted XML representing the object."""
        return self.node.toprettyxml()
        
    def __str__(self):
        return '(%i %s (%s))' % (self.productId, self.productName, \
            [ str(service) for service in self.services ])

class ServiceCall:
    """Represents information about a service provided by your subscription.
    
    Attributes:
        maxUsages    -- throttle usage amount
        period       -- throttle limit time
        periodExpiry -- throttle expiration date
        serviceType  -- services available in the subscription. See BDP website
                        for up-to-date list of values
        usageCount   -- current usage count
        
    """
    def __init__(self, node):
        self.node = node
        
        tag = self.node.getElementsByTagName
        
        self.maxUsages = int(tag('maxUsages')[0].childNodes[0].nodeValue)
        self.period = int(tag('period')[0].childNodes[0].nodeValue)
        self.periodExpiry = _convert_iso_time(
            tag('periodExpiry')[0].childNodes[0].nodeValue)
        self.serviceType = tag('serviceType')[0].childNodes[0].nodeValue
        self.usageCount = int(tag('usageCount')[0].childNodes[0].nodeValue)
        
    def __repr__(self):
        """Returns formatted XML representing the object."""
        return self.node.toprettyxml()
        
    def __str__(self):
        return self.serviceType
        
class AccountStatementItem:
    """Represents an entry on your account statement.
    
    Attributes:
        accountBalance  -- account balance
        amount          -- the amount won/lost for bets or amount 
                           deposited/withdrawn in the account currency
        avgPrice        -- the average matched price of the bet (null if no 
                           part has been matched)
        betId           -- unique identifier generated for every bet placement
        betSize         -- the amount of the stake of your bet. (0 for 
                           commission payments or deposit/withdrawals)
        betType         -- (B)ack or (L)ay
        commissionRate  -- commission rate on market
        eventId         -- id of the market
        eventTypeId     -- event type
        fullMarketName  -- full market name. For card payment items, this field
                           contains the card name
        grossBetAmount  -- gross bet amount
        marketName      -- market name. For card transactions, this field 
                           indicates the type of card transaction (deposit, 
                           deposit fee, or withdrawal).
        marketType      -- (A)sian Handicap, (L)ine, (O)dds, (R)ange. For 
                           account deposits and withdrawals, marketType is set 
                           to NOT_APPLICABLE
        placedDate      -- date and time of bet placement
        selectionId     -- id of the selection (this will be the same for the 
                           same selection across markets)
        selectionName   -- name of the selection
        settledDate     -- date and time at the bet portion was settled
        startDate       -- start date of the market
        transactionType -- OK, RESULT_ERR, RESULT_FIX, RESULT_LOST,
                           RESULT_NOT_APPLICABLE, RESULT_WON
        winLose         -- OK, RESULT_ERR, RESULT_FIX, RESULT_LOST,
                           RESULT_NOT_APPLICABLE, RESULT_WON

    """
    def __init__(self, node):
        # store the xml in case we want to see the raw data
        self.node = node
        
        tag = self.node.getElementsByTagName
        self.accountBalance = float(tag('accountBalance')[0] \
            .childNodes[0].nodeValue)
        self.amount = float(tag('amount')[0].childNodes[0].nodeValue)
        self.avgPrice = float(tag('avgPrice')[0].childNodes[0].nodeValue)
        self.betId = int(tag('betId')[0].childNodes[0].nodeValue)
        self.betSize = float(tag('betSize')[0].childNodes[0].nodeValue)
        self.betType = tag('betType')[0].childNodes[0].nodeValue
        
        commissionRate = tag('commissionRate')[0]
        self.commissionRate = commissionRate.hasChildNodes() \
            and commissionRate.childNodes[0].nodeValue \
            or None
        
        self.eventId = int(tag('eventId')[0].childNodes[0].nodeValue)
        self.eventTypeId = int(tag('eventTypeId')[0].childNodes[0].nodeValue)
        self.fullMarketName = tag('fullMarketName')[0].childNodes[0].nodeValue
        self.grossBetAmount = float(tag('grossBetAmount')[0] \
            .childNodes[0].nodeValue)
        self.marketName = tag('marketName')[0].childNodes[0].nodeValue
        self.marketType = tag('marketType')[0].childNodes[0].nodeValue
        self.placedDate = _convert_iso_time(
            tag('placedDate')[0].childNodes[0].nodeValue)
        self.selectionId = int(tag('selectionId')[0].childNodes[0].nodeValue)
        selectionName = tag('selectionName')[0]
        
        self.selectionName = selectionName.hasChildNodes() \
            and selectionName.childNodes[0].nodeValue \
            or None
        
        self.settledDate = _convert_iso_time(
            tag('settledDate')[0].childNodes[0].nodeValue)
        self.startDate = _convert_iso_time(
            tag('startDate')[0].childNodes[0].nodeValue)
        self.transactionType = tag('transactionType')[0].childNodes[0].nodeValue
        self.winLose = tag('winLose')[0].childNodes[0].nodeValue
        
    def __repr__(self):
        """Returns formatted XML representing the object."""
        return self.node.toprettyxml()
    
    def __str__(self):
        return '%s, %s, %s' % (self.fullMarketName, self.selectionName, \
            self.winLose)
            
class PlaceBet:
    """Represents information about a bet you wish to place.
    
    Attributes:
        asianLineId -- id of the Asian Handicap market to place bets on. Set 
                       to 0 for non-Asian handicap Markets
        betType     -- (B)ack or (L)ay
        marketId    -- id of the market to place the bets on
        price       -- odds you want to set for the bet
        selectionId -- id of desired selection within the market
        size        -- amount of the bet

    """
    def __init__(self, asianLineId, selectionId, marketId, betType, \
                    price, size):
        self.asianLineId = asianLineId
        self.selectionId = selectionId
        self.marketId = marketId
        self.betType = betType
        self.price = price
        self.size = size

class UpdateBets:
    """Represents information about a bet you wish to update.
    
    Attributes:
        betId    -- id of the bet you wish to modify
        newPrice -- new price of bet
        newSize  -- new stake of bet
        oldPrice -- original (current) price of bet
        oldSize  -- original (current) stake of bet

    """
    def __init__(self, betId, newPrice, newSize, oldPrice, oldSize):
        self.betId = betId
        self.newPrice = newPrice
        self.newSize = newSize
        self.oldPrice = oldPrice
        self.oldSize = oldSize

class BetPlacementResult:
    """Represents the result of an attempt to place a bet.
    
    Attributes:
        averagePriceMatched -- average price taken
        betId               -- unique identifier for the bet
        resultCode          -- further information about the success or failure
                               of the bet. See BDP website for up-to-date list
                               of values
        sizeMatched         -- amount that got matched
        success             -- true if bet successfully placed
        
    """
    def __init__(self, node):
        self.node = node
        
        tag = self.node.getElementsByTagName
        
        self.averagePriceMatched = float(tag('averagePriceMatched')[0] \
            .childNodes[0].nodeValue)
        self.betId = int(tag('betId')[0].childNodes[0].nodeValue)
        self.resultCode = tag('resultCode')[0].childNodes[0].nodeValue
        self.sizeMatched = float(tag('sizeMatched')[0].childNodes[0].nodeValue)
        self.success = tag('success')[0].childNodes[0].nodeValue == "true"
        
    def __repr__(self):
        """Returns formatted XML representing the object."""
        return self.node.toprettyxml()

class CancelBetsResult:
    """Represents the result of an attempt to cancel a bet.
    
    Attributes:
        betId         -- unique bet identifier
        resultCode    -- further information about the success or failure of the
                         bet cancellation. See BDP website for up-to-date list
                         of values
        sizeCancelled -- amount cancelled
        sizeMatched   -- amount of original bet matched since placement
        success       -- if true the bet was successfully cancelled
        
    """
    def __init__(self, node):
        self.node = node
        
        tag = self.node.getElementsByTagName
        
        self.betId = int(tag('betId')[0].childNodes[0].nodeValue)
        self.resultCode = tag('resultCode')[0].childNodes[0].nodeValue
        self.sizeCancelled = float(tag('sizeCancelled')[0] \
            .childNodes[0].nodeValue)
        self.sizeMatched = float(tag('sizeMatched')[0].childNodes[0].nodeValue)
        self.success = tag('success')[0].childNodes[0].nodeValue == "true"
        
    def __repr__(self):
        """Returns formatted XML representing the object."""
        return self.node.toprettyxml()

class UpdateBetsResult:
    """Represents the result of an attempt to update a bet.
    
    Attributes:
        betId         -- original bet identifier
        newPrice      -- new odds requested
        newBetId      -- id of any new bet created by update. Only if stake 
                         increased or odds changed otherwise set to 0
        newSize       -- if new bet has been created, the size (stake) of the 
                         new bet
        resultCode    -- further information about the success or failure of 
                         the bet edit. See BDP website for up-to-date list of 
                         values
        sizeCancelled -- any amount of the original bet cancelled as a result 
                         of the update request
        success       -- true if bet edit was successful

    """
    def __init__(self, node):
        self.node = node
        
        tag = self.node.getElementsByTagName
        
        self.betId = int(tag('betId')[0].childNodes[0].nodeValue)
        self.newPrice = float(tag('newPrice')[0].childNodes[0].nodeValue)
        self.newBetId = int(tag('newBetId')[0].childNodes[0].nodeValue)
        self.newSize = float(tag('newSize')[0].childNodes[0].nodeValue)
        self.resultCode = tag('resultCode')[0].childNodes[0].nodeValue
        self.sizeCancelled = float(tag('sizeCancelled')[0].childNodes[0].nodeValue)
        self.success = tag('success')[0].childNodes[0].nodeValue == "true"
        
    def __repr__(self):
        """Returns formatted XML representing the object."""
        return self.node.toprettyxml()

class MarketDisplayDetail:
    """Represents additional information about runners, such as silks.

    Attributes:
        marketId        -- the market
        racingSilks     -- list of extra runner information

    """
    def __init__(self, node):
        self.node = node

        tag = self.node.getElementsByTagName

        self.marketId = int(tag('marketId')[0].childNodes[0].nodeValue)
        
        racingSilks = tag('racingSilks')[0]
        if racingSilks.hasChildNodes():
            if len(tag('sire')) != 0:
                # we have a v2 silk
                self.racingSilks = [ RacingSilkV2(silk) for silk in racingSilks.childNodes ]
            else:
                # normal silk
                self.racingSilks = [ RacingSilk(silk) for silk in racingSilks.childNodes ]
        else:
            self.racingSilks = []

    def __repr__(self):
        """Returns formatted XML representing the object."""
        return self.node.toprettyxml()

class RacingSilk(object):
    """Represents additional information about a single runner.

    Attributes:
        selectionId     -- the selection ID of the runner
        silksURL        -- the path to the silks graphic
        silksText       -- textual description of jockey silks
        trainerName     -- the trainer of the horse
        ageWeight       -- age/weight (stones-pounds)
        form            -- place information for recent races
        daysSince       -- days since horse last ran
        jockeyClaim     -- the jockey's claim
        saddleCloth     -- number on saddle
        stallDraw       -- starting stall

    """
    def __init__(self, node):
        self.node = node

        tag = self.node.getElementsByTagName

        self.selectionId = int(tag('selectionId')[0].childNodes[0].nodeValue)
        self.silksURL = tag('silksURL')[0].childNodes[0].nodeValue
        self.silksText = tag('silksText')[0].childNodes[0].nodeValue
        self.trainerName = tag('trainerName')[0].childNodes[0].nodeValue
        self.ageWeight = tag('ageWeight')[0].childNodes[0].nodeValue
        self.form = tag('form')[0].childNodes[0].nodeValue
        self.daysSince = tag('daysSince')[0].childNodes[0].nodeValue
        self.jockeyClaim = tag('jockeyClaim')[0].childNodes[0].nodeValue
        self.saddleCloth = tag('saddleCloth')[0].childNodes[0].nodeValue
        self.stallDraw = tag('stallDraw')[0].childNodes[0].nodeValue

    def __repr__(self):
        """Returns formatted XML representing the object."""
        return self.node.toprettyxml()

class RacingSilkV2(RacingSilk):
    def __init__(self, node):
        RacingSilk.__init__(self, node)

        tag = self.node.getElementsByTagName

        self.jockeyName = extract(tag('jockeyName'))
        self.colour = extract(tag('colour'))
        self.sex = extract(tag('sex'))
        self.forecastPriceDenominator = \
            int(extract(tag('forecastPriceDenominator')))
        self.forecastPriceNumerator = \
            int(extract(tag('forecastPriceNumerator')))
        self.officialRating = int(extract(tag('officialRating')))
        self.sire = Breeding(tag('sire')[0])
        self.dam = Breeding(tag('dam')[0])
        self.damSire = Breeding(tag('damSire')[0])

class Breeding:
    def __init__(self, node):
        self.node = node
        tag = self.node.getElementsByTagName

        self.name = extract(tag('name'))
        self.bred = extract(tag('bred'))
        self.yearBorn = extract(tag('yearBorn'))

    def __repr__(self):
        return self.node.toprettyxml()

def extract(tag):
    return tag[0].childNodes[0].nodeValue

def _selftest():
    import doctest
    doctest.testmod()
   
def _formatOutput(apiEntity, outputFormat):
    if outputFormat == "xml":
        return apiEntity.node.toprettyxml()
    elif outputFormat == "soap":
        return apiEntity.doc.toprettyxml()
        
if __name__ == "__main__":
    usage = "Usage: pybetfair -umybetfairusername [OPTIONS]"
    shorthelp = "Try `pybetfair --help' for more information."
    longhelp = """Run test suite against Betfair API.
Example: pybetfair -umybetfairusername --testInternal -v

    -h, --help                                  display help
    -v, --verbose                               output progress information. Use multiple
                                                times (up to 3) to increase output detail
        --debuglevel=LEVEL                      1 to display http wiredump
        
    -z, --gzip                                  use gzip compression
    -u, --username=USERNAME                     login with USERNAME
        --productId=ID                          login with product ID
        --hostname=HOSTNAME                     the hostname to connect to (e.g. live api
                                                or testbed if you have access)
        --url=PATH                              the path to the SOAP endpoint on the
                                                required host
        --https=ON                              set 1 to use https
        
        --getEventTypes                         perform getEventTypes request and print
        --getEvents=ID                          perform getEvents for parent event ID
                                                and print
        --getMarket=ID                          perform getMarket for market ID and print
        --getSilks=ID                           perform getSilks for market ID and print
        --getSilksV2=ID                         perform getSilksV2 for market ID and print
        --getMarketPrices=ID                    perform getMarketPrices for market ID and
                                                print
        --getMarketPricesCompressed=ID          perform getMarketPricesCompressed for
                                                market ID and print
        --getCompleteMarketPricesCompressed=ID  perform getCompleteMarketPricesCompressed for
                                                market ID and print
        --getCurrentBets=STATUS                 perform getCurrentBets for STATUS (M or U)
                                                and print
        --getMUBets                             perform getMUBets and print
        --getBetHistory=EVENT_TYPE              perform getBetHistory for EVENT_TYPE and
                                                print
        --getMarketTradedVolume=ID              perform getMarketTradedVolume for market ID
                                                and print
        --getAccountFunds                       perform getAccountFunds and print
        --getSubscriptionInfo                   perform getSubscriptionInfo and print
        --keepAlive                             perform keepAlive and print
        --getMarketProfitAndLoss=ID             perform getMarketProfitAndLoss for
                                                market ID and print
        --getBet=ID                             perform getBet for ID and print
        
        --testInternal                          run internal unit tests. Use with -v to
                                                see detailed results"""
                                    
    import sys, getopt, os
    
    # debugging
    verbose = 0
    debuglevel = 0
    
    # account details
    username = None
    password = None
    productId = 82
    globalHost = 'api.betfair.com'
    exchangeHostUK = 'api.betfair.com'
    exchangeHostAUS = 'api-au.betfair.com'
    globalUrlPath = '/global/v3/BFGlobalService'
    exchangeUrlPath = '/exchange/v5/BFExchangeService'
    useHTTPS = True
    useCompression=False
    
    # output
    outputFormat = "xml"
    
    # service tests
    getEventTypes = False
    getEvents = 0
    getMarket = 0
    getSilks = 0
    getSilksV2 = 0
    getMarketPrices = 0
    getMarketPricesCompressed = 0
    getCompleteMarketPricesCompressed = 0
    getCurrentBets = None
    getAccountFunds = False
    getSubscriptionInfo = False
    getBetHistory = 0
    getMUBets = False
    getMarketProfitAndLoss = 0
    getBet = 0
    
    try:
        opts, args = getopt.getopt(sys.argv[1:],
            # shortopts for verbose/username/password/help/gzip/version/output
            "vu:p:hzVo:", 
            [   
                # debugging
                "verbose",
                "debuglevel=",
                "help",
                "version",
                
                # additional options
                "gzip",
                "outputFormat=",
                
                # account details
                "username=",
                "productId=",
                "globalHost=",
                "exchangeHostUK=",
                "exchangeHostAUS=",
                "globalUrl=",
                "exchangeUrl=",
                "https=",

                # services
                "getEventTypes",
                "getEvents=",
                "getMarket=",
                "getSilks=",
                "getSilksV2=",
                "getMarketPrices=",
                "getMarketPricesCompressed=",
                "getCompleteMarketPricesCompressed=",
                "getCurrentBets=",
                "getMUBets",
                "getAccountFunds",
                "getSubscriptionInfo",
                "getBetHistory=",
                "getMarketProfitAndLoss=",
                "getBet=",
                
                # unit tests
                "testInternal",
            ])

    except getopt.GetoptError, ex:
        print ex
        sys.exit(1)
    
    for opt, arg in opts:
        # debugging
        if opt in ("-v", "--verbose"):
            verbose += 1
        elif opt == "-h":
            print usage
            print shorthelp
            sys.exit(0)
        elif opt == "--help":
            print usage
            print longhelp
            sys.exit(0)
        elif opt == "--debuglevel":
            debuglevel = int(arg)
            
        # additional options
        elif opt in ("-z", "--gzip"):
            useCompression = True
        elif opt in ("-V", "--version"):
            print _VERSION
            sys.exit(0)
        elif opt in ("-o", "--outputFormat"):
            outputFormat = arg
                
        # account details
        elif opt in ("-u", "--username"):
            username = arg
        elif opt == "-p":
            password = arg
        elif opt == "--productId":
            productId = int(arg)
        elif opt == "--globalHost":
            globalHost = arg
        elif opt == "--exchangeHostUK":
            exchangeHostUK = arg
        elif opt == "--exchangeHostAUS":
            exchangeHostAUS = arg
        elif opt == "--globalUrl":
            globalUrlPath = arg
        elif opt == "--exchangeUrl":
            exchangeUrlPath = arg
        elif opt == "--https":
            useHTTPS = arg == "1"
            
        # service tests
        elif opt == "--getEventTypes":
            getEventTypes = True
        elif opt == "--getEvents":
            getEvents = int(arg)
        elif opt == "--getMarket":
            getMarket = int(arg)
        elif opt == "--getSilks":
            getSilks = int(arg)
        elif opt == "--getSilksV2":
            getSilksV2 = int(arg)
        elif opt == "--getMarketPrices":
            getMarketPrices = int(arg)
        elif opt == "--getMarketPricesCompressed":
            getMarketPricesCompressed = int(arg)
        elif opt == "--getCompleteMarketPricesCompressed":
            getCompleteMarketPricesCompressed = int(arg)
        elif opt == "--getCurrentBets":
            getCurrentBets = arg
        elif opt == "--getMUBets":
            getMUBets = True
        elif opt == "--getAccountFunds":
            getAccountFunds = True
        elif opt == "--getSubscriptionInfo":
            getSubscriptionInfo = True
        elif opt == "--getBetHistory":
            getBetHistory = int(arg)
        elif opt == "--getMarketProfitAndLoss":
            getMarketProfitAndLoss = int(arg)
        elif opt == "--getBet":
            getBet = int(arg)

        # unit tests
        elif opt == "--testInternal":
            print "self test", opt
            _selftest()
            sys.exit(0)
            
    try:
        homedir = os.environ["USERPROFILE"]
    except:
        from user import home
        homedir = home
        
    if password == None:
        if homedir != None:
            try:
                rcfile = open(os.path.join(homedir, '.betfairrc'))
            except:
                try:
                    rcfile = open(os.path.join(homedir, 'betfairrc'))
                except:
                    rcfile = None
                
            if rcfile != None:
                password = rcfile.readline().rstrip()
                rcfile.close()
                print "Using configured password"
                
        if password == None:
            # get password interactively (stops proc snooping)
            from getpass import getpass
            password = getpass("Enter password: ")
        
    
    # must have at least username and password
    if not username or not password:
        print "Must specify username and password"
        sys.exit(2)
    
    globalProxy = BFGlobalService(debuglevel=debuglevel, hostname=globalHost, 
                        url=globalUrlPath, secure=useHTTPS,
                        compressed=useCompression)
                        
    exchangeUKProxy = BFExchangeService(debuglevel=debuglevel, 
                        hostname=exchangeHostUK, url=exchangeUrlPath,
                        secure=useHTTPS, compressed=useCompression)
        
    exchangeAUSProxy = BFExchangeService(debuglevel=debuglevel, 
                        hostname=exchangeHostAUS, url=exchangeUrlPath,
                        secure=useHTTPS, compressed=useCompression)
        
    # log in, so we can perform requests
    l = globalProxy.login(username, password, productId)
    sessionToken = l.header.sessionToken
    if verbose == 1: print str(l)
    elif verbose > 1:
        print l.__repr__()
        
    if l.errorCode != "OK":
        print "Login failure: %s" % (l.errorCode,)
        sys.exit(3)
    
    if getEventTypes:
        eventTypes = globalProxy.getActiveEventTypes(sessionToken)
        sessionToken = eventTypes.header.sessionToken
        print _formatOutput(eventTypes, outputFormat)

    if getEvents > 0:
        bfEvents = globalProxy.getEvents(sessionToken, getEvents)
        sessionToken = bfEvents.header.sessionToken
        if verbose > 1:
            print bfEvents.__repr__()
        elif verbose == 1: print str(bfEvents)
 
    if getMarket > 0:
        market = exchangeUKProxy.getMarket(sessionToken, getMarket)
        sessionToken = market.header.sessionToken
        if verbose > 1:
            print market.__repr__()
        elif verbose == 1: print str(market)
 
    if getSilks > 0:
        market = exchangeUKProxy.getSilks(sessionToken, [getSilks])
        sessionToken = market.header.sessionToken
        if verbose > 1:
            print market.__repr__()
        elif verbose == 1: print str(market)

    if getSilksV2 > 0:
        market = exchangeUKProxy.getSilksV2(sessionToken, [getSilksV2])
        sessionToken = market.header.sessionToken
        if verbose > 1:
            print market.__repr__()
        elif verbose == 1: print str(market)
 
    if getMarketPrices > 0:
        prices = exchangeUKProxy.getMarketPrices(sessionToken, getMarketPrices)
        sessionToken = prices.header.sessionToken
        if verbose > 1:
            print prices.__repr__()
        elif verbose == 1: print str(prices)

    if getMarketPricesCompressed >0:
        prices = exchangeUKProxy.getMarketPricesCompressed(sessionToken, getMarketPricesCompressed)
        sessionToken = prices.header.sessionToken
        if verbose > 1:
            print prices.__repr__()
        elif verbose == 1: print str(prices)
 
    if getCompleteMarketPricesCompressed >0:
        prices = exchangeUKProxy.getCompleteMarketPricesCompressed(sessionToken, getCompleteMarketPricesCompressed)
        sessionToken = prices.header.sessionToken
        if verbose > 1:
            print prices.__repr__()
        elif verbose == 1: print str(prices)

    if getCurrentBets:
        bets = exchangeUKProxy.getCurrentBets(sessionToken, recordCount=10, \
            betStatus=getCurrentBets, orderBy="PLACED_DATE")
        sessionToken = bets.header.sessionToken
        if verbose > 1:
            print bets.__repr__()
        elif verbose == 1: print str(bets)

    if getMUBets:
        bets = exchangeUKProxy.getMUBets(sessionToken, recordCount=10, \
            betStatus="MU")
        if verbose > 1:
            print bets.__repr__()
        elif verbose == 1: print str(bets)
# 
    # if getAccountFunds:
        # funds = proxy.getAccountFunds(sessionToken)
        # sessionToken = funds.header.sessionToken
        # if verbose > 1:
            # print funds.__repr__()
        # elif verbose == 1: print str(funds)
# 
    # if getSubscriptionInfo:
        # info = proxy.getSubscriptionInfo(sessionToken)
        # sessionToken = info.header.sessionToken
        # if verbose > 1:
            # print info.__repr__()
        # elif verbose == 1: print str(info)
# 
    # if getBetHistory:
        # bets = proxy.getBetHistory(sessionToken, recordCount=10,
            # betTypesIncluded='S', eventTypeIds=[getBetHistory])
        # sessionToken = bets.header.sessionToken
        # if verbose > 1:
            # print bets.__repr__()
        # elif verbose == 1: print str(bets)
 
    if getMarketProfitAndLoss:
        pl = exchangeUKProxy.getMarketProfitAndLoss(sessionToken, getMarketProfitAndLoss)
        sessionToken = pl.header.sessionToken
        if verbose > 1:
            print pl.__repr__()
        elif verbose == 1: print str(pl)
# 
    # if getBet:
        # bet = proxy.getBet(sessionToken, getBet)
        # sessionToken = bet.header.sessionToken
        # if verbose > 1:
            # print bet.__repr__()
        # elif verbose == 1: print str(bet)
# 
    # if useCompression and verbose:
        # print "Downloaded %i bytes, expanded to %i" % \
            # tuple(proxy.compressedDownloadStats)
            
# vim: set ts=4 sw=4 softtabstop=4 smarttab expandtab:
