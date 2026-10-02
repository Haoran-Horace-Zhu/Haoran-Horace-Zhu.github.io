#!/usr/bin/env python3
"""Verify a generated paper archive without reading or modifying its sources.

The optional baseline is a previously built site, not a source checkout. All
old public routes, document bodies, head resources, and assets are protected.
Only generated HTML footer dates and known temporary notebook titles can be
restored, and only when explicitly requested. No network requests or third-party
Python packages are required.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import subprocess
import sys
import unicodedata
import xml.etree.ElementTree as ET
from datetime import datetime
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urljoin, urlsplit
from urllib.robotparser import RobotFileParser
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError


FOOTER_DATE = re.compile(
    rb"Last updated: (?:January|February|March|April|May|June|July|August|"
    rb"September|October|November|December) [0-9]{2}, [0-9]{4}\."
)
NOTEBOOK_TITLE = re.compile(rb"<title>(jekyll-jupyter-notebook[0-9]{8}-[0-9]+-[A-Za-z0-9]+)</title>")
NOTEBOOK_PATH = re.compile(r"^assets/(?:[^/]+/)*[^/]+\.ipynb\.html$")
VOID_TAGS = frozenset("area base br col embed hr img input link meta param source track wbr".split())
LITERAL_TAGS = frozenset(("script", "style", "pre", "textarea"))
CRAWLERS = ("*", "Googlebot", "Googlebot-Scholar", "OAI-SearchBot")
VERSION_HTML = re.compile(r"^papers/[^/]+/v[1-9][0-9]*\.html$")
GENERATED_METADATA = frozenset(("sitemap.xml", "sitemap.xml.gz", "sitemap_index.xml", "feed.xml", "atom.xml"))
ARCHIVE_TITLE_STYLE = "color: inherit; font: inherit; text-decoration: none;"


def text_key(value: object) -> str:
    """Compare rendered text without changing punctuation or word boundaries."""
    return " ".join(unicodedata.normalize("NFKC", str(value)).split())


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def explicitly_hidden(attributes: dict) -> bool:
    """Closed parent details remain crawlable; explicitly hidden markup does not."""
    style = re.sub(r"\s+", "", attributes.get("style") or "").lower()
    return bool(
        "hidden" in attributes or (attributes.get("aria-hidden") or "").lower() == "true"
        or set((attributes.get("class") or "").split()) & {"d-none", "hidden"}
        or "display:none" in style or "visibility:hidden" in style
    )


class Page(HTMLParser):
    """Small HTML event parser: retain all body attributes, links, and scripts."""

    def __init__(self, source: str):
        super().__init__(convert_charrefs=True)
        self.stack: list[tuple[str, dict[str, str | None]]] = []
        self.body: list[tuple] = []
        self.articles: list[list[tuple]] = []
        self.head_contract: list[tuple] = []
        self.metadata: dict[str, list[str]] = {}
        self.links: list[str] = []
        self.anchors: list[dict] = []
        self.bib_entries: list[dict] = []
        self.canonicals: list[str] = []
        self.ids: set[str] = set()
        self.h1: list[str] = []
        self.title: list[str] = []
        self.visible_text: list[str] = []
        self.json_ld: list[str] = []
        self.visible_authors: list[str] = []
        self.visible_years: list[str] = []
        self.abstracts: list[str] = []
        self.hidden_abstract = False
        self._h1: list[str] | None = None
        self._json: list[str] | None = None
        self._author: tuple[int, list[str]] | None = None
        self._year: tuple[int, list[str]] | None = None
        self._abstract: tuple[int, list[str]] | None = None
        self._article_start: int | None = None
        self._anchor: dict | None = None
        self.has_body = False
        self.feed(source)
        self.close()

    def inside(self, tag: str) -> bool:
        return any(name == tag for name, _ in self.stack)

    def handle_decl(self, declaration: str) -> None:
        self.head_contract.append(("declaration", declaration))

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        data = dict(attrs)
        token = ("start", tag, tuple(sorted(attrs)))
        if tag in ("html", "head"):
            self.head_contract.append(token)
        if tag == "body":
            self.has_body = True
        if tag == "article" and "paper-archive" in (data.get("class") or "").split():
            self._article_start = len(self.body)
        if tag == "body" or self.inside("body"):
            self.body.append(token)
        if self.inside("head") and (tag in ("title", "link", "style", "script", "base")
                                    or (tag == "meta" and (data.get("name") or "").lower() == "viewport")):
            if not (tag == "script" and (data.get("type") or "").lower() == "application/ld+json"):
                self.head_contract.append(token)
        if data.get("id"):
            self.ids.add(data["id"])
        if tag == "a" and data.get("name"):
            self.ids.add(data["name"])
        if data.get("href"):
            self.links.append(data["href"])
        if tag == "article" and "bib-entry" in (data.get("class") or "").split():
            self.bib_entries.append(data)
        if tag == "a":
            entry = next((attrs for name, attrs in reversed(self.stack)
                          if name == "article" and "bib-entry" in (attrs.get("class") or "").split()), {})
            heading = next((attrs for name, attrs in reversed(self.stack)
                            if name in ("h1", "h2", "h3", "h4", "h5", "h6")
                            and "bib-entry__title" in (attrs.get("class") or "").split()), None)
            heading_tag = next((name for name, attrs in reversed(self.stack)
                                if attrs is heading), None)
            self._anchor = {
                "attrs": data, "raw_attrs": tuple(attrs), "text": [], "bib_key": entry.get("data-paper-key"),
                "heading": heading,
                "heading_tag": heading_tag,
                "body_start": len(self.body) - 1 if self.inside("body") else None,
                "hidden": any(explicitly_hidden(attrs) for _, attrs in self.stack + [(tag, data)]),
            }
        if tag == "meta":
            name = (data.get("name") or data.get("property") or "").lower()
            self.metadata.setdefault(name, []).append(data.get("content") or "")
        if tag == "link" and "canonical" in (data.get("rel") or "").lower().split():
            self.canonicals.append(data.get("href") or "")
        if tag == "h1":
            self._h1 = []
        if tag == "script" and (data.get("type") or "").lower() == "application/ld+json":
            self._json = []
        classes = (data.get("class") or "").split()
        if set(classes) & {"paper-author", "paper-archive__author"} or "data-paper-author" in data:
            self._author = (len(self.stack), [])
        if set(classes) & {"paper-year", "paper-archive__year"} or "data-paper-year" in data:
            self._year = (len(self.stack), [])
        if "paper-archive__abstract" in classes:
            self._abstract = (len(self.stack), [])
            for ancestor, attributes in self.stack + [(tag, data)]:
                style = re.sub(r"\s+", "", attributes.get("style") or "").lower()
                if ("hidden" in attributes or set((attributes.get("class") or "").split()) & {"d-none", "hidden"}
                        or "display:none" in style or "visibility:hidden" in style
                        or (ancestor == "details" and "open" not in attributes)):
                    self.hidden_abstract = True
        if tag == "br" and self._abstract is not None:
            self._abstract[1].append("\n")
        if tag not in VOID_TAGS:
            self.stack.append((tag, data))

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self.handle_starttag(tag, attrs)
        if tag not in VOID_TAGS:
            self.handle_endtag(tag)

    def handle_endtag(self, tag: str) -> None:
        in_body = self.inside("body")
        if in_body:
            self.body.append(("end", tag))
        if tag == "article" and self._article_start is not None:
            self.articles.append(self.body[self._article_start:])
            self._article_start = None
        if self.inside("head") and tag in ("title", "style", "script"):
            if not (tag == "script" and self._json is not None):
                self.head_contract.append(("end", tag))
        if tag == "h1" and self._h1 is not None:
            self.h1.append(text_key("".join(self._h1)))
            self._h1 = None
        if tag == "a" and self._anchor is not None:
            self._anchor["text"] = text_key("".join(self._anchor["text"]))
            self._anchor["body_end"] = len(self.body) - 1 if in_body else None
            self.anchors.append(self._anchor)
            self._anchor = None
        if tag == "script" and self._json is not None:
            self.json_ld.append("".join(self._json))
            self._json = None
        positions = [i for i, (name, _) in enumerate(self.stack) if name == tag]
        if positions:
            depth = positions[-1]
            for field, target in (("_author", self.visible_authors), ("_year", self.visible_years), ("_abstract", self.abstracts)):
                capture = getattr(self, field)
                if capture is not None and capture[0] >= depth:
                    target.append(text_key("".join(capture[1])))
                    setattr(self, field, None)
            del self.stack[depth:]

    def handle_data(self, data: str) -> None:
        literal = any(self.inside(tag) for tag in LITERAL_TAGS)
        token_text = data if literal else re.sub(r"\s+", " ", data)
        if self.inside("body") and (literal or data.strip()):
            self.body.append(("text", token_text))
        if self.inside("head") and any(self.inside(tag) for tag in ("title", "script", "style")):
            if self._json is None and (literal or data.strip()):
                self.head_contract.append(("text", token_text))
        if self.inside("title"):
            self.title.append(data)
        if self._h1 is not None:
            self._h1.append(data)
        if self._json is not None:
            self._json.append(data)
        if self.inside("body") and not self.inside("script") and not self.inside("style"):
            self.visible_text.append(data)
            if self._anchor is not None:
                self._anchor["text"].append(data)
            for field in ("_author", "_year", "_abstract"):
                capture = getattr(self, field)
                if capture is not None:
                    capture[1].append(data)


def restore_footer_date(baseline: bytes, candidate: bytes) -> bytes:
    """Replace exact generated date phrases only; do not reserialize HTML."""
    old = FOOTER_DATE.findall(baseline)
    new = FOOTER_DATE.findall(candidate)
    if not old or len(old) != len(new):
        return candidate
    values = iter(old)
    return FOOTER_DATE.sub(lambda _: next(values), candidate)


def restore_notebook_title(baseline: bytes, candidate: bytes) -> bytes:
    """Restore only Jekyll's exact random temporary-name title, byte-for-byte."""
    old = list(NOTEBOOK_TITLE.finditer(baseline))
    new = list(NOTEBOOK_TITLE.finditer(candidate))
    if len(old) != 1 or len(new) != 1:
        return candidate
    return candidate[:new[0].start()] + old[0].group() + candidate[new[0].end():]


def scholarly_articles(value: object):
    if isinstance(value, dict):
        kinds = value.get("@type", [])
        if isinstance(kinds, str):
            kinds = [kinds]
        if any(str(kind).rstrip("/").split("/")[-1] == "ScholarlyArticle" for kind in kinds):
            yield value
        for child in value.values():
            if isinstance(child, (dict, list)):
                yield from scholarly_articles(child)
    elif isinstance(value, list):
        for child in value:
            yield from scholarly_articles(child)


def author_names(value: object) -> list[str]:
    if not isinstance(value, list):
        value = [value]
    return [text_key(item.get("name", "") if isinstance(item, dict) else item) for item in value]


class Verifier:
    def __init__(self, site: Path, baseline: Path | None = None, preserve_footer_date: bool = False,
                 immutable_versions_only: bool = False, forbid_routes: list[str] | None = None,
                 preserve_notebook_title: bool = False, allow_archive_title_links: bool = False):
        self.site = site.resolve()
        self.baseline = baseline.resolve() if baseline else None
        self.preserve_footer_date = preserve_footer_date
        self.immutable_versions_only = immutable_versions_only
        self.preserve_notebook_title = preserve_notebook_title
        self.allow_archive_title_links = allow_archive_title_links
        self.forbid_routes = ["/" + route.strip("/") + "/" for route in (forbid_routes or [])]
        # Strict baseline mode is for archive-only changes: preserve an existing
        # programme embargo. Ordinary builds and version-only checks permit an
        # explicitly authorised future restoration of the research pages.
        if self.baseline and not immutable_versions_only and not (self.baseline / "research/current").exists():
            self.forbid_routes.append("/research/current/")
        self.errors: list[str] = []
        self.warnings: list[str] = []
        self.checked_pages: list[str] = []
        self.checked_pdfs: dict[str, dict] = {}
        self.checked_research_links: list[str] = []
        self.allowed_title_wrappers: list[str] = []
        self.restored_footers: list[str] = []
        self.restored_notebook_titles: list[str] = []
        self.pages: dict[Path, Page] = {}
        self.records: dict[Path, dict | None] = {}
        self.origin: str | None = None
        self.base_path = ""
        self.sitemap_urls: set[str] = set()
        self.robot_parser: RobotFileParser | None = None
        self._text_extractor = shutil.which("pdftotext")

    def error(self, path: Path | str, message: str) -> None:
        self.errors.append(f"{path}: {message}")

    def page(self, path: Path) -> Page:
        if path not in self.pages:
            self.pages[path] = Page(path.read_text(encoding="utf-8"))
        return self.pages[path]

    def relative(self, path: Path) -> str:
        return path.relative_to(self.site).as_posix()

    def forbidden(self, route: str) -> bool:
        route = "/" + unquote(route).lstrip("/")
        if self.base_path and route.startswith(self.base_path + "/"):
            route = route[len(self.base_path):]
        return any(route == prefix.rstrip("/") or route.startswith(prefix) for prefix in self.forbid_routes)

    def resolve_url(self, value: str, current_url: str) -> Path | None:
        parsed = urlsplit(urljoin(current_url, value))
        if parsed.scheme not in ("http", "https") or parsed.netloc != urlsplit(self.origin or "").netloc:
            return None
        public_path = unquote(parsed.path)
        if self.base_path and public_path.startswith(self.base_path + "/"):
            public_path = public_path[len(self.base_path):]
        candidate = (self.site / public_path.lstrip("/")).resolve()
        if not candidate.is_relative_to(self.site):
            raise ValueError("internal URL escapes the generated site")
        if candidate.is_dir() or public_path.endswith("/"):
            candidate = candidate / "index.html"
        elif not candidate.is_file() and not candidate.suffix:
            candidate = candidate / "index.html"
        return candidate

    def check_links(self, path: Path, page: Page, current_url: str) -> None:
        for href in page.links:
            try:
                target = self.resolve_url(href, current_url)
            except ValueError as exc:
                self.error(self.relative(path), f"invalid internal link {href!r}: {exc}")
                continue
            if target is None:
                continue
            if self.forbidden(urlsplit(urljoin(current_url, href)).path):
                self.error(self.relative(path), f"link exposes hidden research programme: {href}")
            if not target.is_file():
                self.error(self.relative(path), f"internal link does not resolve: {href}")
                continue
            fragment = unquote(urlsplit(href).fragment)
            if fragment and target.suffix.lower() == ".html" and fragment not in self.page(target).ids:
                self.error(self.relative(path), f"internal link has no matching fragment: {href}")

    def compare_baseline(self) -> None:
        if self.baseline is None:
            return
        if not self.baseline.is_dir() or not any(self.baseline.rglob("*.html")):
            self.error("baseline", "must be a generated site containing HTML")
            return
        if self.baseline == self.site:
            self.error("baseline", "must be a different directory from the candidate site")
            return
        for old_path in sorted(self.baseline.rglob("*")):
            if not old_path.is_file():
                continue
            relative = old_path.relative_to(self.baseline).as_posix()
            if self.immutable_versions_only and not re.fullmatch(r"papers/[^/]+/v[1-9][0-9]*\.(?:html|pdf|bib)", relative):
                continue
            new_path = self.site / relative
            if not new_path.is_file():
                self.error(relative, "existing public route/asset is missing")
                continue
            if not new_path.resolve().is_relative_to(self.site):
                self.error(relative, "generated path points outside the site; refusing to modify or compare it")
                continue
            in_archive = relative.startswith("papers/")
            if old_path.suffix.lower() == ".html":
                before, after = old_path.read_bytes(), new_path.read_bytes()
                if self.preserve_footer_date:
                    restored = restore_footer_date(before, after)
                    if restored != after:
                        new_path.write_bytes(restored)
                        self.restored_footers.append(relative)
                        after = restored
                if self.preserve_notebook_title and NOTEBOOK_PATH.fullmatch(relative):
                    restored = restore_notebook_title(before, after)
                    if restored != after:
                        new_path.write_bytes(restored)
                        self.restored_notebook_titles.append(relative)
                        after = restored
                # The archive index and stable landings can gain new versions.
                if in_archive and not VERSION_HTML.fullmatch(relative):
                    continue
                try:
                    old_page = Page(before.decode("utf-8"))
                    new_page = Page(after.decode("utf-8"))
                except (UnicodeError, ValueError) as exc:
                    self.error(relative, f"cannot parse existing HTML: {exc}")
                    continue
                if VERSION_HTML.fullmatch(relative):
                    self.compare_scholarly_version(relative, old_page, new_page)
                if self.immutable_versions_only:
                    continue
                if not old_page.has_body or not new_page.has_body:
                    if before != after:
                        self.error(relative, "existing HTML fragment changed")
                elif old_page.body != new_page.body:
                    old_body, new_body = old_page.body, new_page.body
                    if self.allow_archive_title_links and relative == "research/index.html":
                        old_body, old_keys = self.without_authorised_title_wrappers(old_page)
                        new_body, new_keys = self.without_authorised_title_wrappers(new_page)
                        if old_body == new_body:
                            self.allowed_title_wrappers.extend(sorted(new_keys - old_keys))
                    if old_body != new_body:
                        self.error(relative, "existing rendered body, attributes, or click targets changed")
                if old_page.head_contract != new_page.head_contract:
                    self.error(relative, "existing head title, links, styles, or scripts changed")
            elif relative not in GENERATED_METADATA:
                if in_archive and not re.fullmatch(r"papers/[^/]+/v[1-9][0-9]*\.(?:pdf|bib)", relative):
                    continue
                if sha256(old_path) != sha256(new_path):
                    self.error(relative, "existing asset bytes changed")

    def without_authorised_title_wrappers(self, page: Page) -> tuple[list[tuple], set[str]]:
        """Remove only the explicitly approved title anchor's two event tokens.

        No title text, child formatting, neighbouring buttons, or other markup is
        removed. Both pages are still compared in full, and the ordinary archive
        checks independently require each opted-in link to exist and be crawlable.
        """
        papers = {}
        for record_path in sorted((self.site / "papers").glob("*/record.json")):
            record = self.read_record(record_path.parent)
            if record and record["paper"].get("link_from_research") is True:
                paper = record["paper"]
                if isinstance(paper.get("bib_key"), str) and isinstance(paper.get("canonical_url"), str):
                    papers[paper["bib_key"]] = paper
        removed: set[int] = set()
        keys: set[str] = set()
        for anchor in page.anchors:
            key = anchor["bib_key"]
            paper = papers.get(key)
            if not paper or anchor["heading"] is None or anchor["heading_tag"] != "h3":
                continue
            attrs = anchor["attrs"]
            href = attrs.get("href")
            if (set(attrs) != {"class", "style", "href"}
                    or attrs.get("class") != "bib-entry__archive-link"
                    or attrs.get("style") != ARCHIVE_TITLE_STYLE
                    or not href or anchor["hidden"]
                    or anchor["heading"].get("id") != "title-" + key
                    or anchor["text"] != text_key(paper.get("title", ""))
                    or urljoin(urljoin(paper["canonical_url"], "../../research/"), href) != paper["canonical_url"]):
                continue
            start, end = anchor["body_start"], anchor["body_end"]
            if (start is not None and end is not None and page.body[end] == ("end", "a")
                    and page.body[start] == ("start", "a", tuple(sorted(attrs.items())))):
                removed.update((start, end))
                keys.add(key)
        return [token for index, token in enumerate(page.body) if index not in removed], keys

    def compare_scholarly_version(self, relative: str, before: Page, after: Page) -> None:
        """Freeze the archived article, not the site's future theme or navigation."""
        if len(before.articles) != 1 or len(after.articles) != 1 or before.articles != after.articles:
            self.error(relative, "immutable version article content or links changed")
        old_citations = {key: values for key, values in before.metadata.items() if key.startswith("citation_")}
        new_citations = {key: values for key, values in after.metadata.items() if key.startswith("citation_")}
        if old_citations != new_citations or before.canonicals != after.canonicals:
            self.error(relative, "immutable version citation metadata or canonical changed")
        try:
            old_json = [article for raw in before.json_ld for article in scholarly_articles(json.loads(raw))]
            new_json = [article for raw in after.json_ld for article in scholarly_articles(json.loads(raw))]
        except (ValueError, TypeError) as exc:
            self.error(relative, f"invalid immutable version JSON-LD: {exc}")
            return
        if len(old_json) != 1 or old_json != new_json:
            self.error(relative, "immutable version ScholarlyArticle JSON-LD changed")

    def check_sitemap(self) -> None:
        sitemap = self.site / "sitemap.xml"
        if not sitemap.is_file():
            self.error("sitemap.xml", "missing sitemap")
            return
        try:
            root = ET.parse(sitemap).getroot()
            self.sitemap_urls = {node.text.strip() for node in root.iter() if node.tag.split("}")[-1] == "loc" and node.text}
        except ET.ParseError as exc:
            self.error("sitemap.xml", f"invalid XML: {exc}")
            return
        for url in sorted(self.sitemap_urls):
            parsed = urlsplit(url)
            route = unquote(parsed.path)
            if self.forbidden(route) or re.search(r"(?:^|/)404(?:\.html|/|$)", route):
                self.error("sitemap.xml", f"forbidden public route: {url}")
            if parsed.scheme not in ("http", "https") or not parsed.netloc:
                self.error("sitemap.xml", f"URL must be absolute: {url}")
            elif self.origin and f"{parsed.scheme}://{parsed.netloc}" != self.origin:
                self.error("sitemap.xml", f"URL uses a different site origin: {url}")
            else:
                target = self.resolve_url(url, url)
                if target and not target.is_file():
                    self.error("sitemap.xml", f"URL does not resolve: {url}")

    def read_record(self, directory: Path) -> dict | None:
        path = directory / "record.json"
        if path not in self.records:
            try:
                record = json.loads(path.read_text(encoding="utf-8"))
                if not isinstance(record, dict) or record.get("schema_version") != 1:
                    raise ValueError("expected a schema_version: 1 object")
                if not isinstance(record.get("paper"), dict) or not isinstance(record.get("versions"), list):
                    raise ValueError("expected paper object and versions list")
                self.records[path] = record
                for entry in [record["paper"]] + record["versions"]:
                    if isinstance(entry, dict) and entry.get("archived_at"):
                        self.check_archive_date(path, entry)
            except (OSError, ValueError) as exc:
                self.error(self.relative(path), f"invalid archive record: {exc}")
                self.records[path] = None
        return self.records[path]

    def check_archive_date(self, path: Path, entry: dict) -> None:
        try:
            stamp = datetime.fromisoformat(str(entry["archived_at"]).replace("Z", "+00:00"))
            if stamp.tzinfo is None:
                raise ValueError("archived_at requires an explicit UTC offset")
            zone = ZoneInfo(str(entry.get("archive_timezone", "")))
            if stamp.astimezone(zone).date().isoformat() != entry.get("archived_on"):
                raise ValueError("archived_on does not match archived_at in archive_timezone")
        except (ValueError, ZoneInfoNotFoundError) as exc:
            self.error(self.relative(path), f"invalid archive date: {exc}")

    def check_pdf(self, path: Path, expected_hash: object) -> None:
        relative = self.relative(path)
        if not path.is_file():
            self.error(relative, "citation PDF is missing")
            return
        if relative not in self.checked_pdfs:
            with path.open("rb") as stream:
                signature = stream.read(8)
            if not re.match(rb"%PDF-[12]\.[0-9]", signature):
                self.error(relative, "does not have a PDF file signature")
            self.checked_pdfs[relative] = {"sha256": sha256(path), "bytes": path.stat().st_size}
            if self._text_extractor:
                try:
                    process = subprocess.run(
                        [self._text_extractor, "-f", "1", "-l", "1", str(path), "-"],
                        capture_output=True, timeout=30, check=False,
                    )
                    if process.returncode == 0:
                        self.checked_pdfs[relative]["first_page_text_characters"] = len(process.stdout.decode("utf-8", errors="replace").strip())
                    else:
                        self.warnings.append(f"{relative}: optional pdftotext extraction was unsuccessful; signature and SHA-256 were checked")
                except (OSError, subprocess.TimeoutExpired):
                    self.warnings.append(f"{relative}: optional pdftotext extraction unavailable; signature and SHA-256 were checked")
        if not isinstance(expected_hash, str) or not re.fullmatch(r"[0-9a-fA-F]{64}", expected_hash):
            self.error(relative, "record does not contain a valid PDF SHA-256")
        elif self.checked_pdfs[relative]["sha256"] != expected_hash.lower():
            self.error(relative, "PDF SHA-256 differs from record.json")

    def check_research_title_link(self, record_path: Path, record: dict) -> None:
        """Validate only explicitly opted-in Research → landing → current PDF paths."""
        paper = record["paper"]
        enabled = paper.get("link_from_research", False)
        if not isinstance(enabled, bool):
            self.error(self.relative(record_path), "link_from_research must be a boolean")
            return
        if not enabled:
            return
        key = paper.get("bib_key")
        if not isinstance(key, str) or not key:
            self.error(self.relative(record_path), "Research title-link opt-in requires a bib_key")
            return
        canonical = paper.get("canonical_url")
        if not isinstance(canonical, str) or not canonical:
            self.error(self.relative(record_path), "Research title-link opt-in requires a canonical URL")
            return
        research_path = self.site / "research/index.html"
        if not research_path.is_file():
            self.error("research/index.html", f"missing Research page for opted-in paper {key}")
            return
        page = self.page(research_path)
        research_url = self.origin + self.base_path + "/research/"
        entries = [attrs for attrs in page.bib_entries if attrs.get("data-paper-key") == key]
        if len(entries) != 1 or entries[0].get("id") != key:
            self.error("research/index.html", f"requires one bibliography entry with matching id/data-paper-key for {key}")
        anchors = [anchor for anchor in page.anchors if anchor["bib_key"] == key and anchor["heading"] is not None]
        if len(anchors) != 1:
            self.error("research/index.html", f"requires exactly one ordinary title anchor for opted-in paper {key}")
            return
        anchor = anchors[0]
        attrs = anchor["attrs"]
        if len(attrs) != len(anchor["raw_attrs"]):
            self.error("research/index.html", f"title link for {key} must not contain duplicate HTML attributes")
        target = urljoin(research_url, attrs.get("href") or "")
        if (not attrs.get("href") or target != paper.get("canonical_url")
                or self.resolve_url(target, research_url) != record_path.parent / "index.html"):
            self.error("research/index.html", f"title link for {key} must target the stable archive landing canonical URL")
        if anchor["text"] != text_key(paper.get("title", "")):
            self.error("research/index.html", f"title link text differs from the archived paper title for {key}")
        if anchor["heading_tag"] != "h3" or anchor["heading"].get("id") != "title-" + key:
            self.error("research/index.html", f"title heading id does not match paper key {key}")
        if anchor["hidden"] or "nofollow" in (attrs.get("rel") or "").lower().split():
            self.error("research/index.html", f"title link for {key} must be visible and crawlable (no hidden/nofollow)")
        robots = ",".join(page.metadata.get("robots", []) + page.metadata.get("googlebot", [])).lower()
        if re.search(r"\b(?:noindex|nofollow|none)\b", robots):
            self.error("research/index.html", "opted-in Research title links are blocked by robots metadata")
        if self.robot_parser:
            for agent in CRAWLERS:
                if not self.robot_parser.can_fetch(agent, research_url):
                    self.error("research/index.html", f"robots.txt blocks Research title-link discovery for {agent}")
        landing = record_path.parent / "index.html"
        current = paper.get("current_version")
        if not isinstance(current, str) or not re.fullmatch(r"v[1-9][0-9]*", current) or paper.get("version_id") != current:
            self.error(self.relative(record_path), "opted-in landing must identify its declared current archive version")
        elif self.resolve_url(str(paper.get("pdf_url", "")), paper["canonical_url"]) != record_path.parent / (current + ".pdf"):
            self.error(self.relative(record_path), "opted-in landing PDF must match its declared current archive version")
        if landing.is_file():
            pdf_links = [link for link in self.page(landing).anchors
                         if link["attrs"].get("href")
                         and len(link["attrs"]) == len(link["raw_attrs"])
                         and urljoin(paper["canonical_url"], link["attrs"]["href"]) == paper.get("pdf_url")
                         and not link["hidden"]
                         and "nofollow" not in (link["attrs"].get("rel") or "").lower().split()]
            if not pdf_links:
                self.error(self.relative(landing), "opted-in landing needs a visible, crawlable ordinary link to the current PDF")
        self.checked_research_links.append(key)

    def check_paper(self, path: Path, page: Page) -> None:
        relative = self.relative(path)
        self.checked_pages.append(relative)
        metadata = page.metadata

        def single(name: str) -> str:
            values = metadata.get(name, [])
            if len(values) != 1 or not values[0].strip():
                self.error(relative, f"requires exactly one nonempty {name}")
                return ""
            return values[0]

        title = single("citation_title")
        date = single("citation_publication_date")
        pdf_url = single("citation_pdf_url")
        authors = [text_key(value) for value in metadata.get("citation_author", [])]
        if not authors or any(not author for author in authors):
            self.error(relative, "requires nonempty citation_author metadata")
        if page.h1 != [text_key(title)]:
            self.error(relative, "visible h1 differs from citation_title")
        if text_key(title) not in text_key("".join(page.title)):
            self.error(relative, "head title does not contain citation_title")
        visible = text_key(" ".join(page.visible_text))
        if page.visible_authors:
            if page.visible_authors != authors:
                self.error(relative, "visible authors differ from citation_author metadata")
        elif any(author not in visible for author in authors):
            self.error(relative, "citation_author does not appear in visible page text")
        if not re.fullmatch(r"[12][0-9]{3}(?:[-/][0-9]{2}(?:[-/][0-9]{2})?)?", date):
            self.error(relative, "citation_publication_date must preserve a real publication year/date")
        if page.visible_years != [date[:4]]:
            self.error(relative, "visible publication year differs from citation metadata")
        if len(page.canonicals) != 1:
            self.error(relative, "requires exactly one canonical URL")
            return
        canonical = page.canonicals[0]
        parsed = urlsplit(canonical)
        if parsed.scheme != "https" or not parsed.netloc or parsed.query or parsed.fragment:
            self.error(relative, "canonical must be an absolute HTTPS URL without query/fragment")
            return
        if self.resolve_url(canonical, canonical) != path:
            self.error(relative, "canonical URL does not match this generated page")
        if canonical not in self.sitemap_urls:
            self.error(relative, "paper landing/version page is absent from sitemap.xml")
        abstract_urls = metadata.get("citation_abstract_html_url", [])
        if len(abstract_urls) != 1 or abstract_urls[0] != canonical:
            self.error(relative, "citation_abstract_html_url must equal the canonical snapshot/landing URL")
        robots = ",".join(metadata.get("robots", []) + metadata.get("googlebot", [])).lower()
        if re.search(r"\b(?:noindex|none)\b", robots):
            self.error(relative, "paper page is blocked by robots metadata")
        if self.robot_parser:
            for agent in CRAWLERS:
                if not self.robot_parser.can_fetch(agent, canonical):
                    self.error(relative, f"robots.txt blocks {agent}")
        self.check_links(path, page, canonical)
        pdf = self.resolve_url(pdf_url, canonical)
        if pdf is None or pdf.parent != path.parent or not re.fullmatch(r"v[1-9][0-9]*\.pdf", pdf.name):
            self.error(relative, "citation PDF must be a same-directory immutable vN.pdf")
            pdf = None
        if pdf and self.robot_parser:
            for agent in CRAWLERS:
                if not self.robot_parser.can_fetch(agent, urljoin(canonical, pdf_url)):
                    self.error(relative, f"robots.txt blocks citation PDF for {agent}")
        record = self.read_record(path.parent)
        entry = None
        if record:
            if path.name == "index.html":
                entry = record["paper"]
            else:
                matches = [item for item in record["versions"] if isinstance(item, dict) and item.get("canonical_url") == canonical]
                if len(matches) != 1:
                    self.error(relative, "record.json does not identify exactly one matching version")
                else:
                    entry = matches[0]
            if isinstance(entry, dict):
                for key, expected in (("title", title), ("year", date[:4]), ("canonical_url", canonical), ("pdf_url", urljoin(canonical, pdf_url))):
                    if text_key(entry.get(key, "")) != text_key(expected):
                        self.error(relative, f"record.json {key} differs from page metadata")
                if author_names(entry.get("authors", [])) != authors:
                    self.error(relative, "record.json authors differ from page metadata")
                if not entry.get("abstract") or page.abstracts != [text_key(entry["abstract"])]:
                    self.error(relative, "full visible abstract differs from record.json")
                if page.hidden_abstract:
                    self.error(relative, "full abstract must be visible without expanding hidden content")
                publication_date = str(entry.get("publication_date", entry.get("year", "")))
                if date.replace("/", "-") != publication_date.replace("/", "-"):
                    self.error(relative, "publication date precision differs from record.json")
                if len(date) > 4 and date == entry.get("archived_on") and date != entry.get("publication_date"):
                    self.error(relative, "archive date is being used as the publication date")
                if path.name != "index.html" and pdf and pdf.stem != path.stem:
                    self.error(relative, "version HTML must cite the identically numbered PDF")
                if pdf and entry.get("version_id") != pdf.stem:
                    self.error(relative, "record version_id does not match the citation PDF version")
                if pdf:
                    self.check_pdf(pdf, entry.get("sha256"))
                bib = self.resolve_url(str(entry.get("bib_url", "")), canonical)
                if not bib or bib.parent != path.parent or not re.fullmatch(r"v[1-9][0-9]*\.bib", bib.name) or not bib.is_file():
                    self.error(relative, "record BibTeX URL must resolve to a same-directory vN.bib")
                elif entry.get("bibtex") is not None and bib.read_text(encoding="utf-8") != entry["bibtex"]:
                    self.error(relative, "BibTeX download differs from record.json")
                if bib and pdf and bib.stem != pdf.stem:
                    self.error(relative, "BibTeX and PDF download version numbers differ")
                if entry.get("record_url"):
                    record_target = self.resolve_url(str(entry["record_url"]), canonical)
                    if record_target != path.parent / "record.json":
                        self.error(relative, "record_url must resolve to the same-directory record.json")
        articles = []
        for raw in page.json_ld:
            try:
                articles.extend(scholarly_articles(json.loads(raw)))
            except (ValueError, TypeError) as exc:
                self.error(relative, f"invalid JSON-LD: {exc}")
        if len(articles) != 1:
            self.error(relative, "requires exactly one ScholarlyArticle JSON-LD object")
        for article in articles:
            if text_key(article.get("headline", article.get("name", ""))) != text_key(title):
                self.error(relative, "JSON-LD title differs from citation_title")
            if author_names(article.get("author", [])) != authors:
                self.error(relative, "JSON-LD authors differ from citation_author metadata")
            if "datePublished" in article and str(article["datePublished"]) != date.replace("/", "-"):
                self.error(relative, "JSON-LD datePublished differs from publication date/precision")
            if article.get("url", article.get("@id")) != canonical:
                self.error(relative, "JSON-LD URL differs from canonical URL")
            if entry and text_key(article.get("abstract", "")) != text_key(entry.get("abstract", "")):
                self.error(relative, "JSON-LD abstract differs from the full archived abstract")
            if entry and "description" in article and text_key(article["description"]) != text_key(entry.get("abstract", "")):
                self.error(relative, "JSON-LD description differs from the full archived abstract")
            encoding = article.get("encoding")
            if not isinstance(encoding, dict) or encoding.get("contentUrl") != urljoin(canonical, pdf_url):
                self.error(relative, "JSON-LD encoding must identify the citation PDF")
            elif entry and encoding.get("sha256") != entry.get("sha256"):
                self.error(relative, "JSON-LD PDF checksum differs from record.json")

    def run(self) -> dict:
        if not self.site.is_dir():
            self.error("site", "generated site directory does not exist")
            return self.report()
        if self.preserve_footer_date and self.baseline is None:
            self.error("baseline", "--preserve-footer-date requires --baseline")
        if self.immutable_versions_only and self.baseline is None:
            self.error("baseline", "--immutable-versions-only requires --baseline")
        if self.preserve_notebook_title and self.baseline is None:
            self.error("baseline", "--preserve-notebook-title requires --baseline")
        if self.allow_archive_title_links and (self.baseline is None or self.immutable_versions_only):
            self.error("baseline", "--allow-archive-title-links requires a strict --baseline comparison")
        self.compare_baseline()
        archive = self.site / "papers"
        paths = sorted(archive.rglob("*.html")) if archive.is_dir() else []
        paper_paths = [path for path in paths if path.parent != archive]
        if not paper_paths:
            self.error("papers", "no generated paper landing/version pages found")
            return self.report()
        if not (archive / "index.html").is_file():
            self.error("papers/index.html", "archive index is missing")
        for directory in sorted({path.parent for path in paper_paths}):
            if not (directory / "index.html").is_file():
                self.error(self.relative(directory), "stable paper landing page is missing")
            if not any(VERSION_HTML.fullmatch(self.relative(path)) for path in directory.glob("*.html")):
                self.error(self.relative(directory), "no immutable version HTML exists")
        for path in paper_paths:
            page = self.page(path)
            if page.canonicals:
                parsed = urlsplit(page.canonicals[0])
                route = "/" + self.relative(path)
                if path.name == "index.html":
                    route = route.removesuffix("index.html")
                if parsed.path.endswith(route):
                    self.origin = f"{parsed.scheme}://{parsed.netloc}"
                    self.base_path = parsed.path[:-len(route)]
                    break
        if self.origin is None:
            self.error("papers", "cannot establish site origin from a canonical paper URL")
            return self.report()
        robots = self.site / "robots.txt"
        if robots.is_file():
            self.robot_parser = RobotFileParser()
            self.robot_parser.parse(robots.read_text(encoding="utf-8").splitlines())
        else:
            self.error("robots.txt", "missing crawl-policy file")
        self.check_sitemap()
        for path in sorted(self.site.rglob("*")):
            if path.is_file() and self.forbidden(self.relative(path)):
                self.error(self.relative(path), "hidden research programme was generated")
            if self.forbid_routes and path.is_file() and path.suffix.lower() == ".html":
                current_url = self.origin + self.base_path + "/" + self.relative(path)
                for href in self.page(path).links:
                    absolute = urlsplit(urljoin(current_url, href))
                    if absolute.netloc == urlsplit(self.origin).netloc and self.forbidden(absolute.path):
                        self.error(self.relative(path), f"link exposes hidden research programme: {href}")
        for path in paths:
            page = self.page(path)
            if path.parent == archive:
                index_url = self.origin + self.base_path + "/papers/"
                self.check_links(path, page, index_url)
                if index_url not in self.sitemap_urls:
                    self.error("papers/index.html", "archive index is absent from sitemap.xml")
                if self.robot_parser:
                    for agent in CRAWLERS:
                        if not self.robot_parser.can_fetch(agent, index_url):
                            self.error("papers/index.html", f"robots.txt blocks {agent}")
                if any(re.search(r"\b(?:noindex|none)\b", value.lower()) for value in page.metadata.get("robots", []) + page.metadata.get("googlebot", [])):
                    self.error("papers/index.html", "archive index is blocked by robots metadata")
            else:
                self.check_paper(path, page)
        # Records must not silently point at absent version pages or extra files.
        for record_path, record in self.records.items():
            if record is None:
                continue
            self.check_research_title_link(record_path, record)
            for item in record["versions"]:
                if not isinstance(item, dict):
                    self.error(self.relative(record_path), "version entries must be objects")
                    continue
                for field in ("canonical_url", "pdf_url", "bib_url"):
                    value = item.get(field, "")
                    target = self.resolve_url(value, self.origin + "/") if isinstance(value, str) else None
                    if not target or target.parent != record_path.parent or not target.is_file():
                        self.error(self.relative(record_path), f"version {field} does not resolve in the paper directory")
        return self.report()

    def report(self) -> dict:
        return {
            "ok": not self.errors,
            "site": str(self.site),
            "baseline": str(self.baseline) if self.baseline else None,
            "immutable_versions_only": self.immutable_versions_only,
            "forbidden_routes": sorted(set(self.forbid_routes)),
            "paper_pages_checked": self.checked_pages,
            "pdfs_checked": self.checked_pdfs,
            "research_title_links_checked": self.checked_research_links,
            "research_title_wrappers_allowed": self.allowed_title_wrappers,
            "footer_dates_restored": self.restored_footers,
            "notebook_titles_restored": self.restored_notebook_titles,
            "errors": self.errors,
            "warnings": self.warnings,
        }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--site", type=Path, default=Path("_site"))
    parser.add_argument("--baseline", type=Path)
    parser.add_argument("--preserve-footer-date", action="store_true")
    parser.add_argument("--preserve-notebook-title", action="store_true",
                        help="restore only exact random Jekyll notebook titles in prior assets/*.ipynb.html")
    parser.add_argument("--allow-archive-title-links", action="store_true",
                        help="with a strict baseline, permit only exact opted-in Research title anchor wrappers")
    parser.add_argument("--immutable-versions-only", action="store_true",
                        help="with a baseline, protect only old version scholarly content and PDF/BibTeX bytes")
    parser.add_argument("--forbid-route", action="append", default=[],
                        help="fail if this route/prefix is generated, linked, or in the sitemap; repeatable")
    parser.add_argument("--report", type=Path, help="write a JSON verification report")
    args = parser.parse_args(argv)
    verifier = Verifier(args.site, args.baseline, args.preserve_footer_date,
                        args.immutable_versions_only, args.forbid_route, args.preserve_notebook_title,
                        args.allow_archive_title_links)
    try:
        report = verifier.run()
    except (OSError, UnicodeError, ValueError, TypeError) as exc:
        verifier.error("verification", f"cannot complete verification: {exc}")
        report = verifier.report()
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    for error in report["errors"]:
        print(f"ERROR: {error}", file=sys.stderr)
    for warning in report["warnings"]:
        print(f"WARNING: {warning}", file=sys.stderr)
    if report["ok"]:
        print(f"Archive verified: {len(report['paper_pages_checked'])} paper pages, {len(report['pdfs_checked'])} PDFs; {len(report['footer_dates_restored'])} footer dates and {len(report['notebook_titles_restored'])} notebook titles preserved.")
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
