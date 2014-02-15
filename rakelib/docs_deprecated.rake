# doc tasks deprecated to paver

require 'colorize'

def deprecated(deprecated, deprecated_by)

     task deprecated, [:type, :quiet] do |t,args|

        # Need to install paver dependencies for the commands to work!
        sh("pip install Paver==1.2.1 psutil==1.2.1 lazy==1.1 path.py==3.0.1")

        args.with_defaults(:quiet => "quiet")
        new_cmd = [deprecated_by]

        if args.quiet == 'verbose' and deprecated == 'builddocs'
            new_cmd << '--verbose'
        end

        if not args.type.nil?
            new_cmd << "--type=#{args.type}"
        end

        new_cmd = new_cmd.join(" ")

        puts("Task #{deprecated} has been deprecated. Use \"#{new_cmd}\" instead. Waiting 5 seconds...".red)
        sleep(5)
        sh(new_cmd)
    end

end


deprecated('builddocs','paver build_docs')
deprecated('showdocs','paver build_docs')
deprecated('doc','paver build_docs')
