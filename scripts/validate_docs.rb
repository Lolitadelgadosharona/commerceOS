# frozen_string_literal: true

files = Dir["docs/**/*.md"] + ["README.md"]
abort "no Markdown files found" if files.empty?

files.each do |file|
  content = File.read(file)
  abort "missing H1: #{file}" unless content.start_with?("# ")
  abort "tab character: #{file}" if content.include?("\t")
  abort "trailing whitespace: #{file}" if content.lines.any? { |line| line.match?(/[ \t]+\n$/) }
  abort "unbalanced code fence: #{file}" if content.scan(/^```/).length.odd?

  content.scan(/\[[^\]]*\]\(([^)#]+)(?:#[^)]*)?\)/).flatten.each do |link|
    next if link.match?(%r{^(https?|mailto):})

    target = File.expand_path(link, File.dirname(file))
    abort "broken link: #{file} -> #{link}" unless File.exist?(target)
  end
end

puts "Markdown structure and relative links: ok (#{files.length} files)"
