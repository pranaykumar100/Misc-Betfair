using BFCompressedParser.Parsers;
using NUnit.Framework;

namespace TestSuite
{
    [TestFixture]
    public class MarketPricesCompressedTests
    {
        [Test]
        public void TestPricesReceivedFromApi()
        {
            const string data = @"21251122~GBP~ACTIVE~0~1~NR\: (EST) <br>2. Hellaga(7.2%,12\:41)~true~5.0~1223311933533~2. Hellaga,16.41,7.2;~N:3392894~0~0.0~~~7.8~false~~~~|18.0~21.81~L~1~10.0~25.0~L~2~4.4~213.0~L~3~|160.0~3.0~B~1~250.0~31.18~B~2~280.0~4.0~B~3~:3112966~1~179.32~2.78~~37.8~false~~~~|2.16~8.96~L~1~2.14~2.51~L~2~2.12~14.5~L~3~|2.78~28.93~B~1~2.8~70.0~B~2~2.92~8.82~B~3~:3392896~2~85.96~4.8~~22.6~false~~~~|2.58~47.31~L~1~2.56~19.2~L~2~2.5~2.0~L~3~|3.5~50.0~B~1~3.6~2.0~B~2~3.95~6.18~B~3~:3392897~3~0.0~~~4.5~false~~~~|17.0~23.28~L~1~16.5~4.3~L~2~13.0~44.0~L~3~|140.0~3.0~B~1~230.0~6.18~B~2~240.0~27.0~B~3~:3392898~4~0.0~~~7.8~false~~~~|9.2~7.09~L~1~9.0~53.0~L~2~7.4~18.1~L~3~|65.0~6.18~B~1~70.0~5.0~B~2~80.0~25.0~B~3~:1409040~5~4.0~5.4~~19.5~false~~~~|4.6~34.21~L~1~4.5~89.99~L~2~2.78~406.0~L~3~|26.0~3.0~B~1~30.0~6.18~B~2~32.0~7.0~B~3~";

            var m = MarketPricesParser.Parse(data);
            var x = m.runnerPrices.Length;
        }
    }
}