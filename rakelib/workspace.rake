MIGRATION_MARKER_DIR = File.join(REPO_ROOT, '.ws_migrations_complete')
SKIP_MIGRATIONS = ENV['SKIP_WS_MIGRATIONS'] || false

directory MIGRATION_MARKER_DIR

namespace :ws do
    task :migrate => MIGRATION_MARKER_DIR do
        Dir['ws_migrations/*'].select{|m| File.executable?(m)}.each do |migration|
            completion_file = File.join(MIGRATION_MARKER_DIR, File.basename(migration))
            is_excluded = File.basename(migration).start_with?("README")
            if ! File.exist?(completion_file) && ! is_excluded
                sh(migration)
                File.write(completion_file, "")
            end
        end unless SKIP_MIGRATIONS
    end
end
