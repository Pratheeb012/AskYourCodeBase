# RepoMind 🧠

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![FastAPI](https://img.shields.io/badge/Backend-FastAPI-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/Frontend-React_18-61DAFB?logo=react&logoColor=black)](https://reactjs.org/)
[![LLM](https://img.shields.io/badge/LLM-Groq_Llama3-orange)](https://groq.com/)

**RepoMind** is a premium, production-grade AI-native developer tool designed to transform how you interact with complex codebases. By combining Retrieval-Augmented Generation (RAG) with deep static analysis, RepoMind allows you to query any GitHub repository or local ZIP archive using natural language, providing context-aware answers, architectural insights, and dependency visualizations.

---

## ✨ Key Features

### 🔐 Multi-Tenant Security & Isolation
*   **User Isolation**: Strict data partitioning ensures that repositories and chat histories are private to each user.
*   **JWT Authentication**: Secure, industrial-standard authentication flow.

### 🧠 Intelligent RAG Engine
*   **Groq Llama-3.3-70B**: Lightning-fast inference for real-time code understanding.
*   **AI Failover System**: Automatic switching to a high-limit fallback model (`Llama-3-8B`) if the primary model hits a rate limit, ensuring 100% uptime.
*   **Snippet Compression**: Smart truncation and filtering engine that reduces token usage by up to 90% while maintaining context accuracy.
*   **Contextual Awareness**: Proactive retrieval of the most relevant code snippets with full file-path citations.

### 🎨 Premium Developer Experience
*   **Adaptive Design System**: A stunning glassmorphism UI with support for both **Dark** and **Light** modes.
*   **Proactive UI Intelligence**: The interface automatically switches panels (e.g., to the Source tab) when you interact with code references in chat.
*   **Static Insights**: Automated deep-scanning for technical debt, security risks, and code smells.

---

## 🛠️ Technology Stack

| Component | Technology | Role |
| :--- | :--- | :--- |
| **Frontend** | React 18, Vite, Zustand, Framer Motion | Modern, high-performance UI/UX |
| **Backend** | FastAPI (Python 3.10+) | High-speed, asynchronous API |
| **Intelligence** | Groq (Llama-3), FAISS | High-speed LLM & Vector Search |
| **Styling** | Vanilla CSS (Glassmorphism) | Premium, custom-tailored design system |

---

## 🚀 Getting Started

### 1. Backend Setup
1. Navigate to the `backend` directory.
2. Create a virtual environment: `python -m venv venv`
3. Install dependencies: `pip install -r requirements.txt`
4. Create a `.env` file from `.env.example` and add your **Groq API Key**.
5. Start the server: `python -m uvicorn app.main:app --reload`

### 2. Frontend Setup
1. Navigate to the `frontend` directory.
2. Install dependencies: `npm install`
3. Start the dev server: `npm run dev`

---

## 🏗️ Architecture Overview

RepoMind follows a decoupled architecture designed for scale:
1.  **Ingestion Service**: Handles ZIP uploads and GitHub cloning, converting raw code into semantic embeddings.
2.  **Vector Store (FAISS)**: Locally stores indexed code segments for high-speed retrieval.
3.  **Chat Service**: Orchestrates the RAG flow, rewriting queries for optimal search and synthesizing answers.
4.  **Analysis Service**: Performs AST-based static scanning to provide structural insights without using LLM tokens.

---

## 🛡️ Security & Privacy
*   **No Data Leakage**: Your code is stored locally on the server; only relevant snippets are sent to the LLM during queries.
*   **Token Protection**: Never commit your `.env` file. A sanitized `.env.example` is provided for reference.

---

## 📄 License
This project is licensed under the MIT License - see the LICENSE file for details.