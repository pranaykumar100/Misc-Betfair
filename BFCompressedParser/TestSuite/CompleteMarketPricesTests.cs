﻿using System.Linq;
using BFCompressedParser.Parsers;
using NUnit.Framework;

namespace TestSuite
{
    [TestFixture]
    public class CompleteMarketPricesTests
    {
        [Test]
        public void TestExampleDataFromApiReferenceDocument()
        {
            const string exampleFromApiReference =
                #region Data

                "20771785~0~:58805~3~11510.72~4.1~~~false~~~~~|1.01~673.36~0.0~0.0~0." +
                "0~1.02~6.75~0.0~0.0~0.0~1.05~2.25~0.0~0.0~0.0~1.1~1.5~0.0~0.0~0.0~1.1" +
                "5~0.75~0.0~0.0~0.0~2.74~11.49~0.0~0.0~0.0~3.05~9.76~0.0~0.0~0.0~3.2~2" +
                "2.0~0.0~0.0~0.0~3.25~22.0~0.0~0.0~0.0~3.3~10.5~0.0~0.0~0.0~3.4~3.75~0" +
                ".0~0.0~0.0~3.45~19.61~0.0~0.0~0.0~3.5~148.44~0.0~0.0~0.0~3.55~200.07~" +
                "0.0~0.0~0.0~3.6~572.77~0.0~0.0~0.0~3.65~407.5~0.0~0.0~0.0~3.7~908.44~" +
                "0.0~0.0~0.0~3.75~42.18~0.0~0.0~0.0~3.8~36.32~0.0~0.0~0.0~3.85~218.56~" +
                "0.0~0.0~0.0~3.9~368.05~0.0~0.0~0.0~3.95~190.42~0.0~0.0~0.0~4.0~643.01" +
                "~0.0~0.0~0.0~4.1~0.0~66.53~0.0~0.0~4.2~0.0~366.57~0.0~0.0~4.3~0.0~9.2" +
                "6~0.0~0.0~4.4~0.0~83.59~0.0~0.0~4.6~0.0~3.0~0.0~0.0~4.8~0.0~3.0~0.0~0" +
                ".0~5.1~0.0~2.66~0.0~0.0~1000.0~0.0~3.75~0.0~0.0~:214217~1~134754.06~1" +
                ".64~~~false~~~~|1.01~679.2~0.0~0.0~0.0~1.02~3.0~0.0~0.0~0.0~1.05~2.25" +
                "~0.0~0.0~0.0~1.1~1.5~0.0~0.0~0.0~1.15~0.75~0.0~0.0~0.0~1.21~95.24~0.0" +
                "~0.0~0.0~1.35~57.14~0.0~0.0~0.0~1.49~3.0~0.0~0.0~0.0~1.5~1.5~0.0~0.0~" +
                "0.0~1.51~75.03~0.0~0.0~0.0~1.53~3.0~0.0~0.0~0.0~1.54~287.78~0.0~0.0~0" +
                ".0~1.56~373.03~0.0~0.0~0.0~1.57~2116.73~0.0~0.0~0.0~1.59~2.0~0.0~0.0~" +
                "0.0~1.6~0.0~0.0~0.0~0.0~1.61~235.77~0.0~0.0~0.0~1.62~174.01~0.0~0.0~0" +
                ".0~1.63~497.31~0.0~0.0~0.0~1.64~83.91~0.0~0.0~0.0~1.65~0.0~1898.95~0." +
                "0~0.0~1.66~0.0~632.86~0.0~0.0~1.67~0.0~786.56~0.0~0.0~1.68~0.0~1378.7" +
                "~0.0~0.0~1.69~0.0~153.38~0.0~0.0~1.7~0.0~10322.87~0.0~0.0~1.71~0.0~18" +
                "52.29~0.0~0.0~1.72~0.0~27753.86~0.0~0.0~1.73~0.0~75.03~0.0~0.0~1.74~0" +
                ".0~502.76~0.0~0.0~1.75~0.0~18.0~0.0~0.0~1.76~0.0~39.45~0.0~0.0~1.77~0" +
                ".0~1326.81~0.0~0.0~1.78~0.0~7.33~0.0~0.0~1.79~0.0~0.0~0.0~0.0~1.8~0.0" +
                "~532.37~0.0~0.0~1.87~0.0~511.29~0.0~0.0~3.0~0.0~7.5~0.0~0.0~1000.0~0." +
                "0~3.0~0.0~0.0~:13362~2~10476.68~6.8~~~false~~~~|1.01~676.1~0.0~0.0~0." +
                "0~1.02~3.0~0.0~0.0~0.0~1.05~2.25~0.0~0.0~0.0~1.1~1.5~0.0~0.0~0.0~1.15" +
                "~0.75~0.0~0.0~0.0~4.4~0.0~0.0~0.0~0.0~4.7~5.41~0.0~0.0~0.0~5.3~7.65~0" +
                ".0~0.0~0.0~5.4~42.07~0.0~0.0~0.0~5.5~89.99~0.0~0.0~0.0~5.6~150.14~0.0" +
                "~0.0~0.0~6.0~98.57~0.0~0.0~0.0~6.2~321.02~0.0~0.0~0.0~6.4~296.48~0.0~" +
                "0.0~0.0~6.6~215.87~0.0~0.0~0.0~6.8~128.17~0.0~0.0~0.0~7.0~0.0~25.09~0" +
                ".0~0.0~7.2~0.0~334.74~0.0~0.0~7.4~0.0~288.24~0.0~0.0~7.6~0.0~0.0~0.0~" +
                "0.0~7.8~0.0~2.0~0.0~0.0~8.4~0.0~2.0~0.0~0.0~8.6~0.0~9.0~0.0~0.0~";

            #endregion

            var c = CompleteMarketPricesParser.Parse(exampleFromApiReference);

            Assert.AreEqual(0, c.RemovedRunners.Count(), "Wrong number of removed runners");
            Assert.AreEqual(3, c.Runners.Count(), "Wrong number of runners");
        }

        [Test]
        public void TestPricesReceivedFromApi()
        {
            const string prices =
                #region Data

                "21250569~0~Baylini,14.29,8.6;Scartozz,9.59,7.0;:1457299~8~745.56~24.0~~" +
                "3.9~false~0~20.62~24.0~~|1.01~12677.34~0.0~0.0~3.0~1.02~87.59~0.0~0.0~0" +
                ".0~1.03~330.16~0.0~0.0~0.0~1.04~3.09~0.0~0.0~0.0~1.05~260.77~0.0~0.0~0." +
                "0~1.06~603.09~0.0~0.0~0.0~1.1~0.77~0.0~0.0~0.0~1.15~0.77~0.0~0.0~0.0~1." +
                "2~0.77~0.0~0.0~0.0~1.24~16.67~0.0~0.0~0.0~1.25~0.77~0.0~0.0~0.0~1.3~0.7" +
                "7~0.0~0.0~0.0~1.32~15.4~0.0~0.0~0.0~1.35~10.77~0.0~0.0~0.0~1.38~2.0~0.0" +
                "~0.0~0.0~1.39~2.0~0.0~0.0~0.0~1.4~0.77~0.0~0.0~0.0~1.41~8.0~0.0~0.0~0.0" +
                "~1.45~5.77~0.0~0.0~0.0~1.5~0.77~0.0~0.0~0.0~1.55~0.77~0.0~0.0~0.0~1.6~0" +
                ".77~0.0~0.0~0.0~1.65~0.77~0.0~0.0~0.0~1.7~0.77~0.0~0.0~0.0~1.75~0.77~0." +
                "0~0.0~0.0~1.8~0.77~0.0~0.0~0.0~1.85~0.77~0.0~0.0~0.0~1.9~20.77~0.0~0.0~" +
                "0.0~1.95~0.77~0.0~0.0~0.0~2.0~2.77~0.0~0.0~0.0~2.1~2.0~0.0~0.0~0.0~2.26" +
                "~51.47~0.0~0.0~0.0~2.4~7.0~0.0~0.0~0.0~2.96~5.0~0.0~0.0~0.0~3.35~72.34~" +
                "0.0~0.0~0.0~3.45~10.0~0.0~0.0~0.0~3.5~20.0~0.0~0.0~0.0~3.65~2.0~0.0~0.0" +
                "~0.0~4.1~7.72~0.0~0.0~0.0~4.2~2.0~0.0~0.0~0.0~7.0~7.72~0.0~0.0~0.0~7.2~" +
                "17.74~0.0~0.0~0.0~7.4~0.74~0.0~0.0~0.0~7.6~1.9~0.0~0.0~0.0~7.8~1.9~0.0~" +
                "0.0~0.0~8.0~1.9~0.0~0.0~0.0~8.4~3.0~0.0~0.0~0.0~10.0~1023.39~0.0~0.0~0." +
                "0~11.0~0.0~0.0~0.0~2.08~11.5~5.0~0.0~0.0~0.0~14.0~11.28~0.0~0.0~0.0~15." +
                "0~33.33~0.0~0.0~0.0~15.5~159.51~0.0~0.0~0.0~16.0~9.65~0.0~0.0~0.0~17.0~" +
                "4.41~0.0~0.0~0.0~18.0~12.78~0.0~0.0~0.0~19.0~31.68~0.0~0.0~0.0~20.0~10." +
                "22~0.0~0.0~3.09~21.0~9.53~0.0~0.0~0.0~23.0~26.49~0.0~0.0~0.0~24.0~8.91~" +
                "0.0~0.0~0.0~27.0~0.0~1.48~0.0~0.0~28.0~0.0~6.7~0.0~0.0~29.0~0.0~7.2~0.0" +
                "~0.0~30.0~0.0~13.65~0.0~0.0~36.0~0.0~0.26~0.0~0.0~38.0~0.0~21.0~0.0~0.0" +
                "~40.0~0.0~2.0~0.0~0.0~42.0~0.0~0.53~0.0~0.0~44.0~0.0~6.0~0.0~0.0~46.0~0" +
                ".0~6.67~0.0~0.0~48.0~0.0~5.0~0.0~0.0~50.0~0.0~11.02~0.0~0.0~55.0~0.0~0." +
                "5~0.0~0.0~60.0~0.0~2.92~0.0~0.0~65.0~0.0~0.57~0.0~0.0~70.0~0.0~10.0~0.0" +
                "~0.0~1000.0~0.0~0.0~160.38~0.0~:936474~10~974.26~40.0~~3.2~false~0~10.3" +
                "8~37.95~~|1.01~12677.34~0.0~0.0~18.0~1.02~87.59~0.0~0.0~0.0~1.03~330.16" +
                "~0.0~0.0~0.0~1.04~3.09~0.0~0.0~0.0~1.05~260.77~0.0~0.0~0.0~1.06~3.09~0." +
                "0~0.0~0.0~1.1~0.77~0.0~0.0~0.0~1.15~0.77~0.0~0.0~0.0~1.2~0.77~0.0~0.0~0" +
                ".0~1.24~16.67~0.0~0.0~0.0~1.25~0.77~0.0~0.0~0.0~1.3~0.77~0.0~0.0~0.0~1." +
                "32~15.4~0.0~0.0~0.0~1.35~10.77~0.0~0.0~0.0~1.38~2.0~0.0~0.0~0.0~1.39~2." +
                "0~0.0~0.0~0.0~1.4~0.77~0.0~0.0~0.0~1.41~8.0~0.0~0.0~0.0~1.45~5.77~0.0~0" +
                ".0~0.0~1.5~0.77~0.0~0.0~0.0~1.55~0.77~0.0~0.0~0.0~1.6~0.77~0.0~0.0~0.0~" +
                "1.65~0.77~0.0~0.0~0.0~1.7~0.77~0.0~0.0~0.0~1.74~10.0~0.0~0.0~0.0~1.75~0" +
                ".77~0.0~0.0~0.0~1.8~0.77~0.0~0.0~0.0~1.85~0.77~0.0~0.0~0.0~1.9~20.77~0." +
                "0~0.0~0.0~1.95~0.77~0.0~0.0~0.0~2.0~2.77~0.0~0.0~0.0~2.1~2.0~0.0~0.0~0." +
                "0~2.26~51.47~0.0~0.0~0.0~2.4~7.0~0.0~0.0~0.0~2.96~5.0~0.0~0.0~0.0~3.45~" +
                "10.0~0.0~0.0~0.0~3.5~20.0~0.0~0.0~0.0~3.65~2.0~0.0~0.0~0.0~4.1~7.72~0.0" +
                "~0.0~0.0~4.2~2.0~0.0~0.0~0.0~4.3~3.0~0.0~0.0~0.0~4.6~47.22~0.0~0.0~0.0~" +
                "4.8~5.0~0.0~0.0~0.0~6.6~0.02~0.0~0.0~0.0~7.0~7.72~0.0~0.0~0.0~10.0~6.0~" +
                "0.0~0.0~0.0~10.5~11.58~0.0~0.0~0.0~11.0~0.0~0.0~0.0~2.08~12.5~213.6~0.0" +
                "~0.0~0.0~13.0~674.34~0.0~0.0~0.0~14.0~5.36~0.0~0.0~0.0~18.0~0.41~0.0~0." +
                "0~0.0~19.0~2.0~0.0~0.0~0.0~20.0~7.72~0.0~0.0~3.09~21.0~23.8~0.0~0.0~0.0" +
                "~23.0~3.06~0.0~0.0~0.0~24.0~3.0~0.0~0.0~0.0~25.0~2.0~0.0~0.0~0.0~26.0~2" +
                "4.21~0.0~0.0~0.0~28.0~7.41~0.0~0.0~0.0~29.0~0.6~0.0~0.0~0.0~32.0~2.0~0." +
                "0~0.0~0.0~34.0~22.73~0.0~0.0~0.0~38.0~8.13~0.0~0.0~0.0~40.0~0.0~4.65~0." +
                "0~0.0~42.0~0.0~5.92~0.0~0.0~44.0~0.0~8.0~0.0~0.0~48.0~0.0~55.0~0.0~0.0~" +
                "50.0~0.0~6.0~0.0~0.0~55.0~0.0~7.56~0.0~0.0~60.0~0.0~4.0~0.0~0.0~80.0~0." +
                "0~4.0~0.0~0.0~90.0~0.0~15.0~0.0~0.0~1000.0~0.0~0.0~168.96~0.0~:1129583~" +
                "3~4785.24~11.5~~9.1~false~0~11.0~11.5~~|1.01~12739.34~0.0~0.0~11.5~1.02" +
                "~87.59~0.0~0.0~0.0~1.03~330.16~0.0~0.0~0.0~1.04~3.09~0.0~0.0~0.0~1.05~2" +
                "60.77~0.0~0.0~0.0~1.06~3.09~0.0~0.0~0.0~1.1~0.77~0.0~0.0~0.0~1.15~0.77~" +
                "0.0~0.0~0.0~1.2~0.77~0.0~0.0~0.0~1.24~16.67~0.0~0.0~0.0~1.25~0.77~0.0~0" +
                ".0~0.0~1.3~0.77~0.0~0.0~0.0~1.32~10.0~0.0~0.0~0.0~1.35~10.77~0.0~0.0~0." +
                "0~1.38~2.0~0.0~0.0~0.0~1.39~2.0~0.0~0.0~0.0~1.4~0.77~0.0~0.0~0.0~1.41~8" +
                ".0~0.0~0.0~0.0~1.45~5.77~0.0~0.0~0.0~1.5~0.77~0.0~0.0~0.0~1.55~0.77~0.0" +
                "~0.0~0.0~1.6~0.77~0.0~0.0~0.0~1.65~0.77~0.0~0.0~0.0~1.7~0.77~0.0~0.0~0." +
                "0~1.75~0.77~0.0~0.0~0.0~1.8~0.77~0.0~0.0~0.0~1.85~0.77~0.0~0.0~0.0~1.9~" +
                "20.77~0.0~0.0~0.0~1.95~0.77~0.0~0.0~0.0~2.0~2.77~0.0~0.0~0.0~2.1~2.0~0." +
                "0~0.0~0.0~2.26~51.47~0.0~0.0~0.0~2.28~200.0~0.0~0.0~0.0~2.4~7.0~0.0~0.0" +
                "~0.0~2.54~5.0~0.0~0.0~0.0~2.96~5.0~0.0~0.0~0.0~3.0~50.0~0.0~0.0~0.0~3.4" +
                "5~10.0~0.0~0.0~0.0~3.5~20.0~0.0~0.0~0.0~3.55~2340.0~0.0~0.0~0.0~3.6~65." +
                "38~0.0~0.0~0.0~3.65~2.0~0.0~0.0~0.0~3.75~5.0~0.0~0.0~0.0~4.1~7.72~0.0~0" +
                ".0~0.0~4.2~2.0~0.0~0.0~0.0~5.4~11.0~0.0~0.0~0.0~5.6~8.0~0.0~0.0~0.0~5.9" +
                "~23.65~0.0~0.0~0.0~6.0~9.72~0.0~0.0~2.0~6.2~288.47~0.0~0.0~0.0~6.4~0.56" +
                "~0.0~0.0~0.0~7.2~20.0~0.0~0.0~0.0~7.6~22.23~0.0~0.0~0.0~7.8~19.71~0.0~0" +
                ".0~0.0~8.6~131.0~0.0~0.0~0.0~8.8~5.0~0.0~0.0~0.0~9.0~160.55~0.0~0.0~0.0" +
                "~9.2~284.48~0.0~0.0~0.0~9.6~5.0~0.0~0.0~0.0~10.0~16.11~0.0~0.0~0.0~10.5" +
                "~51.22~0.0~0.0~0.0~11.0~107.01~0.0~0.0~2.08~11.5~39.6~0.0~0.0~0.0~12.0~" +
                "0.0~59.46~0.0~0.0~12.5~0.0~64.68~0.0~0.0~13.0~0.0~109.0~0.0~0.0~13.5~0." +
                "0~33.73~0.0~0.0~14.0~0.0~27.0~0.0~0.0~14.5~0.0~2.11~0.0~0.0~15.0~0.0~6." +
                "0~0.0~0.0~16.5~0.0~19.35~0.0~0.0~17.0~0.0~2.0~0.0~0.0~18.0~0.0~2.0~0.0~" +
                "0.0~18.5~0.0~0.0~0.0~10.0~20.0~0.0~2.0~0.0~3.09~21.0~0.0~2.0~0.0~0.0~22" +
                ".0~0.0~11.0~0.0~0.0~24.0~0.0~55.0~0.0~0.0~40.0~0.0~2.0~0.0~0.0~46.0~0.0" +
                "~2.0~0.0~0.0~65.0~0.0~15.0~0.0~0.0~1000.0~0.0~54.55~152.6~0.0~:2858119~" +
                "1~9797.68~5.3~~15.9~false~0~5.4~5.3~~|1.01~12681.52~0.0~0.0~134.02~1.02" +
                "~87.59~0.0~0.0~0.0~1.03~330.16~0.0~0.0~0.0~1.04~3.09~0.0~0.0~0.0~1.05~2" +
                "60.77~0.0~0.0~0.0~1.06~3.09~0.0~0.0~0.0~1.1~10.77~0.0~0.0~0.0~1.15~0.77" +
                "~0.0~0.0~0.0~1.2~0.77~0.0~0.0~0.0~1.24~16.67~0.0~0.0~0.0~1.25~0.77~0.0~" +
                "0.0~0.0~1.29~8.0~0.0~0.0~0.0~1.3~0.77~0.0~0.0~0.0~1.32~10.0~0.0~0.0~0.0" +
                "~1.35~10.77~0.0~0.0~0.0~1.38~2.0~0.0~0.0~0.0~1.39~2.0~0.0~0.0~0.0~1.4~0" +
                ".77~0.0~0.0~0.0~1.41~14.0~0.0~0.0~0.0~1.45~5.77~0.0~0.0~0.0~1.47~13.0~0" +
                ".0~0.0~0.0~1.5~0.77~0.0~0.0~0.0~1.55~0.77~0.0~0.0~0.0~1.6~0.77~0.0~0.0~" +
                "0.0~1.65~0.77~0.0~0.0~0.0~1.7~0.77~0.0~0.0~0.0~1.72~5.0~0.0~0.0~0.0~1.7" +
                "4~229.73~0.0~0.0~0.0~1.75~0.77~0.0~0.0~0.0~1.8~0.77~0.0~0.0~0.0~1.83~15" +
                ".0~0.0~0.0~0.0~1.85~0.77~0.0~0.0~0.0~1.9~20.77~0.0~0.0~0.0~1.95~0.77~0." +
                "0~0.0~0.0~2.0~57.68~0.0~0.0~0.0~2.1~2.0~0.0~0.0~0.0~2.18~5086.96~0.0~0." +
                "0~0.0~2.26~51.47~0.0~0.0~0.0~2.4~7.0~0.0~0.0~0.0~2.5~25.0~0.0~0.0~0.0~2" +
                ".54~2.0~0.0~0.0~0.0~2.74~11.33~0.0~0.0~0.0~2.94~56.7~0.0~0.0~0.0~2.96~1" +
                "187.62~0.0~0.0~0.0~3.3~2.0~0.0~0.0~0.0~3.4~6.0~0.0~0.0~0.0~3.45~10.0~0." +
                "0~0.0~0.0~3.5~20.0~0.0~0.0~0.0~3.65~2.0~0.0~0.0~0.0~3.75~5.0~0.0~0.0~0." +
                "0~4.0~519.31~0.0~0.0~0.0~4.08~0.0~0.0~164.95~0.0~4.1~7.72~0.0~0.0~0.0~4" +
                ".11~0.0~0.0~15.29~0.0~4.2~7.29~0.0~0.0~0.0~4.5~13.42~0.0~0.0~0.0~4.6~6." +
                "0~0.0~0.0~0.0~4.8~13.0~0.0~0.0~0.0~4.9~82.21~0.0~0.0~0.0~5.0~414.71~0.0" +
                "~0.0~0.0~5.1~154.73~0.0~0.0~0.0~5.2~160.85~0.0~0.0~0.0~5.4~0.0~93.2~0.0" +
                "~3.0~5.48~0.0~0.0~20.76~0.0~5.5~0.0~289.73~0.0~0.0~5.6~0.0~10.17~0.0~0." +
                "0~5.8~0.0~76.42~0.0~0.0~5.9~0.0~13.9~0.0~0.0~6.0~0.0~0.0~0.0~2.0~6.4~0." +
                "0~2.87~0.0~0.0~6.58~0.0~0.0~49.55~0.0~6.6~0.0~2.0~0.0~0.0~6.8~0.0~23.78" +
                "~0.0~0.0~7.0~0.0~12.73~0.0~0.0~7.2~0.0~32.31~0.0~0.0~7.4~0.0~6.73~0.0~0" +
                ".0~8.0~0.0~4.73~0.0~0.0~8.6~0.0~2.0~0.0~0.0~9.0~0.0~52.7~0.0~0.0~9.4~0." +
                "0~55.0~0.0~0.0~9.6~0.0~8.0~0.0~0.0~10.0~0.0~2.0~0.0~0.0~10.5~0.0~10.0~0" +
                ".0~0.0~11.0~0.0~15.83~0.0~2.08~12.0~0.0~8.0~0.0~0.0~20.0~0.0~4.0~0.0~3." +
                "09~70.0~0.0~20.0~0.0~0.0~120.0~0.0~0.1~0.0~0.0~1000.0~0.0~125.0~533.46~" +
                "0.0~:1521253~2~8798.86~7.6~~13.3~false~0~3.47~7.21~~|1.01~12801.09~0.0~" +
                "0.0~339.02~1.02~87.59~0.0~0.0~0.0~1.03~330.16~0.0~0.0~0.0~1.04~3.09~0.0" +
                "~0.0~0.0~1.05~260.77~0.0~0.0~0.0~1.06~18.09~0.0~0.0~0.0~1.1~0.77~0.0~0." +
                "0~0.0~1.12~10.0~0.0~0.0~0.0~1.15~0.77~0.0~0.0~0.0~1.2~0.77~0.0~0.0~0.0~" +
                "1.24~16.67~0.0~0.0~0.0~1.25~0.77~0.0~0.0~0.0~1.3~0.77~0.0~0.0~0.0~1.32~" +
                "10.0~0.0~0.0~0.0~1.35~10.77~0.0~0.0~0.0~1.38~2.0~0.0~0.0~0.0~1.39~2.0~0" +
                ".0~0.0~0.0~1.4~0.77~0.0~0.0~0.0~1.41~8.0~0.0~0.0~0.0~1.45~5.77~0.0~0.0~" +
                "0.0~1.5~60.77~0.0~0.0~0.0~1.55~0.77~0.0~0.0~0.0~1.6~10.77~0.0~0.0~0.0~1" +
                ".65~0.77~0.0~0.0~0.0~1.7~0.77~0.0~0.0~0.0~1.75~0.77~0.0~0.0~0.0~1.8~0.7" +
                "7~0.0~0.0~0.0~1.85~0.77~0.0~0.0~0.0~1.9~20.77~0.0~0.0~0.0~1.95~0.77~0.0" +
                "~0.0~0.0~2.0~2.77~0.0~0.0~0.0~2.1~2.0~0.0~0.0~0.0~2.2~34.0~0.0~0.0~0.0~" +
                "2.26~51.47~0.0~0.0~0.0~2.4~7.0~0.0~0.0~0.0~2.7~3545.45~0.0~0.0~0.0~2.74" +
                "~3.0~0.0~0.0~0.0~2.76~96.59~0.0~0.0~0.0~2.78~1302.39~0.0~0.0~0.0~2.96~5" +
                ".0~0.0~0.0~0.0~3.0~19.31~0.0~0.0~0.0~3.45~10.0~0.0~0.0~0.0~3.5~20.0~0.0" +
                "~0.0~0.0~3.65~2.0~0.0~0.0~0.0~3.75~3.0~0.0~0.0~0.0~4.1~7.72~0.0~0.0~0.0" +
                "~4.2~4.0~0.0~0.0~0.0~4.4~2.56~0.0~0.0~0.0~4.8~394.74~0.0~0.0~0.0~5.0~1." +
                "9~0.0~0.0~0.0~5.1~1.9~0.0~0.0~0.0~5.2~1.9~0.0~0.0~0.0~5.3~36.03~0.0~0.0" +
                "~0.0~5.4~11.32~0.0~0.0~0.0~5.6~23.91~0.0~0.0~0.0~5.8~3.54~0.0~0.0~0.0~5" +
                ".9~23.65~0.0~0.0~0.0~6.0~0.0~0.0~0.0~2.0~6.2~6.0~0.0~0.0~0.0~6.4~87.48~" +
                "0.0~0.0~0.0~6.6~10.0~0.0~0.0~0.0~7.0~284.86~0.0~0.0~0.0~7.2~166.62~0.0~" +
                "0.0~0.0~7.31~0.0~0.0~20.81~0.0~7.4~27.33~0.0~0.0~0.0~7.6~0.0~107.49~0.0" +
                "~0.0~7.8~0.0~103.91~0.0~0.0~8.0~0.0~164.54~0.0~0.0~8.2~0.0~5.0~0.0~0.0~" +
                "8.4~0.0~205.75~0.0~0.0~8.6~0.0~11.2~0.0~0.0~9.0~0.0~42.75~0.0~0.0~9.2~0" +
                ".0~6.0~0.0~0.0~9.4~0.0~57.0~0.0~0.0~9.6~0.0~46.0~0.0~0.0~9.8~0.0~3.0~0." +
                "0~0.0~10.0~0.0~27.0~0.0~0.0~10.5~0.0~125.0~0.0~0.0~11.0~0.0~39.0~0.0~2." +
                "08~12.0~0.0~39.0~0.0~0.0~13.5~0.0~55.0~0.0~0.0~14.0~0.0~16.0~0.0~0.0~15" +
                ".0~0.0~8.0~0.0~10.0~20.0~0.0~3.0~0.0~3.09~25.0~0.0~15.0~0.0~0.0~1000.0~" +
                "0.0~90.91~816.84~0.0~:386802~4~2824.84~13.5~~8.0~false~0~20.0~13.42~~|1" +
                ".01~12723.49~0.0~0.0~4.0~1.02~87.59~0.0~0.0~0.0~1.03~330.16~0.0~0.0~0.0" +
                "~1.04~3.09~0.0~0.0~0.0~1.05~260.77~0.0~0.0~0.0~1.06~3.09~0.0~0.0~0.0~1." +
                "1~0.77~0.0~0.0~0.0~1.15~0.77~0.0~0.0~0.0~1.2~0.77~0.0~0.0~0.0~1.24~16.6" +
                "7~0.0~0.0~0.0~1.25~0.77~0.0~0.0~0.0~1.3~0.77~0.0~0.0~0.0~1.32~10.0~0.0~" +
                "0.0~0.0~1.35~10.77~0.0~0.0~0.0~1.38~2.0~0.0~0.0~0.0~1.39~2.0~0.0~0.0~0." +
                "0~1.4~0.77~0.0~0.0~0.0~1.41~8.0~0.0~0.0~0.0~1.45~5.77~0.0~0.0~0.0~1.5~0" +
                ".77~0.0~0.0~0.0~1.55~0.77~0.0~0.0~0.0~1.6~0.77~0.0~0.0~0.0~1.65~0.77~0." +
                "0~0.0~0.0~1.7~0.77~0.0~0.0~0.0~1.75~0.77~0.0~0.0~0.0~1.8~0.77~0.0~0.0~0" +
                ".0~1.85~0.77~0.0~0.0~0.0~1.9~20.77~0.0~0.0~0.0~1.95~0.77~0.0~0.0~0.0~2." +
                "0~2.77~0.0~0.0~0.0~2.1~2.0~0.0~0.0~0.0~2.26~56.47~0.0~0.0~0.0~2.4~7.0~0" +
                ".0~0.0~0.0~2.96~5.0~0.0~0.0~0.0~3.35~72.34~0.0~0.0~0.0~3.45~10.0~0.0~0." +
                "0~0.0~3.5~20.0~0.0~0.0~0.0~3.65~2.0~0.0~0.0~0.0~3.95~2034.78~0.0~0.0~0." +
                "0~4.0~773.07~0.0~0.0~0.0~4.1~7.72~0.0~0.0~0.0~4.2~2.0~0.0~0.0~0.0~5.2~0" +
                ".56~0.0~0.0~0.0~6.0~7.72~0.0~0.0~2.0~7.2~17.74~0.0~0.0~0.0~7.8~21.59~0." +
                "0~0.0~0.0~8.0~2.0~0.0~0.0~0.0~8.6~14.0~0.0~0.0~0.0~9.0~1.62~0.0~0.0~0.0" +
                "~9.2~1.9~0.0~0.0~0.0~9.4~18.34~0.0~0.0~0.0~9.8~1.91~0.0~0.0~0.0~10.0~6." +
                "0~0.0~0.0~0.0~11.0~45.45~0.0~0.0~2.08~11.5~10.0~0.0~0.0~0.0~12.0~40.62~" +
                "0.0~0.0~0.0~12.5~12.15~0.0~0.0~0.0~13.0~22.73~0.0~0.0~0.0~13.5~0.0~1.44" +
                "~0.0~0.0~14.0~0.0~16.4~0.0~0.0~14.5~0.0~52.55~0.0~0.0~15.0~0.0~2.0~0.0~" +
                "0.0~15.5~0.0~7.0~0.0~0.0~16.0~0.0~102.0~0.0~0.0~16.5~0.0~0.11~0.0~0.0~1" +
                "8.0~0.0~9.0~0.0~0.0~19.0~0.0~18.67~0.0~0.0~20.0~0.0~0.0~0.0~3.09~24.0~0" +
                ".0~2.0~0.0~0.0~25.0~0.0~2.0~0.0~0.0~27.0~0.0~62.0~0.0~0.0~28.0~0.0~5.0~" +
                "0.0~0.0~30.0~0.0~2.0~0.0~0.0~48.0~0.0~15.0~0.0~0.0~1000.0~0.0~46.44~183" +
                ".67~0.0~:1472584~9~1811.94~36.0~~3.3~false~0~11.0~34.0~~|1.01~12677.34~" +
                "0.0~0.0~16.28~1.02~87.59~0.0~0.0~0.0~1.03~330.16~0.0~0.0~0.0~1.04~3.09~" +
                "0.0~0.0~0.0~1.05~260.77~0.0~0.0~0.0~1.06~3.09~0.0~0.0~0.0~1.1~0.77~0.0~" +
                "0.0~0.0~1.15~0.77~0.0~0.0~0.0~1.2~0.77~0.0~0.0~0.0~1.24~16.67~0.0~0.0~0" +
                ".0~1.25~0.77~0.0~0.0~0.0~1.3~0.77~0.0~0.0~0.0~1.32~15.4~0.0~0.0~0.0~1.3" +
                "5~10.77~0.0~0.0~0.0~1.38~2.0~0.0~0.0~0.0~1.39~2.0~0.0~0.0~0.0~1.4~0.77~" +
                "0.0~0.0~0.0~1.41~8.0~0.0~0.0~0.0~1.45~5.77~0.0~0.0~0.0~1.5~0.77~0.0~0.0" +
                "~0.0~1.55~0.77~0.0~0.0~0.0~1.6~0.77~0.0~0.0~0.0~1.65~0.77~0.0~0.0~0.0~1" +
                ".7~0.77~0.0~0.0~0.0~1.75~0.77~0.0~0.0~0.0~1.8~0.77~0.0~0.0~0.0~1.85~0.7" +
                "7~0.0~0.0~0.0~1.9~20.77~0.0~0.0~0.0~1.95~0.77~0.0~0.0~0.0~2.0~2.77~0.0~" +
                "0.0~0.0~2.1~2.0~0.0~0.0~0.0~2.26~51.47~0.0~0.0~0.0~2.4~7.0~0.0~0.0~0.0~" +
                "2.96~5.0~0.0~0.0~0.0~3.45~10.0~0.0~0.0~0.0~3.5~20.0~0.0~0.0~0.0~3.65~2." +
                "0~0.0~0.0~0.0~4.1~62.56~0.0~0.0~0.0~4.2~2.0~0.0~0.0~0.0~4.5~8.0~0.0~0.0" +
                "~0.0~7.0~7.72~0.0~0.0~0.0~9.2~13.41~0.0~0.0~0.0~9.6~269.24~0.0~0.0~0.0~" +
                "9.8~709.09~0.0~0.0~0.0~10.0~6.0~0.0~0.0~0.0~11.0~0.0~0.0~0.0~2.08~13.0~" +
                "11.88~0.0~0.0~0.0~13.5~5.56~0.0~0.0~0.0~14.5~5.17~0.0~0.0~0.0~15.0~1.37" +
                "~0.0~0.0~0.0~15.5~1.9~0.0~0.0~0.0~19.5~9.93~0.0~0.0~0.0~20.0~0.0~0.0~0." +
                "0~3.09~21.0~23.8~0.0~0.0~0.0~25.0~6.0~0.0~0.0~0.0~26.0~8.68~0.0~0.0~0.0" +
                "~28.0~0.19~0.0~0.0~0.0~32.0~13.55~0.0~0.0~0.0~34.0~39.3~0.0~0.0~0.0~36." +
                "0~6.9~0.0~0.0~0.0~38.0~4.58~0.0~0.0~0.0~40.0~0.0~9.0~0.0~0.0~44.0~0.0~0" +
                ".01~0.0~0.0~48.0~0.0~6.38~0.0~0.0~70.0~0.0~5.0~0.0~0.0~75.0~0.0~19.0~0." +
                "0~0.0~95.0~0.0~2.0~0.0~0.0~1000.0~0.0~0.0~166.32~0.0~:2569390~0~33920.2" +
                "8~3.65~~27.6~false~0~3.12~3.65~~|1.01~12687.34~0.0~0.0~267.49~1.02~87.5" +
                "9~0.0~0.0~0.0~1.03~830.16~0.0~0.0~0.0~1.04~3.09~0.0~0.0~0.0~1.05~260.77" +
                "~0.0~0.0~0.0~1.06~3.09~0.0~0.0~0.0~1.1~5.55~0.0~0.0~0.0~1.11~500.0~0.0~" +
                "0.0~0.0~1.12~40.0~0.0~0.0~0.0~1.15~6.77~0.0~0.0~0.0~1.2~0.77~0.0~0.0~0." +
                "0~1.24~427.67~0.0~0.0~0.0~1.25~0.77~0.0~0.0~0.0~1.3~0.77~0.0~0.0~0.0~1." +
                "32~10.0~0.0~0.0~0.0~1.35~10.77~0.0~0.0~0.0~1.36~225.0~0.0~0.0~0.0~1.38~" +
                "2.0~0.0~0.0~0.0~1.39~74.0~0.0~0.0~0.0~1.4~0.77~0.0~0.0~0.0~1.41~13.0~0." +
                "0~0.0~0.0~1.45~5.77~0.0~0.0~0.0~1.5~6.86~0.0~0.0~0.0~1.51~25.0~0.0~0.0~" +
                "0.0~1.55~0.77~0.0~0.0~0.0~1.6~40.77~0.0~0.0~0.0~1.65~9227.24~0.0~0.0~0." +
                "0~1.7~0.77~0.0~0.0~0.0~1.71~126.0~0.0~0.0~0.0~1.75~0.77~0.0~0.0~0.0~1.8" +
                "~700.77~0.0~0.0~0.0~1.81~200.0~0.0~0.0~0.0~1.85~0.77~0.0~0.0~0.0~1.86~5" +
                "0.02~0.0~0.0~0.0~1.9~20.77~0.0~0.0~0.0~1.95~0.77~0.0~0.0~0.0~2.0~38.88~" +
                "0.0~0.0~0.0~2.04~200.0~0.0~0.0~0.0~2.1~2.0~0.0~0.0~0.0~2.12~151.78~0.0~" +
                "0.0~0.0~2.14~120.0~0.0~0.0~0.0~2.26~51.47~0.0~0.0~0.0~2.3~64.0~0.0~0.0~" +
                "0.0~2.38~2.9~0.0~0.0~0.0~2.4~2.0~0.0~0.0~0.0~2.5~10.0~0.0~0.0~0.0~2.52~" +
                "100.0~0.0~0.0~0.0~2.62~2.38~0.0~0.0~0.0~2.68~25.0~0.0~0.0~0.0~2.74~0.0~" +
                "0.0~8.85~0.0~2.78~959.25~0.0~0.0~0.0~2.82~0.47~0.0~0.0~0.0~2.84~79.79~0" +
                ".0~0.0~0.0~2.86~62.32~0.0~0.0~0.0~2.88~0.56~0.0~0.0~0.0~2.92~4.0~0.0~0." +
                "0~0.0~2.96~5.0~0.0~0.0~0.0~3.0~254.25~0.0~0.0~0.0~3.05~1139.15~0.0~0.0~" +
                "0.0~3.2~17.14~0.0~0.0~0.0~3.25~42.0~0.0~0.0~0.0~3.3~233.23~0.0~0.0~0.0~" +
                "3.35~85.45~0.0~0.0~0.0~3.4~8.73~0.0~0.0~0.0~3.45~25.0~0.0~0.0~0.0~3.5~1" +
                "123.82~0.0~0.0~0.0~3.55~272.8~0.0~0.0~0.0~3.6~202.78~0.0~0.0~0.0~3.61~0" +
                ".0~0.0~13.06~0.0~3.65~629.5~0.0~0.0~0.0~3.66~0.0~0.0~31.68~0.0~3.7~0.0~" +
                "577.28~0.0~0.0~3.75~0.0~260.05~0.0~0.0~3.8~0.0~232.74~0.0~0.0~3.85~0.0~" +
                "15.45~0.0~0.0~3.9~0.0~60.63~0.0~0.0~3.95~0.0~10.0~0.0~0.0~4.0~0.0~142.0" +
                "~0.0~10.0~4.1~0.0~191.0~0.0~0.0~4.2~0.0~62.5~0.0~0.0~4.4~0.0~17.0~0.0~0" +
                ".0~4.5~0.0~211.0~0.0~0.0~4.6~0.0~300.0~0.0~0.0~4.7~0.0~5.0~0.0~0.0~4.8~" +
                "0.0~132.0~0.0~0.0~4.9~0.0~76.92~0.0~0.0~5.0~0.0~100.0~0.0~0.0~5.1~0.0~2" +
                "1.95~8.06~0.0~5.2~0.0~2.0~0.0~0.0~5.3~0.0~6.0~0.0~0.0~5.5~0.0~12.0~0.0~" +
                "0.0~5.6~0.0~2.0~0.0~0.0~5.7~0.0~55.01~0.0~0.0~6.6~0.0~4.0~0.0~0.0~7.0~0" +
                ".0~21.0~0.0~0.0~8.0~0.0~22.0~0.0~0.0~8.8~0.0~2.0~0.0~0.0~10.0~0.0~4.61~" +
                "0.0~0.0~11.0~0.0~0.0~0.0~2.08~16.5~0.0~15.0~0.0~0.0~20.0~0.0~0.5~0.0~3." +
                "09~1000.0~0.0~226.92~514.46~0.0~:2270116~5~5100.62~15.0~~6.9~false~0~2." +
                "58~12.75~~|1.01~12677.34~0.0~0.0~173.64~1.02~87.59~0.0~0.0~0.0~1.03~330" +
                ".16~0.0~0.0~0.0~1.04~3.09~0.0~0.0~0.0~1.05~260.77~0.0~0.0~0.0~1.06~3.09" +
                "~0.0~0.0~0.0~1.1~0.77~0.0~0.0~0.0~1.15~0.77~0.0~0.0~0.0~1.2~0.77~0.0~0." +
                "0~0.0~1.24~16.67~0.0~0.0~0.0~1.25~0.77~0.0~0.0~0.0~1.3~0.77~0.0~0.0~0.0" +
                "~1.32~10.0~0.0~0.0~0.0~1.35~10.77~0.0~0.0~0.0~1.38~2.0~0.0~0.0~0.0~1.39" +
                "~2.0~0.0~0.0~0.0~1.4~0.77~0.0~0.0~0.0~1.41~8.0~0.0~0.0~0.0~1.45~5.77~0." +
                "0~0.0~0.0~1.5~0.77~0.0~0.0~0.0~1.55~0.77~0.0~0.0~0.0~1.6~0.77~0.0~0.0~0" +
                ".0~1.65~0.77~0.0~0.0~0.0~1.7~0.77~0.0~0.0~0.0~1.75~0.77~0.0~0.0~0.0~1.8" +
                "~0.77~0.0~0.0~0.0~1.85~0.77~0.0~0.0~0.0~1.9~20.77~0.0~0.0~0.0~1.95~0.77" +
                "~0.0~0.0~0.0~2.0~32.77~0.0~0.0~0.0~2.1~2.0~0.0~0.0~0.0~2.26~51.47~0.0~0" +
                ".0~0.0~2.4~7.0~0.0~0.0~0.0~2.96~5.0~0.0~0.0~0.0~3.45~10.0~0.0~0.0~0.0~3" +
                ".5~22.14~0.0~0.0~0.0~3.65~2.0~0.0~0.0~0.0~4.1~7.72~0.0~0.0~0.0~4.2~2.0~" +
                "0.0~0.0~0.0~4.6~1671.43~0.0~0.0~0.0~4.7~626.24~0.0~0.0~0.0~6.0~34.56~0." +
                "0~0.0~0.0~7.0~7.72~0.0~0.0~0.0~7.4~10.0~0.0~0.0~0.0~8.0~20.97~0.0~0.0~0" +
                ".0~9.0~4.0~0.0~0.0~0.0~10.0~6.0~0.0~0.0~0.0~11.0~0.0~0.0~0.0~2.08~11.5~" +
                "15.04~0.0~0.0~0.0~12.0~11.0~0.0~0.0~0.0~12.34~0.0~0.0~35.1~0.0~13.5~18." +
                "0~0.0~0.0~0.0~14.0~5.36~0.0~0.0~0.0~14.5~18.35~0.0~0.0~0.0~15.0~20.65~0" +
                ".0~0.0~0.0~15.5~31.17~0.0~0.0~0.0~16.0~0.0~66.08~0.0~0.0~16.5~0.0~8.24~" +
                "0.0~0.0~17.0~0.0~41.21~0.0~0.0~17.5~0.0~22.12~0.0~0.0~18.0~0.0~11.0~0.0" +
                "~0.0~18.5~0.0~10.0~0.0~0.0~19.0~0.0~93.0~0.0~0.0~20.0~0.0~2.0~0.0~3.09~" +
                "21.0~0.0~6.0~0.0~0.0~22.0~0.0~12.11~0.0~0.0~23.0~0.0~29.0~0.0~0.0~24.0~" +
                "0.0~15.04~0.0~0.0~26.0~0.0~50.0~0.0~0.0~29.0~0.0~24.0~0.0~0.0~30.0~0.0~" +
                "11.0~0.0~0.0~32.0~0.0~11.45~0.0~0.0~34.0~0.0~6.0~0.0~0.0~36.0~0.0~55.0~" +
                "0.0~0.0~38.0~0.0~39.0~0.0~0.0~55.0~0.0~2.0~0.0~0.0~60.0~0.0~6.0~0.0~0.0" +
                "~95.0~0.0~2.0~0.0~0.0~120.0~0.0~15.0~0.0~0.0~400.0~0.0~0.77~0.0~0.0~100" +
                "0.0~0.0~0.25~240.13~0.0~:811434~7~1316.52~24.0~~4.2~false~0~11.0~24.0~~" +
                "|1.01~12677.34~0.0~0.0~21.0~1.02~87.59~0.0~0.0~0.0~1.03~330.16~0.0~0.0~" +
                "0.0~1.04~3.09~0.0~0.0~0.0~1.05~260.77~0.0~0.0~0.0~1.06~3.09~0.0~0.0~0.0" +
                "~1.1~0.77~0.0~0.0~0.0~1.15~0.77~0.0~0.0~0.0~1.2~0.77~0.0~0.0~0.0~1.24~1" +
                "6.67~0.0~0.0~0.0~1.25~0.77~0.0~0.0~0.0~1.3~0.77~0.0~0.0~0.0~1.32~15.4~0" +
                ".0~0.0~0.0~1.35~10.77~0.0~0.0~0.0~1.38~2.0~0.0~0.0~0.0~1.39~2.0~0.0~0.0" +
                "~0.0~1.4~0.77~0.0~0.0~0.0~1.41~8.0~0.0~0.0~0.0~1.45~5.77~0.0~0.0~0.0~1." +
                "5~0.77~0.0~0.0~0.0~1.55~0.77~0.0~0.0~0.0~1.6~0.77~0.0~0.0~0.0~1.65~0.77" +
                "~0.0~0.0~0.0~1.7~0.77~0.0~0.0~0.0~1.74~10.0~0.0~0.0~0.0~1.75~0.77~0.0~0" +
                ".0~0.0~1.8~0.77~0.0~0.0~0.0~1.85~0.77~0.0~0.0~0.0~1.9~20.77~0.0~0.0~0.0" +
                "~1.95~0.77~0.0~0.0~0.0~2.0~2.77~0.0~0.0~0.0~2.1~2.0~0.0~0.0~0.0~2.26~51" +
                ".47~0.0~0.0~0.0~2.4~7.0~0.0~0.0~0.0~2.96~5.0~0.0~0.0~0.0~3.45~10.0~0.0~" +
                "0.0~0.0~3.5~20.0~0.0~0.0~0.0~3.65~6.0~0.0~0.0~0.0~3.8~60.71~0.0~0.0~0.0" +
                "~4.1~7.72~0.0~0.0~0.0~4.2~2.0~0.0~0.0~0.0~5.0~2.0~0.0~0.0~0.0~5.1~9.0~0" +
                ".0~0.0~0.0~6.2~2.0~0.0~0.0~0.0~6.4~429.2~0.0~0.0~0.0~6.6~1170.0~0.0~0.0" +
                "~0.0~7.0~7.72~0.0~0.0~0.0~8.0~3.09~0.0~0.0~0.0~8.4~14.86~0.0~0.0~0.0~8." +
                "8~18.81~0.0~0.0~0.0~9.6~174.42~0.0~0.0~0.0~10.0~6.0~0.0~0.0~0.0~10.5~14" +
                ".72~0.0~0.0~0.0~11.0~0.0~0.0~0.0~2.08~12.0~2.0~0.0~0.0~0.0~13.0~5.77~0." +
                "0~0.0~0.0~14.0~0.53~0.0~0.0~0.0~17.5~4.28~0.0~0.0~0.0~18.0~1.01~0.0~0.0" +
                "~0.0~19.0~10.0~0.0~0.0~0.0~20.0~2.5~0.0~0.0~3.09~21.0~31.15~0.0~0.0~0.0" +
                "~22.0~20.18~0.0~0.0~0.0~23.0~29.42~0.0~0.0~0.0~24.0~17.13~0.0~0.0~0.0~2" +
                "5.0~0.0~21.43~0.0~0.0~29.0~0.0~23.0~0.0~0.0~30.0~0.0~15.72~0.0~0.0~32.0" +
                "~0.0~9.18~0.0~0.0~34.0~0.0~6.0~0.0~0.0~36.0~0.0~57.0~0.0~0.0~38.0~0.0~2" +
                ".0~0.0~0.0~44.0~0.0~8.98~0.0~0.0~48.0~0.0~7.0~0.0~0.0~50.0~0.0~6.0~0.0~" +
                "0.0~70.0~0.0~15.0~0.0~0.0~80.0~0.0~5.0~0.0~0.0~90.0~0.0~0.5~0.0~0.0~95." +
                "0~0.0~2.0~0.0~0.0~1000.0~0.0~2.0~211.61~0.0~:811856~6~1830.86~24.0~~4.5" +
                "~false~0~4.86~21.56~~|1.01~12646.34~0.0~0.0~49.0~1.02~87.59~0.0~0.0~0.0" +
                "~1.03~330.16~0.0~0.0~0.0~1.04~3.09~0.0~0.0~0.0~1.05~260.77~0.0~0.0~0.0~" +
                "1.06~3.09~0.0~0.0~0.0~1.1~0.77~0.0~0.0~0.0~1.15~0.77~0.0~0.0~0.0~1.2~0." +
                "77~0.0~0.0~0.0~1.24~16.67~0.0~0.0~0.0~1.25~0.77~0.0~0.0~0.0~1.3~0.77~0." +
                "0~0.0~0.0~1.32~15.4~0.0~0.0~0.0~1.35~10.77~0.0~0.0~0.0~1.38~2.0~0.0~0.0" +
                "~0.0~1.39~2.0~0.0~0.0~0.0~1.4~0.77~0.0~0.0~0.0~1.41~8.0~0.0~0.0~0.0~1.4" +
                "5~5.77~0.0~0.0~0.0~1.5~0.77~0.0~0.0~0.0~1.55~0.77~0.0~0.0~0.0~1.6~0.77~" +
                "0.0~0.0~0.0~1.65~0.77~0.0~0.0~0.0~1.7~0.77~0.0~0.0~0.0~1.75~0.77~0.0~0." +
                "0~0.0~1.8~0.77~0.0~0.0~0.0~1.85~0.77~0.0~0.0~0.0~1.9~20.77~0.0~0.0~0.0~" +
                "1.95~0.77~0.0~0.0~0.0~2.0~2.77~0.0~0.0~0.0~2.1~2.0~0.0~0.0~0.0~2.26~51." +
                "47~0.0~0.0~0.0~2.4~7.0~0.0~0.0~0.0~2.96~5.0~0.0~0.0~0.0~3.2~20.0~0.0~0." +
                "0~0.0~3.45~10.0~0.0~0.0~0.0~3.5~20.0~0.0~0.0~0.0~3.65~2.0~0.0~0.0~0.0~4" +
                ".1~7.72~0.0~0.0~0.0~4.2~4.0~0.0~0.0~0.0~7.0~7.72~0.0~0.0~0.0~7.14~0.0~0" +
                ".0~20.24~0.0~7.6~25.76~0.0~0.0~0.0~7.8~1063.64~0.0~0.0~0.0~10.0~6.0~0.0" +
                "~0.0~0.0~12.0~2.0~0.0~0.0~0.0~13.0~38.4~0.0~0.0~0.0~13.5~185.78~0.0~0.0" +
                "~0.0~14.5~10.87~0.0~0.0~0.0~15.0~2.0~0.0~0.0~0.0~16.0~4.69~0.0~0.0~0.0~" +
                "17.0~10.24~0.0~0.0~0.0~17.5~4.28~0.0~0.0~0.0~18.0~2.77~0.0~0.0~0.0~18.5" +
                "~4.0~0.0~0.0~0.0~20.0~10.68~0.0~0.0~3.09~21.0~12.85~0.0~0.0~0.0~23.0~10" +
                ".43~0.0~0.0~0.0~24.0~0.0~4.35~0.0~0.0~25.0~0.0~46.0~0.0~0.0~26.0~0.0~50" +
                ".34~0.0~0.0~27.0~0.0~4.0~0.0~0.0~30.0~0.0~61.0~0.0~0.0~32.0~0.0~2.54~0." +
                "0~0.0~34.0~0.0~9.09~0.0~0.0~42.0~0.0~5.0~0.0~0.0~50.0~0.0~5.0~0.0~0.0~1" +
                "000.0~0.0~0.0~169.32~0.0~";

            #endregion

            var c = CompleteMarketPricesParser.Parse(prices);

            Assert.AreEqual(2, c.RemovedRunners.Count(), "Wrong number of removed runners");
            Assert.AreEqual(11, c.Runners.Count(), "Wrong number of runners");
        }

        [Test]
        public void TestRemovedRunnerNameIsSanitized()
        {
            const string prices = 
                @"21250569~0~Bay\,lini,14.29,8.6;Sca\:rtozz,9.59,7.0;";

            var c = CompleteMarketPricesParser.Parse(prices);

            Assert.AreEqual(2, c.RemovedRunners.Count(), "Wrong number of removed runners");
            Assert.IsNotNull(c.RemovedRunners.SingleOrDefault(r => r.Name == "Bay,lini"));
            Assert.IsNotNull(c.RemovedRunners.SingleOrDefault(r => r.Name == "Sca:rtozz"));

            Assert.IsNull(c.RemovedRunners.SingleOrDefault(r => r.Name == "Baylini"));
            Assert.IsNull(c.RemovedRunners.SingleOrDefault(r => r.Name == "Scartozz"));

            Assert.AreEqual(0, c.Runners.Count(), "Wrong number of runners");
        }
    }
}