# ASTRA SENTINEL

AI-Powered Defence Information Monitoring System - ASTRA Software Team 3-Day Build Challenge 2026-27.

## Overview

SENTINEL converts a collection of public articles into structured intelligence. Articles are stored in SQLite and can be categorized, summarized and enriched with keywords, topics and entities using a locally hosted LLM. The dashboard supports search and filtering, while the Intelligence Brief provides a collection-level intelligence view.

## Features

- ASTRA starter dataset ingestion
- AI categorization into defence-related categories
- AI-generated concise summaries
- Keyword, topic and entity extraction
- SQLite data persistence
- Search functionality
- Category and date filtering
- Add-article UI
- Error handling for empty and malformed inputs
- Collection-level Intelligence Brief

## Tech Stack

- Python
- Streamlit
- SQLite
- Ollama
- Llama 3.2 3B
- Pandas
- Plotly

## Architecture

```mermaid
flowchart LR
    A[Starter Dataset / New Article] --> B[Streamlit Frontend]
    B --> C[Python Processing Layer]
    C --> D[Ollama / Llama 3.2 3B]
    D --> E[Structured JSON]
    E --> F[(SQLite Database)]
    F --> G[Dashboard / Search / Filters]
    F --> H[Intelligence Brief]