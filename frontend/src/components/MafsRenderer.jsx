import React, { useMemo, useState, Component } from 'react';
import { Mafs, Coordinates, Plot, Point } from 'mafs';
import * as math from 'mathjs';
import 'mafs/core.css';
import 'mafs/font.css';

class MafsErrorBoundary extends Component {
    constructor(props) {
        super(props);
        this.state = { hasError: false, errorMsg: '' };
    }
    static getDerivedStateFromError(error) {
        return { hasError: true, errorMsg: error.toString() };
    }
    render() {
        if (this.state.hasError) {
            return (
                <div style={{ padding: '1rem', border: '1px solid red', borderRadius: '8px', color: 'red', marginTop: '1rem' }}>
                    ⚠️ Failed to render math graph: {this.state.errorMsg}
                </div>
            );
        }
        return this.props.children;
    }
}

export default function MafsRenderer({ mafsData }) {
    if (!mafsData) return null;

    const { functions, points } = mafsData;
    const safeFunctions = Array.isArray(functions) ? functions : [];
    const safePoints = Array.isArray(points) ? points : [];

    // Default initial bounds, centered around origin
    const [bounds, setBounds] = useState(() => {
        const vw = mafsData.view_window || { x: [-10, 10], y: [-10, 10] };
        return vw;
    });

    const handleZoom = (factor) => {
        setBounds(prev => ({
            x: [prev.x[0] * factor, prev.x[1] * factor],
            y: [prev.y[0] * factor, prev.y[1] * factor]
        }));
    };

    const compiledFunctions = useMemo(() => {
        return safeFunctions.map((f) => {
            try {
                return { ...f, compiled: math.compile(f.expression) };
            } catch (e) {
                console.error("Failed to compile:", f.expression, e);
                return { ...f, compiled: null };
            }
        }).filter(f => f.compiled !== null);
    }, [safeFunctions]);

    return (
        <MafsErrorBoundary>
            <div style={{ position: 'relative', width: '100%', height: '400px', border: '1px solid #333', borderRadius: '8px', overflow: 'hidden', marginTop: '1rem', background: '#f5f5f5' }}>

                {/* On-screen Zoom Controls */}
                <div style={{ position: 'absolute', right: '10px', top: '10px', zIndex: 10, display: 'flex', flexDirection: 'column', gap: '5px' }}>
                    <button
                        onClick={() => handleZoom(0.8)}
                        style={{ padding: '6px 12px', background: 'white', border: '1px solid #ccc', borderRadius: '4px', cursor: 'pointer', fontWeight: 'bold' }}>
                        +
                    </button>
                    <button
                        onClick={() => handleZoom(1.25)}
                        style={{ padding: '6px 12px', background: 'white', border: '1px solid #ccc', borderRadius: '4px', cursor: 'pointer', fontWeight: 'bold' }}>
                        -
                    </button>
                </div>

                <Mafs
                    viewBox={bounds}
                    preserveAspectRatio={false}
                    pan={true}
                    zoom={true}
                >
                    <Coordinates.Cartesian xAxis={{ lines: 1, labels: (n) => (n % 2 === 0 ? n : "") }} yAxis={{ lines: 1, labels: (n) => (n % 2 === 0 ? n : "") }} />

                    {safePoints.map((pt, idx) => (
                        <Point key={`pt-${idx}`} x={pt.x || 0} y={pt.y || 0} color={pt.color || 'blue'} />
                    ))}

                    {compiledFunctions.map((fn, idx) => (
                        <Plot.OfX
                            key={`fn-${idx}`}
                            y={(x) => {
                                try {
                                    return fn.compiled.evaluate({ x: x, n: x, t: x, y: x });
                                } catch (e) {
                                    return 0; // Better safe fallback than NaN which might crash SVG renderer
                                }
                            }}
                            color={fn.color || 'red'}
                        />
                    ))}
                </Mafs>
            </div>
        </MafsErrorBoundary>
    );
}
