# Portfolio Intelligence: AI Query Engine

A high-performance, natural language interface for financial portfolio analysis. This system allows users to query over **10,000 financial records** (equities, ETFs, bonds, and REITs) using plain English, converting questions into optimized SQL queries in real-time.

## 🚀 Overview

The **Portfolio Intelligence API** and **Streamlit UI** provide a seamless experience for portfolio monitoring and deep-dive analysis. It leverages Gemini's reasoning capabilities to understand financial intent and Neon's serverless PostgreSQL for rapid data retrieval.

### Key Features
* **Natural Language to SQL**: Powered by **Gemini 3.1 Flash-Lite** for ultra-low latency query generation.
* **High-Volume Data**: Pre-seeded with **10,000 financial records**.
* **Real-time KPI Dashboard**: Instant visibility into total value, invested capital, and PnL.
* **FastAPI Backend**: Asynchronous endpoints for health checks, portfolio statistics, and NL queries.
* **Interactive UI**: A modern Streamlit dashboard featuring sample query pills, chat history, and data visualizations.

## 🛠️ Tech Stack

* **LLM**: `google-genai` (Gemini 2.5 Flash-Lite).
* **Backend**: `fastapi`, `uvicorn`, `pydantic`.
* **Database**: `psycopg` (PostgreSQL / Neon) with connection pooling.
* **Frontend**: `streamlit`, `pandas`, `httpx`.
* **Environment**: `python-dotenv`, `pydantic-settings`.

## 📂 Project Structure

* `main.py`: Entry point for the FastAPI backend and lifespan management.
* `ui/streamlit_app.py`: Main dashboard and chat interface.
* `core/`: Configuration and logging utilities.
* `db/`: Database initialization and session management.
* `services/`: Business logic for query processing and portfolio stats.
* `llm/`: Services for Gemini integration and caching.
* `scripts/seed_db.py`: Automation script to populate the database on startup.

## 🚦 Getting Started

### 1. Requirements
* Python ^3.13
* Poetry for dependency management

### 2. Environment Setup
Create a `.env` file based on the provided configuration (refer to `.env.example`):
```env
# Required Variables
DATABASE_URL=your_postgresql_url
GEMINI_API_KEY=your_api_key