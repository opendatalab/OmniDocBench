<!-- PageNumber="2080" -->
<!-- PageHeader="Y. Sun, P.S.P. Tse/Journal of Computational Physics 230 (2011) 2076-2094" -->

where the difference operators $\partial_{t}$, $\bar{\partial}_{t}$ are the discretization of $\frac{\partial}{\partial t}$, and the difference operators $\partial_{\mathrm{x}_{1}}$, $\bar{\partial}_{x_{1}}$ are the discretization of $\frac{\partial}{\partial \mathrm{x}_{1}}$. Via these notations and the properties of the difference operators, we present the statement of the local/global conservation laws for the different numerical methods.

# 3.1. Symplectic method for Maxwell's equations

The following method is constructed based on the method of lines, i.e., discretizing the Hamiltonian PDEs in space, then applying the symplectic method to the resulting Hamiltonian ODEs (see for example [6,22]). Later, we will show the method is also multisymplectic in the corresponding statement of multisymplecticity.

For Maxwell's equations in Hamiltonian form, we use the central finite difference in space (which is leapfrog discretization) and implicit midpoint rule (which is symplectic) in time. It is easy to show that the Hamiltonian formulations in (5) and (7) for Maxwell's equations reduce to the same discretized system,

$$\partial_{t} z_{ijk}^{l} + M^{-1} K_{1} \bar{\partial}_{x_{1}} z_{ijk}^{l + \frac{1}{2}} + M^{-1} K_{2} \bar{\partial}_{x_{2}} z_{ijk}^{l + \frac{1}{2}} + M^{-1} K_{3} \bar{\partial}_{x_{3}} z_{ijk}^{l + \frac{1}{2}} = 0,$$
(18)

where indices $i$, $j$, $k$ denote spatial increments and index $l$ denotes time increment, and matrices $M$, $K_{1}$, ... as in (10). We refer to this particular discretization as the symplectic method, though it is also multisymplectic.

The symplectic method (18) is second-order in space and time, and is unconditionally stable. Furthermore, this discrete system preserves two discretized global conservation laws: the first one is the discrete quadratic global conservation law based on (8),

$$\frac{1}{2} \partial_{t} \left[ \mu \mathrm{H}_{ijk}^{l} \cdot \mathrm{H}_{ijk}^{l} + \varepsilon \mathrm{E}_{ijk}^{l} \cdot \mathrm{E}_{ijk}^{l} \right] = 0.$$
(19)

The second discretized global conservation law for the symplectic method is based on the helicity Hamiltonian functional (6)

$$\partial_{t} \left[ \frac{1}{2 \varepsilon} \mathrm{H}_{ijk}^{l} \cdot \widehat{\nabla} \times \mathrm{H}_{ijk}^{l} + \frac{1}{2 \mu} \mathrm{E}_{ijk}^{l} \cdot \widehat{\nabla} \times \mathrm{E}_{ijk}^{l} \right] = 0,$$
(20)

where $\widehat{\nabla} \times = R_{1} \partial_{x_{1}} + R_{2} \partial_{x_{2}} + R_{3} \partial_{x_{3}}$. Furthermore, the scheme (18) is proved to be multisymplectic, since it preserves the following multisymplectic conservation law

$$\partial_{x_{3}} \left[ \frac{1}{\varepsilon} d \mathrm{H}_{ijk-1}^{l + \frac{1}{2}} \wedge \mathrm{R}_{3} d \mathrm{H}_{ijk}^{l + \frac{1}{2}} + \frac{1}{\mu} d \mathrm{E}_{ijk-1}^{l + \frac{1}{2}} \wedge \mathrm{R}_{3} d \mathrm{E}_{ijk}^{l + \frac{1}{2}} \right] = 0.$$
(21)

Besides the global conservation laws, for the scheme (18) applied to Maxwell's equations, we also have the following local conservation laws based on (13)-(15):

The discrete quadratic conservation law is

$$\frac{1}{2} \partial_{x_{3}} \left[ \mathrm{H}_{ijk}^{l + \frac{1}{2}} \cdot \mathrm{R}_{3} \mathrm{E}_{ijk-1}^{l + \frac{1}{2}} + \mathrm{H}_{ijk-1}^{l + \frac{1}{2}} \cdot \mathrm{R}_{3} \mathrm{E}_{ijk}^{l + \frac{1}{2}} \right] = 0.$$
(22)

The discrete energy conservation law is

$$\partial_{t} \left[ \frac{1}{2 \varepsilon} \mathrm{H}_{ijk}^{l} \cdot \widehat{\nabla} \times \mathrm{H}_{ijk}^{l} + \frac{1}{2 \mu} \mathrm{E}_{ijk}^{l} \cdot \widehat{\nabla} \times \mathrm{E}_{ijk}^{l} \right] + \partial_{x_{1}} \left[ \frac{1}{2 \varepsilon} \partial_{t} \mathrm{H}_{ijk}^{l} \cdot \mathrm{R}_{1} \mathrm{H}_{i-1,jk}^{l + \frac{1}{2}} + \frac{1}{2 \mu} \partial_{t} \mathrm{E}_{ijk}^{l} \cdot \mathrm{R}_{1} \mathrm{E}_{i-1,jk}^{l + 1} \right]$$
$$+ \partial_{x_{2}} \left[ \frac{1}{2 \varepsilon} \partial_{t} \mathrm{H}_{ijk}^{l} \cdot \mathrm{R}_{2} \mathrm{H}_{ij-1,k}^{l + \frac{1}{2}} + \frac{1}{2 \mu} \partial_{t} \mathrm{E}_{ijk}^{l} \cdot \mathrm{R}_{2} \mathrm{E}_{ij-1,k}^{l + \frac{1}{2}} \right] + \partial_{x_{3}} \left[ \frac{1}{2 \varepsilon} \partial_{t} \mathrm{H}_{ijk}^{l} \cdot \mathrm{R}_{3} \mathrm{H}_{ijk-1}^{l + \frac{1}{2}} + \frac{1}{2 \mu} \partial_{t} \mathrm{E}_{ijk-1}^{l + 1} \right] = 0.$$
(23)

The discrete momentum conservation law is

<!-- PageFooter="6 Let $p_{i}$ and $q_{i}$ are the functions at grid $i$, $\partial$, $\widetilde{\delta}$ are the difference operators, then" -->

$$\partial \left[ q_{i} p_{i} \right] = q_{i+1} \partial p_{i} + \partial q_{i} p_{i} = \partial q_{i} p_{i+1} + q_{i} \partial p_{i},$$
$$\partial \left[ q_{i+1} p_{i} \right] = \partial q_{i+1} p_{i+1} + q_{i+1} \partial p_{i},$$
$$\bar{\partial} \left[ q_{i} p_{i} \right] = \bar{\partial} q_{i} p_{i+1} + q_{i-1} \bar{\partial} p_{i} = \bar{\partial} p_{i} q_{i+1} + p_{i-1} \bar{\partial} q_{i},$$

$$\bar{\partial} \left[ q_{i} p_{i+1} \right] = q_{i+1} \bar{\partial} p_{i+1} + \bar{\partial} q_{i} p_{i}.$$