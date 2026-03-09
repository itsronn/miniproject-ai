/**
 * Simple display box for a score label and value.
 */
export default function ScoreCard({ label, value }) {
  return (
    <div
      style={{
        border: '1px solid #e2e8f0',
        borderRadius: 10,
        padding: '0.75rem 1rem',
        marginBottom: '0.5rem',
        background: '#f8fafc',
      }}
    >
      <strong>{label}:</strong> {value != null ? value : '—'}
    </div>
  );
}
