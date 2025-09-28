# URL Shortener API 🚀

A **lightweight, secure, and production-ready URL shortener service** built for high performance using **Flask, MySQL, Redis, and Celery**.  
It provides **user authentication, real-time click analytics, trending URLs, and built-in fraud detection**, making it ideal for both production and experimental setups.

---

## 💡 Table of Contents

- [Project Overview](#project-overview)  
- [Features](#features)  
- [Tech Stack](#tech-stack)  
- [Architecture & Flow](#architecture--flow)  
- [Prerequisites](#prerequisites)  
- [Getting Started](#getting-started)  
- [API Endpoints](#api-endpoints)  
- [Rate Limiting & Security](#rate-limiting--security)  
- [Metrics & Observability](#metrics--observability)  
- [Contributing](#contributing)  
- [License](#license)  

---

## 📝 Project Overview

This is a **scalable URL shortener** focused on **performance, security, and observability**. It doesn’t just shorten links — it **tracks analytics, prevents abuse, and identifies trending content**.

**Core Capabilities:**

* **Shortening:** Automatic short codes for URLs.  
* **Analytics:** Track clicks, unique visitors, and referrers.  
* **Security:** Fraud detection and strict rate limiting.  
* **Trending URLs:** Weighted scoring based on recent activity.  

**Architecture Highlights:**

* **Redis:** Fast caching for redirects and rate enforcement.  
* **MySQL:** Persistent storage for URLs and analytics.  
* **Celery:** Background processing for click logging and fraud checks.

---

## ✨ Features

| Category | Feature | Description |
| :--- | :--- | :--- |
| **Authentication** | Secure Access | Sign up, login, and refresh tokens via **JWT**. |
| **URL Management** | Custom Codes | Auto-generate or allow user-defined short codes. |
| **Performance** | Fast Redirects | Low-latency redirects leveraging **Redis caching**. |
| **Analytics** | Click Tracking | Async logging with hourly aggregation of clicks, unique visitors, and top referrers. |
| **Trending** | Weighted Score | Exponential decay scoring for recent activity on URLs. |
| **Security** | Fraud Detection | Detect suspicious clicks using behavior and velocity checks. |
| **Abuse Prevention** | Rate Limiting | Enforced per-user and per-IP via Redis. |
| **Observability** | Prometheus Metrics | Track request counts, latency, and flagged activity. |

---

## 🛠 Tech Stack

| Component | Technology | Role |
| :--- | :--- | :--- |
| **Backend** | Python 3.11, Flask | Core application framework. |
| **Database** | MySQL 8.0 | Persistent storage for users, URLs, and analytics. |
| **Caching / Rate Limiting** | Redis 7 | High-speed store for redirects, trending data, and rate limits. |
| **Task Queuing** | Celery + Redis | Async processing of click logs and fraud detection. |
| **Containerization** | Docker, Docker Compose | Development and production orchestration. |
| **Monitoring** | Prometheus | Metrics collection and exposure. |
| **Authentication** | JWT | Secure, stateless user authentication. |

---

## 🏗 Architecture & Flow

The system separates **fast synchronous operations** (redirects) from **heavy async work** (analytics, fraud checks).

```text
Client (Browser/App)
       ↓
Flask API (Auth, Rate Limiting, Shortening)
       ↓
Redis (Cache / Rate Limits) ↔ MySQL (Persistent Storage)
       ↓
Celery (Async Click Logging / Fraud Checks)
       ↓
Prometheus (Metrics)

### 🔄 Flow Example

1. **User shortens a URL:**  
   Client sends long URL → Flask API generates a short code → stores in MySQL + caches in Redis.

2. **Client accesses short URL:**  
   Hits `/short_code` → Flask retrieves original URL from Redis → redirects.

3. **Click is logged:**  
   Flask pushes click data (IP, User-Agent) to Celery queue.

4. **Celery processes click:**  
   Worker performs fraud check → updates logs → recalculates hourly analytics and trending scores.

5. **Monitoring:**  
   Prometheus scrapes Flask API for metrics.

---

## ⚡ Prerequisites

* Docker & Docker Compose  
* Python 3.11 (if running Flask outside Docker)

---

## 🚀 Getting Started

### 1. Clone Repository

```bash
git clone https://github.com/SysTechSalihY/url-shortener.git
cd url-shortener
