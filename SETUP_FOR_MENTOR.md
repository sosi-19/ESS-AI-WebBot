\# ESS AI Web Assistant — Mentor Setup Guide



\## 1. Requirements



Install these on the computer:



\- Git

\- Python 3.14+

\- Node.js

\- PostgreSQL

\- Ollama



Required Ollama model:



&#x20;   qwen2.5:1.5b



\---



\## 2. Clone the project



Open PowerShell:



&#x20;   git clone https://github.com/sosi-19/ESS-AI-WebBot.git



&#x20;   cd ESS-AI-WebBot



\---



\## 3. Backend setup



Go into backend:



&#x20;   cd backend



Create virtual environment:



&#x20;   python -m venv .venv



Activate it:



&#x20;   .\\.venv\\Scripts\\Activate.ps1



Install dependencies:



&#x20;   pip install -r requirements.txt



\---



\## 4. Create environment file



Copy the example:



&#x20;   Copy-Item .env.example .env



Open it:



&#x20;   notepad .env



Set the PostgreSQL connection:



&#x20;   DATABASE\_URL=postgresql://postgres:YOUR\_POSTGRES\_PASSWORD@localhost:5432/ess\_ai\_webbot



Keep the other values from .env.example.



\---



\## 5. PostgreSQL



Make sure PostgreSQL is running.



Create the database if it does not already exist.



Open:



&#x20;   psql -U postgres



Then:



&#x20;   CREATE DATABASE ess\_ai\_webbot;



Exit:



&#x20;   \\q



\---



\## 6. Ollama



Make sure Ollama is installed and running.



Check:



&#x20;   ollama list



If the required model is missing:



&#x20;   ollama pull qwen2.5:1.5b



\---



\## 7. Create the PDF vector database



From the backend folder:



&#x20;   .\\.venv\\Scripts\\Activate.ps1



Then run:



&#x20;   python -m app.rag.ingest



This reads the ESS PDF files from:



&#x20;   ../data/pdf



and creates the local ChromaDB database.



\---



\## 8. Start the backend



From:



&#x20;   ESS-AI-WebBot\\backend



Run:



&#x20;   .\\.venv\\Scripts\\Activate.ps1



&#x20;   uvicorn app.main:app --reload



Backend:



&#x20;   http://127.0.0.1:8000



Test it by opening:



&#x20;   http://127.0.0.1:8000/



You should see:



&#x20;   {"message":"Welcome to ESS AI Web Assistant"}



Keep this terminal running.



\---



\## 9. Start the frontend



Open a NEW PowerShell window.



Go to:



&#x20;   cd ESS-AI-WebBot\\frontend



Install frontend dependencies:



&#x20;   npm install



Start frontend:



&#x20;   npm run dev



Open the URL shown in the terminal, usually:



&#x20;   http://localhost:5173



or:



&#x20;   http://localhost:5174



\---



\## 10. Use ESS AI



Open the frontend URL in the browser.



Click the ESS AI floating button.



The AI assistant should open.



The project can now run completely on this computer without the developer's computer.



\---



\## Important



Do NOT upload the .env file to GitHub.



The following folders/files are intentionally generated locally:



\- backend/.venv

\- backend/chroma\_db

\- backend/uploads

\- backend/.env

\- frontend/node\_modules



The ESS PDF and CSV data are already included in the repository.

