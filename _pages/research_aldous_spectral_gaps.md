---
layout: page
permalink: /research/current/spectral-gap-problems/
title: Spectral Gap Problems
nav: false
---

<a class="research-topic-back" href="{{ '/research/current/' | relative_url }}">&larr; Research Programmes</a>

<div class="research-note" markdown="1">

<p class="research-note__intro">
  Spectral gaps are central to many questions in graph theory, probability theory, and quantum information theory. This page gives a short account of several problems I have been thinking about and some work related to them.
</p>

### Contents

<nav class="research-note__contents" aria-label="Contents">
  <ul>
    <li>
      <a href="#aldous-spectral-gap-conjecture">Aldous spectral gap conjecture</a>
      <ul>
        <li><a href="#the-octopus-inequality">The Octopus inequality</a></li>
        <li>
          <a href="#aldous-type-spectral-gaps-on-other-groups">Aldous-type spectral gaps on other groups</a>
          <ul>
            <li><a href="#group-valued-coloured-interchange-processes">Group-valued coloured interchange processes</a></li>
          </ul>
        </li>
        <li>
          <a href="#aldous-type-spectral-gaps-for-other-sets">Aldous-type spectral gaps for other sets</a>
          <ul>
            <li><a href="#full-flag-johnson-graphs">Full-flag Johnson graphs</a></li>
          </ul>
        </li>
      </ul>
    </li>
    <li><a href="#alpha-shuffle-spectral-gap-conjecture">$\alpha$-shuffle spectral gap conjecture</a></li>
    <li><a href="#fill-spectral-gap-conjecture">Fill spectral gap conjecture</a></li>
    <li>
      <a href="#spectral-gaps-in-random-quantum-circuits">Spectral gaps in random quantum circuits</a>
      <ul>
        <li>
          <a href="#iswap-and-optimal-quantum-mixing">iSWAP and optimal quantum mixing</a>
          <ul>
            <li><a href="#complete-graph-equality">A complete-graph equality</a></li>
            <li><a href="#optimality-on-arbitrary-graphs">Optimality on arbitrary graphs</a></li>
          </ul>
        </li>
      </ul>
    </li>
    <li>
      <a href="#other-spectral-questions">Other spectral questions</a>
      <ul class="research-note__contents-tertiary">
        <li><a href="#generalised-pancake-graphs">Generalised pancake graphs</a></li>
        <li><a href="#haemers-toughness-conjecture">Haemers' toughness conjecture</a></li>
      </ul>
    </li>
  </ul>
</nav>

## Aldous spectral gap conjecture

Let $\Gamma$ be a finite connected weighted graph on $n$ vertices. In a continuous-time random walk, a particle moves along the edges of $\Gamma$. In the _interchange process_, each vertex instead carries a distinct label. Each edge rings at its assigned rate, and when it does, the labels at its two ends are exchanged. The random walk has $n$ states, while the interchange process has $n!$ states.

If we follow any one label in the interchange process, we recover the original random walk. It follows that

$$
\operatorname{gap}(\operatorname{IP}(\Gamma))
\leq
\operatorname{gap}(\operatorname{RW}(\Gamma)).
$$

Aldous conjectured around 1992 that this inequality is always an equality. The conjecture was later recorded by Aldous and Fill. Handjani and Jungreis proved it for weighted trees. Caputo, Liggett and Richthammer subsequently proved it for every finite weighted graph, using electrical-network reductions together with the _Octopus Inequality_.

The result also has a representation-theoretic interpretation. A weighted graph on $[n]$ gives a weighted collection of transpositions in $\mathfrak{S}&#95;{n}$, and the spectral gap of the resulting walk can be read from the natural action of $\mathfrak{S}&#95;{n}$ on $[n]$. Removing the constant functions from this action leaves the standard representation indexed by $(n-1,1)$. Thus a walk on $n!$ permutations has its first non-trivial eigenvalue in a representation of dimension $n-1$.

### The Octopus inequality

The key step in Caputo, Liggett and Richthammer's proof appears when they remove a vertex $x$ from the graph. As in electrical-network reduction, the edges incident with $x$ are replaced by effective edges between its neighbours, with conductances

$$
\frac{c_{xy}c_{xz}}{\sum_{w\neq x}c_{xw}}.
$$

For the _interchange process_, the _Octopus inequality_ says that the energy of these new interactions is dominated by the energy carried by the original star at $x$. This is what allows the induction to pass from $n$ vertices to $n-1$. The name came from the pictures drawn during the proof: the edges around $x$ looked like tentacles.

The inequality gave exactly the estimate that the proof needed, but did not explain why the corresponding self-adjoint element of $\mathbb{C}[\mathfrak{S}&#95;{n}]$, with both positive and negative coefficients, should be positive semidefinite. Caputo and Aldous later asked whether a more illuminating explanation might come from another area of mathematics.

In recent work, I found such a connection through the universal Plücker coordinates introduced by Karp and Purbhoo in their solution of the inverse Wronski problem. I determined exactly how far their positivity survives when one parameter is negative: the threshold is governed by the largest Plancherel up-transition probability. At the critical boundary $\sum&#95;{a}u&#95;{a}^{-1}=0$, the first Plücker relation writes the normalised coordinate indexed by $(2,2)$ as $\omega^2\mathbf{1}-\mathcal{T}^2$, and its positivity is equivalent to the _Octopus inequality_. Thus the central comparison in Aldous' conjecture becomes a critical case of positivity in real Schubert calculus. The same point of view also gives Plücker-theoretic proofs of two hypergraph extensions.

### Aldous-type spectral gaps on other groups

One can ask the same question after replacing $\mathfrak{S}&#95;{n}$ with another group: in which natural representation does the first non-trivial eigenvalue occur? Cesi proved such a result for a class of weighted walks on the type-$B$ Weyl group $W(B_n)$, where the relevant representation has dimension $2n$. Levhari and Puder proved a corresponding result for the generalised symmetric groups $G\wr\mathfrak{S}&#95;{n}$, with $G$ an arbitrary finite group. There is also a continuous analogue: Alon and Puder related the corresponding question for random walks on $\mathrm{U}(n)$ to discrete KMP processes, also known as uniform-reshuffling processes.

<span id="group-valued-coloured-interchange-processes" class="research-note__anchor" aria-hidden="true"></span>
**Group-valued coloured interchange processes.** These questions also arise when the labels carry group-valued colours. In recent work, I introduced random walks on the wreath product $G\wr\mathfrak{S}&#95;{n}$ generated by transpositions together with arbitrary symmetric transitions in the base group $G^n$. I showed that their spectral gaps are determined by the lifted standard representation and the spherical irreducible representations in the associated quasi-regular representation. For abelian $G$, these representations admit a multislice model, and their Laplacians become discrete Schrödinger operators. I also classified the minimal families of irreducible representations that determine the gap for every choice of transition rates.

### Aldous-type spectral gaps for other sets

Another variation is to keep $\mathfrak{S}&#95;{n}$ fixed and replace the transpositions by a different connection set. The question is whether the spectral gap is still attained in the standard representation. A connection set with this property is said to have the _Aldous property_. Parzanchevski and Puder proved comparison results for full conjugacy classes, while also showing that the same statement does not hold for every normal connection set. Li studied many families generated by cycles and found examples both with and without the Aldous property.

<span id="full-flag-johnson-graphs" class="research-note__anchor" aria-hidden="true"></span>
**Full-flag Johnson graphs.** Gary Greaves and I considered a non-normal example, the full-flag Johnson graph $\operatorname{FJ}(n,2)$. For $n\geq4$, its spectral gap agrees with that of the Schreier quotient associated with its point-stabiliser equitable partition. More generally, I conjecture that $\operatorname{FJ}(n,k)$ has the Aldous property for every $3\leq k<n$.

### References

<ol class="research-references">
  <li>D. Aldous, P. Caputo, R. Durrett, A. E. Holroyd, P. Jung and A. L. Puha, <em>The life and mathematical legacy of Thomas M. Liggett</em>, Notices of the American Mathematical Society 68 (2021), 67–79.</li>
  <li>D. Aldous and J. A. Fill, <em>Reversible Markov Chains and Random Walks on Graphs</em>, unfinished monograph (2002; recompiled 2014), Open Problem 14.29.</li>
  <li>G. Alon, G. Kozma and D. Puder, <em>On the Aldous–Caputo spectral gap conjecture for hypergraphs</em>, Mathematical Proceedings of the Cambridge Philosophical Society 179 (2025), 259–298.</li>
  <li>G. Alon and D. Puder, <em>Aldous-type spectral gaps in unitary groups</em>, arXiv:2603.00353 (2026).</li>
  <li>P. Caputo, T. M. Liggett and T. Richthammer, <em>Proof of Aldous' spectral gap conjecture</em>, Journal of the American Mathematical Society 23 (2010), 831–851.</li>
  <li>F. Cesi, <em>On the spectral gap of some Cayley graphs on the Weyl group $W(B_n)$</em>, Linear Algebra and its Applications 586 (2020), 274–295.</li>
  <li>G. Greaves and H. Zhu, <em>Aldous property for full-flag Johnson graphs</em>, arXiv:2603.10406 (2026).</li>
  <li>S. Handjani and D. Jungreis, <em>Rate of convergence for shuffling cards by transpositions</em>, Journal of Theoretical Probability 9 (1996), 983–993.</li>
  <li>S. N. Karp and K. Purbhoo, <em>Universal Plücker coordinates for the Wronski map and positivity in real Schubert calculus</em>, Journal of the American Mathematical Society, to appear; arXiv:2309.04645.</li>
  <li>N. Levhari and D. Puder, <em>Aldous-type spectral gaps in generalized symmetric groups</em>, arXiv:2605.22101 (2026).</li>
  <li>Y. Li, <em>The Second Largest Eigenvalue of Cayley Graphs on Symmetric Groups</em>, PhD thesis, The University of Melbourne, 2024.</li>
  <li>O. Parzanchevski and D. Puder, <em>Aldous's spectral gap conjecture for normal sets</em>, Transactions of the American Mathematical Society 373 (2020), 7067–7086.</li>
  <li>H. Zhu, <em>Random walks on wreath products and spectral gaps for coloured interchange processes</em>, arXiv:2608.20613 (2026).</li>
  <li>H. Zhu, <em>Universal Plücker positivity and the Octopus inequality</em>, arXiv:2609.03746 (2026).</li>
</ol>

<hr class="research-note__divider" aria-hidden="true">

## $\alpha$-shuffle spectral gap conjecture

Transpositions are not the only possible local moves. On a hypergraph, one may instead reshuffle all the labels in a chosen subset. Let $V=[n]$ and assign a non-negative rate $\alpha_A$ to each subset $A\subseteq V$. In the _$\alpha$-shuffle process_, at rate $\alpha_A$, the labels occupying $A$ are permuted uniformly at random.

If we follow a single label, we obtain a continuous-time random walk on $V$ with jump rates

$$
c_\alpha(i,j)
=
\sum_{A\subseteq V:\,i,j\in A}
\frac{\alpha_A}{|A|}
\qquad (i\neq j).
$$

As before, this gives

$$
\operatorname{gap}(\alpha\text{-shuffle})
\leq
\operatorname{gap}(\operatorname{RW}(V,c_\alpha)).
$$

Caputo conjectured that equality holds for every choice of non-negative weights $\alpha_A$. This is the _$\alpha$-shuffle spectral gap conjecture_, also known as the _Aldous–Caputo spectral gap conjecture_. The ordinary _interchange process_ is recovered by taking $\alpha_A=0$ unless $\lvert A\rvert=2$. Bristiel and Caputo proved the mean-field case. Alon, Kozma and Puder later extended the _Octopus Inequality_ and proved the conjecture for several other families of hypergraphs.

### References

<ol class="research-references">
  <li>G. Alon, G. Kozma and D. Puder, <em>On the Aldous–Caputo spectral gap conjecture for hypergraphs</em>, Mathematical Proceedings of the Cambridge Philosophical Society 179 (2025), 259–298.</li>
  <li>A. Bristiel and P. Caputo, <em>Entropy inequalities for random walks and permutations</em>, Annales de l’Institut Henri Poincaré, Probabilités et Statistiques 60 (2024), 54–81.</li>
</ol>

<hr class="research-note__divider" aria-hidden="true">

## Fill spectral gap conjecture

Fill's Gap Problem concerns a biased version of the adjacent-transposition shuffle. In notes written in 2003, motivated by the _move-ahead-one_ rule for self-organising lists, he asked whether the uniform chain minimises the spectral gap among all regular choices of the bias parameters. The notes circulated for more than twenty years before they were posted on arXiv in 2025. Gheissari, Lee and Vigoda describe this as ‘well-known and long-standing’.

For distinct labels $i$ and $j$, choose parameters satisfying

$$
0<p_{i,j}<1,
\qquad
p_{i,j}+p_{j,i}=1.
$$

From a permutation $x=(x_1,\ldots,x_n)$, choose $r\in\{1,\ldots,n-1\}$ uniformly. The chain keeps $x_r$ immediately to the left of $x_{r+1}$ with probability $p_{x_r,x_{r+1}}$, and reverses their order with probability $p_{x_{r+1},x_r}$. It is reversible, with stationary distribution

$$
\pi(x)
=
Z^{-1}
\prod_{1\leq r<s\leq n}p_{x_r,x_s},
$$

where $Z$ is the normalising constant.

Fill called the parameter vector $\mathbf{p}$ _regular_ if

$$
\begin{aligned}
p_{i-1,i} &\geq \frac12
&& (2\leq i\leq n),\\
p_{i-1,j} &\geq p_{i,j}
&& (2\leq i<j\leq n),\\
p_{i,j+1} &\geq p_{i,j}
&& (1\leq i<j\leq n-1).
\end{aligned}
$$

Writing $\lambda_K=1-\beta_K$ for the spectral gap of the transition matrix, Fill conjectured that every regular vector satisfies

$$
\lambda_K(\mathbf{p})
\geq
\lambda_K(\mathbf{p}_{\mathrm{unif}})
=
\frac{1-\cos(\pi/n)}{n-1},
\qquad
p^{\mathrm{unif}}_{i,j}=\frac12.
$$

In other words, a regular bias should not reduce the spectral gap below that of the unbiased adjacent-transposition chain. Unlike Aldous's conjecture, which compares an _interchange process_ with its associated one-particle random walk, Fill's problem compares different biases within the same family of chains.

Gary Greaves and I proved the following lower bound for every probability vector on $n\geq3$ labels:

$$
\lambda_K(\mathbf{p})
\geq
\frac{1-2m_{\mathbf{p}}\cos(\pi/n)}{n-1},
\qquad
m_{\mathbf{p}}
=
\max_{1\leq i<j<k\leq n}
\sqrt{
  p_{i,j}p_{j,k}p_{k,i}
  +
  p_{k,j}p_{j,i}p_{i,k}
}.
$$

For a regular vector, $m_{\mathbf{p}}\leq 1/2$, so Fill's inequality follows. Equality with the uniform gap holds if and only if there is some $c\in[n]$ such that $p_{c,i}=1/2$ for every $i\neq c$. Thus the uniform chain is a minimiser, but not the only one. For the regular chains attaining this minimum, we also determined the multiplicity of the corresponding second-largest eigenvalue.

### References

<ol class="research-references">
  <li>J. A. Fill, <em>An interesting spectral gap problem, from Jim Fill</em>, unpublished notes (2003), posted as arXiv:2508.12557 (2025).</li>
  <li>R. Gheissari, H. Lee and E. Vigoda, <em>Mixing of general biased adjacent transposition chains</em>, Proceedings of the 58th Annual ACM Symposium on Theory of Computing (STOC 2026), 1236–1241.</li>
  <li>G. Greaves and H. Zhu, <em>Spectral gap of biased adjacent-transposition chains</em>, arXiv:2603.26303 (2026).</li>
</ol>

<hr class="research-note__divider" aria-hidden="true">

## Spectral gaps in random quantum circuits

Local random quantum circuits build global randomness from repeated two-qubit gates. At second-moment order, the rate of convergence towards Haar randomness is governed by the spectral gap of a moment operator: a larger gap means faster convergence towards a unitary $2$-design.

### iSWAP and optimal quantum mixing

This turns the choice of gate into a spectral optimisation problem. For a fixed interaction graph, which two-qubit gate gives the largest gap? Work of Kong, Li and Liu pointed to the ironed iSWAP gadget and led to two closely related conjectures.

<span id="complete-graph-equality" class="research-note__anchor" aria-hidden="true"></span>
**A complete-graph equality.** In joint work with Yanying Liang, we first considered ironed two-qubit gadgets on the complete graph $K&#95;{n}$. We proved that, for $n\geq5$, every gadget with KAK-derived parameter $a=5/9$ has the same second-moment spectral gap as iSWAP:

$$
\Delta\!\left(T^{\mathrm{IG}}_{2,K_n}\right)
=
\Delta\!\left(T^{\mathrm{iSWAP}}_{2,K_n}\right).
$$

This includes the iSWAP, $B$-gate and CNOT families. The complete graph has enough symmetry for Schur–Weyl duality to split the relevant operator into total-spin sectors. The main point is that the eigenvalue controlling the gap always occurs in the highest-spin sector. Once this is known, the remaining KAK parameter no longer affects the gap.

<span id="optimality-on-arbitrary-graphs" class="research-note__anchor" aria-hidden="true"></span>
**Optimality on arbitrary graphs.** The complete-graph symmetry disappears for a general interaction graph. In companion work, we proved that on every connected graph with at least three vertices, the ironed iSWAP ensemble maximises the second-moment spectral gap among all two-local unitary circuit ensembles whose moment operator is Hermitian. The gate distribution may even vary from one edge to another. In symbols,

$$
\Delta\!\left(T^{\mathcal E}_{2,G}\right)
\leq
\Delta\!\left(T^{\mathrm{iSWAP}}_{2,G}\right).
$$

Here the proof takes a different route. Local Haar compression reduces the comparison to a four-dimensional space, and an invariant cone of asymmetric four-point inequalities produces a Perron–Frobenius comparison certificate. Together, the two results give complementary answers: a whole family of gates matches iSWAP on the complete graph, while no Hermitian two-local ensemble can surpass it on any connected interaction graph.

### References

<ol class="research-references">
  <li>L. Kong, Z. Li and Z.-W. Liu, <em>Convergence efficiency of quantum gates and circuits</em>, arXiv:2411.04898 (2024).</li>
  <li>Y. Liang and H. Zhu, <em>iSWAP maximises the second-moment spectral gap in random quantum circuits</em>, arXiv:2607.29551 (2026).</li>
  <li>Y. Liang and H. Zhu, <em>Spectral gaps of ironed two-qubit gadgets matching the iSWAP gap</em>, arXiv:2607.28521 (2026).</li>
</ol>

<hr class="research-note__divider" aria-hidden="true">

## Other spectral questions

<span id="generalised-pancake-graphs" class="research-note__anchor" aria-hidden="true"></span>
**Generalised pancake graphs.** Pancake graphs encode the problem of sorting a stack by prefix reversals. Motivated by questions of Blanco and Buehrle, Gary Greaves and I proved that the spectral gap is below $2$ for generalised pancake graphs and below $1$ in the burnt case, and gave lower bounds for certain integer-eigenvalue multiplicities. The main idea of our proof is simply to find the right ordering of the parts in an equitable partition. Behind it is a spectral observation that we did not state separately in the paper: the Schreier spectrum from the natural action of $\mathfrak{S}&#95;{n}$ sits inside the hyperoctahedral Schreier spectrum, and, when $m$ is even, twice the latter sits inside the corresponding spectrum for $\mathbb{Z}&#95;{m}\wr\mathfrak{S}&#95;{n}$. Since these Schreier graphs are quotients of the pancake graphs, the same eigenvalues occur in the corresponding pancake graphs.

<span id="haemers-toughness-conjecture" class="research-note__anchor" aria-hidden="true"></span>
**Haemers' toughness conjecture.** Toughness compares the number of removed vertices with the number of components left behind. Haemers conjectured that a connected graph $\Gamma$ with minimum degree $\delta$ and Laplacian eigenvalues $0=\mu_1<\mu_2\leq\cdots\leq\mu_n$ satisfies

$$
t(\Gamma)
\geq
\frac{\mu_2}{\mu_n-\delta}.
$$

Gary and I proved this inequality. Complete multipartite graphs show that the bound cannot be improved in general.

### References

<ol class="research-references">
  <li>G. Greaves and H. Zhu, <em>A note on some spectral properties of generalised pancake graphs</em>, Discrete Mathematics 349 (2026), 115102.</li>
  <li>G. Greaves and H. Zhu, <em>A proof of Haemers' toughness conjecture</em>, arXiv:2605.15738 (2026).</li>
</ol>

</div>
