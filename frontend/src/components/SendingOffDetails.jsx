import React from 'react';
import { sendingOffDetails } from '../utils/discipline.js';

export function SendingOffDetails({ card, events, language = 'en', onContinue }) {
  const es = language === 'es';
  const detail = sendingOffDetails(card, events, language);
  return (
    <section
      className="dashboard-card sending-off-details"
      aria-label={es ? 'Detalles de la expulsión' : 'Sending-off details'}
    >
      <span className="feature-pill">
        {es ? 'Tarjeta roja · incidente ficticio' : 'Red card · fictional incident'}
      </span>
      <h2>{detail.heading}</h2>
      <p>{detail.reason}</p>
      <p>{detail.consequence}</p>
      <details>
        <summary>{es ? 'Ver datos del incidente' : 'View event evidence'}</summary>
        <p>
          {card.team_name} ·{' '}
          {detail.post ? (es ? 'Después del pitido final' : 'After full time') : detail.clock}
        </p>
        <p>{es ? 'Fuente: datos sintéticos de demostración' : 'Source: synthetic demo feed'}</p>
        <code>{card.event_id}</code>
      </details>
      <button className="btn-primary" onClick={onContinue}>
        {detail.post
          ? es
            ? 'Volver al resumen final'
            : 'Back to match summary'
          : es
            ? 'Continuar partido'
            : 'Continue match'}
      </button>
    </section>
  );
}
