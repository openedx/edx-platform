# Instructor Dashboard Tab Manager

log = -> console.log.apply console, arguments
plantTimeout = (ms, cb) -> setTimeout cb, ms

CSS_INSTRUCTOR_CONTENT = 'instructor-dashboard-content-2'
CSS_ACTIVE_SECTION = 'active-section'
CSS_IDASH_SECTION = 'idash-section'
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
  # setup section header click handlers
  for link in ($ link for link in links)
    link.click (e) ->
      e.preventDefault()
      # deactivate (styling) all sections
      idash_content.find(".#{CSS_IDASH_SECTION}").removeClass CSS_ACTIVE_SECTION
      idash_content.find(".#{CSS_INSTRUCTOR_NAV}").children().removeClass CSS_ACTIVE_SECTION

      # find paired section
      section_name = $(this).data 'section'
      section = idash_content.find "##{section_name}"

      # activate (styling) active
      section.addClass CSS_ACTIVE_SECTION
      $(this).addClass CSS_ACTIVE_SECTION

      # write deep link
      location.hash = "#{HASH_LINK_PREFIX}#{section_name}"

      plantTimeout 0, -> section.data('wrapper')?.onClickTitle?()

  # recover deep link from url
  # click default or go to section specified by hash
  if (new RegExp "^#{HASH_LINK_PREFIX}").test location.hash
    rmatch = (new RegExp "^#{HASH_LINK_PREFIX}(.*)").exec location.hash
    section_name = rmatch[1]
    link = links.filter "[data-section='#{section_name}']"
    link.click()
  else
    links.eq(0).click()


# call setup handlers for each section
setup_instructor_dashboard_sections = (idash_content) ->
  log "setting up instructor dashboard sections"
  # fault isolation
  # an error thrown in one section will not block other sections from exectuing
  plantTimeout 0, -> new window.InstructorDashboard.sections.CourseInfo idash_content.find ".#{CSS_IDASH_SECTION}#course_info"
  plantTimeout 0, -> new window.InstructorDashboard.sections.DataDownload idash_content.find ".#{CSS_IDASH_SECTION}#data_download"
  plantTimeout 0, -> new window.InstructorDashboard.sections.Membership   idash_content.find ".#{CSS_IDASH_SECTION}#membership"
  plantTimeout 0, -> new window.InstructorDashboard.sections.StudentAdmin idash_content.find ".#{CSS_IDASH_SECTION}#student_admin"
  plantTimeout 0, -> new window.InstructorDashboard.sections.Analytics    idash_content.find ".#{CSS_IDASH_SECTION}#analytics"
