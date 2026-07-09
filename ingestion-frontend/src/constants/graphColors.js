// Shared color constants for knowledge graph visualization.

export const NODE_COLORS = {
  // Ingested entity types
  repo:            '#9C27B0',
  author:          '#2196F3',
  label:           '#F59E0B',
  issue:           '#22C55E',
  pr:              '#EF4444',
  file:            '#64748B',
  // Financial entity types
  Product:         '#06B6D4',
  Regulation:      '#F97316',
  Concept:         '#84CC16',
  CustomerSegment: '#EC4899',
  Institution:     '#92400E',
  Entity:          '#9E9E9E',
  default:         '#9E9E9E',
}

export const EDGE_COLORS = {
  RESOLVES:       '#22C55E',
  CREATED:        '#2196F3',
  TAGGED:         '#F59E0B',
  CHANGES:        '#EF4444',
  MENTIONED:      '#9C27B0',
  REGULATED_BY:   '#F97316',
  SUITABLE_FOR:   '#06B6D4',
  REQUIRES:       '#84CC16',
  ALTERNATIVE_TO: '#EC4899',
  ENFORCED_BY:    '#FF5722',
  APPLIES_TO:     '#03A9F4',
  IMPORTANT_FOR:  '#84CC16',
  PREFERS:        '#EC4899',
  default:        '#9E9E9E',
}

export const EDGE_WIDTHS = {
  RESOLVES:     3,
  CHANGES:      2,
  REGULATED_BY: 2,
  CREATED:      1.5,
  default:      1,
}

export const EDGE_DASHED = {
  TAGGED:    true,
  MENTIONED: true,
}
