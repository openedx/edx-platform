
# Packaging constants
COMMIT = (ENV["GIT_COMMIT"] || `git rev-parse HEAD`).chomp()[0, 10]
PACKAGE_NAME = "edx"
BRANCH = (ENV["GIT_BRANCH"] || `git symbolic-ref -q HEAD`).chomp().gsub('refs/heads/', '').gsub('origin/', '')

desc "Build a properties file used to trigger autodeploy builds"
task :autodeploy_properties do
    File.open("autodeploy.properties", "w") do |file|
        file.puts("UPSTREAM_NOOP=false")
        file.puts("UPSTREAM_BRANCH=#{BRANCH}")
        file.puts("UPSTREAM_JOB=#{PACKAGE_NAME}")
        file.puts("UPSTREAM_REVISION=#{COMMIT}")
    end
end
