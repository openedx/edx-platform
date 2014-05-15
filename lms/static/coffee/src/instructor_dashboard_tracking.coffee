if $('.instructor-dashboard-wrapper').length == 1
    analytics.track "Loaded a Legacy Instructor Dashboard Page", 
        location: window.location.pathname
        dashboard_page: $('.navbar .selectedmode').text()
