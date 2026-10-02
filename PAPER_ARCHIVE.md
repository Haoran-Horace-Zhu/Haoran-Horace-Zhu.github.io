# Personal paper archive

This archive gives approved, self-hosted papers permanent landing pages, bibliographic metadata and versioned files. It preserves the presentation of the homepage and Research listing, paper buttons, CV, navigation and search menu. A Research title links to its archive only when explicitly opted in; currently this applies only to *Diagonal trace identities for bosonic and fermionic matrices*. It is not an arXiv mirror or a claim that a paper has been peer reviewed.

## Public addresses

For the first archived paper:

- Index: `/papers/`
- Latest record: `/papers/diagonal-trace-identities/`
- Fixed version: `/papers/diagonal-trace-identities/v1.html`
- Fixed PDF and citation: `v1.pdf` and `v1.bib`, in the same directory
- Machine-readable record: `record.json`, in the same directory

The original `/assets/pdf/zhu-diagonal-trace-identities-2026.pdf` is deliberately unchanged. Existing links still work. New paper and version pages are ordinary public HTML pages, available to people and crawlers alike, and included in the sitemap. They are not added to the navigation or site search menu.

## Publication is explicit

`_data/paper_archive.yml` is the only publication allowlist. A file or bibliography entry is **not** published merely because it exists. Files must be placed under `_paper_files/` and explicitly listed. The generator never scans Downloads, Overleaf, manuscript folders or research programme pages. The source folder, tests, scripts and this guide are excluded from the generated website.

Only use a manuscript that the author has approved for public distribution and is entitled to share. Do not copy a publisher's PDF without checking the relevant permission. Do not add confidential notes, unapproved co-authored drafts, hidden programmes or private local paths to metadata.

The GitHub repository itself is public. Excluding a file from the built website is **not** access control: a committed file may still be read on GitHub. Only approved public material belongs in this repository, even if it has not yet been added to the archive allowlist.

## Adding an approved paper

1. Ensure its entry in `_bibliography/papers.bib` has the agreed title, full author list, year and abstract. Updating that bibliography also updates the existing Research listing; obtain the owner's agreement if this is a new listing.
2. Choose a short permanent lowercase slug. Copy the approved, text-searchable PDF to `_paper_files/<slug>/v1.pdf`. Never modify an existing archived file in place. The build checks the PDF signature, a maximum size of 5 MB and a SHA-256 digest. These checks do not replace inspecting the actual title, authors and abstract in the PDF.
3. Obtain its digest with `shasum -a 256 _paper_files/<slug>/v1.pdf`.
4. Add a record to the allowlist using the existing entry as the schema example. `bib_key` must match the bibliography. Supply the digest, an actual UTC `archived_at` timestamp, the corresponding local `archived_on` date, and its IANA timezone.
5. Copy the agreed metadata and a complete BibTeX citation into the version's `snapshot`. The title, authors, year, abstract and supplied journal/DOI/arXiv fields must agree with the bibliography. A fixed-version BibTeX URL should point to `/papers/<slug>/v1.html`. Do not invent a DOI, publication date, journal acceptance, licence or priority claim.
6. With the owner's approval, set the paper-level `link_from_research: true`. The Research title then links to the stable latest record without changing its typography or other buttons. This is optional and defaults to false. It does not add the paper to News or Selected Publications. For a new self-hosted preprint, use `entry_kind={preprint}` in the bibliography and an absolute archive PDF URL, such as `https://haoran-horace-zhu.github.io/papers/<slug>/v1.pdf`; a relative bibliography PDF path is otherwise interpreted beneath `/assets/pdf/`. Do not repoint existing PDF buttons without a separate request.
7. Run the checks below, inspect the new page on desktop and mobile, and publish only after they pass.

The snapshot is intentional: later edits to the main bibliography must not silently rewrite an old archived version. Metadata corrections that change the current snapshot should be made as a new archive version, preserving the previous record.

## Revisions and dates

For a revision, append `v2` (then `v3`, etc.), use a new PDF path, timestamp, digest and metadata snapshot, and set `current_version` to that version. Never recycle a slug or version number. The latest record follows the current version; prior version PDFs, citations and scholarly content remain fixed. Old version pages retain the history known at their creation and link to the latest record.

An **archive date** records the creation of that archive copy. It is not evidence of the first public posting, the date of a mathematical result, or the journal publication date. The first record preserves an already-public PDF unchanged, and explicitly says so. Citation dates come from the bibliography, never from an archive timestamp. Version numbers are labelled **archive versions**, not manuscript or arXiv versions.

The SHA-256 checksum identifies exact file bytes. It is useful for detecting accidental replacement; it is not an independently certified timestamp. Git/deployment history and permanent public URLs improve traceability but cannot by themselves establish mathematical priority, novelty or correctness. No external deposit or account registration is performed by this archive.

## Verification and deployment

```sh
bundle exec ruby tests/paper_archive_test.rb
python3 -m unittest discover -s tests -p 'test_*.py' -v
TZ=UTC JEKYLL_ENV=production bundle exec jekyll build --trace
python3 scripts/verify_paper_archive.py --site _site --forbid-route /research/current/
```

Omit `--forbid-route` only after the owner has deliberately restored the programmes. The deployment workflow derives this guard from `research_programmes_visible`.

The workflow checks against the previously deployed `gh-pages` tree before publishing. For changes confined to archive infrastructure it compares every existing page's body, links, navigation/search scripts, head resources and existing assets. Generated footer dates are restored to their previous value: an infrastructure-only update must not change the visible 'Last updated' date of an otherwise unchanged page. The legacy notebook converter also generates a random temporary filename as its HTML title; only this precisely recognised temporary label is restored from the baseline. The rest of that document must still match. Existing global structured metadata may be corrected without changing presentation. Local builds use UTC, matching GitHub's build environment, so News dates do not shift with the developer's timezone.

The explicit `--allow-archive-title-links` mode permits only the recognised title-link wrapper for opted-in archive records on Research. It does not permit changed title text, reordered papers, changed paper buttons, JavaScript click handlers or stylesheet changes. All unrelated pages remain under the strict comparison, including their footer dates. The ordinary strict mode still permits no changes to existing click targets.

For ordinary content updates, verification still protects archived PDF/BibTeX bytes and the scholarly content of version pages, while permitting intentional changes to the rest of the site and shared navigation. Latest landing pages and `record.json` can evolve as versions are added. New archive-only CSS does not style existing pages.

The generated-site verifier checks full visible abstracts, title/author/year consistency, canonical and citation URLs, valid JSON-LD, same-directory PDF links, checksums, BibTeX/record links, robots access, sitemap inclusion, internal links and forbidden routes. Opted-in Research title links are checked against the corresponding latest record, not a fixed version or PDF. Verification reports are saved as workflow artifacts. A failed check prevents deployment. Deployment runs are serialised so an older concurrent run cannot remove a version that has just been published.

## Discoverability and its limits

Each paper has a human-readable standalone page, full abstract, downloadable text-searchable PDF, Scholar-style `citation_*` tags and `ScholarlyArticle` JSON-LD. HTML records are included in the existing sitemap. The existing robots policy allows crawling and is not changed by this feature.

The Diagonal paper has a normal HTML link from its Research title to its archive. Its original PDF, Abstract and Bib buttons are unchanged, as are all other paper titles. This gives people and crawlers a direct route from the homepage through Research to the archive and its versioned files, in addition to the sitemap. Future archive titles can be connected individually with the same explicit opt-in. No background or contribution paragraph is required when the author's abstract already provides that information.

There are no hidden keyword blocks, bot-only pages or fabricated publication dates. Public availability and correct metadata do not guarantee Google Scholar inclusion, prompt indexing, citation by a search-enabled AI, or inclusion in model training. Search Console submission can be done separately if the owner chooses; no account connection or submission is assumed.
