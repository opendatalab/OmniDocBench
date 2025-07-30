<!-- PageNumber="808" -->


# 2.9 Elimination of secondary structures

Based on the superposition principle, vortices and vortical shear layers from blades passing the measurement
window are identified and numerically removed from the
image such that the vortex of interest remains almost
unaffected. Thereafter, its parameters can be identified
without being biased by disturbing structures. Currently,
this is performed manually in the measurement plane,
and only for the in-plane velocities. The disturbing
vortex is identified by a best fit to a Vatistas swirl model
and its contribution is then subtracted from the entire
velocity field. This can also be done iteratively until no
fragments of the disturbing structure remain. In general,
both (or more) structures could be identified simultaneously, but this is complicated by different orientation
of their vortex axis with respect to the measurement
plane and not implemented yet.

An example is given in Fig. 10a where two vortices of
opposite sense of rotation are close to each other, and
both are affecting the other vortex flow field adversely.
In (a) the vortex centre was manually set to the centre of
the disturbing structure, using the scalar field of
$\widehat { \lambda } _ { 2 }$ -convolution. After elimination of this structure using
a best fit to Vatistas swirl model the remaining vortex is
clearly unaffected by other structures (b) and its
parameters can be identified. To do even more, the shear
layer at the lower left of the image could be eliminated
by the same procedure.


# 2.10 Identification of vortex parameters

The identification of the swirl and the axial velocity
profiles, the core radius and the circulation is often
hindered by other flow structures in close proximity of
the vortex of interest. These are shear layers with vorticity and additional vortices shed by other blades just
passing the measurement window, especially where BVI
takes place.

Using a best fit of a Vatistas vortex swirl model [26],
the parameters describing the vortex are identified. This
model is written in terms of the maximum swirl velocity
$V _ { s , m a x }$ at the core radius $r _ { c } ,$ the shape parameter $n$ that
describes the distribution of vorticity (and therewith the
distribution of $\widehat { \curlywedge } _ { 2 }$ and $\left. \varrho \right)$ , and the radial distance from the
vortex centre. The development of vortex circulation, and
thus the fraction of total circulation at the core radius, is
connected to the swirl velocity profile as well. All relations
for the Vatistas vortex are given [27]. Note that all vari-
ables are made non-dimensional, i.e., the velocities are
divided by $\Omega R$ , circulation and kinematic viscosity by $\Omega$
$R ^ { 2 }$ , vorticity by $\Omega$ , coordinates by the core radius $r _ { _ { \leq } }$ , the
core radius by $R$ , and the flow field operators by $\Omega ^ { \bar { 2 } } .$

$$V _ { s } = V _ { s 0 } \frac { r } { \left( 1 + r ^ { 2 n } \right) ^ { 1 / n } }$$
$$V _ { s 0 } = V _ { s , m a x } 2 ^ { 1 / n } = \frac { \Gamma _ { v } } { 2 \pi r _ { c } }$$


Fig. 10 Elimination of disturbing structures. BL, pos. 47 of Fig. 1,
simple average

![4 $$\omega _ { y } / \Omega$$ 3 2 1 $$1 0 0 z _ { V } / R$$ 0 3 2 $$m a x$$ -1 0 -2 -2 min -3 -4 -3 -2 -1 0 1 2 3 $$1 0 0 x _ { V } / R$$ (a) original data 4 $$a _ { y } / \Omega$$ 3 2 1 $$1 0 0 z _ { V } / R$$ 十 0 3 $$m a x$$ -1 0 -2 min -3 -4 -3 -2 -1 0 1 2 3 $$1 0 0 x _ { V } / R$$ (b) counter-rotating vortex removed](figures/1.1)


Alternatively, the Lamb-Oseen [10, 18] or Newman
[17] vortex can be fitted to the data. These are also
written in terms of $V _ { s , m a x }$ and $r _ { c } ,$ but the radial distribution function is different and a factor a of an exponential function defines the shape. Expanding the
parameter $\alpha$ to the inclusion of the vortex age $\psi _ { v }$ the
Hamel-Oseen [5] model can be used as well.

$$V _ { s } = V _ { s 0 } \frac { 1 - e ^ { - \mathrm { s r } ^ { 2 } } } { r }$$
$$V _ { s 0 } = \frac { V _ { s , m a x } } { 1 - e ^ { - \alpha } } = \frac { \Gamma _ { v } } { 2 \pi r _ { c } }$$

Vatistas model is used here, since with the shape
parameter $n$ a wide range of swirl shapes can be defined,
covering the Scully vortex $\left( n = 1 \right)$ , the Lamb-Oseen
vortex $\left( n \approx 2 \right)$ , or the Rankine vortex $\left( n = \infty \right)$ . When the
data are cleaned from spurious vectors, mean values of
the flow subtracted and rotated into the vortex axis
system, the distribution of swirl velocities of all vectors is
fitted with the Vatistas model using a least squares error
method. The best fit is performed at a radial extension of
2-3 core radii.
```