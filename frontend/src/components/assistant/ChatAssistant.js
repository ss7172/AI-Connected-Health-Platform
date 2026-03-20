// frontend/src/components/assistant/ChatAssistant.js
import { useState, useRef, useEffect } from 'react';
import { api } from '../../api/client';
import Navbar from '../common/Navbar';

const SAMPLE_QUERIES = [
  'What medications is Ramesh Nayak on?',
  'Which patients have stable angina?',
  'Show me patients with hypertension',
  'What is Priya Sahoo\'s diagnosis history?',
];

export default function ChatAssistant() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const bottomRef = useRef(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const sendQuery = async (query) => {
    if (!query.trim() || loading) return;

    const userMessage = { role: 'user', content: query };
    setMessages(prev => [...prev, userMessage]);
    setInput('');
    setLoading(true);
    setError('');

    try {
      const data = await api.post('/assistant/query', { query });
      const assistantMessage = {
        role: 'assistant',
        content: data.answer,
        sources: data.sources,
        chunks_retrieved: data.chunks_retrieved,
        model: data.model,
      };
      setMessages(prev => [...prev, assistantMessage]);
    } catch (err) {
      setError(err.error || 'Failed to get response. Please try again.');
      // Remove the user message on error
      setMessages(prev => prev.slice(0, -1));
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    sendQuery(input);
  };

  const isEmpty = messages.length === 0;

  return (
    <div style={{ minHeight: '100vh', backgroundColor: '#f7fafc', fontFamily: 'system-ui, sans-serif', display: 'flex', flexDirection: 'column' }}>
      <Navbar />

      <div style={{ flex: 1, display: 'flex', flexDirection: 'column', maxWidth: '860px', width: '100%', margin: '0 auto', padding: '1.5rem', boxSizing: 'border-box' }}>

        {/* Header */}
        <div style={{ marginBottom: '1.5rem' }}>
          <h1 style={{ fontSize: '1.5rem', fontWeight: '700', color: '#1a202c', margin: '0 0 0.25rem' }}>
            Clinical AI Assistant
          </h1>
          <p style={{ color: '#718096', fontSize: '0.875rem', margin: 0 }}>
            Ask questions about patient records in natural language
          </p>
        </div>

        {/* Chat area */}
        <div style={{ flex: 1, display: 'flex', flexDirection: 'column' }}>

          {/* Empty state — sample queries */}
          {isEmpty && (
            <div style={{ flex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', gap: '1.5rem', padding: '2rem 0' }}>
              <div style={{ textAlign: 'center' }}>
                <div style={{ fontSize: '2.5rem', marginBottom: '0.75rem' }}>🏥</div>
                <p style={{ color: '#4a5568', fontWeight: '600', margin: '0 0 0.25rem' }}>Ask about your patients</p>
                <p style={{ color: '#a0aec0', fontSize: '0.875rem', margin: 0 }}>Queries are answered from real clinical records</p>
              </div>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.75rem', justifyContent: 'center', maxWidth: '600px' }}>
                {SAMPLE_QUERIES.map(q => (
                  <button
                    key={q}
                    onClick={() => sendQuery(q)}
                    style={{
                      backgroundColor: 'white',
                      border: '1px solid #e2e8f0',
                      borderRadius: '999px',
                      padding: '0.5rem 1rem',
                      fontSize: '0.8rem',
                      color: '#4a5568',
                      cursor: 'pointer',
                      fontFamily: 'system-ui, sans-serif',
                      transition: 'border-color 0.15s',
                    }}
                  >
                    {q}
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* Messages */}
          {!isEmpty && (
            <div style={{ flex: 1, overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: '1.25rem', marginBottom: '1rem' }}>
              {messages.map((msg, idx) => (
                <div key={idx}>
                  {msg.role === 'user' ? (
                    <div style={{ display: 'flex', justifyContent: 'flex-end' }}>
                      <div style={{
                        backgroundColor: '#3182ce',
                        color: 'white',
                        borderRadius: '18px 18px 4px 18px',
                        padding: '0.75rem 1.1rem',
                        maxWidth: '70%',
                        fontSize: '0.9rem',
                        lineHeight: '1.5',
                      }}>
                        {msg.content}
                      </div>
                    </div>
                  ) : (
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
                      {/* Answer bubble */}
                      <div style={{
                        backgroundColor: 'white',
                        border: '1px solid #e2e8f0',
                        borderRadius: '4px 18px 18px 18px',
                        padding: '1rem 1.1rem',
                        maxWidth: '85%',
                        fontSize: '0.9rem',
                        lineHeight: '1.6',
                        color: '#2d3748',
                        boxShadow: '0 1px 3px rgba(0,0,0,0.04)',
                        whiteSpace: 'pre-wrap',
                      }}>
                        {msg.content}
                      </div>

                      {/* Source cards */}
                      {msg.sources && msg.sources.length > 0 && (
                        <div style={{ maxWidth: '85%' }}>
                          <p style={{ fontSize: '0.7rem', color: '#a0aec0', fontWeight: '700', textTransform: 'uppercase', letterSpacing: '0.05em', margin: '0 0 0.4rem 0.25rem' }}>
                            Sources · {msg.chunks_retrieved} records retrieved · {msg.model}
                          </p>
                          <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.4rem' }}>
                            {msg.sources.map((s, i) => (
                              <div key={i} style={{
                                backgroundColor: '#ebf8ff',
                                border: '1px solid #bee3f8',
                                borderRadius: '6px',
                                padding: '0.3rem 0.6rem',
                                fontSize: '0.75rem',
                                color: '#2b6cb0',
                              }}>
                                <span style={{ fontWeight: '700' }}>{s.patient_name}</span>
                                <span style={{ color: '#63b3ed' }}> #{s.patient_id}</span>
                                {s.department && <span style={{ color: '#90cdf4' }}> · {s.department}</span>}
                              </div>
                            ))}
                          </div>
                        </div>
                      )}
                    </div>
                  )}
                </div>
              ))}

              {/* Loading indicator */}
              {loading && (
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                  <div style={{
                    backgroundColor: 'white',
                    border: '1px solid #e2e8f0',
                    borderRadius: '4px 18px 18px 18px',
                    padding: '0.75rem 1.1rem',
                    fontSize: '0.875rem',
                    color: '#a0aec0',
                  }}>
                    Searching patient records...
                  </div>
                </div>
              )}

              <div ref={bottomRef} />
            </div>
          )}

          {/* Error */}
          {error && (
            <div style={{
              backgroundColor: '#fff5f5',
              border: '1px solid #fc8181',
              color: '#c53030',
              padding: '0.75rem 1rem',
              borderRadius: '8px',
              fontSize: '0.875rem',
              marginBottom: '1rem',
            }}>
              {error}
            </div>
          )}

          {/* Input */}
          <form onSubmit={handleSubmit} style={{ display: 'flex', gap: '0.75rem', alignItems: 'flex-end' }}>
            <input
              type="text"
              value={input}
              onChange={e => setInput(e.target.value)}
              placeholder="Ask about patients, diagnoses, medications..."
              disabled={loading}
              style={{
                flex: 1,
                padding: '0.75rem 1rem',
                border: '1px solid #e2e8f0',
                borderRadius: '10px',
                fontSize: '0.9rem',
                outline: 'none',
                fontFamily: 'system-ui, sans-serif',
                backgroundColor: loading ? '#f7fafc' : 'white',
              }}
            />
            <button
              type="submit"
              disabled={loading || !input.trim()}
              style={{
                backgroundColor: loading || !input.trim() ? '#a0aec0' : '#3182ce',
                color: 'white',
                border: 'none',
                borderRadius: '10px',
                padding: '0.75rem 1.25rem',
                fontSize: '0.9rem',
                fontWeight: '600',
                cursor: loading || !input.trim() ? 'not-allowed' : 'pointer',
                fontFamily: 'system-ui, sans-serif',
                whiteSpace: 'nowrap',
              }}
            >
              {loading ? '...' : 'Ask'}
            </button>
          </form>
        </div>
      </div>
    </div>
  );
}