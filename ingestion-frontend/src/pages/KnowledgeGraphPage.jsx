import { useEffect, useRef, useState, useCallback } from 'react'
import * as d3 from 'd3'
import { NODE_COLORS, EDGE_COLORS, EDGE_WIDTHS, EDGE_DASHED } from '../constants/graphColors'

export default function KnowledgeGraphPage() {
  const [selectedSource, setSelectedSource] = useState('financial')
  const [sources, setSources] = useState([])
  const [graphData, setGraphData] = useState(null)
  const [graphStats, setGraphStats] = useState(null)
  const [loading, setLoading] = useState(false)
  const [selectedNode, setSelectedNode] = useState(null)
  const [filterEntityTypes, setFilterEntityTypes] = useState([])
  const [filterRelTypes, setFilterRelTypes] = useState([])
  const [findPathMode, setFindPathMode] = useState(false)
  const [pathNodes, setPathNodes] = useState([null, null])
  const [searchTerm, setSearchTerm] = useState('')

  const svgRef = useRef(null)
  const simulationRef = useRef(null)
  const tooltipRef = useRef(null)

  // ── Load completed sources for dropdown ─────────────────────
  useEffect(() => {
    fetch('/api/ingest/list')
      .then(r => r.json())
      .then(data => setSources((data.ingestions || []).filter(i => i.status === 'complete')))
      .catch(() => {})
  }, [])

  // ── Load graph when source changes ──────────────────────────
  useEffect(() => {
    if (!selectedSource) return
    setLoading(true)
    setSelectedNode(null)
    setFilterEntityTypes([])
    setFilterRelTypes([])
    setFindPathMode(false)
    setPathNodes([null, null])

    const graphUrl = selectedSource === 'financial'
      ? '/api/graph/financial'
      : `/api/graph/source/${selectedSource}`

    Promise.all([
      fetch(graphUrl).then(r => r.json()),
      fetch(`/api/graph/stats/${selectedSource}`).then(r => r.json()),
    ])
      .then(([g, s]) => { setGraphData(g); setGraphStats(s); setLoading(false) })
      .catch(() => setLoading(false))
  }, [selectedSource])

  // ── Expand neighborhood ──────────────────────────────────────
  const fetchEntityNeighborhood = useCallback((label) => {
    const url = selectedSource === 'financial'
      ? `/api/graph/entity/${encodeURIComponent(label)}?depth=2`
      : `/api/graph/entity/${encodeURIComponent(label)}?depth=2&ingestion_id=${selectedSource}`

    fetch(url).then(r => r.json()).then(data => {
      if (!data.nodes?.length) return
      setGraphData(prev => {
        if (!prev) return data
        const existIds = new Set(prev.nodes.map(n => n.id))
        const existEdgeIds = new Set(prev.edges.map(e => e.id))
        return {
          ...prev,
          nodes: [...prev.nodes, ...data.nodes.filter(n => !existIds.has(n.id))],
          edges: [...prev.edges, ...data.edges.filter(e => !existEdgeIds.has(e.id))],
        }
      })
    }).catch(() => {})
  }, [selectedSource])

  // ── Find path ────────────────────────────────────────────────
  const fetchPath = useCallback((fromLabel, toLabel) => {
    const url = selectedSource === 'financial'
      ? `/api/graph/path?from_entity=${encodeURIComponent(fromLabel)}&to_entity=${encodeURIComponent(toLabel)}`
      : `/api/graph/path?from_entity=${encodeURIComponent(fromLabel)}&to_entity=${encodeURIComponent(toLabel)}&ingestion_id=${selectedSource}`

    fetch(url).then(r => r.json()).then(data => {
      if (!data.nodes?.length) return
      setGraphData(prev => {
        if (!prev) return data
        const existIds = new Set(prev.nodes.map(n => n.id))
        const existEdgeIds = new Set(prev.edges.map(e => e.id))
        return {
          ...prev,
          nodes: [...prev.nodes, ...data.nodes.filter(n => !existIds.has(n.id))],
          edges: [...prev.edges, ...data.edges.filter(e => !existEdgeIds.has(e.id))],
        }
      })
      setFindPathMode(false)
      setPathNodes([null, null])
    }).catch(() => {})
  }, [selectedSource])

  // ── D3 rendering ─────────────────────────────────────────────
  useEffect(() => {
    if (!graphData || !svgRef.current) return
    if (simulationRef.current) simulationRef.current.stop()
    if (tooltipRef.current) d3.select(tooltipRef.current).remove()

    const visibleNodes = graphData.nodes.filter(n =>
      filterEntityTypes.length === 0 || filterEntityTypes.includes(n.entity_type)
    )
    const visibleIds = new Set(visibleNodes.map(n => n.id))
    const visibleEdges = graphData.edges.filter(e => {
      const s = typeof e.source === 'object' ? e.source.id : e.source
      const t = typeof e.target === 'object' ? e.target.id : e.target
      return visibleIds.has(s) && visibleIds.has(t) &&
        (filterRelTypes.length === 0 || filterRelTypes.includes(e.relationship))
    })

    const svg = d3.select(svgRef.current)
    svg.selectAll('*').remove()

    const width = svgRef.current.clientWidth || 800
    const height = svgRef.current.clientHeight || 600

    const zoom = d3.zoom().scaleExtent([0.05, 4])
      .on('zoom', e => container.attr('transform', e.transform))
    svg.call(zoom)

    const container = svg.append('g')

    // Arrow markers
    const relTypes = [...new Set(visibleEdges.map(e => e.relationship)), 'default']
    svg.append('defs').selectAll('marker')
      .data(relTypes).enter().append('marker')
      .attr('id', d => `kg-arrow-${d.replace(/[^a-zA-Z0-9]/g, '_')}`)
      .attr('viewBox', '0 -5 10 10').attr('refX', 22).attr('refY', 0)
      .attr('markerWidth', 6).attr('markerHeight', 6).attr('orient', 'auto')
      .append('path')
      .attr('fill', d => EDGE_COLORS[d] || EDGE_COLORS.default)
      .attr('d', 'M0,-5L10,0L0,5')

    const nodesCopy = visibleNodes.map(n => ({ ...n }))
    const edgesCopy = visibleEdges.map(e => ({ ...e }))

    const simulation = d3.forceSimulation(nodesCopy)
      .force('link', d3.forceLink(edgesCopy).id(d => d.id).distance(90))
      .force('charge', d3.forceManyBody().strength(-280))
      .force('center', d3.forceCenter(width / 2, height / 2))
      .force('collision', d3.forceCollide(d => getRadius(d) + 6))
    simulationRef.current = simulation

    const edgeLines = container.append('g').selectAll('line').data(edgesCopy).enter().append('line')
      .attr('stroke', d => EDGE_COLORS[d.relationship] || EDGE_COLORS.default)
      .attr('stroke-width', d => EDGE_WIDTHS[d.relationship] || 1)
      .attr('stroke-dasharray', d => EDGE_DASHED[d.relationship] ? '5,3' : null)
      .attr('marker-end', d => `url(#kg-arrow-${d.relationship.replace(/[^a-zA-Z0-9]/g, '_')})`)
      .attr('opacity', 0.65)

    const edgeLabels = container.append('g').selectAll('text').data(edgesCopy).enter().append('text')
      .attr('font-size', '8px').attr('fill', '#888').attr('text-anchor', 'middle')
      .text(d => d.relationship).style('pointer-events', 'none').style('opacity', 0)

    const tooltip = d3.select('body').append('div')
      .style('position', 'absolute').style('background', 'rgba(0,0,0,0.88)')
      .style('color', '#fff').style('padding', '6px 10px').style('border-radius', '6px')
      .style('font-size', '12px').style('pointer-events', 'none').style('opacity', 0)
      .style('z-index', 9999).style('max-width', '200px')
    tooltipRef.current = tooltip.node()

    const nodeGroups = container.append('g').selectAll('g').data(nodesCopy).enter().append('g')
      .attr('cursor', 'pointer')
      .call(d3.drag()
        .on('start', (e, d) => { if (!e.active) simulation.alphaTarget(0.3).restart(); d.fx = d.x; d.fy = d.y })
        .on('drag', (e, d) => { d.fx = e.x; d.fy = e.y })
        .on('end', (e, d) => { if (!e.active) simulation.alphaTarget(0); d.fx = null; d.fy = null })
      )

    nodeGroups.append('circle')
      .attr('r', d => getRadius(d))
      .attr('fill', d => NODE_COLORS[d.entity_type] || NODE_COLORS.default)
      .attr('stroke', '#fff').attr('stroke-width', 1.5)
      .attr('opacity', d => searchTerm && !d.label.toLowerCase().includes(searchTerm.toLowerCase()) ? 0.15 : 1)

    nodeGroups.append('text')
      .attr('dy', d => getRadius(d) + 11).attr('text-anchor', 'middle')
      .attr('font-size', '9px').attr('fill', '#555')
      .style('pointer-events', 'none')
      .text(d => d.label.length > 14 ? d.label.slice(0, 14) + '…' : d.label)

    nodeGroups
      .on('click', (event, d) => {
        event.stopPropagation()
        if (findPathMode) {
          setPathNodes(prev => {
            if (!prev[0]) return [d, null]
            if (!prev[1] && d.id !== prev[0].id) { fetchPath(prev[0].label, d.label); return [prev[0], d] }
            return prev
          })
        } else {
          setSelectedNode(d)
        }
      })
      .on('dblclick', (event, d) => { event.stopPropagation(); fetchEntityNeighborhood(d.label) })
      .on('mouseover', (event, d) => {
        edgeLabels.style('opacity', e => {
          const s = typeof e.source === 'object' ? e.source.id : e.source
          const t = typeof e.target === 'object' ? e.target.id : e.target
          return (s === d.id || t === d.id) ? 1 : 0
        })
        tooltip.style('opacity', 1)
          .html(`<strong>${d.label}</strong><br/><span style="color:#aaa">${d.entity_type}</span><br/>${d.connection_count} connections`)
      })
      .on('mousemove', e => tooltip.style('left', (e.pageX + 12) + 'px').style('top', (e.pageY - 28) + 'px'))
      .on('mouseout', () => { edgeLabels.style('opacity', 0); tooltip.style('opacity', 0) })

    simulation.on('tick', () => {
      edgeLines
        .attr('x1', d => d.source.x).attr('y1', d => d.source.y)
        .attr('x2', d => d.target.x).attr('y2', d => d.target.y)
      edgeLabels
        .attr('x', d => (d.source.x + d.target.x) / 2)
        .attr('y', d => (d.source.y + d.target.y) / 2)
      nodeGroups.attr('transform', d => `translate(${d.x},${d.y})`)
    })

    return () => { simulation.stop(); tooltip.remove() }
  }, [graphData, filterEntityTypes, filterRelTypes, searchTerm, findPathMode, fetchEntityNeighborhood, fetchPath])

  function getRadius(node) {
    return Math.min(24, Math.max(7, 7 + (node.connection_count || 0) * 1.4))
  }

  const allEntityTypes = graphData ? [...new Set(graphData.nodes.map(n => n.entity_type))] : []
  const allRelTypes = graphData ? [...new Set(graphData.edges.map(e => e.relationship))] : []

  const getSourceIcon = (type) => {
    const icons = { github_repo: '🐙', webpage: '🌐', pdf: '📄', youtube: '🎥', reddit: '💬', rss: '📡' }
    return icons[type] || '📦'
  }

  return (
    <div className="h-[calc(100vh-4rem)] flex overflow-hidden">

      {/* LEFT: Controls */}
      <div className="w-60 flex-shrink-0 flex flex-col gap-4 overflow-y-auto p-4 border-r border-claude-border bg-claude-surface">

        {/* Source selector */}
        <div>
          <p className="text-xs font-mono font-medium text-claude-text-tertiary uppercase tracking-widest mb-2">Data Source</p>
          <select
            value={selectedSource}
            onChange={e => setSelectedSource(e.target.value)}
            className="w-full bg-claude-bg border border-claude-border rounded-lg px-3 py-2 text-sm text-claude-text focus:outline-none focus:ring-2 focus:ring-claude-accent"
          >
            <option value="financial">📊 All Sources</option>
            {sources.map(s => (
              <option key={s.ingestion_id} value={s.ingestion_id}>
                {getSourceIcon(s.source_type)} {s.source_name || s.ingestion_id}
              </option>
            ))}
          </select>
        </div>

        {/* Search */}
        <div>
          <p className="text-xs font-medium text-claude-text-secondary uppercase tracking-wider mb-2">Search</p>
          <input
            type="text"
            placeholder="Highlight nodes..."
            value={searchTerm}
            onChange={e => setSearchTerm(e.target.value)}
            className="w-full bg-claude-bg border border-claude-border rounded-lg px-3 py-2 text-sm text-claude-text placeholder-claude-text-tertiary focus:outline-none focus:ring-2 focus:ring-claude-accent"
          />
        </div>

        {/* Entity type filter */}
        {allEntityTypes.length > 0 && (
          <div>
            <p className="text-xs font-medium text-claude-text-secondary uppercase tracking-wider mb-2">Node Types</p>
            <div className="space-y-1.5">
              {allEntityTypes.map(type => {
                const active = filterEntityTypes.length === 0 || filterEntityTypes.includes(type)
                const count = graphData.nodes.filter(n => n.entity_type === type).length
                return (
                  <label key={type} className="flex items-center gap-2 text-xs cursor-pointer">
                    <input
                      type="checkbox"
                      checked={active}
                      onChange={e => {
                        if (e.target.checked) {
                          setFilterEntityTypes(prev => [...prev, type])
                        } else {
                          setFilterEntityTypes(
                            filterEntityTypes.length === 0
                              ? allEntityTypes.filter(t => t !== type)
                              : prev => prev.filter(t => t !== type)
                          )
                        }
                      }}
                      className="w-3 h-3 rounded"
                    />
                    <span className="w-2.5 h-2.5 rounded-full flex-shrink-0"
                      style={{ backgroundColor: NODE_COLORS[type] || NODE_COLORS.default }} />
                    <span className="text-claude-text flex-1 truncate">{type}</span>
                    <span className="text-claude-text-tertiary">{count}</span>
                  </label>
                )
              })}
            </div>
          </div>
        )}

        {/* Relationship filter */}
        {allRelTypes.length > 0 && (
          <div>
            <p className="text-xs font-medium text-claude-text-secondary uppercase tracking-wider mb-2">Relationships</p>
            <div className="space-y-1.5">
              {allRelTypes.map(rel => {
                const active = filterRelTypes.length === 0 || filterRelTypes.includes(rel)
                return (
                  <label key={rel} className="flex items-center gap-2 text-xs cursor-pointer">
                    <input
                      type="checkbox"
                      checked={active}
                      onChange={e => {
                        if (e.target.checked) {
                          setFilterRelTypes(prev => [...prev, rel])
                        } else {
                          setFilterRelTypes(
                            filterRelTypes.length === 0
                              ? allRelTypes.filter(r => r !== rel)
                              : prev => prev.filter(r => r !== rel)
                          )
                        }
                      }}
                      className="w-3 h-3 rounded"
                    />
                    <span className="w-5 border-t inline-block flex-shrink-0"
                      style={{
                        borderColor: EDGE_COLORS[rel] || EDGE_COLORS.default,
                        borderStyle: EDGE_DASHED[rel] ? 'dashed' : 'solid',
                        borderWidth: '1.5px'
                      }} />
                    <span className="text-claude-text truncate">{rel}</span>
                  </label>
                )
              })}
            </div>
          </div>
        )}

        {/* Find Path */}
        <div>
          <p className="text-xs font-medium text-claude-text-secondary uppercase tracking-wider mb-2">Find Connection</p>
          <button
            onClick={() => { setFindPathMode(p => !p); setPathNodes([null, null]) }}
            className={`w-full py-2 px-3 rounded-lg text-xs font-medium transition-colors ${
              findPathMode
                ? 'bg-claude-accent text-white'
                : 'bg-claude-code-bg border border-claude-border text-claude-text hover:bg-claude-border'
            }`}
          >
            {findPathMode ? 'Cancel' : 'Enable Path Find'}
          </button>
          {findPathMode && (
            <div className="mt-2 text-xs text-claude-text-secondary space-y-0.5">
              <div>From: <span className="text-claude-text">{pathNodes[0]?.label || 'click a node'}</span></div>
              <div>To: <span className="text-claude-text">{pathNodes[1]?.label || 'click another'}</span></div>
            </div>
          )}
        </div>

        {/* Stats */}
        {graphStats && (
          <div>
            <p className="text-xs font-medium text-claude-text-secondary uppercase tracking-wider mb-2">Stats</p>
            <div className="bg-claude-code-bg border border-claude-border rounded-lg p-3 space-y-1.5 text-xs">
              <div className="flex justify-between">
                <span className="text-claude-text-secondary">Nodes</span>
                <span className="text-claude-text font-medium">{graphStats.node_count}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-claude-text-secondary">Edges</span>
                <span className="text-claude-text font-medium">{graphStats.edge_count}</span>
              </div>
              {graphStats.most_connected?.length > 0 && (
                <div className="pt-1.5 border-t border-claude-border">
                  <p className="text-claude-text-tertiary mb-1">Most connected</p>
                  {graphStats.most_connected.map((n, i) => (
                    <div key={i} className="flex justify-between">
                      <span className="text-claude-text-secondary truncate max-w-[110px]">{n.name}</span>
                      <span className="text-claude-text-tertiary">{n.connections}</span>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        )}
      </div>

      {/* CENTER: Graph canvas */}
      <div className="flex-1 relative overflow-hidden"
        style={{
          background: '#F7F6F3',
          backgroundImage: `url("data:image/svg+xml,%3Csvg width='20' height='20' xmlns='http://www.w3.org/2000/svg'%3E%3Ccircle cx='1' cy='1' r='1' fill='%23D4D0C8' fill-opacity='0.6'/%3E%3C/svg%3E")`,
          backgroundSize: '20px 20px',
        }}>
        {loading && (
          <div className="absolute inset-0 flex items-center justify-center bg-claude-bg/90 z-20">
            <div className="flex items-center gap-3 text-claude-text-secondary">
              <div className="w-5 h-5 border-2 border-claude-border border-t-claude-accent rounded-full animate-spin" />
              Loading graph...
            </div>
          </div>
        )}

        {!loading && (!graphData || graphData.nodes?.length === 0) && (
          <div className="absolute inset-0 flex items-center justify-center">
            <div className="text-center">
              <div className="w-16 h-16 bg-claude-code-bg rounded-full flex items-center justify-center mx-auto mb-4">
                <svg className="w-8 h-8 text-claude-text-tertiary" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 20l-5.447-2.724A1 1 0 013 16.382V5.618a1 1 0 011.447-.894L9 7m0 13l6-3m-6 3V7m6 10l4.553 2.276A1 1 0 0021 18.382V7.618a1 1 0 00-.553-.894L15 4m0 13V4m0 0L9 7" />
                </svg>
              </div>
              <p className="font-heading text-2xl font-bold text-claude-text mb-1">No graph data</p>
              <p className="text-claude-text-secondary text-sm">Ingest a source with entities to see the graph</p>
            </div>
          </div>
        )}

        {/* Legend */}
        {allEntityTypes.length > 0 && (
          <div className="absolute top-3 right-3 bg-claude-surface border border-claude-border rounded-lg p-3 text-xs z-10 shadow-claude">
            <p className="font-medium text-claude-text mb-2">Legend</p>
            {allEntityTypes.slice(0, 7).map(type => (
              <div key={type} className="flex items-center gap-1.5 mb-1">
                <span className="w-2.5 h-2.5 rounded-full flex-shrink-0"
                  style={{ backgroundColor: NODE_COLORS[type] || NODE_COLORS.default }} />
                <span className="text-claude-text-secondary">{type}</span>
              </div>
            ))}
          </div>
        )}

        {/* Hint */}
        <div className="absolute bottom-3 left-3 text-xs text-claude-text-tertiary z-10">
          Scroll to zoom · Drag nodes · Click to inspect · Double-click to expand
        </div>

        <svg ref={svgRef} width="100%" height="100%" />
      </div>

      {/* RIGHT: Node detail panel */}
      {selectedNode && (
        <div className="w-56 flex-shrink-0 bg-claude-surface border-l border-claude-border p-4 overflow-y-auto">
          <div className="flex justify-between items-start mb-3">
            <h3 className="font-display font-bold text-sm text-claude-text leading-tight break-all">
              {selectedNode.label}
            </h3>
            <button
              onClick={() => setSelectedNode(null)}
              className="text-claude-text-tertiary hover:text-claude-text text-lg leading-none ml-2 flex-shrink-0"
            >×</button>
          </div>

          <div className="space-y-3 text-xs">
            <div>
              <p className="text-claude-text-secondary mb-0.5">Type</p>
              <div className="flex items-center gap-1.5">
                <span className="w-2.5 h-2.5 rounded-full flex-shrink-0"
                  style={{ backgroundColor: NODE_COLORS[selectedNode.entity_type] || NODE_COLORS.default }} />
                <span className="text-claude-text">{selectedNode.entity_type}</span>
              </div>
            </div>

            <div>
              <p className="text-claude-text-secondary mb-0.5 font-mono text-xs uppercase tracking-wider">Connections</p>
              <span className="text-claude-text font-mono font-medium">{selectedNode.connection_count}</span>
            </div>

            {selectedNode.source_url && (
              <div>
                <p className="text-claude-text-secondary mb-0.5">Source</p>
                <a href={selectedNode.source_url} target="_blank" rel="noopener noreferrer"
                  className="text-claude-accent hover:underline break-all">
                  {selectedNode.source_id || selectedNode.source_url.slice(0, 40) + '…'}
                </a>
              </div>
            )}

            <div>
              <p className="text-claude-text-secondary mb-1">Connected to</p>
              <div className="space-y-0.5">
                {(graphData?.edges || [])
                  .filter(e => {
                    const s = typeof e.source === 'object' ? e.source.id : e.source
                    const t = typeof e.target === 'object' ? e.target.id : e.target
                    return s === selectedNode.id || t === selectedNode.id
                  })
                  .slice(0, 8)
                  .map((e, i) => {
                    const s = typeof e.source === 'object' ? e.source.id : e.source
                    const t = typeof e.target === 'object' ? e.target.id : e.target
                    const otherId = s === selectedNode.id ? t : s
                    const other = graphData.nodes.find(n => n.id === otherId)
                    return (
                      <div key={i} className="flex items-center gap-1">
                        <span style={{ color: EDGE_COLORS[e.relationship] || EDGE_COLORS.default }}>
                          {e.relationship}
                        </span>
                        <span className="text-claude-text-secondary truncate">{other?.label || otherId}</span>
                      </div>
                    )
                  })}
              </div>
            </div>

            <button
              onClick={() => fetchEntityNeighborhood(selectedNode.label)}
              className="w-full py-1.5 bg-claude-code-bg border border-claude-border rounded-lg text-claude-text-secondary hover:text-claude-text hover:bg-claude-border transition-colors"
            >
              Expand neighborhood
            </button>

            <button
              onClick={() => { setFindPathMode(true); setPathNodes([selectedNode, null]) }}
              className="w-full py-1.5 bg-claude-accent/10 border border-claude-accent/30 rounded-lg text-claude-accent hover:bg-claude-accent/20 transition-colors"
            >
              Find path from here
            </button>
          </div>
        </div>
      )}
    </div>
  )
}
