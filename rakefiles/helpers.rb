require 'digest/md5'


def select_executable(*cmds)
    cmds.find_all{ |cmd| system("which #{cmd} > /dev/null 2>&1") }[0] || fail("No executables found from #{cmds.join(', ')}")
end

def django_admin(system, env, command, *args)
    django_admin = ENV['DJANGO_ADMIN_PATH'] || select_executable('django-admin.py', 'django-admin')
    return "#{django_admin} #{command} --traceback --settings=#{system}.envs.#{env} --pythonpath=. #{args.join(' ')}"
end

def report_dir_path(dir)
    return File.join(REPORT_DIR, dir.to_s)
end

def compute_fingerprint(files, dirs)
    digest = Digest::MD5.new()

    # Digest the contents of all the files.
    Dir[*files].select{|file| File.file?(file)}.each do |file|
        digest.file(file)
    end

    # Digest the names of the files in all the dirs.
    dirs.each do |dir|
        file_names = Dir.entries(dir).sort.join(" ")
        digest.update(file_names)
    end

    digest.hexdigest
end

# Hash the contents of all the files, and the names of files in the dirs.
# Run the block if they've changed.
def when_changed(unchanged_message, files, dirs=[])
    Rake::Task[PREREQS_MD5_DIR].invoke
    cache_file = File.join(PREREQS_MD5_DIR, files[0].gsub(/\W+/, '-').sub(/-+$/, '')) + '.md5'
    if !File.exists?(cache_file) or compute_fingerprint(files, dirs) != File.read(cache_file)
        yield
        File.write(cache_file, compute_fingerprint(files, dirs))
    elsif !unchanged_message.empty?
        puts unchanged_message
    end
end

# Runs Process.spawn, and kills the process at the end of the rake process
# Expects the same arguments as Process.spawn
def background_process(*command)
    pid = Process.spawn({}, *command, {:pgroup => true})

    at_exit do
        puts "Ending process and children"
        pgid = Process.getpgid(pid)
        begin
            Timeout.timeout(5) do
                puts "Interrupting process group #{pgid}"
                Process.kill(:SIGINT, -pgid)
                puts "Waiting on process group #{pgid}"
                Process.wait(-pgid)
                puts "Done waiting on process group #{pgid}"
            end
        rescue Timeout::Error
            begin
                Timeout.timeout(5) do
                    puts "Terminating process group #{pgid}"
                    Process.kill(:SIGTERM, -pgid)
                    puts "Waiting on process group #{pgid}"
                    Process.wait(-pgid)
                    puts "Done waiting on process group #{pgid}"
                end
            rescue Timeout::Error
                puts "Killing process group #{pgid}"
                Process.kill(:SIGKILL, -pgid)
                puts "Waiting on process group #{pgid}"
                Process.wait(-pgid)
                puts "Done waiting on process group #{pgid}"
            end
        end
    end
end

def environments(system)
    Dir["#{system}/envs/**/*.py"].select{|file| ! (/__init__.py$/ =~ file)}.map do |env_file|
        env_file.gsub("#{system}/envs/", '').gsub(/\.py/, '').gsub('/', '.')
    end
end
