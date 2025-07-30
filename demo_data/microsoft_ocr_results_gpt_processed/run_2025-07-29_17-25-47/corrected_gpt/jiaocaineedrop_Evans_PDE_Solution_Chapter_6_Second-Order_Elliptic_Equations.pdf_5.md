10. Proof. We omit (a) since it is standard. For (b), if $u$ attains an interior maximum, then the conclusion follows from the strong maximum principle.

If not, then for some $x^{0} \in \partial U, u(x^{0}) > u(x) \forall x \in U$. Then Hopf's lemma implies $\frac{\partial u}{\partial \nu}(x^{0}) > 0$, which is a contradiction.

Remark 2. A generalization of this problem to mixed boundary conditions is recorded in Gilbarg-Trudinger, Elliptic PDEs of second order, Problem 3.1.

11. Proof. Define

$$B[u, v] = \int_{U} \sum_{i, j} a^{ij} u_{x_{i}} v_{x_{j}} dx \text{ for } u \in H^{1}(U), v \in H_{0}^{1}(U).$$

By Exercise 5.17, $\phi(u) \in H^{1}(U)$. Then, for all $v \in C_{c}^{\infty}(U)$, $v \geq 0$,

$$B[\phi(u), v] = \int_{U} \sum_{i, j} a^{ij} (\phi(u))_{x_{i}} v_{x_{j}} dx$$
$$= \int_{U} \sum_{i, j} a^{ij} \phi^{\prime}(u) u_{x_{i}} v_{x_{j}} dx, (\phi^{\prime}(u) \text{ is bounded since } u \text{ is bounded})$$
$$= \int_{U} \sum_{i, j} a^{ij} u_{x_{i}} (\phi^{\prime}(u) v)_{x_{j}} - \sum_{i, j} a_{ij} \phi^{\prime\prime}(u) u_{x_{i}} u_{x_{j}} v dx$$
$$\leq 0 - \int_{U} \phi^{\prime\prime}(u) v |Du|^{2} dx \leq 0, \text{ by convexity of } \phi.$$

(We don't know whether the product of two $H^{1}$ functions is weakly differentiable. This is why we do not take $v \in H_{0}^{1}$.) Now we complete the proof with the standard density argument.

12. Proof. Given $u \in C^{2}(U) \cap C(\bar{U})$ with $Lu \leq 0$ in $U$ and $u \leq 0$ on $\partial U$. Since $\bar{U}$ is compact and $v \in C(\bar{U})$, $v \geq c > 0$. So $w := \frac{u}{v} \in C^{2}(U) \cap C(\bar{U})$. Brutal computation gives us

$$- a^{ij} w_{x_{i}x_{j}} = \frac{-a^{ij} u_{x_{i}x_{j}} v + a^{ij} v_{x_{i}x_{j}} u}{v^{2}} + \frac{a^{ij} v_{x_{i}} u_{x_{j}} - a^{ij} u_{x_{i}} v_{x_{j}}}{v^{2}} - a^{ij} \frac{2}{v} v_{x_{j}} \frac{v_{x_{i}} u - v u_{x_{i}}}{v^{2}}$$
$$= \frac{(Lu - b^{i} u_{x_{i}} - c u) v + (-Lv + b^{i} v_{x_{i}} + c v) u}{v^{2}} + 0 + a^{ij} \frac{2}{v} v_{x_{j}} w_{x_{i}}, \text{ since } a^{ij} = a^{ji}$$
$$= \frac{Lu}{v} - \frac{u Lv}{v^{2}} - b^{i} w_{x_{i}} + a^{ij} \frac{2}{v} v_{x_{j}} w_{x_{i}}$$

Therefore,

$$Mw := - a^{ij} w_{x_{i}x_{j}} + w_{x_{i}} \left[ b^{i} - a^{ij} \frac{2}{v} v_{x_{j}} \right] = \frac{Lu}{v} - \frac{u Lv}{v^{2}} \leq 0 \text{ on } \{ x \in \bar{U} : u > 0 \} \subseteq U$$

If $\{ x \in \bar{U} : u > 0 \}$ is not empty, Weak maximum principle to the operator $M$ with bounded coefficients (since $v \in C^{1}(\bar{U})$) will lead to a contradiction that

$$0 < \max_{\{ \bar{u > 0} \}} w = \max_{\partial \{ u > 0 \}} w = \frac{0}{v} = 0$$

Hence $u \leq 0$ in $U$.

<!-- PageNumber="6" -->