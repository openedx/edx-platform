# Instructor Dashboard Manager
# TODO add deep linking

log = -> console.log.apply console, arguments

CSS_INSTRUCTOR_CONTENT = 'instructor-dashboard-content-2'
CSS_ACTIVE_SECTION = 'active-section'
CSS_IDASH_SECTION = 'idash-section'

$ =>
  instructor_dashboard_content = $ ".#{CSS_INSTRUCTOR_CONTENT}"
  if instructor_dashboard_content.length != 0
    setup_instructor_dashboard instructor_dashboard_content

setup_instructor_dashboard = (idash_content) =>
  links = idash_content.find('.instructor_nav').find('a')
  log 'links', links
  for link in ($ link for link in links)
    log 'link', link

    link.click ->
      log 'link click', link

      idash_content.find(".#{CSS_IDASH_SECTION}").removeClass CSS_ACTIVE_SECTION
      section_name = $(this).data 'section'
      section = idash_content.find "##{section_name}"
      section.addClass CSS_ACTIVE_SECTION

      log section_name
