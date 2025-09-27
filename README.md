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

This project is a **scalable URL shortener service** designed for **high performance, security, and observability**.  
It allows users to:

- Shorten URLs with optional custom codes  
- Redirect short URLs to their original destinations  
- Track detailed click analytics including unique visitors, top referrers, and suspicious clicks  
- Discover trending URLs based on weighted recent clicks  
- Protect against abuse with fraud detection and rate limiting  

The system leverages **Redis** for caching and rate limiting, **MySQL** for persistent storage, and **Celery** for asynchronous tasks.  
Prometheus metrics are exposed for monitoring traffic, clicks, and suspicious activity.

---

## ✨ Features

- **User Authentication:** Sign up, login, refresh tokens, and logout with **JWT**  
- **URL Shortening:** Generate short links with optional custom codes  
- **Redirect Service:** Efficiently redirect while logging clicks asynchronously  
- **Click Analytics:** Hourly aggregation of:
  - Total clicks  
  - Unique visitors  
  - Suspicious clicks (fraud detection)  
  - Top referrers  
- **Trending URLs:** Weighted scoring with exponential decay for recent clicks  
- **Fraud Detection:** Fingerprint, velocity, and behavior checks to prevent abuse  
- **Rate Limiting:** Per-user and per-IP using Redis  
- **Observability:** Prometheus metrics for requests, latency, and suspicious activity  
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

Flask API: Handles authentication, URL shortening, redirects, analytics, and rate limiting

Redis: Caches short URLs, trending URLs, enforces rate limits, and stores session-like data

MySQL: Persistent storage for users, URLs, clicks, hourly analytics, and sequences

Celery Workers: Asynchronous processing of click logs and fraud detection

Prometheus: Collects metrics and exposes them for observability and alerting

Docker & Docker Compose: Orchestrates services for development and production environments

---
## 🔄 Flow Example

User submits a long URL → Flask API generates a short code.

Client accesses short URL → Flask redirects to original URL.

Click is logged asynchronously via Celery → Updates analytics and fraud checks.

Metrics are updated → Prometheus scrapes for monitoring dashboards.
---
## ⚡ Prerequisites

Docker & Docker Compose

Python 3.11 (if running outside Docker)

MySQL client (for database inspection)

Redis client (for caching and rate limiting)

## 🚀 Getting Started
Clone Repository

git clone https://github.com/yourusername/url-shortener.git
cd url-shortener

Setup Environment Variables

Create a .env file:

Start Services (Docker)

Initialize Database

## 📡 API Endpoints

POST /auth/signup → Create user

POST /auth/login → Obtain JWT

POST /url/shorten → Shorten a URL

GET /<short_code> → Redirect to original URL

GET /analytics/<url_id> → View click analytics

## ⏱ Rate Limiting

Enforced per IP and per user using Redis

Prevents abuse and ensures fair usage

Configurable thresholds via environment variables

## 📊 Metrics & Analytics

Prometheus metrics for:

Requests per endpoint

Request latency

Click counts (total, unique, suspicious)

Trending URLs

Hourly aggregation in MySQL

Fraud detection integrated with click logging

## 🤝 Contributing

Fork the repository

Create your feature branch (git checkout -b feature/my-feature)

Commit changes (git commit -am 'Add new feature')

Push to branch (git push origin feature/my-feature)

Open a pull request

MIT License © 2025 Salih Yılboğa
