Fig. 2 Test images superimposed: in red the first, in green the second frame (left). The white square indicates the Interrogation Window. On the right the same image with a rectangular artificially saturated area on the first frame
![img-0.jpeg](img-0.jpeg)
![img-1.jpeg](img-1.jpeg)

Fig. 3 Maps of dissimilarity with Lorentzian, sum of squared differences and fast correlation. Dissimilarity are subtracted of the minimum value and normalized by the maximum value. Contours are drawn from 0 to 1 with a step of 0.05 . For reference, the levels
0.7, 0.6 and 0.5 are drawn in red, green, and blue, respectively. The lowest the dissimilarity the darker the background. Abscissa and ordinate represent guessed displacement in the $x$ and $y$ direction, respectively

Fig. 4 Dissimilarity maps on the modified image. Same contour lines and axes as in Fig. 3
![img-2.jpeg](img-2.jpeg)
conservation by spurious pixels (outliers) between (e.g. the white square artificially added in the first frame).

The SSD and cross-correlation are functions defined univocally. Conversely, the Lorentzian depends on a parameter, $\sigma_{\mathrm{e}}$, which tunes how robust the estimator has to be. As a matter of fact, it should equal the amplitude of the expected differences between pixels fulfilling the BCC. The above maps have been computed with a value equal to 26 , that is about one half of the standard deviation of the image gray levels ( $\sigma=43 \pm 0.1$ for both images).

In order to test the sensitivity of the solution on the parameter $\sigma_{\mathrm{e}}$, the dissimilarity map given by the

Lorentzian estimator was computed for six different values of $\sigma_{\mathrm{e}}$, ranging from 2 to 128 ; results are plotted in Fig. 5. If one assumes the level of the second peak as an indication of the signal to noise ratio, one should conclude that the values of 26 is not optimal, since the values from 3 up to 13 behaves slightly better, but the results are more or less similar to those obtained with 26. Further increases of the value deteriorate the $\mathrm{S} / \mathrm{N}$ ratio, but also for $\sigma_{\mathrm{e}}=128$, the Lorentzian estimator works noticeably better than SSD or cross-correlation. These results indicate that the Lorentzian estimator performs well for a wide range of values of the parameter, even though the optimal seems to be at about $1 / 3$ of the