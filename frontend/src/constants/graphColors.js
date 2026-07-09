// Shared color constants for knowledge graph visualization.
// Used by both KnowledgeGraphTab and MiniGraph components.

export const NODE_COLORS = {
  // Ingested entity types
  repo:            "#9C27B0",  // purple
  author:          "#2196F3",  // blue
  label:           "#FFC107",  // yellow
  issue:           "#4CAF50",  // green
  pr:              "#F44336",  // red
  file:            "#607D8B",  // grey-blue
  // Financial entity types
  Product:         "#00BCD4",  // cyan
  Regulation:      "#FF9800",  // orange
  Concept:         "#8BC34A",  // light green
  CustomerSegment: "#E91E63",  // pink
  Institution:     "#795548",  // brown
  Entity:          "#9E9E9E",  // grey (fallback for financial)
  default:         "#9E9E9E",  // grey fallback
}

export const EDGE_COLORS = {
  RESOLVES:       "#4CAF50",  // green — fix/resolution
  CREATED:        "#2196F3",  // blue — authorship
  TAGGED:         "#FFC107",  // yellow — labels
  CHANGES:        "#F44336",  // red — code changes
  MENTIONED:      "#9C27B0",  // purple
  REGULATED_BY:   "#FF9800",  // orange
  SUITABLE_FOR:   "#00BCD4",  // cyan
  REQUIRES:       "#8BC34A",  // light green
  ALTERNATIVE_TO: "#E91E63",  // pink
  ENFORCED_BY:    "#FF5722",  // deep orange
  APPLIES_TO:     "#03A9F4",  // light blue
  IMPORTANT_FOR:  "#8BC34A",  // light green
  PREFERS:        "#E91E63",  // pink
  default:        "#9E9E9E",  // grey fallback
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
