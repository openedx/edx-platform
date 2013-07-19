# Instructor Dashboard Tab Manager
# The instructor dashboard is broken into sections.
# Only one section is visible at a time,
#   and is responsible for its own functionality.
#
# NOTE: plantTimeout (which is just setTimeout from util.coffee)
#       is used frequently in the instructor dashboard to isolate
#       failures. If one piece of code under a plantTimeout fails
#       then it will not crash the rest of the dashboard.
#
# NOTE: The instructor dashboard currently does not
#       use backbone. Just lots of jquery. This should be fixed.
#
# NOTE: Server endpoints in the dashboard are stored in
#       the 'data-endpoint' attribute of relevant html elements.
#       The urls are rendered there by a template.
#
# NOTE: For an example of what a section object should look like
#       see course_info.coffee

# imports from other modules
# wrap in (-> ... apply) to defer evaluation
# such that the value can be defined later than this assignment (file load order).
plantTimeout = -> window.InstructorDashboard.util.plantTimeout.apply this, arguments
std_ajax_err = -> window.InstructorDashboard.util.std_ajax_err.apply this, arguments

# CSS classes
CSS_INSTRUCTOR_CONTENT = 'instructor-dashboard-content-2'
CSS_ACTIVE_SECTION = 'active-section'
CSS_IDASH_SECTION = 'idash-section'
CSS_INSTRUCTOR_NAV = 'instructor-nav'

# prefix for deep-linking
HASH_LINK_PREFIX = '#view-'

# once we're ready, check if this page is the instructor dashboard
$ =>
  instructor_dashboard_content = $ ".#{CSS_INSTRUCTOR_CONTENT}"
  if instructor_dashboard_content.length > 0
    setup_instructor_dashboard          instructor_dashboard_content
    setup_instructor_dashboard_sections instructor_dashboard_content


# enable navigation bar
# handles hiding and showing sections
setup_instructor_dashboard = (idash_content) =>
  # clickable section titles
  links = idash_content.find(".#{CSS_INSTRUCTOR_NAV}").find('a')

  for link in ($ link for link in links)
    link.click (e) ->
      e.preventDefault()

      # deactivate all link & section styles
      idash_content.find(".#{CSS_INSTRUCTOR_NAV}").children().removeClass CSS_ACTIVE_SECTION
      idash_content.find(".#{CSS_IDASH_SECTION}").removeClass CSS_ACTIVE_SECTION

      # discover section paired to link
      section_name = $(this).data 'section'
      section = idash_content.find "##{section_name}"

      # activate link & section styling
      $(this).addClass CSS_ACTIVE_SECTION
      section.addClass CSS_ACTIVE_SECTION

      # tracking
      # analytics.pageview "instructor_#{section_name}"

      # deep linking
      # write to url
      location.hash = "#{HASH_LINK_PREFIX}#{section_name}"

      plantTimeout 0, -> section.data('wrapper')?.onClickTitle?()
      # plantTimeout 0, -> section.data('wrapper')?.onExit?()


  # activate an initial section by 'clicking' on it.
  # check for a deep-link, or click the first link.
  click_first_link = ->
    link = links.eq(0)
    link.click()
    link.data('wrapper')?.onClickTitle?()

  if (new RegExp "^#{HASH_LINK_PREFIX}").test location.hash
    rmatch = (new RegExp "^#{HASH_LINK_PREFIX}(.*)").exec location.hash
    section_name = rmatch[1]
    link = links.filter "[data-section='#{section_name}']"
    if link.length == 1
      link.click()
      link.data('wrapper')?.onClickTitle?()
    else
      click_first_link()
  else
    click_first_link()



# enable sections
setup_instructor_dashboard_sections = (idash_content) ->
  # see fault isolation NOTE at top of file.
  # an error thrown in one section will not block other sections from exectuing.
  plantTimeout 0, -> new window.InstructorDashboard.sections.CourseInfo   idash_content.find ".#{CSS_IDASH_SECTION}#course_info"
  plantTimeout 0, -> new window.InstructorDashboard.sections.DataDownload idash_content.find ".#{CSS_IDASH_SECTION}#data_download"
  plantTimeout 0, -> new window.InstructorDashboard.sections.Membership   idash_content.find ".#{CSS_IDASH_SECTION}#membership"
  plantTimeout 0, -> new window.InstructorDashboard.sections.StudentAdmin idash_content.find ".#{CSS_IDASH_SECTION}#student_admin"
  plantTimeout 0, -> new window.InstructorDashboard.sections.Analytics    idash_content.find ".#{CSS_IDASH_SECTION}#analytics"
