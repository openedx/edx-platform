$:.push File.expand_path('../lib', __FILE__)
require 'sassy-maps/version'

Gem::Specification.new do |s|
  s.name        = 'sassy-maps'
  s.version     = SassyMaps::VERSION
  s.platform    = Gem::Platform::RUBY
  s.authors     = ['Sam Richard']
  s.email       = ['sam@snug.ug']
  s.license     = 'MIT'
  s.homepage    = 'https://github.com/Snugug/Sassy-Maps'
  s.summary     = 'Map helper functions for Sass 3.3 Maps'
  s.description = 'Map helper functions for Sass 3.3 Maps including get-deep and set/set-deep'
  s.rubyforge_project = 'sassy-maps'
  s.files = ['README.md']
  s.files += Dir.glob("lib/**/*.*")
  s.files += Dir.glob("sass/**/*.*")
  s.test_files    = `git ls-files -- {test,spec,features}/*`.split("\n")
  s.require_paths = ["lib"]
  s.add_dependency('sass', '~> 3.3')
  s.add_development_dependency('bundler')
  s.add_development_dependency('rake')
  s.add_development_dependency('minitest')
  s.add_development_dependency('minitap')
  s.add_development_dependency('tapout')
  s.add_development_dependency('term-ansicolor')
  s.add_development_dependency('colorize')
end
