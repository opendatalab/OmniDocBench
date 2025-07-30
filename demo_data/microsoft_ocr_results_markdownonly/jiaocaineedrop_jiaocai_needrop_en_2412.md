设 $u \left( x \right) = \ln \left( x + 1 \right) - x$ ,则 $u ^ { \prime } \left( x \right) = \frac { 1 } { x + 1 } - 1 = \frac { - x } { x + 1 }$ ,

所以当- $1 < x < 0$ 时, $u ^ { \prime } \left( x \right) > 0$ ;当 $x > 0$ 时, $u ^ { \prime } \left( x \right) < 0$ ,
所以 $u \left( x \right)$ 在 $\left( - \quad 1 , 0 \right)$ 上为增函数,在 $\left( 0 , + \infty \right)$ 上为减函数,

故 $u \left( x \right) _ { \max } = u \left( 0 \right) = 0$ ,所以 $\ln \left( x + 1 \right) \leq x$ 成立.

由上还不等式可得,当t $> 1$ 时, $\ln \left( 1 + \frac { 1 } { t } \right) \leq \frac { 1 } { t } < \frac { 2 } { t + 1 }$ ,故 $S ^ { \prime } \left( t \right) < 0$ 恒成立,
故 $S \left( t \right)$ 在 $\left( 1 , + \infty \right)$ 上为减函数,则 $S \left( t \right) < S \left( 1 \right) = 0$ ,
所以 $\left( t - 1 \right) \ln \left( t + 1 \right) - t \ln t < 0$ 成立,即 $x _ { 1 } + x _ { 2 } < e$ 成立.

综上所述, $\ln \left( a + b \right) < \ln \left( a b \right) + 1$ .


# 核心考点五:极最值问题


## 【规律方法】

利用导数求函数的极最值问题. 解题方法是利用导函数与单调性关系确定单调区间,从而求得极最
值. 只是对含有参数的极最值问题,需要对导函数进行二次讨论,对导函数或其中部分函数再一次求导,
确定单调性,零点的存在性及唯一性等,由于零点的存在性与参数有关,因此对函数的极最值又需引入新
函数,对新函数再用导数进行求值、证明等操作.


## 【典型例题】

例14.(2023春·江西鹰潭·高三贵溪市实验中学校考阶段练习)已知函数 $f \left( x \right) = \frac { 1 } { 3 } x ^ { 3 } - a x + a , a \in R$ .

(1)当 $a = - \quad 1$ ,求 $f \left( x \right)$ 在 $\left[ - \quad 2 , 2 \right]$ 上的最值;

(2)讨论 $f \left( x \right)$ 的极值点的个数.

【解析】(1)当 $a = - \quad 1$ 时, $f \left( x \right) = \frac { 1 } { 3 } x ^ { 3 } + x - 1 , \quad x \in \left[ - 2 , 2 \right]$

$f ^ { \prime } \left( x \right) = x ^ { 2 } + 1 > 0$ ,故 $f \left( x \right)$ 在[-2,2]上单调递增,

$$: : f \left( x \right) _ { \min } = f \left( - 2 \right) = - \frac { 1 7 } { 3 } , \quad : f \left( x \right) _ { \max } = f \left( 2 \right) = \frac { 1 1 } { 3 } .$$

(2) $f ^ { ^ { \prime } } \left( x \right) = x ^ { 2 } - a$ ,

1当 $a \leqslant 0$ 时, $f ^ { \prime } \left( x \right) \geq 0$ 恒成立,此时 $f \left( x \right)$ 在R上单调递增,不存在极值点.

2当 $a > 0$ 时,令 $f ^ { \prime } \left( x \right) > 0$ ,即 $x ^ { 2 } - a > 0$ ,解得: $x < - \sqrt { a }$ 或 $x > \sqrt { a }$ ,

令 $f ^ { \prime } \left( x \right) < 0$ ,即 $x ^ { 2 } - a < 0$ ,解得 $x \in \left( - \sqrt { a } , \sqrt { a } \right)$

故此时 $f \left( x \right)$ 在 $\left( - \infty , - \sqrt { a } \right)$ 递增,在 $\left( - \sqrt { a } , \sqrt { a } \right)$ 递减,在 $\left( \sqrt { a } , + \infty \right)$ 递增,
所以 $f \left( x \right)$ 在 $x = - \sqrt { a }$ 时取得极大值,在 $x = \sqrt { a }$ 时取得极小值,故此时极值点个数为2,
综上所述: $a \leqslant 0$ 时, $f \left( x \right)$ 无极值点,

<!-- PageNumber="32 / 75" -->
