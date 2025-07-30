For consistency, the time derivative of the constraints of (10) must vanish and hence they must have vanishing Poisson bracket with $H$. Using the fundamental Poisson brackets

$$
\left[U(x), \Pi^{U}(y)\right]=\delta(x-y)
$$

etc., we find that the primary constraints of (10) imply the secondary constraints

$$
\left(\Sigma, \Sigma_{i}\right)=\left(-\partial_{k} \Pi_{k}^{V}, \varepsilon^{i j k} \partial_{j}\left(\Pi_{k}^{B}-m V_{k}\right)-\mu^{2} B_{i}\right)
$$

If $\mu^{2}=0$ (the Cremmer-Scherk model Lagrangian [1]), the constraints of (14) would become reducible as then $\partial_{i} \Sigma_{i}=0$ and only the transverse portions of $\Sigma_{i}$ are constraints. Furthermore, with $\mu^{2} \neq 0$, the requirement $\dot{\Sigma}_{i}=0$ leads to a tertiary constraint

$$
T_{k} \equiv \mu^{2} \Pi_{k}^{B}=0
$$

with $\Sigma_{i}$ and $T_{k}$ constituting second class constraints as

$$
\left[T_{k}(x), \Sigma_{i}(y)\right]=\mu^{4} \delta_{i k} \delta(x-y)
$$

All other constraints are first class and no further constraints need to be imposed for consistency. There are consequently five first class constraints ( $\Phi^{U}, \Phi_{k}^{A}$ and $\Sigma$ ) and six second class constraints ( $\Sigma_{i}$ and $T_{k}$ ). The constraints $\Phi^{U}$ and $\Sigma$ correspond to the usual gauge transformations $\delta W_{0}=\partial_{0} \Omega, \delta W_{i}=\partial_{i} \Omega$ associated with a gauge field $W_{\mu}$, while $\Phi_{k}^{A}$ is associated with the fact that in (12) $A_{k}$ acts merely as a Lagrange multiplier (i.e., it is not dynamical) and hence its value is completely arbitrary. Suitable gauge conditions associated with the first class constraints are

$$
\left(\gamma^{U}, \gamma_{k}^{A}, \gamma^{V}\right)=\left(U, A_{k}, \partial_{k} V_{k}\right)=0
$$

From (10), (14), (15) and (17) it is evident that the only dynamical degrees of freedom are

$$
V_{i}^{T} \equiv\left(\delta_{i j}-\partial_{i} \partial_{j} / \partial^{2}\right) V_{j}
$$

We can verify this directly by explicitly eliminating the non-physical degrees of freedom in (4). First, one decomposes $V_{k}, A_{k}$ and $B_{k}$ into transverse $(T)$ and longitudinal $(L)$ parts where

$$
\nabla \times \mathbf{V}^{L} \equiv 0 \equiv \nabla \cdot \mathbf{V}^{T}
$$

etc., (4) now becomes

$$
\begin{aligned}
2 L= & \left(\dot{\mathbf{B}}^{L}\right)^{2}-\left(\nabla \cdot \mathbf{B}^{L}\right)^{2}+\left[\dot{\mathbf{B}}^{T}-\nabla \times \mathbf{A}^{T}\right]^{2}+\left(\dot{\mathbf{V}}^{T}\right)^{2}-\left(\nabla \times \mathbf{V}^{T}\right)^{2}+\left[\dot{\mathbf{V}}^{L}-\nabla U\right]^{2} \\
& +2 m\left[\mathbf{V}^{T} \cdot\left(\nabla \times \mathbf{A}^{T}\right)+\mathbf{B}^{L} \cdot \dot{\mathbf{V}}^{L}+\mathbf{B}^{T} \cdot \dot{\mathbf{V}}^{T}-\mathbf{B}^{L} \cdot \nabla U\right]+2 \mu^{2}\left[\mathbf{A}^{T} \cdot \mathbf{B}^{T}+\mathbf{A}^{L} \cdot \mathbf{B}^{L}\right]
\end{aligned}
$$

The equations of motion for $\mathbf{A}^{L}$ and $U$, respectively, imply that

$$
\mathbf{B}^{L}=0=\dot{\mathbf{V}}^{L}-\nabla U
$$

reducing (20) to

$$
2 L=\left(\dot{\mathbf{V}}^{T}\right)^{2}-\left(\nabla \times \mathbf{V}^{T}\right)^{2}+\left[\dot{\mathbf{B}}^{T}-\nabla \times \mathbf{A}^{T}\right]^{2}+2 m \mathbf{V}^{T} \cdot\left(\nabla \times \mathbf{A}^{T}\right)+2 m \mathbf{B}^{T} \cdot \dot{\mathbf{V}}^{T}+2 \mu^{2} \mathbf{A}^{T} \cdot \mathbf{B}^{T}
$$

Since

$$
\mathbf{A}^{T} \cdot \mathbf{B}^{T}=-\left(\nabla \times \mathbf{A}^{T}\right) \cdot\left(\nabla^{2}\right)^{-1}\left(\nabla \times \mathbf{B}^{T}\right)
$$

we can eliminate $\nabla \times \mathbf{A}^{T}$ from (22) to obtain

$$
\nabla \times \mathbf{A}^{T}=\dot{\mathbf{B}}^{T}-m \mathbf{V}^{T}+\mu^{2}\left(\nabla^{2}\right)^{-1}\left(\nabla \times \mathbf{B}^{T}\right)
$$