using System.Collections.Generic;
using System.Linq;

namespace BFCompressedParser.Parsers
{
    public static class CompleteMarketPricesParser
    {
        public static CompleteMarketPrices Parse(string priceData)
        {
            // Change any escaped separators with a token (I think only 
            // selection names for removed runners are a potential hit)
            string sanitised = priceData.Sanitize();

            // Split into market data and runner data
            List<string> fields = sanitised.Split(':').ToList();

            // Market info in first field
            string[] marketInfo = fields[0].Split('~');

            // Runner fields from index 1 to end (including removed runners)
            var runners = new List<string>(fields.GetRange(1, fields.Count - 1));

            // Done. Simple or what? :-)
            return new CompleteMarketPrices(marketInfo, runners);
        }
    }
}