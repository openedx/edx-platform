DEVSTACK_PORTS = {
    "lms" => '8000',
    "studio" => '8001'
}

# Abort if system is not one we recognize
def check_devstack_sys(sys_name)
    if not DEVSTACK_PORTS.has_key?(sys_name)
        puts "Devstack system must be either 'lms' or 'studio'"
        exit 1
    end
end

# Convert "studio" to "cms"
def old_system(sys_name)
    if sys_name == "studio"
        return "cms"
    else
        return sys_name
    end
end

namespace :devstack do

    desc "Start the server"
    task :start, [:system] do |t, args|
        check_devstack_sys(args.system)
        port = DEVSTACK_PORTS[args.system]
        sys = old_system(args.system)
        sh("./manage.py #{sys} runserver --settings=devstack 0.0.0.0:#{port}")
    end

    desc "Update static assets"
    task :assets, [:system] do |t, args|
        check_devstack_sys(args.system)
        Rake::Task["assets"].invoke(old_system(args.system), 'devstack')
    end

    desc "Update Python, Ruby, and Node requirements"
    task :install => [:install_prereqs]
end


desc "Start the devstack lms or studio server"
task :devstack, [:system] => ['devstack:install', 'devstack:assets'] do |t, args|
    Rake::Task['devstack:start'].invoke(args.system)
end
