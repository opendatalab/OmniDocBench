<!-- PageHeader="Industrial & Engineering Chemistry Research" -->
<!-- PageHeader="ARTICLE" -->

Figure 5. Sensitivity analysis and SVD results for ternary system.

![0.60 $$\alpha_{390} = 1.50$$ -100 40 $$K_{FA0}$$ -200 $$\alpha_{390} = 11.75$$ $$K_{FB0}$$ 20 -300 0 $$\alpha_{390} = 2.00$$ -400 0 10 20 30 -20 0 10 20 30 0 0.6 -0.1 0.4 $$U_{FA0}$$ -0.2 $$U_{FB0}$$ 0.2 -0.3 0 -0.4 0 10 20 30 -0.2 0 10 20 30 $$N_T$$ $$N_T$$](figures/1.1)

Table 4. Controller Pairing and Parameters for Ternary System

| $$\alpha_{390}$$ | loop | $$K_C$$ | $$\tau_I$$ | action |
| - | - | - | - | - |
| 2.00 | $$T_4 - F_{AO}$$ | 8.29 | 16.76 | direct |
| | $$T_{18} - F_{B0}$$ | 19.54 | 22.57 | reverse |
| 1.75 | $$T_6 - F_{AO}$$ | 5.70 | 39.6 | direct |
| | $$T_{23} - F_{B0}$$ | 11.26 | 11.22 | reverse |
| 1.50 | $$T_9 - F_{AO}$$ | 8.87 | 40.13 | direct |
| | $$T_{29} - F_{B0}$$ | 51.01 | 20.20 | reverse |

increase as the value of $\alpha_{390}$ decreases. However, the offset does not exceed 0.1 mol % even for the case of $\alpha_{390} = 1.50$.

The results of this ternary system differ significantly from those of the quaternary systems in terms of the actions of temperature controllers. The studies on quaternary systems concluded that the two temperature controllers had to have the same action.6 However, dynamically stable results are obtained for this ternary system with temperature controllers having opposite actions. Details of the physical explanation of this situation are given in a recent paper.

3.2. Ternary System with Inert Component. The flowsheet of ternary system with inert is given in Figure 9. This system involves four components. However, one of them is an inert component $I$ in terms of the reaction. Since its volatility is assumed the same as that of the light reactant $A$, it is fed from the fresh feed stream $F_{A0}$ as a mixture with $A$. The other fresh feed stream $F_{BO}$ contains pure reactant $B$. While the heavy product $C$ leaves the column from the bottom, the low-boiling inert $I$ is removed from the distillate without taking part in the reaction. Thus, the column has three zones: a stripping section, a reactive zone, and a rectifying section. It is assumed that the light and heavy fresh feed streams are fed from the bottom and top trays of the reactive zone, respectively.

The main design objective is to obtain the purity of the bottoms product at 98 mol % $C$. On the other hand, the amount of reactants escaping from the distillate stream should also be considered. This is especially important for the light reactant $A$, which has an identical volatility with the inert component $I$.

Thus, a constraint of 3 mol % is defined for the maximum amount of reactants leaving the column from the top. The liquid holdups in the reactive trays are selected as 2000 mols to have reasonable liquid height. The composition of $F_{A0}$ is 50 mol % $A$ and 50 mol % $I$. Kinetic parameters of the ternary system are given in Table 5. The basic design procedure is based on the existing paper in the literature.21

The optimization problem for the ternary system with inert includes five design variables. These are (1) the number of stripping trays $N_S$, (2) the number of reactive trays $N_{RX}$, and (3) the number of rectifying trays $N_B$, (4) the column pressure $P_1$, and (5) the reflux $R$. The objective function is TAC, and the same basis of economics is used as that has been used for the ternary system without inert component.

Table 6 gives the optimum design parameters and economics for the relative volatility cases considered. For the base case of $\alpha_{390} = 2.00$, the optimum operating pressure of the column is 9 bar. The bottoms purity of 98 mol % $C$ is achieved with a column having 7 stripping, 12 reactive, and 7 rectifying trays. The column diameter is 1.00 m with a vapor boilup of 55.06 mol/s. The total capital investment for the column, reboiler, and condenser is $5532.42 \times 10^3$, while the cost of energy is $S237.33 \times 10^3 / \mathrm{yr}$. Assuming a payback period of 3 years, the TAC is $S414.80 \times 10^3 / \mathrm{yr}$. There is a slight decrease in the operating pressure with the decrease of $\alpha_{390}$, but the change is not dramatic. This decrease is reasonable because lower pressure helps the VLE by reducing temperatures and increasing relative volatilities. There is an increase in the optimum number of total trays with the decrease of $\alpha_{390}$. Decrease of $\alpha_{390}$ from 2.00 to 1.75 results in a higher change in the number of separation trays. On the other hand, the increase in the number of reactive trays is more remarkable for the case of $\alpha_{390} = 1.50$. The other design variable reflux $R$ and the vapor boilup $V_S$ increase dramatically as $\alpha_{390}$ declines. Thus, the capital and energy costs get significantly higher as the value of $\alpha_{390}$ decreases.

Figure 10 shows the temperature profiles of three relative volatility cases. There is a sharp temperature profile for the case of $\alpha_{390} = 2.00$. This is especially true for the stripping section. The decrease of the value of $\alpha_{390}$ moderates the sharpness of the temperature profile. The size of the hump in the reactive zone also

<!-- PageNumber="8142" -->
<!-- PageFooter="dx.doi.org/10.1021/ie102256j |Ind. Eng. Chem. Res. 2011, 50, 8138-8152" -->