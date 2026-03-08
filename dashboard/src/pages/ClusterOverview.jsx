import React, { useEffect, useState } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend } from 'recharts';

const ClusterOverview = () => {
    const [data, setData] = useState([]);

    useEffect(() => {
        fetch('/api/telemetry/live/cluster_1')
            .then(response => response.json())
            .then(data => setData(data.gpus));
    }, []);

    return (
        <div>
            <h1>Cluster Overview</h1>
            <LineChart
                width={600}
                height={300}
                data={data}
                margin={{ top: 5, right: 30, left: 20, bottom: 5 }}
            >
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="id" />
                <YAxis />
                <Tooltip />
                <Legend />
                <Line type="monotone" dataKey="vram_used" stroke="#8884d8" activeDot={{ r: 8 }} />
                <Line type="monotone" dataKey="gpu_util" stroke="#82ca9d" />
            </LineChart>
        </div>
    );
};

export default ClusterOverview;