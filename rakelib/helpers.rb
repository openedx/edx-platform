require 'digest/md5'
require 'sys/proctable'
require 'colorize'
require 'timeout'
require 'net/http'

def django_admin(system, env, command, *args)
    return "./manage.py #{system} --settings #{env} #{command} --traceback #{args.join(' ')}"
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
def background_process(command, logfile=nil)
    spawn_opts = {:pgroup => true}
    if !logfile.nil?
        puts "Running '#{command.join(' ')}', redirecting output to #{logfile}"
        spawn_opts[[:err, :out]] = [logfile, 'a']
    end
    pid = Process.spawn({}, *command, spawn_opts)
    command = [*command]

    at_exit do
        pgid = Process.getpgid(pid)
        begin
            Timeout.timeout(5) do
                Process.kill(:SIGINT, -pgid)
                Process.wait(-pgid)
            end
        rescue Timeout::Error
            begin
                Timeout.timeout(5) do
                    Process.kill(:SIGTERM, -pgid)
                    Process.wait(-pgid)
                end
            rescue Timeout::Error
                Process.kill(:SIGKILL, -pgid)
                Process.wait(-pgid)
            end
        end
    end
end

# Runs a command as a background process, as long as no other processes
# tagged with the same tag are running
def singleton_process(command, logfile=nil)
    command = [*command]
    if Sys::ProcTable.ps.select {|proc| proc.cmdline.include?(command.join(' '))}.empty?
        background_process(command, logfile)
    else
        puts "Process '#{command.join(' ')} already running, skipping".blue
    end
end

# Wait for a server to respond with status 200 at "/"
def wait_for_server(server, port)
    attempts = 0
    begin
        http = Net::HTTP.start(server, port, {open_timeout: 10, read_timeout: 10})
        response = http.head("/")
        response.code == "200"
        true
    rescue
        sleep(1)
        attempts += 1
        if attempts < 20
            retry
        else
            false
        end
    end
end

def environments(system)
    Dir["#{system}/envs/**/*.py"].select{|file| ! (/__init__.py$/ =~ file)}.map do |env_file|
        env_file.gsub("#{system}/envs/", '').gsub(/\.py/, '').gsub('/', '.')
    end
end


$failed_tests = []

# Run sh on args. If TESTS_FAIL_FAST is set, then stop on the first shell failure.
# Otherwise, a final task will be added that will fail if any tests have failed
def test_sh(name, *args)
    puts("\n=======================================".green)
    puts("Running #{name} tests".green)
    puts("=======================================".green)

    sh(*args) do |ok, res|
        if ok
            return
        end

        if ENV['TESTS_FAIL_FAST']
            fail("Test failed!")
        else
            $failed_tests << name
        end
    end

    puts("\n=======================================\n".green)
end

# Add a task after all other tasks that fails if any tests have failed
if !ENV['TESTS_FAIL_FAST']
    task :fail_tests do
        if $failed_tests.length > 0
            puts("=======================================".red)
            puts("Tests failed in these test suites:".red)
            $failed_tests.each do |test|
                puts("* #{test}".red)
            end
            exit 1
        end
    end

    Rake.application.top_level_tasks << :fail_tests
end
