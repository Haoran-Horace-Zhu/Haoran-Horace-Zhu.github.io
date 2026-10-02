require 'minitest/autorun'
require 'tmpdir'
require 'fileutils'

# Small adapter doubles keep these unit tests usable with system Ruby 2.6.
# A production Jekyll build and output verification remain separate checks.
module Jekyll
  module Errors
    class FatalException < StandardError; end
  end

  class Generator
    def self.safe(_value); end
    def self.priority(_value); end
  end

  class PageWithoutAFile
    attr_accessor :content, :data

    def initialize(_site, _source, _directory, _name)
      @data = {}
    end

    def url
      data['permalink']
    end

    def destination(dest)
      File.join(dest, PaperArchive.output_path(url).sub(%r{\A/}, ''))
    end
  end

  class StaticFile
    attr_reader :relative_path

    def initialize(site, base, directory, name)
      @site = site
      @base = base
      @dir = directory
      @name = name
    end

    def path
      File.join(@base, @dir, @name)
    end

    def write(dest)
      target = destination(dest)
      FileUtils.mkdir_p(File.dirname(target))
      FileUtils.cp(path, target)
      true
    end
  end
end

require_relative '../_plugins/paper_archive'

class PaperArchiveTest < Minitest::Test
  def setup
    @source = Dir.mktmpdir('paper-archive-test-')
    @pdf = File.join(@source, '_paper_files', 'example-paper', 'v1.pdf')
    FileUtils.mkdir_p(File.dirname(@pdf))
    File.binwrite(@pdf, "%PDF-1.4\nApproved fixture, not an actual manuscript.\n%%EOF\n")
    @bib = <<~BIB
      ---
      ---
      @article{Example2026,
        author = {Zhu, Haoran and van Example, Ada},
        title = {An example paper},
        abstract = {An explicitly approved public abstract.},
        year = {2026},
        journal = {Example Journal},
        doi = {10.0000/example}
      }
      @article{NotApproved,
        author = {Other, Author},
        title = {A bibliography entry is not publication authorization},
        year = {2025}
      }
    BIB
    @snapshot = {
      'title' => 'An example paper', 'authors' => ['Haoran Zhu', 'Ada van Example'],
      'abstract' => 'An explicitly approved public abstract.', 'year' => '2026',
      'journal' => 'Example Journal', 'doi' => '10.0000/example',
      'bibtex' => <<~BIB
        @article{Example2026,
          author = {Zhu, Haoran and van Example, Ada},
          title = {An example paper},
          year = {2026},
          journal = {Example Journal},
          url = {https://example.test/papers/example-paper/v1.html},
          doi = {10.0000/example}
        }
      BIB
    }
    @version = {
      'id' => 'v1', 'source' => '_paper_files/example-paper/v1.pdf',
      'sha256' => Digest::SHA256.file(@pdf).hexdigest,
      'archived_at' => '2026-10-02T01:28:09Z', 'archived_on' => '2026-10-01',
      'archive_timezone' => 'America/Los_Angeles',
      'note' => 'Archive date, not a first-publication claim.', 'snapshot' => @snapshot
    }
    @paper = {
      'bib_key' => 'Example2026', 'slug' => 'example-paper',
      'current_version' => 'v1', 'versions' => [@version]
    }
    @manifest = { 'schema_version' => 1, 'papers' => [@paper] }
  end

  def teardown
    FileUtils.remove_entry(@source) if @source && File.exist?(@source)
  end

  def model(**options)
    PaperArchive::Manifest.new(**{
      source: @source, manifest: @manifest, bibliography: @bib,
      url: 'https://example.test', baseurl: ''
    }.merge(options))
  end

  def invalid(message = nil, **options)
    error = assert_raises(PaperArchive::Error) { model(**options) }
    assert_match(message, error.message) if message
    error
  end

  def site_fixture
    FileUtils.mkdir_p(File.join(@source, '_bibliography'))
    File.write(File.join(@source, '_bibliography', 'papers.bib'), @bib)
    Struct.new(:source, :dest, :config, :data, :pages, :static_files, :collections).new(
      @source, File.join(@source, '_site'), { 'url' => 'https://example.test', 'baseurl' => '' },
      { 'paper_archive' => @manifest }, [], [], {}
    )
  end

  def next_version(id)
    version = Marshal.load(Marshal.dump(@version))
    version['id'] = id
    version['snapshot']['bibtex'] = version['snapshot']['bibtex'].sub('v1.html', "#{id}.html")
    version
  end

  def test_adapter_creates_only_non_navigation_pages_and_one_pdf
    site = site_fixture
    PaperArchive::Generator.new.generate(site)
    assert_equal 4, site.pages.length
    assert_equal 2, site.static_files.length
    assert_empty site.collections
    assert site.pages.all? { |page| page.data['nav'] == false }
    assert_equal 3, site.pages.count { |page| page.data['sitemap'] == true }
    assert_equal 1, site.data['generated_paper_archive'].length
    landing = site.pages.find { |page| page.url == '/papers/example-paper/' }
    assert_equal 'paper_archive', landing.data['layout']
    index = site.pages.find { |page| page.url == '/papers/' }
    assert_equal 'paper_archive_index', index.data['layout']
    assert_equal 1, index.data['archived_papers'].length
    assert site.static_files.any? { |file| file.relative_path == '/papers/example-paper/v1.pdf' }
  end

  def test_adapter_preserves_literal_json_and_bibtex_without_liquid_rendering
    site = site_fixture
    PaperArchive::Generator.new.generate(site)
    bib = site.static_files.find { |file| file.is_a?(PaperArchive::LiteralBibtex) }
    record = site.pages.find { |page| page.url.end_with?('record.json') }
    [record].each do |page|
      assert_nil page.data['layout']
      assert_equal false, page.data['sitemap']
      assert_equal false, page.data['render_with_liquid']
    end
    assert_equal false, bib.data['sitemap']
    refute site.pages.any? { |page| page.url.end_with?('.bib') }
    assert_equal @snapshot['bibtex'], bib.content
    json = JSON.parse(record.content)
    assert_equal 1, json['schema_version']
    assert_equal 1, json['versions'].length
    assert_equal 'v1', json['paper']['version_id']
    refute_includes record.content, '_paper_files'
  end

  def test_adapter_validates_before_mutating_existing_pages
    site = site_fixture
    existing = Jekyll::PageWithoutAFile.new(site, @source, 'research', 'index.html')
    existing.data = { 'permalink' => '/research/', 'nav' => true }
    site.pages << existing
    @version['sha256'] = '0' * 64
    assert_raises(Jekyll::Errors::FatalException) { PaperArchive::Generator.new.generate(site) }
    assert_equal [existing], site.pages
    assert_equal true, existing.data['nav']
    assert_empty site.static_files
    refute site.data.key?('generated_paper_archive')
  end

  def test_adapter_rejects_existing_page_collision
    site = site_fixture
    existing = Jekyll::PageWithoutAFile.new(site, @source, 'papers', 'index.html')
    existing.data = { 'permalink' => '/papers/' }
    site.pages << existing
    assert_raises(Jekyll::Errors::FatalException) { PaperArchive::Generator.new.generate(site) }
    assert_equal [existing], site.pages
  end

  def test_approved_pdf_copies_to_public_route_without_changing_source
    site = site_fixture
    PaperArchive::Generator.new.generate(site)
    file = site.static_files.find { |item| item.is_a?(PaperArchive::ArchivedPDF) }
    assert_equal @pdf, file.path
    file.write(site.dest)
    output = File.join(site.dest, 'papers', 'example-paper', 'v1.pdf')
    assert_equal @version['sha256'], Digest::SHA256.file(output).hexdigest
    assert_equal @version['sha256'], Digest::SHA256.file(@pdf).hexdigest
    refute File.exist?(File.join(site.dest, '_paper_files'))
  end

  def test_pdf_modified_after_validation_cannot_be_copied
    site = site_fixture
    PaperArchive::Generator.new.generate(site)
    File.open(@pdf, 'ab') { |file| file.write('unexpected mutation') }
    pdf = site.static_files.find { |file| file.is_a?(PaperArchive::ArchivedPDF) }
    assert_raises(PaperArchive::Error) { pdf.write(site.dest) }
    refute File.exist?(pdf.destination(site.dest))
  end

  def test_bibtex_is_written_as_exact_literal_bytes_outside_the_converter_pipeline
    site = site_fixture
    PaperArchive::Generator.new.generate(site)
    bib = site.static_files.find { |file| file.is_a?(PaperArchive::LiteralBibtex) }
    assert bib.write?
    assert_equal Time.iso8601(@version['archived_at']), bib.modified_time
    bib.write(site.dest)
    actual = File.binread(File.join(site.dest, 'papers', 'example-paper', 'v1.bib'))
    assert_equal @snapshot['bibtex'].b, actual
    assert actual.start_with?('@article{')
    refute_includes actual, '<p>'
  end

  def test_explicit_allowlist_and_stable_links
    archive = model
    assert_equal 1, archive.papers.length
    assert_equal 1, archive.files.length
    assert_equal 6, archive.outputs.length
    landing = archive.papers.first['landing']
    assert_equal '/papers/example-paper/', landing['url']
    assert_equal 'https://example.test/papers/example-paper/', landing['canonical_url']
    assert_equal 'https://example.test/papers/example-paper/v1.pdf', landing['pdf_url']
    assert_equal 'https://example.test/papers/example-paper/v1.bib', landing['bib_url']
    assert_equal false, landing['is_version']
    assert_equal false, landing['link_from_research']
    assert_equal true, archive.papers.first['versions'].first['is_version']
    assert_equal 'https://example.test/papers/example-paper/v1.html',
                 archive.papers.first['versions'].first['canonical_url']
  end

  def test_research_link_is_an_explicit_landing_only_choice
    initial_version = model.papers.first['versions'].first
    @paper['link_from_research'] = true
    paper = model.papers.first
    assert_equal true, paper['landing']['link_from_research']
    assert_equal initial_version, paper['versions'].first
    refute paper['versions'].first.key?('link_from_research')
    refute paper['landing']['versions'].first.key?('link_from_research')
    @paper['link_from_research'] = false
    assert_equal false, model.papers.first['landing']['link_from_research']
  end

  def test_research_link_rejects_non_boolean_values
    ['true', 'false', 1, 0, nil, [], {}].each do |value|
      @paper['link_from_research'] = value
      invalid(/link_from_research must be true or false/)
    end
  end

  def test_research_link_is_exposed_to_current_index_and_record_only
    @paper['link_from_research'] = true
    site = site_fixture
    PaperArchive::Generator.new.generate(site)
    assert_equal true, site.data['generated_paper_archive'].first['link_from_research']
    index = site.pages.find { |page| page.url == '/papers/' }
    assert_equal true, index.data['archived_papers'].first['link_from_research']
    json = JSON.parse(site.pages.find { |page| page.url.end_with?('record.json') }.content)
    assert_equal true, json['paper']['link_from_research']
    refute json['versions'].first.key?('link_from_research')
    version = site.pages.find { |page| page.url.end_with?('/v1.html') }
    refute version.data['archive'].key?('link_from_research')
  end

  def test_no_private_paths_in_public_records
    output = JSON.generate(model.papers)
    refute_includes output, '_paper_files'
    refute_includes output, @source
  end

  def test_unknown_schema_fields_are_rejected_instead_of_silently_ignored
    [@manifest, @paper, @version, @snapshot].each do |mapping|
      mapping['unexpected_field'] = 'Do not publish this field'
      invalid(/unknown fields unexpected_field/)
      mapping.delete('unexpected_field')
    end
    @paper['enabled'] = false
    invalid(/unknown fields enabled/)
  end

  def test_project_baseurl_is_applied_once
    @snapshot['bibtex'] = @snapshot['bibtex'].sub('https://example.test/', 'https://example.test/archive/')
    landing = model(baseurl: '/archive/').papers.first['landing']
    assert_equal '/papers/example-paper/', landing['url']
    assert_equal 'https://example.test/archive/papers/example-paper/v1.pdf', landing['pdf_url']
  end

  def test_empty_allowlist_generates_nothing
    @manifest['papers'] = []
    archive = model
    assert_empty archive.papers
    assert_empty archive.files
    assert_empty archive.outputs
  end

  def test_missing_schema_is_rejected
    @manifest.delete('schema_version')
    invalid(/schema_version/)
  end

  def test_papers_must_be_an_array
    @manifest['papers'] = { 'Example2026' => @paper }
    invalid(/papers array/)
  end

  def test_duplicate_allowlisted_key_is_rejected
    @manifest['papers'] << @paper.merge('slug' => 'another-slug')
    invalid(/Duplicate archive bib_key/)
  end

  def test_duplicate_slug_is_rejected
    @manifest['papers'] << @paper.merge('bib_key' => 'NotApproved')
    invalid(/Duplicate archive slug/)
  end

  def test_missing_bibliography_key_is_rejected
    @paper['bib_key'] = 'MissingKey'
    invalid(/Missing bibliography key/)
  end

  def test_duplicate_bibliography_keys_cannot_be_silently_renamed
    @bib += "\n@article{Example2026, title={A conflicting entry}, year={2026}}\n"
    invalid(/Duplicate bibliography key/)
  end

  def test_unsafe_slugs_are_rejected
    ['../private', 'contains space', 'UPPER', 'a/b', 'a%2fb', 'a--b', 'a.html'].each do |slug|
      @paper['slug'] = slug
      invalid(/unsafe slug/)
    end
  end

  def test_missing_versions_are_rejected
    @paper['versions'] = []
    invalid(/versions must/)
  end

  def test_duplicate_version_id_is_rejected
    @paper['versions'] << @version.dup
    invalid(/duplicate version id/)
  end

  def test_unsafe_version_ids_are_rejected
    ['../v1', 'v0', 'v01', 'latest', 'v1.html', 'V1'].each do |id|
      @version['id'] = id
      invalid(/unsafe version id/)
    end
  end

  def test_current_version_must_exist
    @paper['current_version'] = 'v2'
    invalid(/current_version is not listed/)
  end

  def test_versions_must_be_consecutive
    @paper['versions'] << next_version('v3')
    invalid(/ordered consecutively/)
  end

  def test_current_version_must_be_the_last_version
    @paper['versions'] << next_version('v2')
    invalid(/last version/)
  end

  def test_version_archive_timestamps_cannot_go_backwards
    @paper['current_version'] = 'v2'
    @paper['versions'] << next_version('v2').merge('archived_at' => '2026-09-01T00:00:00Z')
    invalid(/timestamps must be nondecreasing/)
  end

  def test_required_snapshot_fields
    %w[title abstract year bibtex authors].each do |field|
      old = @snapshot.delete(field)
      invalid(/#{field}/)
      @snapshot[field] = old
    end
  end

  def test_snapshot_authors_cannot_be_empty
    @snapshot['authors'] = []
    invalid(/authors/)
  end

  def test_current_title_must_match_bibliography
    @bib = @bib.sub('An example paper', 'A changed title')
    invalid(/snapshot title/)
  end

  def test_current_abstract_must_match_bibliography
    @bib = @bib.sub('An explicitly approved public abstract.', 'A changed abstract.')
    invalid(/snapshot abstract/)
  end

  def test_current_authors_must_match_bibliography
    @bib = @bib.sub('Zhu, Haoran', 'Zhu, Different')
    invalid(/snapshot authors/)
  end

  def test_current_year_must_match_bibliography
    @bib = @bib.sub('year = {2026}', 'year = {2027}')
    invalid(/snapshot year/)
  end

  def test_current_doi_and_journal_must_match_bibliography
    original = @bib
    @bib = original.sub('Example Journal', 'Changed Journal')
    invalid(/snapshot journal/)
    @bib = original.sub('10.0000/example', '10.0000/changed')
    invalid(/snapshot doi/)
  end

  def test_metadata_whitespace_is_normalized_for_comparison
    @snapshot['title'] = "  An   example\npaper  "
    @snapshot['authors'] = ['Haoran  Zhu', 'Ada van   Example']
    assert_equal 1, model.papers.length
  end

  def test_bibtex_citation_must_match_its_own_snapshot
    @snapshot['bibtex'] = @snapshot['bibtex'].sub('An example paper', 'Wrong citation title')
    invalid(/snapshot title/)
  end

  def test_bibtex_url_must_reference_its_own_immutable_version
    @snapshot['bibtex'] = @snapshot['bibtex'].sub('v1.html', '')
    invalid(/bibtex url must equal/)
  end

  def test_bibtex_url_is_required
    @snapshot['bibtex'] = @snapshot['bibtex'].lines.reject { |line| line.include?('url =') }.join
    invalid(/bibtex url must equal/)
  end

  def test_bibtex_citation_must_have_exactly_one_matching_key
    original = @snapshot['bibtex']
    @snapshot['bibtex'] = original.sub('Example2026', 'WrongKey')
    invalid(/exactly one entry/)
    @snapshot['bibtex'] = original + original.sub('Example2026', 'AnotherKey')
    invalid(/exactly one entry/)
  end

  def test_each_version_preserves_its_own_snapshot
    initial_version_record = model.papers.first['versions'].first
    old_snapshot = Marshal.load(Marshal.dump(@snapshot))
    current_snapshot = next_version('v2')['snapshot']
    current_snapshot['title'] = 'An updated example paper'
    current_snapshot['bibtex'] = current_snapshot['bibtex'].sub('An example paper', current_snapshot['title'])
    @bib = @bib.sub('An example paper', current_snapshot['title'])
    @paper['current_version'] = 'v2'
    @paper['versions'] << @version.merge('id' => 'v2', 'snapshot' => current_snapshot)
    archive = model
    paper = archive.papers.first
    assert_equal 'An updated example paper', paper['landing']['title']
    assert_equal old_snapshot['title'], paper['versions'][0]['title']
    assert_equal 'An updated example paper', paper['versions'][1]['title']
    assert_equal 2, paper['landing']['versions'].length
    assert_equal initial_version_record, paper['versions'][0]
    assert_equal 'v1', paper['versions'][0]['current_version']
    assert_equal 1, paper['versions'][0]['versions'].length
    assert_equal 2, archive.files.length
    assert_equal 9, archive.outputs.length
    assert_equal 'https://example.test/papers/example-paper/v2.pdf', paper['landing']['pdf_url']
  end

  def test_path_traversal_and_absolute_paths_are_rejected
    ['../v1.pdf', '/tmp/v1.pdf', '_paper_files/../v1.pdf', '_paper_files/a/../../v1.pdf',
     '_paper_files//v1.pdf', '_paper_files/a\\v1.pdf', '_paper_files/%2e%2e/v1.pdf'].each do |source|
      @version['source'] = source
      invalid(/safe path/)
    end
  end

  def test_missing_pdf_is_rejected
    File.delete(@pdf)
    invalid(/source is missing/)
  end

  def test_symlink_outside_approved_directory_is_rejected
    outside = File.join(@source, 'outside.pdf')
    File.rename(@pdf, outside)
    File.symlink(outside, @pdf)
    invalid(/escapes _paper_files/)
  end

  def test_symlinked_archive_root_is_rejected
    root = File.join(@source, '_paper_files')
    other = File.join(@source, 'other-directory')
    File.rename(root, other)
    File.symlink(other, root)
    invalid(/real directory/)
  end

  def test_bad_checksum_format_is_rejected
    @version['sha256'] = 'not-a-checksum'
    invalid(/64 lowercase/)
  end

  def test_wrong_checksum_is_rejected
    @version['sha256'] = '0' * 64
    invalid(/checksum does not match/)
  end

  def test_non_pdf_is_rejected_even_with_matching_checksum
    File.binwrite(@pdf, '<html>Not a PDF</html>')
    @version['sha256'] = Digest::SHA256.file(@pdf).hexdigest
    invalid(/must start with %PDF-/)
  end

  def test_pdf_larger_than_five_megabytes_is_rejected
    File.open(@pdf, 'ab') { |file| file.truncate(PaperArchive::MAX_PDF_BYTES + 1) }
    @version['sha256'] = Digest::SHA256.file(@pdf).hexdigest
    invalid(/at most 5 MB/)
  end

  def test_dates_must_not_be_ambiguous_or_invalid
    original = @version['archived_at']
    @version['archived_at'] = '2026-10-01'
    invalid(/UTC timestamp/)
    @version['archived_at'] = original
    @version['archived_on'] = '2026-02-30'
    invalid(/invalid archive date/)
  end

  def test_timezone_must_look_like_an_iana_name
    @version['archive_timezone'] = '-0700'
    invalid(/IANA timezone/)
  end

  def test_existing_routes_and_static_files_cannot_be_overwritten
    ['/papers/', '/papers/index.html', '/papers/example-paper/',
     '/papers/example-paper/index.html', '/papers/example-paper/v1.html',
     '/papers/example-paper/v1.pdf', '/papers/example-paper/v1.bib',
     '/papers/example-paper/record.json', '/papers', '/papers/example-paper'].each do |route|
      invalid(/output collision/, reserved_routes: [route])
    end
  end

  def test_neighboring_routes_are_allowed
    assert_equal 1, model(reserved_routes: ['/research/', '/papers-elsewhere/', '/papers/other/']).papers.length
  end

  def test_invalid_site_origins_and_baseurls_are_rejected
    ['//example.test', 'https://example.test/path', 'https://user:password@example.test',
     'https://example.test?secret=yes', 'ftp://example.test'].each { |origin| invalid(/site.url/, url: origin) }
    ['../archive', '/archive/../private', '//example.test', '/with space'].each do |base|
      invalid(/site.baseurl/, baseurl: base)
    end
  end
end
