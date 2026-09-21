import React, { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { supabase } from '../supabaseClient';
import { useAuth } from '../context/AuthContext.jsx';
import './AdminDashboard.css';

/* ── Constants ─────────────────────────────────────────────────── */
const ROLE_META = {
  Technical: { icon: '⚙️', gradient: 'linear-gradient(135deg, hsl(215,80%,48%), hsl(240,75%,55%))' },
  Academy:   { icon: '🎓', gradient: 'linear-gradient(135deg, hsl(270,70%,50%), hsl(295,65%,55%))' },
  HR:        { icon: '👥', gradient: 'linear-gradient(135deg, hsl(340,70%,50%), hsl(15,75%,55%))' },
  General:   { icon: '📋', gradient: 'linear-gradient(135deg, hsl(170,60%,40%), hsl(195,65%,48%))' },
};

const PRIORITY_CONFIG = {
  Low:      { color: 'hsl(140,55%,50%)',  bg: 'hsla(140,55%,50%,0.12)', border: 'hsla(140,55%,50%,0.3)',  order: 4 },
  Medium:   { color: 'hsl(45,80%,55%)',   bg: 'hsla(45,80%,55%,0.12)',  border: 'hsla(45,80%,55%,0.3)',   order: 3 },
  High:     { color: 'hsl(25,85%,58%)',   bg: 'hsla(25,85%,58%,0.12)',  border: 'hsla(25,85%,58%,0.3)',   order: 2 },
  Critical: { color: 'hsl(0,75%,60%)',    bg: 'hsla(0,75%,60%,0.12)',   border: 'hsla(0,75%,60%,0.3)',    order: 1 },
};

const STATUS_CONFIG = {
  Open:         { color: 'hsl(215,80%,65%)', bg: 'hsla(215,80%,65%,0.12)', border: 'hsla(215,80%,65%,0.3)' },
  'In Progress':{ color: 'hsl(45,80%,60%)',  bg: 'hsla(45,80%,60%,0.12)',  border: 'hsla(45,80%,60%,0.3)'  },
  Resolved:     { color: 'hsl(140,55%,55%)', bg: 'hsla(140,55%,55%,0.12)', border: 'hsla(140,55%,55%,0.3)' },
};

const STATUSES = ['Open', 'In Progress', 'Resolved'];

/* ── Helpers ───────────────────────────────────────────────────── */
function timeAgo(dateStr) {
  const diff = Date.now() - new Date(dateStr).getTime();
  const mins  = Math.floor(diff / 60000);
  const hours = Math.floor(diff / 3600000);
  const days  = Math.floor(diff / 86400000);
  if (mins < 2)   return 'Just now';
  if (mins < 60)  return `${mins}m ago`;
  if (hours < 24) return `${hours}h ago`;
  return `${days}d ago`;
}

/* ── Ticket Card ───────────────────────────────────────────────── */
const TicketCard = ({ ticket, onStatusChange }) => {
  const p = PRIORITY_CONFIG[ticket.priority] || PRIORITY_CONFIG.Medium;
  const s = STATUS_CONFIG[ticket.status]     || STATUS_CONFIG.Open;

  return (
    <div
      className="ticket-card"
      style={{ borderLeftColor: p.color }}
    >
      <div className="ticket-card-header">
        <span
          className="priority-badge"
          style={{ color: p.color, background: p.bg, border: `1px solid ${p.border}` }}
        >
          {ticket.priority}
        </span>
        <span className="ticket-time">{timeAgo(ticket.created_at)}</span>
      </div>

      <p className="ticket-username">👤 {ticket.username}</p>

      <p className="ticket-summary">{ticket.summary || ticket.original_query}</p>

      {ticket.original_query && ticket.summary && (
        <details className="ticket-original">
          <summary>View original query</summary>
          <p>{ticket.original_query}</p>
        </details>
      )}

      <div className="ticket-card-footer">
        <span
          className="status-badge"
          style={{ color: s.color, background: s.bg, border: `1px solid ${s.border}` }}
        >
          {ticket.status}
        </span>
        <select
          className="status-select"
          value={ticket.status}
          onChange={(e) => onStatusChange(ticket.id, e.target.value)}
          aria-label="Change ticket status"
        >
          {STATUSES.map((st) => (
            <option key={st} value={st}>{st}</option>
          ))}
        </select>
      </div>
    </div>
  );
};

/* ── AdminDashboard ────────────────────────────────────────────── */
const AdminDashboard = () => {
  const { user, logout, loading: authLoading } = useAuth();
  const navigate = useNavigate();

  const [tickets, setTickets]       = useState([]);
  const [fetching, setFetching]     = useState(true);
  const [fetchError, setFetchError] = useState('');
  const [search, setSearch]         = useState('');
  const [filterStatus, setFilterStatus] = useState('All');

  /* ── Redirect if not logged in ── */
  useEffect(() => {
    if (!authLoading && !user) {
      navigate('/admin/login', { replace: true });
    }
  }, [user, authLoading, navigate]);

  /* ── Fetch tickets ── */
  const fetchTickets = useCallback(async () => {
    if (!user?.role) return;
    setFetching(true);
    setFetchError('');
    try {
      const { data, error } = await supabase
        .from('tickets')
        .select('*')
        .eq('category', user.role)
        .order('created_at', { ascending: false });

      if (error) throw error;
      setTickets(data || []);
    } catch (err) {
      setFetchError('Failed to load tickets: ' + err.message);
    } finally {
      setFetching(false);
    }
  }, [user?.role]);

  useEffect(() => {
    if (user?.role) fetchTickets();
  }, [user?.role, fetchTickets]);

  /* ── Realtime subscription ── */
  useEffect(() => {
    if (!user?.role) return;
    const channel = supabase
      .channel('tickets-changes')
      .on(
        'postgres_changes',
        { event: '*', schema: 'public', table: 'tickets', filter: `category=eq.${user.role}` },
        () => fetchTickets()
      )
      .subscribe();

    return () => supabase.removeChannel(channel);
  }, [user?.role, fetchTickets]);

  /* ── Status update ── */
  const handleStatusChange = async (ticketId, newStatus) => {
    // Optimistic update
    setTickets((prev) =>
      prev.map((t) => (t.id === ticketId ? { ...t, status: newStatus } : t))
    );
    const { error } = await supabase
      .from('tickets')
      .update({ status: newStatus })
      .eq('id', ticketId);

    if (error) {
      console.error('Status update failed:', error);
      fetchTickets(); // revert by re-fetching
    }
  };

  /* ── Logout ── */
  const handleLogout = async () => {
    await logout();
    navigate('/admin/login', { replace: true });
  };

  /* ── Derived state ── */
  const stats = {
    total:      tickets.length,
    open:       tickets.filter((t) => t.status === 'Open').length,
    inProgress: tickets.filter((t) => t.status === 'In Progress').length,
    resolved:   tickets.filter((t) => t.status === 'Resolved').length,
  };

  const filtered = tickets
    .filter((t) =>
      filterStatus === 'All' || t.status === filterStatus
    )
    .filter((t) =>
      !search.trim() ||
      t.username?.toLowerCase().includes(search.toLowerCase()) ||
      t.summary?.toLowerCase().includes(search.toLowerCase()) ||
      t.original_query?.toLowerCase().includes(search.toLowerCase())
    )
    .sort((a, b) =>
      (PRIORITY_CONFIG[a.priority]?.order || 99) -
      (PRIORITY_CONFIG[b.priority]?.order || 99)
    );

  const roleMeta = ROLE_META[user?.role] || ROLE_META.General;

  /* ── Render guards ── */
  if (authLoading) {
    return (
      <div className="dash-loading-screen">
        <span className="spinner-lg" />
        <p>Loading…</p>
      </div>
    );
  }

  if (!user) return null;

  return (
    <div className="dash-page">

      {/* ── Header ── */}
      <header className="dash-header">
        <div className="dash-header-left">
          <div
            className="role-icon-badge"
            style={{ background: roleMeta.gradient }}
          >
            {roleMeta.icon}
          </div>
          <div>
            <h1 className="dash-title">{user.role} Dashboard</h1>
            <p className="dash-sub">Welcome back, <strong>{user.name}</strong></p>
          </div>
        </div>
        <div className="dash-header-right">
          <span className="header-email">{user.email}</span>
          <button className="logout-btn" onClick={handleLogout} id="logout-btn">
            Sign Out
          </button>
        </div>
      </header>

      {/* ── Stats bar ── */}
      <div className="stats-bar">
        {[
          { label: 'Total',       value: stats.total,      accent: 'hsl(220,20%,60%)' },
          { label: 'Open',        value: stats.open,       accent: 'hsl(215,80%,65%)' },
          { label: 'In Progress', value: stats.inProgress, accent: 'hsl(45,80%,60%)'  },
          { label: 'Resolved',    value: stats.resolved,   accent: 'hsl(140,55%,55%)' },
        ].map(({ label, value, accent }) => (
          <div key={label} className="stat-card">
            <span className="stat-value" style={{ color: accent }}>{value}</span>
            <span className="stat-label">{label}</span>
          </div>
        ))}
      </div>

      {/* ── Filters ── */}
      <div className="dash-toolbar">
        <div className="search-wrapper">
          <span className="search-icon">🔍</span>
          <input
            type="text"
            className="search-input"
            placeholder="Search by name, summary…"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            id="ticket-search"
          />
        </div>
        <div className="filter-tabs">
          {['All', ...STATUSES].map((st) => (
            <button
              key={st}
              className={`filter-tab ${filterStatus === st ? 'active' : ''}`}
              onClick={() => setFilterStatus(st)}
            >
              {st}
            </button>
          ))}
        </div>
        <button className="refresh-btn" onClick={fetchTickets} title="Refresh tickets">
          🔄
        </button>
      </div>

      {/* ── Ticket grid ── */}
      <main className="dash-main">
        {fetching ? (
          <div className="center-message">
            <span className="spinner-lg" />
            <p>Loading tickets…</p>
          </div>
        ) : fetchError ? (
          <div className="error-banner">{fetchError}</div>
        ) : filtered.length === 0 ? (
          <div className="center-message">
            <p className="empty-icon">📭</p>
            <p>No tickets found{search || filterStatus !== 'All' ? ' for the current filters.' : '.'}</p>
          </div>
        ) : (
          <div className="tickets-grid">
            {filtered.map((ticket) => (
              <TicketCard
                key={ticket.id}
                ticket={ticket}
                onStatusChange={handleStatusChange}
              />
            ))}
          </div>
        )}
      </main>
    </div>
  );
};

export default AdminDashboard;
