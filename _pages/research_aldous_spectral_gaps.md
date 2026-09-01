---
layout: page
permalink: /research/current/spectral-gap-problems/
title: Spectral Gap Problems
nav: false
---

<a class="research-topic-back" href="{{ '/research/current/' | relative_url }}">&larr; Current Research</a>

<div class="research-note" markdown="1">

<p class="research-note__intro">
  Spectral-gap problems are among the questions I find most compelling. They arise naturally in graph theory, probability theory and quantum information theory, and their different formulations invite combinatorial, probabilistic and operator-theoretic approaches. This page gives a brief introduction to several problems in this programme, together with my related work.
</p>

## Aldous spectral gap conjecture

Let $\Gamma$ be a finite connected weighted graph on $n$ vertices. A continuous-time random walk follows one particle as it moves across the edges of $\Gamma$. In the **interchange process**, the vertices carry $n$ distinct labels, and the two labels at the ends of an edge are exchanged at that edge's rate. The random walk has $n$ states, whereas the interchange process has $n!$ states.

Following any single label projects the interchange process onto the original random walk. Consequently,

$$
\operatorname{gap}(\operatorname{IP}(\Gamma))
\leq
\operatorname{gap}(\operatorname{RW}(\Gamma)).
$$

The conjecture arose around 1992 and was later recorded by Aldous and Fill&nbsp;<span class="research-citation">[1]</span>. It asserts that equality holds for every finite weighted graph. Handjani and Jungreis&nbsp;<span class="research-citation">[11]</span> proved the weighted-tree case, and Caputo, Liggett and Richthammer&nbsp;<span class="research-citation">[5]</span> proved the full conjecture by combining electrical-network reduction with the **Octopus Inequality**.

There is an equivalent representation-theoretic formulation. A weighted graph on $[n]$ determines a weighted set of transpositions in $\mathfrak{S}_{n}$. The conjecture says that the spectral gap of the resulting Cayley walk on $\mathfrak{S}_{n}$ is already visible in its natural action on $[n]$—or, after removing the trivial summand, in the standard representation indexed by $(n-1,1)$. Thus the first non-trivial eigenvalue of an operator on $n!$ states is detected in dimension $n-1$.

**Aldous-type spectral gaps on arbitrary groups.** The classical theorem opens a broader programme: given a group and a distinguished low-dimensional representation, determine when that representation already captures the spectral gap of a much larger Cayley walk. Cesi&nbsp;<span class="research-citation">[6]</span> established such a result for a structured class of weighted generators in the type-$B$ Weyl group $W(B_n)$, with the gap detected by a $2n$-dimensional permutation representation. Levhari and Puder&nbsp;<span class="research-citation">[12]</span> proved an analogue for the generalised symmetric groups $G\wr\mathfrak{S}_{n}$, where $G$ is an arbitrary finite group. A continuous version developed by Alon and Puder&nbsp;<span class="research-citation">[3]</span> connects random walks on $\mathrm{U}(n)$ with discrete KMP, or uniform-reshuffling, processes.

**Aldous-type spectral gaps for other connection sets.** Keeping $\mathfrak{S}_{n}$ fixed while changing the connection set leads to a second central problem: determine when the strictly second-largest eigenvalue is still attained by the standard representation—the property now called the **Aldous property**. Parzanchevski and Puder&nbsp;<span class="research-citation">[14]</span> established strong comparison results for full conjugacy classes and showed why the most direct extension fails for arbitrary normal sets. Li&nbsp;<span class="research-citation">[13]</span> systematically analysed cycle-generated families, for which the Aldous property may hold or fail depending on the connection set.

Non-normal examples are substantially harder. In joint work with Gary Greaves, we proved that, for $n\geq4$, the full-flag Johnson graph $\operatorname{FJ}(n,2)$ has spectral gap equal to that of the Schreier quotient arising from its point-stabiliser equitable partition&nbsp;<span class="research-citation">[9]</span>.

<hr class="research-note__divider" aria-hidden="true">

## $\alpha$-shuffle spectral gap conjecture

The interaction itself may also change. Whereas the interchange process swaps the two labels at an edge, a hypergraph update may reshuffle all labels in a larger set. Let $V=[n]$ and assign a rate $\alpha_A\geq0$ to each subset $A\subseteq V$. In the **$\alpha$-shuffle process**, at rate $\alpha_A$ a uniformly random permutation is applied to the labels occupying $A$.

Following a single label gives a continuous-time random walk on $V$ with jump rates

$$
c_\alpha(i,j)
=
\sum_{A\subseteq V:\,i,j\in A}
\frac{\alpha_A}{|A|}
\qquad (i\neq j).
$$

Projection therefore gives

$$
\operatorname{gap}(\alpha\text{-shuffle})
\leq
\operatorname{gap}(\operatorname{RW}(V,c_\alpha)).
$$

Caputo conjectured that equality holds for arbitrary nonnegative weights $\alpha$. This is the **$\alpha$-shuffle spectral gap conjecture**, also known as the **Aldous–Caputo spectral gap conjecture**. The ordinary interchange process is the special case in which $\alpha_A=0$ unless $|A|=2$. Bristiel and Caputo&nbsp;<span class="research-citation">[4]</span> proved the conjecture in the mean-field setting, while Alon, Kozma and Puder&nbsp;<span class="research-citation">[2]</span> generalised the Octopus Inequality and established further substantial families of hypergraphs.

<hr class="research-note__divider" aria-hidden="true">

## Fill spectral gap conjecture

The general biased adjacent-transposition shuffle is a well-studied Markov chain on $\mathfrak{S}_{n}$. It arises from self-organising lists, where it is important in the probabilistic analysis of stationary behaviour, and is closely connected to exclusion processes in probability and statistical mechanics. Gheissari, Lee and Vigoda&nbsp;<span class="research-citation">[8]</span> call Fill's polynomial-mixing conjecture for this chain ‘well-known and long-standing’. The same 2003 manuscript, posted essentially unchanged in 2025, contains the sharper spectral-gap problem considered here&nbsp;<span class="research-citation">[7]</span>: among regular biases, is the gap minimised by the unbiased chain?

The chain is defined as follows. For distinct labels $i$ and $j$, choose parameters satisfying

$$
0<p_{i,j}<1,
\qquad
p_{i,j}+p_{j,i}=1.
$$

From a permutation $x=(x_1,\ldots,x_n)$, choose $r\in\{1,\ldots,n-1\}$ uniformly. The chain keeps $x_r$ immediately to the left of $x_{r+1}$ with probability $p_{x_r,x_{r+1}}$, and reverses their order with probability $p_{x_{r+1},x_r}$. It is reversible with stationary distribution

$$
\pi(x)
=
Z^{-1}
\prod_{1\leq r<s\leq n}p_{x_r,x_s}.
$$

Fill's motivation came from the **move-ahead-one** rule for self-organising linear-search lists and from the problem of sampling efficiently from this stationary distribution. He called the parameter vector $\mathbf{p}$ **regular** when

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

Thus the unbiased adjacent-transposition chain should minimise the gap among all regular biases. Where Aldous compares a symmetric interchange process with its one-particle projection, Fill asks for the extremal gap across a family of biased chains. The label-dependent bias breaks the symmetry of the uniform model, so the two problems are close in spirit but require different mechanisms.

In joint work with Gary Greaves, we proved the following sharp lower bound for every probability vector of order $n\geq3$&nbsp;<span class="research-citation">[10]</span>:

$$
\lambda_K(\mathbf{p})
\geq
\frac{1-2m_{\mathbf{p}}\cos(\pi/n)}{n-1},
\qquad
m_{\mathbf{p}}
=
\max_{i<j<k}
\sqrt{
  p_{i,j}p_{j,k}p_{k,i}
  +
  p_{k,j}p_{j,i}p_{i,k}
}.
$$

For regular vectors, $m_{\mathbf{p}}\leq 1/2$, which resolves Fill's conjecture. Moreover, for $n\geq3$, equality with the uniform gap holds precisely when there is a **neutral label** $c$, meaning that $p_{c,i}=1/2$ for every $i\neq c$. Hence the uniform chain is a minimiser, but not the unique one. We also determined the exact multiplicity of the corresponding second-largest eigenvalue.

### References

<ol class="research-references">
  <li>
    D. Aldous and J. A. Fill, <em>Reversible Markov Chains and Random Walks on Graphs</em>, unfinished monograph (2002; recompiled 2014), Open Problem 14.29.
  </li>
  <li>
    G. Alon, G. Kozma and D. Puder, <em>On the Aldous–Caputo spectral gap conjecture for hypergraphs</em>, Mathematical Proceedings of the Cambridge Philosophical Society 179 (2025), 259–298.
  </li>
  <li>
    G. Alon and D. Puder, <em>Aldous-type spectral gaps in unitary groups</em>, arXiv:2603.00353 (2026).
  </li>
  <li>
    A. Bristiel and P. Caputo, <em>Entropy inequalities for random walks and permutations</em>, Annales de l’Institut Henri Poincaré, Probabilités et Statistiques 60 (2024), 54–81.
  </li>
  <li>
    P. Caputo, T. M. Liggett and T. Richthammer, <em>Proof of Aldous' spectral gap conjecture</em>, Journal of the American Mathematical Society 23 (2010), 831–851.
  </li>
  <li>
    F. Cesi, <em>On the spectral gap of some Cayley graphs on the Weyl group $W(B_n)$</em>, Linear Algebra and its Applications 586 (2020), 274–295.
  </li>
  <li>
    J. A. Fill, <em>An interesting spectral gap problem, from Jim Fill</em>, unpublished notes (2003), posted as arXiv:2508.12557 (2025).
  </li>
  <li>
    R. Gheissari, H. Lee and E. Vigoda, <em>Mixing of general biased adjacent transposition chains</em>, Proceedings of the 58th Annual ACM Symposium on Theory of Computing (STOC 2026), 1236–1241.
  </li>
  <li>
    G. Greaves and H. Zhu, <em>Aldous property for full-flag Johnson graphs</em>, arXiv:2603.10406 (2026).
  </li>
  <li>
    G. Greaves and H. Zhu, <em>Spectral gap of biased adjacent-transposition chains</em>, arXiv:2603.26303 (2026).
  </li>
  <li>
    S. Handjani and D. Jungreis, <em>Rate of convergence for shuffling cards by transpositions</em>, Journal of Theoretical Probability 9 (1996), 983–993.
  </li>
  <li>
    N. Levhari and D. Puder, <em>Aldous-type spectral gaps in generalized symmetric groups</em>, arXiv:2605.22101 (2026).
  </li>
  <li>
    Y. Li, <em>The Second Largest Eigenvalue of Cayley Graphs on Symmetric Groups</em>, PhD thesis, The University of Melbourne, 2024.
  </li>
  <li>
    O. Parzanchevski and D. Puder, <em>Aldous's spectral gap conjecture for normal sets</em>, Transactions of the American Mathematical Society 373 (2020), 7067–7086.
  </li>
</ol>

</div>
