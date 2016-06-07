$ ->
  if window.navigator.appName is "Microsoft Internet Explorer"
  	isMPInstalled = (boolean) ->
  	# check if MathPlayer is installed
  	# (from http://www.dessci.com/en/products/mathplayer/check.htm)
  		try
  			oMP = new ActiveXObject("MathPlayer.Factory.1")
  			true
  		catch e
  			false

  	# detect if there is mathjax on the page
  	# if not, set 'aria-hidden' to 'true'
  	if MathJax? and not isMPInstalled()
  		$("#mathjax-accessibility-message").attr("aria-hidden", "false")

  	if MathJax? and $("#mathplayer-browser-message").length > 0
  		$("#mathplayer-browser-message").attr("aria-hidden", "false")
		
  	else
  		$("#mathjax-accessibility-message").attr("aria-hidden", "true")
