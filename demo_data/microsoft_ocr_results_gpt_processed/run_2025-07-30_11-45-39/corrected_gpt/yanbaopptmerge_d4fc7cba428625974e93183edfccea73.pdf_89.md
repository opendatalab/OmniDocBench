<!-- PageNumber="82" -->
<!-- PageHeader="Chapter 2 | Descriptive Statistics" -->


Table 2.28

| Data | Freq. | Deviations | Deviations2 | (Freq.)(Deviations2) |
| - | - | - | - | - |
| $$X$$ | $$f$$ | $$\left( x - \bar { x } \right)$$ | $$\left( x - \bar { x } \right) ^ { 2 }$$ | $$\left( f \right) \left( x - \sqrt { x } \right) ^ { 2 }$$ |
| 9 | 1 | $$9 - 10.525 = -1.525$$ | $$\left( -1.525 \right) ^ { 2 } = 2.325625$$ | $$1 \times 2.325625 = 2.325625$$ |
| 9.5 | 2 | $$9.5 - 10.525 = -1.025$$ | $$\left( -1.025 \right) ^ { 2 } = 1.050625$$ | $$2 \times 1.050625 = 2.101250$$ |
| 10 | 4 | $$10 - 10.525 = -0.525$$ | $$\left( -0.525 \right) ^ { 2 } = 0.275625$$ | $$4 \times 0.275625 = 1.1025$$ |
| 10.5 | 4 | $$10.5 - 10.525 = -0.025$$ | $$\left( -0.025 \right) ^ { 2 } = 0.000625$$ | $$4 \times 0.000625 = 0.0025$$ |
| 11 | 6 | $$11 - 10.525 = 0.475$$ | $$\left( 0.475 \right) ^ { 2 } = 0.225625$$ | $$6 \times 0.225625 = 1.35375$$ |
| 11.5 | 3 | $$11.5 - 10.525 = 0.975$$ | $$\left( 0.975 \right) ^ { 2 } = 0.950625$$ | $$3 \times 0.950625 = 2.851875$$ |
| | | | | The total is 9.7375 |


The sample variance, $s ^ { 2 }$ , is equal to the sum of the last column (9.7375) divided by the total number of data values
minus one $\left( 20 - 1 \right)$ :

$$s ^ { 2 } = \frac { 9.7375 } { 20 - 1 } = 0.5125$$

The sample standard deviation s is equal to the square root of the sample variance:

$s = \sqrt { 0.5125 } = 0.715891$ , which is rounded to two decimal places, $s = 0.72$ .


# Explanation of the standard deviation calculation shown in the table

The deviations show how spread out the data are about the mean. The data value 11.5 is farther from the mean than is the
data value 11 which is indicated by the deviations 0.97 and 0.47. A positive deviation occurs when the data value is greater
than the mean, whereas a negative deviation occurs when the data value is less than the mean. The deviation is -1.525 for
the data value nine. If you add the deviations, the sum is always zero. (For Example 2.29, there are $n = 20$ deviations.)
So you cannot simply add the deviations to get the spread of the data. By squaring the deviations, you make them positive
numbers, and the sum will also be positive. The variance, then, is the average squared deviation. By squaring the deviations
we are placing an extreme penalty on observations that are far from the mean; these observations get greater weight in the
calculations of the variance. We will see later on that the variance (standard deviation) plays the critical role in determining
our conclusions in inferential statistics. We can begin now by using the standard deviation as a measure of "unusualness."
"How did you do on the test?" "Terrific! Two standard deviations above the mean." This, we will see, is an unusually good
exam grade.

The variance is a squared measure and does not have the same units as the data. Taking the square root solves the problem.
The standard deviation measures the spread in the same units as the data.

Notice that instead of dividing by $n = 20$ , the calculation divided by $n - 1 = 20 - 1 = 19$ because the data is a sample. For
the sample variance, we divide by the sample size minus one $\left( n - 1 \right)$ . Why not divide by $n?$ The answer has to do with
the population variance. The sample variance is an estimate of the population variance. This estimate requires us to use
an estimate of the population mean rather than the actual population mean. Based on the theoretical mathematics that lies
behind these calculations, dividing by $\left( n - 1 \right)$ gives a better estimate of the population variance.

The standard deviation, $s$ or $\sigma ,$ is either zero or larger than zero. Describing the data with reference to the spread is
called "variability". The variability in data depends upon the method by which the outcomes are obtained; for example, by
measuring or by random sampling. When the standard deviation is zero, there is no spread; that is, the all the data values are
equal to each other. The standard deviation is small when the data are all concentrated close to the mean, and is larger when
the data values show more variation from the mean. When the standard deviation is a lot larger than zero, the data values
are very spread out about the mean; outliers can make $s$ or $\sigma$ very large.

<!-- PageFooter="This OpenStax book is available for free at http://cnx.org/content/col11776/1.33" -->
```