# assets tasks deprecated to paver

require 'colorize'

def deprecated(deprecated, deprecated_by,  *args)

    task deprecated, [:system, :env] do |t,args|

        args.with_defaults(:system => "lms", :env => "dev")

        if deprecated.include? "gather_assets"
            new_cmd = deprecated_by
        else
            new_cmd = deprecated_by + " --system=#{args.system} --env=#{args.env}"
        end

        puts("Task #{deprecated} has been deprecated. Use #{new_cmd} instead. Waiting 5 seconds...".red)
        sleep(5)
        sh(new_cmd)
        exit
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

deprecated("assets:debug", "paver compile_assets ")
deprecated("assets:watch", "paver compile_assets --watch")

deprecated("assets", "paver compile_assets ")

[:lms, :cms].each do |system|

    deprecated("#{system}:gather_assets", "paver compile_assets --system=#{system} --collectstatic")
    environments(system).each do |env|
      deprecated("#{system}:gather_assets:#{env}", "paver compile_assets --system=#{system} --env=#{env} --collectstatic")
    end
end

