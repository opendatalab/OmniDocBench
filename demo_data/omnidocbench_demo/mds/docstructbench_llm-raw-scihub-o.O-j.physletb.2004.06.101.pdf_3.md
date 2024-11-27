For consistency, the time derivative of the constraints of (10) must vanish and hence they must have vanishing Poisson bracket with H . Using the fundamental Poisson brackets

$$
\left[ U ( x ), \Pi^{U} ( y ) \right]=\delta( x-y )，
$$

(13)

etc., we find that the primary constraints of (10) imply the secondary constraints

$$
( \Sigma, \Sigma_{i} )=\left(-\partial_{k} \Pi_{k}^{V}, \varepsilon^{i j k} \partial_{j} \left( \Pi_{k}^{B}-m V_{k} \right)-\mu^{2} B_{i} \right).
$$

(14)

If $ \mu^{2}=0 $ ( the Cremmer-Scherk model Lagrangian [1]), the constraints of (14) would become reducible as then $ \partial_{i} \, \varSigma_{i}=0 $ and only the transverse portions of $ \varSigma_{i} $ are constraints. Furthermore, with $ \mu^{2} \neq0 $ , the requirement $ \dot{\varSigma}_{i}=0 $ leads to a tertiary constrain

$$
T_{k} \equiv\mu^{2} \varPi_{k}^{B}=0
$$

(15)

with $ \varSigma_{i} $ and $ T_{k} $ constituting second class constraints as

$$
\left[ T_{k} ( x ), \, \varSigma_{i} ( y ) \right]=\mu^{4} \delta_{i k} \delta( x-y ).
$$

(16)

All other constraints are first class and no further constraints need to be imposed for consistency. There are consequently five first class constraints（ $ \varPhi^{U} $ $ \varPhi_{k}^{A} $ and $ \varSigma $ ）and six second class constraints （ $ \varSigma_{i} $ and $ T_{k} $ ）.The constraints $ \varPhi^{U} $ and $ \varSigma $ correspond to the usual gauge transformations $ \delta W_{0}=\partial_{0} \varOmega $ , $ \delta W_{i}=\partial_{i} \varOmega $ associated with a gauge field $ W_{\mu} $ , while $ \varPhi_{k}^{A} $ is associated with the fact that in (12) $ A_{k} $ acts merely as a Lagrange multiplier (i.e., it is not dynamical) and hence its value is completely arbitrary. Suitable gauge conditions associated with the first class constraints are

$$
\left( \gamma^{U}, \gamma_{k}^{A}, \gamma^{V} \right)=\left( U, A_{k}, \partial_{k} V_{k} \right)=0.
$$

(17)

From (10), (14), (15) and (17) it is evident that the only dynamical degrees of freedom are

$$
V_{i}^{T} \equiv\big( \delta_{i j}-\partial_{i} \partial_{j} / \partial^{2} \big) V_{j}.
$$

(18)

We can verify this directly by explicitly eliminating the non-physical degrees of freedom in (4). First, one decomposes $ V_{k} $ , $ A_{k} $ and $ B_{k} $ into transverse (T) and longitudinal (L) parts where

$$
\mathbf{\nabla} \times\mathbf{V}^{L} \equiv0 \equiv\mathbf{\nabla} \cdot\mathbf{V}^{T}，
$$

(19)

etc., (4 ) now becomes

$$
\begin{array} {l} {{{2 L=\left( \dot{\mathbf{B}}^{L} \right)^{2}-\left( \nabla\cdot\mathbf{B}^{L} \right)^{2}+\left[ \dot{\mathbf{B}}^{T}-\nabla\times\mathbf{A}^{T} \right]^{2}+\left( \dot{\mathbf{V}}^{T} \right)^{2}-\left( \nabla\times\mathbf{V}^{T} \right)^{2}+\left[ \dot{\mathbf{V}}^{L}-\nabla U \right]^{2}}}} \\ {{{\ \ \ +2 m \left[ \mathbf{V}^{T} \cdot\left( \nabla\times\mathbf{A}^{T} \right)+\mathbf{B}^{L} \cdot\dot{\mathbf{V}}^{L}+\mathbf{B}^{T} \cdot\dot{\mathbf{V}}^{T}-\mathbf{B}^{L} \cdot\nabla U \right]+2 \mu^{2} \left[ \mathbf{A}^{T} \cdot\mathbf{B}^{T}+\mathbf{A}^{L} \cdot\mathbf{B}^{L} \right]}}} \\ \end{array}.
$$

(20)

The equations of motion for $ A^L $ and U , respectively, imply that

$$
{\bf B}^{L}=0={\dot{\bf V}}^{L}-\nabla U，
$$

(21)

reducing (20) to

$$
2 L=\left( {\dot{\mathbf{V}}}^{T} \right)^{2}-\left( \nabla\times\mathbf{V}^{T} \right)^{2}+\left[ {\dot{\mathbf{B}}}^{T}-\nabla\times\mathbf{A}^{T} \right]^{2}+2 m \mathbf{V}^{T} \cdot\left( \nabla\times\mathbf{A}^{T} \right)+2 m \mathbf{B}^{T} \cdot{\dot{\mathbf{V}}}^{T}+2 \mu^{2} \mathbf{A}^{T} \cdot\mathbf{B}^{T}.
$$

(22)

Since

$$
\mathbf{A}^{T} \cdot\mathbf{B}^{T}=-\big( \nabla\times\mathbf{A}^{T} \big) \cdot\big( \nabla^{2} \big)^{-1} \big( \nabla\times\mathbf{B}^{T} \big)，
$$

(23)

we can eliminate $ \nabla\times\mathbf{A}^{T} $ from (22) to obtain

$$
\nabla\times{\bf A}^{T}=\dot{{\bf B}}^{T}-m {\bf V}^{T}+\mu^{2} \big( \nabla^{2} \big)^{-1} \big( \nabla\times{\bf B}^{T} \big).
$$

(24)

