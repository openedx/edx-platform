
def xmodule_cmd(watch=false, debug=false)
    xmodule_cmd = 'xmodule_assets common/static/xmodule'
    if watch
        "watchmedo shell-command " +
                   "--patterns='*.js;*.coffee;*.sass;*.scss;*.css' " +
                   "--recursive " +
                   "--command='#{xmodule_cmd}' " +
                   "common/lib/xmodule"
    else
        xmodule_cmd
    end
end

def coffee_cmd(watch=false, debug=false)
    "node_modules/.bin/coffee #{watch ? '--watch' : ''} --compile */static"
end

def sass_cmd(watch=false, debug=false)
    "sass #{debug ? '--debug-info' : '--style compressed'} " +
          "--load-path ./common/static/sass " +
          "--require ./common/static/sass/bourbon/lib/bourbon.rb " +
          "#{watch ? '--watch' : '--update'} */static"
end

desc "Compile all assets"
multitask :assets => 'assets:all'

namespace :assets do

    desc "Compile all assets in debug mode"
    multitask :debug

    desc "Watch all assets for changes and automatically recompile"
    task :watch => 'assets:_watch' do
        puts "Press ENTER to terminate".red
        $stdin.gets
    end

    {:xmodule => :install_python_prereqs,
     :coffee => :install_node_prereqs,
     :sass => :install_ruby_prereqs}.each_pair do |asset_type, prereq_task|
        desc "Compile all #{asset_type} assets"
        task asset_type => prereq_task do
            cmd = send(asset_type.to_s + "_cmd", watch=false, debug=false)
            sh(cmd)
        end

        multitask :all => asset_type
        multitask :debug => "assets:#{asset_type}:debug"
        multitask :_watch => "assets:#{asset_type}:_watch"

        namespace asset_type do
            desc "Compile all #{asset_type} assets in debug mode"
            task :debug => prereq_task do
                cmd = send(asset_type.to_s + "_cmd", watch=false, debug=true)
                sh(cmd)
            end

            desc "Watch all #{asset_type} assets and compile on change"
            task :watch => "assets:#{asset_type}:_watch" do
                puts "Press ENTER to terminate".red
                $stdin.gets
            end

            task :_watch => prereq_task do
                cmd = send(asset_type.to_s + "_cmd", watch=true, debug=true)
                background_process(cmd)
            end
        end
    end


    multitask :sass => 'assets:xmodule'
    namespace :sass do
        # In watch mode, sass doesn't immediately compile out of date files,
        # so force a recompile first
        task :_watch => 'assets:sass:debug'
        multitask :debug => 'assets:xmodule:debug'
    end

    multitask :coffee => 'assets:xmodule'
    namespace :coffee do
        multitask :debug => 'assets:xmodule:debug'
    end
end

[:lms, :cms].each do |system|
    # Per environment tasks
    environments(system).each do |env|
        desc "Compile coffeescript and sass, and then run collectstatic in the specified environment"
        task "#{system}:gather_assets:#{env}" => :assets do
            sh("#{django_admin(system, env, 'collectstatic', '--noinput')} > /dev/null") do |ok, status|
                if !ok
                    abort "collectstatic failed!"
                end
            end
        end
    end
end
