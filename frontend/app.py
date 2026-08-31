import os
from typing import Any

import requests
import streamlit as st

DEFAULT_BACKEND_URL = os.getenv("BACKEND_URL", "http://127.0.0.1:8734")

st.set_page_config(page_title="AI Interview Simulation", page_icon="🧠", layout="wide")

st.markdown(
    """
    <style>
        .stApp {
            background: linear-gradient(180deg, #0f172a 0%, #111827 10%, #f8fafc 10%, #f8fafc 100%);
        }
        .block-container {
            padding-top: 2rem;
            padding-bottom: 2rem;
        }
        .main .block-container {
            max-width: 1400px;
        }
        div[data-testid="stSidebar"] {
            background: rgba(15, 23, 42, 0.96);
            color: white;
        }
        [data-testid="stSidebar"] .stButton > button,
        [data-testid="stSidebar"] .stTextInput > div {
            border-radius: 0.75rem;
        }
        .metric-card {
            background: white;
            border: 1px solid #e2e8f0;
            border-radius: 0.9rem;
            padding: 0.8rem 1rem;
            box-shadow: 0 4px 16px rgba(15, 23, 42, 0.04);
        }
        .status-pill {
            display: inline-block;
            padding: 0.25rem 0.65rem;
            border-radius: 999px;
            background: #e0f2fe;
            color: #075985;
            font-weight: 600;
            font-size: 0.75rem;
        }
    </style>
    """,
    unsafe_allow_html=True,
)


def init_state() -> None:
    defaults: dict[str, Any] = {
        "backend_url": DEFAULT_BACKEND_URL,
        "session_id": None,
        "current_question": None,
        "history": [],
        "score": 0,
        "user_name": "Karthik",
        "token": None,
        "auth_user": None,
        "resume_name": None,
        "resume_path": None,
    }
    for key, value in defaults.items():
        st.session_state.setdefault(key, value)


init_state()


def current_backend_url() -> str:
    return st.session_state.get("backend_url", DEFAULT_BACKEND_URL)


def reset_interview_state() -> None:
    st.session_state.session_id = None
    st.session_state.current_question = None
    st.session_state.history = []
    st.session_state.score = 0


def _auth_headers() -> dict[str, str]:
    token = st.session_state.get("token")
    if token:
        return {"Authorization": f"Bearer {token}"}
    return {}


def _api_request(method: str, path: str, **kwargs: Any) -> Any:
    response = requests.request(
        method,
        f"{current_backend_url().rstrip('/')}{path}",
        timeout=kwargs.pop("timeout", 30),
        **kwargs,
    )
    try:
        payload = response.json()
    except ValueError:
        payload = {"detail": response.text}

    if not response.ok:
        detail = payload.get("detail", payload) if isinstance(payload, dict) else payload
        raise requests.HTTPError(str(detail))
    return payload


def api_health() -> dict[str, Any] | None:
    try:
        return _api_request("GET", "/health", timeout=3)
    except Exception:
        return None


def api_register(username: str, password: str, email: str | None = None):
    payload = {"username": username, "password": password}
    if email:
        payload["email"] = email
    return _api_request("POST", "/auth/register", json=payload, timeout=10)


def api_login(username: str, password: str):
    return _api_request(
        "POST",
        "/auth/login",
        json={"username": username, "password": password},
        timeout=10,
    )


def api_me():
    return _api_request("GET", "/auth/me", headers=_auth_headers(), timeout=10)


def api_upload_resume(file):
    return _api_request(
        "POST",
        "/resume/upload_resume",
        files={"file": (file.name, file.getvalue(), "application/pdf")},
        headers=_auth_headers(),
        timeout=60,
    )


def api_start_interview(user_name: str):
    return _api_request(
        "POST",
        "/interview/start",
        json={"user_name": user_name},
        headers=_auth_headers(),
        timeout=30,
    )


def api_submit_answer(session_id: int, answer: str):
    return _api_request(
        "POST",
        "/interview/answer",
        json={"session_id": session_id, "answer": answer},
        headers=_auth_headers(),
        timeout=60,
    )


def api_get_session(session_id: int):
    return _api_request("GET", f"/interview/session/{session_id}", headers=_auth_headers(), timeout=10)


st.title("AI Interview Simulation — RAG + LangGraph")
st.caption("Upload your resume, start a guided session, and receive structured scoring with adaptive follow-up questions.")

with st.sidebar:
    st.header("Settings")
    st.session_state.backend_url = st.text_input(
        "Backend URL",
        value=st.session_state.backend_url,
        help="FastAPI base URL",
        key="backend_url_input",
    )

    st.subheader("Auth")
    if st.session_state.token and st.session_state.auth_user:
        st.success(f"Logged in as {st.session_state.auth_user['username']}")
        if st.button("Logout", use_container_width=True):
            st.session_state.token = None
            st.session_state.auth_user = None
            reset_interview_state()
            st.rerun()
    else:
        with st.form("auth_form", clear_on_submit=False):
            auth_user = st.text_input("Username", key="auth_username_input")
            auth_pass = st.text_input("Password", type="password", key="auth_password_input")
            auth_email = st.text_input("Email (for register)", key="auth_email_input")
            c1, c2 = st.columns(2)
            with c1:
                login_clicked = st.form_submit_button("Login")
            with c2:
                register_clicked = st.form_submit_button("Register")

            if login_clicked:
                try:
                    token_payload = api_login(auth_user, auth_pass)
                    st.session_state.token = token_payload["access_token"]
                    st.session_state.auth_user = api_me()
                    st.success(f"Welcome {st.session_state.auth_user['username']}")
                    st.rerun()
                except Exception as exc:
                    st.error(f"Login failed: {exc}")

            if register_clicked:
                try:
                    api_register(auth_user, auth_pass, auth_email or None)
                    st.success("Registration successful — you can now log in.")
                except Exception as exc:
                    st.error(f"Registration failed: {exc}")

    st.session_state.user_name = st.text_input(
        "Candidate name",
        value=st.session_state.user_name,
        disabled=bool(st.session_state.token),
        key="candidate_name_input",
    )
    if st.session_state.token:
        st.caption(f"Authenticated user: {st.session_state.auth_user['username'] if st.session_state.auth_user else ''}")

    health = api_health()
    if health:
        st.markdown(f"<div class='status-pill'>Backend: {health.get('status', 'Healthy')}</div>", unsafe_allow_html=True)
    else:
        st.error(f"Backend unreachable at {current_backend_url()}")

    if st.button("Reset session", use_container_width=True):
        reset_interview_state()
        st.rerun()

    st.divider()
    st.markdown("**Flow**")
    st.markdown("1. Upload resume PDF\n2. Start interview\n3. Answer and review scoring")

    with st.expander("MCP / Agent"):
        st.caption("Try `GET /mcp/tools` and `POST /mcp/call` or `POST /agent/interview/start`")
        if st.button("List MCP tools"):
            try:
                response = _api_request("GET", "/mcp/tools", headers=_auth_headers(), timeout=5)
                st.json(response)
            except Exception as exc:
                st.error(str(exc))

# --- Layout ---
col_upload, col_interview = st.columns([1.05, 1.35])

with col_upload:
    st.subheader("1 — Upload Resume")
    uploaded = st.file_uploader("PDF only", type=["pdf"], help="Upload a resume to enrich the interview context.")
    if uploaded is not None:
        st.session_state.resume_name = uploaded.name
        st.session_state.resume_path = uploaded.name
        st.info(f"Selected file: {uploaded.name} ({uploaded.size / 1024:.1f} KB)")

    if uploaded is not None and st.button("Upload & Ingest", type="primary", use_container_width=True):
        with st.spinner("Uploading and ingesting resume…"):
            try:
                res = api_upload_resume(uploaded)
                st.success(res.get("message", "Resume uploaded successfully."))
                st.code(res.get("file_path", ""), language="text")
            except requests.HTTPError as exc:
                st.error(f"Upload failed: {exc}")
            except Exception as exc:
                st.error(f"Upload failed: {exc}")

    st.divider()
    st.subheader("2 — Start Interview")
    interview_disabled = not st.session_state.user_name.strip()
    if st.button("Start interview", type="primary", disabled=interview_disabled, use_container_width=True):
        try:
            with st.spinner("Generating opening question…"):
                data = api_start_interview(st.session_state.user_name.strip())
            st.session_state.session_id = data["session_id"]
            st.session_state.current_question = data.get("first_question")
            st.session_state.history = []
            st.session_state.score = 0
            st.success(f"Session #{data['session_id']} started successfully.")
        except Exception as exc:
            st.error(f"Start failed: {exc}")

    if st.session_state.session_id is not None:
        st.info(f"Session ID: {st.session_state.session_id} • User: {st.session_state.user_name}")
        if st.button("Refresh session from backend"):
            try:
                session = api_get_session(st.session_state.session_id)
                st.session_state.history = session.get("history", [])
                st.session_state.score = session.get("score", 0)
                if session.get("suggested_next_question"):
                    st.session_state.current_question = session["suggested_next_question"]
                st.success("Session synced from backend.")
            except Exception as exc:
                st.error(f"Could not refresh session: {exc}")

with col_interview:
    st.subheader("3 — Interview")

    if st.session_state.session_id is None:
        st.warning("Start an interview to begin.")
    else:
        metric_cols = st.columns(3)
        metric_cols[0].markdown(
            f"<div class='metric-card'><div>Current score</div><h2>{st.session_state.score}</h2></div>",
            unsafe_allow_html=True,
        )
        metric_cols[1].markdown(
            f"<div class='metric-card'><div>Turns</div><h2>{len(st.session_state.history)}</h2></div>",
            unsafe_allow_html=True,
        )
        metric_cols[2].markdown(
            "<div class='metric-card'><div>Status</div><h2>Live</h2></div>",
            unsafe_allow_html=True,
        )

        if st.session_state.current_question:
            st.markdown("**Current question:**")
            st.info(st.session_state.current_question)

        answer = st.text_area("Your answer", height=150, placeholder="Type your answer here…")
        if st.button("Submit answer", type="primary", disabled=not answer.strip(), use_container_width=True):
            with st.spinner("Evaluating response…"):
                try:
                    result = api_submit_answer(st.session_state.session_id, answer.strip())
                    st.session_state.current_question = result["next_question"]
                    st.session_state.score = result["current_score"]

                    if st.session_state.history:
                        last_question = st.session_state.history[-1].get("question", "—")
                    else:
                        last_question = "—"

                    st.session_state.history.append(
                        {
                            "question": last_question,
                            "answer": answer.strip(),
                            "score": result["score"],
                            "evaluation": result["evaluation"],
                            "next_question": result["next_question"],
                        }
                    )

                    try:
                        session = api_get_session(st.session_state.session_id)
                        st.session_state.history = session.get("history", st.session_state.history)
                        st.session_state.score = session.get("score", st.session_state.score)
                    except Exception:
                        pass

                    st.success(f"Score: {result['score']}/10 — {result['evaluation']}")
                    col_a, col_b = st.columns(2)
                    if result.get("strengths"):
                        col_a.markdown("**Strengths**\n- " + "\n- ".join(result["strengths"]))
                    if result.get("weaknesses"):
                        col_b.markdown("**Weaknesses**\n- " + "\n- ".join(result["weaknesses"]))
                except requests.HTTPError as exc:
                    st.error(f"Submit failed: {exc}")
                except Exception as exc:
                    st.error(f"Submit failed: {exc}")

        st.divider()
        st.markdown("**History**")
        if not st.session_state.history and st.session_state.session_id is not None:
            try:
                session = api_get_session(st.session_state.session_id)
                st.session_state.history = session.get("history", [])
            except Exception:
                pass

        if not st.session_state.history:
            st.caption("No turns yet — your interview will appear here as you answer.")
        else:
            for i, turn in enumerate(reversed(st.session_state.history), start=1):
                turn_number = len(st.session_state.history) - i + 1
                score = turn.get("score", turn.get("score_delta", "—"))
                eval_text = turn.get("evaluation", "")
                with st.expander(f"Turn {turn_number} — Score: {score} — {eval_text[:50]}", expanded=(i == 1)):
                    st.markdown(f"**Question:** {turn.get('question', '')}")
                    st.markdown(f"**Answer:** {turn.get('answer', '')}")
                    st.caption(f"Evaluation: {eval_text} | Next: {turn.get('next_question', '')}")

st.divider()
st.caption(
    "Backend: `POST /resume/upload_resume` → `POST /interview/start` → `POST /interview/answer` → `GET /interview/session/{id}` • Offline fallback when Ollama is unavailable."
)
