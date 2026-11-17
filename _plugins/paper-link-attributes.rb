# frozen_string_literal: true

require 'nokogiri'
require 'uri'

module PaperLinkAttributes
  module_function

  def paper_link?(href)
    uri = URI.parse(href)
    return false unless uri.is_a?(URI::HTTP)

    case uri.host&.downcase
    when 'researchgate.net', 'www.researchgate.net'
      uri.path.match?(%r{\A/(?:profile/[^/]+/)?publication/\d+(?:[_/]|\z)})
    when 'arxiv.org', 'www.arxiv.org', 'export.arxiv.org'
      uri.path.match?(%r{\A/(?:abs|pdf|html|format|ps)/[^/]+})
    when 'doi.org', 'dx.doi.org'
      uri.path.match?(%r{\A/10\.\d+/.+})
    else
      false
    end
  rescue URI::InvalidURIError
    false
  end

  def remove_nofollow(html)
    document = Nokogiri::HTML(html)
    changed = false
    document.css('a[href][rel]').each do |link|
      values = link['rel'].split
      next unless values.any? { |value| value.casecmp?('nofollow') } && paper_link?(link['href'])

      values.reject! { |value| value.casecmp?('nofollow') }
      if values.empty?
        link.remove_attribute('rel')
      else
        link['rel'] = values.join(' ')
      end
      changed = true
    end
    changed ? document.to_html : html
  end
end

# Run after jekyll-link-attributes has added the site's normal defaults.
Jekyll::Hooks.register %i[pages documents], :post_render, priority: :low do |page|
  next unless page.output_ext == '.html' && page.output.match?(/nofollow/i)

  page.output = PaperLinkAttributes.remove_nofollow(page.output)
end
