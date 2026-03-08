import React, { useEffect, useState } from 'react';

const Recommendations = () => {
    const [recommendations, setRecommendations] = useState([]);

    useEffect(() => {
        fetch('/api/models/model_sha256_1/recommendations')
            .then(response => response.json())
            .then(data => setRecommendations(data));
    }, []);

    return (
        <div>
            <h1>Pending Optimization Recommendations</h1>
            <ul>
                {recommendations.map((rec, index) => (
                    <li key={index}>{rec.family} {rec.size}B - {rec.quant} {rec.backend}</li>
                ))}
            </ul>
        </div>
    );
};

export default Recommendations;