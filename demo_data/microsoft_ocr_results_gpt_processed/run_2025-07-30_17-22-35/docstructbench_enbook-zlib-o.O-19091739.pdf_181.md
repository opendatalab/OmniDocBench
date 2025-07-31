<!-- PageNumber="819" -->
<!-- PageHeader="CHAPTER 29 MAGNETIC FIELDS" -->

Example 29.1 cont.

Model We are asked to find the magnetic field due to a simple current distribution, so this
example is a typical problem for which the Biot-Savart law is appropriate. We must find
the field contribution from a small element of current and then integrate over the current
distribution from $\theta _ { 1 }$ to $\theta _ { 2}$, as shown in Figure 29.3b.

Analyse Let's start by considering a length element $d \overrightarrow { \mathrm { s } }$ located a distance r from $P .$ The
direction of the magnetic field at point $P$ due to the current in this element is out of the
page because $d \overrightarrow { \mathrm { s } } \times \widehat { \mathrm { r } }$ is out of the page. In fact, because all the current elements $I d \overrightarrow { s }$ lie in
the plane of the page, they all produce a magnetic field directed out of the page at point $P .$
Therefore, the direction of the magnetic field at point $P$ is out of the page and we need only
find the magnitude of the field. We place the origin at $O$ and let point $P$ be along the positive
$y$ axis, with $\bar { k }$ being a unit vector pointing out of the page.

From the geometry in Figure 29.3a, we can see that the angle between the vectors $d s$ and $\overrightarrow { \mathrm { r } }$
is $\left( \frac { \pi } { 2 } - \theta \right)$ radians.

Evaluate the cross product in the Biot-Savart law:

$$d \bar { s } \times \widehat { \mathrm { r } } = | d \bar { \mathrm { s } } \times \widehat { \mathrm { r } } | \widehat { \mathrm { k } } = \left[ d x \sin \left( \frac { \pi } { 2 } - \theta \right) \right] \widehat { \mathrm { k } } = \left( d x \cos \theta \right) \widehat { \mathrm { k } }$$

Substitute into Equation 29.1:

$$d \overrightarrow { B } = \left( d B \right) \widehat { k } = \frac { \mu _ { _ { 0 } } I } { 4 \pi } \frac { d x \cos \theta } { r ^ { 2 } } \widehat { k }$$
(1)

From the geometry in Figure 29.3a, express $r$ in terms of $\theta$ :

$$r = \frac { a } { \cos \theta }$$
(2)

Notice that tan $\theta = - x / a$ from the right triangle in Figure 29.3a (the negative sign is necessary because $d \overrightarrow { s }$ is located at a
negative value of $x$ and solve for $x$ :

$$x = - a \tan \theta$$

Find the differential $d x$ :

$$d x = - a \sec ^ { 2 } \theta d \theta = - \frac { a d \theta } { \cos ^ { 2 } \theta }$$
(3)

Substitute Equations (2) and (3) into the magnitude of the field from Equation (1):

$$d B = - \frac { \mu _ { 0 } I } { 4 \pi } \left( \frac { a d \theta } { \cos ^ { 2 } \theta } \right) \left( \frac { \cos ^ { 2 } \theta } { a ^ { 2 } } \right) \cos \theta = - \frac { \mu _ { 0 } I } { 4 \pi a } \cos \theta d \theta$$
(4)

Integrate Equation (4) over all length elements on the wire, where the subtending angles range from $\theta_1$ to $\theta_2$ as defined in
Figure 29.3b:

$$B = - \frac { \mu _ { 0 } I } { 4 \pi a } \int _ { \theta _ { 1 } } ^ { \theta _ { 2 } } \cos \theta d \theta = \frac { \mu _ { 0 } I } { 4 \pi a } \left( \sin \theta _ { 1 } - \sin \theta _ { 2 } \right)$$
(29.4)

Check the dimensions, noting that the quantity in brackets is dimensionless:

$$\left. \left[ \mathrm { M Q } ^ { - 1 } \mathrm { T } ^ { - 1 } \right] = \left[ \mathrm { M L Q } ^ { - 2 } \right] \left[ \mathrm { Q T } ^ { - 1 } \right] / \left[ \mathrm { L } \right] = \left[ \mathrm { M Q } ^ { - 1 } \mathrm { T } ^ { - 1 } \right] \stackrel { \left( \right. } { \mathcal{Q} } \right)$$

(B) Find an expression for the field at a point near a very long current-carrying wire.


# Solution

We can use Equation 29.4 to find the magnetic field of any straight current-carrying wire if we know the geometry and
hence the angles $\theta ,$ and $\theta _ { 2 }$ . If the wire in Figure 29.3b becomes infinitely long, we see that $\theta _ { 1 } = \pi / 2$ and $\theta _ { 2 } = - \pi / 2$ for


![$$| d \overrightarrow { \mathrm { s } } | = d x$$ $$\mathfrak{M}$$ $$P$$ 1 $${ } ^ { \prime } \widetilde { \theta }$$ $$r$$ $$a$$ $$\widehat { \mathrm { r } }$$ $$| \mathfrak{X} |$$ $$d \overrightarrow { \mathrm { s } }$$ $$0$$ $$I$$ a](figures/1.1)


$$y$$

$$P$$

$$\theta _ { 1 }$$

$$\theta _ { 2 }$$

$$X$$


Figure 29.3
(Example 29.1) (a) A thin,
straight wire carrying a
current I (b) The angles $\theta _ { 1 }$ and
$\theta _ { 2 }$ are used for determining
the net field.

![b](figures/1.2)


<!-- PageFooter="Copyright 2017 Cengage Learning. All Rights Reserved. May not be copied, scanned, or duplicated, in whole or in part. WCN 02-300" -->