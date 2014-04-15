if $('.instructor-dashboard-wrapper').length == 1
    analytics.track "edx.bi.course.legacy_instructor_dashboard.loaded", 
        category: "courseware"
        location: window.location.pathname
        dashboard_page: $('.navbar .selectedmode').text()
