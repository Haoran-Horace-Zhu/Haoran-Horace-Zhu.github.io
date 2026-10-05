require 'minitest/autorun'
require 'liquid'
require 'yaml'
require_relative '../_plugins/hide-custom-bibtex'

module ResearchNotesTestFilters
  # Keep these template tests independent of Jekyll's full build pipeline.
  def markdownify(value)
    "<p>#{value}</p>"
  end

  def relative_url(value)
    value
  end
end

Liquid::Template.register_filter(ResearchNotesTestFilters)

class ResearchNotesTest < Minitest::Test
  Site = Struct.new(:config)

  def setup
    @template = File.read(File.expand_path('../_layouts/bib_research.liquid', __dir__)).sub(/\A---\n---\n/, '')
    @config = YAML.load_file(File.expand_path('../_config.yml', __dir__))
    @entry = {
      'key' => 'ExampleNote', 'entry_kind' => 'note', 'title' => 'A mathematical note',
      'year' => '2026', 'abstract' => 'A mathematical abstract.',
      'pdf' => 'example-note.pdf', 'bibtex_show' => true,
      'background' => 'I wrote this note while studying an example.',
      'bibtex' => "@misc{ExampleNote,\n  title = {A mathematical note},\n  background = {A personal account.},\n  entry_kind = {note},\n  year = {2026}\n}\n"
    }
  end

  def render(entry = @entry, linked: false)
    archive = [{ 'bib_key' => entry['key'], 'url' => '/papers/example/', 'link_from_research' => linked }]
    Liquid::Template.parse(@template).render!(
      { 'entry' => entry, 'site' => { 'data' => { 'generated_paper_archive' => archive } } },
      registers: { site: Site.new(@config) }
    )
  end

  def test_note_title_is_plain_even_when_archive_is_opted_in
    title = render(linked: true)[/<h3\b.*?<\/h3>/m]
    assert_includes title, 'A mathematical note'
    refute_includes title, '<a '
  end

  def test_existing_archive_title_link_is_preserved
    title = render(@entry.merge('entry_kind' => 'preprint'), linked: true)[/<h3\b.*?<\/h3>/m]
    assert_includes title, 'href="/papers/example/"'
  end

  def test_background_reuses_inline_panel_controls
    html = render
    assert_includes html, 'data-bib-panel="background-ExampleNote"'
    assert_includes html, 'aria-controls="background-ExampleNote" aria-expanded="false">Background</button>'
    assert_includes html, 'id="background-ExampleNote" role="region" aria-label="Background"'
    assert_includes html, '<p>I wrote this note while studying an example.</p>'
    assert_includes html, 'data-bib-panel="abstract-ExampleNote"'
    assert_includes html, 'href="/assets/pdf/example-note.pdf">PDF</a>'
    assert_includes html, 'data-bib-panel="bibtex-ExampleNote"'
  end

  def test_no_empty_background_button
    refute_includes render(@entry.reject { |key, _| key == 'background' }), '>Background</button>'
    refute_includes render(@entry.merge('background' => '')), '>Background</button>'
    refute_includes render(@entry.merge('entry_kind' => 'preprint')), '>Background</button>'
  end

  def test_background_is_not_part_of_bibtex_citation
    citation = render[/<pre><code>(.*?)<\/code><\/pre>/m, 1]
    refute_match(/background|personal account|entry_kind/, citation)
    assert_includes citation, 'A mathematical note'
    assert_includes citation, '2026'
  end

  def test_notes_section_has_its_own_query_and_follows_preprints
    page = File.read(File.expand_path('../_pages/research.md', __dir__))
    assert_operator page.index('id="preprints"'), :<, page.index('id="notes"')
    assert_operator page.index('id="notes"'), :<, page.index('id="thesis"')
    assert_includes page, 'Notes and results <span class="research-notes__status">(not intended for publication)</span>'
    assert_includes page, '--group_by none --query @*[entry_kind=note]'
  end
end
