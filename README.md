# URL Shortener API 🚀

A **lightweight, secure, and production-ready URL shortener** built with **Flask, MySQL, Redis, and Celery**.  
Supports user authentication, URL shortening, redirects, click analytics, trending URLs, and fraud detection.

---

## 💡 Table of Contents

- [Project Overview](#project-overview)  
- [Features](#features)  
- [Tech Stack](#tech-stack)  
- [Architecture](#architecture)  
- [Prerequisites](#prerequisites)  
- [Getting Started](#getting-started)  
- [API Endpoints](#api-endpoints)  
- [Rate Limiting](#rate-limiting)  
- [Metrics & Analytics](#metrics--analytics)  
- [Contributing](#contributing)  
- [License](#license)  

---

## 📝 Project Overview

This project is a **scalable URL shortener service** that allows users to shorten URLs, track clicks, monitor analytics, and discover trending links.  
It is optimized for **performance and security**, using Redis caching, MySQL analytics, and Celery workers for asynchronous tasks.

The system also integrates **fraud detection** to prevent abuse, tracks **unique visitors**, and calculates **trending scores** using weighted recent clicks.

---

## ✨ Features

- **User Authentication:** Sign up, login, refresh tokens, and logout with **JWT-based authentication**  
- **URL Shortening:** Generate short links with optional custom codes  
- **Redirect Service:** Quickly redirect to original URLs while logging clicks  
- **Click Analytics:** Hourly analytics including:
  - Total clicks  
  - Unique visitors  
  - Suspicious clicks (fraud detection)  
  - Top referrers  
- **Trending URLs:** Weighted recent clicks with exponential decay  
- **Fraud Detection:** Fingerprint, velocity, and behavior checks  
- **Rate Limiting:** Per-user and per-IP using Redis  
- **Observability:** Prometheus metrics for requests, latency, clicks, and suspicious activity  
- **Caching:** Redis cache for faster redirects and trending URL retrieval  

---

## 🛠 Tech Stack

- **Backend:** Python 3.11, Flask  
- **Database:** MySQL 8.0  
- **Cache / Rate Limiting:** Redis 7  
- **Async Tasks:** Celery + Redis  
- **Authentication:** JWT (access + refresh tokens)  
- **Containerization:** Docker, Docker Compose  
- **Monitoring:** Prometheus  
- **Analytics:** Hourly aggregation & trending calculation  

---

## 🏗 Architecture

```text
Client: Sends requests to Flask API

Flask API: Handles auth, URL shortening, redirects, and analytics

Redis: Caches short URLs, trending URLs, and enforces rate limits

MySQL: Stores users, URLs, clicks, hourly analytics, and sequences

Celery Workers: Handle asynchronous click logging and fraud detection

Prometheus: Collects and exposes metrics for observability
