import React, { useState } from 'react';

const Settings = () => {
    const [clusterConfig, setClusterConfig] = useState({});
    const [learningOptIn, setLearningOptIn] = useState(false);

    const handleClusterConfigChange = (e) => {
        setClusterConfig({ ...clusterConfig, [e.target.name]: e.target.value });
    };

    const handleLearningOptInChange = (e) => {
        setLearningOptIn(e.target.checked);
    };

    const handleSubmit = (e) => {
        e.preventDefault();
        console.log('Cluster Config:', clusterConfig);
        console.log('Learning Opt-In:', learningOptIn);
    };

    return (
        <div>
            <h1>Cluster Config</h1>
            <form onSubmit={handleSubmit}>
                <label>
                    GPU Count:
                    <input type="number" name="gpuCount" onChange={handleClusterConfigChange} />
                </label>
                <br />
                <label>
                    Model Path:
                    <input type="text" name="modelPath" onChange={handleClusterConfigChange} />
                </label>
                <br />
                <label>
                    <input type="checkbox" checked={learningOptIn} onChange={handleLearningOptInChange} />
                    Opt-in to Cross-Customer Learning
                </label>
                <br />
                <button type="submit">Save</button>
            </form>
        </div>
    );
};

export default Settings;