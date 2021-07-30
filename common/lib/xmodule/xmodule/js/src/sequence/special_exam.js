(function(){
	window.onbeforeunload = function(event){
        /*
        Check if there are any unattempted problem in the sequence and
        show a window unload popup if there is.
        */
        var unattempted_problems = []
        var contents = $('.seq_contents')
        contents.each(function(idx) {
            var tempEl = $('<div></div>')
            // load the content of sequence in a temporary element
            edx.HtmlUtils.setHtml(tempEl, edx.HtmlUtils.HTML($(this).text()))
            var problems = $('.problems-wrapper', tempEl)
            problems.each(function(index) {
                var el = $(this)
                if (el.data('graded') && el.data('attempts-used') === 0) {
                    unattempted_problems.push(el)
                }
            })
        })
        if (unattempted_problems.length > 0) {
            event.preventDefault();
            return "You have unattempted question? Are you sure you want to leave?"
        }
	}
})();
