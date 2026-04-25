import { useLanguage } from '../context/LanguageContext';
import './Fields.css';

const FIELDS = [
  { id: 'B12', name: 'Field B12',     crop: 'Soybean',  status: 'Healthy',       area: '4.2 ha', moisture: 42, score: 94, color: '#1b5e20' },
  { id: 'A14', name: 'Zone A-14',     crop: 'Wheat',    status: 'Harvest-Ready', area: '6.1 ha', moisture: 35, score: 88, color: '#2e7d32' },
  { id: 'C07', name: 'Sector C-07',   crop: 'Cotton',   status: 'Monitoring',    area: '3.8 ha', moisture: 55, score: 72, color: '#558b2f' },
  { id: 'D02', name: 'Block D-02',    crop: 'Maize',    status: 'Healthy',       area: '5.5 ha', moisture: 48, score: 91, color: '#1b5e20' },
];

const STATUS_BADGE = {
  'Healthy':       'badge badge-success',
  'Harvest-Ready': 'badge',
  'Monitoring':    'badge badge-pending',
};

export default function Fields() {
  const { t } = useLanguage();
  return (
    <div className="fields animate-fade-up">
      <div className="fields__header">
        <div>
          <h1 className="text-h2" style={{ color: 'var(--color-primary-dark)' }}>{t('nav.fields')}</h1>
          <p className="text-body-md" style={{ color: 'var(--color-secondary)' }}>Manage and monitor all your field zones</p>
        </div>
        <button id="add-field-btn" className="btn btn-primary">
          <span className="material-symbols-outlined icon icon-sm">add</span>
          Add Field
        </button>
      </div>

      <div className="fields__grid">
        {FIELDS.map(f => (
          <div key={f.id} className="field-card" id={`field-${f.id}`}>
            <div className="field-card__top" style={{ background: `linear-gradient(135deg, ${f.color}, #004d40)` }}>
              <span className="material-symbols-outlined icon-fill" style={{ fontSize: 40, color: 'rgba(255,255,255,0.2)', position: 'absolute', right: 16, top: 16 }}>potted_plant</span>
              <div className="field-card__badge-wrap">
                <span className={STATUS_BADGE[f.status] || 'badge'} style={f.status === 'Harvest-Ready' ? { background: '#fff3e0', color: '#e65100' } : {}}>
                  {f.status}
                </span>
              </div>
              <div>
                <h3 className="text-h3" style={{ color: 'white' }}>{f.name}</h3>
                <p style={{ color: 'rgba(255,255,255,0.7)', fontWeight: 600, fontSize: 14 }}>{f.crop} • {f.area}</p>
              </div>
            </div>
            <div className="field-card__body">
              <div className="field-metric">
                <span className="text-label-caps" style={{ color: 'var(--color-secondary)' }}>Moisture</span>
                <div className="progress-bar" style={{ marginTop: 4 }}>
                  <div className="progress-fill" style={{ width: `${f.moisture}%` }} />
                </div>
                <span style={{ fontSize: 13, fontWeight: 700, color: 'var(--color-primary)' }}>{f.moisture}%</span>
              </div>
              <div className="field-metric">
                <span className="text-label-caps" style={{ color: 'var(--color-secondary)' }}>AI Fit Score</span>
                <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                  <div className="progress-bar" style={{ marginTop: 4, flex: 1 }}>
                    <div className="progress-fill" style={{ width: `${f.score}%` }} />
                  </div>
                  <span style={{ fontSize: 13, fontWeight: 700, color: 'var(--color-primary)' }}>{f.score}%</span>
                </div>
              </div>
              <div className="field-card__actions">
                <button className="btn btn-secondary" style={{ flex: 1, padding: '10px 0' }}>
                  <span className="material-symbols-outlined icon icon-sm">analytics</span>
                  Analyze
                </button>
                <button className="btn btn-ghost" style={{ padding: '10px 16px' }}>
                  <span className="material-symbols-outlined icon icon-sm">more_horiz</span>
                </button>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
