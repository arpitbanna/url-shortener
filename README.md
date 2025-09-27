# URL Shortener API

A simple, secure, and scalable URL shortener built with **Flask, MySQL, and Redis**. Supports user authentication, URL shortening, redirects, and click analytics.

---

## Table of Contents

- [Features](#features)  
- [Tech Stack](#tech-stack)  
- [Prerequisites](#prerequisites)  
- [Getting Started](#getting-started)  
  - [Clone Repository](#clone-repository)  
  - [Setup Environment Variables](#setup-environment-variables)  
  - [Start Services](#start-services)  
  - [Initialize Database](#initialize-database)  
- [API Endpoints](#api-endpoints)  
- [Rate Limiting](#rate-limiting)  
- [Contributing](#contributing)  
- [License](#license)  

---

## Features

- User signup and login with **JWT-based authentication**  
- Shorten URLs with **custom codes**  
- Redirect short URLs to **original URLs**  
- Track clicks and **URL analytics** per user  
- Redis caching for faster redirects  
- **Rate limiting** per user and per IP  
- Optional logging of **IP, user agent, and referrer**  

---

## Tech Stack

- **Backend:** Python 3.11, Flask  
- **Database:** MySQL 8.0  
- **Cache / Rate Limiting:** Redis 7  
- **Authentication:** JWT (access + refresh tokens)  
- **Containerization:** Docker, Docker Compose  

---

## Prerequisites

- Docker & Docker Compose  
- Python 3.11 (if running outside Docker)  
- MySQL client (for DB inspection)  
- Redis client (for caching)

---

## Getting Started

### Clone Repository

```bash
git clone https://github.com/yourusername/url-shortener.git
cd url-shortener
