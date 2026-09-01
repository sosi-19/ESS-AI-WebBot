\# 🇪🇹 ESS AI Web Assistant



An AI-powered web assistant designed for the \*\*Ethiopia Statistical Service (ESS)\*\*.



The system allows users to ask questions about ESS statistical reports and datasets using natural language. It combines \*\*Retrieval-Augmented Generation (RAG)\*\* for PDF reports with \*\*data analysis capabilities\*\* for CSV datasets.



\---



\## 📌 Project Overview



The ESS AI Web Assistant provides an intelligent interface for accessing and understanding statistical information published by the Ethiopia Statistical Service.



Instead of manually searching through large statistical reports or datasets, users can ask questions in natural language and receive answers based on the available ESS data.



The system supports:



\- 📄 Question answering from ESS PDF reports

\- 📊 Statistical analysis of CSV datasets

\- 🔎 Semantic search using embeddings

\- 🤖 Local AI-powered response generation

\- 📁 Uploading and asking questions about PDF files

\- 👤 User registration and authentication

\- 💬 Chat history for authenticated users

\- 🌐 Public/guest chat access

\- 🧩 Embeddable ESS AI widget

\- 📚 ESS statistical codebook support



\---



\# ✨ Main Features



\## 1. PDF Question Answering



The system uses Retrieval-Augmented Generation (RAG) to answer questions from ESS statistical reports.



The process is:



```text

PDF Report

&#x20;   ↓

Text Extraction

&#x20;   ↓

Chunking

&#x20;   ↓

Embeddings

&#x20;   ↓

ChromaDB

&#x20;   ↓

Semantic Retrieval

&#x20;   ↓

Relevant Context

&#x20;   ↓

Local LLM

&#x20;   ↓

Answer

