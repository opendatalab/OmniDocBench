<!-- PageNumber="283" -->


Fig. 2 Test images
right the same image with a
area on the first frame

![Lorentzian SSD Fast Correlation 15 15 15 10 10 10 5 5 5 0 0 0 -5 -5 5 -10 -10 -10 -15 -15 -15 -10 0 10 -10 0 10 -10 0 10](figures/1.1)


Fig. 3 Maps of dissimilarity with Lorentzian, sum of squared
differences and fast correlation. Dissimilarity are subtracted of the
minimum value and normalized by the maximum value. Contours
are drawn from 0 to 1 with a step of 0.05. For reference, the levels

0.7, 0.6 and 0.5 are drawn in red, green, and blue, respectively. The
lowest the dissimilarity the darker the background. Abscissa and
ordinate represent guessed displacement in the $x$ and $| \mathcal{V} |$ direction,
respectively

Fig. 4 Dissimilarity maps on
the modified image. Same
contour lines and axes as in
Fig. 3

![Lorentzian SSD Fast Correlation 15 15 15 10 10 10 5 5 5 0 0 0 -5 -5 5 -10 -10 -10 -15 -15 -10 0 10 -10 0 10 -15 -10 0 10](figures/1.2)


conservation by spurious pixels (outliers) between (e.g.
the white square artificially added in the first frame).

The SSD and cross-correlation are functions defined
univocally. Conversely, the Lorentzian depends on a
parameter, $\sigma _ { \mathrm { e } } ,$ which tunes how robust the estimator has
to be. As a matter of fact, it should equal the amplitude
of the expected differences between pixels fulfilling the
BCC. The above maps have been computed with a value
equal to 26, that is about one half of the standard
deviation of the image gray levels $\left( \sigma = 43 \pm 0.1 \right.$ for
both images).

In order to test the sensitivity of the solution on
the parameter $\sigma _ { \mathrm { e } }$ , the dissimilarity map given by the

Lorentzian estimator was computed for six different
values of $\sigma _ { \mathrm { e } } ,$ ranging from 2 to 128; results are plotted in
Fig. 5. If one assumes the level of the second peak as an
indication of the signal to noise ratio, one should con-
clude that the values of 26 is not optimal, since the
values from 3 up to 13 behaves slightly better, but the
results are more or less similar to those obtained with 26.
Further increases of the value deteriorate the $S / N$ ratio,
but also for $\sigma _ { e } = 128$ , the Lorentzian estimator works
noticeably better than SSD or cross-correlation. These
results indicate that the Lorentzian estimator performs
well for a wide range of values of the parameter, even
though the optimal seems to be at about $1 / 3$ of the

superimposed: in red the first, in
green the second frame (left).
The white square indicates the
Interrogation Window. On the
rectangular artificially saturated