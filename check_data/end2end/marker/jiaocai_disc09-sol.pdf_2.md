3 1.3 2
// Assume n holds the length of arr double fast_product(double *arr, int n) {
3 double product = 1;
\#pragma omp parallel for 4 5 for (int i = 0; i < n; i++) {
product *= arr[i];
6 7
}
8 return product; 9
}
(a) What is wrong with this code?

The code has the shared variable product.

(b) Fix the code using \#pragma omp critical 1 double fast_product(double *arr, inten) {
2 3 double product = 1;
\#pragma omp parallel for 4 for (int i = 0; i < n; i++) {
5 6
\#pragma omp critical product *= arr[i];
7
 }
8 return product;
 }
9
(c) Fix the code using \#pragma omp reduction(operation: var).

1 double fast_product(double *arr, int n) {
2 double product = 1; 3 4
\#pragma omp parallel for reduction(*: product)
for (intli = 0; i < n; i++) {
5 product *= arr[i];
6
}
7 return product; 8
}

## 2 Logic Gates

2.1 Label the following logic gates:

![0_image_0.png](0_image_0.png)

NOT, AND, OR, XOR, NAND, NOR, XNOR
2.2

![0_image_1.png](0_image_1.png)

Convert the following to boolean expressions:
(a)  NAND