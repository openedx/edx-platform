# Theming constants
THEME_NAME = ENV_TOKENS['THEME_NAME']
USE_CUSTOM_THEME = !(THEME_NAME.nil? || THEME_NAME.empty?)
if USE_CUSTOM_THEME
    THEME_ROOT = File.join(ENV_ROOT, "themes", THEME_NAME)
    THEME_SASS = File.join(THEME_ROOT, "static", "sass")
end

def xmodule_cmd(watch=false, debug=false)
    xmodule_cmd = 'xmodule_assets common/static/xmodule'
    if watch
        "watchmedo shell-command " +
                  "--patterns='*.js;*.coffee;*.sass;*.scss;*.css' " +
                  "--recursive " +
                  "--command='#{xmodule_cmd}' " +
                  "--wait " +
                  "common/lib/xmodule"
    else
        xmodule_cmd
    end
end

def coffee_cmd(watch=false, debug=false)
    if watch
        # On OSx, coffee fails with EMFILE when
        # trying to watch all of our coffee files at the same
        # time.
        #
        # Ref: https://github.com/joyent/node/issues/2479
        #
        # So, instead, we use watchmedo, which works around the problem
        "watchmedo shell-command " +
                  "--command 'node_modules/.bin/coffee -c ${watch_src_path}' " +
                  "--recursive " +
                  "--patterns '*.coffee' " +
                  "--ignore-directories " +
                  "--wait " +
                  "."
    else
        'node_modules/.bin/coffee --compile .'
    end
end

def sass_cmd(watch=false, debug=false)
    sass_load_paths = ["./common/static/sass"]
    sass_watch_paths = ["*/static"]
    if USE_CUSTOM_THEME
      sass_load_paths << THEME_SASS
      sass_watch_paths << THEME_SASS
    end

    "sass #{debug ? '--debug-info' : '--style compressed'} " +
          "--load-path #{sass_load_paths.join(' ')} " +
          "--require ./common/static/sass/bourbon/lib/bourbon.rb " +
          "#{watch ? '--watch' : '--update'} #{sass_watch_paths.join(' ')}"
end

desc "Compile all assets"
multitask :assets => 'assets:all'

namespace :assets do

    desc "Compile all assets in debug mode"
    multitask :debug

    desc "Preprocess all templatized static asset files"
    task :preprocess, [:system, :env] do |t, args|
      args.with_defaults(:system => "lms", :env => "dev")
      sh(django_admin(args.system, args.env, "preprocess_assets")) do |ok, status|
        abort "asset preprocessing failed!" if !ok
      end
    end

    desc "Watch all assets for changes and automatically recompile"
    task :watch => 'assets:_watch' do
        puts "Press ENTER to terminate".red
        $stdin.gets
    end

    {:xmodule => [:install_python_prereqs],
     :coffee => [:install_node_prereqs],
     :sass => [:install_ruby_prereqs, :preprocess]}.each_pair do |asset_type, prereq_tasks|
        desc "Compile all #{asset_type} assets"
        task asset_type => prereq_tasks do
            cmd = send(asset_type.to_s + "_cmd", watch=false, debug=false)
            if cmd.kind_of?(Array)
                cmd.each {|c| sh(c)}
            else
                sh(cmd)
            end
        end

        multitask :all => asset_type
        multitask :debug => "assets:#{asset_type}:debug"
        multitask :_watch => "assets:#{asset_type}:_watch"

        namespace asset_type do
            desc "Compile all #{asset_type} assets in debug mode"
            task :debug => prereq_tasks do
                cmd = send(asset_type.to_s + "_cmd", watch=false, debug=true)
                sh(cmd)
            end

            desc "Watch all #{asset_type} assets and compile on change"
            task :watch => "assets:#{asset_type}:_watch" do
                puts "Press ENTER to terminate".red
                $stdin.gets
            end

            # Fully compile before watching for changes
            task :_watch => (prereq_tasks + ["assets:#{asset_type}:debug"]) do
                cmd = send(asset_type.to_s + "_cmd", watch=true, debug=true)
                if cmd.kind_of?(Array)
                    cmd.each {|c| background_process(c)}
                else
                    background_process(cmd)
                end
            end
        end
    end

    multitask :sass => 'assets:xmodule'
    namespace :sass do
        multitask :debug => 'assets:xmodule:debug'
    end

    multitask :coffee => 'assets:xmodule'
    namespace :coffee do
        multitask :debug => 'assets:xmodule:debug'
    end

    namespace :xmodule do
        # Only start the xmodule watcher after the coffee and sass watchers have already started
        task :_watch => ['assets:coffee:_watch', 'assets:sass:_watch']
    end
end

# This task does the real heavy lifting to gather all of the static
# assets. We want people to call it via the wrapper below, so we
# don't provide a description so that it won't show up in rake -T.
task :gather_assets, [:system, :env] => :assets do |t, args|
    sh("#{django_admin(args.system, args.env, 'collectstatic', '--noinput')} > /dev/null") do |ok, status|
        if !ok
            abort "collectstatic failed!"
        end
    end
end

[:lms, :cms].each do |system|
    # Per environment tasks
    environments(system).each do |env|
        # This task wraps the one above, since we need the system and
        # env arguments to be passed to all dependent tasks.
        desc "Compile coffeescript and sass, and then run collectstatic in the specified environment"
        task "#{system}:gather_assets:#{env}" do
          Rake::Task[:gather_assets].invoke(system, env)
        end
    end
end
