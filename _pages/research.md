---
layout: page
permalink: /research/
title: Research
description: Publications and preprints in combinatorics, probability, algebra, and mathematical physics.
hide_description: true
nav: true
nav_order: 2
---

<section class="research-overview" aria-label="Research interests">
  <p class="research-overview__intro">My research connects combinatorics with probability theory and mathematical physics.</p>
  {% comment %}Temporarily hidden for the October conference; restore alongside the programme pages in _config.yml.{% endcomment %}
  {% if site.research_programmes_visible %}
    <p class="research-overview__programme"><a href="{{ '/research/current/' | relative_url }}">Explore my research programmes</a></p>
  {% endif %}

<div class="research-themes">
  <details class="research-theme">
    <summary>
      <span>Combinatorics</span>
      <span class="research-theme__toggle" aria-hidden="true"></span>
    </summary>
    <p>Cayley graphs, symmetric functions, quantum determinants, quadratic forms, and association schemes.</p>
  </details>

  <details class="research-theme">
    <summary>
      <span>Probability Theory</span>
      <span class="research-theme__toggle" aria-hidden="true"></span>
    </summary>
    <p>Markov chains, random walks, random partitions, random matrices, and cutoff phenomena.</p>
  </details>

  <details class="research-theme">
    <summary>
      <span>Mathematical Physics</span>
      <span class="research-theme__toggle" aria-hidden="true"></span>
    </summary>
    <p>Vertex-operator calculus, integrable systems, and the boson–fermion correspondence.</p>
  </details>
</div>

<details class="research-other-interests">
  <summary><span>Other interests</span><span class="research-theme__toggle" aria-hidden="true"></span></summary>
  <p>Lie algebras, arithmetic schemes, hypermatrices, the Hurwitz composition problem, and quantum information.</p>
</details>
</section>

<div class="research-bibliography">
<section id="publications" aria-labelledby="publications-heading">
  <header class="research-bibliography__heading">
    <h2 id="publications-heading">Publications</h2>
    <span class="research-bibliography__note">Published and forthcoming</span>
  </header>
  <div class="research-bibliography__list">
    {% bibliography --template bib_research --query @*[entry_kind=publication] %}
  </div>
</section>

<details id="preprints" class="research-preprints">
  <summary>
    <h2 class="research-preprints__label">Preprints</h2>
    <span class="research-preprints__control" aria-hidden="true"><span class="research-preprints__show">Show</span><span class="research-preprints__hide">Hide</span><span class="research-preprints__chevron"></span></span>
  </summary>
  <div class="research-bibliography__list">
    {% bibliography --template bib_research --query @*[entry_kind=preprint] %}
  </div>
</details>

<section id="thesis" class="research-thesis" aria-labelledby="thesis-heading">
  <h2 id="thesis-heading">Thesis</h2>
  <div class="research-bibliography__list">
    {% bibliography --template bib_research --group_by none --query @*[entry_kind=thesis] %}
  </div>
</section>

<p class="research-bibliography__profiles"><a href="https://arxiv.org/a/zhu_h_7.html">arXiv</a><span aria-hidden="true"> · </span><a href="https://scholar.google.com/citations?user=BB5H9Z0AAAAJ">Google Scholar</a></p>
</div>

<link rel="stylesheet" href="{{ '/assets/css/research-bibliography.css' | relative_url }}">
<script defer src="{{ '/assets/js/research-bibliography.js' | relative_url }}"></script>
