# Instructor Dashboard Tab Manager

log = -> console.log.apply console, arguments

CSS_INSTRUCTOR_CONTENT = 'instructor-dashboard-content-2'
CSS_ACTIVE_SECTION = 'active-section'
CSS_IDASH_SECTION = 'idash-section'
CSS_IDASH_DEFAULT_SECTION = 'idash-default-section'
CSS_INSTRUCTOR_NAV = 'instructor-nav'

HASH_LINK_PREFIX = '#view-'


# once we're ready, check if this page has the instructor dashboard
$ =>
  instructor_dashboard_content = $ ".#{CSS_INSTRUCTOR_CONTENT}"
  if instructor_dashboard_content.length != 0
    log "setting up instructor dashboard"
    setup_instructor_dashboard          instructor_dashboard_content
    setup_instructor_dashboard_sections instructor_dashboard_content


# enable links
setup_instructor_dashboard = (idash_content) =>
  links = idash_content.find(".#{CSS_INSTRUCTOR_NAV}").find('a')
  for link in ($ link for link in links)
    link.click (e) ->
      idash_content.find(".#{CSS_IDASH_SECTION}").removeClass CSS_ACTIVE_SECTION
      idash_content.find(".#{CSS_INSTRUCTOR_NAV}").children().removeClass CSS_ACTIVE_SECTION
      section_name = $(this).data 'section'
      section = idash_content.find "##{section_name}"
      section.addClass CSS_ACTIVE_SECTION
      $(this).addClass CSS_ACTIVE_SECTION

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


# enable sections
setup_instructor_dashboard_sections = (idash_content) ->
  window.x = idash_content
  setup_section_data_download idash_content.find(".#{CSS_IDASH_SECTION}#data-download")

setup_section_data_download = (section) ->
  grade_config_btn = section.find("input[value='Grading Configuration']'")
  grade_config_btn.click (e) ->
    log "fetching grading config"
    $.getJSON grade_config_btn.data('endpoint'), (data) ->
      section.find('.dumped-data-display').html data['grading_config_summary']

  list_studs_btn = section.find("input[value='List enrolled students with profile information']'")
  list_studs_btn.click (e) ->
    log "fetching student list"
    $.getJSON list_studs_btn.data('endpoint'), (data) ->
      section.find('.dumped-data-display').text JSON.stringify(data)
