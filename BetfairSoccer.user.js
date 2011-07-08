// ==UserScript==
// @name          BBC Betfair Soccer
// @namespace http://www.betfair.com/
// @include       http://news.bbc.co.uk/sport1/*
// @description Injects Betfair market links and prices into BBC Sport pages
// ==/UserScript==

window.addEventListener(
    'load',
    function() {
        // get fixtures from betfair
        GM_xmlhttpRequest({
            method: 'GET',
            url: 'http://search.betfair.com/ResultsRSS.do?query=soccer%20fixtures%20match%20odds',
            headers: {
                'User-agent': 'Mozilla/4.0 (compatible) Greasemonkey',
            },
            onload: function(responseDetails) {
                var parser = new DOMParser();
                var xml = parser.parseFromString(responseDetails.responseText, "application/xml");
                processDoc("//div[@class='mvb' or @class='arr' or @class='sh' or @class='mxb']", xml);
            }
        });    
    }, true); 
    
function processDoc(xpath, fixturesXml) {
    nodeList = document.evaluate (xpath, document, null, XPathResult.UNORDERED_NODE_SNAPSHOT_TYPE, null);
    fixtures = parsePremiershipFixtures(fixturesXml);

    // find matches between betfair search results and fixtures on current page
    for (var i = 0; i < nodeList.snapshotLength; i++ ) {
        var txt = nodeList.snapshotItem(i).textContent;
        for (var j = 0; j < fixtures.length; j++) {
            if (txt.match(fixtures[j].marketName)) {
                // found a fixture on the page with a corresponding betfair market - add a link
                createBetfairLink(nodeList.snapshotItem(i), fixtures[j]);
            }
        }
    }
}

function parsePremiershipFixtures(fixturesXml) {
    var items = fixturesXml.getElementsByTagName("item");
    var mo_regex = /^Soccer\/(.+?)\/ Match Odds$/;
    var mi_regex = /.*mi=(\d+).*/;
    var prem = [];
    
    for (var i = 0; i < items.length; i++) {
        // check title node to see if we have a match odds market
        var title = items[i].getElementsByTagName("title")[0].textContent;
        var match = mo_regex.exec(title);

        if (match != null) {
            // bingo! now get market id by parsing link
            var name = match[1];
            var link = items[i].getElementsByTagName("link")[0].textContent;
            var id = mi_regex.exec(link)[1];
            
            // return info in handy object form
            prem.push({marketName: name, link: link, marketId: id});
        }
    }
    
    return prem;
}

function handleMouseover(event) {
    // get the market id
    var market_id = /^bflink-(\d+)$/.exec(event.target.getAttribute('id'))[1];
    GM_log('requesting prices for ' + market_id);
    GM_xmlhttpRequest({
        method: 'GET',
        url: 'http://rest.labs.betfair.com/market/' + market_id + '/runners?extend=price&format=json',
        headers: {
            'User-agent': 'Mozilla/4.0 (compatible) Greasemonkey',
        },
        onload: function(responseDetails) {
            eval('data = ' + responseDetails.responseText);
            
            var runners = data.list.runner;
            var s = "Betfair prices: ";
            var first = true;
            
            for (var i in runners) {
                if (first) first = false;
                else s += ", ";
                 s += runners[i].name + " (" + runners[i].price.bestBackPrice + ")";
            }
            
            event.target.setAttribute('title', s);
        }
    }, true);
}
    
function createBetfairLink(ele, fixture) {
    var link = document.createElement('a');
    link.setAttribute('href', fixture.link);
    var img = document.createElement('img');
    img.setAttribute('id', 'bflink-' + fixture.marketId);
    img.setAttribute('src', 'http://www.betfair.com/favicon.ico');
    img.setAttribute('border', '0');
    img.setAttribute('hspace', '3');
    img.addEventListener('mouseover', handleMouseover, true);
    link.appendChild(img);
    ele.appendChild(link);
}