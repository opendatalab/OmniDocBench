<!-- PageHeader="封 座位号" -->

密

不

考场号

订
装
准考证号

卷

此

姓名

# 2024年全国硕士研究生招生考试试题与答案(数学一)

# 数学

本试卷共4页,22题. 全卷满分150分,考试用时120分钟.

注意事项:

1. 答卷前,考生务必将自己的姓名、准考证号填写在答题卡上.

2. 回答选择题时,用铅笔把答题卡上对应题目的答案标号涂黑,写在本试卷上无效.

3. 考试结束后,将本试卷和答题卡一并交回.

4. 本试卷由 kmath.cn 自动生成.

| 得分 | |
| --- | --- |
| 阅卷人 | |

一、单选题:本题共10小题,每小题5分,共40分.在每小题给出的四个选项中,只有一项是符合题目要求的.

1. 已知函数 $f(x) = \int_{0}^{x} e^{\cos t} \, dt$, $g(x) = \int_{0}^{\sin x} e^{t^2} \, dt$, 则

    A. $f(x)$ 是奇函数, $g(x)$ 是偶函数

    B. $f(x)$ 是偶函数, $g(x)$ 是奇函数

    C. $f(x)$ 和 $g(x)$ 均为奇函数

    D. $f(x)$ 和 $g(x)$ 均为周期函数

    [答案]: C

    [解析]: 由于 $e^{\cos t}$ 是偶函数,所以 $f(x) = \int_{0}^{x} e^{\cos t} \, dt$ 是奇函数, $g'(x) = e^{(\sin x)^2} \cos x$ 是偶函数,所以 $g(x)$ 是奇函数. 故选C.

2. 设 $P = P(x, y, z)$ 和 $Q = Q(x, y, z)$ 均为连续函数, $\Sigma$ 为曲面 $z = \sqrt{1 - x^2 - y^2}$ ( $x \leqslant 0$, $y \geqslant 0$ ) 的上侧, 则 $\iint_{\Sigma} P \, dy \, dz + Q \, dz \, dx =$

    A. $\iint_{\Sigma} \left( \frac{x}{z} P + \frac{y}{z} Q \right) \, dx \, dy$

    B. $\iint_{\Sigma} \left( -\frac{x}{z} P + \frac{y}{z} Q \right) \, dx \, dy$

    C. $\iint_{\Sigma} \left( \frac{x}{z} P - \frac{y}{z} Q \right) \, dx \, dy$

    D. $\iint_{\Sigma} \left( -\frac{x}{z} P - \frac{y}{z} Q \right) \, dx \, dy$

    [答案]: A

    [解析]: 转换投影法, $z = \sqrt{1 - x^2 - y^2}$, $\frac{\partial z}{\partial x} = -\frac{x}{z}$, $\frac{\partial z}{\partial y} = -\frac{y}{z}$

    $$\iint_{\Sigma} P \, dy \, dz + Q \, dz \, dx = \iint_{\Sigma} \left( \frac{x}{z} P + \frac{y}{z} Q \right) \, dx \, dy$$

    故选A.

3. 已知幂级数 $\sum_{n=0}^{\infty} a_n x^n$ 的和函数为 $\ln(2 + x)$, 则 $\sum_{n=0}^{\infty} n a_{2n} =$

    A. $-\frac{1}{6}$

    B. $-\frac{1}{3}$

    C. $\frac{1}{6}$

    D. $\frac{1}{3}$

    [答案]: A

    [解析]: 方法1: $\ln(2 + x) = \ln 2 + \ln \left( 1 + \frac{1}{2} x \right) = \ln 2 + \sum_{n=1}^{\infty} (-1)^{n-1} \frac{\left( \frac{1}{2} x \right)^n}{n}$

    所以, $a_n = \left\{ \begin{array}{ll} \ln 2, & n = 0 \\ (-1)^{n-1} \frac{1}{n 2^n}, & n > 0 \end{array} \right.$

    当 $n > 0$, $a_{2n} = -\frac{1}{2n \cdot 2^{2n}}$, 所以 $\sum_{n=0}^{\infty} n a_{2n} = \sum_{n=1}^{\infty} n a_{2n} = \sum_{n=1}^{\infty} n \cdot \left( -\frac{1}{2n \cdot 2^{2n}} \right) = -\sum_{n=1}^{\infty} \frac{1}{2^{2n+1}} = -\frac{\left( \frac{1}{2} \right)^3}{1 - \frac{1}{4}} = -\frac{1}{6}$ 故选A.

    方法2:

    $$\left[ \ln(2 + x) \right]' = \frac{1}{2 + x} = \frac{1}{2 \left( 1 + \frac{x}{2} \right)} = \frac{1}{2} \sum_{n=0}^{\infty} (-1)^n \left( \frac{x}{2} \right)^n$$

    $$\ln(2 + x) = \sum_{n=0}^{\infty} (-1)^n \frac{\left( \frac{1}{2} x \right)^{n+1}}{n+1} + C = \sum_{n=1}^{\infty} (-1)^{n-1} \frac{\left( \frac{1}{2} x \right)^n}{n} + C$$

    $$S(0) = C = \ln(2 + 0) = \ln 2$$

    所以, $\sum_{n=0}^{\infty} n a_{2n} = \sum_{n=1}^{\infty} n a_{2n} = \sum_{n=1}^{\infty} n \cdot \left( -\frac{1}{2n \cdot 2^{2n}} \right) = -\sum_{n=1}^{\infty} \frac{1}{2^{2n+1}} = -\frac{\left( \frac{1}{2} \right)^3}{1 - \frac{1}{4}} = -\frac{1}{6}$ 故选A.

4. 设函数 $f(x)$ 在区间 $(-1, 1)$ 上有定义,且 $\lim_{x \rightarrow 0} f(x) = 0$, 则

    A. $\lim_{x \rightarrow 0} \frac{f(x)}{x} = m$ 时, $f'(0) = m$

    B. 当 $f'(0) = m$, $\lim_{x \rightarrow 0} \frac{f(x)}{x} = m$

    C. 当 $\lim_{x \rightarrow 0} f'(x) = m$, $f'(0) = m$

    D. 当 $f'(0) = m$

    [答案]: B

    [解析]: 因为 $f'(0) = m$, 所以 $f(x)$ 在 $x = 0$ 处连续, 从而 $\lim_{x \rightarrow 0} f(x) = f(0) = 0$, 所以 $\lim_{x \rightarrow 0} \frac{f(x)}{x} = \lim_{x \rightarrow 0} \frac{f(x) - f(0)}{x - 0} = m$, 故选B.

    对于A选项, $\lim_{x \rightarrow 0} \frac{f(x)}{x} = m$, 推不出来 $f'(0) = m$ 对于C选项, $f'(x)$ 在 $x = 0$ 处不一定连续;对于D选项, $f'(x)$ 在 $x = 0$ 处极限未必存在.

5. 在空间直角坐标系 $O - xyz$ 中,三张平面 $\pi_i : a_i x + b_i y + c_i z = d_i (i = 1, 2, 3)$ 的位置关系如图所示,

    记 $\alpha_i = (a_i, b_i, c_i, d_i)$, 则

    A. $m = 1, n = 2$

    B. $m = n = 2$

    C. $m = 2, n = 3$

    D. $m = n = 3$

数学试题第1页(共10页)

<!-- PageFooter="数学试题第2页(共10页)" -->