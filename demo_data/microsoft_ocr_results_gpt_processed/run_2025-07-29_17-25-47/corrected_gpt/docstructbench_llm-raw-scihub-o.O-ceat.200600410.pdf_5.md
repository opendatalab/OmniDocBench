<!-- PageHeader="Chem. Eng. Technol. 2007, 30, No. 9, 1203-1211" -->
<!-- PageHeader="Real-time processes" -->
<!-- PageNumber="1207" -->

Table 1. Considered process variables of the FCCU case study.

| Variable | Description |
|----------|-------------|
| 1        | Flow of wash oil to reactor riser |
| 2        | Flow of fresh feed to reactor riser |
| 3        | Flow of slurry to reactor riser |
| 4        | Temperature of fresh feed entering furnace |
| 5        | Fresh feed temperature to riser |
| 6        | Furnace firebox temperature |
| 7        | Combustion air blower inlet suction flow |
| 8        | Combustion air blower throughput |
| 9        | Combustion air flow rate |
| 10       | Lift air blower suction flow |
| 11       | Lift air blower speed |
| 12       | Lift air blower throughput |
| 13       | Riser temperature |
| 14       | Wet gas compressor suction pressure |
| 15       | Wet gas compressor inlet suction flow |
| 16       | Wet gas flow to vapor recovery unit |
| 17       | Regenerator bed temperature |
| 18       | Stack gas valve position |
| 19       | Regenerator pressure |
| 20       | Standpipe catalyst level |
| 21       | Stack gas O2 concentration |
| 22       | Combustion air blower discharge pressure |
| 23       | Wet gas composition suction valve position |

Figure 2. Scatter plot in original feature space.

![Scatter plot in original feature space](figures/1.1)

Figure 3. Scatter plot in high-dimensional feature space.

![Scatter plot in high-dimensional feature space](figures/1.2)

The dataset, which is generated from simulation studies, in the FCCU process and extracted from the first and second optimal discriminant vector using Fisher discriminant analysis. Then the data was projected to the optimal discriminant vector, which resulted in the generation of a scatter plot of the first and second feature vector in the original space. It can be seen in Fig. 2 that only fault 1 can be differentiated clearly from the normal data and that faults 2 and 3 cannot be differentiated from normal data. The reason for this is that FDA is a linear method in operation. Consequently, it has a poor ability to deal with data which shows complex nonlinear relationships among variables. The scatter plot of the first kernel Fisher feature vector and the second vector via kernel FDA is presented in Fig. 3. It is seen from Fig. 3 that after projecting to the high-dimensional feature space through selecting the appropriate kernel function, the kernel Fisher discriminant method can easily discriminate data that belong to different classes.

The RBF function is used as the selected kernel function, and the parameter \( c \) is selected as 0.8 according to experience, viz:

$$
K \left( x_i, x_j \right) = \exp \left( - \frac{\| x_i - x_j \|^2}{c} \right)
$$

The process disturbances considered are listed in Tab. 2. A 10% loss of combustion air blower capacity was selected for

Table 2. Process disturbances for FCCU.

| Case | Disturbance |
|------|-------------|
| 1    | 10% loss of combustion air blower capacity |
| 2    | 5% degradation in the flow of regenerated catalyst |
| 3    | 5% increase in the coke factor of the feed |
| 4    | 10% decrease in the heat exchanger coefficient of the furnace |
| 5    | 10% increase in fresh feed |
| 6    | 5% decrease in lift air blower speed |
| 7    | 5% increase in friction coefficient of regenerated catalyst |
| 8    | Negative bias of reactor pressure sensor |

<!-- PageFooter="© 2007 WILEY-VCH Verlag GmbH & Co. KGaA, Weinheim" -->
<!-- PageFooter="http://www.cet-journal.com" -->