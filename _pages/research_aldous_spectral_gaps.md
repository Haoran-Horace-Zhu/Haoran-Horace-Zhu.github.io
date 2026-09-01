---
layout: page
permalink: /research/current/spectral-gap-problems/
title: Spectral Gap Problems
nav: false
---

<a class="research-topic-back" href="{{ '/research/current/' | relative_url }}">&larr; Current Research</a>

<div class="research-note" markdown="1">

**Aldous spectral gap conjecture.** Let $\Gamma$ be a finite connected weighted graph on $n$ vertices. A continuous-time random walk follows one particle as it moves across the edges of $\Gamma$. In the **interchange process**, the vertices carry $n$ distinct labels and the two labels at the ends of an edge are exchanged at that edge's rate. The random walk has $n$ states, whereas the interchange process has $n!$ states.

Following any single label projects the interchange process onto the original random walk. Consequently,

$$
\operatorname{gap}(\operatorname{IP}(\Gamma)) \leq \operatorname{gap}(\operatorname{RW}(\Gamma)).
$$

David Aldous's conjecture, which arose around 1992 and was later recorded in the Aldous–Fill monograph, asserted that equality holds for every finite weighted graph. Handjani and Jungreis proved the weighted-tree case in 1996. The full conjecture was proved by Caputo, Liggett and Richthammer in 2010 through a recursive argument combining electrical-network reduction with the **Octopus Inequality**.

There is an equivalent representation-theoretic formulation. A weighted graph on $[n]$ determines a weighted set of transpositions in $\mathfrak{S}_n$. The conjecture says that the spectral gap of the resulting Cayley walk on $\mathfrak{S}_n$ is already visible in its natural action on $[n]$—or, after removing the trivial summand, in the standard representation indexed by $(n-1,1)$. Thus an operator on $n!$ states has its first non-trivial eigenvalue detected in dimension $n-1$.

**Aldous-type spectral gaps on arbitrary groups.** The classical theorem suggests a broader spectral question: when is the first non-trivial eigenvalue of a large walk already detected by a canonical smaller representation or Schreier quotient? For the type-$B$ Weyl group $W(B_n)$, Cesi proved an Aldous-type result for a structured class of weighted generators, with the gap detected by a $2n$-dimensional permutation representation. More recent work studies generalised symmetric groups $G\wr\mathfrak{S}_n$, where $G$ is a finite group. Analogous questions can also be posed for compact groups such as $\mathrm{U}(n)$, where the comparison process is related to discrete KMP or uniform-reshuffling dynamics.

**Aldous-type spectral gaps for other connection sets.** Even within $\mathfrak{S}_n$, the transpositions may be replaced by other connection sets. For normal sets, unions of conjugacy classes and sets of cycles, one asks whether the strictly second-largest eigenvalue is still attained by the standard representation—the property now commonly called the **Aldous property**. Work of Parzanchevski and Puder, together with the systematic treatment in Yuxuan Li's thesis, shows that the answer is delicate: many cycle-generated families have the property, while others do not.

This direction also includes non-normal examples. In joint work with Gary Greaves, I proved that the full-flag Johnson graph $\operatorname{FJ}(n,2)$ has the Aldous property: its spectral gap is equal to that of the Schreier quotient arising from a point stabiliser.

The interaction itself may also change. On a hypergraph, a local update can reshuffle several labels at once rather than exchange a pair. Caputo's hypergraph extension asks whether an appropriate low-particle process continues to determine the gap. Alon, Kozma and Puder generalised the Octopus Inequality and proved the conjecture for several non-trivial families of hypergraphs. In each of these settings, the common spectral issue is whether a comparatively small part of the representation theory captures the first obstruction to relaxation.

<hr class="research-note__divider" aria-hidden="true">

**Fill spectral gap conjecture.** A different spectral problem appears when an adjacent-transposition chain is no longer symmetric. In unpublished notes written in 2003—later posted essentially unchanged on arXiv—James Allen Fill considered a Markov chain on $\mathfrak{S}_n$ with label-dependent probabilities $p_{i,j}$, where $p_{i,j}+p_{j,i}=1$. From a permutation, the chain chooses a pair of adjacent positions uniformly and either orders their two labels according to these probabilities or stays in place.

Fill's motivation came from the **move-ahead-one** rule for self-organising linear-search lists. Frequently requested records should gradually move towards the front of a list, but the resulting bias makes the convergence analysis substantially harder. The chain nevertheless remains reversible with a natural stationary distribution, making it a useful model for both relaxation and sampling.

For a regular parameter vector $\mathbf{p}$—roughly, one whose biases consistently favour a common order—Fill conjectured that the unbiased chain is a minimiser of the spectral gap:

$$
\lambda_K(\mathbf{p}) \geq \lambda_K(\mathbf{p}_{\mathrm{unif}})
= \frac{1-\cos(\pi/n)}{n-1},
\qquad p^{\mathrm{unif}}_{i,j}=\frac12.
$$

Where Aldous compares a symmetric many-particle process with its one-particle projection, Fill asks for the extremal gap across a family of biased adjacent-transposition chains. The local bias removes much of the symmetry available in the interchange process, so a different mechanism is required.

In joint work with Gary Greaves, I proved a sharp lower bound for arbitrary bias and resolved Fill's conjecture for every regular parameter vector. We also characterised the equality cases: the minimum is attained precisely when there is a **neutral label** $c$, meaning that $p_{c,i}=1/2$ for every $i\neq c$. Hence the uniform chain is a minimiser, but not the unique one. We further determined the multiplicity of the corresponding second-largest eigenvalue.

### References

<ol class="research-references">
  <li>
    D. Aldous and J. A. Fill, <a href="https://www.stat.berkeley.edu/~aldous/RWG/book.html"><em>Reversible Markov Chains and Random Walks on Graphs</em></a>, unfinished monograph (2002; recompiled 2014), Open Problem 14.29.
  </li>
  <li>
    G. Alon, G. Kozma and D. Puder, <a href="https://doi.org/10.1017/S0305004125000179">“On the Aldous–Caputo spectral gap conjecture for hypergraphs”</a>, <em>Mathematical Proceedings of the Cambridge Philosophical Society</em> 179 (2025), 259–298.
  </li>
  <li>
    G. Alon and D. Puder, <a href="https://arxiv.org/abs/2603.00353">“Aldous-type spectral gaps in unitary groups”</a>, arXiv:2603.00353 (2026).
  </li>
  <li>
    P. Caputo, T. M. Liggett and T. Richthammer, <a href="https://doi.org/10.1090/S0894-0347-10-00659-4">“Proof of Aldous' spectral gap conjecture”</a>, <em>Journal of the American Mathematical Society</em> 23 (2010), 831–851.
  </li>
  <li>
    F. Cesi, <a href="https://doi.org/10.1016/j.laa.2019.10.024">“On the spectral gap of some Cayley graphs on the Weyl group $W(B_n)$”</a>, <em>Linear Algebra and its Applications</em> 586 (2020), 274–295.
  </li>
  <li>
    J. A. Fill, <a href="https://arxiv.org/abs/2508.12557"><em>An Interesting Spectral Gap Problem, from Jim Fill</em></a>, unpublished notes (2003), posted as arXiv:2508.12557 (2025).
  </li>
  <li>
    G. Greaves and H. Zhu, <a href="https://arxiv.org/abs/2603.10406">“Aldous property for full-flag Johnson graphs”</a>, arXiv:2603.10406 (2026).
  </li>
  <li>
    G. Greaves and H. Zhu, <a href="https://arxiv.org/abs/2603.26303">“Spectral gap of biased adjacent-transposition chains”</a>, arXiv:2603.26303 (2026).
  </li>
  <li>
    S. Handjani and D. Jungreis, <a href="https://doi.org/10.1007/BF02214260">“Rate of convergence for shuffling cards by transpositions”</a>, <em>Journal of Theoretical Probability</em> 9 (1996), 983–993.
  </li>
  <li>
    N. Levhari and D. Puder, <a href="https://arxiv.org/abs/2605.22101">“Aldous-type spectral gaps in generalized symmetric groups”</a>, arXiv:2605.22101 (2026).
  </li>
  <li>
    Y. Li, <a href="https://hdl.handle.net/11343/354742"><em>The Second Largest Eigenvalue of Cayley Graphs on Symmetric Groups</em></a>, PhD thesis, The University of Melbourne, 2024.
  </li>
  <li>
    O. Parzanchevski and D. Puder, <a href="https://doi.org/10.1090/tran/8155">“Aldous's spectral gap conjecture for normal sets”</a>, <em>Transactions of the American Mathematical Society</em> 373 (2020), 7067–7086.
  </li>
</ol>

</div>
