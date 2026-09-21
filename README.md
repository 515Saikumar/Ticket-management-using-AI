# 🎫 AI-Powered Helpdesk Ticket Triage System

<div align="center">

![React](https://img.shields.io/badge/React-20232A?style=for-the-badge&logo=react&logoColor=61DAFB)
![Vite](https://img.shields.io/badge/Vite-646CFF?style=for-the-badge&logo=vite&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi)
![Supabase](https://img.shields.io/badge/Supabase-3ECF8E?style=for-the-badge&logo=supabase&logoColor=white)
![Groq](https://img.shields.io/badge/Groq_LLM-F55036?style=for-the-badge)

**An intelligent support ticket management system powered by Large Language Models.**  
Users submit issues in plain English — the AI automatically classifies, prioritizes, and stores them.

</div>

---

## ✨ Features

- 🤖 **AI Triage** — LLM reads the user's issue and extracts category, priority, and a clean summary automatically
- 🔍 **Relevance Detection** — Rejects gibberish, off-topic, or vague queries before they hit the database
- 🏷️ **Smart Classification** — Categories: `Technical` · `Academy` · `HR` · `General`
- 🚦 **Priority Levels** — `Critical` · `High` · `Medium` · `Low`
- 🛡️ **Admin Panel** — Secure admin dashboard to view and manage all tickets (Supabase Auth)
- ⚡ **Model Fallback Chain** — Automatically falls back across multiple Groq models if one fails
- 🗄️ **Persistent Storage** — All tickets stored in Supabase PostgreSQL

---

## 🏗️ Architecture

```
User → React Frontend (Vite :5173)
         ↓  POST /extract-ticket
     FastAPI Backend (Uvicorn :8000)
         ├── ① Input Validation
         ├── ② Groq LLM Call  ←→  Groq Cloud API
         ├── ③ Parse JSON Response
         ├── ④ Relevance Check  (422 if off-topic)
         ├── ⑤ Sanitize Fields
         └── ⑥ Insert → Supabase PostgreSQL
         ↓
     TicketResponse JSON → Success Card UI
```

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| **Frontend** | React 18 + Vite, Vanilla CSS |
| **Backend** | FastAPI + Uvicorn (Python) |
| **AI / LLM** | Groq API — `qwen3.8-27b`, `gpt-oss-120b` (fallback chain) |
| **Database** | Supabase (PostgreSQL) |
| **Auth** | Supabase Auth (admin panel) |

---

## 🚀 Getting Started

### Prerequisites
- Node.js ≥ 18
- Python ≥ 3.10
- A [Groq API key](https://console.groq.com)
- A [Supabase](https://supabase.com) project

---

### 1. Clone the repository

```bash
git clone https://github.com/515Saikumar/Ticket-management-using-AI.git
cd Ticket-management-using-AI
```

---

### 2. Frontend Setup

```bash
npm install
```

Create a `.env.local` file in the project root:

```env
VITE_SUPABASE_URL=https://your-project-id.supabase.co
VITE_SUPABASE_ANON_KEY=your_supabase_anon_key
```

---

### 3. Backend Setup

```bash
cd backend
pip install -r requirements.txt
```

Create a `.env` file inside the `backend/` folder:

```env
GROQ_API_KEY=your_groq_api_key
SUPABASE_URL=https://your-project-id.supabase.co
SUPABASE_SERVICE_KEY=your_supabase_service_role_key
```

---

### 4. Supabase — Create the `tickets` table

Run this SQL in your Supabase SQL Editor:

```sql
create table tickets (
  id             uuid primary key default gen_random_uuid(),
  username       text not null,
  original_query text not null,
  category       text not null,
  priority       text not null,
  summary        text not null,
  status         text not null default 'Open',
  created_at     timestamptz default now()
);
```

---

### 5. Run the App

**Terminal 1 — Backend:**
```bash
cd backend
uvicorn main:app --reload --port 8000
```

**Terminal 2 — Frontend:**
```bash
npm run dev
```

Open **http://localhost:5173** in your browser.

---

## 📂 Project Structure

```
Ticket-management-using-AI/
├── backend/
│   ├── main.py                 # FastAPI app — LLM + Supabase logic
│   ├── requirements.txt
│   └── .env.example            # Template for backend secrets
├── src/
│   ├── pages/
│   │   ├── Dashboard.jsx       # User ticket submission form
│   │   ├── AdminDashboard.jsx  # Admin ticket management view
│   │   └── AdminLogin.jsx      # Admin authentication page
│   ├── context/
│   │   └── AuthContext.jsx     # Supabase auth context
│   ├── router/
│   │   └── AppRouter.jsx       # React Router setup
│   └── supabaseClient.js       # Supabase JS client init
├── .env.example                # Template for frontend secrets
└── vite.config.js
```

---

## 🔐 Environment Variables

### Frontend (`.env.local`)

| Variable | Description |
|---|---|
| `VITE_SUPABASE_URL` | Your Supabase project URL |
| `VITE_SUPABASE_ANON_KEY` | Supabase anon/public key |

### Backend (`backend/.env`)

| Variable | Description |
|---|---|
| `GROQ_API_KEY` | API key from [console.groq.com](https://console.groq.com) |
| `SUPABASE_URL` | Your Supabase project URL |
| `SUPABASE_SERVICE_KEY` | Supabase service role key (**never expose to frontend**) |

---

## 🤖 How the AI Works

1. User submits their **name** and **issue description**
2. Backend sends the text to **Groq LLM** with a detailed system prompt
3. LLM returns structured JSON:
   ```json
   {
     "username": "Arjun",
     "category": "Technical",
     "priority": "High",
     "summary": "User cannot log into the company dashboard."
   }
   ```
4. If the query is off-topic or gibberish, LLM returns `{"relevant": false}` → user sees a helpful notice
5. Valid tickets are saved to Supabase and shown as a success card

---

## 📸 Pages

| Page | Route | Access |
|---|---|---|
| Ticket Submission | `/` | Public |
| Admin Login | `/admin` | Public |
| Admin Dashboard | `/admin/dashboard` | Admin only (Supabase Auth) |

---

## 📄 License

This project is open source and available under the [MIT License](LICENSE).

---

<div align="center">
Built with ❤️ using React, FastAPI, Groq LLM &amp; Supabase
</div>
