using System.Collections.Generic;
using Betfair.Net.BFExchange;

namespace Betfair.Net
{
    public class CompleteMarketTradedVolume
    {
        public int SelectionID { get; internal set; }
        public int AsianLineID { get; internal set; }
        public double ActualBSP { get; internal set; }
        public double TotalBspBackMatchedAmount { get; internal set; }
        public double TotalBspLiabilityMatchedAmount { get; internal set; }
        public IEnumerable<VolumeInfo> Prices { get; internal set; }
    }
}