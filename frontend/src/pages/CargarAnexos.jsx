import React, { useState, useEffect, useRef } from 'react';
import { radicadoService, anexoService } from '../services/api';
import { useLanguage } from '../contexts/LanguageContext';

export const CargarAnexos = () => {
  const { t } = useLanguage();
  const [radicados, setRadicados] = useState([]);
  const [selectedRadId, setSelectedRadId] = useState('');
  const [selectedFile, setSelectedFile] = useState(null);
  const [anexos, setAnexos] = useState([]);
  const [errorMessage, setErrorMessage] = useState('');
  const [successMessage, setSuccessMessage] = useState('');
  const [loading, setLoading] = useState(false);
  const fileInputRef = useRef(null);

  // Cargar radicados existentes para seleccionar a cuál adjuntar
  useEffect(() => {
    const fetchRadicados = async () => {
      try {
        const res = await radicadoService.listar();
        // Filtrar radicados finalizados - no se pueden adjuntar documentos a expedientes cerrados
        const radicadosValidos = res.data.filter(r => r.rad_estado !== 'FINALIZADO');
        setRadicados(radicadosValidos);
        if (radicadosValidos.length > 0) {
          setSelectedRadId(radicadosValidos[0].rad_id);
        }
      } catch (err) {
        console.error("Error al cargar radicados:", err);
      }
    };
    fetchRadicados();
  }, []);

  // Cargar lista de anexos al seleccionar un radicado
  useEffect(() => {
    if (selectedRadId) {
      cargarAnexos(selectedRadId);
    }
  }, [selectedRadId]);

  const cargarAnexos = async (radId) => {
    try {
      const res = await anexoService.listar(radId);
      setAnexos(res.data);
    } catch (err) {
      console.error("Error al cargar anexos:", err);
    }
  };

  const handleFileChange = (e) => {
    setErrorMessage('');
    setSuccessMessage('');
    const file = e.target.files[0];
    if (!file) {
      setSelectedFile(null);
      return;
    }

    // C.A.2 y C.A.3: Validación local estricta de formato .pdf y <= 15MB
    const isPdf = file.name.toLowerCase().endsWith('.pdf') || file.type === 'application/pdf';
    const isUnder15MB = file.size <= 15 * 1024 * 1024;

    if (!isPdf || !isUnder15MB) {
      // Bloquear la subida y mostrar alerta roja exacta
      setSelectedFile(null);
      if (fileInputRef.current) fileInputRef.current.value = '';
      setErrorMessage(t('anexos.errorFileFormat'));
      return;
    }

    setSelectedFile(file);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!selectedRadId) {
      setErrorMessage(t('anexos.selectFilingLabel'));
      return;
    }

    if (!selectedFile) {
      setErrorMessage(t('anexos.errorFileFormat'));
      return;
    }

    setErrorMessage('');
    setSuccessMessage('');
    setLoading(true);

    const formData = new FormData();
    formData.append('rad_id', selectedRadId);
    formData.append('file_adjunto', selectedFile);

    try {
      // C.A.4: Envío y almacenamiento
      const res = await anexoService.subir(formData);

      // C.A.5: Actualizar grid_anexos y mostrar mensaje exacto en verde
      setSuccessMessage(res.data.mensaje || t('anexos.successUploaded'));
      setAnexos(res.data.grid_anexos || []);
      setSelectedFile(null);
      if (fileInputRef.current) fileInputRef.current.value = '';
    } catch (err) {
      if (err.response && err.response.data && err.response.data.detail) {
        setErrorMessage(err.response.data.detail);
      } else {
        setErrorMessage(t('anexos.errorFileFormat'));
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div id="frm_cargar_anexos" className="card">
      <div className="card-header">
        <div>
          <h2 className="card-title">{t('anexos.title')}</h2>
          <p style={{ color: 'var(--text-muted)', fontSize: '0.875rem' }}>
            {t('anexos.module')}
          </p>
        </div>
      </div>

      {/* C.A.3: Alerta en rojo exacta */}
      {errorMessage && (
        <div className="alert alert-red">
          <span>{errorMessage}</span>
          <button onClick={() => setErrorMessage('')} style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'var(--color-red)' }}>✕</button>
        </div>
      )}

      {/* C.A.5: Mensaje en verde exacto */}
      {successMessage && (
        <div className="alert alert-green">
          <span>{successMessage}</span>
          <button onClick={() => setSuccessMessage('')} style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'var(--color-green)' }}>✕</button>
        </div>
      )}

      <form onSubmit={handleSubmit} style={{ marginBottom: '2rem' }}>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '1.5rem' }}>
          <div className="form-group">
            <label className="form-label" htmlFor="cmb_radicado_anexo">
              {t('anexos.selectFilingLabel')}
            </label>
            <select
              id="cmb_radicado_anexo"
              className="form-select"
              value={selectedRadId}
              onChange={(e) => setSelectedRadId(e.target.value)}
            >
              {radicados.map((rad) => (
                <option key={rad.rad_id} value={rad.rad_id}>
                  {rad.rad_codigo} — {rad.rad_asunto.substring(0, 40)} ({rad.rad_estado})
                </option>
              ))}
            </select>
          </div>

          <div className="form-group">
            <label className="form-label" htmlFor="file_adjunto">
              {t('anexos.fileInputLabel')}
            </label>
            <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
              <input
                id="file_adjunto"
                ref={fileInputRef}
                type="file"
                accept=".pdf"
                style={{ display: 'none' }}
                onChange={handleFileChange}
              />
              {/* C.A.1: btn_examinar */}
              <button
                id="btn_examinar"
                type="button"
                className="btn btn-secondary"
                onClick={() => fileInputRef.current && fileInputRef.current.click()}
              >
                📁 {t('anexos.browseBtn')}
              </button>
              <span style={{ fontSize: '0.85rem', color: '#475569', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                {selectedFile ? `${selectedFile.name} (${(selectedFile.size / 1024).toFixed(1)} KB)` : ''}
              </span>
            </div>
          </div>
        </div>

        <div style={{ marginTop: '1rem' }}>
          {/* C.A.4: btn_subir_archivo */}
          <button
            id="btn_subir_archivo"
            type="submit"
            className="btn btn-primary"
            disabled={loading || !selectedFile}
          >
            {loading ? t('anexos.uploading') : t('anexos.uploadBtn')}
          </button>
        </div>
      </form>

      {/* C.A.5: grid_anexos */}
      <div>
        <h3 style={{ fontSize: '1rem', fontWeight: 600, color: 'var(--primary)', marginBottom: '0.5rem' }}>
          {t('anexos.attachedFilesTitle')}
        </h3>
        <div className="table-container">
          <table id="grid_anexos" className="data-table">
            <thead>
              <tr>
                <th>ID</th>
                <th>{t('anexos.colFileName')}</th>
                <th>{t('anexos.colFileSize')}</th>
                <th>{t('anexos.colUploadDate')}</th>
                <th>{t('anexos.colDownload')}</th>
              </tr>
            </thead>
            <tbody>
              {anexos.length === 0 ? (
                <tr>
                  <td colSpan="5" style={{ textAlign: 'center', padding: '1.5rem', color: 'var(--text-muted)' }}>
                    {t('anexos.noAttachments')}
                  </td>
                </tr>
              ) : (
                anexos.map((anx) => (
                  <tr key={anx.anx_id}>
                    <td>{anx.anx_id}</td>
                    <td style={{ fontWeight: 600 }}>📄 {anx.anx_nombre_original}</td>
                    <td>{anx.anx_tamano_kb} KB</td>
                    <td>{new Date(anx.anx_fecha_carga).toLocaleString()}</td>
                    <td>
                      <a
                        href={anexoService.obtenerUrlArchivo(anx.anx_id)}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="btn btn-secondary"
                        style={{ padding: '0.35rem 0.75rem', fontSize: '0.8rem', display: 'inline-flex', alignItems: 'center', gap: '0.35rem', textDecoration: 'none' }}
                      >
                        📥 {t('anexos.downloadPdf') || 'Ver / Descargar PDF'}
                      </a>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
