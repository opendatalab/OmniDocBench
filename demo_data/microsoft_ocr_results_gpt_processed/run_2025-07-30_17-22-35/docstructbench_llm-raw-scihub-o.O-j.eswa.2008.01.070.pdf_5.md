<!-- PageNumber="2941" -->
<!-- PageHeader="O. López-Ortega, I. Villar-Medina / Expert Systems with Applications 36 (2009) 2937-2946" -->


| INPUTS | | | | | OUTPUT |
| RAW MATERIAL FAMILY | NUMBER OF TINTS | RES (DPI) | FINISHING TYPE | NUMBER OF TOOLS | MACHINE |
| - | - | - | - | - | - |
| FABRIC | 0 | N.E. | N.E. | 1 | 830 |
| FABRIC | 0 | 280 | N.E. | 1 | 830 |
| FABRIC | 1 | 280 | N.E. | 1 | 830 |
| FABRIC | 2 | 360 | N.E. | 1 | 830 |
| FABRIC | 3 | 360 | N.E. | 1 | 830 |
| FABRIC | 3 | 400 | LAMINATED | 1 | 2200 |
| FABRIC | 3 | 400 | LAMINATED | 2 | NILPETER |
| FABRIC | 3 | 400 | LAMINATED | 2 | NILPETER |
| FABRIC | 4 | 700 | N.E. | 2 | 2200 |
| FABRIC | 4 | 700 | N.E. | 2 | 2200 |
| FABRIC | 4 | 700 | N.E. | 2 | 2200 |
| FABRIC | 7 | 800 | LAMINATED | 2 | NILPETER |
| FABRIC | 7 | 800 | N.E. | 2 | NILPETER |
| FABRIC | 7 | 800 | N.E. | 1 | NILPETER |
| CARDBOARD | 0 | 280 | N.E | 1 | 830 |
| CARDBOARD | 1 | 360 | N.E. | 1 | 830 |
| CARDBOARD | 3 | 360 | N.E. | 1 | 830 |
| CARDBOARD | 4 | 500 | LAMINATED | 1 | 2200 |
| CARDBOARD | 4 | 360 | N.E. | 1 | 2200 |
| CARDBOARD | 5 | 600 | LAMINATED | 1 | 2200 |
| CARDBOARD | 6 | 700 | N.E. | 2 | NILPETER |
| CARDBOARD | 5 | 800 | N.E. | 3 | NILPETER |
| CARDBOARD | 6 | 700 | LAMINATED | 2 | NILPETER |
| CARDBOARD | 5 | 800 | LAMINATED | 2 | NILPETER |
| KIMDURA | 0 | 360 | N.E. | 1 | 2200 |
| KIMDURA | 1 | 400 | LAMINATED | 1 | 2200 |
| KIMDURA | 1 | 400 | LAMINATED | 2 | 2200 |
| KIMDURA | 1 | 400 | LAMINATED | 1 | 2200 |
| KIMDURA | 5 | 360 | N.E. | 1 | NILPETER |
| KIMDURA | 6 | 360 | N.E. | 1 | NILPETER |
| BOPP | 0 | 280 | N.E. | 1 | 830 |
| BOPP | 1 | 360 | LAMINATED | 1 | 830 |
| BOPP | 3 | 400 | N.E. | 1 | 2200 |
| BOPP | 3 | 400 | LAMINATED | 1 | 2200 |
| BOPP | 5 | 500 | N.E. | 1 | 2200 |
| BOPP | 6 | 700 | N.E. | 1 | 2200 |
| BOPP | 7 | 800 | N.E. | 2 | NILPETER |
| PAPER | 0 | 280 | N.E. | 1 | 830 |
| PAPER | 0 | 280 | N.E. | 1 | 830 |
| PAPER | 1 | 360 | N.E. | 1 | 830 |
| PAPER | 2 | 360 | N.E. | 1 | 830 |
| PAPER | 3 | 500 | N.E. | 1 | 2200 |
| PAPER | 3 | 600 | SULFATED | 1 | 2200 |
| PAPER | 3 | 700 | LAMINATED | 2 | 2200 |
| PAPER | 3 | 600 | LAMINATED | 2 | 2200 |
| PAPER | 6 | 360 | LAMINATED | 1 | NILPETER |
| PAPER | 5 | 700 | N.E. | 2 | NILPETER |
| PAPER | 6 | 800 | N.E. | 3 | NILPETER |
| OTHER | 4 | 500 | N.E. | 3 | NILPETER |


Fig. 2. The training matrix.

as input 1 of the training matrix has six different values, six
processing units are built. However, the actual value is rep-
resented by a string, which is not a suitable input type for
the FANN. Thus, such values are converted to a stream of
O's and I's. Table 1 illustrates the codification for the raw
material family.

The prior codification is necessary because FANNs only
handle values within the closed interval [0, 1]. Therefore,
the actual input and output values that the net receives
and obtains are 0's and 1's. This codification-decodifica-
tion is done by the encoder class attached to the machine
agent (see Fig. 5). Therefore, the FANN has six processing
units in the input layer, which are in charge of dealing
exclusively with the raw material family. The totality of dis-
crete values contained in the input and output sets were


Table 1
Codification of the raw material family set

| Input stream | | | | | | Raw material family |
| - | - | - | - | - | - | - |
| 0 0 | | 0 | 0 | 0 | 1 | Paper |
| 0 0 | | 0 | 0 | 1 | 0 | Fabric |
| 0 0 | | 0 | 1 | 0 | 0 | Kimdura |
| 0 0 | | 1 | 0 | 0 | 0 | Cardboard |
| 0 1 | | 0 | 0 | 0 | 0 | BOPP |
| 1 0 | | 0 | 0 | 0 | 0 | Other |


codified in a similar way. Tables 2-6 show the resultant
codification.

Consequently, the number of processing units in the
input layer of the FANN equals the number of codified
input values. For this case, 25 processing units in the input