import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import './Dashboard.css';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';


const CATEGORY_META = {
  Technical: { icon: '⚙️', color: 'hsl(215, 80%, 60%)' },
  Academy: { icon: '🎓', color: 'hsl(270, 70%, 65%)' },
  HR: { icon: '👥', color: 'hsl(340, 70%, 60%)' },
  General: { icon: '📋', color: 'hsl(170, 60%, 50%)' },
};

const PRIORITY_META = {
  Low: { label: 'Low', color: 'hsl(140, 55%, 50%)' },
  Medium: { label: 'Medium', color: 'hsl(45,  80%, 55%)' },
  High: { label: 'High', color: 'hsl(25,  85%, 55%)' },
  Critical: { label: 'Critical', color: 'hsl(0,   75%, 58%)' },
};

const Dashboard = () => {
  const navigate = useNavigate();

  /* ── form state ── */
  const [username, setUsername]         = useState('');
  const [query, setQuery]               = useState('');
  const [submitting, setSubmitting]     = useState(false);
  const [errorMessage, setErrorMessage] = useState('');
  const [noticeMessage, setNoticeMessage] = useState(''); // polite notice for irrelevant queries

  /* ── success state ── */
  const [submitted, setSubmitted] = useState(false);
  const [ticketResult, setTicketResult] = useState(null); // extracted fields

  /* ── submit handler ── */
  const handleTicketSubmit = async (e) => {
    e.preventDefault();
    setErrorMessage('');
    setNoticeMessage('');
    if (!username.trim() || !query.trim()) return;

    // ── Instant frontend guard: minimum 4 words ──────────────────────
    const wordCount = query.trim().split(/\s+/).filter(Boolean).length;
    if (wordCount < 4) {
      setNoticeMessage(
        'Please enter detailed information about your problem. ' +
        'A short description helps us understand and resolve your issue faster.'
      );
      return; // no API call
    }

    try {
      setSubmitting(true);

      // Call Python backend — Groq LLM + Supabase insert happen server-side
      const response = await fetch(`${API_URL}/extract-ticket`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username: username.trim(), query: query.trim() }),
      });

      if (!response.ok) {
        const err = await response.json().catch(() => ({ detail: response.statusText }));
        if (response.status === 422) {
          // Polite notice — query not related to helpdesk
          setNoticeMessage(
            err.detail ||
            'Please enter a valid work-related query. We handle issues like system access, HR queries, Academy portal problems, and technical errors.'
          );
        } else {
          setErrorMessage('Server error: ' + (err.detail || response.statusText));
        }
        return;
      }

      const fields = await response.json(); // { username, category, priority, summary }

      setTicketResult(fields);
      setSubmitted(true);

      setTimeout(() => {
        setSubmitted(false);
        setTicketResult(null);
        setUsername('');
        setQuery('');
      }, 5000);
    } catch (err) {
      console.error('Submission failed:', err);
      setErrorMessage(
        err.message.includes('fetch')
          ? '⚠️ Cannot reach the backend. Make sure the Python server is running on port 8000.'
          : 'Submission failed: ' + err.message
      );
    } finally {
      setSubmitting(false);
    }
  };


  return (
    <div className="page-wrapper">

      {/* ── Admin login button (top-right corner) ── */}
      <div className="admin-corner">
        <button
          className="admin-toggle-btn"
          onClick={() => navigate('/admin/login')}
          id="admin-login-btn"
        >
          🛡️ Admin Login
        </button>
      </div>

      {/* ── Ticket submission section ── */}
      <section className="ticket-section">
        <div className="section-header">
          <div className="section-badge">Helpdesk Portal</div>
          <h1>Submit a Support Ticket</h1>
          <p>Describe your issue in plain language — our AI will classify and route it automatically.</p>
        </div>

        {submitted && ticketResult ? (
          <div className="success-card">
            <div className="success-icon">✅</div>
            <h3>Ticket Submitted!</h3>
            <p className="success-sub">Your query has been received and categorised.</p>
            <div className="ticket-meta-row">
              <span
                className="meta-badge category-badge"
                style={{
                  background: CATEGORY_META[ticketResult.category]?.color + '22',
                  color: CATEGORY_META[ticketResult.category]?.color,
                  border: `1px solid ${CATEGORY_META[ticketResult.category]?.color}44`
                }}
              >
                {CATEGORY_META[ticketResult.category]?.icon} {ticketResult.category}
              </span>
              <span
                className="meta-badge priority-badge"
                style={{
                  background: PRIORITY_META[ticketResult.priority]?.color + '22',
                  color: PRIORITY_META[ticketResult.priority]?.color,
                  border: `1px solid ${PRIORITY_META[ticketResult.priority]?.color}44`
                }}
              >
                🔔 {ticketResult.priority} Priority
              </span>
            </div>
            <p className="success-summary">"{ticketResult.summary}"</p>
          </div>
        ) : (
          <form className="ticket-form" onSubmit={handleTicketSubmit}>
            {noticeMessage && (
              <div className="form-notice">
                <span className="notice-icon">💬</span>
                <div className="notice-text">
                  <strong>Please enter a valid query</strong>
                  {noticeMessage}
                </div>
              </div>
            )}
            {errorMessage && (
              <div className="form-error">{errorMessage}</div>
            )}

            <div className="form-group">
              <label htmlFor="username">Your Name</label>
              <input
                id="username"
                type="text"
                placeholder="Enter your name"
                value={username}
                onChange={(e) => { setUsername(e.target.value); setErrorMessage(''); setNoticeMessage(''); }}
                required
              />
            </div>

            <div className="form-group">
              <label htmlFor="query">Describe Your Issue</label>
              <textarea
                id="query"
                placeholder="E.g. I am struggling to access the Academy page, it shows a blank screen after logging in..."
                value={query}
                onChange={(e) => { setQuery(e.target.value); setErrorMessage(''); setNoticeMessage(''); }}
                rows={6}
                required
              />
              <span className="field-hint">Our AI will automatically detect the category and priority.</span>
            </div>

            <button
              type="submit"
              className="submit-btn"
              id="submit-ticket-btn"
              disabled={submitting}
            >
              {submitting ? (
                <span className="btn-loading">
                  <span className="spinner" /> Analysing &amp; Submitting…
                </span>
              ) : (
                'Submit Ticket →'
              )}
            </button>
          </form>
        )}
      </section>
    </div>
  );
};

export default Dashboard;
