<!-- PageNumber="2080" -->
<!-- PageHeader="Y. Sun, P.S.P. Tse/Journal of Computational Physics 230 (2011) 2076-2094" -->

where the difference operators $\partial _ { t }$ , $\bar { \partial } _ { t }$ are the discretization of $\frac { \partial } { \partial t } ,$ and the difference operators $\partial _ { \mathrm { x } _ { \mathrm { l } } }$ , $\bar { \partial } _ { x _ { 1 } }$ are the discretization of
$\frac { \partial } { \partial \mathrm { x } _ { 1 } }$ . Via these notations and the properties of the difference operators,6 we present the statement of the local/global conservation laws for the different numerical methods.


# 3.1. Symplectic method for Maxwell's equations

The following method is constructed based on the method of lines, i.e. discretizing the Hamiltonian PDEs in space, then
applying the symplectic method to the resulting Hamiltonian ODEs (see for example [6,22]). Later, we will show the method
is also multisymplectic in the corresponding statement of multisymplecticity.

For Maxwell's equations in Hamiltonian form, we use the central finite difference in space (which is leapfrog discretization) and implicit midpoint rule (which is symplectic) in time, it is easy to show that the Hamiltonian formulations in (5) and
(7) for Maxwell's equations reduce to the same discretized system,

$$\partial _ { t } z _ { i j k } ^ { l } + M ^ { - 1 } K _ { 1 } \bar { \partial } _ { \chi _ { 1 } } z _ { i j k } ^ { l + \frac { 1 } { 2 } } + M ^ { - 1 } K _ { 2 } \bar { \partial } _ { x _ { 2 } } z _ { l j , k } ^ { l + \frac { 1 } { 2 } } + M ^ { - 1 } K _ { 3 } \bar { \partial } _ { x _ { 3 } } \bar { z } _ { l j , k } ^ { l + \frac { 1 } { 2 } } = 0 ,$$
(18)

where indices $i$ , j, $k$ denote spatial increments and index I denotes time increment, and matrices $M$ , $K _ { 1 } , . ,$ ... as in (10). We refer
to this particular discretization as the symplectic method, though it is also multisymplectic.

The symplectic method (18) is second-order in space and time, and is unconditionally stable. Furthermore, this discrete
system preserves two discretized global conservation laws: the first one is the discrete quadratic global conservation law based
on (8),

$$\frac { 1 } { 2 } \partial _ { t } \left[ \mu \mathrm { H } _ { i j , k } ^ { l } \cdot \mathrm { H } _ { i j , k } ^ { l } + \varepsilon \mathrm { E } _ { i j , k } ^ { l } \cdot \mathrm { E } _ { i j , k } ^ { l } \right] = 0 .$$
(19)

The second discretized global conservation law for symplectic method is based on the helicity Hamiltonian functional (6)

$$\partial _ { t } \left[ \frac { 1 } { 2 \varepsilon } \mathrm { H } _ { i j , k } ^ { l } \cdot \widehat { \nabla } \times \mathrm { H } _ { i j , k } ^ { l } + \frac { 1 } { 2 \mu } \mathrm { E } _ { i j , k } ^ { l } \cdot \widehat { \nabla } \times \mathrm { E } _ { i j , k } ^ { l } \right] = 0 ,$$
(20)

where $\widetilde { \nabla } \times = R _ { 1 } \partial _ { x _ { 1 } } + R _ { 2 } \partial _ { x _ { 2 } } + R _ { 3 } \partial _ { x _ { 3 } }$ . Furthermore, the scheme (18) is proved to be multisymplectic, since it preserves the following multisymplectic conservation law

$$+ \partial _ { \mathrm { x } _ { 3 } } \left[ \frac { 1 } { \mathrm { e } } d \mathrm { H } _ { \mathrm { i } j k - 1 } ^ { l + \frac { 1 } { 2 } } \wedge \mathrm { R } _ { 3 } \mathrm { d H } _ { \mathrm { i } j , k } ^ { l + \frac { 1 } { 2 } } + \frac { 1 } { \mu } d \mathrm { E } _ { i j k - 1 } ^ { l + \frac { 1 } { 2 } } \wedge \mathrm { R } _ { 3 } \mathrm { d E } _ { i , k } ^ { l + \frac { 1 } { 2 } } \right] = 0 .$$
(21)

Besides the global conservation laws, for the scheme (18) applied to Maxwell's equations, we also have the following local
conservation laws based on (13)-(15):

The discrete quadratic conservation law is

$$+ \frac { 1 } { 2 } \partial _ { \mathrm { x } _ { 3 } } \left[ \mathrm { H } _ { i j , k } ^ { l + \frac { 1 } { 2 } } \cdot \mathrm { R } _ { 3 } \mathrm { E } _ { i j , k - 1 } ^ { l + \frac { 1 } { 2 } } + \mathrm { H } _ { i j , k - 1 } ^ { l + \frac { 1 } { 2 } } \cdot \mathrm { R } _ { 3 } \mathrm { E } _ { i j , k } ^ { l + \frac { 1 } { 2 } } \right] = 0 .$$
(22)

The discrete energy conservation law is

$$\partial _ { t } \left[ \frac { 1 } { 2 e } \mathrm { H } _ { i j , k } ^ { l } \cdot \widehat { \nabla } \times \mathrm { H } _ { i j , k } ^ { l } + \frac { 1 } { 2 \underline { \mu } } \mathrm { E } _ { i j , k } ^ { l } \cdot \widehat { \nabla } \times \mathrm { E } _ { i j , k } ^ { l } \right] + \partial _ { x _ { l } } \left[ \frac { 1 } { 2 e } \partial _ { t } \mathrm { H } _ { i j k } ^ { l } \cdot \mathrm { R } _ { 1 } \mathrm { H } _ { i - 1 , j k } ^ { l + \frac { 1 } { 2 } } + \frac { 1 } { 2 \mu } \partial _ { t } \mathrm { E } _ { i j k } ^ { l } \cdot \mathrm { R } _ { 1 } \mathrm { E } _ { i - 1 , j k } ^ { l + 1 } \right]$$
$$+ \partial _ { \mathrm { x } _ { 2 } } \left[ \frac { 1 } { 2 e } \partial _ { t } \mathrm { H } _ { i j k } ^ { l } \cdot \mathrm { R } _ { 2 } \mathrm { H } _ { i j - 1 , k } ^ { l + \frac { 1 } { 2 } } + \frac { 1 } { 2 \mu } \partial _ { t } \mathrm { E } _ { i j , k } ^ { l } \cdot R _ { 2 } \mathrm { E } _ { i j - 1 , k } ^ { l + \frac { 1 } { 2 } } \right] + \partial _ { 3 } \left[ \frac { 1 } { 2 e } \partial _ { t } \mathrm { H } _ { i j , k } ^ { l } \cdot \mathrm { R } _ { 3 } \mathrm { H } _ { i j k - 1 } ^ { l + \frac { 1 } { 2 } } + \frac { 1 } { 2 \mu } \partial _ { t } \mathrm { E } _ { i j k - 1 } ^ { l + 1 } \right] = 0 .$$
(23)

The discrete momentum conservation law is

<!-- PageFooter="6 Let $p _ { i }$ and $q _ { i }$ are the functions at grid $i$ , $\partial$ , $\widetilde { \delta }$ are the difference operators, then" -->

$$\partial \left[ q _ { i } p _ { i } \right] = q _ { i + 1 } \partial p _ { i } + \partial q _ { i } p _ { i } = \partial q _ { i } p _ { i + 1 } + q _ { i } \partial p _ { i } ,$$
$$\partial \left[ q _ { i + 1 } p _ { i } \right] = \partial q _ { i + 1 } p _ { i + 1 } + q _ { i + 1 } \partial p _ { i } ,$$
$$\bar { \partial } \left[ q _ { i } p _ { i } \right] = \bar { \partial } q _ { i } p _ { i + 1 } + q _ { i - 1 } \bar { \partial } p _ { i } = \bar { \partial } p _ { i } q _ { i + 1 } + p _ { i - 1 } \bar { \partial } q _ { i } |$$

$$\bar { \partial } \left[ q _ { i } p _ { i + 1 } \right] = q _ { i + 1 } \bar { \partial } p _ { i + 1 } + \bar { \partial } q _ { i } p _ { i } .$$