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

function replaceWithSearch(){
    var searchWrapper = document.createElement("div");
    searchWrapper.className = "search-wrapper";

    var searchForm = document.createElement("form");
    searchForm.className = "auto-submit";
    searchForm.id = "query-box";
    searchForm.action = "/search";
    searchForm.method = "get";

    var searchBoxWrapper = document.createElement("div");
    searchBoxWrapper.className = "searchbox-wrapper";

    var searchBox = document.createElement("input");
    searchBox.id = "searchbox";
    searchBox.type = "text";
    searchBox.className = "searchbox parameter";
    searchBox.name = "s";

    searchBoxWrapper.appendChild(searchBox);
    searchForm.appendChild(searchBoxWrapper);
    searchWrapper.appendChild(searchForm);
    this.parentNode.replaceChild(searchWrapper, this);
}

$(document).ready(function(){
    $("li a:contains('Search')").bind("click", replaceWithSearch);
});

