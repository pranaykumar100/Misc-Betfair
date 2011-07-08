using System;

namespace BFCompressedParser
{
    public class RemovedRunner
    {
        internal RemovedRunner(string[] data)
        {
            Name = data[0].Desanitize();

            // Grr, have to provide a date part to the parser
            string dt = string.Format("{0:yyyy/MM/dd} {1}", DateTime.Now, data[1].Replace('.', ':'));
            TimeRemoved = DateTime.Parse(dt).ToLocalTime().TimeOfDay;

            AdjustmentFactor = data[2] + "%";
        }

        public string AdjustmentFactor { get; set; }
        public TimeSpan TimeRemoved { get; set; }
        public string Name { get; set; }
    }
}