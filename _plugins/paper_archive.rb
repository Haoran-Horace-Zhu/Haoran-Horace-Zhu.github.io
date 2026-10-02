# An explicit, fail-closed archive. Bibliography entries alone never publish files.
require 'bibtex'
require 'date'
require 'digest'
require 'fileutils'
require 'json'
require 'pathname'
require 'time'
require 'uri'

module PaperArchive
  MAX_PDF_BYTES = 5_000_000

  class Error < StandardError; end

  def self.normalized(value)
    value.to_s.gsub(/\s+/, ' ').strip
  end

  def self.authors(entry)
    return [] unless entry[:author]

    entry.author.to_a.map do |name|
      [name.first, name.prefix, name.last, name.suffix].map { |part| normalized(part) }
        .reject(&:empty?).join(' ')
    end
  end

  def self.parse_bibliography(text)
    # The website bibliography has Jekyll front matter, not BibTeX content.
    text = text.sub(/\A---\s*\r?\n.*?^---\s*\r?\n/m, '')
    # bibtex-ruby silently renames duplicate keys on registration. Check its
    # lexer tokens first, so a typo cannot attach a PDF to the wrong entry.
    keys = BibTeX::Lexer.new.analyse(text).stack.select { |token| token.first == :KEY }.map(&:last)
    duplicate = keys.group_by { |key| key }.find { |_, matches| matches.length > 1 }
    raise Error, "Duplicate bibliography key: #{duplicate.first}" if duplicate
    bibliography = BibTeX.parse(text)
    raise Error, 'Bibliography contains parse errors' unless bibliography.errors.empty?
    bibliography.entries.values
  rescue StandardError => e
    raise Error, "Cannot parse archive bibliography: #{e.message}"
  end

  def self.output_path(route)
    path = route.to_s
    path = "/#{path}" unless path.start_with?('/')
    path += 'index.html' if path.end_with?('/')
    path
  end

  # Produces plain Ruby hashes so validation can be tested without booting Jekyll.
  class Manifest
    attr_reader :papers, :files, :outputs

    def initialize(source:, manifest:, bibliography:, url:, baseurl: '', reserved_routes: [])
      @source = File.realpath(source)
      @manifest = manifest
      @bibliography = bibliography
      @url = validate_origin(url)
      @baseurl = validate_baseurl(baseurl)
      @reserved_routes = reserved_routes.map { |route| PaperArchive.output_path(route) }
      @papers = []
      @files = []
      @outputs = []
      validate!
    end

    def absolute(path)
      "#{@url}#{@baseurl}#{path}"
    end

    private

    def fail!(message)
      raise Error, message
    end

    def validate_origin(value)
      origin = value.to_s.sub(%r{/+\z}, '')
      uri = URI.parse(origin)
      unless %w[http https].include?(uri.scheme) && uri.host && !uri.userinfo &&
             !uri.query && !uri.fragment && (uri.path.nil? || uri.path.empty?)
        fail!('Archive site.url must be an absolute HTTP(S) origin')
      end
      origin
    rescue URI::InvalidURIError
      fail!('Archive site.url is invalid')
    end

    def validate_baseurl(value)
      base = value.to_s.sub(%r{/+\z}, '')
      return '' if base.empty?
      unless base.match?(%r{\A/(?:[A-Za-z0-9_-]+/)*[A-Za-z0-9_-]+\z})
        fail!('Archive site.baseurl must be a safe absolute path')
      end
      base
    end

    def string!(hash, key, context)
      value = hash[key]
      unless value.is_a?(String) && !PaperArchive.normalized(value).empty?
        fail!("#{context}: #{key} must be a nonempty string")
      end
      value
    end

    def keys!(hash, allowed, context)
      unknown = hash.keys - allowed
      fail!("#{context}: unknown fields #{unknown.join(', ')}") unless unknown.empty?
    end

    def validate!
      unless @manifest.is_a?(Hash) && @manifest['schema_version'] == 1 && @manifest['papers'].is_a?(Array)
        fail!('Archive manifest must have schema_version: 1 and a papers array')
      end
      keys!(@manifest, %w[schema_version papers], 'Archive manifest')
      entries = @bibliography.is_a?(String) ? PaperArchive.parse_bibliography(@bibliography) : @bibliography
      bib = {}
      entries.each do |entry|
        key = entry.key.to_s
        fail!("Duplicate bibliography key: #{key}") if bib.key?(key)
        bib[key] = entry
      end
      seen_keys = {}
      seen_slugs = {}
      @manifest['papers'].each do |paper|
        fail!('Every archive paper must be a mapping') unless paper.is_a?(Hash)
        keys!(paper, %w[bib_key slug current_version versions], 'Archive paper')
        key = string!(paper, 'bib_key', 'Archive paper')
        slug = string!(paper, 'slug', key)
        fail!("#{key}: unsafe slug") unless slug.match?(/\A[a-z0-9]+(?:-[a-z0-9]+)*\z/)
        fail!("Duplicate archive bib_key: #{key}") if seen_keys[key]
        fail!("Duplicate archive slug: #{slug}") if seen_slugs[slug]
        fail!("Missing bibliography key: #{key}") unless bib[key]
        seen_keys[key] = seen_slugs[slug] = true
        validate_paper(paper, bib[key], key, slug)
      end
      reserve!('/papers/') unless @papers.empty?
    end

    def validate_paper(paper, entry, key, slug)
      versions = paper['versions']
      unless versions.is_a?(Array) && !versions.empty?
        fail!("#{key}: versions must be a nonempty array")
      end
      current_id = string!(paper, 'current_version', key)
      version_ids = {}
      snapshots = {}
      summaries = versions.each_with_index.map do |version, index|
        fail!("#{key}: every version must be a mapping") unless version.is_a?(Hash)
        keys!(version, %w[id source sha256 archived_at archived_on archive_timezone note snapshot], key)
        id = string!(version, 'id', key)
        fail!("#{key}: unsafe version id") unless id.match?(/\Av[1-9][0-9]*\z/)
        fail!("#{key}: duplicate version id #{id}") if version_ids[id]
        fail!("#{key}: versions must be ordered consecutively from v1") unless id == "v#{index + 1}"
        version_ids[id] = true
        context = "#{key}/#{id}"
        snapshots[id] = validate_snapshot(version['snapshot'], key, context,
                                          absolute("/papers/#{slug}/#{id}.html"))
        validate_dates(version, context)
        source, checksum = validate_pdf(version, context)
        stem = "/papers/#{slug}/#{id}"
        %w[.html .pdf .bib].each { |extension| reserve!(stem + extension) }
        @files << { 'source' => source, 'url' => stem + '.pdf', 'sha256' => checksum }
        {
          'id' => id, 'html_url' => absolute(stem + '.html'),
          'pdf_url' => absolute(stem + '.pdf'), 'bib_url' => absolute(stem + '.bib'),
          'sha256' => checksum, 'archived_at' => version['archived_at'],
          'archived_on' => version['archived_on'], 'archive_timezone' => version['archive_timezone'],
          'note' => string!(version, 'note', context)
        }
      end
      fail!("#{key}: current_version is not listed in versions") unless snapshots[current_id]
      fail!("#{key}: current_version must be the last version") unless current_id == summaries.last['id']
      summaries.each_cons(2) do |earlier, later|
        unless Time.iso8601(earlier['archived_at']) <= Time.iso8601(later['archived_at'])
          fail!("#{key}: version archive timestamps must be nondecreasing")
        end
      end
      compare_entry!(snapshots[current_id], entry, key, true)
      landing_path = "/papers/#{slug}/"
      reserve!(landing_path)
      reserve!(landing_path + 'record.json')
      version_pages = summaries.each_with_index.map do |summary, index|
        # Later appends must not rewrite the metadata/history of an old version.
        archive_hash(snapshots[summary['id']], summary, summaries.take(index + 1), key, slug,
                     summary['id'], "/papers/#{slug}/#{summary['id']}.html", true)
      end
      current = summaries.find { |summary| summary['id'] == current_id }
      landing = archive_hash(snapshots[current_id], current, summaries, key, slug,
                             current_id, landing_path, false)
      @papers << { 'landing' => landing, 'versions' => version_pages }
    end

    def validate_snapshot(snapshot, key, context, canonical_url)
      fail!("#{context}: snapshot must be a mapping") unless snapshot.is_a?(Hash)
      keys!(snapshot, %w[title authors abstract year journal doi arxiv bibtex], context)
      %w[title abstract year bibtex].each { |field| string!(snapshot, field, context) }
      unless snapshot['authors'].is_a?(Array) && !snapshot['authors'].empty? &&
             snapshot['authors'].all? { |author| author.is_a?(String) && !PaperArchive.normalized(author).empty? }
        fail!("#{context}: authors must be a nonempty array of names")
      end
      fail!("#{context}: year must have four digits") unless snapshot['year'].match?(/\A[0-9]{4}\z/)
      %w[journal doi arxiv].each do |field|
        string!(snapshot, field, context) if snapshot.key?(field)
      end
      citation_entries = PaperArchive.parse_bibliography(snapshot['bibtex'])
      unless citation_entries.length == 1 && citation_entries.first.key.to_s == key
        fail!("#{context}: bibtex must contain exactly one entry with the matching key")
      end
      unless PaperArchive.normalized(citation_entries.first[:url]) == canonical_url
        fail!("#{context}: bibtex url must equal this version's canonical URL")
      end
      compare_entry!(snapshot, citation_entries.first, context, false)
      # Only approved public metadata enters generated output; unknown fields do not leak.
      snapshot.select { |field, _| %w[title authors abstract year journal doi arxiv bibtex].include?(field) }
    end

    def compare_entry!(snapshot, entry, context, require_abstract)
      fields = %w[title year]
      fields << 'abstract' if require_abstract || entry[:abstract]
      %w[journal doi arxiv].each { |field| fields << field if snapshot.key?(field) }
      fields.each do |field|
        unless PaperArchive.normalized(snapshot[field]) == PaperArchive.normalized(entry[field.to_sym])
          fail!("#{context}: snapshot #{field} does not match bibliography metadata")
        end
      end
      unless snapshot['authors'].map { |author| PaperArchive.normalized(author) } == PaperArchive.authors(entry)
        fail!("#{context}: snapshot authors do not match bibliography metadata")
      end
    end

    def validate_dates(version, context)
      at = string!(version, 'archived_at', context)
      on = string!(version, 'archived_on', context)
      zone = string!(version, 'archive_timezone', context)
      unless at.match?(/\A\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z\z/) && Time.iso8601(at).utc.iso8601 == at
        fail!("#{context}: archived_at must be an ISO 8601 UTC timestamp")
      end
      unless on.match?(/\A\d{4}-\d{2}-\d{2}\z/) && Date.iso8601(on).iso8601 == on
        fail!("#{context}: archived_on must be an ISO date")
      end
      unless zone == 'UTC' || zone.match?(%r{\A[A-Za-z_+-]+(?:/[A-Za-z0-9_+-]+)+\z})
        fail!("#{context}: archive_timezone must be an IANA timezone name")
      end
    rescue ArgumentError
      fail!("#{context}: invalid archive date")
    end

    def validate_pdf(version, context)
      source = string!(version, 'source', context)
      components = source.split('/')
      unless source.start_with?('_paper_files/') && source.end_with?('.pdf') &&
             components.all? { |part| part.match?(/\A[A-Za-z0-9][A-Za-z0-9._-]*\z/) || part == '_paper_files' } &&
             !components.any? { |part| part == '.' || part == '..' } && !source.include?('//')
        fail!("#{context}: PDF source must be a safe path below _paper_files")
      end
      root = File.join(@source, '_paper_files')
      unless File.directory?(root) && File.realpath(root) == root
        fail!("#{context}: _paper_files must be a real directory inside the site")
      end
      path = File.join(@source, source)
      unless File.file?(path) && File.realpath(path).start_with?(root + File::SEPARATOR)
        fail!("#{context}: PDF source is missing or escapes _paper_files")
      end
      checksum = string!(version, 'sha256', context)
      fail!("#{context}: sha256 must contain 64 lowercase hexadecimal characters") unless checksum.match?(/\A[a-f0-9]{64}\z/)
      unless File.size(path) <= MAX_PDF_BYTES && File.binread(path, 5) == '%PDF-'
        fail!("#{context}: PDF must start with %PDF- and be at most 5 MB")
      end
      fail!("#{context}: PDF checksum does not match") unless Digest::SHA256.file(path).hexdigest == checksum
      [source, checksum]
    rescue Errno::ENOENT, Errno::ELOOP
      fail!("#{context}: PDF source is missing or has an invalid symlink")
    end

    def reserve!(route)
      output = PaperArchive.output_path(route)
      conflict = (@reserved_routes + @outputs).find do |other|
        output == other || output.start_with?(other + '/') || other.start_with?(output + '/')
      end
      fail!("Archive output collision: #{route} conflicts with #{conflict}") if conflict
      @outputs << output
    end

    def archive_hash(snapshot, summary, summaries, key, slug, current, path, is_version)
      snapshot.merge(
        'bib_key' => key, 'slug' => slug, 'url' => path, 'canonical_url' => absolute(path),
        'pdf_url' => summary['pdf_url'], 'bib_url' => summary['bib_url'],
        'record_url' => absolute("/papers/#{slug}/record.json"),
        'versions' => summaries, 'current_version' => current, 'version_id' => summary['id'],
        'is_version' => is_version, 'sha256' => summary['sha256'],
        'archived_at' => summary['archived_at'], 'archived_on' => summary['archived_on'],
        'archive_timezone' => summary['archive_timezone'], 'note' => summary['note']
      )
    end
  end
end

if defined?(Jekyll::Generator)
  module PaperArchive
    # A .bib Page is processed by Jekyll Scholar's BibTeX-to-HTML converter,
    # even when render_with_liquid is false. Static artifacts bypass the whole
    # rendering/conversion pipeline and preserve the approved citation bytes.
    class LiteralBibtex < Jekyll::StaticFile
      attr_reader :content

      def initialize(site, url, content, archived_at)
        @archive_url = url
        @content = content.dup.freeze
        @modified_time = Time.iso8601(archived_at)
        super(site, site.source, File.dirname(url), File.basename(url))
        @relative_path = url
      end

      def url
        @archive_url
      end

      def destination(dest)
        File.join(dest, @archive_url.sub(%r{\A/}, ''))
      end

      def data
        { 'sitemap' => false }
      end

      def modified_time
        @modified_time
      end

      def write?
        true
      end

      def write(dest)
        target = destination(dest)
        FileUtils.mkdir_p(File.dirname(target))
        FileUtils.rm(target) if File.exist?(target) || File.symlink?(target)
        File.binwrite(target, @content)
        true
      end
    end

    class ArchivedPDF < Jekyll::StaticFile
      def initialize(site, file)
        @archive_source = file['source']
        @archive_url = file['url']
        @archive_checksum = file['sha256']
        super(site, site.source, File.dirname(@archive_source), File.basename(@archive_source))
        @relative_path = @archive_url
      end

      def destination(dest)
        File.join(dest, @archive_url.sub(%r{\A/}, ''))
      end

      def write(dest)
        root = File.join(File.realpath(@site.source), '_paper_files')
        unless File.realpath(root) == root && File.realpath(path).start_with?(root + File::SEPARATOR) &&
               Digest::SHA256.file(path).hexdigest == @archive_checksum
          raise Error, 'Approved archive PDF changed after validation'
        end
        super
      end
    end

    class Generator < Jekyll::Generator
      safe true
      priority :low

      def generate(site)
        manifest = site.data['paper_archive']
        return unless manifest

        bibliography = File.read(File.join(site.source, '_bibliography', 'papers.bib'))
        reserved = (site.pages + site.static_files + site.collections.values.flat_map(&:docs)).map do |item|
          destination = item.destination(site.dest)
          '/' + Pathname.new(destination).relative_path_from(Pathname.new(site.dest)).to_s
        end
        archive = Manifest.new(source: site.source, manifest: manifest, bibliography: bibliography,
                               url: site.config['url'], baseurl: site.config['baseurl'], reserved_routes: reserved)
        summaries = archive.papers.map { |paper| paper['landing'] }
        site.data['generated_paper_archive'] = summaries
        return if summaries.empty?

        add_page(site, '/papers/', '', 'layout' => 'paper_archive_index',
                 'title' => 'Paper archive', 'archived_papers' => summaries, 'sitemap' => true)
        archive.papers.each do |paper|
          ([paper['landing']] + paper['versions']).each do |record|
            add_page(site, record['url'], '', 'layout' => 'paper_archive', 'title' => record['title'],
                     'description' => record['abstract'], 'archive' => record, 'sitemap' => true)
          end
          paper['versions'].each do |record|
            site.static_files << LiteralBibtex.new(
              site, "/papers/#{record['slug']}/#{record['version_id']}.bib", record['bibtex'], record['archived_at']
            )
          end
          record = { 'schema_version' => 1, 'paper' => paper['landing'], 'versions' => paper['versions'] }
          add_page(site, "/papers/#{paper['landing']['slug']}/record.json", JSON.pretty_generate(record) + "\n",
                   'layout' => nil, 'sitemap' => false, 'render_with_liquid' => false)
        end
        archive.files.each { |file| site.static_files << ArchivedPDF.new(site, file) }
      rescue PaperArchive::Error => e
        raise Jekyll::Errors::FatalException, "Paper archive: #{e.message}"
      end

      private

      def add_page(site, url, content, data)
        output = PaperArchive.output_path(url).sub(%r{\A/}, '')
        page = Jekyll::PageWithoutAFile.new(site, site.source, File.dirname(output), File.basename(output))
        page.content = content
        page.data = data.merge('nav' => false, 'permalink' => url)
        site.pages << page
      end
    end
  end
end
