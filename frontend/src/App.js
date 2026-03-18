import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './context/AuthContext';
import ProtectedRoute from './components/common/ProtectedRoute';
import LoginPage from './components/auth/LoginPage';
import Dashboard from './components/dashboard/Dashboard';
import PatientList from './components/patients/PatientList';
import PatientForm from './components/patients/PatientForm';

function RoleBasedRedirect() {
  const { user } = useAuth();
  if (!user) return <Navigate to="/login" replace />;
  if (user.role === 'admin') return <Navigate to="/dashboard" replace />;
  return <Navigate to="/appointments/today" replace />;
}

export default function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={<LoginPage />} />
          <Route
            path="/dashboard"
            element={
              <ProtectedRoute roles={['admin']}>
                <Dashboard />
              </ProtectedRoute>
            }
          />
          <Route
            path="/patients"
            element={
              <ProtectedRoute roles={['admin', 'front_desk', 'doctor']}>
                <PatientList />
              </ProtectedRoute>
            }
          />
          <Route
              path="/patients/new"
              element={
                <ProtectedRoute roles={['admin', 'front_desk']}>
                  <PatientForm />
                </ProtectedRoute>
            }
          />
          <Route
            path="/patients/:id/edit"
            element={
              <ProtectedRoute roles={['admin', 'front_desk']}>
                <PatientForm />
              </ProtectedRoute>
            }
          />
          <Route
            path="/appointments/today"
            element={
              <ProtectedRoute roles={['doctor', 'front_desk', 'admin']}>
                <div style={{ padding: '2rem' }}>
                  Today's Schedule — coming Day 5
                </div>
              </ProtectedRoute>
            }
          />
          <Route path="/" element={<RoleBasedRedirect />} />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  );
}