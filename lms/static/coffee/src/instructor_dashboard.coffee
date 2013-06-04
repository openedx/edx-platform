# Instructor Dashboard Manager

log = -> console.log.apply console, arguments

CSS_INSTRUCTOR_CONTENT = 'instructor-dashboard-content-2'
CSS_ACTIVE_SECTION = 'active-section'
CSS_IDASH_SECTION = 'idash-section'
CSS_IDASH_DEFAULT_SECTION = 'idash-default-section'

HASH_LINK_PREFIX = '#viewing-'

$ =>
  instructor_dashboard_content = $ ".#{CSS_INSTRUCTOR_CONTENT}"
  if instructor_dashboard_content.length != 0
    setup_instructor_dashboard instructor_dashboard_content

setup_instructor_dashboard = (idash_content) =>
  links = idash_content.find('.instructor_nav').find('a')
  for link in ($ link for link in links)
    link.click (e) ->
      idash_content.find(".#{CSS_IDASH_SECTION}").removeClass CSS_ACTIVE_SECTION
      section_name = $(this).data 'section'
      section = idash_content.find "##{section_name}"
      section.addClass CSS_ACTIVE_SECTION

      location.hash = "#{HASH_LINK_PREFIX}#{section_name}"

      log "clicked #{section_name}"
      e.preventDefault()

  # click default or go to section specified by hash
  if (new RegExp "^#{HASH_LINK_PREFIX}").test location.hash
    rmatch = (new RegExp "^#{HASH_LINK_PREFIX}(.*)").exec location.hash
    section_name = rmatch[1]
    link = links.filter "[data-section='#{section_name}']"
    link.click()
  else
    links.filter(".#{CSS_IDASH_DEFAULT_SECTION}").click()
