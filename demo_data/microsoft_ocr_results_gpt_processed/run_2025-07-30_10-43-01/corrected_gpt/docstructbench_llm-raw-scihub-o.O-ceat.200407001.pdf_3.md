$$\stackrel { \mathrm { C } } { \mathcal{A} } _ { T } ^ { \mathrm { E } }$$
Full Paper

$$\Lambda _ { _ { \mathrm { T } } } \left( \mathrm { r } \right) = \lambda _ { \mathrm { b e d } } \left( \mathrm { r } \right) + \mathrm { K } _ { _ { \mathrm { l } } } \mathrm { P e } _ { _ { 0 } } \frac { \mathrm { u } _ { _ { \mathrm { c } } } } { \bar { \mathrm { u } } _ { _ { 0 } } } \mathrm { f } \left( \mathrm { R } - \mathrm { r } \right) \lambda _ { _ { \mathrm { f } } }$$
(17)

The damping function $\mathrm { f } \left( \mathrm { R } - \mathrm { r } \right)$ remains the same as for the
mass transfer (Eq.(11)), while the slope parameter and the
damping parameter are slightly modified to, respectively,

$$\mathrm { K } _ { 1 } = \frac { 1 } { 8 }$$
(18)

$$K _ { 2 } = 0.44 + 4 \exp \left( - \frac { R e _ { 0 } } { 70 } \right)$$
(19)

The heat release by adsorption, see [19] for $\Delta \mathrm { H } _ { \mathrm { a d } } ,$ is de-
rived in the last term on the right-hand side of Eq.(14) from
the change of solids load with time. This very term couples
the energy with the mass balance, so that both have to be
solved simultaneously in order to account for thermal ef-
fects. Heat transfer resistances to or in the particles are ne-
glected. The terms $\delta _ { \mathrm { b e d } } \left( \mathrm { r } \right)$ and $\lambda _ { \mathrm { b e d } } \left( \mathrm { r } \right)$ in Eqs. (8), (10), (15)
and (17) describe the isotropic effective diffusivity and ther-
mal conductivity of the bed without fluid flow. Boundary
and initial conditions for Eqs. (7) and (14) are recapitulated
in Tab. 1.

On the basis of the above described general model various
reductions are possible by neglecting thermal effects, the ra-
dial coordinate or gas-to-particle and intraparticle mass
transfer resistances. From such reduced versions the follow-
ing has been considered in more detail in the present work:

1\) plug-flow model (1-D) with local equilibrium between
the gas and the solids,

2\) plug-flow model (1-D) with mass transfer resistance to
the solids,

3\) 2-D maldistribution model with local equilibrium,

4\) 2-D maldistribution model with mass transfer resistance
to the solids.

In our terminology "plug flow" means that every influence
of the radial coordinate is neglected, including the influence
of the wall on porosity and flow velocity. However, axial dis-
persion, as expressed by the dispersion coefficient $\mathrm { D } _ { \mathrm { a x } }$ , is ac-
counted for, so that the equation

$$\bar { \Psi } \frac { \partial \mathrm { Y } } { \partial t } = \mathrm { D } _ { \mathrm { a x } } \frac { \partial ^ { 2 } \mathrm { Y } } { \partial \mathrm { z } ^ { 2 } } - \bar { \mathrm { u } } _ { 0 } \frac { \partial \mathrm { Y } } { \partial \mathrm { z } } - \left[ 1 - \bar { \psi } \right] \frac { \partial \mathrm { X } } { \partial \mathrm { t } } \frac { \partial \mathrm { p } } { \partial _ { \mathrm { f } } }$$
(20)

applies to the isothermal plug flow models (models 1 and 2).
Eq. (20) is the classical, conventional way to model packed
bed adsorbers. Local equilibrium corresponds, in terms of
the two-layers model from [19], to the limiting case of $\beta _ { \mathrm { f } } \rightarrow \infty$

and $\beta _ { \mathrm { p } } \rightarrow \infty$ . At this limit, equilibrium is considered to be
sufficient for calculating the response of the solid phase to
changes of the concentration in the fluid. Model 4 is our
complete, highest order model, as previously outlined and in
exact correspondence to [13-18]. Mainly this model has been
evaluated for both isothermal and non-isothermal condi-
tions.


# 4 Numerical Solution and its Validation

The partial differential equation or equations of the var-
ious models have been solved by the method of lines. The
numerical calculations were conducted for different mesh
densities, and the results accepted when the change of calcu-
lated gas moisture content values was lower than 0.05 % of
the maximal difference of gas moisture content appearing in
the packed bed. When the error was bigger, the mesh was
made denser. Since the width of the concentration front is,
in many cases, not much smaller than the length of the bed,
equidistant meshes have been used in the axial direction. In
the maldistribution models (models 3 and 4 in the previous
section) meshes that were denser near the wall than in the
center of the tube have been applied.

To check the numerical procedure, respective results have
been compared with available analytical solutions. One of
such a solution is attributed to Anzelius [1] and refers to
model 2 after the classification of section 3, additionally re-
duced by neglecting axial dispersion $\left( \mathrm { D } _ { \mathrm { a x } } = 0 \right)$ . Furthermore,
it is assumed that the sorption equilibrium is throughout lin-
ear ("Henry's law"), and that the bed is long. The mass
transfer resistance is attributed to the fluid phase. Then, ax-
ial profiles can be derived to

$$\frac { C } { C _ { \in } } = \frac { 1 } { 2 } e r f c \left( \sqrt { \frac { e } { 5 } } - \sqrt { \tau } \right)$$
(21)

with

$$5 = 6 \frac { \beta _ { f } } { d _ { p } } \frac { z } { u } \frac { 1 - \psi } { \psi }$$
(22)

and

$$\tau = 6 \frac { \beta _ { _ { L } } } { d _ { _ { \mathrm { D } } } K } \left( t - \frac { \mathrm { z } } { \mathrm { u } } \right)$$
(23)

In Eq. (21) the concentration of adsorbate in the gas
phase, C, is used instead of the content, $\mathrm { Y } . ,$ assuming an ini-


Table 1. Boundary and initial conditions for models.

| | | | | |
| - | - | - | - | - |
| $$t > 0$$
$$0 \leq \mathrm { r } \leq \mathrm { R }$$ | $$\mathrm { z } = 0$$
$$\mathrm { z } = \mathrm { L }$$ | $$\frac { \partial \mathrm { X } } { \partial \mathrm { z } } = 0$$ | $$\mathrm { Y } = \mathrm { Y } _ { \mathrm { i n } } \quad \mathrm { o r }$$
$$\mathrm { u } _ { 0 } \left( \mathrm { Y } _ { \mathrm { i n } } - \mathrm { Y } \right) = - \mathrm { D } _ { \mathrm { a x } } \frac { \partial \mathrm { Y } } { \partial \mathrm { z } }$$
$$\frac { \partial \mathrm { Y } } { \partial \mathrm { z } } = 0$$ | $$\mathrm { T } = \mathrm { T } _ { \mathrm { i n } }$$
$$\frac { \partial \mathrm { T } } { \partial \mathrm { z } } = 0$$ |
| $$t > 0$$
$$0 \leq \mathrm { z } \leq \mathrm { L }$$ | $$\mathrm { r } = 0$$
$$\mathrm { r } = \mathrm { R }$$ | $$\frac { \partial \mathrm { X } } { \partial \mathrm { r } } = 0$$
$$\frac { \partial \mathrm { X } } { \partial \mathrm { r } } = 0$$ | $$\frac { \partial \mathrm { Y } } { \partial \mathrm { r } } = 0$$
$$\frac { \partial \mathrm { Y } } { \partial \mathrm { r } } = 0$$ | $$\frac { \partial \Gamma } { \partial \mathrm { r } } = 0$$
$$\mathrm { T } = \mathrm { T } _ { \mathrm { w } }$$ |
| $$t = 0$$
$$0 \leq \mathrm { r } \leq \mathrm { R }$$ | $$0 \leq \mathrm { z } \leq \mathrm { L }$$ | $$\mathrm { X } \left( \mathrm { r } , \mathrm { z } \right) = \mathrm { X } _ { 0 }$$ | $$\mathrm { Y } \left( \mathrm { r } , \mathrm { z } \right) = \mathrm { Y } _ { 0 }$$ | $$\mathrm { T } \left( \mathrm { r } , \mathrm { z } \right) = \mathrm { T } _ { 0 }$$ |


<!-- PageFooter="Chem. Eng. Technol. 2004, 27, No. 11" -->
<!-- PageFooter="http://www.cet-journal.de" -->
<!-- PageFooter="© 2004 WILEY-VCH Verlag GmbH & Co. KGaA, Weinheim" -->
<!-- PageNumber="1181" -->