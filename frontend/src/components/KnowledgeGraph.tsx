import React, { useEffect, useState, useRef } from 'react';
import ForceGraph2D from 'react-force-graph-2d';
import { getKnowledgeGraph } from '../services/api';

interface GraphNode {
  id: string;
  name: string;
  type: string;
  [key: string]: any;
}

interface GraphLink {
  source: string;
  target: string;
  type: string;
  label?: string;
}

interface GraphData {
  nodes: GraphNode[];
  links: GraphLink[];
  stats: {
    total_nodes: number;
    total_links: number;
    parties: number;
    documents: number;
    transactions: number;
    emails: number;
  };
}

const KnowledgeGraph: React.FC = () => {
  const [graphData, setGraphData] = useState<GraphData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const graphRef = useRef<any>();

  useEffect(() => {
    loadGraph();
  }, []);

  const loadGraph = async () => {
    setLoading(true);
    setError('');
    try {
      const data = await getKnowledgeGraph();
      setGraphData(data);
    } catch (err: any) {
      console.error('Failed to load knowledge graph:', err);
      setError('Failed to load knowledge graph. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const getNodeColor = (node: GraphNode) => {
    switch (node.type) {
      case 'party':
        return '#4f46e5'; // Primary color for parties/vendors
      case 'document':
        return '#10b981'; // Success color for documents
      case 'transaction':
        return '#f59e0b'; // Warning color for transactions
      case 'email':
        return '#06b6d4'; // Secondary color for emails
      default:
        return '#6b7280'; // Gray for unknown
    }
  };

  const getNodeSize = (node: GraphNode) => {
    switch (node.type) {
      case 'party':
        return 8;
      case 'transaction':
        return 6;
      case 'document':
        return 7;
      case 'email':
        return 5;
      default:
        return 5;
    }
  };

  const getLinkColor = (link: GraphLink) => {
    switch (link.type) {
      case 'has_transaction':
        return '#f59e0b';
      case 'involves_party':
        return '#4f46e5';
      case 'has_attachment':
        return '#06b6d4';
      default:
        return '#e5e7eb';
    }
  };

  if (loading) {
    return (
      <div className="loading">
        <div className="spinner"></div>
        Loading Knowledge Graph...
      </div>
    );
  }

  if (error) {
    return <div className="error">{error}</div>;
  }

  if (!graphData || graphData.nodes.length === 0) {
    return (
      <div className="no-data">
        <h1>Knowledge Graph</h1>
        <p>No data available yet. Upload documents or sync emails to build your knowledge graph.</p>
      </div>
    );
  }

  return (
    <div className="knowledge-graph">
      <h1>Knowledge Graph</h1>

      {/* Statistics */}
      <div className="graph-stats">
        <div className="graph-stat-item">
          <strong>{graphData.stats.total_nodes}</strong>
          <span>Total Nodes</span>
        </div>
        <div className="graph-stat-item">
          <strong>{graphData.stats.total_links}</strong>
          <span>Total Links</span>
        </div>
        <div className="graph-stat-item">
          <strong>{graphData.stats.parties}</strong>
          <span>Vendors/Parties</span>
        </div>
        <div className="graph-stat-item">
          <strong>{graphData.stats.documents}</strong>
          <span>Documents</span>
        </div>
        <div className="graph-stat-item">
          <strong>{graphData.stats.transactions}</strong>
          <span>Transactions</span>
        </div>
        <div className="graph-stat-item">
          <strong>{graphData.stats.emails}</strong>
          <span>Emails</span>
        </div>
      </div>

      {/* Graph Visualization */}
      <div className="graph-container">
        <ForceGraph2D
          ref={graphRef}
          graphData={graphData}
          nodeLabel={(node: any) => `${node.name} (${node.type})`}
          nodeColor={(node: any) => getNodeColor(node as GraphNode)}
          nodeVal={(node: any) => getNodeSize(node as GraphNode)}
          nodeCanvasObject={(node: any, ctx, globalScale) => {
            const label = node.name;
            const fontSize = 12 / globalScale;
            ctx.font = `${fontSize}px Sans-Serif`;
            const textWidth = ctx.measureText(label).width;
            const bckgDimensions = [textWidth, fontSize].map(n => n + fontSize * 0.2);

            // Draw node circle
            ctx.fillStyle = getNodeColor(node);
            ctx.beginPath();
            ctx.arc(node.x, node.y, getNodeSize(node), 0, 2 * Math.PI, false);
            ctx.fill();

            // Draw label background
            ctx.fillStyle = 'rgba(255, 255, 255, 0.9)';
            ctx.fillRect(
              node.x - bckgDimensions[0] / 2,
              node.y - bckgDimensions[1] / 2 + getNodeSize(node) + 2,
              bckgDimensions[0],
              bckgDimensions[1]
            );

            // Draw label text
            ctx.textAlign = 'center';
            ctx.textBaseline = 'middle';
            ctx.fillStyle = '#333';
            ctx.fillText(label, node.x, node.y + getNodeSize(node) + 8);
          }}
          linkLabel={(link: any) => link.label || link.type}
          linkColor={(link: any) => getLinkColor(link as GraphLink)}
          linkDirectionalArrowLength={3.5}
          linkDirectionalArrowRelPos={1}
          linkWidth={1.5}
          backgroundColor="#f9fafb"
          width={window.innerWidth - 200}
          height={600}
          onNodeClick={(node: any) => {
            console.log('Clicked node:', node);
            // You can add navigation or modal here
            if (node.type === 'document') {
              window.location.href = `/document/${node.id.replace('document-', '')}`;
            }
          }}
        />
      </div>

      {/* Legend */}
      <div className="graph-legend">
        <div className="legend-item">
          <div className="legend-dot" style={{ backgroundColor: '#4f46e5' }}></div>
          <span>Vendors/Parties</span>
        </div>
        <div className="legend-item">
          <div className="legend-dot" style={{ backgroundColor: '#10b981' }}></div>
          <span>Documents</span>
        </div>
        <div className="legend-item">
          <div className="legend-dot" style={{ backgroundColor: '#f59e0b' }}></div>
          <span>Transactions</span>
        </div>
        <div className="legend-item">
          <div className="legend-dot" style={{ backgroundColor: '#06b6d4' }}></div>
          <span>Emails</span>
        </div>
      </div>

      {/* Instructions */}
      <div className="info">
        <h3>How to Use</h3>
        <ul>
          <li>Zoom in/out with mouse wheel</li>
          <li>Drag to pan around the graph</li>
          <li>Click on document nodes to view details</li>
          <li>Hover over nodes to see their names</li>
          <li>Links show relationships between entities</li>
        </ul>
      </div>
    </div>
  );
};

export default KnowledgeGraph;
