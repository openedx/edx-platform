# devstack tasks deprecated to paver

require 'colorize'

def deprecated(deprecated, deprecated_by,  *args)

    task deprecated, [:system] do |t,args|

        args.with_defaults(:system => nil)

        if not args.system.nil?
            new_cmd = "#{deprecated_by} --system=#{args.system}"
        end

        puts("Task #{deprecated} has been deprecated. Use #{new_cmd} instead. Waiting 5 seconds...".red)
        sleep(5)
        sh(new_cmd)
        exit
    end
end

deprecated("devstack:start", "paver devstack_start")
deprecated("devstack:assets", "paver devstack_assets")
deprecated("devstack:install", "paver devstack_install")
deprecated("devstack", "paver devstack")


