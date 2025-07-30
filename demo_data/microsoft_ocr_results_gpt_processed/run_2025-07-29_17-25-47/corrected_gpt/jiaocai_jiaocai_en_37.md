<!-- PageHeader="Theory of Computation Final Exam (Page 2 of 5)" -->
<!-- PageHeader="15 Jan., 2015" -->

# 2. (18%) On FA and Regular Languages

Say whether each of the following languages is regular or not regular? Prove your answers.

(a) $L_{1} = \{ w \mid w \in \{0, 1\}^{*} \text{ and } w \text{ has an equal number of 0s and 1s} \}$.

(b) $L_{2} = \{ w \mid w \in \{0, 1\}^{*} \text{ and } w \text{ has an equal number of 01s and 10s} \}$.

# 3. (20%) On PDA and Context-Free Languages

Let $L_{3} = \{ w c a^{m} b^{n} \mid w \in \{a, b\}^{*}, w = w^{R}, m, n \in \mathbb{N}, n \leq m \leq 2n \}$.

(a) Give a context-free grammar for the language $L_{3}$.

(b) Design a PDA $M = (K, \Sigma, \Gamma, \Delta, s, F)$ accepting the language $L_{3}$.

Solution: (a)

(b) The PDA $M = (K, \Sigma, \Gamma, \Delta, s, F)$ is defined below:

$$K = \{\}$$
$$\Sigma = \{a, b, c\}$$
$$\Gamma = \{\}$$
$$s =$$
$$F = \{\}$$
$$3$$
$$(q, \sigma, \beta)$$
$$(p, \gamma)$$