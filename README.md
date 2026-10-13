# PRIVASEC: Privacy-Preserving Intelligent Cyber Defense Platform

[![Security Tests](https://img.shields.io/badge/Security%20Tests-10%2F10%20Passing-brightgreen)]()
[![FastAPI](https://img.shields.io/badge/Backend-FastAPI-009688)]()
[![React](https://img.shields.io/badge/Frontend-React%2019%20%2B%20Vite-61DAFB)]()
[![License](https://img.shields.io/badge/License-MIT-blue.svg)]()

**PRIVASEC** is a full-stack cybersecurity operations and privacy engineering platform combining privacy-preserving computing, intelligent threat detection, adaptive access control, automated incident response, and cryptographic tool suites.

---

## 🌟 Implemented Cybersecurity Modules

| # | Concept / Module | Implementation Details |
|---|---|---|
| **01** | **Privacy-Preserving Computing** | Data minimization, differential privacy Laplace demo, retention policies, and storage separation. |
| **02** | **PII Detection Engine** | Microsoft Presidio analyzer + custom Indian PAN and Aadhaar recognizers, candidate verification. |
| **03** | **Data Masking** | Format-preserving display masking (e.g. `XXXXX1234X`, `a***@example.com`), full masking, and redaction. |
| **04** | **Pseudonymization Vault** | Domain-separated HMAC-SHA256 tokenization and AES-256-GCM encrypted re-identification vault. |
| **05** | **Machine Learning Anomaly Detection** | Isolation Forest tree-based scoring normalized to a 0–100 scale with explainable feature attribution. |
| **06** | **Behavioral Analytics** | Rolling baseline statistics per pseudonymous user (typical hours, velocity, device fingerprints). |
| **07** | **Explainable Risk Scoring Engine** | Composite 5-factor weighted modeling (0–100) mapping signals to automated response actions. |
| **08** | **Web & API Security Gateway** | Sliding-window rate limiting, SQLi/XSS pattern alerts, security headers, and normalized event emission. |
| **09** | **Adaptive Authentication** | Argon2id password hashing, TOTP multifactor authentication, QR code enrollment, and step-up challenges. |
| **10** | **Automated Incident Response** | Configurable containment policies (session revocation, step-up, throttling), investigation timelines, and rollbacks. |
| **11** | **Cryptography Suite** | AES-256-GCM authenticated text & file encryption, nonce isolation, and SHA-256/512 integrity checks. |
| **12** | **Visual Cryptography Lab** | 2-out-of-2 visual secret sharing with 2x2 subpixel expansion and optical overlay reconstruction. |
| **13** | **Steganography Lab** | Lossless PNG least-significant-bit (LSB) embedding with AES-256-GCM encrypted payloads and PSNR metrics. |

---

## 🚀 Quick Start (Running Locally)

### Prerequisites
- Python 3.10+ (tested with Python 3.13 / 3.14)
- Node.js 18+ (tested with Node.js 24)

### 1. Launch the Backend
```powershell
cd backend
# Activate virtual environment
.\.venv\Scripts\activate

# Start FastAPI Uvicorn Server
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```
The backend initializes the database schema, seeds default accounts and policies, and is available at:
- **API Base:** `http://127.0.0.1:8000/api`
- **Swagger Documentation:** `http://127.0.0.1:8000/docs`
- **Health Check:** `http://127.0.0.1:8000/health`

### 2. Launch the Frontend
In a separate terminal window:
```powershell
cd frontend
npm run dev
```
The React SOC Console will be running at:
- **Web Interface:** `http://127.0.0.1:5173`

---

## 👥 Seeded Demonstration Accounts

All demonstration accounts use the password: `Password123!`

| Role | Email | Permissions |
|---|---|---|
| **Super Admin** | `admin@privasec.io` | Manage users, organization policies, key rotation, incident containment. |
| **Security Analyst** | `analyst@privasec.io` | Threat monitoring, incident triage, investigation timeline, attack simulation. |
| **Privacy Officer** | `privacy@privasec.io` | PII scans, data masking policies, authorized re-identification vault, retention audit. |
| **Standard User** | `user@privasec.io` | Cryptography suite, visual secret sharing, steganography demonstrations. |

> *Tip: You can use the one-click **Quick Role Switcher** buttons on the login page to immediately sign in as any role.*

---

## 🧪 Running Automated Tests

Run the full pytest suite:
```powershell
cd backend
.\.venv\Scripts\python.exe -m pytest tests -v
```

All 10 unit and integration tests pass:
- `test_hash_chain_genesis_and_verification`: Verifies append-only SHA-256 chaining and tamper detection.
- `test_aes_gcm_round_trip`: Verifies authenticated encryption and decryption.
- `test_aes_gcm_tamper_rejection`: Ensures altered ciphertext or tags are strictly rejected.
- `test_visual_cryptography_split_and_reconstruct`: Verifies 2-out-of-2 visual secret sharing.
- `test_steganography_embed_and_extract`: Verifies PNG LSB embedding and extraction.
- `test_pii_detection_pan_and_aadhaar`: Validates Presidio and Indian PAN / Aadhaar recognition.
- `test_masking_strategies`: Validates format-preserving masking and redaction.
- `test_differential_privacy_count`: Verifies Laplace perturbation bounds.
- `test_anomaly_detection_isolation_forest`: Tests Isolation Forest tree evaluation.
- `test_risk_scoring_bounds_and_levels`: Validates 5-factor weighted risk modeling.

---

## 🐳 Docker Compose Deployment
```bash
docker-compose up --build
```
Spawns PostgreSQL 16, Redis 7, Celery Worker, FastAPI backend, and Nginx React frontend.

---

## 📖 Architecture & Threat Model Documentation
- [Architecture & Design Specifications](docs/ARCHITECTURE.md)
- [Mathematical Algorithms & Formulas](docs/ALGORITHMS.md)
- [STRIDE Threat Model & Security Posture](docs/SECURITY_AND_THREAT_MODEL.md)
