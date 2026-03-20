import { useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';

const NAV_LINKS = [
  { path: '/dashboard', label: 'Dashboard', roles: ['admin'] },
  { path: '/patients', label: 'Patients', roles: ['admin', 'front_desk', 'doctor'] },
  { path: '/appointments/today', label: "Today's Schedule", roles: ['admin', 'front_desk', 'doctor'] },
  { path: '/appointments/book', label: 'Book Appointment', roles: ['admin', 'front_desk'] },
  { path: '/billing', label: 'Billing', roles: ['admin', 'front_desk'] },
  { path: '/pipeline', label: 'Pipeline', roles: ['admin'] },
  { path: '/assistant', label: 'AI Assistant', roles: ['admin', 'doctor'] },
];

export default function Navbar() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  const visibleLinks = NAV_LINKS.filter(link =>
    link.roles.includes(user?.role)
  );

  return (
    <nav style={styles.nav}>
      <div style={styles.brand} onClick={() => navigate('/')}>
        <span style={styles.brandName}>Redmond Polyclinic</span>
        <span style={styles.brandSub}>PMS</span>
      </div>

      <div style={styles.links}>
        {visibleLinks.map(link => (
          <button
            key={link.path}
            onClick={() => navigate(link.path)}
            style={{
              ...styles.link,
              ...(location.pathname.startsWith(link.path) ? styles.linkActive : {}),
            }}
          >
            {link.label}
          </button>
        ))}
      </div>

      <div style={styles.userSection}>
        <span style={styles.userName}>{user?.full_name}</span>
        <span style={styles.userRole}>{user?.role}</span>
        <button onClick={handleLogout} style={styles.logoutBtn}>
          Sign Out
        </button>
      </div>
    </nav>
  );
}

const styles = {
  nav: {
    backgroundColor: 'white',
    borderBottom: '1px solid #e2e8f0',
    padding: '0 2rem',
    height: '60px',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'space-between',
    position: 'sticky',
    top: 0,
    zIndex: 100,
    boxShadow: '0 1px 3px rgba(0,0,0,0.05)',
  },
  brand: {
    display: 'flex',
    alignItems: 'baseline',
    gap: '0.5rem',
    cursor: 'pointer',
  },
  brandName: {
    fontSize: '1rem',
    fontWeight: '700',
    color: '#1a202c',
  },
  brandSub: {
    fontSize: '0.75rem',
    color: '#718096',
    fontWeight: '600',
  },
  links: {
    display: 'flex',
    gap: '0.25rem',
  },
  link: {
    backgroundColor: 'transparent',
    border: 'none',
    padding: '0.5rem 1rem',
    borderRadius: '6px',
    cursor: 'pointer',
    fontSize: '0.9rem',
    color: '#4a5568',
    fontWeight: '500',
    fontFamily: 'system-ui, sans-serif',
  },
  linkActive: {
    backgroundColor: '#ebf8ff',
    color: '#2b6cb0',
    fontWeight: '600',
  },
  userSection: {
    display: 'flex',
    alignItems: 'center',
    gap: '0.75rem',
  },
  userName: {
    fontSize: '0.875rem',
    fontWeight: '600',
    color: '#2d3748',
  },
  userRole: {
    backgroundColor: '#ebf8ff',
    color: '#2b6cb0',
    padding: '0.2rem 0.6rem',
    borderRadius: '999px',
    fontSize: '0.7rem',
    fontWeight: '700',
    textTransform: 'uppercase',
  },
  logoutBtn: {
    backgroundColor: 'transparent',
    border: '1px solid #e2e8f0',
    color: '#718096',
    padding: '0.35rem 0.85rem',
    borderRadius: '6px',
    cursor: 'pointer',
    fontSize: '0.8rem',
    fontFamily: 'system-ui, sans-serif',
  },
};