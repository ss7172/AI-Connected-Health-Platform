import { useState, useEffect } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { api } from '../../api/client';
import Navbar from '../common/Navbar';

export default function PatientForm() {
  const { id } = useParams(); // exists if editing
  const isEdit = Boolean(id);
  const navigate = useNavigate();

  const [form, setForm] = useState({
    first_name: '',
    last_name: '',
    date_of_birth: '',
    gender: '',
    phone: '',
    email: '',
    address: '',
    emergency_contact: '',
    blood_group: '',
  });

  const [phoneExists, setPhoneExists] = useState(false);
  const [phoneChecking, setPhoneChecking] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [fetchingPatient, setFetchingPatient] = useState(isEdit);

  // Load existing patient data if editing
  useEffect(() => {
    if (!isEdit) return;

    const fetchPatient = async () => {
      try {
        const data = await api.get(`/patients/${id}`);
        const p = data.patient;
        setForm({
          first_name: p.first_name,
          last_name: p.last_name,
          date_of_birth: p.date_of_birth,
          gender: p.gender,
          phone: p.phone,
          email: p.email || '',
          address: p.address || '',
          emergency_contact: p.emergency_contact || '',
          blood_group: p.blood_group || '',
        });
      } catch (err) {
        setError('Failed to load patient data');
      } finally {
        setFetchingPatient(false);
      }
    };

    fetchPatient();
  }, [id, isEdit]);

  const handleChange = (e) => {
    const { name, value } = e.target;
    setForm(prev => ({ ...prev, [name]: value }));

    // Reset phone check when phone changes
    if (name === 'phone') {
      setPhoneExists(false);
    }
  };

  // Phone dedup check on blur
  const handlePhoneBlur = async () => {
    if (!form.phone || form.phone.length < 10) return;
    if (isEdit) return; // Skip dedup check when editing

    setPhoneChecking(true);
    try {
      const data = await api.get(`/patients/check-phone/${form.phone}`);
      setPhoneExists(data.exists);
    } catch (err) {
      // Ignore check errors
    } finally {
      setPhoneChecking(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (phoneExists) return;

    setLoading(true);
    setError('');

    try {
      // Clean empty strings to null
      const payload = Object.fromEntries(
        Object.entries(form).map(([k, v]) => [k, v === '' ? null : v])
      );

      if (isEdit) {
        await api.put(`/patients/${id}`, payload);
      } else {
        await api.post('/patients', payload);
      }

      navigate('/patients');
    } catch (err) {
      setError(err.error || 'Failed to save patient');
    } finally {
      setLoading(false);
    }
  };

  if (fetchingPatient) {
    return (
      <div style={{ minHeight: '100vh', backgroundColor: '#f7fafc', fontFamily: 'system-ui, sans-serif' }}>
        <Navbar />
        <div style={{ padding: '2rem' }}>Loading patient...</div>
      </div>
    );
  }

  return (
    <div style={{ minHeight: '100vh', backgroundColor: '#f7fafc', fontFamily: 'system-ui, sans-serif' }}>
      <Navbar />
      <div style={{ padding: '2rem', maxWidth: '700px', margin: '0 auto' }}>

        {/* Header */}
        <div style={styles.pageHeader}>
          <div>
            <h1 style={styles.title}>
              {isEdit ? 'Edit Patient' : 'Register New Patient'}
            </h1>
            <p style={styles.subtitle}>
              {isEdit ? 'Update patient information' : 'Enter patient details to register'}
            </p>
          </div>
          <button
            onClick={() => navigate('/patients')}
            style={styles.backBtn}
          >
            ← Back
          </button>
        </div>

        {/* Form */}
        <div style={styles.formCard}>
          {error && <div style={styles.errorBanner}>{error}</div>}

          <form onSubmit={handleSubmit}>
            {/* Name Row */}
            <div style={styles.row}>
              <div style={styles.field}>
                <label style={styles.label}>First Name *</label>
                <input
                  name="first_name"
                  value={form.first_name}
                  onChange={handleChange}
                  required
                  style={styles.input}
                />
              </div>
              <div style={styles.field}>
                <label style={styles.label}>Last Name *</label>
                <input
                  name="last_name"
                  value={form.last_name}
                  onChange={handleChange}
                  required
                  style={styles.input}
                />
              </div>
            </div>

            {/* DOB + Gender */}
            <div style={styles.row}>
              <div style={styles.field}>
                <label style={styles.label}>Date of Birth *</label>
                <input
                  type="date"
                  name="date_of_birth"
                  value={form.date_of_birth}
                  onChange={handleChange}
                  required
                  style={styles.input}
                />
              </div>
              <div style={styles.field}>
                <label style={styles.label}>Gender *</label>
                <select
                  name="gender"
                  value={form.gender}
                  onChange={handleChange}
                  required
                  style={styles.input}
                >
                  <option value="">Select gender</option>
                  <option value="male">Male</option>
                  <option value="female">Female</option>
                  <option value="other">Other</option>
                </select>
              </div>
            </div>

            {/* Phone */}
            <div style={styles.field}>
              <label style={styles.label}>Phone * (primary ID)</label>
              <input
                name="phone"
                value={form.phone}
                onChange={handleChange}
                onBlur={handlePhoneBlur}
                required
                placeholder="10-digit mobile number"
                style={{
                  ...styles.input,
                  borderColor: phoneExists ? '#fc8181' : '#e2e8f0',
                }}
              />
              {phoneChecking && (
                <p style={styles.hint}>Checking...</p>
              )}
              {phoneExists && (
                <p style={styles.errorHint}>
                  ⚠️ This phone number is already registered
                </p>
              )}
            </div>

            {/* Email */}
            <div style={styles.field}>
              <label style={styles.label}>Email</label>
              <input
                type="email"
                name="email"
                value={form.email}
                onChange={handleChange}
                style={styles.input}
              />
            </div>

            {/* Blood Group */}
            <div style={styles.field}>
              <label style={styles.label}>Blood Group</label>
              <select
                name="blood_group"
                value={form.blood_group}
                onChange={handleChange}
                style={styles.input}
              >
                <option value="">Unknown</option>
                {['A+', 'A-', 'B+', 'B-', 'O+', 'O-', 'AB+', 'AB-'].map(bg => (
                  <option key={bg} value={bg}>{bg}</option>
                ))}
              </select>
            </div>

            {/* Address */}
            <div style={styles.field}>
              <label style={styles.label}>Address</label>
              <textarea
                name="address"
                value={form.address}
                onChange={handleChange}
                rows={3}
                style={{ ...styles.input, resize: 'vertical' }}
              />
            </div>

            {/* Emergency Contact */}
            <div style={styles.field}>
              <label style={styles.label}>Emergency Contact</label>
              <input
                name="emergency_contact"
                value={form.emergency_contact}
                onChange={handleChange}
                placeholder="Name and phone number"
                style={styles.input}
              />
            </div>

            {/* Submit */}
            <div style={styles.actions}>
              <button
                type="button"
                onClick={() => navigate('/patients')}
                style={styles.cancelBtn}
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={loading || phoneExists}
                style={{
                  ...styles.submitBtn,
                  opacity: loading || phoneExists ? 0.7 : 1,
                }}
              >
                {loading
                  ? 'Saving...'
                  : isEdit ? 'Update Patient' : 'Register Patient'
                }
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
}

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
  backBtn: {
    backgroundColor: 'white',
    border: '1px solid #e2e8f0',
    color: '#4a5568',
    padding: '0.5rem 1rem',
    borderRadius: '6px',
    cursor: 'pointer',
    fontSize: '0.875rem',
    fontFamily: 'system-ui, sans-serif',
  },
  formCard: {
    backgroundColor: 'white',
    borderRadius: '10px',
    padding: '2rem',
    boxShadow: '0 1px 3px rgba(0,0,0,0.06)',
  },
  errorBanner: {
    backgroundColor: '#fff5f5',
    border: '1px solid #fc8181',
    color: '#c53030',
    padding: '0.75rem 1rem',
    borderRadius: '6px',
    marginBottom: '1.5rem',
    fontSize: '0.875rem',
  },
  row: {
    display: 'grid',
    gridTemplateColumns: '1fr 1fr',
    gap: '1rem',
    marginBottom: '1rem',
  },
  field: {
    display: 'flex',
    flexDirection: 'column',
    gap: '0.4rem',
    marginBottom: '1rem',
  },
  label: {
    fontSize: '0.875rem',
    fontWeight: '600',
    color: '#4a5568',
  },
  input: {
    padding: '0.6rem 0.875rem',
    border: '1px solid #e2e8f0',
    borderRadius: '6px',
    fontSize: '0.9rem',
    outline: 'none',
    fontFamily: 'system-ui, sans-serif',
    width: '100%',
    boxSizing: 'border-box',
  },
  hint: {
    fontSize: '0.8rem',
    color: '#718096',
    margin: '0.25rem 0 0',
  },
  errorHint: {
    fontSize: '0.8rem',
    color: '#c53030',
    margin: '0.25rem 0 0',
  },
  actions: {
    display: 'flex',
    justifyContent: 'flex-end',
    gap: '1rem',
    marginTop: '1.5rem',
    paddingTop: '1.5rem',
    borderTop: '1px solid #e2e8f0',
  },
  cancelBtn: {
    backgroundColor: 'white',
    border: '1px solid #e2e8f0',
    color: '#4a5568',
    padding: '0.6rem 1.5rem',
    borderRadius: '6px',
    cursor: 'pointer',
    fontSize: '0.9rem',
    fontFamily: 'system-ui, sans-serif',
  },
  submitBtn: {
    backgroundColor: '#3182ce',
    color: 'white',
    border: 'none',
    padding: '0.6rem 1.5rem',
    borderRadius: '6px',
    cursor: 'pointer',
    fontSize: '0.9rem',
    fontWeight: '600',
    fontFamily: 'system-ui, sans-serif',
  },
};