require 'launchy'

# --- Develop and public documentation ---
desc "Invoke sphinx 'make build' to generate docs."
task :builddocs, [:options] do |t, args|
    path = "docs"

    Dir.chdir(path) do
        sh('make html')
    end
end

desc "Show docs in browser (mac and ubuntu)."
task :showdocs, [:options] do |t, args|
    path = "docs"

    Launchy.open("#{path}/build/html/index.html")
end

desc "Build docs and show them in browser"
task :doc, [:options] =>  :builddocs do |t, args|
    Rake::Task["showdocs"].invoke(args.options)
end
# --- Develop and public documentation ---
