import React, { useState } from 'react';

export function EvidenceGraph({ graph, stories = [] }) {
  const [activeTab, setActiveTab] = useState('pipeline'); // 'pipeline' | 'graph-nodes'

  const nodes = graph?.nodes || [];
  const edges = graph?.edges || [];

  const eventNodes = nodes.filter((n) => n.type === 'event');
  const metricNodes = nodes.filter((n) => n.type === 'metric_window');
  const storyNodes = nodes.filter((n) => n.type === 'story');

  return (
    <section
      className="dashboard-card graph-card"
      aria-label="Match Story Graph and Evidence Architecture"
    >
      <div className="card-header">
        <div className="header-text-group">
          <div className="title-with-pill">
            <h2 className="card-title">Match Story Graph & AI Grounding</h2>
            <span className="feature-pill">Rule: graph-v1</span>
          </div>
          <p className="card-subtitle">
            How MatchOS turns raw events into deterministic graph nodes and verified Azure AI
            briefings.
          </p>
        </div>

        <div className="tab-pills" role="tablist">
          <button
            type="button"
            role="tab"
            aria-selected={activeTab === 'pipeline'}
            className={`tab-btn ${activeTab === 'pipeline' ? 'active' : ''}`}
            onClick={() => setActiveTab('pipeline')}
          >
            Grounding Pipeline
          </button>
          <button
            type="button"
            role="tab"
            aria-selected={activeTab === 'graph-nodes'}
            className={`tab-btn ${activeTab === 'graph-nodes' ? 'active' : ''}`}
            onClick={() => setActiveTab('graph-nodes')}
          >
            Graph Nodes ({nodes.length})
          </button>
        </div>
      </div>

      {activeTab === 'pipeline' ? (
        <div className="pipeline-flow-container">
          <div className="pipeline-step">
            <div className="step-number">1</div>
            <div className="step-content">
              <h4>Synthetic Ingestion</h4>
              <p>
                Replay highlights validated against schema 1.1 for strict sequence ordering and
                match clock consistency.
              </p>
              <span className="step-tag">FastAPI · Pydantic</span>
            </div>
          </div>

          <div className="pipeline-connector">
            <span className="connector-arrow">→</span>
            <span className="connector-label">validates</span>
          </div>

          <div className="pipeline-step">
            <div className="step-number">2</div>
            <div className="step-content">
              <h4>Deterministic Graph</h4>
              <p>
                Rules aggregate 5-min shot windows and goals. Connects nodes via explicit{' '}
                <code>supports</code> edges.
              </p>
              <span className="step-tag">
                {metricNodes.length} windows · {edges.length} edges
              </span>
            </div>
          </div>

          <div className="pipeline-connector">
            <span className="connector-arrow">→</span>
            <span className="connector-label">supports</span>
          </div>

          <div className="pipeline-step">
            <div className="step-number">3</div>
            <div className="step-content">
              <h4>Azure AI Selection</h4>
              <p>
                Azure <code>gpt-4.1-mini</code> calls <code>get_match_evidence</code> and selects
                candidate story IDs.
              </p>
              <span className="step-tag">Tool calls · Bound candidates</span>
            </div>
          </div>

          <div className="pipeline-connector">
            <span className="connector-arrow">→</span>
            <span className="connector-label">verifies</span>
          </div>

          <div className="pipeline-step highlight-step">
            <div className="step-number">4</div>
            <div className="step-content">
              <h4>Grounded Fan Catch-Up</h4>
              <p>
                Backend verifies AI selection against deterministic evidence and renders trusted
                audience wording.
              </p>
              <span className="step-tag">Casual & Advanced</span>
            </div>
          </div>
        </div>
      ) : (
        <div className="graph-nodes-overview">
          <div className="graph-metrics-bar">
            <div className="graph-metric">
              <span className="num">{eventNodes.length}</span>
              <span className="label">Event Nodes</span>
            </div>
            <div className="graph-metric">
              <span className="num">{metricNodes.length}</span>
              <span className="label">Metric Windows</span>
            </div>
            <div className="graph-metric">
              <span className="num">{storyNodes.length}</span>
              <span className="label">Story Nodes</span>
            </div>
            <div className="graph-metric">
              <span className="num">{edges.length}</span>
              <span className="label">Support Edges</span>
            </div>
          </div>

          <div className="graph-stories-inspection">
            {stories.map((story) => {
              const incomingEdges = edges.filter((e) => e.target === story.story_id);
              return (
                <div key={story.story_id} className="graph-story-chain">
                  <div className="chain-header">
                    <strong>Story: {story.text}</strong>
                    <code>{story.story_id}</code>
                  </div>
                  <div className="chain-links">
                    <span className="chain-incoming-label">Supported by:</span>
                    <div className="chain-nodes">
                      {incomingEdges.map((edge, idx) => (
                        <span key={idx} className="chain-node-pill">
                          <code>{edge.source}</code>
                          <span className="edge-type">--({edge.type})--&gt;</span>
                        </span>
                      ))}
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      <div className="disclaimer-footnote">
        <span className="disclaimer-icon">ℹ</span>
        <span>
          Graph edges use <code>type: "supports"</code> to link evidence. They denote mathematical
          support, not tactical causation.
        </span>
      </div>
    </section>
  );
}
