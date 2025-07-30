10. Proof. We omit (a) since it is standard. For (b), if $u$ attains an interior maximum, then the
conclusion follows from strong maximum principle.

If not, then for some $x ^ { 0 } \in \partial U , u \left( x ^ { 0 } \right) > u \left( x \right) \forall x \in U$ . Then Hopf's lemma implies that $\frac { \partial u } { \partial \nu } \left( x ^ { 0 } \right) > 0$ ,
which is a contradiction.

Remark 2. A generalization of this problem to mixed boundary conditions is recorded in
Gilbarg-Trudinger, Elliptic PDEs of second order, Problem 3.1.

11. Proof. Define

$$B \left[ u , v \right] = \int _ { U } \sum _ { i , j } a ^ { i j } u _ { x _ { i } } v _ { x _ { j } } d x \mathrm { f o r } u \in H ^ { 1 } \left( U \right) , v \in H _ { 0 } ^ { 1 } \left( U \right) .$$

By Exercise 5.17, $\phi \left( u \right) \in H ^ { 1 } \left( U \right)$ . Then, for all $v \in C _ { c } ^ { \infty } \left( U \right)$ , $v \geq 0$ ,

$$B \left[ \phi \left( u \right) , v \right] = \int _ { U } \sum _ { i , j } a ^ { i j } \left( \phi \left( u \right) \right) _ { x _ { i } } v _ { x _ { j } } d x$$
$$= \int _ { U } \sum _ { i , j } a ^ { i j } \phi ^ { \prime } \left( u \right) u _ { x _ { i } } v _ { x _ { j } } d x , \left( \phi ^ { \prime } \left( u \right) \text { is bounded since $u$ is bounded } \right)$$
$$= \int _ { U } \sum _ { i , j } a ^ { i j } u _ { x _ { i } } \left( \phi ^ { \prime } \left( u \right) v \right) _ { x _ { j } } - \sum _ { i , j } a _ { i j } \phi ^ { \prime \prime } \left( u \right) u _ { x _ { i } } u _ { x _ { j } } v d x$$
$$\leq 0 - \int _ { U } \phi ^ { \prime \prime } \left( u \right) v | D u | ^ { 2 } d x \leq 0 , \text { by convexity of } \phi .$$

(We don't know whether the product of two $H ^ { 1 }$ functions is weakly differentiable. This is why
we do not take $\left. v \in H _ { 0 } ^ { 1 } . \right)$ Now we complete the proof with the standard density argument.

12. Proof. Given $u \in C ^ { 2 } \left( U \right) \cap C \left( \bar { U } \right)$ with $L u \leq 0$ in $U$ and $u \leq 0$ on $\partial U$ . Since $\bar { U }$ is compact and
$v \in C \left( \bar { U } \right)$ , $v \geq c > 0$ . So $w : = \frac { u } { v } \in C ^ { 2 } \left( U \right) \cap C \left( \bar { U } \right)$ . A brutal computation gives us

$$- a ^ { i j } w _ { x _ { i } x _ { j } } = \frac { - a ^ { i j } u _ { x _ { i } x _ { j } } v + a ^ { i j } v _ { x _ { i } x _ { j } } u } { v ^ { 2 } } + \frac { a ^ { i j } v _ { x _ { i } } u _ { x _ { j } } - a ^ { i j } u _ { x _ { i } } v _ { x _ { j } } } { v ^ { 2 } } - a ^ { i j } \frac { 2 } { v } v _ { x _ { j } } \frac { v _ { x _ { i } } u - v u _ { x _ { i } } } { v ^ { 2 } }$$
$$\left. = \frac { \left( L u - b ^ { i } u _ { x _ { i } } - c u \right) v + \left( - L v + b ^ { i } v _ { x _ { i } } + c v \right) u } { v ^ { 2 } } + 0 + a ^ { i j } \frac { 2 } { v } v _ { x _ { j } } w _ { x _ { i } } , \mathrm { s i n c e } a ^ { i j } = a ^ { j i } \right]$$
$$= \frac { L u } { v } - \frac { u L v } { v ^ { 2 } } - b ^ { i } w _ { x _ { i } } + a ^ { i j } \frac { 2 } { v } v _ { x _ { j } } w _ { x _ { i } }$$

Therefore,

$$M w : = - a ^ { i j } w _ { x _ { i } x _ { j } } + w _ { x _ { i } } \left[ b ^ { i } - a ^ { i j } \frac { 2 } { v } v _ { x _ { j } } \right] = \frac { L u } { v } - \frac { u L v } { v ^ { 2 } } \leq 0 \mathrm { o n } \left\{ x \in \bar { U } : u > 0 \right\} \subseteq U$$

If $\left\{ x \in \bar { U } : u > 0 \right\}$ is not empty, Weak maximum principle to the operator $M$ with bounded
coefficients (since $\left. v \in C ^ { 1 } \left( \bar { U } \right) \right)$ will lead to a contradiction that

$$0 < \max _ { \left\{ \bar { u > 0 } \right\} } w = \max _ { \partial \left\{ u > 0 \right\} } w = \frac { 0 } { v } = 0$$

Hence $u \leq 0$ in $U$ .
```