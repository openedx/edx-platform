require 'launchy'

# --- Develop and public documentation ---
desc "Invoke sphinx 'make build' to generate docs."
task :builddocs, [:type, :quiet] do |t, args|
    args.with_defaults(:quiet => "quiet")
    if args.type == 'dev'
        path = "docs/developers"
    elsif args.type == 'author'
        path = "docs/course_authors"
    elsif args.type == 'data'
        path = "docs/data"
    else
        path = "docs"
    end

    Dir.chdir(path) do
        if args.quiet == 'verbose'
            sh('make html quiet=false')
        else
            sh('make html quiet=true')
        end
    end
end

desc "Show docs in browser (mac and ubuntu)."
task :showdocs, [:options] do |t, args|
    if args.options == 'dev'
        path = "docs/developers"
    elsif args.options == 'author'
        path = "docs/course_authors"
    elsif args.options == 'data'
        path = "docs/data"
    else
        path = "docs"
    end

    Launchy.open("#{path}/build/html/index.html")
end

desc "Build docs and show them in browser"
task :doc, [:type, :quiet] =>  :builddocs do |t, args|
    Rake::Task["showdocs"].invoke(args.type, args.quiet)
end
# --- Develop and public documentation ---
