namespace Betfair.Net.Fsharp

module AsyncApi = 
    open Betfair.Net
    open Betfair.Net.BFGlobal
    open Betfair.Net.BFExchange
    
    open Betfair.Net.Fsharp.Types
    open Betfair.Net.Fsharp.Finders
    open Betfair.Net.Fsharp.AsyncCore
    
    let MakeGlobalHeader = make_global_header
    let MakeExchangeHeader = make_exchange_header
    
    let GetManyEventsByIdWithService (service:BFGlobalService) sessionToken ids =
        ids |> Array.map (fun id -> async_events_from_parent_id service sessionToken id)
            |> Async.Parallel
            |> Async.RunSynchronously
            |> FindAllEvents

    let GetManyEventsWithService service sessionToken (evs:BFEvent[]) =
        let ids = evs |> Array.map(fun ev -> ev.eventId)
        GetManyEventsByIdWithService service sessionToken ids
            
    // Get prices for all the specified markets
    let GetManyPricesWithService (service:BFExchangeService) sessionToken (markets:MarketSummary[]) =
        let wrapper = async_prices_from_summary service sessionToken
        markets |> Array.map (fun x -> wrapper x)
                |> Async.Parallel
                |> Async.RunSynchronously
                |> FindAllPrices
                
    // Get full markets for all the specified summaries
    let GetManyMarketsWithService (service:BFExchangeService) sessionToken (markets:MarketSummary[]) =
        let wrapper = async_market_from_summary service sessionToken
        markets |> Array.map (fun x -> wrapper x)
                |> Async.Parallel
                |> Async.RunSynchronously    
                |> FindAllMarkets
                
    let GetAllMarketInfoWithServices (gservice:BFGlobalService) (eservice:BFExchangeService) sessionToken id =
        [ async_market_from_id eservice sessionToken id;
          async_prices_from_id eservice sessionToken id; 
          async_current_bets_from_market_id eservice sessionToken id ] 
            |> Async.Parallel
            |> Async.RunSynchronously



    (* Some handy synchronous wrappers *)
    
    let loginWithService (service:BFGlobalService) username password productID =
        let req = new LoginReq(username = username, password = password, productId = productID)
        service.login req
        
    let getEventsWithService (service:BFGlobalService) sessionToken eventParentId =
        async_events_from_parent_id service sessionToken eventParentId
            |> Async.RunSynchronously


    (* Below this point are convenience functions that use a default service object *)

    let globalService = new BFGlobalService()
    let ukService = new BFExchangeService()
    
    let login = loginWithService (new BFGlobalService())
    let getManyEvents = GetManyEventsWithService globalService
    let getManyEventsById = GetManyEventsByIdWithService globalService
    let getMarkets = GetManyMarketsWithService ukService
    let getPrices = GetManyPricesWithService ukService
    let getAllMarketInfo = GetAllMarketInfoWithServices globalService ukService
