import { useState, useEffect } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { api } from '../../api/client';
import Navbar from '../common/Navbar';

export default function BookAppointment() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const prefilledPatientId = searchParams.get('patient_id');

  // Form state
  const [form, setForm] = useState({
    patient_id: prefilledPatientId || '',
    doctor_id: '',
    department_id: '',
    appointment_date: '',
    appointment_time: '',
    notes: '',
  });

  // Data for dropdowns
  const [departments, setDepartments] = useState([]);
  const [doctors, setDoctors] = useState([]);
  const [availableSlots, setAvailableSlots] = useState([]);
  const [patientSearch, setPatientSearch] = useState('');
  const [patientResults, setPatientResults] = useState([]);
  const [selectedPatient, setSelectedPatient] = useState(null);

  // UI state
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [searchingPatient, setSearchingPatient] = useState(false);
  const [loadingSlots, setLoadingSlots] = useState(false);

  // Load departments on mount
  useEffect(() => {
    const fetchDepartments = async () => {
      try {
        const data = await api.get('/departments');
        setDepartments(data.departments);
      } catch (err) {
        setError('Failed to load departments');
      }
    };
    fetchDepartments();
  }, []);

  // Load prefilled patient if patient_id in URL
  useEffect(() => {
    if (!prefilledPatientId) return;
    const fetchPatient = async () => {
      try {
        const data = await api.get(`/patients/${prefilledPatientId}`);
        setSelectedPatient(data.patient);
      } catch (err) {}
    };
    fetchPatient();
  }, [prefilledPatientId]);

  // Load doctors when department changes
  useEffect(() => {
    if (!form.department_id) {
      setDoctors([]);
      return;
    }
    const fetchDoctors = async () => {
      try {
        const data = await api.get(`/doctors?department_id=${form.department_id}`);
        setDoctors(data.doctors);
        setForm(prev => ({ ...prev, doctor_id: '' }));
      } catch (err) {}
    };
    fetchDoctors();
  }, [form.department_id]);

  // Load available slots when doctor + date selected
  useEffect(() => {
    if (!form.doctor_id || !form.appointment_date) {
      setAvailableSlots([]);
      return;
    }
    const fetchSlots = async () => {
      setLoadingSlots(true);
      try {
        const data = await api.get(
          `/doctors/${form.doctor_id}/available-slots?date=${form.appointment_date}`
        );
        setAvailableSlots(data.available_slots);
        setForm(prev => ({ ...prev, appointment_time: '' }));
      } catch (err) {
        setAvailableSlots([]);
      } finally {
        setLoadingSlots(false);
      }
    };
    fetchSlots();
  }, [form.doctor_id, form.appointment_date]);

  // Patient search
  const handlePatientSearch = async (e) => {
    const value = e.target.value;
    setPatientSearch(value);
    setSelectedPatient(null);
    setForm(prev => ({ ...prev, patient_id: '' }));

    if (value.length < 3) {
      setPatientResults([]);
      return;
    }

    setSearchingPatient(true);
    try {
      const data = await api.get(`/patients?search=${value}&per_page=5`);
      setPatientResults(data.items);
    } catch (err) {
      setPatientResults([]);
    } finally {
      setSearchingPatient(false);
    }
  };

  const selectPatient = (patient) => {
    setSelectedPatient(patient);
    setForm(prev => ({ ...prev, patient_id: patient.id }));
    setPatientSearch('');
    setPatientResults([]);
  };

  const handleChange = (e) => {
    const { name, value } = e.target;
    setForm(prev => ({ ...prev, [name]: value }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      await api.post('/appointments', {
        ...form,
        patient_id: parseInt(form.patient_id),
        doctor_id: parseInt(form.doctor_id),
        department_id: parseInt(form.department_id),
      });
      navigate('/appointments/today');
    } catch (err) {
      setError(err.error || 'Failed to book appointment');
    } finally {
      setLoading(false);
    }
  };

  // Min date is today
  const today = new Date().toISOString().split('T')[0];

  return (
    <div style={{ minHeight: '100vh', backgroundColor: '#f7fafc', fontFamily: 'system-ui, sans-serif' }}>
      <Navbar />
      <div style={{ padding: '2rem', maxWidth: '700px', margin: '0 auto' }}>

        {/* Header */}
        <div style={styles.pageHeader}>
          <div>
            <h1 style={styles.title}>Book Appointment</h1>
            <p style={styles.subtitle}>Schedule a new patient appointment</p>
          </div>
          <button onClick={() => navigate('/appointments/today')} style={styles.backBtn}>
            ← Back
          </button>
        </div>

        <div style={styles.formCard}>
          {error && <div style={styles.errorBanner}>{error}</div>}

          <form onSubmit={handleSubmit}>

            {/* Patient Selection */}
            <div style={styles.section}>
              <h3 style={styles.sectionTitle}>Patient</h3>

              {selectedPatient ? (
                <div style={styles.selectedPatient}>
                  <div>
                    <div style={styles.selectedName}>{selectedPatient.full_name}</div>
                    <div style={styles.selectedDetail}>
                      {selectedPatient.phone} · Age {selectedPatient.age} · {selectedPatient.gender}
                    </div>
                  </div>
                  {!prefilledPatientId && (
                    <button
                      type="button"
                      onClick={() => {
                        setSelectedPatient(null);
                        setForm(prev => ({ ...prev, patient_id: '' }));
                      }}
                      style={styles.changeBtn}
                    >
                      Change
                    </button>
                  )}
                </div>
              ) : (
                <div style={{ position: 'relative' }}>
                  <input
                    type="text"
                    placeholder="Search patient by name or phone..."
                    value={patientSearch}
                    onChange={handlePatientSearch}
                    style={styles.input}
                  />
                  {searchingPatient && (
                    <p style={styles.hint}>Searching...</p>
                  )}
                  {patientResults.length > 0 && (
                    <div style={styles.dropdown}>
                      {patientResults.map(patient => (
                        <div
                          key={patient.id}
                          style={styles.dropdownItem}
                          onClick={() => selectPatient(patient)}
                        >
                          <div style={styles.dropdownName}>{patient.full_name}</div>
                          <div style={styles.dropdownDetail}>
                            {patient.phone} · Age {patient.age}
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              )}
            </div>

            {/* Department */}
            <div style={styles.section}>
              <h3 style={styles.sectionTitle}>Department & Doctor</h3>
              <div style={styles.row}>
                <div style={styles.field}>
                  <label style={styles.label}>Department *</label>
                  <select
                    name="department_id"
                    value={form.department_id}
                    onChange={handleChange}
                    required
                    style={styles.input}
                  >
                    <option value="">Select department</option>
                    {departments.map(dept => (
                      <option key={dept.id} value={dept.id}>
                        {dept.name} — ₹{dept.consultation_fee}
                      </option>
                    ))}
                  </select>
                </div>
                <div style={styles.field}>
                  <label style={styles.label}>Doctor *</label>
                  <select
                    name="doctor_id"
                    value={form.doctor_id}
                    onChange={handleChange}
                    required
                    disabled={!form.department_id}
                    style={{
                      ...styles.input,
                      opacity: !form.department_id ? 0.5 : 1,
                    }}
                  >
                    <option value="">Select doctor</option>
                    {doctors.map(doctor => (
                      <option key={doctor.id} value={doctor.id}>
                        {doctor.full_name}
                      </option>
                    ))}
                  </select>
                </div>
              </div>
            </div>

            {/* Date & Time */}
            <div style={styles.section}>
              <h3 style={styles.sectionTitle}>Date & Time</h3>
              <div style={styles.row}>
                <div style={styles.field}>
                  <label style={styles.label}>Date *</label>
                  <input
                    type="date"
                    name="appointment_date"
                    value={form.appointment_date}
                    onChange={handleChange}
                    min={today}
                    required
                    style={styles.input}
                  />
                </div>
                <div style={styles.field}>
                  <label style={styles.label}>Time *</label>
                  {loadingSlots ? (
                    <p style={styles.hint}>Loading available slots...</p>
                  ) : availableSlots.length > 0 ? (
                    <select
                      name="appointment_time"
                      value={form.appointment_time}
                      onChange={handleChange}
                      required
                      style={styles.input}
                    >
                      <option value="">Select time slot</option>
                      {availableSlots.map(slot => (
                        <option key={slot} value={slot}>{slot}</option>
                      ))}
                    </select>
                  ) : form.doctor_id && form.appointment_date ? (
                    <p style={styles.errorHint}>No slots available for this date</p>
                  ) : (
                    <p style={styles.hint}>Select doctor and date first</p>
                  )}
                </div>
              </div>
            </div>

            {/* Notes */}
            <div style={styles.field}>
              <label style={styles.label}>Notes</label>
              <textarea
                name="notes"
                value={form.notes}
                onChange={handleChange}
                rows={3}
                placeholder="Optional notes about the appointment"
                style={{ ...styles.input, resize: 'vertical' }}
              />
            </div>

            {/* Submit */}
            <div style={styles.actions}>
              <button
                type="button"
                onClick={() => navigate('/appointments/today')}
                style={styles.cancelBtn}
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={loading || !form.patient_id}
                style={{
                  ...styles.submitBtn,
                  opacity: loading || !form.patient_id ? 0.7 : 1,
                }}
              >
                {loading ? 'Booking...' : 'Book Appointment'}
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
  section: {
    marginBottom: '1.5rem',
    paddingBottom: '1.5rem',
    borderBottom: '1px solid #f0f4f8',
  },
  sectionTitle: {
    fontSize: '0.875rem',
    fontWeight: '700',
    color: '#4a5568',
    textTransform: 'uppercase',
    letterSpacing: '0.05em',
    margin: '0 0 1rem',
  },
  row: {
    display: 'grid',
    gridTemplateColumns: '1fr 1fr',
    gap: '1rem',
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
  selectedPatient: {
    backgroundColor: '#f0fff4',
    border: '1px solid #9ae6b4',
    borderRadius: '8px',
    padding: '1rem',
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  selectedName: {
    fontWeight: '700',
    color: '#276749',
    fontSize: '1rem',
  },
  selectedDetail: {
    fontSize: '0.85rem',
    color: '#48bb78',
    marginTop: '0.2rem',
  },
  changeBtn: {
    backgroundColor: 'white',
    border: '1px solid #9ae6b4',
    color: '#276749',
    padding: '0.3rem 0.75rem',
    borderRadius: '4px',
    cursor: 'pointer',
    fontSize: '0.8rem',
    fontFamily: 'system-ui, sans-serif',
  },
  dropdown: {
    position: 'absolute',
    top: '100%',
    left: 0,
    right: 0,
    backgroundColor: 'white',
    border: '1px solid #e2e8f0',
    borderRadius: '6px',
    boxShadow: '0 4px 12px rgba(0,0,0,0.1)',
    zIndex: 10,
    maxHeight: '200px',
    overflowY: 'auto',
  },
  dropdownItem: {
    padding: '0.75rem 1rem',
    cursor: 'pointer',
    borderBottom: '1px solid #f0f4f8',
  },
  dropdownName: {
    fontWeight: '600',
    color: '#2d3748',
    fontSize: '0.9rem',
  },
  dropdownDetail: {
    fontSize: '0.8rem',
    color: '#718096',
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