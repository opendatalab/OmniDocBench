<!-- PageNumber="2089" -->
<!-- PageHeader="Y. Sun, P.S.P. Tse/Journal of Computational Physics 230 (2011) 2076-2094" -->


Fig. 4. The dispersion contours with stepsizes $\Delta t = 0.01$ , $\Delta = 0.1$ for Maxwell's equations (46) from (a) exact dispersion; (b) boxscheme; (c) symplectic
method and (d) Yee's method. The constant contour values are $co \in \left[ 2 , 4 , 6 , \ldots , 24 \right]$ .

![30 Exact dispersion 30 Boxscheme 20 20 10 10 $$\mathrm { k y }$$ 0 $$\mathrm { k y }$$ 0 -10 -10 -20 -20 -30 -20 -10 0 10 20 30 -30 -20 -10 0 10 20 30 kx $$\mathrm { k x }$$
$$\mathrm { k x }$$ (a) (b) 30 Symplectic method 30 Yee's method 20 20 10 10 $$k y$$ $$\mathrm { k y }$$ 0 0 -10 -10 -20 -20 -30 -20 -10 0 10 20 30 -30 -20 -10 0 10 20 30 kx (c) (d)](figures/1.1)


$$\rho = \tan ^ { - 1 } \left( \frac { \left( \nu _ { g } \right) _ { y } } { \left( \nu _ { g } \right) _ { x } } \right) , \quad | v _ { g } | = \sqrt { \left( \nu _ { g } \right) _ { x } ^ { 2 } + \left( \nu _ { g } \right) _ { y } ^ { 2 } } .$$
(48)

Substituting into (48) the vectors $k$ and $v _ { \mathrm { g } }$ in polar coordinates (44), and let $a = | \kappa | \Delta ,$ this yields the propagation angle $\varphi$ and
the propagation speed $| v _ { \mathrm { g } } |$ in terms of $a$ and $\theta$ .

For example, $\varphi$ for the boxscheme is given by

$$\underline { \varphi } = \tan ^ { - 1 } \left( \frac { \sin \left( \frac { 1 } { 2 } \sin \left( \theta \right) a \right) \cos ^ { 3 } \left( \frac { 1 } { 2 } \cos \left( \theta \right) a \right) } { \cos ^ { 3 } \left( \frac { 1 } { 2 } \sin \left( \theta \right) a \right) \sin \left( \frac { 1 } { 2 } \cos \left( \theta \right) a \right) } \right) .$$

Taking the Taylor expansion of this expression with respect to $a = 0$ yields,

$$\phi \approx \theta - \frac { 1 } { 12 } \sin \left( 4 \theta \right) a ^ { 2 } + O \left( a ^ { 3 } \right) .$$
(49)

Similarly, the Taylor expansion of $| v _ { \mathrm { g } } |$ at $a = 0$ yields,

$$| v _ { g } | \approx 1 + \left( \frac { 1 } { 16 } \cos \left( 4 \theta \right) - \frac { r ^ { 2 } } { 4 } + \frac { 3 } { 16 } \right) a ^ { 2 } + O \left( a ^ { 4 } \right)$$
(50)
```