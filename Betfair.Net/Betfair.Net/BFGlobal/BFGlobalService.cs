using System;

namespace Betfair.Net.BFGlobal
{
    public partial class BFGlobalService
    {
        public IAsyncResult BeginInvokeWrapper(string methodName, APIRequest request, AsyncCallback callback, object asyncState)
        {
            return BeginInvoke(methodName, new [] {request}, callback, asyncState);
        }

        public object EndInvokeWrapper(IAsyncResult asyncResult)
        {
            return EndInvoke(asyncResult)[0];
        }
    }
}
