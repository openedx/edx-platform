function getParameters(){
    var paramstr = window.location.search.substr(1);
    var args = paramstr.split("&");
    var params = {};

    for (var i=0; i < args.length; i++){
        var temparray = args[i].split("=");
        params[temparray[0]] = temparray[1];
    }

    return params;
}

function getSearchAction(){
    var urlSplit = document.URL.split("/");
    var courseIndex = urlSplit.indexOf("courses");
    var searchAction = urlSplit.slice(courseIndex, courseIndex+4);
    searchAction.push("search");
    return searchAction.join("/");
}

function constructSearchBox(value){
    var searchWrapper = document.createElement("div");
    searchWrapper.className = "animated fadeInRight search-wrapper";
    searchWrapper.id = "search-wrapper";

    var searchForm = document.createElement("form");
    searchForm.className = "auto-submit";
    searchForm.id = "query-box";
    searchForm.action = "/"+getSearchAction();
    searchForm.method = "get";

    var searchBoxWrapper = document.createElement("div");
    searchBoxWrapper.className = "searchbox-wrapper";

    var searchBox = document.createElement("input");
    searchBox.id = "searchbox";
    searchBox.type = "text";
    searchBox.className = "searchbox parameter";
    searchBox.name = "s";
    searchBox.value = value;

    searchBoxWrapper.appendChild(searchBox);
    searchForm.appendChild(searchBoxWrapper);
    searchWrapper.appendChild(searchForm);

    return searchWrapper;
}

function replaceWithSearch(){
    $(this).addClass("animated fadeOut");
    var searchWrapper = constructSearchBox("");
    var width = $("div.search-icon").width();
    var height = $("div.search-icon").height();
    $(this).on('webkitAnimationEnd oanimationend oAnimationEnd msAnimationEnd animationend',
        function (e){
            $(this).parent().replaceWith(searchWrapper);
            $("#searchbox").css("width", width);
            $("#searchbox").css("height", height);
            if (document.URL.indexOf("search?s=") == -1){
                document.getElementById("searchbox").focus();
        }
    });
}

function updateOldSearch(){
    var params = getParameters();
    var newBox = constructSearchBox(old_query);
    var courseTab = $("a.search-bar").get(0);
    if (typeof courseTab != 'undefined'){
        courseTab.parentNode.replaceChild(newBox, courseTab);
    }
}

function paginate(element){
    var currentResults = parseInt($("._currentFilter span.count").text(), 10);
    $(element).pagination({
        items           : currentResults,
        itemsOnPage     : 10,
        currentPage     : page,
        displayedPages  : 3,
        edges           : 2,
        cssStyle        : "light-theme",
        onPageClick     : function(pageNumber, event){
            console.log("Hooray!");
            event.preventDefault();
            replaceCurrentContent(current_filter, pageNumber);
        }
    });
}

function moveFilterClasses(){
    /**
    * Keeps all of the classes related to filters on the proper DOM elements on update
    *
    * We are indicating current filter by assigning a class to the element in the DOM.
    * This function makes sure that these classes stay on the correct elements.
    */

    $("._currentFilter").removeClass("_currentFilter");
    if (document.location.href.match(/filter=\w+/)){
        var currentFilter = document.location.href.match(/filter=(\w+)/)[1];
        var newFilter = $("#"+currentFilter);
        newFilter.addClass("_currentFilter");
    }
    else {
        $("#all").addClass("_currentFilter");
    }
}

function getSearchResults(resultsObject, filter, current_page){
    /**
    * Returns relevant portion of search results
    * Assume that results Object will just be a parsed version of the
    * search_results variable passed in from the template.
    */

    return resultsObject[filter].results[current_page];
}

function renderSearchResult(searchResult){
    /**
    * Renders the given search result into a contained section element
    */

    var resultTitle = document.createElement("h1");
    resultTitle.className = "result-title";
    resultTitle.innerHTML = searchResult.data.display_name;

    var category = document.createElement("span");
    category.className = searchResult.category + "-image";

    var resultHeader = document.createElement("div");
    resultHeader.className = "result-header";
    resultHeader.appendChild(category);
    resultHeader.appendChild(resultTitle);

    var thumbnail = document.createElement("img");
    thumbnail.className = "thumbnail";
    if (searchResult.thumbnail !== undefined){
        thumbnail.src = searchResult.thumbnail;
        thumbnail.alt = searchResult.data.display_name;
    }

    var resultThumbnail = document.createElement("div");
    resultThumbnail.className = "result-thumbnail";
    resultThumbnail.appendChild(thumbnail);

    var thumbnailWrapper = document.createElement("div");
    thumbnailWrapper.className = "thumbnail-wrapper";
    thumbnailWrapper.appendChild(resultThumbnail);

    var snippets = document.createElement("div");
    snippets.className = "snippet";
    snippets.innerHTML = searchResult.snippets;

    var resultSnippets = document.createElement("div");
    resultSnippets.className = "result-snippets";
    resultSnippets.appendChild(snippets);

    var resultBody = document.createElement("div");
    resultBody.className = "result-body";
    resultBody.appendChild(thumbnailWrapper);
    resultBody.appendChild(resultSnippets);

    var resultContainer = document.createElement("div");
    resultContainer.className = "result-container";
    resultContainer.appendChild(resultHeader);
    resultContainer.appendChild(resultBody);

    var link = document.createElement('a');
    link.href = searchResult.url;
    link.appendChild(resultContainer);
    
    var section = document.createElement("section");
    section.appendChild(link);
    
    return section;

}

function replaceCurrentContent(filter, current_page){
    /**
    * Replaces the current content of search contents
    */

    var searchResults = jQuery.parseJSON(search_results);
    var relevantPage = getSearchResults(searchResults, filter, current_page);
    if (relevantPage !== undefined){
        $("div.search-container section").remove();
        for (var i=0; i<relevantPage.length; i++){
            $("div.search-container").append(renderSearchResult(relevantPage[i]));
        }
    }
    else {
        var newQueryString = "?s=" + old_query + "&filter=" + filter + "&page=" + current_page;
        var newUrl = document.location.origin + document.location.pathname + newQueryString;
        window.location.href = newUrl;
    }
}

function changeFilter(){
    /**
    * Changes the filter get parameter in the URL and does a redirect
    *
    * Assumes that when changing filters the user wants to go back to the first page of results
    */

    var newFilter = $(this).attr("id");
    replaceCurrentContent(newFilter, 1);
}

$(document).ready(function(){
    moveFilterClasses();
    if (typeof old_query !== "undefined"){
        updateOldSearch();
    } else {
        $("a.search-bar").bind("click", replaceWithSearch);
    }

    if ($("p.pagination-stub").length > 0) {
        paginate($("p.pagination-stub").eq(0));
    }

    $("ul.filter-menu li").bind("click", changeFilter);
});

