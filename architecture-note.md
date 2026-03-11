#### **Database Selection: Neon (PostgreSQL)**

The project utilizes **Neon**, a serverless PostgreSQL platform. It was chosen for several primary reasons:

*   **Scale-to-Zero & Performance:** It offers the reliability of Postgres with cloud-native features and high-performance capabilities.
    
*   **Relational Integrity:** Financial data (equities, ETFs, REITs) requires strict schema enforcement and complex join capabilities for portfolio analysis.
    
*   **Connection Pooling:** Using Neon’s built-in connection pooling ensures the FastAPI backend can handle concurrent natural language queries without hitting database connection limits.
    

#### **Schema Design**

The database is centered around a portfolio table optimized for fast aggregation.

*   **Fields:** It tracks symbol, name, asset\_class (e.g., Equity, Bond), sector, quantity, buy\_price, and current\_price.
    
*   **Indexing:** B-tree indexes are applied to key columns to accelerate common filtering and grouping operations used in the query engine.
    
*   **Data Volume:** The system is designed to handle and is pre-seeded with **10,000 financial records**.
    

#### **NL Query Interpretation & Logic**

The system uses a **Text-to-SQL Generation** approach powered by **Gemini 2.5 Flash-Lite**.

*   **The Workflow:** When a user submits a query, the backend processes the natural language through the LLM to generate the corresponding SQL.
    
*   **Hybrid Logic:** The system uses a Pydantic-based validation layer to ensure the LLM output is a valid query that adheres to the established schema before execution.
    
*   **Intent Recognition:** The LLM serves as the "router," deciding whether a query requires a simple SELECT, an aggregation (e.g., SUM), or specific filtering.
    

#### **Latency Control (The 2-Second Target)**

To maintain a response time near 2 seconds, the architecture employs several optimization strategies:

*   **Model Selection:** The engine uses **Gemini 2.5 Flash-Lite**, which is specifically optimized for high-speed inference and low latency.
    
*   **Pre-warming:** The LLM cache and database pools are initialized during the FastAPI "lifespan" startup to eliminate overhead during the request cycle.
    
*   **Asynchronous Execution:** The entire stack—from the httpx calls in the UI to the psycopg database drivers—is fully asynchronous.
    
*   **Efficiency Monitoring:** The system tracks and returns latency\_ms for every query to ensure performance targets are consistently met.