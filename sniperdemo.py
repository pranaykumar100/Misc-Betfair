#!/usr/bin/python
# -*- coding: UTF-8 -*-

# Copyright (C) 2006 Russ Gray russgray@shinyhead.me.uk
# 
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.
        
def calculateProfit(runner, divisor, totalStake):
    "Calculates the profit on a runner when the other stakes are subtracted from the return"
    stake = runner['winChance'] / divisor
    return (stake * (runner['odds'] - 1)) - (totalStake - stake)
    
def processRunners(market, prices, excludeOver, verbose):
    overround = 0.0
    totalMatched = 0.0
    hitlist = []
    ignoredRunners = []

    for runnerPrices in prices.marketPrices.runnerPrices:

        totalMatched += runnerPrices.totalAmountMatched

        # can't calculate overround if any runners have
        # nothing unmatched
        if len(runnerPrices.bestPricesToBack) == 0:
            print "Incomplete book"
            overround = 1000
            break
    
        runner = market.findRunner(runnerPrices.selectionId, runnerPrices.asianLineId)
    
        # ignore runner if over the exclude limit
        if runnerPrices.bestPricesToBack[0].price > excludeOver:
            ignoredRunners.append(runner)
            if verbose > 1: 
                print "Ignoring runner with price %.2f" % runnerPrices.bestPricesToBack[0].price
            continue
    
        # save info about runner and add to hitlist
        bestBackPrice = runnerPrices.bestPricesToBack[0]
        winChance = 100 / bestBackPrice.price
    
        hitlist.append({ \
                'runner' : runner, \
                'odds' : bestBackPrice.price, \
                'winChance' : winChance, \
                'available' : bestBackPrice.amountAvailable })
        overround = overround + winChance

    return (hitlist, ignoredRunners, overround, totalMatched)

def calculateBets(hitlist, divisor, totalStake, verbose):
    placeBets = []
    # assume the market has enough money
    moneyIsAvailable = True
    
    for runner in hitlist:
        # alter stake to fit plan dictated by minimum stake
        stake = runner['winChance'] / divisor
    
        # print scenario
        if verbose:
            print "Back %-28s for %11.2f @ %6.2f %11.2f avail." \
                % (runner['runner'].name, stake, runner['odds'], runner['available'])
            
        # check market volume - can't snipe if there isn't enough
        # money to accept all our bets
        if stake > runner['available']:
            moneyIsAvailable = False
        
        # create the bet if we have enough volume
        if moneyIsAvailable:
            r = runner['runner']
            placeBets.append(PlaceBet(r.asianLineId, r.selectionId, market.marketId, \
                betType, runner['odds'], stake))
                
   # check the least profitable runner is above the specified minimum
    profits = [ calculateProfit(runner, divisor, totalStake) for runner in hitlist ]
    minProfit = min(profits)

    return placeBets, profits, moneyIsAvailable

def snipe(proxy, sessionToken, market, verbose=False):
    # start sniping. Basic algorithm is:
    # 1) get prices
    # 2) calculate overround
    # 3) if overround is further from 100% than the trigger (e.g. 98.9%
    #    with a 1% trigger for back bets) then we have a sniping opportunity
    # 4) calculate stake based on £1 per percent chance of winning (i.e.
    #    £50 on an evens shot)
    # 5) make adjustments according to minimum stake
    # 6) print scenario and total stake required
    headshot = False
    try:
        while not headshot:
            # get prices on specified market, abort on fail
            prices = proxy.getMarketPrices(sessionToken, marketId=market.marketId)
            if prices.errorCode == "OK":
                sessionToken = prices.header.sessionToken
            else:
                print "Failed to get prices - aborting (%s)" % (prices.errorCode,)
                sys.exit(1)
            
            # check market status and react according to user params
            if prices.marketPrices.marketStatus == "SUSPENDED":
                print "Market is suspended"
                if abortOnSuspend: sys.exit(0)
            elif prices.marketPrices.marketStatus == "CLOSED":
                print "Market has closed"
                sys.exit(0)
            elif prices.marketPrices.delay > 0 and not betInPlay:
                print "Market in-play"
                sys.exit(0)
            else:
                # process according to bet type
                if betType == "B":
                    hitlist, ignoredRunners, overround, totalMatched = processRunners(market, prices, excludeOver, verbose)

                    # all runners processed - is there an opportunity to snipe?
                    if 100.0 - triggerMargin >= overround:
                        print 
                        print "*" * 72
                        print "Sniping opportunity found! Overround is %.1f\n" % (overround,)
                        placeBets = []
                        
                        # lowest stake will be on longest shot
                        outsider = min([ runner['winChance'] for runner in hitlist ])
                        divisor = outsider / minimumStake
                        
                        # how much do we need to bet, given the specified minimum stake,
                        # and is the total too high?
                        totalStake = sum( [ runner['winChance'] / divisor for runner in hitlist ])
                        if totalStake > maxTotalStake:
                            print "Could snipe with stake of %.2f, but limited to %.2f" % (totalStake, maxTotalStake)
                        else:
                            placeBets, profits, moneyIsAvailable = calculateBets(hitlist, divisor, totalStake, verbose)
                            minProfit = min(profits)

                            if verbose:
                                if len(ignoredRunners) > 0:
                                    print "Ignoring: ", [ r.name for r in ignoredRunners ]

                            if minProfit < minimumAverageProfit:
                                print "Lowest profit of %.2f below minimum specified %.2f" \
                                    % (minProfit, minimumAverageProfit)
                            else:
                                avgProfit = sum(profits) / len(hitlist)
                                print "\n%.2f required for avg profit of %.2f" % (totalStake, avgProfit)
                                
                                if moneyIsAvailable: 
                                    if liveAmmo:
                                        # OK, take the shot
                                        results = ukProxy.placeBets(sessionToken, placeBets)
                                        if results.errorCode == "OK":
                                            sessionToken = results.header.sessionToken
                                            if verbose: print str(results)
                                        else:
                                            print "Failed to place bets: %s" % (results.errorCode,)
                                            print str(results)
                                    else:
                                        # chicken out
                                        print "Training exercise, aborting"
                                    
                                    # whether we placed bets or not, we're done
                                    headshot = True
                                else:
                                    print "Market lacks volume, won't take the shot"
                    else: 
                        # not this time - pause, and try again
                        if verbose:
                            print "Overround of %.1f%%, trigger at %.2f%%%s, %.2f matched" % (overround, 100.0 - triggerMargin, \
                                prices.marketPrices.delay > 0 and ' (in-play)' or '', totalMatched)
                        
            if not headshot:
                # couldn't snipe this time - pause and try again
                sleep(interval)
    except KeyboardInterrupt:
        pass

if __name__ == "__main__":
    from pybetfair import BFGlobalService, BFExchangeService, PlaceBet
    from time import sleep
    import sys, getopt, os
    
    # login credentials
    username = None
    password = None
    productId = 82
    
    # debugging flags
    verbose = 0
    debuglevel = 0
    
    # sniping rules
    marketId = 0 # the market to monitor
    minimumStake = 2 # minimum stake (Betfair will not allow <2)
    betType = "B" # back or lay
    triggerMargin = 1.0 # 1% anomaly or greater triggers sniper
    interval = 7 # how often to refresh prices and look for under-round
    excludeOver = 1001 # do not include runners with high odds in the book
    maxTotalStake = 50 # do not place bets totalling more than this limiter
    liveAmmo = False # place bets, or just print notification?
    abortOnSuspend = False # quit when the market suspends (e.g. removed runner)
    hostname = 'api.betfair.com' # the server to connect to (defaults to live site)
    useHTTPS = True # encrypt comms (required for live site)
    betInPlay = False # continue sniping during race (bet delay may wreck a shot)
    minimumAverageProfit = 0.01 # must guarantee at least this much profit, otherwise the shot is ignored
    
    try:
        homedir = os.environ["USERPROFILE"]
    except:
        from user import home
        homedir = home
        
    if homedir != None:
        try:
            file = open(os.path.join(homedir, 'betfairrc'))
            password = file.readline().rstrip()
            file.close()
            print "Using configured password"
        except:
            password = None
            
    if password == None:
        # get password interactively (stops proc snooping)
        #print "Enter password:"
        #password = sys.stdin.readline()[:-1]
        from getpass import getpass
        password = getpass("Enter password: ")

    # parse command line
    try:
        opts, args = getopt.getopt(sys.argv[1:],
            "vu:p:m:", # shortopts
            [   
                # debugging
                "verbose",
                "debuglevel=",
                
                # account details
                "username=",
                "productId=",
                "hostname=",
                "https=",

                # sniper settings
                "marketId=",
                "minimumStake=",
                "triggerMargin=",
                "betType=",
                "excludeOver=",
                "maxTotalStake=",
                "liveAmmo",
                "refreshRate=",
                "abortOnSuspend",
                "betInPlay=",
                "minimumAverageProfit=",
            ])

    except getopt.GetoptError, ex:
        print ex
        sys.exit(1)
    
    for opt, arg in opts:
        # debugging
        if opt in ("-v", "--verbose"):
            verbose += 1
        elif opt == "--debuglevel":
            debuglevel = int(arg)
            
        # account details
        elif opt in ("-u", "--username"):
            username = arg
        elif opt == "--productId":
            productId = int(arg)
        elif opt == "--hostname":
            hostname = arg
        elif opt == "--https":
            useHTTPS = (arg == "1")
            
        # sniper settings
        elif opt in ("-m", "--marketId"):
            marketId = int(arg)
        elif opt == "--minimumStake":
            minimumStake = float(arg)
        elif opt == "--triggerMargin":
            triggerMargin = float(arg)
        elif opt == "--betType":
            betType = arg
        elif opt == "--excludeOver":
            excludeOver = float(arg)
        elif opt == "--maxTotalStake":
            maxTotalStake = float(arg)
        elif opt == "--liveAmmo":
            liveAmmo = True
        elif opt == "--refreshRate":
            interval = int(arg)
        elif opt == "--abortOnSuspend":
            abortOnSuspend = True
        elif opt == "--betInPlay":
            betInPlay = (arg == "1")
        elif opt == "--minimumAverageProfit":
            minimumAverageProfit = float(arg)

    if verbose:
        # print preflight report
        print "\nSettings:"
        print "   ", "minimumStake: %.2f" % (minimumStake,)
        print "   ", "triggerMargin: %.2f%%" % (triggerMargin,)
        print "   ", "betType: %s" % (betType,)
        print "   ", "refresh: %i" % (interval,)
        print "   ", "exclude: >%i" % (excludeOver,)
        print "   ", "verbose: %i" % (verbose,)
        print "   ", "abortOnSuspend: %s" % (abortOnSuspend,)
        print "   ", "betInPlay: %s" % (betInPlay,)
        print "   ", "minimumAverageProfit: %s" % (minimumAverageProfit,)
        if liveAmmo:
            print "    liveAmmo: ON, pausing for 5 seconds safety"
            sleep(5)
        else: print "    liveAmmo: OFF, firing blanks"
        
    # must have at least username and market ID
    if not username or marketId == 0:
        print "Must specify username and marketId"
        sys.exit(3)

    # dev settings: api betexb10, exchange betexb58        
    globalProxy = BFGlobalService(debuglevel=debuglevel, hostname=hostname, secure=useHTTPS)
    
    # login to API, abort on fail
    loginResponse = globalProxy.login(username, password, productId)
    if loginResponse.errorCode == "OK":
        sessionToken = loginResponse.header.sessionToken
    else:
        print "Failed to login - aborting (%s)" % (loginResponse.errorCode,)
        sys.exit(1)

    # get specified market, abort on fail
    ukProxy = BFExchangeService(debuglevel=debuglevel, hostname=hostname, secure=useHTTPS)
    marketResponse = ukProxy.getMarket(sessionToken, marketId=marketId)
    if marketResponse.errorCode == "OK":
        sessionToken = marketResponse.header.sessionToken
    else:
        print "Failed to get market - aborting (%s)" % (marketResponse.errorCode,)
        sys.exit(1)

    market = marketResponse.market
    if verbose:
        # print market rundown
        print "\nMarket info:"
        print "    id:", market.marketId
        print "    name:", market.menuPath + market.name
        print "    start:", market.marketTime.isoformat()
        print "    status:", market.marketStatus
        print "    runners:"
        for runner in market.runners:
            print "       ", runner.name
        print
        
    snipe(ukProxy, sessionToken, market, verbose)
