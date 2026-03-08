import React, { useEffect, useState } from 'react';
import { PieChart, Pie, Cell, Tooltip, Legend } from 'recharts';

const VRAMBudget = () => {
    const [data, setData] = useState([]);

    useEffect(() => {
        fetch('/api/telemetry/live/cluster_1')
            .then(response => response.json())
            .then(data => {
                const totalVRAM = data.gpus.reduce((acc, gpu) => acc + gpu.vram, 0);
                const usedVRAM = data.gpus.reduce((acc, gpu) => acc + gpu.vram_used, 0);
                setData([
                    { name: 'Used VRAM', value: usedVRAM },
                    { name: 'Free VRAM', value: totalVRAM - usedVRAM }
                ]);
            });
    }, []);

    const COLORS = ['#0088FE', '#00C49F'];

    return (
        <div>
            <h1>VRAM Budget</h1>
            <PieChart width={400} height={400}>
                <Pie
                    data={data}
                    cx={200}
                    cy={200}
                    labelLine={false}
                    label={({ name, percent }) => `${name}: ${(percent * 100).toFixed(0)}%`}
                    outerRadius={80}
                    fill="#8884d8"
                    dataKey="value"
                >
                    {data.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                    ))}
                </Pie>
                <Tooltip />
                <Legend />
            </PieChart>
        </div>
    );
};

export default VRAMBudget;