import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './context/AuthContext';
import ProtectedRoute from './components/common/ProtectedRoute';
import LoginPage from './components/auth/LoginPage';
import Dashboard from './components/dashboard/Dashboard';
import PatientList from './components/patients/PatientList';
import PatientForm from './components/patients/PatientForm';
import PatientProfile from './components/patients/PatientProfile';
import TodaySchedule from './components/appointments/TodaySchedule';
import BookAppointment from './components/appointments/BookAppointment';
import VisitForm from './components/visits/VisitForm';
import BillingList from './components/billing/BillingList';
import InvoiceDetail from './components/billing/InvoiceDetail';
import PipelineStatus from './components/pipeline/PipelineStatus';
import ChatAssistant from './components/assistant/ChatAssistant';

  

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

          {/* PATIENTS — static routes before dynamic */}
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
            path="/patients/:id"
            element={
              <ProtectedRoute roles={['admin', 'front_desk', 'doctor']}>
                <PatientProfile />
              </ProtectedRoute>
            }
          />

          {/* APPOINTMENTS — static routes before dynamic */}
          <Route
            path="/appointments/today"
            element={
              <ProtectedRoute roles={['doctor', 'front_desk', 'admin']}>
                <TodaySchedule />
              </ProtectedRoute>
            }
          />
          <Route
            path="/appointments/book"
            element={
              <ProtectedRoute roles={['admin', 'front_desk']}>
                <BookAppointment />
              </ProtectedRoute>
            }
          />
          <Route
            path="/visits/new"
            element={
              <ProtectedRoute roles={['doctor']}>
                <VisitForm />
              </ProtectedRoute>
            }
          />
          <Route
            path="/billing"
            element={
              <ProtectedRoute roles={['admin', 'front_desk']}>
                <BillingList />
              </ProtectedRoute>
            }
          />
          <Route
            path="/billing/:id"
            element={
              <ProtectedRoute roles={['admin', 'front_desk']}>
                <InvoiceDetail />
              </ProtectedRoute>
            }
            />
          <Route
            path="/pipeline"
            element={
              <ProtectedRoute roles={['admin']}>
                <PipelineStatus />
              </ProtectedRoute>
            }
          />
            <Route
            path="/assistant"
            element={
              <ProtectedRoute roles={['admin','doctor']}>
                <ChatAssistant />
              </ProtectedRoute>
            }
          />
          <Route path="/" element={<RoleBasedRedirect />} />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  );
}