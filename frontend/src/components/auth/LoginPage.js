import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';

export default function LoginPage() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const { login } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);

  try {
    const user = await login(email, password);
    if (user.role === 'admin') {
      navigate('/dashboard');
    } else {
      navigate('/appointments/today');
    }
  } catch (err) {
    setError(err.error || 'Login failed. Please try again.');
  } finally {
    setLoading(false);
  }
};

  return (
    <div style={styles.container}>
      <div style={styles.card}>
        <div style={styles.header}>
          <h1 style={styles.title}>Redmond Polyclinic</h1>
          <p style={styles.subtitle}>Patient Management System</p>
        </div>

        <form onSubmit={handleSubmit} style={styles.form}>
          {error && (
            <div style={styles.error}>{error}</div>
          )}

          <div style={styles.field}>
            <label style={styles.label}>Username</label>
            <input
              type="text"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="e.g. admin"
              required
              style={styles.input}
            />
          </div>



          <div style={styles.field}>
            <label style={styles.label}>Password</label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="Password"
              required
              style={styles.input}
            />
          </div>

          <button
            type="submit"
            disabled={loading}
            style={{
              ...styles.button,
              opacity: loading ? 0.7 : 1,
            }}
          >
            {loading ? 'Signing in...' : 'Sign In'}
          </button>
        </form>

                  {/* Demo credentials */}
            <div style={styles.demoBox}>
            <p style={styles.demoTitle}>Demo Credentials</p>
            <div style={styles.demoGrid}>
                <div>
                <p style={styles.demoRole}>Admin</p>
                <p style={styles.demoCred}>admin / admin123</p>
                </div>
                <div>
                <p style={styles.demoRole}>Doctor</p>
                <p style={styles.demoCred}>dr.mohanty / doctor123</p>
                </div>
                <div>
                <p style={styles.demoRole}>Front Desk</p>
                <p style={styles.demoCred}>frontdesk1 / front123</p>
                </div>
            </div>
            </div>
      </div>
    </div>
  );
}

const styles = {
  container: {
    minHeight: '100vh',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: '#f0f4f8',
    fontFamily: 'system-ui, sans-serif',
  },
  card: {
    backgroundColor: 'white',
    borderRadius: '12px',
    padding: '2.5rem',
    width: '100%',
    maxWidth: '400px',
    boxShadow: '0 4px 24px rgba(0,0,0,0.08)',
  },
  header: {
    textAlign: 'center',
    marginBottom: '2rem',
  },
  title: {
    fontSize: '1.5rem',
    fontWeight: '700',
    color: '#1a202c',
    margin: '0 0 0.25rem',
  },
  subtitle: {
    color: '#718096',
    fontSize: '0.9rem',
    margin: 0,
  },
  form: {
    display: 'flex',
    flexDirection: 'column',
    gap: '1.25rem',
  },
  error: {
    backgroundColor: '#fff5f5',
    border: '1px solid #fc8181',
    color: '#c53030',
    padding: '0.75rem 1rem',
    borderRadius: '6px',
    fontSize: '0.875rem',
  },
  field: {
    display: 'flex',
    flexDirection: 'column',
    gap: '0.5rem',
  },
  label: {
    fontSize: '0.875rem',
    fontWeight: '600',
    color: '#4a5568',
  },
  input: {
    padding: '0.75rem 1rem',
    border: '1px solid #e2e8f0',
    borderRadius: '6px',
    fontSize: '1rem',
    outline: 'none',
    transition: 'border-color 0.2s',
  },
  button: {
    backgroundColor: '#3182ce',
    color: 'white',
    padding: '0.75rem',
    borderRadius: '6px',
    border: 'none',
    fontSize: '1rem',
    fontWeight: '600',
    cursor: 'pointer',
    marginTop: '0.5rem',
  },
  demoBox: {
  marginTop: '1.5rem',
  backgroundColor: '#f7fafc',
  border: '1px solid #e2e8f0',
  borderRadius: '8px',
  padding: '1rem',
},
demoTitle: {
  fontSize: '0.75rem',
  fontWeight: '700',
  color: '#718096',
  textTransform: 'uppercase',
  letterSpacing: '0.05em',
  margin: '0 0 0.75rem',
},
demoGrid: {
  display: 'grid',
  gridTemplateColumns: 'repeat(3, 1fr)',
  gap: '0.5rem',
},
demoRole: {
  fontSize: '0.75rem',
  fontWeight: '700',
  color: '#4a5568',
  margin: '0 0 0.2rem',
},
demoCred: {
  fontSize: '0.8rem',
  color: '#718096',
  fontFamily: 'monospace',
  margin: 0,
},
};