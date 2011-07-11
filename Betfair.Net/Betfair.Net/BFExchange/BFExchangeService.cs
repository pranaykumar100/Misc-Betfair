using System;

namespace Betfair.Net.BFExchange
{
    public partial class BFExchangeService
    {
        public IAsyncResult BeginInvokeWrapper(string methodName, APIRequest request, AsyncCallback callback, object asyncState)
        {
            return BeginInvoke(methodName, new[] { request }, callback, asyncState);
        }

        public object EndInvokeWrapper(IAsyncResult asyncResult)
        {
            return EndInvoke(asyncResult)[0];
        }
    }
}
