<!-- PageHeader="Compiler Construction: Principles and Practice" -->
<!-- PageHeader="Chapter 5 Exercise Answers, Page 5" -->

(d)


| | Parsing stack | Input | Action |
| 1 | $$\mathbb{S} 0$$ | $$i n t \quad x , y , z$$ | shift 3 |
| 2 | $$0 \quad i n t \quad 3$$ | $$x , y , z$$ | reduce 2 |
| 3 | $$8 0 T 2$$ | $$x , y , z$$ | shift 6 |
| 4 | $$8 0 T 2 \text { id } 6$$ | $$y , z$$ | reduce 5 |
| 5 | $$S 0 T 2 V 5$$ | $$y , z$$ | shift 7 |
| 6 | $$8 0 T 2 V 5 , 7$$ | $$y , z$$ | shift 8 |
| 7 | $$8 0 T 2 V 5 , 7 \text { id } 8$$ | $$z$$ | reduce 4 |
| 8 | $$8 0 T 2 V 5$$ | $$, z$$ | shift 7 |
| 9 | $$8 0 T 2 V 5 , 7$$ | $$\mathrm { z }$$ | shift 8 |
| 10 | $$3 0 T 2 V 5 , 7 \text { id } 8$$ | $$|$$ | reduce 4 |
| 11 | $$8 0 T 2 V 5$$ | $$|$$ | reduce 1 |
| 12 | $$\mathrm { S } 0 D 1$$ | $$|$$ | accept |


(e)

$$\left[ D ^ { \prime } \rightarrow . D , \mathrm { S } \right]$$

$$D$$

$$\left[ D ^ { \prime } \rightarrow D \cdot , \mathrm { S } \right]$$

$$\left[ D \rightarrow . T V , S \right]$$
$$\left[ T \rightarrow . \mathrm { i n t } , \widetilde { i d } \right]$$

$$\left[ T \rightarrow . \mathrm { f l o a t } , \mathrm { i d } \right]$$

$$T$$

$$\left[ D \rightarrow T . V , \mathrm { S } \right]$$

$$\left. \bar { \left[ \right. } V \rightarrow . V , \mathrm { i d } , \mathrm { S } / _ { \mathrm { r } } \right]$$

$$\left[ V \rightarrow . \mathrm { i d } , \mathrm { S } / _ { \mathrm { r } } \right]$$

$$i d$$

$$\left[ T \rightarrow \mathrm { i n t } . , \mathrm { i d } \right]$$

$$\left[ T \rightarrow \mathrm { f l o a t } . , \mathrm { i d } \right]$$

$$\left[ V \rightarrow i d . , S / , \right]$$

$$\left[ D \rightarrow T V . , S \right]$$
$$\left. \widetilde { \left[ \right. } V \rightarrow V _ { \cdot } , \mathrm { i d } , \mathrm { S } / _ { \star } \right]$$

$$i d$$

$$\left[ V \rightarrow V _ { r } . \mathrm { i d } , \mathrm { S } / _ { r } \right]$$

$$\left[ V \rightarrow V _ { r } i d \cdot , S / _ { r } \right]$$


![1 0 int float 2 3 4 6 5 7 8](figures/1.1)


(f) The LALR(1) parsing table is the same as the SLR(1) parsing table shown in (c).


# Exercise 5.10

We use similar language to that on page 210, with appropriate modifications:

The SLR(1) parsing algorithm. Let $s$ be the current state whose number is at the top of the
parsing stack. Then actions are defined as follows:

(1) If state $s$ contains any item of the form $A \rightarrow \alpha . X \beta$ , where $X$ is a terminal, and $X$ is the
next token in the input string, then the action is to remove the current input token and push onto
the stack the number of the state containing the item $A \rightarrow \alpha X . \beta$ .

<!-- PageFooter="https://www.coursehero.com/file/23512560/ch5ans/" -->

ro.com
```