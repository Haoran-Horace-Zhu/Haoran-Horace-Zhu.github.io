"""Stdlib regression tests; fixtures are generated in temporary directories."""

import hashlib
import html
import importlib.util
import json
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "verify_paper_archive.py"
SPEC = importlib.util.spec_from_file_location("verify_paper_archive", SCRIPT)
verify = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(verify)

ORIGIN = "https://example.test"
TITLE = "A theorem & its applications"
ABSTRACT = "We prove a theorem using $x < y$ & $z$. This is the full abstract."
PDF = b"%PDF-1.4\nminimal signature-only test fixture\n"
BIB = "@article{theorem, title={A theorem and its applications}, year={2024}}\n"


def document(body, head="", date="October 01, 2026"):
    return (
        '<!doctype html><html><head><title>Existing site</title>'
        '<link rel="stylesheet" href="/assets/site.css">'
        + head + '</head><body><nav><a href="/">Home</a></nav>' + body
        + '<footer>Last updated: ' + date + '.</footer>'
        '<script src="/assets/site.js"></script></body></html>'
    )


class ArchiveFixture(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.site = self.root / "site"
        self.site.mkdir()
        self.write("assets/site.css", "body{color:black}\n")
        self.write("assets/site.js", "window.siteReady = true;\n")
        self.write("index.html", document('<main id="main"><h1>Home</h1><a href="/research/">Research</a></main>'))
        self.write("research/index.html", document("<main><h1>Research</h1></main>"))
        self.write("404.html", document("<h1>Not found</h1>"))
        self.write("robots.txt", "User-agent: *\nAllow: /\nSitemap: https://example.test/sitemap.xml\n")
        landing = ORIGIN + "/papers/theorem/"
        self.entry = {
            "title": TITLE, "authors": ["Ada Example", "Ben Sample"], "year": 2024,
            "abstract": ABSTRACT,
            "canonical_url": landing, "pdf_url": landing + "v1.pdf", "bib_url": landing + "v1.bib",
            "bibtex": BIB, "sha256": hashlib.sha256(PDF).hexdigest(),
            "archived_on": "2026-10-01", "version_id": "v1",
            "archived_at": "2026-10-02T01:28:09Z", "archive_timezone": "America/Los_Angeles",
            "record_url": landing + "record.json",
        }
        self.version = dict(self.entry, canonical_url=landing + "v1.html")
        self.record = {"schema_version": 1, "paper": self.entry, "versions": [self.version]}
        self.write("papers/theorem/v1.pdf", PDF)
        self.write("papers/theorem/v1.bib", BIB)
        self.save_record()
        self.save_paper("index.html", self.entry)
        self.save_paper("v1.html", self.version)
        self.write("papers/index.html", document('<h1>Papers</h1><a href="theorem/">The theorem</a>'))
        self.write("sitemap.xml", '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
                   '<url><loc>https://example.test/</loc></url><url><loc>https://example.test/research/</loc></url>'
                   '<url><loc>https://example.test/papers/</loc></url>'
                   '<url><loc>' + landing + '</loc></url>'
                   '<url><loc>' + landing + 'v1.html</loc></url></urlset>')

    def write(self, name, content):
        path = self.site / name
        path.parent.mkdir(parents=True, exist_ok=True)
        if isinstance(content, bytes):
            path.write_bytes(content)
        else:
            path.write_text(content, encoding="utf-8")
        return path

    def replace(self, name, old, new):
        path = self.site / name
        path.write_text(path.read_text(encoding="utf-8").replace(old, new), encoding="utf-8")

    def save_record(self):
        self.write("papers/theorem/record.json", json.dumps(self.record))

    def save_paper(self, name, entry, article=None):
        if article is None:
            article = {
                "@context": "https://schema.org", "@type": "ScholarlyArticle", "headline": TITLE,
                "author": [{"@type": "Person", "name": author} for author in entry["authors"]],
                "url": entry["canonical_url"],
                "abstract": ABSTRACT, "description": ABSTRACT,
                "encoding": {"@type": "MediaObject", "contentUrl": entry["pdf_url"], "sha256": entry["sha256"]},
            }
        title = TITLE.replace("&", "&amp;")
        self.write("papers/theorem/" + name,
                   '<html><head><title>' + title + ' | Archive</title>'
                   '<link rel="canonical" href="' + entry["canonical_url"] + '">'
                   '<meta name="citation_title" content="' + title + '">'
                   '<meta name="citation_publication_date" content="2024">'
                   '<meta name="citation_author" content="Ada Example">'
                   '<meta name="citation_author" content="Ben Sample">'
                   '<meta name="citation_pdf_url" content="' + entry["pdf_url"] + '">'
                   '<meta name="citation_abstract_html_url" content="' + entry["canonical_url"] + '">'
                   '<script type="application/ld+json">' + json.dumps(article) + '</script>'
                   '</head><body><nav><a href="/">Home</a></nav><article class="paper-archive"><h1>' + title + '</h1>'
                   '<ul><li class="paper-author">Ada Example</li><li class="paper-author">Ben Sample</li></ul>'
                   '<span class="paper-year">2024</span>'
                   '<div class="paper-archive__abstract"><p>' + html.escape(ABSTRACT) + '</p></div>'
                   '<a href="v1.pdf">PDF</a><a href="v1.bib">BibTeX</a><a href="record.json">Record</a>'
                   '<a href="v1.html">Version</a><a href="/research/#research">Research</a>'
                   '</article><footer>Last updated: October 01, 2026.</footer></body></html>')
        self.replace("research/index.html", "<h1>Research</h1>", '<h1 id="research">Research</h1>')

    def run_verifier(self, baseline=None, preserve=False, immutable_only=False, forbid_routes=None, preserve_notebook=False, allow_title_links=False):
        checker = verify.Verifier(self.site, baseline, preserve, immutable_only, forbid_routes, preserve_notebook, allow_title_links)
        checker._text_extractor = None
        return checker.run()

    def assert_failure(self, report, phrase):
        self.assertFalse(report["ok"], report)
        self.assertTrue(any(phrase in error for error in report["errors"]), report["errors"])

    def baseline(self, with_archive=False):
        target = self.root / "baseline"
        shutil.copytree(self.site, target)
        if not with_archive:
            shutil.rmtree(target / "papers")
        return target

    def research_entry(self, linked=True, details=False):
        title = html.escape(TITLE)
        if linked:
            title = '<a class="bib-entry__archive-link" href="/papers/theorem/" style="' + verify.ARCHIVE_TITLE_STYLE + '">' + title + '</a>'
        entry = ('<article class="bib-entry" id="TheoremKey" data-paper-key="TheoremKey">'
                 '<h3 class="bib-entry__title" id="title-TheoremKey">' + title + '</h3>'
                 '<div class="bib-entry__actions"><a href="/papers/theorem/v1.pdf">PDF</a>'
                 '<button type="button" data-bib-panel="bibtex-TheoremKey">Bib</button></div></article>')
        if details:
            entry = '<details><summary>Preprints</summary>' + entry + '</details>'
        self.write("research/index.html", document('<h1 id="research">Research</h1>' + entry))

    def opt_in_research(self, linked=True, details=False):
        self.entry.update({"link_from_research": True, "bib_key": "TheoremKey", "current_version": "v1"})
        self.save_record()
        self.research_entry(linked=linked, details=details)

    def initial_ad_fixture(self, transient_v2=False):
        """Add the exact abstract migration beside an unrelated protected paper."""
        old_pdf, new_pdf = PDF + b"old AD", PDF + b"corrected AD"
        for name, value in (("INITIAL_AD_OLD_SHA", hashlib.sha256(old_pdf).hexdigest()),
                            ("INITIAL_AD_NEW_SHA", hashlib.sha256(new_pdf).hexdigest())):
            override = patch.object(verify, name, value)
            override.start()
            self.addCleanup(override.stop)
        folder = verify.INITIAL_AD_PATH
        url = ORIGIN + "/" + folder
        title = "Cutoff for random Cayley graphs of finite groups"

        def version(number, abstract, checksum):
            return {
                "title": title, "authors": ["Haoran Zhu"], "year": "2026", "abstract": abstract,
                "current_version": number, "version_id": number,
                "canonical_url": url + number + ".html", "pdf_url": url + number + ".pdf",
                "bib_url": url + number + ".bib", "sha256": checksum,
                "bibtex": "@article{AD, title={" + title + "}, url={" + url + number + ".html}}\n",
                "record_url": url + "record.json", "archived_at": "2026-10-07T00:00:02Z",
                "archived_on": "2026-10-06", "archive_timezone": "America/Los_Angeles",
                "note": "First version.",
            }

        def page(name, item):
            schema = {"@context": "https://schema.org", "@type": "ScholarlyArticle",
                      "headline": title, "author": [{"@type": "Person", "name": "Haoran Zhu"}],
                      "url": item["canonical_url"], "abstract": item["abstract"],
                      "encoding": {"contentUrl": item["pdf_url"], "sha256": item["sha256"]}}
            self.write(folder + name,
                       '<html><head><title>' + title + '</title><link rel="canonical" href="' + item["canonical_url"] + '">'
                       '<meta name="citation_title" content="' + title + '">'
                       '<meta name="citation_author" content="Haoran Zhu">'
                       '<meta name="citation_publication_date" content="2026">'
                       '<meta name="citation_pdf_url" content="' + item["pdf_url"] + '">'
                       '<meta name="citation_abstract_html_url" content="' + item["canonical_url"] + '">'
                       '<script type="application/ld+json">' + json.dumps(schema) + '</script></head>'
                       '<body><article class="paper-archive"><h1>' + title + '</h1>'
                       '<span class="paper-author">Haoran Zhu</span><span class="paper-year">2026</span>'
                       '<div class="paper-archive__abstract"><p>' + item["abstract"] + '</p></div>'
                       '<a href="' + item["pdf_url"] + '">PDF</a>'
                       '<a href="' + item["bib_url"] + '">BibTeX</a>'
                       '<code>' + item["sha256"] + '</code></article></body></html>')

        def publish(versions):
            latest = dict(versions[-1], canonical_url=url)
            self.write(folder + "record.json", json.dumps({"schema_version": 1, "paper": latest, "versions": versions}))
            page("index.html", latest)
            for item in versions:
                name = item["version_id"]
                page(name + ".html", item)
                self.write(folder + name + ".bib", item["bibtex"])

        first = version("v1", verify.INITIAL_AD_OLD_ABSTRACT, verify.INITIAL_AD_OLD_SHA)
        corrected = dict(first, abstract=verify.INITIAL_AD_NEW_ABSTRACT, sha256=verify.INITIAL_AD_NEW_SHA)
        versions = [first]
        self.write(folder + "v1.pdf", old_pdf)
        if transient_v2:
            versions.append(version("v2", verify.INITIAL_AD_NEW_ABSTRACT, verify.INITIAL_AD_NEW_SHA))
            self.write(folder + "v2.pdf", new_pdf)
        publish(versions)
        locations = [url, url + "v1.html"] + ([url + "v2.html"] if transient_v2 else [])
        self.replace("sitemap.xml", "</urlset>", "".join('<url><loc>' + loc + '</loc></url>' for loc in locations) + "</urlset>")
        baseline = self.baseline(with_archive=True)
        publish([corrected])
        self.write(folder + "v1.pdf", new_pdf)
        if transient_v2:
            for suffix in ("html", "pdf", "bib"):
                (self.site / folder / ("v2." + suffix)).unlink()
            self.replace("sitemap.xml", '<url><loc>' + url + 'v2.html</loc></url>', "")
        return baseline

    def test_initial_ad_correction_from_v1_only(self):
        report = self.run_verifier(self.initial_ad_fixture(), immutable_only=True)
        self.assertTrue(report["ok"], report)
        self.assertEqual(report["approved_initial_corrections"],
                         [verify.INITIAL_AD_PATH + "v1.html", verify.INITIAL_AD_PATH + "v1.pdf"])

    def test_initial_ad_correction_removes_only_the_known_transient_v2(self):
        report = self.run_verifier(self.initial_ad_fixture(transient_v2=True), immutable_only=True)
        self.assertTrue(report["ok"], report)
        self.assertEqual(len(report["approved_initial_corrections"]), 5)

    def test_corrected_ad_baseline_needs_no_exception(self):
        self.initial_ad_fixture(transient_v2=True)
        baseline = self.root / "corrected-baseline"
        shutil.copytree(self.site, baseline)
        report = self.run_verifier(baseline, immutable_only=True)
        self.assertTrue(report["ok"], report)
        self.assertEqual(report["approved_initial_corrections"], [])

    def test_initial_ad_correction_rejects_wrong_new_pdf(self):
        baseline = self.initial_ad_fixture()
        self.write(verify.INITIAL_AD_PATH + "v1.pdf", PDF + b"unapproved replacement")
        self.assert_failure(self.run_verifier(baseline, immutable_only=True), "existing asset bytes changed")

    def test_initial_ad_correction_rejects_wrong_old_pdf(self):
        baseline = self.initial_ad_fixture()
        (baseline / verify.INITIAL_AD_PATH / "v1.pdf").write_bytes(PDF + b"unknown old version")
        self.assert_failure(self.run_verifier(baseline, immutable_only=True), "existing asset bytes changed")

    def test_initial_ad_correction_rejects_extra_abstract_change(self):
        baseline = self.initial_ad_fixture()
        for name in ("record.json", "index.html", "v1.html"):
            self.replace(verify.INITIAL_AD_PATH + name, verify.INITIAL_AD_NEW_ABSTRACT,
                         verify.INITIAL_AD_NEW_ABSTRACT + " Another claim.")
        self.assert_failure(self.run_verifier(baseline, immutable_only=True), "immutable version article")

    def test_initial_ad_correction_rejects_extra_version_article_change(self):
        baseline = self.initial_ad_fixture()
        self.replace(verify.INITIAL_AD_PATH + "v1.html", "</article>", "<p>Unapproved change</p></article>")
        self.assert_failure(self.run_verifier(baseline, immutable_only=True), "immutable version article")

    def test_initial_ad_correction_rejects_changed_original_date(self):
        baseline = self.initial_ad_fixture()
        self.replace(verify.INITIAL_AD_PATH + "record.json", "2026-10-07T00:00:02Z", "2026-10-07T00:00:03Z")
        self.assert_failure(self.run_verifier(baseline, immutable_only=True), "existing asset bytes changed")

    def test_initial_ad_correction_rejects_unknown_transient_pdf(self):
        baseline = self.initial_ad_fixture(transient_v2=True)
        (baseline / verify.INITIAL_AD_PATH / "v2.pdf").write_bytes(PDF + b"another version")
        self.assert_failure(self.run_verifier(baseline, immutable_only=True), "existing public route/asset is missing")

    def test_initial_ad_correction_does_not_allow_other_paper_replacement(self):
        baseline = self.initial_ad_fixture(transient_v2=True)
        self.write("papers/theorem/v1.pdf", PDF + b"unrelated change")
        self.assert_failure(self.run_verifier(baseline, immutable_only=True), "existing asset bytes changed")

    def test_initial_ad_correction_does_not_allow_other_paper_removal(self):
        baseline = self.initial_ad_fixture(transient_v2=True)
        (self.site / "papers/theorem/v1.html").unlink()
        self.assert_failure(self.run_verifier(baseline, immutable_only=True), "existing public route/asset is missing")

    def test_initial_ad_correction_does_not_allow_bibtex_replacement(self):
        baseline = self.initial_ad_fixture()
        self.write(verify.INITIAL_AD_PATH + "v1.bib", BIB)
        self.assert_failure(self.run_verifier(baseline, immutable_only=True), "existing asset bytes changed")

    def test_valid_minimal_archive(self):
        report = self.run_verifier()
        self.assertTrue(report["ok"], report)
        self.assertEqual(len(report["paper_pages_checked"]), 2)
        self.assertEqual(len(report["pdfs_checked"]), 1)

    def test_baseline_allows_only_new_pages_and_assets(self):
        baseline = self.baseline()
        self.assertTrue(self.run_verifier(baseline)["ok"])

    def test_existing_text_change_is_rejected(self):
        baseline = self.baseline()
        self.replace("index.html", "<h1>Home</h1>", "<h1>Welcome</h1>")
        self.assert_failure(self.run_verifier(baseline), "existing rendered body")

    def test_existing_click_target_change_is_rejected(self):
        baseline = self.baseline()
        self.replace("index.html", 'href="/research/"', 'href="/papers/"')
        self.assert_failure(self.run_verifier(baseline), "existing rendered body")

    def test_existing_head_resources_cannot_change(self):
        baseline = self.baseline()
        self.replace("index.html", 'href="/assets/site.css"', 'href="/assets/new.css"')
        self.assert_failure(self.run_verifier(baseline), "existing head")

    def test_new_head_jsonld_does_not_change_visual_contract(self):
        baseline = self.baseline()
        self.replace("index.html", "</head>", '<script type="application/ld+json">{"@type":"WebSite"}</script></head>')
        self.assertTrue(self.run_verifier(baseline)["ok"])

    def test_baseline_detects_any_removed_html_route(self):
        baseline = self.baseline()
        (self.site / "404.html").unlink()
        self.assert_failure(self.run_verifier(baseline), "existing public route/asset is missing")

    def test_asset_bytes_are_immutable(self):
        baseline = self.baseline()
        self.write("assets/site.js", "window.siteReady = false;\n")
        self.assert_failure(self.run_verifier(baseline), "existing asset bytes changed")

    def test_footer_changes_fail_without_explicit_preservation(self):
        baseline = self.baseline()
        self.replace("index.html", "October 01, 2026", "October 02, 2026")
        self.assert_failure(self.run_verifier(baseline), "existing rendered body")

    def test_footer_preservation_changes_only_exact_date_bytes(self):
        baseline = self.baseline()
        original = (self.site / "index.html").read_bytes()
        self.replace("index.html", "October 01, 2026", "October 02, 2026")
        report = self.run_verifier(baseline, preserve=True)
        self.assertTrue(report["ok"], report)
        self.assertEqual((self.site / "index.html").read_bytes(), original)
        self.assertEqual(report["footer_dates_restored"], ["index.html"])

    def test_footer_preservation_does_not_mask_content_change(self):
        baseline = self.baseline()
        self.replace("index.html", "October 01, 2026", "October 02, 2026")
        self.replace("index.html", "<h1>Home</h1>", "<h1>Changed</h1>")
        self.assert_failure(self.run_verifier(baseline, preserve=True), "existing rendered body")
        self.assertIn("<h1>Changed</h1>", (self.site / "index.html").read_text())

    def test_footer_preservation_requires_baseline(self):
        self.assert_failure(self.run_verifier(preserve=True), "requires --baseline")

    def test_footer_exact_format_and_count_are_required(self):
        original = b"Last updated: October 01, 2026."
        self.assertEqual(verify.restore_footer_date(original, b"Last updated: October 2, 2026."), b"Last updated: October 2, 2026.")
        doubled = b"Last updated: October 02, 2026. Last updated: October 02, 2026."
        self.assertEqual(verify.restore_footer_date(original, doubled), doubled)

    def test_pure_formatting_whitespace_does_not_fail(self):
        baseline = self.baseline()
        self.replace("index.html", "</nav><main", "</nav>\n  <main")
        self.assertTrue(self.run_verifier(baseline)["ok"])

    def test_nonempty_script_whitespace_is_not_normalized_away(self):
        old = verify.Page('<body><script>let s = "a  b";</script></body>')
        new = verify.Page('<body><script>let s = "a b";</script></body>')
        self.assertNotEqual(old.body, new.body)

    def test_bad_jsonld_is_rejected(self):
        self.replace("papers/theorem/index.html", '"@context": "https://schema.org",', '"@context": ,')
        self.assert_failure(self.run_verifier(), "invalid JSON-LD")

    def test_wrong_jsonld_type_is_rejected(self):
        self.replace("papers/theorem/index.html", '"ScholarlyArticle"', '"WebPage"')
        self.assert_failure(self.run_verifier(), "ScholarlyArticle")

    def test_invented_publication_precision_is_rejected(self):
        self.replace("papers/theorem/index.html", '"headline":', '"datePublished": "2024-01-01", "headline":')
        self.assert_failure(self.run_verifier(), "publication date/precision")

    def test_archiving_date_is_not_publication_date(self):
        self.replace("papers/theorem/index.html", 'content="2024"', 'content="2026-10-01"')
        self.assert_failure(self.run_verifier(), "archive date is being used")

    def test_visible_title_and_authors_must_match(self):
        self.replace("papers/theorem/index.html", '<li class="paper-author">Ben Sample</li>', '<li class="paper-author">Wrong Author</li>')
        self.replace("papers/theorem/index.html", "<h1>A theorem &amp; its applications</h1>", "<h1>Other title</h1>")
        report = self.run_verifier()
        self.assert_failure(report, "visible h1")
        self.assert_failure(report, "visible authors")

    def test_citation_pdf_must_be_same_directory(self):
        self.replace("papers/theorem/index.html", 'name="citation_pdf_url" content="https://example.test/papers/theorem/v1.pdf"',
                     'name="citation_pdf_url" content="https://example.test/assets/v1.pdf"')
        self.assert_failure(self.run_verifier(), "same-directory immutable")

    def test_pdf_signature_and_hash_are_checked(self):
        self.write("papers/theorem/v1.pdf", b"not a PDF")
        report = self.run_verifier()
        self.assert_failure(report, "PDF file signature")
        self.assert_failure(report, "SHA-256 differs")

    def test_bibtex_matches_record(self):
        self.write("papers/theorem/v1.bib", "wrong\n")
        self.assert_failure(self.run_verifier(), "BibTeX download differs")

    def test_malformed_record_is_rejected(self):
        self.write("papers/theorem/record.json", "[]")
        self.assert_failure(self.run_verifier(), "invalid archive record")

    def test_relative_internal_absolute_and_fragment_links_are_checked(self):
        self.replace("papers/theorem/index.html", 'href="v1.pdf"', 'href="missing.pdf"')
        self.replace("papers/theorem/v1.html", 'href="/research/#research"', 'href="http://example.test/research/#missing"')
        report = self.run_verifier()
        self.assert_failure(report, "internal link does not resolve")
        self.assert_failure(report, "no matching fragment")

    def test_missing_landing_sitemap_entry_is_rejected(self):
        self.replace("sitemap.xml", '<url><loc>https://example.test/papers/theorem/</loc></url>', "")
        self.assert_failure(self.run_verifier(), "absent from sitemap")

    def test_hidden_programmes_and_404_are_not_in_sitemap(self):
        self.replace("sitemap.xml", "</urlset>", '<url><loc>https://example.test/research/current/</loc></url>'
                     '<url><loc>https://example.test/404.html</loc></url></urlset>')
        self.write("research/current/index.html", document("Hidden programme"))
        report = self.run_verifier(forbid_routes=["/research/current/"])
        self.assert_failure(report, "forbidden public route")
        self.assert_failure(report, "hidden research programme was generated")

    def test_robots_block_is_rejected(self):
        self.write("robots.txt", "User-agent: *\nDisallow: /papers/\n")
        self.assert_failure(self.run_verifier(), "robots.txt blocks")

    def test_robots_meta_noindex_is_rejected(self):
        self.replace("papers/theorem/index.html", "</head>", '<meta name="robots" content="noindex,follow"></head>')
        self.assert_failure(self.run_verifier(), "blocked by robots metadata")

    def test_version_pdf_is_immutable_even_if_record_hash_changes(self):
        baseline = self.baseline(with_archive=True)
        changed = PDF + b"updated"
        self.write("papers/theorem/v1.pdf", changed)
        self.entry["sha256"] = self.version["sha256"] = hashlib.sha256(changed).hexdigest()
        self.save_record()
        self.assert_failure(self.run_verifier(baseline), "existing asset bytes changed")

    def test_version_html_is_immutable_but_stable_landing_can_evolve(self):
        baseline = self.baseline(with_archive=True)
        self.replace("papers/theorem/index.html", "</body>", "<p>New version available.</p></body>")
        self.assertTrue(self.run_verifier(baseline)["ok"])
        self.replace("papers/theorem/v1.html", "</body>", "<p>Changed old version.</p></body>")
        self.assert_failure(self.run_verifier(baseline), "existing rendered body")

    def test_graph_jsonld_and_year_only_date_are_supported(self):
        article = {"@type": ["CreativeWork", "ScholarlyArticle"], "name": TITLE,
                   "author": [{"name": "Ada Example"}, {"name": "Ben Sample"}],
                   "url": self.entry["canonical_url"], "datePublished": "2024", "abstract": ABSTRACT,
                   "encoding": {"contentUrl": self.entry["pdf_url"], "sha256": self.entry["sha256"]}}
        self.save_paper("index.html", self.entry, {"@graph": [article]})
        self.assertTrue(self.run_verifier()["ok"])

    def test_immutable_mode_requires_baseline(self):
        self.assert_failure(self.run_verifier(immutable_only=True), "requires --baseline")

    def test_immutable_mode_allows_theme_and_navigation_changes(self):
        baseline = self.baseline(with_archive=True)
        self.replace("index.html", "<h1>Home</h1>", "<h1>Welcome</h1>")
        self.write("assets/site.css", "body{color:blue}")
        self.replace("papers/theorem/v1.html", '<nav><a href="/">Home</a></nav>', '<nav><a href="/research/">Research</a></nav>')
        self.replace("papers/theorem/v1.html", "October 01, 2026", "October 02, 2026")
        report = self.run_verifier(baseline, immutable_only=True)
        self.assertTrue(report["ok"], report)

    def test_immutable_mode_preserves_article_and_metadata(self):
        baseline = self.baseline(with_archive=True)
        self.replace("papers/theorem/v1.html", "</article>", "<p>Changed archived abstract</p></article>")
        self.assert_failure(self.run_verifier(baseline, immutable_only=True), "immutable version article")

    def test_immutable_mode_protects_citation_metadata(self):
        baseline = self.baseline(with_archive=True)
        self.replace("papers/theorem/v1.html", "</head>", '<meta name="citation_doi" content="10.1/changed"></head>')
        self.assert_failure(self.run_verifier(baseline, immutable_only=True), "immutable version citation")

    def test_immutable_mode_protects_jsonld(self):
        baseline = self.baseline(with_archive=True)
        self.replace("papers/theorem/v1.html", '"abstract": ' + json.dumps(ABSTRACT), '"abstract": "Changed"')
        self.assert_failure(self.run_verifier(baseline, immutable_only=True), "immutable version ScholarlyArticle")

    def test_immutable_mode_preserves_only_version_footer_dates(self):
        baseline = self.baseline(with_archive=True)
        for name in ("index.html", "papers/theorem/index.html", "papers/theorem/v1.html"):
            self.replace(name, "October 01, 2026", "October 02, 2026")
        report = self.run_verifier(baseline, preserve=True, immutable_only=True)
        self.assertTrue(report["ok"], report)
        self.assertEqual(report["footer_dates_restored"], ["papers/theorem/v1.html"])
        self.assertIn("October 02, 2026", (self.site / "index.html").read_text())

    def test_programmes_can_be_restored_in_ordinary_future_builds(self):
        self.write("research/current/index.html", document("Programmes restored"))
        self.replace("sitemap.xml", "</urlset>", '<url><loc>https://example.test/research/current/</loc></url></urlset>')
        self.assertTrue(self.run_verifier()["ok"])

    def test_archive_only_baseline_preserves_programme_embargo(self):
        baseline = self.baseline()
        self.write("research/current/index.html", document("Accidental programme exposure"))
        self.assert_failure(self.run_verifier(baseline), "hidden research programme was generated")

    def test_archived_date_is_checked_in_the_named_timezone(self):
        self.entry["archived_on"] = "2026-10-02"
        self.save_record()
        self.assert_failure(self.run_verifier(), "archived_on does not match")

    def test_invalid_archive_timezone_is_rejected(self):
        self.entry["archive_timezone"] = "Mars/Olympus"
        self.save_record()
        self.assert_failure(self.run_verifier(), "invalid archive date")

    def test_jsonld_pdf_url_and_checksum_must_match(self):
        self.replace("papers/theorem/index.html", '"contentUrl": "https://example.test/papers/theorem/v1.pdf"', '"contentUrl": "https://example.test/elsewhere.pdf"')
        self.assert_failure(self.run_verifier(), "JSON-LD encoding")

    def test_abstract_url_must_identify_this_snapshot(self):
        self.replace("papers/theorem/v1.html", 'name="citation_abstract_html_url" content="https://example.test/papers/theorem/v1.html"',
                     'name="citation_abstract_html_url" content="https://example.test/papers/theorem/"')
        self.assert_failure(self.run_verifier(), "canonical snapshot/landing URL")

    def test_truncated_abstract_is_rejected(self):
        self.replace("papers/theorem/index.html", '<p>' + html.escape(ABSTRACT) + '</p>', '<p>We prove a theorem.</p>')
        self.assert_failure(self.run_verifier(), "full visible abstract")

    def test_hidden_abstract_is_rejected(self):
        self.replace("papers/theorem/index.html", '<div class="paper-archive__abstract">', '<div class="paper-archive__abstract" hidden>')
        self.assert_failure(self.run_verifier(), "abstract must be visible")

    def test_jsonld_abstract_matches_record(self):
        self.replace("papers/theorem/index.html", '"abstract": ' + json.dumps(ABSTRACT), '"abstract": "A different abstract"')
        self.assert_failure(self.run_verifier(), "JSON-LD abstract differs")

    def test_all_version_pages_must_be_in_sitemap(self):
        self.replace("sitemap.xml", '<url><loc>https://example.test/papers/theorem/v1.html</loc></url>', "")
        self.assert_failure(self.run_verifier(), "landing/version page is absent")

    def test_archive_index_must_be_in_sitemap(self):
        self.replace("sitemap.xml", '<url><loc>https://example.test/papers/</loc></url>', "")
        self.assert_failure(self.run_verifier(), "archive index is absent")

    def test_oai_searchbot_must_not_be_blocked(self):
        self.write("robots.txt", "User-agent: OAI-SearchBot\nDisallow: /papers/\n\nUser-agent: *\nAllow: /\n")
        self.assert_failure(self.run_verifier(), "robots.txt blocks OAI-SearchBot")

    def test_strict_baseline_also_freezes_version_citation_metadata(self):
        baseline = self.baseline(with_archive=True)
        self.replace("papers/theorem/v1.html", "</head>", '<meta name="citation_doi" content="10.1/changed"></head>')
        self.assert_failure(self.run_verifier(baseline), "immutable version citation")

    def test_strict_baseline_also_freezes_version_jsonld(self):
        baseline = self.baseline(with_archive=True)
        self.replace("papers/theorem/v1.html", '"headline":', '"identifier": "Changed", "headline":')
        self.assert_failure(self.run_verifier(baseline), "immutable version ScholarlyArticle")

    def test_missing_stable_landing_is_rejected(self):
        (self.site / "papers/theorem/index.html").unlink()
        self.assert_failure(self.run_verifier(), "stable paper landing page is missing")

    def test_full_publication_day_cannot_be_invented_from_year(self):
        self.replace("papers/theorem/index.html", 'content="2024"', 'content="2024-04-01"')
        self.assert_failure(self.run_verifier(), "publication date precision differs")

    def test_visible_year_cannot_be_omitted(self):
        self.replace("papers/theorem/index.html", '<span class="paper-year">2024</span>', "")
        self.assert_failure(self.run_verifier(), "visible publication year")

    def test_forbidden_route_links_are_checked_outside_the_archive(self):
        self.replace("index.html", 'href="/research/"', 'href="/research/current/"')
        self.assert_failure(self.run_verifier(forbid_routes=["/research/current/"]), "link exposes hidden research")

    def test_footer_restoration_never_writes_through_a_source_symlink(self):
        baseline = self.baseline()
        outside = self.root / "source.html"
        content = (self.site / "index.html").read_text().replace("October 01, 2026", "October 02, 2026")
        outside.write_text(content)
        (self.site / "index.html").unlink()
        (self.site / "index.html").symlink_to(outside)
        self.assert_failure(self.run_verifier(baseline, preserve=True), "points outside the site")
        self.assertEqual(outside.read_text(), content)

    def test_notebook_title_preservation_requires_baseline(self):
        self.assert_failure(self.run_verifier(preserve_notebook=True), "--preserve-notebook-title requires --baseline")

    def test_notebook_temp_title_is_preserved_without_other_byte_changes(self):
        name = "assets/jupyter/demo.ipynb.html"
        before = b"<html><head><title>jekyll-jupyter-notebook20261001-2413-sopga3</title></head><body><p>Notebook.</p></body></html>"
        self.write(name, before)
        baseline = self.baseline()
        self.replace(name, "20261001-2413-sopga3", "20261002-9999-newXYZ")
        report = self.run_verifier(baseline, preserve_notebook=True)
        self.assertTrue(report["ok"], report)
        self.assertEqual((self.site / name).read_bytes(), before)
        self.assertEqual(report["notebook_titles_restored"], [name])

    def test_notebook_title_preservation_does_not_hide_body_changes(self):
        name = "assets/jupyter/demo.ipynb.html"
        self.write(name, '<html><head><title>jekyll-jupyter-notebook20261001-2413-sopga3</title></head><body><p>Notebook.</p></body></html>')
        baseline = self.baseline()
        self.replace(name, "20261001-2413-sopga3", "20261002-9999-newXYZ")
        self.replace(name, "Notebook.", "Different content.")
        self.assert_failure(self.run_verifier(baseline, preserve_notebook=True), "existing rendered body")

    def test_only_exact_generated_notebook_titles_are_restored(self):
        name = "assets/jupyter/demo.ipynb.html"
        self.write(name, '<html><head><title>jekyll-jupyter-notebook20261001-2413-sopga3</title></head><body>Notebook</body></html>')
        baseline = self.baseline()
        self.replace(name, "jekyll-jupyter-notebook20261001-2413-sopga3", "A real notebook title")
        self.assert_failure(self.run_verifier(baseline, preserve_notebook=True), "existing head title")
        self.assertIn("A real notebook title", (self.site / name).read_text())

    def test_notebook_pattern_never_changes_other_html_titles(self):
        name = "assets/jupyter/not-a-notebook.html"
        self.write(name, '<html><head><title>jekyll-jupyter-notebook20261001-2413-sopga3</title></head><body>Notebook</body></html>')
        baseline = self.baseline()
        self.replace(name, "20261001-2413-sopga3", "20261002-9999-newXYZ")
        self.assert_failure(self.run_verifier(baseline, preserve_notebook=True), "existing head title")
        self.assertIn("20261002-9999-newXYZ", (self.site / name).read_text())

    def test_existing_root_theme_attributes_cannot_change(self):
        baseline = self.baseline()
        self.replace("index.html", "<html>", '<html data-theme="dark">')
        self.assert_failure(self.run_verifier(baseline), "existing head title")

    def test_existing_base_and_viewport_cannot_change_clicks_or_layout(self):
        baseline = self.baseline()
        self.replace("index.html", "</head>", '<base href="/other/"><meta name="viewport" content="width=1"></head>')
        self.assert_failure(self.run_verifier(baseline), "existing head title")

    def test_research_link_is_required_only_for_explicitly_opted_in_records(self):
        self.assertTrue(self.run_verifier()["ok"])
        self.entry["link_from_research"] = False
        self.save_record()
        self.assertTrue(self.run_verifier()["ok"])
        self.opt_in_research(linked=False)
        self.assert_failure(self.run_verifier(), "exactly one ordinary title anchor")

    def test_research_link_opt_in_has_strict_boolean_type(self):
        self.entry["link_from_research"] = "true"
        self.save_record()
        self.assert_failure(self.run_verifier(), "link_from_research must be a boolean")

    def test_research_title_to_landing_to_current_pdf_path(self):
        self.opt_in_research()
        report = self.run_verifier()
        self.assertTrue(report["ok"], report)
        self.assertEqual(report["research_title_links_checked"], ["TheoremKey"])

    def test_research_title_link_accepts_absolute_href(self):
        self.opt_in_research()
        self.replace("research/index.html", 'href="/papers/theorem/"', 'href="https://example.test/papers/theorem/"')
        self.assertTrue(self.run_verifier()["ok"])

    def test_research_title_cannot_target_a_frozen_version_or_pdf(self):
        for target in ("v1.html", "v1.pdf", "?download=1", "#abstract"):
            with self.subTest(target=target):
                self.opt_in_research()
                self.replace("research/index.html", 'href="/papers/theorem/"', 'href="/papers/theorem/' + target + '"')
                self.assert_failure(self.run_verifier(), "stable archive landing canonical URL")

    def test_research_title_link_must_wrap_the_exact_title(self):
        self.opt_in_research()
        self.replace("research/index.html", html.escape(TITLE) + '</a>', "Read paper</a>")
        self.assert_failure(self.run_verifier(), "title link text differs")

    def test_research_title_must_not_be_hidden_or_nofollow(self):
        for attribute in ('hidden', 'rel="nofollow"', 'aria-hidden="true"'):
            with self.subTest(attribute=attribute):
                self.opt_in_research()
                self.replace("research/index.html", '<a class="bib-entry__archive-link"', '<a ' + attribute + ' class="bib-entry__archive-link"')
                self.assert_failure(self.run_verifier(), "visible and crawlable")

    def test_research_title_in_closed_preprints_details_remains_valid(self):
        self.opt_in_research(details=True)
        self.assertTrue(self.run_verifier()["ok"])

    def test_research_title_entry_ids_must_match_the_bibliography_key(self):
        self.opt_in_research()
        self.replace("research/index.html", 'id="TheoremKey"', 'id="OtherKey"')
        self.assert_failure(self.run_verifier(), "matching id/data-paper-key")

    def test_opted_in_landing_must_link_to_declared_current_pdf(self):
        self.opt_in_research()
        self.entry["current_version"] = "v2"
        self.save_record()
        self.assert_failure(self.run_verifier(), "declared current archive version")

    def test_opted_in_landing_needs_a_real_pdf_anchor_not_just_metadata(self):
        self.opt_in_research()
        self.replace("papers/theorem/index.html", '<a href="v1.pdf">PDF</a>', '')
        self.assert_failure(self.run_verifier(), "ordinary link to the current PDF")

    def test_research_title_link_path_cannot_be_blocked_by_robots(self):
        self.opt_in_research()
        self.write("robots.txt", "User-agent: *\nDisallow: /research/\n")
        self.assert_failure(self.run_verifier(), "Research title-link discovery")

    def test_default_strict_baseline_still_rejects_the_new_title_link(self):
        self.research_entry(linked=False)
        baseline = self.baseline(with_archive=True)
        self.opt_in_research()
        self.assert_failure(self.run_verifier(baseline), "existing rendered body")

    def test_explicit_title_link_allowance_requires_strict_baseline(self):
        self.assert_failure(self.run_verifier(allow_title_links=True), "requires a strict --baseline")
        baseline = self.baseline(with_archive=True)
        self.assert_failure(self.run_verifier(baseline, immutable_only=True, allow_title_links=True), "requires a strict --baseline")

    def test_explicit_title_link_option_allows_only_the_exact_wrapper(self):
        self.research_entry(linked=False)
        baseline = self.baseline(with_archive=True)
        self.opt_in_research()
        report = self.run_verifier(baseline, allow_title_links=True)
        self.assertTrue(report["ok"], report)
        self.assertEqual(report["research_title_wrappers_allowed"], ["TheoremKey"])

    def test_existing_approved_title_link_is_unchanged_in_strict_mode(self):
        self.opt_in_research()
        baseline = self.baseline(with_archive=True)
        report = self.run_verifier(baseline, allow_title_links=True)
        self.assertTrue(report["ok"], report)
        self.assertEqual(report["research_title_wrappers_allowed"], [])

    def test_title_wrapper_option_does_not_exempt_pdf_or_bib_buttons(self):
        self.research_entry(linked=False)
        baseline = self.baseline(with_archive=True)
        self.opt_in_research()
        self.replace("research/index.html", 'href="/papers/theorem/v1.pdf"', 'href="/other.pdf"')
        self.replace("research/index.html", 'data-bib-panel="bibtex-TheoremKey"', 'data-bib-panel="wrong"')
        self.assert_failure(self.run_verifier(baseline, allow_title_links=True), "existing rendered body")

    def test_title_wrapper_option_does_not_exempt_other_markup_or_assets(self):
        self.research_entry(linked=False)
        baseline = self.baseline(with_archive=True)
        self.opt_in_research()
        self.replace("research/index.html", '<h1 id="research">Research</h1>', '<h1 id="research">Changed prose</h1>')
        self.write("assets/site.css", "body{color:red}")
        report = self.run_verifier(baseline, allow_title_links=True)
        self.assert_failure(report, "existing rendered body")
        self.assert_failure(report, "existing asset bytes changed")

    def test_title_wrapper_option_rejects_extra_handlers_and_style_changes(self):
        self.research_entry(linked=False)
        baseline = self.baseline(with_archive=True)
        for replacement in ('onclick="alert(1)" class="bib-entry__archive-link"', 'class="bib-entry__archive-link extra"'):
            with self.subTest(replacement=replacement):
                self.opt_in_research()
                self.replace("research/index.html", 'class="bib-entry__archive-link"', replacement)
                self.assert_failure(self.run_verifier(baseline, allow_title_links=True), "existing rendered body")
        self.opt_in_research()
        self.replace("research/index.html", verify.ARCHIVE_TITLE_STYLE, "color: red;")
        self.assert_failure(self.run_verifier(baseline, allow_title_links=True), "existing rendered body")

    def test_title_wrapper_option_does_not_allow_silent_opt_out_removal(self):
        self.opt_in_research()
        baseline = self.baseline(with_archive=True)
        self.entry["link_from_research"] = False
        self.save_record()
        self.research_entry(linked=False)
        self.assert_failure(self.run_verifier(baseline, allow_title_links=True), "existing rendered body")

    def test_duplicate_anchor_attributes_cannot_hide_the_browser_click_target(self):
        self.research_entry(linked=False)
        baseline = self.baseline(with_archive=True)
        self.opt_in_research()
        self.replace("research/index.html", 'href="/papers/theorem/"', 'href="/wrong/" href="/papers/theorem/"')
        report = self.run_verifier(baseline, allow_title_links=True)
        self.assert_failure(report, "existing rendered body")
        self.assert_failure(report, "duplicate HTML attributes")

    def test_duplicate_styles_cannot_be_normalised_into_the_approved_style(self):
        self.research_entry(linked=False)
        baseline = self.baseline(with_archive=True)
        self.opt_in_research()
        self.replace("research/index.html", 'style="' + verify.ARCHIVE_TITLE_STYLE + '"', 'style="color:red" style="' + verify.ARCHIVE_TITLE_STYLE + '"')
        self.assert_failure(self.run_verifier(baseline, allow_title_links=True), "existing rendered body")


if __name__ == "__main__":
    unittest.main()
