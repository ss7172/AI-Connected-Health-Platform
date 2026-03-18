import { useState, useEffect } from 'react';
import { api } from '../../api/client';
import Navbar from '../common/Navbar';
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';

export default function Dashboard() {
  const [summary, setSummary] = useState(null);
  const [revenue, setRevenue] = useState(null);
  const [deptStats, setDeptStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

 
  useEffect(() => {
    const fetchData = async () => {
      try {
        const [summaryData, revenueData, deptData] = await Promise.all([
          api.get('/dashboard/summary'),
          api.get('/dashboard/revenue?period=30days'),
          api.get('/dashboard/department-stats'),
        ]);
        setSummary(summaryData);
        setRevenue(revenueData);
        setDeptStats(deptData.departments);
      } catch (err) {
        setError('Failed to load dashboard data');
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, []);

  if (loading) {
    return (
      <div style={styles.center}>
        <p>Loading dashboard...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div style={styles.center}>
        <p style={{ color: 'red' }}>{error}</p>
      </div>
    );
  }

  return (
    <div style={{ minHeight: '100vh', backgroundColor: '#f7fafc', fontFamily: 'system-ui, sans-serif' }}>
      <Navbar />
      <div style={{ padding: '2rem' }}>

        {/* Page title */}
        <div style={{ marginBottom: '2rem' }}>
          <h1 style={styles.title}>Dashboard</h1>
          <p style={styles.subtitle}>
            {new Date().toLocaleDateString('en-IN', {
              weekday: 'long',
              year: 'numeric',
              month: 'long',
              day: 'numeric',
            })}
          </p>
        </div>

        {/* Today's Stats */}
        <div style={styles.statsGrid}>
          <StatCard
            label="Today's Appointments"
            value={summary.today.appointments.total}
            sub={`${summary.today.appointments.completed} completed`}
            color="#3182ce"
          />
          <StatCard
            label="Scheduled"
            value={summary.today.appointments.scheduled}
            sub="waiting"
            color="#ed8936"
          />
          <StatCard
            label="Today's Revenue"
            value={`₹${summary.today.revenue.toLocaleString('en-IN')}`}
            sub="collected today"
            color="#38a169"
          />
          <StatCard
            label="Pending Payments"
            value={summary.pending_payments.count}
            sub={`₹${summary.pending_payments.amount.toLocaleString('en-IN')} outstanding`}
            color="#e53e3e"
          />
          <StatCard
            label="Total Patients"
            value={summary.patients.total_active.toLocaleString('en-IN')}
            sub={`${summary.patients.new_this_month} new this month`}
            color="#805ad5"
          />
        </div>

        {/* Revenue Summary */}
        <div style={styles.section}>
        <h2 style={styles.sectionTitle}>Revenue — Last 30 Days</h2>
        <div style={styles.revenueCards}>
            <div style={styles.revenueCard}>
            <p style={styles.revenueLabel}>Total</p>
            <p style={styles.revenueValue}>
                ₹{revenue.summary.total.toLocaleString('en-IN')}
            </p>
            </div>
            <div style={styles.revenueCard}>
            <p style={styles.revenueLabel}>Consultation</p>
            <p style={{ ...styles.revenueValue, color: '#3182ce' }}>
                ₹{revenue.summary.consultation.toLocaleString('en-IN')}
            </p>
            </div>
            <div style={styles.revenueCard}>
            <p style={styles.revenueLabel}>Tests & Procedures</p>
            <p style={{ ...styles.revenueValue, color: '#38a169' }}>
                ₹{revenue.summary.tests_and_procedures.toLocaleString('en-IN')}
            </p>
            </div>
        </div>
        <div style={{ marginTop: '1.5rem' }}>
            <RevenueChart data={revenue.data} />
        </div>
        </div>

        {/* Department Stats */}
        <div style={styles.section}>
          <h2 style={styles.sectionTitle}>Department Performance — This Month</h2>
          <table style={styles.table}>
            <thead>
              <tr>
                {['Department', 'Appointments', 'Completed', 'Completion %', 'Revenue'].map(h => (
                  <th key={h} style={styles.th}>{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {deptStats.map(dept => (
                <tr key={dept.department_id} style={styles.tr}>
                  <td style={styles.td}>{dept.department_name}</td>
                  <td style={styles.td}>{dept.monthly_appointments}</td>
                  <td style={styles.td}>{dept.monthly_completed}</td>
                  <td style={styles.td}>{dept.completion_rate}%</td>
                  <td style={styles.td}>
                    ₹{dept.monthly_revenue.toLocaleString('en-IN')}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

      </div>
    </div>
  );

}

function StatCard({ label, value, sub, color }) {
  return (
    <div style={styles.card}>
      <div style={{ ...styles.cardAccent, backgroundColor: color }} />
      <p style={styles.cardLabel}>{label}</p>
      <p style={{ ...styles.cardValue, color }}>{value}</p>
      <p style={styles.cardSub}>{sub}</p>
    </div>
  );
}

function RevenueChart({ data }) {
  const chartData = data.map(d => ({
    date: d.date.slice(5), // Show MM-DD only
    Consultation: d.consultation,
    'Tests & Procedures': d.test + d.procedure,
  }));

  return (
    <ResponsiveContainer width="100%" height={250}>
      <AreaChart data={chartData} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
        <defs>
          <linearGradient id="colorConsultation" x1="0" y1="0" x2="0" y2="1">
            <stop offset="5%" stopColor="#3182ce" stopOpacity={0.3} />
            <stop offset="95%" stopColor="#3182ce" stopOpacity={0} />
          </linearGradient>
          <linearGradient id="colorTests" x1="0" y1="0" x2="0" y2="1">
            <stop offset="5%" stopColor="#38a169" stopOpacity={0.3} />
            <stop offset="95%" stopColor="#38a169" stopOpacity={0} />
          </linearGradient>
        </defs>
        <CartesianGrid strokeDasharray="3 3" stroke="#f0f4f8" />
        <XAxis
          dataKey="date"
          tick={{ fontSize: 11, fill: '#718096' }}
          tickLine={false}
          interval={4}
        />
        <YAxis
          tick={{ fontSize: 11, fill: '#718096' }}
          tickLine={false}
          axisLine={false}
          tickFormatter={v => `₹${(v/1000).toFixed(0)}k`}
        />
        <Tooltip
          formatter={(value) => [`₹${value.toLocaleString('en-IN')}`, '']}
          contentStyle={{ fontSize: '0.8rem', borderRadius: '6px' }}
        />
        <Legend wrapperStyle={{ fontSize: '0.8rem' }} />
        <Area
          type="monotone"
          dataKey="Consultation"
          stroke="#3182ce"
          strokeWidth={2}
          fill="url(#colorConsultation)"
        />
        <Area
          type="monotone"
          dataKey="Tests & Procedures"
          stroke="#38a169"
          strokeWidth={2}
          fill="url(#colorTests)"
        />
      </AreaChart>
    </ResponsiveContainer>
  );
}

const styles = {
  container: {
    minHeight: '100vh',
    backgroundColor: '#f7fafc',
    fontFamily: 'system-ui, sans-serif',
    padding: '2rem',
  },
  center: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    minHeight: '100vh',
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
  statsGrid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
    gap: '1rem',
    marginBottom: '2rem',
  },
  card: {
    backgroundColor: 'white',
    borderRadius: '10px',
    padding: '1.25rem',
    boxShadow: '0 1px 3px rgba(0,0,0,0.06)',
    position: 'relative',
    overflow: 'hidden',
  },
  cardAccent: {
    position: 'absolute',
    top: 0,
    left: 0,
    right: 0,
    height: '3px',
  },
  cardLabel: {
    fontSize: '0.8rem',
    color: '#718096',
    fontWeight: '600',
    textTransform: 'uppercase',
    letterSpacing: '0.05em',
    margin: '0.5rem 0 0.5rem',
  },
  cardValue: {
    fontSize: '1.75rem',
    fontWeight: '700',
    margin: '0 0 0.25rem',
  },
  cardSub: {
    fontSize: '0.8rem',
    color: '#a0aec0',
    margin: 0,
  },
  section: {
    backgroundColor: 'white',
    borderRadius: '10px',
    padding: '1.5rem',
    boxShadow: '0 1px 3px rgba(0,0,0,0.06)',
    marginBottom: '1.5rem',
  },
  sectionTitle: {
    fontSize: '1rem',
    fontWeight: '700',
    color: '#2d3748',
    margin: '0 0 1.25rem',
  },
  revenueCards: {
    display: 'grid',
    gridTemplateColumns: 'repeat(3, 1fr)',
    gap: '1rem',
  },
  revenueCard: {
    backgroundColor: '#f7fafc',
    borderRadius: '8px',
    padding: '1rem',
    textAlign: 'center',
  },
  revenueLabel: {
    fontSize: '0.8rem',
    color: '#718096',
    margin: '0 0 0.5rem',
    fontWeight: '600',
    textTransform: 'uppercase',
  },
  revenueValue: {
    fontSize: '1.5rem',
    fontWeight: '700',
    color: '#2d3748',
    margin: 0,
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
  },
  tr: {
    borderBottom: '1px solid #f0f4f8',
  },
  td: {
    padding: '0.875rem 1rem',
    fontSize: '0.9rem',
    color: '#2d3748',
  },
};