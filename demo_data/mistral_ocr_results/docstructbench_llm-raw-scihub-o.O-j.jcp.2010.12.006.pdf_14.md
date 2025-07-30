![img-0.jpeg](img-0.jpeg)

**Fig. 4.** The dispersion contours with stepsizes ∆*t* = 0.01, ∆ = 0.1 for Maxwell's equations (46) from (a) exact dispersion; (b) boxscheme; (c) symplectic method and (d) Yee's method. The constant contour values are ω ∈ [2,4,6,...,24].

$$
\varphi = \tan^{-1} \left(\frac{\left(v_g\right)_g}{\left(v_g\right)_s}\right), \quad |v_g| = \sqrt{\left(v_g\right)_s^2 + \left(v_g\right)_g^2}. \tag{48}
$$

Substituting into (48) the vectors κ and *v*<sub>*g*</sub> in polar coordinates (44), and let *a* = |κ|∆, this yields the propagation angle φ and the propagation speed |*v*<sub>*g*</sub>| in terms of *a* and θ.

For example, φ for the boxscheme is given by

$$
\varphi = \tan^{-1} \left(\frac{\sin \left(\frac{1}{2}\sin(\theta)a\right)\cos^3 \left(\frac{1}{2}\cos(\theta)a\right)}{\cos^3 \left(\frac{1}{2}\sin(\theta)a\right)\sin \left(\frac{1}{2}\cos(\theta)a\right)}\right).
$$

Taking the Taylor expansion of this expression with respect to *a* = 0 yields,

$$
\varphi \approx \theta - \frac{1}{12} \sin(4\theta)a^2 + O(a^3). \tag{49}
$$

Similarly, the Taylor expansion of |*v*<sub>*g*</sub>| at *a* = 0 yields,

$$
|v_g| \approx 1 + \left(\frac{1}{16} \cos(4\theta) - \frac{r^2}{4} + \frac{3}{16}\right)a^2 + O(a^4). \tag{50}
$$