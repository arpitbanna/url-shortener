# URL Shortener API

A simple, secure, and scalable URL shortener built with Flask, MySQL, and Redis. This project supports user authentication, URL shortening, redirects, and click analytics.

---

## Table of Contents

- [Features](#features)  
- [Tech Stack](#tech-stack)  
- [Prerequisites](#prerequisites)  
- [Getting Started](#getting-started)  
  - [1. Clone Repository](#1-clone-repository)  
  - [2. Setup Environment Variables](#2-setup-environment-variables)  
  - [3. Start Services](#3-start-services)  
  - [4. Initialize Database](#4-initialize-database)  
- [API Endpoints](#api-endpoints)  
- [Rate Limiting](#rate-limiting)  
- [Contributing](#contributing)  
- [License](#license)  

---

## Features

- User signup and login with JWT-based authentication  
- Shorten URLs with optional custom codes  
- Redirect short URLs to original URLs  
- Track clicks per URL 
- Redis caching for faster redirects  
- Rate limiting to prevent abuse  

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
- MySQL client (optional, for DB inspection)  

---

## Getting Started

### 1. Clone Repository

```bash
git clone https://github.com/yourusername/url-shortener.git
cd url-shortener
