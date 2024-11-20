/*
 * This is a high level diagram visualizing how the system revokes course and program certificates. It is written using
 * Structurizr DSL (https://structurizr.org/).
 */
workspace {
    model {
        properties {
            "structurizr.groupSeparator" "/"
        }
        event_bus = softwareSystem "Event Bus"

        group "LMS" {
            grades_app = softwareSystem "Grades Django app"
            group "Certificates app" {
                signal_handlers = softwareSystem "Certificates Signal Handlers"
            }
            credentials_app = softwareSystem "Credentials Django app"
            programs_app = softwareSystem "Programs Django App"
            celery = softwareSystem "Celery"
            database = softwareSystem "Database"
        }

        group "Credentials IDA" {
            credentials_ida_consumer = softwareSystem "Credentials Event Bus Consumer"
            credentials_api_app = softwareSystem "Credentials API Django App"
            credentials_credentials_app = softwareSystem "Credentials Django App"
        }

        grades_app -> signal_handlers "Emits COURSE_GRADE_NOW_FAILED signal"
        signal_handlers -> database "Update certificate's status to NOT_PASSING"
        database -> event_bus "Emits a CERTIFICATE_REVOKED event"
        credentials_ida_consumer -> event_bus "Listening for Certificate events"
        credentials_ida_consumer -> credentials_credentials_app "Revoke Certificate record"
        database -> programs_app "On save(), emits a COURSE_CERT_CHANGED signal"
        database -> programs_app "On save(), emits a COURSE_CERT_REVOKED signal"
        // The following line is correct, an `award_course_certificate` task is queued whether we award or revoke a
        // course certificate. It handles both operations.
        programs_app -> celery "Enqueue award_course_certificate task"
        programs_app -> celery "Enqueue revoke_program_certificate task"
        celery -> credentials_app "Process award_course_certificate task"
        celery -> credentials_app "Process revoke_program_certificate task"
        credentials_app -> credentials_api_app "POST request to revoke course credential"
        credentials_app -> credentials_api_app "POST request to revoke program credential"
    }

    views {
        systemLandscape "SystemLandscape" {
            include *
            autolayout lr
        }

        styles {
            element "Database" {
                shape Cylinder
            }
        }
    }
}
