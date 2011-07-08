namespace BFCompressedParser
{
    public static class BetfairStringExtensions
    {
        public static string Sanitize(this string s)
        {
            return s
                .Replace(@"\,", "<COMMA>")
                .Replace(@"\;", "<SEMICOLON>")
                .Replace(@"\:", "<COLON>")
                .Replace(@"\|", "<PIPE>");
        }

        public static string Desanitize(this string s)
        {
            return s
                .Replace("<COMMA>", @",")
                .Replace("<SEMICOLON>", @";")
                .Replace("<COLON>", @":")
                .Replace("<PIPE>", @"|");
        }

        /// <summary>
        /// A bit like string.TrimEnd, but only removes a single instance of the
        /// specified trailing character rather than all
        /// </summary>
        public static string RemoveSingleTrailingChar(this string s, char ch)
        {
            return s.EndsWith(ch.ToString()) ? s.Remove(s.Length - 1) : s;
        }
    }
}