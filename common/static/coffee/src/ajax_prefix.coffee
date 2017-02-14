@AjaxPrefix =
    addAjaxPrefix: (jQuery, prefix) -> 
        jQuery.postWithPrefix = (url, data, callback, type) ->
            $.post("#{prefix()}#{url}", data, callback, type)

        jQuery.getWithPrefix = (url, data, callback, type) ->
            $.get("#{prefix()}#{url}", data, callback, type)

        jQuery.ajaxWithPrefix = (url, settings) ->
            if settings?
                $.ajax("#{prefix()}#{url}", settings)
            else
                settings = url
                settings.url = "#{prefix()}#{settings.url}"
                $.ajax settings

