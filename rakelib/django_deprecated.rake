# django assets tasks deprecated to paver

require 'colorize'

def deprecated(deprecated, deprecated_by)

    task deprecated, [:arg1, :arg2, :arg3, :arg4] do |t,args|

        # Need to install paver dependencies for the commands to work!
        sh("pip install Paver==1.2.1 psutil==1.2.1 lazy==1.1 path.py==3.0.1")

        if deprecated == "cms" or deprecated == "lms"
            args.with_defaults(:arg1 => "dev", :arg2 => "")
            port = args.arg2 == "" ? "" : "--port=#{args.arg2}"
            new_cmd = deprecated_by + " --settings=#{args.arg1} #{port}"
        else
            new_cmd = deprecated_by
        end

        puts("Task #{deprecated} has been deprecated. Use #{new_cmd} instead. Waiting 5 seconds...".red)
        sleep(5)
        sh(new_cmd)
        exit
    end
end

deprecated('lms','paver lms')
deprecated('fastlms', 'paver lms --fast')

deprecated('cms','paver studio')
deprecated('fastcms', 'paver studio --fast')

deprecated('cms:clone', 'python manage.py cms -h')
deprecated('cms:delete_course', 'python manage.py cms -h')
deprecated('cms:export', 'python manage.py cms -h')
deprecated('cms:import', 'python manage.py cms -h')
deprecated('cms:xlint', 'python manage.py cms -h')
deprecated('set_staff', 'python manage.py cms -h')

deprecated("django-admin", "python manage.py -h")
deprecated("resetdb", "paver update_db")


[:lms, :cms].each do |system|

    deprecated("#{system}:resetdb", "paver update_db")
    deprecated("#{system}_worker", "paver celery")

    environments(system).each do |env|
      deprecated("#{system}:resetdb:#{env}", "paver update_db")
      deprecated("#{system}:#{env}", "paver #{system} --settings=#{env}")
      deprecated("#{system}:check_settings:#{env}", "paver check_settings #{system} #{env}")
    end

end
