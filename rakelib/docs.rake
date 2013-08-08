require 'launchy'

# --- Develop and public documentation ---
desc "Invoke sphinx 'make build' to generate docs."
task :builddocs, [:options] do |t, args|
    if args.options == 'dev'
        path = "docs/developer"
    elsif args.options == 'author'
        path = "docs/course_authors"
    elsif args.options == 'data'
        path = "docs/data"
    else
        path = "docs"
    end

    Dir.chdir(path) do
        sh('make html')
    end
    path = "docs"

    Dir.chdir(path) do
        sh('make html')
    end
end

desc "Show docs in browser (mac and ubuntu)."
task :showdocs, [:options] do |t, args|
    if args.options == 'dev'
        path = "docs/developer"
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
task :doc, [:options] =>  :builddocs do |t, args|
    Rake::Task["showdocs"].invoke(args.options)
end
# --- Develop and public documentation ---
