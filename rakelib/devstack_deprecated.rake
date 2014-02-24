# devstack tasks deprecated to paver

require 'colorize'

def deprecated(deprecated, deprecated_by,  *args)

    task deprecated, [:system] do |t,args|

        # Need to install paver dependencies for the commands to work!
        sh("pip install Paver==1.2.1 psutil==1.2.1 lazy==1.1 path.py==3.0.1")

        args.with_defaults(:system => 'lms')
        deprecated_by = "#{deprecated_by} #{args.system}"

        puts("Task #{deprecated} has been deprecated. Use #{deprecated_by} instead. Waiting 5 seconds...".red)
        sleep(5)
        sh(deprecated_by)
        exit
    end
end

deprecated("devstack:start", "paver devstack --fast")
deprecated("devstack:assets", "paver update_assets --settings=devstack")
deprecated("devstack:install", "paver install_prereqs")
deprecated("devstack", "paver devstack")
