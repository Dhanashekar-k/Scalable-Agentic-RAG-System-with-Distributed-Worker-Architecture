import { useEffect, useRef, useState } from 'react'
import * as d3 from 'd3'
import { NODE_COLORS, EDGE_COLORS, EDGE_WIDTHS, EDGE_DASHED } from '../constants/graphColors'

/**
 * MiniGraph — compact read-only D3 force graph for embedding in source cards.
 * Props: ingestionId (string)
 */
export default function MiniGraph({ ingestionId }) {
  const svgRef = useRef(null)
  const [graphData, setGraphData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    if (!ingestionId) return
    setLoading(true)
    setError(null)

    fetch(`/api/graph/source/${ingestionId}`)
      .then(r => r.json())
      .then(data => { setGraphData(data); setLoading(false) })
      .catch(() => { setError('Failed to load graph'); setLoading(false) })
  }, [ingestionId])

  useEffect(() => {
    if (!graphData?.nodes?.length || !svgRef.current) return

    const svg = d3.select(svgRef.current)
    svg.selectAll('*').remove()

    const width = svgRef.current.clientWidth || 400
    const height = svgRef.current.clientHeight || 256

    const zoom = d3.zoom()
      .scaleExtent([0.2, 3])
      .on('zoom', e => container.attr('transform', e.transform))
    svg.call(zoom)

    const container = svg.append('g')

    svg.append('defs').append('marker')
      .attr('id', `mini-arrow-${ingestionId}`)
      .attr('viewBox', '0 -5 10 10')
      .attr('refX', 16).attr('refY', 0)
      .attr('markerWidth', 5).attr('markerHeight', 5)
      .attr('orient', 'auto')
      .append('path').attr('fill', '#888').attr('d', 'M0,-5L10,0L0,5')

    const nodes = graphData.nodes.slice(0, 80)
    const nodeIds = new Set(nodes.map(n => n.id))
    const edges = graphData.edges
      .filter(e => nodeIds.has(e.source) && nodeIds.has(e.target))
      .slice(0, 120)

    const simulation = d3.forceSimulation(nodes)
      .force('link', d3.forceLink(edges).id(d => d.id).distance(50))
      .force('charge', d3.forceManyBody().strength(-120))
      .force('center', d3.forceCenter(width / 2, height / 2))
      .force('collision', d3.forceCollide(8))

    const link = container.append('g')
      .selectAll('line').data(edges).enter().append('line')
      .attr('stroke', d => EDGE_COLORS[d.relationship] || EDGE_COLORS.default)
      .attr('stroke-width', d => (EDGE_WIDTHS[d.relationship] || 1) * 0.7)
      .attr('stroke-dasharray', d => EDGE_DASHED[d.relationship] ? '4,2' : null)
      .attr('opacity', 0.6)
      .attr('marker-end', `url(#mini-arrow-${ingestionId})`)

    const node = container.append('g')
      .selectAll('circle').data(nodes).enter().append('circle')
      .attr('r', d => Math.min(12, Math.max(4, 4 + (d.connection_count || 0))))
      .attr('fill', d => NODE_COLORS[d.entity_type] || NODE_COLORS.default)
      .attr('stroke', '#fff')
      .attr('stroke-width', 1)
      .attr('cursor', 'default')

    // Tooltip
    const tooltip = d3.select('body').append('div')
      .style('position', 'absolute')
      .style('background', 'rgba(0,0,0,0.85)')
      .style('color', '#fff')
      .style('padding', '4px 8px')
      .style('border-radius', '4px')
      .style('font-size', '11px')
      .style('pointer-events', 'none')
      .style('opacity', 0)
      .style('z-index', 9999)

    node
      .on('mouseover', (event, d) => tooltip.style('opacity', 1).text(`${d.label} (${d.entity_type})`))
      .on('mousemove', event => tooltip.style('left', (event.pageX + 10) + 'px').style('top', (event.pageY - 20) + 'px'))
      .on('mouseout', () => tooltip.style('opacity', 0))

    simulation.on('tick', () => {
      link
        .attr('x1', d => d.source.x).attr('y1', d => d.source.y)
        .attr('x2', d => d.target.x).attr('y2', d => d.target.y)
      node.attr('cx', d => d.x).attr('cy', d => d.y)
    })

    return () => { simulation.stop(); tooltip.remove() }
  }, [graphData, ingestionId])

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full bg-claude-code-bg rounded-lg">
        <div className="flex items-center gap-2 text-claude-text-tertiary text-xs">
          <div className="w-3 h-3 border border-claude-border border-t-claude-accent rounded-full animate-spin" />
          Loading graph...
        </div>
      </div>
    )
  }

  if (error || !graphData?.nodes?.length) {
    return (
      <div className="flex items-center justify-center h-full bg-claude-code-bg rounded-lg">
        <p className="text-claude-text-tertiary text-xs">
          {error || 'No graph data available'}
        </p>
      </div>
    )
  }

  return (
    <div className="relative w-full h-full bg-claude-code-bg rounded-lg overflow-hidden">
      {/* Stats */}
      <div className="absolute top-2 left-2 z-10 flex gap-1.5">
        <span className="bg-black/40 text-claude-text-secondary text-xs px-2 py-0.5 rounded">
          {graphData.nodes.length} nodes
        </span>
        <span className="bg-black/40 text-claude-text-secondary text-xs px-2 py-0.5 rounded">
          {graphData.edges.length} edges
        </span>
      </div>
      {/* Type legend dots */}
      <div className="absolute bottom-2 right-2 z-10 flex gap-1.5 items-center">
        {Object.entries(graphData.stats?.entity_type_distribution || {}).slice(0, 5).map(([type]) => (
          <span
            key={type}
            title={type}
            className="w-2.5 h-2.5 rounded-full inline-block border border-white/20"
            style={{ backgroundColor: NODE_COLORS[type] || NODE_COLORS.default }}
          />
        ))}
      </div>
      <svg ref={svgRef} width="100%" height="100%" />
    </div>
  )
}
