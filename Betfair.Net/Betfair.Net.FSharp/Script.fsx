// This file is a script that can be executed with the F# Interactive.  
// It can be used to explore and test the library project.
// Note that script files will not be part of the project build.

#I @"C:\Users\grayr\Documents\Visual Studio 2008\Projects\Betfair.Net\Betfair.Net\bin\Debug"
#r "Betfair.Net.dll"

#load "Types.fs"
#load "Finders.fs"
#load "AsyncCore.fs"
#load "AsyncApi.fs"

open Betfair.Net.BFGlobal
open Betfair.Net.BFExchange
open Betfair.Net.Fsharp.AsyncApi
open System.Text.RegularExpressions

let getEventDates sessionToken parent =
    let req = new GetEventsReq(header = MakeGlobalHeader sessionToken, eventParentId = parent)
    let evs = globalService.getEvents(req)
    evs.eventItems |> Array.filter (fun x -> Regex.IsMatch(x.eventName, "^Fixture.*"))
    
// Get flattened list of all AvB events under the specified list of events    
let getFlattenedEventItems sessionToken evs =
    evs |> getManyEvents sessionToken
        |> Array.map (fun x -> x.eventItems)
        |> Array.concat 
    
let getMatchOddsMarkets sessionToken fixtures =
    getManyEvents sessionToken fixtures
        |> Array.map (fun x -> x.marketItems)
        |> Array.concat
        |> Array.filter (fun x -> Regex.IsMatch(x.marketName, "^Match Odds$"))
        |> Array.map (fun x -> (Array.find (fun (e:BFEvent) -> e.eventId = x.eventParentId) fixtures, x))
        
let testPrem sessionToken =
    let dates = getEventDates sessionToken 2022802
    let fixtures = getFlattenedEventItems sessionToken dates
    let matchOdds = getMatchOddsMarkets sessionToken fixtures
    (dates, fixtures, matchOdds)
    
let r = login "" "" 204
let s = r.header.sessionToken

