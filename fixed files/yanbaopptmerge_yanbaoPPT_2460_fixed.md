# 奇点分类（III）

• $\Delta = 0$，$A$ 有两个相同的特征值

$$
P^{-1} A P = \begin{pmatrix} \lambda & 0 \\ 0 & \lambda \end{pmatrix}
$$

微分方程组：
$$
\begin{cases}
\frac{du}{dt} = \lambda u \\
\frac{dv}{dt} = \lambda v
\end{cases}
\quad \Rightarrow \quad
\begin{cases}
u = u_0 e^{\lambda t} \\
v = v_0 e^{\lambda t} \\
\frac{u}{v} = \frac{u_0}{v_0}
\end{cases}
$$

• $\alpha < 0$, $\lambda < 0$  
• $\alpha > 0$, $\lambda > 0$

---

![浙江大学 Zhejiang University](figures/1.1)

**数学建模**

$$
\frac{du}{dt} = P^{-1} A P u
$$

$$
\alpha = \mathrm{tr}(A) = \lambda_1 + \lambda_2
$$

$$
\beta = |A| = \lambda_1 \lambda_2
$$

$$
v \qquad u
$$

![](figures/1.2)

21
