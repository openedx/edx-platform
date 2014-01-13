# django assets tasks deprecated to paver

require 'colorize'

def deprecated(deprecated, deprecated_by)

    namespace :cms do

       task deprecated, [:env, :options] do |t,args|

            puts("in cms")
            args.with_defaults(:env => "dev", :options => "")

            if deprecated == "cms" or deprecated == "lms"
                port = args.options == "" ? "" : "--port=#{args.options}"
                new_cmd = deprecated_by + " --env=#{args.env} #{port}"
            else
                new_cmd = deprecated_by
            end

            puts("Task #{deprecated} has been deprecated. Use #{new_cmd} instead. Waiting 5 seconds...".red)
            sleep(5)
            sh(new_cmd)
            exit
        end
    end

    task deprecated, [:arg1, :arg2, :arg3, :arg4] do |t,args|

        puts("#{deprecated}")
        if deprecated == "cms" or deprecated == "lms"
            args.with_defaults(:arg1 => "dev", :arg2 => "")
            port = args.arg2 == "" ? "" : "--port=#{args.arg2}"
            new_cmd = deprecated_by + " --env=#{args.arg1} #{port}"
        elsif deprecated == "set_staff"
            # arg1 == user, arg2 == system, arg3 == env
            args.with_defaults(:arg1 => "", :arg2 => "lms", :arg3 => "dev")
            new_cmd = deprecated_by + " --user=#{args.arg1} --system=#{args.arg2} --env=#{args.arg3}"
        elsif deprecated == "django-admin"
            # arg1 == action, arg2 == system, arg3 == env, arg4 == options
            args.with_defaults(:arg1 => "", :arg2 => "lms", :arg3 => "dev", :arg4 => "")
            new_cmd = deprecated_by + " --action=#{args.arg1} --system=#{args.arg2} --env=#{args.arg3} --options=#{args.arg4}"
        elsif deprecated == "cms:export"
            course_id = ENV['COURSE_ID']
            output_path = ENV['OUTPUT_PATH']
            new_cmd = deprecated_by + " --course_id=#{course_id} --output=#{output_path}"
        elsif deprecated == "cms:import" or deprecated == "cms:xlint"
            data_dir = ENV['DATA_DIR']
            course_dir = ENV['COURSE_DIR']
            new_cmd = deprecated_by + " --env=dev --course_dir=#{course_dir} --data_dir=#{data_dir}"
        elsif deprecated == "cms:delete_course"
            location = ENV['LOC']
            commit = ENV['COMMIT']
            new_cmd = deprecated_by + " --env=dev --location=#{location} --commit=#{commit}"
        elsif deprecated == "cms:clone"
            src = ENV['SOURCE_LOC']
            dest = ENV['DEST_LOC']
            new_cmd = deprecated_by + " --env=dev --src=#{src} --dest=#{dest}"
        else
            new_cmd = deprecated_by
        end

        puts("Task #{deprecated} has been deprecated. Use #{new_cmd} instead. Waiting 5 seconds...".red)
        sleep(5)
        sh(new_cmd)
        exit
    end
end

deprecated('cms','paver cms')
deprecated('cms:clone','paver clone_course')
deprecated('cms:delete_course','paver delete_course')
deprecated('cms:export','paver export_course')
deprecated('cms:import','paver import_course')
deprecated('cms:xlint', 'paver xlint_course')
deprecated('set_staff','paver set_staff')
deprecated("django-admin", "paver django_admin")


[:lms, :cms].each do |system|

    deprecated("resetdb", "paver resetdb")
    deprecated("#{system}:resetdb", "paver resetdb --system=#{system}")

    deprecated("#{system}", "paver #{system}")


    deprecated("#{system}_worker", "paver run_celery --system=#{system}")

    deprecated("fastlms", "paver fast_lms")

    environments(system).each do |env|
      deprecated("#{system}:resetdb:#{env}", "paver resetdb --system=#{system} --env=#{env}")
      deprecated("#{system}:${env}", "paver #{system} --env=#{env}")
      deprecated("#{system}:check_settings:#{env}", "paver check_settings --system=#{system} --env=#{env}")
    end

end
