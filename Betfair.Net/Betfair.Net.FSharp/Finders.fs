namespace Betfair.Net.Fsharp

module Finders = 
    open Betfair.Net.Fsharp.Types
    
    let FindAllForMarket resps marketId = 
        let matchMarket = function
            | Event(x)       -> x.marketItems |> Array.exists (fun m -> m.marketId = marketId)
            | Market(x)      -> x.market.marketId = marketId
            | Prices(x)      -> x.marketPrices.marketId = marketId
            | CurrentBets(x) -> x.bets |> Array.exists (fun m -> m.marketId = marketId)
            | _ -> false
        
        List.filter matchMarket resps
        
        
        
        
    let FindPrices marketId responses =
        responses |> Array.pick (function
                                  | Prices(x) when x.marketPrices.marketId = marketId -> Some(x)
                                  | _ -> None)
       
    let FindMarket marketId responses =
        responses |> Array.pick (function
                                  | Market(x) when x.market.marketId = marketId -> Some(x)
                                  | _ -> None)

    let FindAllMarkets = Array.choose (function
                                        | Market(x) -> Some(x)
                                        | _ -> None)
        
    let FindAllPrices = Array.choose (function
                                       | Prices(x) -> Some(x)
                                       | _ -> None)
        
    let FindAllEvents = Array.choose (function
                                       | Event(x) -> Some(x)
                                       | _ -> None)
        
