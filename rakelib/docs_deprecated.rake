# doc tasks deprecated to paver

require 'colorize'

def deprecated(deprecated, deprecated_by)

     task deprecated, [:type, :quiet] do |t,args|

        args.with_defaults(:quiet => "quiet", :type => "dev")

        if deprecated == "showdocs"
           new_cmd = deprecated_by + " --type=#{args.type}"
        else
           new_cmd = deprecated_by + " --type=#{args.type}  #{args.quiet == 'quiet' ? '' : '--verbose'}"
        end

        puts("Task #{deprecated} has been deprecated. Use \"#{new_cmd}\" instead. Waiting 5 seconds...".red)
        sleep(5)
        sh(new_cmd)
    end

end


deprecated('builddocs','paver build_docs')
deprecated('showdocs','paver show_docs')
deprecated('doc','paver doc')


