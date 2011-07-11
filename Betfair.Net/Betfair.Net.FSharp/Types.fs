namespace Betfair.Net.Fsharp

module Types =    
    open Betfair.Net.BFGlobal
    open Betfair.Net.BFExchange

    // Extension methods to add async wrapper to proxies
    type BFGlobalService with
        member x.BuildAsyncPrimitive(name, req) =
            Async.BuildPrimitive(name, req, x.BeginInvokeWrapper, x.EndInvokeWrapper)
            
        member x.GetEventsAsync req         = x.BuildAsyncPrimitive("getEvents", req)
        member x.GetActiveEventTypes req    = x.BuildAsyncPrimitive("getActiveEventTypes", req)
        
    type BFExchangeService with
        member x.BuildAsyncPrimitive(name, req) =
            Async.BuildPrimitive(name, req, x.BeginInvokeWrapper, x.EndInvokeWrapper)
            
        member x.GetMarketAsync req         = x.BuildAsyncPrimitive("getMarket", req)
        member x.GetMarketPricesAsync req   = x.BuildAsyncPrimitive("getMarketPrices", req)
        member x.GetCurrentBetsAsync req    = x.BuildAsyncPrimitive("getCurrentBets", req)
    
    
    
    type ResponseType =
        | Event of GetEventsResp
        | Sport of GetEventTypesResp
        | Market of GetMarketResp
        | Prices of GetMarketPricesResp
        | CurrentBets of GetCurrentBetsResp

    let wrap_response (r:obj) =
        match r with
        | :? GetMarketResp          -> Market(r :?> GetMarketResp)
        | :? GetMarketPricesResp    -> Prices(r :?> GetMarketPricesResp)
        | :? GetEventsResp          -> Event(r :?> GetEventsResp)
        | :? GetEventTypesResp      -> Sport(r :?> GetEventTypesResp)
        | :? GetCurrentBetsResp     -> CurrentBets(r :?> GetCurrentBetsResp)
        | _                         -> failwith "b0rk"
