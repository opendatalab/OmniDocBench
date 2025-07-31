<!-- PageNumber="1210" -->
<!-- PageHeader="X. Zhang et al." -->
<!-- PageHeader="Chem. Eng. Technol. 2007, 30, No. 9, 1203-1211" -->


Figure 12. Degree of similarity of case 1 in the historical dataset.

![1 0.9 0.8 0.7 Similar degree 0.6 0.5 0.4 0.3 0.2 0.1 0 1 2 3 4 5 6 7 8 Case 1](figures/1.1)


pose is to verify the efficiency of the PCA plus kernel FDA
method. The results that indicate the time consumed are
shown in Tab. 3. From Tab. 3, it is seen that the proposed
method is competitive with kernel FDA. The computation
time is different with the different numbers of PCs reserved in
PCA. The time consumed becomes longer with the increase of
PCs. Although the entire time consumed owith PCA plus
KFDA is longer than PCA, it is much less than that for the ker-
nel FDA method alone. The results show that if one chooses
the appropriate number of PCs, then the proposed method is
more preferable for real-time process monitoring and fault di-
agnosis.

In order to evaluate the ability of the proposed approach to
identify disturbance, the detection results were classified as 4
levels (A, B, C, and D) and listed as follows:

\- A: The method can detect the occurrence of the disturbance
and the result is excellent.

\- B: The method can detect the occurrence of the disturbance
and the result is clear.

\- C: The method can detect the occurrence of the disturbance
and the result is not very clear.


Table 3. Comparison of the time consumed for fault detection and diagnosis between PCA, KFDA and $P C A + K F D A$ .

| Fault Number | Time consumed (s) | | | | | | |
| | $$\mathrm { P C s } = 8 \left( 6 0 \% \mathrm { v a r i a n c e } \right)$$
$$P C s = 1 5 \left( 9 5 v a r i a n c e \right)$$ | | | | $$P C s = 1 9 \left( 9 9 v a r i a n c e \right)$$ | | |
| | PCA | $$\mathrm { P C A } + \mathrm { K F D A }$$ | PCA | $$\mathrm { P C A } + \mathrm { K F D A }$$ | PCA | $$\mathrm { P C A } + \mathrm { K F D A }$$ | KFDA |
| - | - | - | - | - | - | - | - |
| 1 | 5.2 | 14.1 | 5.4 | 23.7 | 5.5 | 36.2 | 56.3 |
| 2 | 4.7 | 13.9 | 4.8 | 21.2 | 4.8 | 32.1 | 51.7 |
| 3 | 5.0 | 13.4 | 5.1 | 22.1 | 5.0 | 34.4 | 53.6 |
| 4 | 6.0 | 16.8 | 6.3 | 27.1 | 6.1 | 45.2 | 64.3 |
| 5 | 5.5 | 14.7 | 5.7 | 24.6 | 5.5 | 36.8 | 59.5 |
| 6 | 5.1 | 14.1 | 5.2 | 23.9 | 5.1 | 35.1 | 57.4 |
| 7 | 5.1 | 14.9 | 5.3 | 24.2 | 5.2 | 35.8 | 58.9 |
| 8 | 5.8 | 16.2 | 6.1 | 26.5 | 6.0 | 43.9 | 61.5 |


Table 4. Comparison of fault detection ability among PCA, KFDA and $P C A + K F D A$ .

| Fault Number | Detection Results | | | | | | |
| | $$P C s = 8 \left( 6 0 v a r i a n c e \right)$$ | | $$P C s = 1 5 \left( 9 5 v a r i a n c e \right)$$ | | $$P C s = 1 9 \left( 9 9 v a r i a n c e \right)$$ | | |
| | PCA | $$\mathrm { P C A } + \mathrm { K F D A }$$ | PCA | $$\mathrm { P C A } + \mathrm { K F D A }$$ | PCA | $$\mathrm { P C A } + \mathrm { K F D A }$$ | KFDA |
| - | - | - | - | - | - | - | - |
| 1 | C | B | C | A | C | B | B |
| 2 | D | B | C | A | D | A | A |
| 3 | D | B | C | A | C | B | $$B$$ |
| 4 | C | A | B | A | C | A | $$A$$ |
| 5 | C | $$A$$ | B | A | C | A | $$A$$ |
| 6 | B | B | C | B | B | B | B |
| 7 | C | B | C | A | C | B | B |
| 8 | D | B | B | A | C | A | A |


<!-- PageFooter="© 2007 WILEY-VCH Verlag GmbH & Co. KGaA, Weinheim" -->
<!-- PageFooter="http://www.cet-journal.com" -->
