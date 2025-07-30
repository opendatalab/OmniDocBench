<!-- PageHeader="Compiler Construction: Principles and Practice" -->
<!-- PageHeader="Chapter 5 Exercise Answers, Page 5" -->

(d)

| | Parsing stack | Input | Action |
|---|---|---|---|
| 1 | $$\mathbb{S} 0$$ | $$int \quad x, y, z$$ | shift 3 |
| 2 | $$0 \quad int \quad 3$$ | $$x, y, z $$ | reduce 2 |
| 3 | $$8 0 T 2$$ | $$x, y, z $$ | shift 6 |
| 4 | $$8 0 T 2 \text{id} 6$$ | $$y, z$$ | reduce 5 |
| 5 | $$S 0 T 2 V 5$$ | $$y, z $$ | shift 7 |
| 6 | $$8 0 T 2 V 5, 7$$ | $$y, z $$ | shift 8 |
| 7 | $$8 0 T 2 V 5, 7 \text{id} 8$$ | $$z$$ | reduce 4 |
| 8 | $$8 0 T 2 V 5$$ | $$, z $$ | shift 7 |
| 9 | $$8 0 T 2 V 5, 7$$ | $$\mathrm{z} $$ | shift 8 |
| 10 | $$3 0 T 2 V 5, 7 \text{id} 8$$ | $$ $$ | reduce 4 |
| 11 | $$8 0 T 2 V 5$$ | $$ $$ | reduce 1 |
| 12 | $$\mathrm{S} 0 D 1$$ | $$ $$ | accept |

(e)

$$\left[ D' \rightarrow . D, S \right]$$

$$D$$

$$\left[ D' \rightarrow D \cdot, S \right]$$

$$\left[ D \rightarrow . T V, S \right]$$
$$\left[ T \rightarrow . \text{int}, \text{id} \right]$$

$$\left[ T \rightarrow . \text{float}, \text{id} \right]$$

$$T$$

$$\left[ D \rightarrow T . V, S \right]$$

$$\left[ V \rightarrow . V, \text{id}, S / _ { r } \right]$$

$$\left[ V \rightarrow . \text{id}, S / _ { r } \right]$$

$$\text{id}$$

$$\left[ T \rightarrow \text{int} . , \text{id} \right]$$

$$\left[ T \rightarrow \text{float} . , \text{id} \right]$$

$$\left[ V \rightarrow \text{id} . , S / , \right]$$

$$\left[ D \rightarrow T V . , S \right]$$
$$\left[ V \rightarrow V _ { \cdot } , \text{id}, S \bar { / } _ { \star } \right]$$

$$\text{id}$$

$$\left[ V \rightarrow V _ { r } . \text{id}, S / _ { r } \right]$$

$$\left[ V \rightarrow V _ { r } \text{id} \cdot , S / _ { r } \right]$$

![10 int float 2 3 4 6 5 7 8](figures/1.1)

(f) The LALR(1) parsing table is the same as the SLR(1) parsing table shown in (c).

# Exercise 5.10

We use similar language to that on page 210, with appropriate modifications:

The SLR(1) parsing algorithm. Let $s$ be the current state whose number is at the top of the
parsing stack. Then actions are defined as follows:

(1) If state $s$ contains any item of the form $A \rightarrow \alpha . X \beta$, where $X$ is a terminal, and $X$ is the
next token in the input string, then the action is to remove the current input token and push onto
the stack the number of the state containing the item $A \rightarrow \alpha X . \beta$.

<!-- PageFooter="https://www.coursehero.com/file/23512560/ch5ans/" -->

ro.com