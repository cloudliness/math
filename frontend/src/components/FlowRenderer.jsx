import React, { useCallback } from 'react';
import ReactFlow, {
    MiniMap,
    Controls,
    Background,
    useNodesState,
    useEdgesState,
    addEdge,
} from 'reactflow';
import 'reactflow/dist/style.css';

export default function FlowRenderer({ flowData }) {
    const [nodes, setNodes, onNodesChange] = useNodesState(flowData?.nodes || []);
    const [edges, setEdges, onEdgesChange] = useEdgesState(flowData?.edges || []);

    const onConnect = useCallback((params) => setEdges((eds) => addEdge(params, eds)), [setEdges]);

    if (!flowData || !flowData.nodes || flowData.nodes.length === 0) {
        return null;
    }

    return (
        <div style={{ width: '100%', height: '400px', border: '1px solid #333', borderRadius: '8px', overflow: 'hidden', marginTop: '1rem', background: '#1e1e1e' }}>
            <ReactFlow
                nodes={nodes}
                edges={edges}
                onNodesChange={onNodesChange}
                onEdgesChange={onEdgesChange}
                onConnect={onConnect}
                fitView
                attributionPosition="bottom-right"
            >
                <Controls />
                <MiniMap nodeStrokeWidth={3} zoomable pannable />
                <Background variant="dots" gap={12} size={1} color="#444" />
            </ReactFlow>
        </div>
    );
}
