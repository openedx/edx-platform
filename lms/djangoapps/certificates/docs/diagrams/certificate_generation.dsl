/*
 * This is a high level diagram visualizing how the system awards course and program certificates. It is written using
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
            verify_student_app = softwareSystem "Verify Student app"
            student_app = softwareSystem "Student app"
            group "Certificates app" {
                signal_handlers = softwareSystem "Certificates Signal Handlers"
                generation_handler = softwareSystem "Certificates Generation Handler"
                allowlist = softwareSystem "Certificate AllowList"
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

        grades_app -> signal_handlers "Emits COURSE_GRADE_NOW_PASSED signal"
        verify_student_app -> signal_handlers "Emits IDV_ATTEMPT_APPROVED signal"
        verify_student_app -> signal_handlers "Emits LEARNER_SSO_VERIFIED signal"
        verify_student_app -> signal_handlers "Emits PHOTO_VERIFICATION_APPROVED signal"
        student_app -> signal_handlers "Emits ENROLLMENT_TRACK_UPDATED signal"
        allowlist -> signal_handlers "Emits APPEND_CERTIFICATE_ALLOWLIST signal"
        signal_handlers -> generation_handler "Invokes generate_allowlist_certificate()"
        signal_handlers -> generation_handler "Invokes generate_regular_certificate()"
        generation_handler -> celery "Enqueues generate_certificate_task task"
        celery -> database "UPSERT certificate record to database"
        database -> event_bus "Emits a CERTIFICATE_CREATED event"
        database -> programs_app "Emits a COURSE_CERT_CHANGED signal"
        credentials_ida_consumer -> event_bus "Listening for Certificate events"
        database -> programs_app "If passing, emits a COURSE_CERT_AWARDED signal"
        programs_app -> celery "Enqueue award_course_certificate task"
        programs_app -> celery "Enqueue award_program_certificate task"
        celery -> credentials_app "Process award_course_certificate task"
        celery -> credentials_app "Process award_program_certificate task"
        credentials_app -> credentials_api_app "POST request to award course credential"
        credentials_app -> credentials_api_app "POST request to award program credential"
        credentials_ida_consumer -> credentials_credentials_app "Award Certificate record"
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
