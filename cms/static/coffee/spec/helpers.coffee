# Stub jQuery.cookie
@stubCookies =
  csrftoken: 'stubCSRFToken'

jQuery.cookie = (key, value) =>
  if value?
    @stubCookies[key] = value
  else
    @stubCookies[key]
