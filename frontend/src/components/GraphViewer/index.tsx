import ReactFlow, { Background, Controls, type Node, type Edge } from "reactflow";
import "reactflow/dist/style.css";
import type { AgentDetail } from "../../types";

interface Props {
  agent: AgentDetail;
}

export default function GraphViewer({ agent }: Props) {
  const supervisorNode: Node = {
    id: "supervisor",
    type: "default",
    position: { x: 300, y: 40 },
    data: { label: agent.name || "Supervisor" },
    style: {
      background: "#0369a1",
      color: "#fff",
      border: "1px solid #0284c7",
      borderRadius: 8,
      padding: "8px 16px",
      fontWeight: 600,
      fontSize: 13,
    },
  };

  const subagentNodes: Node[] = agent.subagents.map((sa, i) => {
    const total = agent.subagents.length;
    const angle = (i / Math.max(total, 1)) * 2 * Math.PI - Math.PI / 2;
    const radius = 200;
    const cx = 300 + radius * Math.cos(angle);
    const cy = 260 + radius * Math.sin(angle);
    return {
      id: sa.id,
      type: "default",
      position: { x: cx - 60, y: cy - 20 },
      data: { label: sa.name },
      style: {
        background: "#1f2937",
        color: "#e5e7eb",
        border: "1px solid #374151",
        borderRadius: 8,
        padding: "6px 14px",
        fontSize: 12,
      },
    };
  });

  const generalPurposeNode: Node | null =
    agent.subagents.length === 0
      ? {
          id: "general-purpose",
          type: "default",
          position: { x: 200, y: 260 },
          data: { label: "general-purpose (default)" },
          style: {
            background: "#111827",
            color: "#6b7280",
            border: "1px dashed #374151",
            borderRadius: 8,
            padding: "6px 14px",
            fontSize: 12,
            fontStyle: "italic",
          },
        }
      : null;

  const edges: Edge[] = [
    ...agent.subagents.map((sa) => ({
      id: `supervisor->${sa.id}`,
      source: "supervisor",
      target: sa.id,
      label: "task",
      style: { stroke: "#0284c7" },
      labelStyle: { fill: "#9ca3af", fontSize: 10 },
    })),
    ...(generalPurposeNode
      ? [
          {
            id: "supervisor->general-purpose",
            source: "supervisor",
            target: "general-purpose",
            label: "task",
            style: { stroke: "#374151", strokeDasharray: "4" },
            labelStyle: { fill: "#6b7280", fontSize: 10 },
          },
        ]
      : []),
  ];

  const nodes: Node[] = [
    supervisorNode,
    ...subagentNodes,
    ...(generalPurposeNode ? [generalPurposeNode] : []),
  ];

  return (
    <div style={{ height: 480 }} className="rounded-xl border border-gray-800 bg-gray-950">
      <ReactFlow nodes={nodes} edges={edges} fitView>
        <Background color="#1f2937" gap={20} />
        <Controls className="[&>button]:bg-gray-800 [&>button]:border-gray-700 [&>button]:text-gray-300" />
      </ReactFlow>
    </div>
  );
}
