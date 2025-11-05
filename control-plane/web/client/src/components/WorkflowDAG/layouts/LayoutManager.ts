import dagre from 'dagre';
import type { Node, Edge } from '@xyflow/react';
import { ELKLayoutEngine, type ELKLayoutType } from './ELKLayoutEngine';

export type DagreLayoutType = 'tree' | 'flow';
export type AllLayoutType = DagreLayoutType | ELKLayoutType;

export interface LayoutManagerConfig {
  smallGraphThreshold: number; // Threshold for switching to ELK layouts
  performanceThreshold: number; // Threshold for virtualized rendering
}

export class LayoutManager {
  private elkEngine: ELKLayoutEngine;
  private config: LayoutManagerConfig;

  constructor(config: LayoutManagerConfig = { smallGraphThreshold: 50, performanceThreshold: 300 }) {
    this.elkEngine = new ELKLayoutEngine();
    this.config = config;
  }

  /**
   * Determine if graph should use ELK layouts based on size
   */
  isLargeGraph(nodeCount: number): boolean {
    return nodeCount >= this.config.smallGraphThreshold;
  }

  /**
   * Get available layout types based on graph size
   */
  getAvailableLayouts(nodeCount: number): AllLayoutType[] {
    if (this.isLargeGraph(nodeCount)) {
      // Large graphs: All layouts available, but ELK layouts preferred
      return [...ELKLayoutEngine.getAvailableLayouts(), 'tree', 'flow'];
    } else {
      // Small graphs: All layouts available, but Dagre layouts preferred
      return ['tree', 'flow', ...ELKLayoutEngine.getAvailableLayouts()];
    }
  }

  /**
   * Get the default layout based on graph size
   */
  getDefaultLayout(nodeCount: number): AllLayoutType {
    if (this.isLargeGraph(nodeCount)) {
      // Large graphs: Default to box layout for performance
      return 'box';
    } else {
      // Small graphs: Default to tree layout
      return 'tree';
    }
  }

  /**
   * Check if a layout type is slow for large graphs
   */
  isSlowLayout(layoutType: AllLayoutType): boolean {
    if (layoutType === 'tree' || layoutType === 'flow') {
      return false; // Dagre layouts are generally fast
    }
    return ELKLayoutEngine.isSlowForLargeGraphs(layoutType as ELKLayoutType);
  }

  /**
   * Get layout description
   */
  getLayoutDescription(layoutType: AllLayoutType): string {
    switch (layoutType) {
      case 'tree':
        return 'Tree layout - Top to bottom hierarchy';
      case 'flow':
        return 'Flow layout - Left to right flow';
      default:
        return ELKLayoutEngine.getLayoutDescription(layoutType as ELKLayoutType);
    }
  }

  /**
   * Apply layout to nodes and edges
   */
  async applyLayout(
    nodes: Node[],
    edges: Edge[],
    layoutType: AllLayoutType,
    onProgress?: (progress: number) => void
  ): Promise<{ nodes: Node[]; edges: Edge[] }> {
    onProgress?.(0);

    try {
      if (layoutType === 'tree' || layoutType === 'flow') {
        // Use Dagre layout
        const result = this.applyDagreLayout(nodes, edges, layoutType);
        onProgress?.(100);
        return result;
      } else {
        // Use ELK layout
        onProgress?.(25);
        const result = await this.elkEngine.applyLayout(nodes, edges, layoutType as ELKLayoutType);
        onProgress?.(100);
        return result;
      }
    } catch (error) {
      console.error('Layout application failed:', error);
      onProgress?.(100);
      return { nodes, edges }; // Return original on failure
    }
  }

  /**
   * Apply Dagre layout (existing implementation)
   */
  private applyDagreLayout(nodes: Node[], edges: Edge[], layoutType: DagreLayoutType): { nodes: Node[]; edges: Edge[] } {
    const g = new dagre.graphlib.Graph();
    g.setDefaultEdgeLabel(() => ({}));
    
    // Calculate average node width for better spacing
    const nodeDimensions = nodes.map(node => this.calculateNodeDimensions(node.data));
    const avgWidth = nodeDimensions.reduce((sum, dim) => sum + dim.width, 0) / nodeDimensions.length;
    const maxWidth = Math.max(...nodeDimensions.map(dim => dim.width));
    
    // Configure layout with dynamic spacing based on actual node sizes
    const direction = layoutType === 'tree' ? 'TB' : 'LR';
    const spacing = direction === 'TB'
      ? { rankSep: 140, nodeSep: Math.max(100, avgWidth * 0.4) }  // Tree layout: top-to-bottom
      : { rankSep: Math.max(280, maxWidth * 1.2), nodeSep: 120 }; // Flow layout: left-to-right
    
    g.setGraph({
      rankdir: direction,
      ranksep: spacing.rankSep,
      nodesep: spacing.nodeSep,
      marginx: 60,
      marginy: 60,
    });

    // Add nodes to the graph with their actual dimensions
    nodes.forEach((node, index) => {
      const dimensions = nodeDimensions[index];
      g.setNode(node.id, {
        width: dimensions.width,
        height: dimensions.height,
      });
    });

    // Add edges to the graph
    edges.forEach((edge) => {
      g.setEdge(edge.source, edge.target);
    });

    // Calculate layout
    dagre.layout(g);

    // Apply positions to nodes using their actual dimensions
    const layoutedNodes = nodes.map((node, index) => {
      const nodeWithPosition = g.node(node.id);
      const dimensions = nodeDimensions[index];
      return {
        ...node,
        position: {
          x: nodeWithPosition.x - dimensions.width / 2,
          y: nodeWithPosition.y - dimensions.height / 2,
        },
      };
    });

    return { nodes: layoutedNodes, edges };
  }

  /**
   * Calculate node dimensions (same logic as in original component)
   */
  private calculateNodeDimensions(nodeData: any): { width: number; height: number } {
    const taskText = nodeData.task_name || nodeData.reasoner_id || '';
    const agentText = nodeData.agent_name || nodeData.agent_node_id || '';
    
    const minWidth = 200;
    const maxWidth = 360;
    const charWidth = 7.5;
    
    const humanizeText = (text: string): string => {
      return text
        .replace(/_/g, ' ')
        .replace(/-/g, ' ')
        .replace(/\b\w/g, l => l.toUpperCase())
        .replace(/\s+/g, ' ')
        .trim();
    };
    
    const taskHuman = humanizeText(taskText);
    const agentHuman = humanizeText(agentText);
    
    const taskWordsLength = taskHuman.split(' ').reduce((max, word) => Math.max(max, word.length), 0);
    const agentWordsLength = agentHuman.split(' ').reduce((max, word) => Math.max(max, word.length), 0);
    
    const longestWord = Math.max(taskWordsLength, agentWordsLength);
    const estimatedWidth = Math.max(
      longestWord * charWidth * 1.8,
      (taskHuman.length / 2.2) * charWidth,
      (agentHuman.length / 2.2) * charWidth
    ) + 80;
    
    const width = Math.min(maxWidth, Math.max(minWidth, estimatedWidth));
    const height = 100; // Fixed height as set in WorkflowNode
    
    return { width, height };
  }

  /**
   * Get configuration
   */
  getConfig(): LayoutManagerConfig {
    return { ...this.config };
  }

  /**
   * Update configuration
   */
  updateConfig(newConfig: Partial<LayoutManagerConfig>): void {
    this.config = { ...this.config, ...newConfig };
  }
}
