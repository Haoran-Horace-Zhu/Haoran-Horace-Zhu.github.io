---
layout: page
permalink: /research/current/
title: Current Research
description: An evolving account of the themes, projects, and questions that currently shape my work.
nav: false
show_ongoing_projects: false
show_notes_and_perspectives: false
---

<nav class="current-research-index" aria-label="On this page">
  <span class="current-research-index__label">On this page</span>
  <a href="#current-themes">Current themes</a>
  {% if page.show_ongoing_projects %}<a href="#ongoing-projects">Ongoing projects</a>{% endif %}
  <a href="#broader-interests">Broader interests</a>
  {% if page.show_notes_and_perspectives %}<a href="#notes-and-perspectives">Notes and perspectives</a>{% endif %}
</nav>

<section id="current-themes" class="current-research-section">
  <span class="current-research-section__number" aria-hidden="true">01</span>
  <div>
    <span class="academic-overview__eyebrow">Research landscape</span>
    <h2>Current Themes</h2>
    <div class="current-research-theme-grid">
      <article>
        <h3>Combinatorics</h3>
        <p>Cayley graphs, asymptotic representation theory, symmetric functions, quantum determinants, quadratic forms, and harmonic analysis on infinite symmetric groups.</p>
      </article>
      <article>
        <h3>Probability Theory</h3>
        <p>Markov chains, random walks, random partitions, and random matrices.</p>
      </article>
      <article>
        <h3>Mathematical Physics</h3>
        <p>Vertex-operator calculus, integrable systems, the boson–fermion correspondence, and quantum information.</p>
      </article>
    </div>
  </div>
</section>

{% if page.show_ongoing_projects %}

  <section id="ongoing-projects" class="current-research-section">
    <span class="current-research-section__number" aria-hidden="true">02</span>
    <div>
      <span class="academic-overview__eyebrow">Work in progress</span>
      <h2>Ongoing Projects</h2>
      <p>Project descriptions will be added here.</p>
    </div>
  </section>
{% endif %}

<section id="broader-interests" class="current-research-section">
  <span class="current-research-section__number" aria-hidden="true">{% if page.show_ongoing_projects %}03{% else %}02{% endif %}</span>
  <div>
    <span class="academic-overview__eyebrow">Beyond current projects</span>
    <h2>Broader Research Interests</h2>
    <p>Lie algebras, arithmetic schemes, hypermatrices, and the Hurwitz composition problem.</p>
  </div>
</section>

{% if page.show_notes_and_perspectives %}

  <section id="notes-and-perspectives" class="current-research-section">
    <span class="current-research-section__number" aria-hidden="true">{% if page.show_ongoing_projects %}04{% else %}03{% endif %}</span>
    <div>
      <span class="academic-overview__eyebrow">Developing ideas</span>
      <h2>Notes and Perspectives</h2>
      <p>Notes and perspectives will be added here.</p>
    </div>
  </section>
{% endif %}
