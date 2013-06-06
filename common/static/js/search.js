function correctionLink(event, spelling_correction){
    $("#searchbox")[0].value = spelling_correction;
    submitForms(false);
}

function submitForms(retain_page) {
    var get_data = [];
    var form_list = $(".auto-submit .parameter");
    for (var i in form_list){
        get_data.push.apply(get_data, form_list.eq(i).serializeArray());
    }
    var url = document.URL.split("?")[0]+"?";
    for (var o in get_data){
        if (retain_page === false){
            if (get_data[o].name == "page"){
                get_data[o].value = 1;
            }
        }
        url = url + (get_data[o].name + "=" +get_data[o].value + "&");
    }
    document.location.href = url.substring(0, url.length-1);
}

function incrementPage(){
    var current_page = $("#current-page input");
    current_page[0].value++;
    submitForms(true);
}

function decrementPage(){
    var current_page = $("#current-page input");
    current_page[0].value--;
    submitForms(true);
}

function clickHandle(e, retain_page){
    e.preventDefault();
    submitForms(retain_page);
}

function searchHandle(e, retain_page){
    if(e.keyCode === 13){
        e.preventDefault();
        submitForms(retain_page);
    }
}

function changeHandler(input, max_pages){
    if (input.value < 1) {input.value=1;}
    if (input.value > max_pages) {input.value=max_pages;}
}

function filterTrigger(input, type, retain_page){
    if (type == "org"){
        $("#selected-org").val($($(input).children(":first")).text());
    }

    if (type == "course"){
        $("#selected-course").val($(input).children(":first").text());
    }

    submitForms(retain_page);
}

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

function constructSearchBox(value){
    var searchWrapper = document.createElement("div");
    searchWrapper.className = "search-wrapper";
    searchWrapper.id = "search-wrapper";

    var searchForm = document.createElement("form");
    searchForm.className = "auto-submit";
    searchForm.id = "query-box";
    searchForm.action = "search";
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
    var searchWrapper = constructSearchBox("");
    this.parentNode.replaceChild(searchWrapper, this);
    if (document.URL.indexOf("search?s=") == -1){
        document.getElementById("searchbox").focus();
    }
}

function updateOldSearch(){
    var params = getParameters();
    var newBox = constructSearchBox(params.s);
    var courseTab = $("li a:contains('Search')").get(0);
    if (typeof courseTab != 'undefined'){
        courseTab.parentNode.replaceChild(newBox, courseTab);
    }
}

$(document).ready(function(){
    if (document.URL.indexOf("search?s=") !== -1){
        updateOldSearch();
    } else {
        $("li a:contains('Search')").bind("click", replaceWithSearch);
    }
});

