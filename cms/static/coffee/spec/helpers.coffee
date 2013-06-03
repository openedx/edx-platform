jasmine.getFixtures().fixturesPath = 'fixtures'

# Stub jQuery.cookie
@stubCookies =
  csrftoken: "stubCSRFToken"

jQuery.cookie = (key, value) =>
  if value?
    @stubCookies[key] = value
  else
    @stubCookies[key]

# Path Jasmine's `it` method to raise an error when the test is not defined.
# This is helpful when writing the specs first before writing the test.
@it = (desc, func) ->
  if func?
    jasmine.getEnv().it(desc, func)
  else
    jasmine.getEnv().it desc, ->
      throw "test is undefined"
