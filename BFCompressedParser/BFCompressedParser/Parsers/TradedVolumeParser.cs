using System.Collections.Generic;
using System.Linq;
using BFCompressedParser.BFExchange;

namespace BFCompressedParser.Parsers
{
    public static class TradedVolumeParser
    {
        public static IEnumerable<CompleteMarketTradedVolume> Parse(string volumeData)
        {
            IEnumerable<string> runnerData = volumeData.Split(':').Where(v => v != string.Empty);

            foreach (string runner in runnerData)
            {
                List<string> fields = runner.Split('|').ToList();
                string[] selectionInfo = fields[0].Split('~');

                double totalBspBackMatchedAmount = double.Parse(selectionInfo[3]);
                double totalBspLiabilityMatchedAmount = double.Parse(selectionInfo[4]);

                yield return
                    new CompleteMarketTradedVolume
                        {
                            SelectionID = int.Parse(selectionInfo[0]),
                            AsianLineID = int.Parse(selectionInfo[1]),
                            ActualBSP = double.Parse(selectionInfo[2]),
                            TotalBspBackMatchedAmount = totalBspBackMatchedAmount,
                            TotalBspLiabilityMatchedAmount = totalBspLiabilityMatchedAmount,
                            Prices =
                                ParseVolumeData(fields.GetRange(1, fields.Count - 1), totalBspBackMatchedAmount,
                                                totalBspLiabilityMatchedAmount),
                        };
            }
        }

        private static IEnumerable<VolumeInfo> ParseVolumeData(IEnumerable<string> volumes, double totalBackMatched,
                                                               double totalLiabilityMatched)
        {
            foreach (string v in volumes)
            {
                string[] fields = v.Split('~');
                yield return new VolumeInfo
                    {
                        odds = double.Parse(fields[0]),
                        totalMatchedAmount = double.Parse(fields[1]),
                        totalBspBackMatchedAmount = totalBackMatched,
                        totalBspLiabilityMatchedAmount = totalLiabilityMatched,
                    };
            }
        }
    }
}