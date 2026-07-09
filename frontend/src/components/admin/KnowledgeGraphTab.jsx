import { useEffect, useRef, useState, useCallback } from 'react'
import * as d3 from 'd3'
import { NODE_COLORS, EDGE_COLORS, EDGE_WIDTHS, EDGE_DASHED } from '../../constants/graphColors'

export default function KnowledgeGraphTab() {
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

  // ── Load ingested sources for dropdown ──────────────────────
  useEffect(() => {
    fetch('/api/ingest/list')
      .then(r => r.json())
      .then(data => {
        const completed = (data.ingestions || []).filter(i => i.status === 'complete')
        setSources(completed)
      })
      .catch(() => {})
  }, [])

  // ── Load graph data when source changes ─────────────────────
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

    const statsUrl = `/api/graph/stats/${selectedSource}`

    Promise.all([
      fetch(graphUrl).then(r => r.json()),
      fetch(statsUrl).then(r => r.json())
    ])
      .then(([gData, sData]) => {
        setGraphData(gData)
        setGraphStats(sData)
        setLoading(false)
      })
      .catch(() => setLoading(false))
  }, [selectedSource])

  // ── Expand neighborhood on double-click ─────────────────────
  const fetchEntityNeighborhood = useCallback((nodeLabel) => {
    const url = selectedSource === 'financial'
      ? `/api/graph/entity/${encodeURIComponent(nodeLabel)}?depth=2`
      : `/api/graph/entity/${encodeURIComponent(nodeLabel)}?depth=2&ingestion_id=${selectedSource}`

    fetch(url)
      .then(r => r.json())
      .then(data => {
        if (!data.nodes?.length) return
        setGraphData(prev => {
          if (!prev) return data
          const existingIds = new Set(prev.nodes.map(n => n.id))
          const newNodes = data.nodes.filter(n => !existingIds.has(n.id))
          const existingEdgeIds = new Set(prev.edges.map(e => e.id))
          const newEdges = data.edges.filter(e => !existingEdgeIds.has(e.id))
          return {
            ...prev,
            nodes: [...prev.nodes, ...newNodes],
            edges: [...prev.edges, ...newEdges]
          }
        })
      })
      .catch(() => {})
  }, [selectedSource])

  // ── Find path between two nodes ─────────────────────────────
  const fetchPath = useCallback((fromLabel, toLabel) => {
    const base = selectedSource === 'financial'
      ? `/api/graph/path?from_entity=${encodeURIComponent(fromLabel)}&to_entity=${encodeURIComponent(toLabel)}`
      : `/api/graph/path?from_entity=${encodeURIComponent(fromLabel)}&to_entity=${encodeURIComponent(toLabel)}&ingestion_id=${selectedSource}`

    fetch(base)
      .then(r => r.json())
      .then(data => {
        if (!data.nodes?.length) return
        setGraphData(prev => {
          if (!prev) return data
          const existingIds = new Set(prev.nodes.map(n => n.id))
          const newNodes = data.nodes.filter(n => !existingIds.has(n.id))
          const existingEdgeIds = new Set(prev.edges.map(e => e.id))
          const newEdges = data.edges.filter(e => !existingEdgeIds.has(e.id))
          return {
            ...prev,
            nodes: [...prev.nodes, ...newNodes],
            edges: [...prev.edges, ...newEdges]
          }
        })
        setFindPathMode(false)
        setPathNodes([null, null])
      })
      .catch(() => {})
  }, [selectedSource])

  // ── D3 rendering ─────────────────────────────────────────────
  useEffect(() => {
    if (!graphData || !svgRef.current) return
    if (simulationRef.current) simulationRef.current.stop()
    if (tooltipRef.current) tooltipRef.current.remove()

    // Filter nodes/edges
    const visibleNodes = graphData.nodes.filter(n =>
      filterEntityTypes.length === 0 || filterEntityTypes.includes(n.entity_type)
    )
    const visibleIds = new Set(visibleNodes.map(n => n.id))
    const visibleEdges = graphData.edges.filter(e => {
      const srcId = typeof e.source === 'object' ? e.source.id : e.source
      const tgtId = typeof e.target === 'object' ? e.target.id : e.target
      return visibleIds.has(srcId) && visibleIds.has(tgtId) &&
        (filterRelTypes.length === 0 || filterRelTypes.includes(e.relationship))
    })

    const svg = d3.select(svgRef.current)
    svg.selectAll('*').remove()

    const width = svgRef.current.clientWidth || 800
    const height = svgRef.current.clientHeight || 600

    // Zoom
    const zoom = d3.zoom()
      .scaleExtent([0.05, 4])
      .on('zoom', event => container.attr('transform', event.transform))
    svg.call(zoom)

    const container = svg.append('g')

    // Arrow markers
    const allRelTypes = [...new Set(visibleEdges.map(e => e.relationship)), 'default']
    svg.append('defs').selectAll('marker')
      .data(allRelTypes)
      .enter().append('marker')
      .attr('id', d => `arrow-${d.replace(/[^a-zA-Z0-9]/g, '_')}`)
      .attr('viewBox', '0 -5 10 10')
      .attr('refX', 22)
      .attr('refY', 0)
      .attr('markerWidth', 6)
      .attr('markerHeight', 6)
      .attr('orient', 'auto')
      .append('path')
      .attr('fill', d => EDGE_COLORS[d] || EDGE_COLORS.default)
      .attr('d', 'M0,-5L10,0L0,5')

    // Simulation — use copies to avoid mutating original data
    const nodesCopy = visibleNodes.map(n => ({ ...n }))
    const edgesCopy = visibleEdges.map(e => ({ ...e }))

    const simulation = d3.forceSimulation(nodesCopy)
      .force('link', d3.forceLink(edgesCopy).id(d => d.id).distance(90))
      .force('charge', d3.forceManyBody().strength(-280))
      .force('center', d3.forceCenter(width / 2, height / 2))
      .force('collision', d3.forceCollide(d => getNodeRadius(d) + 6))
    simulationRef.current = simulation

    // Edges
    const edgeLines = container.append('g')
      .selectAll('line')
      .data(edgesCopy)
      .enter().append('line')
      .attr('stroke', d => EDGE_COLORS[d.relationship] || EDGE_COLORS.default)
      .attr('stroke-width', d => EDGE_WIDTHS[d.relationship] || 1)
      .attr('stroke-dasharray', d => EDGE_DASHED[d.relationship] ? '5,3' : null)
      .attr('marker-end', d => `url(#arrow-${d.relationship.replace(/[^a-zA-Z0-9]/g, '_')})`)
      .attr('opacity', 0.65)

    // Edge labels (hidden by default, shown on node hover)
    const edgeLabels = container.append('g')
      .selectAll('text')
      .data(edgesCopy)
      .enter().append('text')
      .attr('font-size', '8px')
      .attr('fill', '#aaa')
      .attr('text-anchor', 'middle')
      .text(d => d.relationship)
      .style('pointer-events', 'none')
      .style('opacity', 0)

    // Tooltip
    const tooltip = d3.select('body').append('div')
      .style('position', 'absolute')
      .style('background', 'rgba(0,0,0,0.9)')
      .style('color', '#fff')
      .style('padding', '6px 10px')
      .style('border-radius', '6px')
      .style('font-size', '12px')
      .style('pointer-events', 'none')
      .style('opacity', 0)
      .style('z-index', 9999)
      .style('max-width', '200px')
    tooltipRef.current = tooltip.node()

    // Node groups
    const nodeGroups = container.append('g')
      .selectAll('g')
      .data(nodesCopy)
      .enter().append('g')
      .attr('cursor', 'pointer')
      .call(
        d3.drag()
          .on('start', (event, d) => {
            if (!event.active) simulation.alphaTarget(0.3).restart()
            d.fx = d.x; d.fy = d.y
          })
          .on('drag', (event, d) => { d.fx = event.x; d.fy = event.y })
          .on('end', (event, d) => {
            if (!event.active) simulation.alphaTarget(0)
            d.fx = null; d.fy = null
          })
      )

    // Circles
    nodeGroups.append('circle')
      .attr('r', d => getNodeRadius(d))
      .attr('fill', d => NODE_COLORS[d.entity_type] || NODE_COLORS.default)
      .attr('stroke', '#111')
      .attr('stroke-width', 1.5)
      .attr('opacity', d => {
        if (searchTerm && !d.label.toLowerCase().includes(searchTerm.toLowerCase())) return 0.15
        return 1
      })

    // Labels
    nodeGroups.append('text')
      .attr('dy', d => getNodeRadius(d) + 11)
      .attr('text-anchor', 'middle')
      .attr('font-size', '9px')
      .attr('fill', '#ccc')
      .style('pointer-events', 'none')
      .text(d => truncate(d.label, 14))

    // Interactions
    nodeGroups
      .on('click', (event, d) => {
        event.stopPropagation()
        if (findPathMode) {
          setPathNodes(prev => {
            if (!prev[0]) return [d, null]
            if (!prev[1] && d.id !== prev[0].id) {
              fetchPath(prev[0].label, d.label)
              return [prev[0], d]
            }
            return prev
          })
        } else {
          setSelectedNode(d)
        }
      })
      .on('dblclick', (event, d) => {
        event.stopPropagation()
        fetchEntityNeighborhood(d.label)
      })
      .on('mouseover', (event, d) => {
        edgeLabels.style('opacity', e => {
          const srcId = typeof e.source === 'object' ? e.source.id : e.source
          const tgtId = typeof e.target === 'object' ? e.target.id : e.target
          return (srcId === d.id || tgtId === d.id) ? 1 : 0
        })
        tooltip
          .style('opacity', 1)
          .html(`<strong>${d.label}</strong><br/><span style="color:#aaa">${d.entity_type}</span><br/>${d.connection_count} connections`)
      })
      .on('mousemove', event => {
        tooltip
          .style('left', (event.pageX + 12) + 'px')
          .style('top', (event.pageY - 28) + 'px')
      })
      .on('mouseout', () => {
        edgeLabels.style('opacity', 0)
        tooltip.style('opacity', 0)
      })

    // Tick
    simulation.on('tick', () => {
      edgeLines
        .attr('x1', d => d.source.x)
        .attr('y1', d => d.source.y)
        .attr('x2', d => d.target.x)
        .attr('y2', d => d.target.y)
      edgeLabels
        .attr('x', d => (d.source.x + d.target.x) / 2)
        .attr('y', d => (d.source.y + d.target.y) / 2)
      nodeGroups.attr('transform', d => `translate(${d.x},${d.y})`)
    })

    return () => {
      simulation.stop()
      tooltip.remove()
    }
  }, [graphData, filterEntityTypes, filterRelTypes, searchTerm, findPathMode, fetchEntityNeighborhood, fetchPath])

  // ── Helpers ──────────────────────────────────────────────────
  function getNodeRadius(node) {
    return Math.min(24, Math.max(7, 7 + (node.connection_count || 0) * 1.4))
  }
  function truncate(str, max) {
    return str.length > max ? str.slice(0, max) + '…' : str
  }

  const allEntityTypes = graphData ? [...new Set(graphData.nodes.map(n => n.entity_type))] : []
  const allRelTypes = graphData ? [...new Set(graphData.edges.map(e => e.relationship))] : []

  const getSourceIcon = (type) => {
    const icons = { github_repo: '🐙', webpage: '🌐', pdf: '📄', youtube: '🎥', reddit: '💬', rss: '📡' }
    return icons[type] || '📦'
  }

  // ── Render ───────────────────────────────────────────────────
  return (
    <div className="flex h-full gap-0 overflow-hidden">

      {/* LEFT: Controls */}
      <div className="w-64 flex-shrink-0 flex flex-col gap-3 overflow-y-auto p-4 border-r border-gray-800 bg-gray-950">

        {/* Source selector */}
        <div>
          <p className="text-xs text-gray-500 uppercase tracking-wider mb-2">Data Source</p>
          <select
            value={selectedSource}
            onChange={e => setSelectedSource(e.target.value)}
            className="w-full bg-gray-900 border border-gray-800 rounded px-2 py-1.5 text-sm text-white focus:outline-none focus:border-gray-600"
          >
            <option value="financial">📊 Financial Domain</option>
            {sources.map(s => (
              <option key={s.ingestion_id} value={s.ingestion_id}>
                {getSourceIcon(s.source_type)} {s.source_name || s.ingestion_id}
              </option>
            ))}
          </select>
        </div>

        {/* Search */}
        <div>
          <p className="text-xs text-gray-500 uppercase tracking-wider mb-2">Search Nodes</p>
          <input
            type="text"
            placeholder="Highlight matching nodes..."
            value={searchTerm}
            onChange={e => setSearchTerm(e.target.value)}
            className="w-full bg-gray-900 border border-gray-800 rounded px-2 py-1.5 text-sm text-white placeholder-gray-700 focus:outline-none focus:border-gray-600"
          />
        </div>

        {/* Entity type filter */}
        {allEntityTypes.length > 0 && (
          <div>
            <p className="text-xs text-gray-500 uppercase tracking-wider mb-2">Node Types</p>
            <div className="space-y-1">
              {allEntityTypes.map(type => {
                const active = filterEntityTypes.length === 0 || filterEntityTypes.includes(type)
                const count = graphData.nodes.filter(n => n.entity_type === type).length
                return (
                  <label key={type} className="flex items-center gap-2 text-xs cursor-pointer group">
                    <input
                      type="checkbox"
                      checked={active}
                      onChange={e => {
                        if (e.target.checked) {
                          setFilterEntityTypes(prev => prev.filter(t => t !== type).length === allEntityTypes.length - 1
                            ? [] : [...prev, type])
                        } else {
                          setFilterEntityTypes(
                            filterEntityTypes.length === 0
                              ? allEntityTypes.filter(t => t !== type)
                              : prev => prev.filter(t => t !== type)
                          )
                        }
                      }}
                      className="w-3 h-3"
                    />
                    <span
                      className="w-2.5 h-2.5 rounded-full flex-shrink-0"
                      style={{ backgroundColor: NODE_COLORS[type] || NODE_COLORS.default }}
                    />
                    <span className="text-gray-300 truncate flex-1">{type}</span>
                    <span className="text-gray-600">{count}</span>
                  </label>
                )
              })}
            </div>
          </div>
        )}

        {/* Relationship filter */}
        {allRelTypes.length > 0 && (
          <div>
            <p className="text-xs text-gray-500 uppercase tracking-wider mb-2">Relationships</p>
            <div className="space-y-1">
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
                      className="w-3 h-3"
                    />
                    <span
                      className="w-5 border-t inline-block flex-shrink-0"
                      style={{
                        borderColor: EDGE_COLORS[rel] || EDGE_COLORS.default,
                        borderStyle: EDGE_DASHED[rel] ? 'dashed' : 'solid',
                        borderWidth: '1.5px'
                      }}
                    />
                    <span className="text-gray-300 truncate">{rel}</span>
                  </label>
                )
              })}
            </div>
          </div>
        )}

        {/* Find Path */}
        <div>
          <p className="text-xs text-gray-500 uppercase tracking-wider mb-2">Find Connection</p>
          <button
            onClick={() => { setFindPathMode(p => !p); setPathNodes([null, null]) }}
            className={`w-full py-1.5 px-3 rounded text-xs font-medium transition-colors ${
              findPathMode
                ? 'bg-blue-600 text-white'
                : 'bg-gray-900 border border-gray-800 text-gray-400 hover:text-white'
            }`}
          >
            {findPathMode ? 'Cancel' : 'Enable Path Find'}
          </button>
          {findPathMode && (
            <div className="mt-2 text-xs text-gray-500 space-y-0.5">
              <div>From: <span className="text-gray-300">{pathNodes[0]?.label || 'click a node'}</span></div>
              <div>To: <span className="text-gray-300">{pathNodes[1]?.label || 'click another'}</span></div>
            </div>
          )}
        </div>

        {/* Stats */}
        {graphStats && (
          <div>
            <p className="text-xs text-gray-500 uppercase tracking-wider mb-2">Graph Stats</p>
            <div className="bg-gray-900 border border-gray-800 rounded p-3 space-y-1.5 text-xs">
              <div className="flex justify-between">
                <span className="text-gray-500">Nodes</span>
                <span className="text-white font-medium">{graphStats.node_count}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-500">Edges</span>
                <span className="text-white font-medium">{graphStats.edge_count}</span>
              </div>
              {graphStats.most_connected?.length > 0 && (
                <div className="pt-1 border-t border-gray-800">
                  <p className="text-gray-600 mb-1">Most connected</p>
                  {graphStats.most_connected.map((n, i) => (
                    <div key={i} className="flex justify-between">
                      <span className="text-gray-400 truncate max-w-[120px]">{n.name}</span>
                      <span className="text-gray-600">{n.connections}</span>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        )}
      </div>

      {/* CENTER: Graph canvas */}
      <div className="flex-1 relative overflow-hidden bg-gray-950">
        {loading && (
          <div className="absolute inset-0 flex items-center justify-center bg-gray-950/90 z-20">
            <div className="flex items-center gap-3 text-gray-400">
              <div className="w-5 h-5 border-2 border-gray-700 border-t-gray-300 rounded-full animate-spin" />
              Loading graph...
            </div>
          </div>
        )}

        {!loading && (!graphData || graphData.nodes?.length === 0) && (
          <div className="absolute inset-0 flex items-center justify-center">
            <div className="text-center text-gray-600">
              <p className="text-lg mb-1">No graph data</p>
              <p className="text-sm">Select a source with ingested entities</p>
            </div>
          </div>
        )}

        {/* Legend */}
        <div className="absolute top-3 right-3 bg-black/70 border border-gray-800 rounded p-2 text-xs z-10">
          <p className="text-gray-500 mb-1.5 font-medium">Legend</p>
          {allEntityTypes.slice(0, 7).map(type => (
            <div key={type} className="flex items-center gap-1.5 mb-0.5">
              <span
                className="w-2.5 h-2.5 rounded-full flex-shrink-0"
                style={{ backgroundColor: NODE_COLORS[type] || NODE_COLORS.default }}
              />
              <span className="text-gray-400">{type}</span>
            </div>
          ))}
        </div>

        {/* Hint */}
        <div className="absolute bottom-3 left-3 text-xs text-gray-700 z-10">
          Scroll to zoom · Drag nodes · Click to inspect · Double-click to expand
        </div>

        <svg ref={svgRef} width="100%" height="100%" />
      </div>

      {/* RIGHT: Node detail panel */}
      {selectedNode && (
        <div className="w-56 flex-shrink-0 bg-gray-950 border-l border-gray-800 p-4 overflow-y-auto">
          <div className="flex justify-between items-start mb-3">
            <h3 className="font-semibold text-sm text-white leading-tight break-all">
              {selectedNode.label}
            </h3>
            <button
              onClick={() => setSelectedNode(null)}
              className="text-gray-600 hover:text-gray-300 text-lg leading-none ml-2 flex-shrink-0"
            >×</button>
          </div>

          <div className="space-y-3 text-xs">
            <div>
              <p className="text-gray-600 mb-0.5">Type</p>
              <div className="flex items-center gap-1.5">
                <span
                  className="w-2.5 h-2.5 rounded-full flex-shrink-0"
                  style={{ backgroundColor: NODE_COLORS[selectedNode.entity_type] || NODE_COLORS.default }}
                />
                <span className="text-gray-300">{selectedNode.entity_type}</span>
              </div>
            </div>

            <div>
              <p className="text-gray-600 mb-0.5">Connections</p>
              <span className="text-white font-medium">{selectedNode.connection_count}</span>
            </div>

            {selectedNode.source_url && (
              <div>
                <p className="text-gray-600 mb-0.5">Source</p>
                <a
                  href={selectedNode.source_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-blue-400 hover:underline break-all"
                >
                  {selectedNode.source_id || selectedNode.source_url.slice(0, 40) + '…'}
                </a>
              </div>
            )}

            {/* Connected edges */}
            <div>
              <p className="text-gray-600 mb-1">Connected to</p>
              <div className="space-y-0.5">
                {(graphData?.edges || [])
                  .filter(e => {
                    const srcId = typeof e.source === 'object' ? e.source.id : e.source
                    const tgtId = typeof e.target === 'object' ? e.target.id : e.target
                    return srcId === selectedNode.id || tgtId === selectedNode.id
                  })
                  .slice(0, 8)
                  .map((e, i) => {
                    const srcId = typeof e.source === 'object' ? e.source.id : e.source
                    const tgtId = typeof e.target === 'object' ? e.target.id : e.target
                    const otherId = srcId === selectedNode.id ? tgtId : srcId
                    const other = graphData.nodes.find(n => n.id === otherId)
                    return (
                      <div key={i} className="flex items-center gap-1">
                        <span style={{ color: EDGE_COLORS[e.relationship] || EDGE_COLORS.default }}>
                          {e.relationship}
                        </span>
                        <span className="text-gray-400 truncate">{other?.label || otherId}</span>
                      </div>
                    )
                  })}
              </div>
            </div>

            <button
              onClick={() => fetchEntityNeighborhood(selectedNode.label)}
              className="w-full py-1.5 bg-gray-900 border border-gray-800 rounded text-gray-400 hover:text-white hover:bg-gray-800 transition-colors"
            >
              Expand neighborhood
            </button>

            <button
              onClick={() => { setFindPathMode(true); setPathNodes([selectedNode, null]) }}
              className="w-full py-1.5 bg-blue-950/50 border border-blue-900 rounded text-blue-400 hover:bg-blue-950 transition-colors"
            >
              Find path from here
            </button>
          </div>
        </div>
      )}
    </div>
  )
}
