namespace Betfair.Net.Fsharp

module internal AsyncCore =
    open Betfair.Net
    open Betfair.Net.BFGlobal
    open Betfair.Net.BFExchange
    open Betfair.Net.Fsharp.Types

    // Helper funcs
    let make_global_header sessionToken = new BFGlobal.APIRequestHeader(sessionToken = sessionToken)
    let make_exchange_header sessionToken = new BFExchange.APIRequestHeader(sessionToken = sessionToken)

    let create_async req f =
        async { let! rsp = f(req)
                return (wrap_response rsp) }
    
    let async_market_from_id (service:BFExchangeService) sessionToken marketId =
        let req = new GetMarketReq(header = make_exchange_header sessionToken, marketId = marketId)
        create_async req service.GetMarketAsync

    let async_market_from_summary (service:BFExchangeService) sessionToken (ms:MarketSummary) =
        async_market_from_id service sessionToken ms.marketId

    let async_prices_from_id (service:BFExchangeService) sessionToken marketId =
        let req = new GetMarketPricesReq(header = make_exchange_header sessionToken, marketId = marketId)
        create_async req service.GetMarketPricesAsync

    let async_prices_from_summary (service:BFExchangeService) sessionToken (ms:MarketSummary) =
        async_prices_from_id service sessionToken ms.marketId

    let async_events_from_parent_id (service:BFGlobalService) sessionToken eventParentId =
        let req = new GetEventsReq(header = make_global_header sessionToken, eventParentId = eventParentId)
        create_async req service.GetEventsAsync
        
    let async_current_bets_from_market_id (service:BFExchangeService) sessionToken marketId =
        let req = new GetCurrentBetsReq(header = make_exchange_header sessionToken, marketId = marketId, recordCount = 50)
        create_async req service.GetCurrentBetsAsync
