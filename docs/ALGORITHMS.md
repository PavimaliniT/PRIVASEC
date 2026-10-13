# PRIVASEC Algorithms & Mathematical Formulations

## 1. Machine Learning Anomaly Detection (Isolation Forest)
The Isolation Forest isolates observations by randomly selecting a feature and randomly selecting a split value between the minimum and maximum values of the feature.

### Score Normalization
The raw decision function $s(x)$ ranges typically from $[-0.3, +0.25]$. We map this to a documented $[0, 100]$ normalized score:
$$\text{Score}_{\text{normalized}} = \text{clip}\left((0.18 - s(x)) \times 190.0,\, 0.0,\, 100.0\right)$$
- Normal observations ($s(x) > 0.05$) score between $0$ and $25$.
- Borderline observations score between $30$ and $55$.
- Severe outliers ($s(x) < -0.15$) score $\ge 62.7$ up to $100.0$.

---

## 2. Differential Privacy (Laplace Mechanism)
For counting queries over sensitive databases, global sensitivity $\Delta f = 1$ because the addition or removal of a single individual changes the count by at most 1.

$$\mathcal{M}(x) = f(x) + Y, \quad Y \sim \text{Laplace}\left(0, \frac{\Delta f}{\epsilon}\right)$$
The scale parameter $b = \frac{1}{\epsilon}$. The 95% confidence bounds are given by:
$$\text{Margin}_{95\%} = b \cdot \ln(20) \approx \frac{2.9957}{\epsilon}$$

---

## 3. Visual Cryptography (2-out-of-2 Secret Sharing)
Based on the Naor-Shamir (1994) construction:
- **Expansion factor:** Each pixel is expanded into a $2 \times 2$ block of 4 subpixels (2 black, 2 white).
- **White Secret Pixel:**
  $$\text{Share}_1 = P_i, \quad \text{Share}_2 = P_i$$
  Overlay: $\min(\text{Share}_1, \text{Share}_2) = P_i$ (2 black, 2 white subpixels = 50% optical transmission).
- **Black Secret Pixel:**
  $$\text{Share}_1 = P_i, \quad \text{Share}_2 = \overline{P_i}$$
  Overlay: 4 black subpixels (0% transmission = complete optical extinction).
- **Information-Theoretic Guarantee:** Probability distribution of patterns in any single share is uniform across all 6 permutations, regardless of whether the original pixel was black or white.

---

## 4. LSB Steganography & PSNR Fidelity
Data is encrypted with AES-256-GCM, packed with `PSEC` magic header and 32-bit length prefix, and injected into the least significant bit (bit 0) of the flattened RGB image array:
$$I_{\text{stego}}[k] = (I_{\text{cover}}[k] \ \& \ \text{0xFE}) \ | \ b_k$$

### Image Quality Metrics
$$\text{MSE} = \frac{1}{M \cdot N \cdot C} \sum_{i,j,c} \left(I_{\text{cover}}(i,j,c) - I_{\text{stego}}(i,j,c)\right)^2$$
$$\text{PSNR} = 10 \cdot \log_{10}\left(\frac{255^2}{\text{MSE}}\right) \quad (\text{dB})$$
Values above $40\text{ dB}$ are considered visually imperceptible to the human eye.

---

## 5. Append-Only Audit Ledger Hash Chain
Genesis state begins with a 64-character null hash pointer:
$$H_0 = \text{"0000000000000000000000000000000000000000000000000000000000000000"}$$
Each subsequent entry $k$ is chained via:
$$H_k = \text{SHA-256}\left(H_{k-1} \,\|\, \text{actor\_id} \,\|\, \text{action} \,\|\, \text{canonical\_json}(\text{meta}) \,\|\, \text{timestamp\_iso}\right)$$
Any mutation, reordering, or deletion of past entries invalidates all succeeding block hashes.
