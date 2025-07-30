## 2024 年全国硕士研究生招生考试试题与答案（数学一）

## 数 学

本试卷共 4 页， 22 题。全卷满分 150 分，考试用时 120 分钟。

## 注意事项:

1. 答卷前，考生务必将自己的姓名，准考证号填写在答题卡上。
2. 回答选择题时，用铅笔把答题卡上对应题目的答案标号涂黑，写在本试卷上无效。
3. 考试结束后，将本试卷和答题卡一并交回。
4. 本试卷由 kmath.cn 自动生成。

| 得分 |  |
| :-- | :-- |
| 问卷人 |  |

一、单选题: 本题共 10 小题, 每小题 5 分, 共 40 分。在每小题抢出的四个选项中, 只有一项是符合题目要求的。

1. 已知函数 $f(x)=\int_{0}^{x} e^{\cos x} d t, g(x)=\int_{0}^{2 \pi x} e^{t^{2}} d t$, 则
A. $f(x)$ 是奇函数, $g(x)$ 是偶函数
B. $f(x)$ 是偶函数, $g(x)$ 是奇函数
C. $f(x) \Rightarrow g(x)$ 均为奇函数
D. $f(x) \Rightarrow g(x)$ 均为周期函数
[答案]:C [解析]:【解析】由于 $e^{\cos x}$ 是偶函数, 所以 $f(x)=\int_{0}^{x} e^{\cos x} d t$ 是奇函数, 又 $g^{\prime}(x)=e^{(\sin x)^{2}} \cos x$ 是偶函数, 所以 $g(x)$ 是奇函数。故选 C.
2. 设 $P=P(x, y, z) \square Q=Q(x, y, z)$ 均为连续函数, $\sum$ 为曲面 $Z=\sqrt{1-x^{2}-y^{2}}(x \leqslant 0, y \geqslant 0)$ 的上侧,则 $\iint_{E} P d y d z+Q d z d x=$
A. $\iint_{E}\left(\frac{x}{z} P+\frac{y}{z} Q\right) d x d y$
B. $\iint_{E}\left(-\frac{x}{z} P+\frac{y}{z} Q\right) d x d y$
C. $\iint_{E}\left(\frac{x}{z} P-\frac{y}{z} Q\right) d x d y$
D. $\iint_{E}\left(-\frac{x}{z} P-\frac{y}{z} Q\right) d x d y$
[答案]:A [解析]:【解析】转换投影法, $z=\sqrt{1-x^{2}-y^{2}}: \frac{\partial z}{\partial x}=\frac{x}{z}: \frac{\partial z}{\partial y}=-\frac{y}{z}$

$$
\iint_{E} P d y d z+Q d z d x=\iint_{E}\left(\frac{x}{z} P+\frac{y}{z} Q\right) d x d y
$$

故选 A.
3. 已知幂级数 $\sum_{n=0}^{\infty} a_{n} x^{n}$ 的和函数为 $\ln (2+x)$, 则 $\sum_{n=0}^{\infty} n a_{2 n}=$
A. $-\frac{1}{6}$
B. $-\frac{1}{3}$
C. $\frac{1}{6}$
D. $\frac{1}{3}$
[答案]:A [解析]:【解析】方法 $1: \ln (2+x)=\ln 2\left(1+\frac{1}{2} x\right)=\ln 2+\ln \left(1+\frac{1}{2} x\right)$

$$
=\ln 2+\sum_{n=1}^{\infty}(-1)^{n-1} \frac{\left(\frac{1}{2} x\right)^{n}}{n}
$$

所以, $a_{n}= \begin{cases}\ln 2, & n=0 \\ (-1)^{n-1} \frac{1}{n 2^{n}}, & n>0\end{cases} \operatorname{ch} n>0, a_{2 n}=-\frac{1}{2 n \cdot 2^{2 n}}$, 所以, $\sum_{n=0}^{\infty} n a_{2 n}=\sum_{n=1}^{\infty} n a_{2 n}=$ $\sum_{n=1}^{\infty} n \cdot\left(-\frac{1}{2 n \cdot 2^{2 n}}\right)=-\sum_{n=1}^{\infty} \frac{1}{2^{2 n+1}}=-\frac{\left(\frac{1}{2}\right)^{2}}{1-\frac{1}{2}}=-\frac{1}{6}$ 故选 A. 方法 2 :

$$
\begin{gathered}
{[\ln (2+x)]^{r}}=\frac{1}{2+x}=\frac{1}{2\left(1+\frac{x}{2}\right)}=\frac{1}{2} \sum_{n=0}^{\infty}(-1)^{n}\left(\frac{x}{2}\right)^{n} \\
\ln (2+x)=\sum_{n=0}^{\infty}(-1)^{n} \frac{\left(\frac{1}{2} x\right)^{n+1}}{n+1}+C=\sum_{n=1}^{\infty}(-1)^{n-1} \frac{\left(\frac{1}{2} x\right)^{n}}{n}+C \\
S(0)=C=\ln (2+0)=\ln 2
\end{gathered}
$$

所以, $a_{n}= \begin{cases}\ln 2, & n=0 \\ (-1)^{n-1} \frac{1}{n 2^{n}}, & n>0\end{cases}$
所以, $\sum_{n=0}^{\infty} n a_{2 n}=\sum_{n=1}^{\infty} n a_{2 n}=\sum_{n=1}^{\infty} n \cdot\left(-\frac{1}{2 n \cdot 2^{2 n}}\right)=-\sum_{n=1}^{\infty} \frac{1}{2^{2 n+1}}=-\frac{\left(\frac{1}{2}\right)^{2}}{1-\frac{1}{2}}=\frac{1}{6}$ 故选 A .
4. 设函数 $f(x)$ 在区间 $(-1,1)$ 上有定义, 且 $\lim _{x \rightarrow 0} f(x)=0$, 则
A. 当 $\lim _{x \rightarrow 0} \frac{f(x)}{x}=m$ 时, $f^{\prime}(0)=m$
B. 当 $f^{\prime}(0)=m$ 时, $\lim _{x \rightarrow 0} \frac{f(x)}{x}=m$
C. 当 $\lim _{x \rightarrow 0} f^{\prime}(x)=m$ 时, $f^{\prime}(0)=m$
D. 当 $f^{\prime}(0)=m$ 时, $\lim _{x \rightarrow 0} f^{\prime}(x)=m$
[答案]:B [解析]:【解析】因为 $f^{\prime}(0)=m$, 所以 $f(x)$ 在 $x=0$ 处连续, 从而 $\lim _{x \rightarrow 0} f(x)=f(0)=0$, 所以 $\lim _{x \rightarrow 0} \frac{f(x)}{x}=\lim _{x \rightarrow 0} \frac{f(x)-f(0)}{x-0}=m$, 故选 B.

对于 A 选项, $\lim _{x \rightarrow 0} \frac{f(x)}{x}=m$, 推不出来 $f^{\prime}(0)=m$; 对于 C 选项, $f^{\prime}(x)$ 在 $x=0$ 处不一定连续; 对于 D 选项, $f^{\prime}(x)$ 在 $x=0$ 处根据未必存在。
5. 在空间直角坐标系 $O-x y z$ 中, 三张平面 $\pi_{i}: a_{i} x+b_{i} y+c_{i} z=d_{i}(i=1,2,3)$ 的位置关系如图所示,记 $\alpha_{i}=\left(a_{i}, b_{i}, c_{i}, d_{i}\right)$, 若 $r\left(\begin{array}{c}\alpha_{i} \\ \alpha_{2} \\ \alpha_{3}\end{array}\right)=m, r\left(\begin{array}{c}\beta_{1} \\ \beta_{2} \\ \beta_{3}\end{array}\right)=n$, 则
![img-0.jpeg](img-0.jpeg)
A. $m=1, n=2$
B. $m=n=2$
C. $m=2, n=3$
D. $m=n=3$

数学试题第 2 页（共 10 页）