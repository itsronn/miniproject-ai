/**
 * Basic file input wrapper. Accepts only images. Optional preview.
 */
export default function FileUpload({ accept = 'image/*', onFileSelect, previewUrl }) {
  const handleChange = (e) => {
    const file = e.target.files?.[0];
    if (file) onFileSelect(file);
  };

  return (
    <div className="file-upload">
      <input type="file" accept={accept} onChange={handleChange} />
      {previewUrl && (
        <div style={{ marginTop: '1rem' }}>
          <img src={previewUrl} alt="Preview" style={{ maxWidth: '100%', maxHeight: 200, borderRadius: 8 }} />
        </div>
      )}
    </div>
  );
}
