# assets tasks deprecated to paver

require 'colorize'

def deprecated(deprecated, deprecated_by,  *args)

    namespace :assets do

        task [:system, :env] do |t,args|

            puts("Task #{deprecated} has been deprecated. Use paver compile_assets instead. Waiting 5 seconds...".red)
            sleep(5)
            system = args[:system]
            env = args[:env]
            sh("paver compile_assets --system=#{system} --env=#{env}")
            exit
        end

        task :preprocess, [:system, :env] do |t,args|

            puts("Task #{deprecated} has been deprecated. Use paver compile_assets instead. Waiting 5 seconds...".red)
            sleep(5)
            system = args[:system]
            env = args[:env]
            sh("paver compile_assets --system=#{system} --env=#{env}")
            exit
        end

        task :coffee, [:system, :env] do |t,args|

            puts("Task #{deprecated} has been deprecated. Use paver compile_coffeescript instead. Waiting 5 seconds...".red)
            sleep(5)
            system = args[:system]
            env = args[:env]
            sh("paver compile_coffeescript --system=#{system} --env=#{env}")
            exit
        end

        task :sass, [:system, :env] do |t,args|

            puts("Task #{deprecated} has been deprecated. Use paver compile_sass instead. Waiting 5 seconds...".red)
            sleep(5)
            system = args[:system]
            env = args[:env]
            sh("paver compile_sass --system=#{system} --env=#{env}")
            exit
        end

        task :xmodule, [:system, :env] do |t,args|

            puts("Task #{deprecated} has been deprecated. Use paver compile_xmodule instead. Waiting 5 seconds...".red)
            sleep(5)
            system = args[:system]
            env = args[:env]
            sh("paver compile_xmodule --system=#{system} --env=#{env}")
            exit
        end

    end


    task deprecated do

        if args.length > 0 then
            args_str = args.join(',')
            new_cmd = "#{deprecated_by}[#{args_str}]"
            puts(args_str)
        else
            new_cmd = deprecated_by
        end

        puts("Task #{deprecated} has been deprecated. Use #{new_cmd} instead. Waiting 5 seconds...".red)
        sleep(5)
        sh(deprecated_by)
    end



end

deprecated("assets:coffee", "paver compile_coffeescript")
deprecated("assets:coffee:clobber", "paver compile_coffeescript --clobber")
deprecated("assets:coffee:debug", "paver compile_coffeescript --debug")
deprecated("assets:coffee:watch", "paver compile_coffeescript --watch")

deprecated("assets:sass", "paver compile_sass")
deprecated("assets:sass:debug", "paver compile_sass --debug")
deprecated("assets:sass:watch", "paver compile_sass --watch")

deprecated("assets:xmodule", "paver compile_xmodule")
deprecated("assets:xmodule:debug", "paver compile_xmodule --debug")
deprecated("assets:xmodule:watch", "paver compile_xmodule --watch")

deprecated("assets:debug", "paver compile_assets --system=lms")
deprecated("assets:watch", "paver compile_assets --system=lms --watch")

[:lms, :cms].each do |system|

    deprecated("assets", "paver compile_assets --system=#{system}")

    deprecated("#{system}:gather_assets", "paver compile_assets --system=#{system} --collectstatic")
    environments(system).each do |env|
      deprecated("#{system}:gather_assets:#{env}", "paver compile_assets --system=#{system} --env=#{env} --collectstatic")
    end
end

