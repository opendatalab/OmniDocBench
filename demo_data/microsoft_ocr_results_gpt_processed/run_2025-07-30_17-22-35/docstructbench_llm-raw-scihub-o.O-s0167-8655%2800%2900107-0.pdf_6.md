<!-- PageNumber="254" -->
<!-- PageHeader="A. Siebert / Pattern Recognition Letters 22 (2001) 249-256" -->


Fig. 5. Mag-Lap 2-D feature histograms for invariant representation of image ToolA: (a) 0GC, $8 \times 8$ (b) CGC, $8 \times 8$ (c) 0GC,
$3 2 \times 3 2$ ; (d) CGC, $3 2 \times 3 2$ . The gradient magnitude is along the vertical axis, the Laplacian along the horizontal axis.

![35 35 8 8 30 30 7 7 6 25. 25 6. 5 5 20- 20 4. 4. 15. 15 3. 3. 2- 10- 10 2. 1 1. 5. 5 0 0 0 0 0 0 10 200 200 20 20 400 400 30 40](figures/1.1)


Table 1
Distance matrix for intensity images, $x ^ { 2 }$ metric, $8 \times 8$ bins, $\sigma _ { \mathrm { p r e } } = 0 ^ { \mathrm { a } }$

| $$x ^ { 2 }$$ | Build | WoBA | WoBB | WoBC | WoBD | Cycl | Sand | ToolA | ToolB | ToolC |
| - | - | - | - | - | - | - | - | - | - | - |
| Build | 204.7 | 951.9 | 1915.3 | 1100.7 | 1835.8 | 1692.4 | 1889.2 | 1978.0 | 3546.3 | 2322.3 |
| WoBA | 2018.0 | 490.5 | 1695.2 | 982.4 | 1284.4 | 2488.2 | 2458.4 | 466.6 | 1214.3 | 592.0 |
| WoBB | 4201.7 | 2514.2 | 603.6 | 1993.4 | 1000.8 | 1564.0 | 1825.9 | 1240.0 | 578.6 | 1167.5 |
| WoBC | 1197.9 | 843.8 | 740.2 | 469.7 | 381.7 | 1299.2 | 949.0 | 1040.3 | 1584.1 | 1028.1 |
| WoBD | 4045.1 | 3050.5 | 493.5 | 2246.2 | 1033.4 | 803.2 | 1182.5 | 2003.1 | 1443.4 | 2012.2 |
| Cycl | 983.1 | 1309.7 | 934.9 | 1097.0 | 1158.9 | 399.3 | 490.4 | 1925.1 | 2691.5 | 2238.1 |
| Sand | 1453.0 | 1154.3 | 1339.9 | 737.9 | 1115.1 | 1240.1 | 1037.5 | 1820.1 | 2609.2 | 2133.4 |
| ToolA | 3305.8 | 1398.8 | 1034.2 | 1421.6 | 1000.1 | 2313.6 | 2348.9 | 303.2 | 248.9 | 283.1 |
| ToolB | 6202.4 | 3264.8 | 1643.6 | 2919.5 | 1692.3 | 3351.2 | 3470.5 | 1325.7 | 539.8 | 1029.2 |
| ToolC | 3540.1 | 1668.4 | 1079.5 | 1717.9 | 1232.2 | 2282.5 | 2503.6 | 380.5 | 261.8 | 310.4 |

a

a Minimum distances in bold face.


Table 2
Distance matrix for invariant representations, $x 2$ metric, $8 \times 8$ bins, $\sigma _ { \mathrm { p r e } } = 1 . 0 ^ { \mathrm { a } }$

| $$x ^ { 7 }$$ | Build | WoBA | WoBB | WoBC | WoBD | Cycl | Sand | ToolA | ToolB | ToolC |
| - | - | - | - | - | - | - | - | - | - | - |
| Build | 136.1 | 353.1 | 523.7 | 352.9 | 1340.8 | 647.1 | 1411.8 | 715.5 | 618.7 | 1215.1 |
| WoBA | 613.5 | 57.9 | 236.0 | 249.4 | 345.8 | 168.3 | 482.3 | 144.0 | 141.4 | 395.9 |
| WoBB | 517.8 | 204.0 | 51.6 | 255.3 | 463.1 | 240.7 | 608.5 | 240.7 | 177.7 | 359.4 |
| WoBC | 484.3 | 264.3 | 234.5 | 85.2 | 656.9 | 362.7 | 787.3 | 286.1 | 254.7 | 517.8 |
| WoBD | 1703.0 | 565.1 | 670.5 | 740.2 | 59.7 | 315.8 | 404.0 | 368.5 | 465.3 | 259.6 |
| Cycl | 753.3 | 164.0 | 311.6 | 325.3 | 273.1 | 25.9 | 193.6 | 182.2 | 234.5 | 309.0 |
| Sand | 1834.4 | 587.9 | 939.8 | 920.1 | 402.7 | 268.5 | 60.9 | 559.1 | 731.6 | 691.1 |
| ToolA | 833.8 | 194.9 | 299.0 | 264.4 | 258.4 | 220.2 | 448.8 | 52.8 | 112.2 | 309.2 |
| ToolB | 699.2 | 171.4 | 215.9 | 207.3 | 346.0 | 281.0 | 642.4 | 136.2 | 82.4 | 334.1 |
| ToolC | 1240.5 | 395.4 | 342.1 | 437.3 | 176.5 | 251.8 | 507.9 | 212.2 | 274.0 | 57.5 |

a

1 Minimum distances in bold face.


representation are more equally distributed over
all histogram bins.

The $x ^ { 2 }$ distances for the images in our test
database, for $8 \times 8$ bins, are given in Table 1 for
the intensity images without pre-filtering, and in
Table 2 for the invariant representations with

gentle Gaussian pre-filtering, $\sigma _ { \mathrm { p r e } } = 1 . 0$ . Each row
shows the distances from the given 0GC histo-
grams to the CGC histograms. Note that the
tables are not symmetric. If the $x ^ { 2 }$ value is
smallest on the diagonal, then the query image
has been correctly recognized. The percentage of
