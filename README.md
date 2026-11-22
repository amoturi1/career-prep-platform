# AI Career & Internship Prep Platform

This web platform helps students prepare for internships and jobs. Students keep a career profile and résumé, track applications, compare their résumé with job descriptions, practice mock interviews with feedback, and get help from human mentors. Mentors manage requests, review what students choose to share, and give feedback. Administrators publish jobs, events and announcements, manage accounts, and view usage analytics.

**All 36 backlog stories (107 points) are implemented.** Every story is mapped to its code in Section 6.

| Layer | Technology | Folder |
|---|---|---|
| Presentation | React 18 + Vite | `frontend/` |
| Application | Python + FastAPI | `backend/app/routers` (HTTP), `backend/app/services` (rules) |
| AI | Built-in engine, optional Claude API | `backend/app/ai/` |
| Data | SQLAlchemy + SQLite (local), PostgreSQL-ready | `backend/app/models.py` |
| Auth | bcrypt password hashing + JSON Web Tokens | `backend/app/security.py`, `backend/app/deps.py` |

---

## 1. First-time setup

You need **Python 3.11 or newer** and **Node.js 18 or newer**. Check with `python3 --version` and `node --version`.

> **Mac note:** the `python3` that ships with macOS is often 3.9, which is too old. Install a newer one from https://www.python.org/downloads/ and use `python3.13` (or whichever version you installed) in the first command below.

**Backend**, from the project folder:

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env               # Windows: copy .env.example .env
python -c "import secrets; print(secrets.token_hex(32))"   # copy the output into SECRET_KEY in .env
python seed.py
```

**Frontend**, in a second terminal:

```bash
cd frontend
npm install
```

### Demo accounts created by `seed.py`

| Role | Email | Password |
|---|---|---|
| Administrator | `admin@careerprep.com` | `Admin12345` |
| Mentor | `mentor@careerprep.com` | `Mentor12345` |
| Student | create one with **Create account** | your choice |

`seed.py` also adds sample jobs, internships, a career fair, an announcement, and four open mentor session times. Running it again is safe; it only adds what's missing.

---

## 2. Run the app

You need two terminals.

```bash
# Terminal 1: backend
cd backend
source .venv/bin/activate
uvicorn app.main:app --reload
```

```bash
# Terminal 2: frontend
cd frontend
npm run dev
```

Open **http://localhost:5173**. The interactive API documentation is at **http://localhost:8000/docs**.

---

## 3. Upgrading from the Sprint 1 version

If you already ran Sprint 1, unzip the new version over your existing folder. Your `.env`, `.venv`, `node_modules` and database are kept. Then run:

```bash
cd backend
source .venv/bin/activate
pip install -r requirements.txt    # adds PDF and file-upload support
python seed.py                     # adds the mentor account, events and session times
```

Then restart the backend. Your existing accounts, profiles and applications stay as they are, and the database gets its new tables and columns automatically.

---

## 4. Run the tests

```bash
cd backend
source .venv/bin/activate
pytest -v
```

There are **76 automated tests**. They cover validation, authorization, privacy and consent rules, record saving, error cases, the database upgrade, and the AI engine (NFR-11). Tests always use the built-in AI engine and a throwaway in-memory database, so they never touch your data or call a paid API.

---

## 5. The AI features

The résumé match, skill-gap analysis and interview feedback work **without any API key**. They use a built-in engine (`backend/app/ai/local_engine.py`) that:

- recognizes about 100 skills in résumés and job descriptions, telling "Java" apart from "JavaScript" and "SQL" apart from "MySQL";
- weighs required skills above "nice to have" ones, and treats "Python **or** Java" as satisfied by either one;
- explains every match by quoting the job line and the résumé line behind it (NFR-09);
- separates skills you're **missing** from skills on your profile that your résumé **doesn't show yet** (PB-21);
- scores interview answers on structure (situation, your actions, the result, measurable impact, filler words) and says what in the answer led to each point.

**To use Claude instead:** add your key to `backend/.env`:

```
ANTHROPIC_API_KEY=sk-ant-...
```

Then restart the backend. If a Claude call ever fails, the built-in engine answers instead, and the result says "local (fallback)" (NFR-07). Every AI result is labeled advisory (NFR-08).

---

## 6. Backlog traceability: all 36 stories

| Story | What it does | API | Screen |
|---|---|---|---|
| PB-01 | Create account | `POST /api/auth/register` | Create account |
| PB-02 | Sign in | `POST /api/auth/login` | Sign in |
| PB-03 | Validation messages | `schemas.py` + handler in `main.py` | every form |
| PB-04 | Create profile | `POST /api/profile` | Profile |
| PB-05 | Edit profile | `PUT /api/profile` | Profile |
| PB-06 | View profile | `GET /api/profile` | Profile |
| PB-07 | Add application | `POST /api/applications` | Applications → Add |
| PB-08 | View applications | `GET /api/applications` | Applications |
| PB-09 | Update status | `PATCH /api/applications/{id}/status` | Applications (dropdown) |
| PB-10 | Edit application | `PUT /api/applications/{id}` | Applications → Edit |
| PB-11 | Sign out | `POST /api/auth/logout` (revokes token) | top bar |
| PB-12 | Delete application | `DELETE /api/applications/{id}` | Applications → Delete |
| PB-13 | Filter by status | `GET /api/applications?status=` | Applications |
| PB-14 | Browse jobs | `GET /api/opportunities` | Jobs & Events |
| PB-15 | Event details | `GET /api/opportunities?kind=event` | Jobs & Events → Events |
| PB-16 | Publish a job | `POST /api/opportunities` | Admin → Content |
| PB-17 | Publish events/announcements | `POST /api/opportunities` (kind) | Admin → Content |
| PB-18 | Add a résumé (PDF/DOCX/TXT/paste) | `POST /api/resumes/upload`, `/text` | Resume |
| PB-19 | Replace a résumé (versions) | `POST /api/resumes/{id}/make-current` | Resume |
| PB-20 | Compare résumé with job | `POST /api/match` | Resume Match |
| PB-21 | Skill gaps | `result.missing`, `result.under_evidenced` | Resume Match |
| PB-22 | Explain AI suggestions | `result.matched[].evidence/requirement` | Resume Match |
| PB-23 | Start mock interview | `POST /api/interviews` | Mock Interview |
| PB-24 | Submit an answer | `POST /api/interviews/{id}/answers` | Mock Interview |
| PB-25 | Review feedback | answer `feedback` | Mock Interview |
| PB-26 | Request mentor support | `POST /api/mentoring/requests` | Mentors |
| PB-27 | Accept/decline/update requests | `/api/mentor/requests/{id}/accept`, `/decline`, `/status` | Mentor → Requests |
| PB-28 | Review materials, give feedback | `GET /api/mentor/requests/{id}`, `POST …/feedback` | Mentor → Requests |
| PB-29 | Monitor supported students | `GET /api/mentor/students` | Mentor → My Students |
| PB-30 | Manage accounts and roles | `GET/PATCH /api/admin/users` | Admin → Users |
| PB-31 | Set mentor availability | `/api/mentor/slots` | Mentor → Availability |
| PB-32 | Book a mentor session | `POST /api/mentoring/requests` with `slot_id` | Mentors → Book |
| PB-33 | View request status and feedback | `GET /api/mentoring/requests` | Mentors → My requests |
| PB-34 | Update or archive content | `PUT /api/opportunities/{id}`, `PATCH …/status` | Admin → Content |
| PB-35 | View past match results | `GET /api/match` | Resume Match → Past results |
| PB-36 | Platform analytics | `GET /api/admin/analytics` | Admin → Analytics |

---

## 7. Full demo script

**Student**
1. Create an account. Try empty fields and a weak password first to show validation.
2. Fill in your **Profile**. List a skill like Docker that isn't on your résumé, to show the "under-evidenced" check later.
3. **Applications**: add a few, change a status from the table, filter by status, edit one.
4. **Resume**: upload a PDF or Word résumé (or paste text). Upload a second version, then switch back to the first.
5. **Jobs & Events**: open a listing and click **Compare my resume**. Walk through the score, the quoted evidence, the gaps and the suggestions. Check **Past results**.
6. **Mock Interview**: start from a listing, answer one question well (situation, action, result with a number) and one badly ("um, we kind of fixed it"), and compare the feedback.
7. **Mentors**: book an open time, ticking what to share. Also send a general resume-review request.

**Mentor** (`mentor@careerprep.com`)

8. **Requests**: open the general request. The materials are locked until you accept it. Accept, review the shared résumé, send feedback, and mark it completed.
9. **Availability**: add a new time. **My Students**: see progress for students who shared it.

**Student again**

10. **Mentors → My requests**: the status and the mentor's feedback are visible.

**Admin** (`admin@careerprep.com`)

11. **Content**: publish an event and an announcement, edit a listing, archive one, and confirm it disappears for students.
12. **Users**: promote a student to mentor, or deactivate an account (that user is signed out immediately).
13. **Analytics**: weekly activity, average match score, and request statuses, all as totals.

**Access control:** while signed in as a student, visit `http://localhost:5173/admin/users`. You're sent back to your own home page.

---

## 8. Implementation decisions (requirements Section 7)

- **Authentication:** email and password hashed with bcrypt. Sign-in issues a 60-minute JWT. Sign-out revokes the token. Deactivated accounts are rejected on every request.
- **Roles:** self-registration creates students. Admins promote users to mentor or admin. The last active admin can't be removed, and admins can't lock themselves out.
- **Résumé files:** PDF, DOCX and TXT up to 2 MB, or pasted text. **Only the extracted text is stored**, never the file (NFR-02). Every upload is kept as a version, and one is current.
- **Mock-interview answers:** typed text. Each answer and its feedback are saved, so sessions can be reviewed later.
- **AI outputs are saved:** match results and interview feedback are stored for history (PB-35) and aggregate analytics (PB-36).
- **Mentor assignment:** open requests go to a shared queue, and any mentor can accept one. Booking a mentor's time slot assigns that mentor directly.
- **Consent:** on every request, the student chooses whether to share their profile, current résumé and progress summary. Only the mentor who takes the request sees those items, and only after accepting. Application notes and interview answers are never shared.
- **Database:** SQLite locally. New tables and columns are added automatically on startup. For PostgreSQL, install `psycopg[binary]` and change `DATABASE_URL`.

---

## 9. Project structure

```
backend/app/
  main.py            app setup, error handling, routes
  models.py          all database tables
  schemas.py         request/response shapes and validation
  ai/                AI layer: built-in engine, Claude engine, skill vocabulary
  services/          business rules (accounts, résumés, analysis, interviews, mentorship, admin…)
  routers/           HTTP endpoints, one file per epic
backend/tests/       76 pytest tests
frontend/src/
  pages/             student pages; pages/mentor and pages/admin for the other roles
  components/        shared pieces (forms, cards, match results, feedback, progress)
```

---

## 10. Troubleshooting

| Problem | Fix |
|---|---|
| "Can't reach the server" | The backend isn't running. Start Terminal 1. |
| `uvicorn: command not found` | Activate the virtual environment first (`source .venv/bin/activate`). |
| Résumé upload says PDF support isn't installed | Run `pip install -r requirements.txt` again. |
| A scanned PDF has "not enough text" | It's an image. Paste the résumé text instead. |
| Want a clean database | Stop the backend, delete `backend/careerprep.db`, run `python seed.py`, and restart. |
| Port already in use | Stop the other program, or change the port (`--port 8001`) and update `frontend/vite.config.js`. |
