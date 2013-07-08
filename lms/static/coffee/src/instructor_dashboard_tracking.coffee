if $('.instructor-dashboard-wrapper').length == 1
    analytics.track "Loaded an Instructor Dashboard Page", 
        location: window.location.pathname
        dashboard_page: $('.navbar .selectedmode').text()
