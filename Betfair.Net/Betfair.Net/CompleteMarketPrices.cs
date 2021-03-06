﻿using System.Collections.Generic;
using Betfair.Net.BFExchange;
using Betfair.Net.Parsers;

namespace Betfair.Net
{
    public class CompleteMarketPrices
    {
        internal CompleteMarketPrices(string[] marketInfo, IEnumerable<string> runnerInfo)
        {
            MarketID = int.Parse(marketInfo[0]);
            BetDelay = int.Parse(marketInfo[1]);

            RemovedRunnersString = marketInfo[2];
            RemovedRunners = RemovedRunnerParser.Parse(marketInfo[2]);
            Runners = RunnerPricesParser.Parse(runnerInfo);
        }

        public IEnumerable<RunnerPrices> Runners { get; private set; }
        public IEnumerable<RemovedRunner> RemovedRunners { get; private set; }
        public string RemovedRunnersString { get; private set; }
        public int BetDelay { get; private set; }
        public int MarketID { get; private set; }
    }
}