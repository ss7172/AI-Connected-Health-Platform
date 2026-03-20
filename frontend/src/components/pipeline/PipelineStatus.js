import { useState, useEffect } from 'react';
import { api } from '../../api/client';
import Navbar from '../common/Navbar';

const STATUS_COLORS = {
  success: { bg: '#f0fff4', color: '#276749', label: '✓ success' },
  failed:  { bg: '#fff5f5', color: '#c53030', label: '✗ failed' },
  running: { bg: '#ebf8ff', color: '#2b6cb0', label: '⟳ running' },
};

export default function PipelineStatus() {
  const [jobs, setJobs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [running, setRunning] = useState(false);
  const [error, setError] = useState('');
  const [lastRefresh, setLastRefresh] = useState(null);

  const fetchStatus = async () => {
    try {
      const data = await api.get('/pipeline/status');
      setJobs(data.jobs);
      setLastRefresh(new Date());
      setError('');
    } catch (err) {
      setError('Failed to load pipeline status');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchStatus();
  }, []);

  const handleRunPipeline = async () => {
    if (!window.confirm(
      'Run the full pipeline now? This will refresh all analytics tables.'
    )) return;

    setRunning(true);
    try {
      await api.post('/pipeline/run', {});
      await fetchStatus();
    } catch (err) {
      setError(err.error || 'Pipeline run failed');
    } finally {
      setRunning(false);
    }
  };

  const formatDuration = (seconds) => {
    if (!seconds) return '—';
    const s = parseFloat(seconds);
    if (s < 60) return `${s.toFixed(2)}s`;
    return `${(s / 60).toFixed(1)}m`;
  };

  const formatDate = (isoString) => {
    if (!isoString) return '—';
    return new Date(isoString).toLocaleString('en-IN', {
      day: 'numeric', month: 'short', year: 'numeric',
      hour: '2-digit', minute: '2-digit',
    });
  };

  const totalRows = jobs.reduce((sum, j) => sum + (j.rows_processed || 0), 0);
  const allSuccess = jobs.length > 0 && jobs.every(j => j.status === 'success');

  return (
    <div style={{ minHeight: '100vh', backgroundColor: '#f7fafc', fontFamily: 'system-ui, sans-serif' }}>
      <Navbar />
      <div style={{ padding: '2rem' }}>

        {/* Header */}
        <div style={styles.pageHeader}>
          <div>
            <h1 style={styles.title}>Pipeline Status</h1>
            <p style={styles.subtitle}>
              Clinical data pipeline — analytics schema
              {lastRefresh && ` · Last refreshed ${lastRefresh.toLocaleTimeString('en-IN')}`}
            </p>
          </div>
          <button
            onClick={handleRunPipeline}
            disabled={running}
            style={{
              ...styles.runBtn,
              opacity: running ? 0.7 : 1,
            }}
          >
            {running ? '⟳ Running...' : '▶ Run Pipeline Now'}
          </button>
        </div>

        {error && <div style={styles.errorBanner}>{error}</div>}

        {/* Summary Cards */}
        {!loading && jobs.length > 0 && (
          <div style={styles.summaryGrid}>
            <div style={styles.summaryCard}>
              <p style={styles.summaryLabel}>Total Rows</p>
              <p style={styles.summaryValue}>
                {totalRows.toLocaleString('en-IN')}
              </p>
            </div>
            <div style={styles.summaryCard}>
              <p style={styles.summaryLabel}>Jobs</p>
              <p style={styles.summaryValue}>{jobs.length}</p>
            </div>
            <div style={styles.summaryCard}>
              <p style={styles.summaryLabel}>Overall Status</p>
              <p style={{
                ...styles.summaryValue,
                color: allSuccess ? '#276749' : '#c53030',
                fontSize: '1rem',
                fontWeight: '700',
              }}>
                {allSuccess ? '✓ All Healthy' : '✗ Check Failures'}
              </p>
            </div>
            <div style={styles.summaryCard}>
              <p style={styles.summaryLabel}>RAG Corpus</p>
              <p style={styles.summaryValue}>
                {jobs.find(j => j.job_name === 'clinical_summaries')?.rows_processed?.toLocaleString('en-IN') || '—'}
                <span style={styles.summaryUnit}> summaries</span>
              </p>
            </div>
          </div>
        )}

        {/* Jobs Table */}
        <div style={styles.tableContainer}>
          {loading ? (
            <div style={styles.center}>Loading pipeline status...</div>
          ) : jobs.length === 0 ? (
            <div style={styles.center}>
              No pipeline runs found. Click "Run Pipeline Now" to start.
            </div>
          ) : (
            <table style={styles.table}>
              <thead>
                <tr>
                  {['Job', 'Status', 'Rows Processed', 'Duration', 'Last Run'].map(h => (
                    <th key={h} style={styles.th}>{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {jobs.map(job => {
                  const statusStyle = STATUS_COLORS[job.status] || STATUS_COLORS.running;
                  return (
                    <tr key={job.job_name} style={styles.tr}>
                      <td style={styles.td}>
                        <div style={styles.jobName}>{job.job_name}</div>
                        <div style={styles.jobDesc}>
                          {JOB_DESCRIPTIONS[job.job_name] || ''}
                        </div>
                      </td>
                      <td style={styles.td}>
                        <span style={{
                          ...styles.statusBadge,
                          backgroundColor: statusStyle.bg,
                          color: statusStyle.color,
                        }}>
                          {statusStyle.label}
                        </span>
                      </td>
                      <td style={styles.td}>
                        <strong>
                          {job.rows_processed?.toLocaleString('en-IN') || '—'}
                        </strong>
                      </td>
                      <td style={styles.td}>
                        {formatDuration(job.duration_seconds)}
                      </td>
                      <td style={styles.td}>
                        {formatDate(job.completed_at)}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          )}
        </div>

        {/* Analytics Tables Info */}
        <div style={styles.infoSection}>
          <h2 style={styles.infoTitle}>Analytics Schema</h2>
          <div style={styles.infoGrid}>
            {ANALYTICS_TABLES.map(table => (
              <div key={table.name} style={styles.infoCard}>
                <div style={styles.infoCardTop}>
                  <span style={styles.tableName}>{table.name}</span>
                  <span style={styles.tableRows}>
                    {jobs.find(j => j.job_name === table.job)?.rows_processed?.toLocaleString('en-IN') || '—'} rows
                  </span>
                </div>
                <p style={styles.tableDesc}>{table.description}</p>
              </div>
            ))}
          </div>
        </div>

      </div>
    </div>
  );
}

const JOB_DESCRIPTIONS = {
  revenue_analytics:    'Daily revenue by department — consultation vs tests/procedures',
  operational_metrics:  'Appointment funnel per doctor per day — utilization and completion rates',
  patient_analytics:    'Denormalized patient profiles with visit stats and risk flags',
  clinical_summaries:   'Structured text summaries per patient — RAG corpus for Clinical AI',
};

const ANALYTICS_TABLES = [
  {
    name: 'analytics.daily_revenue',
    job: 'revenue_analytics',
    description: 'Pre-computed revenue by department per day. Dashboard reads from this.',
  },
  {
    name: 'analytics.operational_metrics',
    job: 'operational_metrics',
    description: 'Appointment funnel metrics per doctor per day.',
  },
  {
    name: 'analytics.patient_profiles',
    job: 'patient_analytics',
    description: 'One row per active patient with aggregated visit and billing metrics.',
  },
  {
    name: 'analytics.patient_clinical_summaries',
    job: 'clinical_summaries',
    description: 'Structured text per patient. Input corpus for the RAG Clinical AI Assistant.',
  },
];

const styles = {
  pageHeader: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    marginBottom: '1.5rem',
  },
  title: {
    fontSize: '1.5rem',
    fontWeight: '700',
    color: '#1a202c',
    margin: '0 0 0.25rem',
  },
  subtitle: {
    color: '#718096',
    fontSize: '0.875rem',
    margin: 0,
  },
  runBtn: {
    backgroundColor: '#3182ce',
    color: 'white',
    border: 'none',
    padding: '0.6rem 1.25rem',
    borderRadius: '6px',
    fontSize: '0.9rem',
    fontWeight: '600',
    cursor: 'pointer',
    fontFamily: 'system-ui, sans-serif',
  },
  errorBanner: {
    backgroundColor: '#fff5f5',
    border: '1px solid #fc8181',
    color: '#c53030',
    padding: '0.75rem 1rem',
    borderRadius: '6px',
    marginBottom: '1rem',
    fontSize: '0.875rem',
  },
  summaryGrid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(4, 1fr)',
    gap: '1rem',
    marginBottom: '1.5rem',
  },
  summaryCard: {
    backgroundColor: 'white',
    borderRadius: '10px',
    padding: '1.25rem',
    boxShadow: '0 1px 3px rgba(0,0,0,0.06)',
  },
  summaryLabel: {
    fontSize: '0.75rem',
    fontWeight: '700',
    color: '#718096',
    textTransform: 'uppercase',
    letterSpacing: '0.05em',
    margin: '0 0 0.5rem',
  },
  summaryValue: {
    fontSize: '1.5rem',
    fontWeight: '700',
    color: '#1a202c',
    margin: 0,
  },
  summaryUnit: {
    fontSize: '0.8rem',
    fontWeight: '400',
    color: '#718096',
  },
  tableContainer: {
    backgroundColor: 'white',
    borderRadius: '10px',
    boxShadow: '0 1px 3px rgba(0,0,0,0.06)',
    overflow: 'hidden',
    marginBottom: '1.5rem',
  },
  center: {
    padding: '3rem',
    textAlign: 'center',
    color: '#718096',
  },
  table: {
    width: '100%',
    borderCollapse: 'collapse',
  },
  th: {
    textAlign: 'left',
    padding: '0.75rem 1rem',
    fontSize: '0.75rem',
    fontWeight: '700',
    color: '#718096',
    textTransform: 'uppercase',
    letterSpacing: '0.05em',
    borderBottom: '2px solid #e2e8f0',
    backgroundColor: '#f7fafc',
  },
  tr: {
    borderBottom: '1px solid #f0f4f8',
  },
  td: {
    padding: '0.875rem 1rem',
    fontSize: '0.9rem',
    color: '#2d3748',
  },
  jobName: {
    fontWeight: '600',
    color: '#2d3748',
    fontFamily: 'monospace',
    fontSize: '0.875rem',
  },
  jobDesc: {
    fontSize: '0.8rem',
    color: '#718096',
    marginTop: '0.2rem',
  },
  statusBadge: {
    padding: '0.25rem 0.6rem',
    borderRadius: '4px',
    fontSize: '0.8rem',
    fontWeight: '600',
  },
  infoSection: {
    backgroundColor: 'white',
    borderRadius: '10px',
    padding: '1.5rem',
    boxShadow: '0 1px 3px rgba(0,0,0,0.06)',
  },
  infoTitle: {
    fontSize: '1rem',
    fontWeight: '700',
    color: '#2d3748',
    margin: '0 0 1rem',
  },
  infoGrid: {
    display: 'grid',
    gridTemplateColumns: '1fr 1fr',
    gap: '1rem',
  },
  infoCard: {
    backgroundColor: '#f7fafc',
    borderRadius: '8px',
    padding: '1rem',
  },
  infoCardTop: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: '0.5rem',
  },
  tableName: {
    fontFamily: 'monospace',
    fontSize: '0.8rem',
    fontWeight: '700',
    color: '#2b6cb0',
  },
  tableRows: {
    fontSize: '0.8rem',
    fontWeight: '700',
    color: '#38a169',
  },
  tableDesc: {
    fontSize: '0.8rem',
    color: '#718096',
    margin: 0,
  },
};