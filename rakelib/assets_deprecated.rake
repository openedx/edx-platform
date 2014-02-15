# assets tasks deprecated to paver

require 'colorize'

def deprecated(deprecated, deprecated_by,  *args)

    task deprecated, [:system, :env] do |t,args|

        # Need to install paver dependencies for the commands to work!
        sh("pip install Paver==1.2.1 psutil==1.2.1 lazy==1.1 path.py==3.0.1")

        args.with_defaults(:system => "lms", :env => "dev")

        if deprecated_by.nil?
            puts("Task #{deprecated} has been deprecated.".red)

        else
            if deprecated.include? "gather_assets"
                new_cmd = deprecated_by
            else
                new_cmd = deprecated_by + " #{args.system} --settings=#{args.env}"
            end

            puts("Task #{deprecated} has been deprecated. Use #{new_cmd} instead.".red)
            sh(new_cmd)
        end
    end
end

deprecated("assets:coffee", "paver update_assets")
deprecated("assets:coffee:clobber", nil)
deprecated("assets:coffee:debug", "paver update_assets --debug")
deprecated("assets:coffee:watch", "paver update_assets")

deprecated("assets:sass", "paver update_assets")
deprecated("assets:sass:debug", "paver update_assets --debug")
deprecated("assets:sass:watch", "paver update_assets")

deprecated("assets:xmodule", "paver update_assets")
deprecated("assets:xmodule:debug", "paver update_assets --debug")
deprecated("assets:xmodule:watch", "paver update_assets")

deprecated("assets:debug", "paver update_assets --debug")
deprecated("assets:watch", "paver update_assets")

deprecated("assets", "paver update_assets")

[:lms, :cms].each do |system|

    deprecated("#{system}:gather_assets", "paver update_assets #{system}")
    environments(system).each do |env|
      deprecated("#{system}:gather_assets:#{env}", "paver update_assets #{system} --settings=#{env}")
    end
end

