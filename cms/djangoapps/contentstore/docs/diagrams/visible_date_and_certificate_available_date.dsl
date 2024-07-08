/*
 * This is a high level diagram visualizing how the `CERTIFICATE_AVAILBLE_DATE` and "visible date" attribute updates
 * are updated internally and transmit to the Credentials IDA.
 *
 * It is written using Structurizr DSL (https://structurizr.org/).
 */
workspace {
    model {
        properties {
            "structurizr.groupSeparator" "/"
        }
        author = person "Course Author" "External user from partner org with course authoring privileges in the CMS"
        credentials = softwareSystem "Credentials IDA"
        group "edx-platform" {
            modulestore = element "edx-platform Mongo DB"
            monolith_db = element "edx-platform Relational DB"
            celery = softwareSystem "Celery"

            group "CMS" {
                studio = softwareSystem "CMS FrontEnd"
                contentstore_app = softwareSystem "Contentstore Django app"
            }
            group "CORE (shared)" {
                co_app = softwareSystem "CourseOverview Django App"
                programs_app = softwareSystem "Programs Django App"
            }
        }

        author -> studio "Updates certificate available date setting"
        studio -> contentstore_app "Processes course settings update"
        contentstore_app -> modulestore "Saves course settings update"
        contentstore_app -> co_app "Emits COURSE PUBLISHED signal"
        co_app -> modulestore "Retrieves course details from Mongo"
        co_app -> monolith_db "Updates CourseOverview record"
        co_app -> programs_app "Emits COURSE_CERT_DATE_CHANGED signal"
        programs_app -> celery "Enqueue UPDATE_CERTIFICATE_VISIBLE_DATE task"
        programs_app -> celery "Enqueue UPDATE_CERTIFICATE_AVAILABLE_DATE task"
        celery -> credentials "REST requests to update `visible_date` attributes"
        celery -> credentials "REST request to update `certificate_available_date` setting"
    }

    views {
        systemLandscape "SystemLandscape" {
            include *
            autolayout lr
        }
    }
}
