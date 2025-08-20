// islands.js - Island visualization functionality

export function renderIslandsView(data) {
    const container = document.getElementById('islands-grid');
    if (!container || !data.islands_stats) return;

    container.innerHTML = '';

    // Create island cards
    data.islands_stats.forEach(island => {
        const card = document.createElement('div');
        card.className = `island-card ${island.is_current ? 'current' : ''}`;
        
        const statusColor = island.population_size > 0 ? '#22c55e' : '#ef4444';
        
        card.innerHTML = `
            <div class="island-header">
                <h3>Island ${island.island_id}</h3>
                <div class="island-status" style="color: ${statusColor}">●</div>
                ${island.is_current ? '<span class="current-badge">Current</span>' : ''}
            </div>
            <div class="island-stats">
                <div class="stat">
                    <label>Population</label>
                    <value>${island.population_size}</value>
                </div>
                <div class="stat">
                    <label>Generation</label>
                    <value>${island.generation}</value>
                </div>
                <div class="stat">
                    <label>Best Score</label>
                    <value>${island.best_score.toFixed(4)}</value>
                </div>
                <div class="stat">
                    <label>Avg Score</label>
                    <value>${island.average_score.toFixed(4)}</value>
                </div>
            </div>
            ${island.best_program_id ? `
                <div class="island-best">
                    <label>Best Program:</label>
                    <button class="program-link" onclick="showProgramInSidebar('${island.best_program_id}')">${island.best_program_id.substring(0, 8)}...</button>
                </div>
            ` : ''}
        `;
        
        container.appendChild(card);
    });

    // Add CSS styles if not already added
    if (!document.getElementById('islands-styles')) {
        const style = document.createElement('style');
        style.id = 'islands-styles';
        style.textContent = `
            .islands-container {
                padding: 20px;
                max-width: 1200px;
                margin: 0 auto;
            }
            
            .islands-grid {
                display: grid;
                grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
                gap: 20px;
                margin-top: 20px;
            }
            
            .island-card {
                background: var(--toolbar-bg);
                border: 2px solid var(--border-color);
                border-radius: 8px;
                padding: 16px;
                transition: all 0.3s ease;
            }
            
            .island-card.current {
                border-color: #3b82f6;
                box-shadow: 0 4px 12px rgba(59, 130, 246, 0.15);
            }
            
            .island-card:hover {
                transform: translateY(-2px);
                box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
            }
            
            .island-header {
                display: flex;
                align-items: center;
                justify-content: space-between;
                margin-bottom: 12px;
            }
            
            .island-header h3 {
                margin: 0;
                color: var(--text-color);
                font-size: 16px;
            }
            
            .island-status {
                font-size: 14px;
            }
            
            .current-badge {
                background: #3b82f6;
                color: white;
                padding: 2px 8px;
                border-radius: 12px;
                font-size: 10px;
                font-weight: 600;
                text-transform: uppercase;
            }
            
            .island-stats {
                display: grid;
                grid-template-columns: 1fr 1fr;
                gap: 8px;
                margin-bottom: 12px;
            }
            
            .stat {
                display: flex;
                flex-direction: column;
            }
            
            .stat label {
                font-size: 11px;
                color: var(--muted-text);
                text-transform: uppercase;
                font-weight: 500;
                margin-bottom: 2px;
            }
            
            .stat value {
                font-size: 14px;
                font-weight: 600;
                color: var(--text-color);
            }
            
            .island-best {
                border-top: 1px solid var(--border-color);
                padding-top: 8px;
                font-size: 12px;
            }
            
            .island-best label {
                color: var(--muted-text);
                font-weight: 500;
                margin-right: 8px;
            }
            
            .program-link {
                background: #f3f4f6;
                border: 1px solid #d1d5db;
                border-radius: 4px;
                padding: 2px 6px;
                font-size: 11px;
                cursor: pointer;
                color: #374151;
                font-family: monospace;
            }
            
            .program-link:hover {
                background: #e5e7eb;
            }
            
            [data-theme="dark"] .program-link {
                background: #374151;
                border-color: #4b5563;
                color: #d1d5db;
            }
            
            [data-theme="dark"] .program-link:hover {
                background: #4b5563;
            }
        `;
        document.head.appendChild(style);
    }
}

// Function to show program in sidebar (will be called from onclick)
window.showProgramInSidebar = function(programId) {
    // This will integrate with existing sidebar functionality
    if (window.showSidebarContent) {
        // Find the program data
        const allNodes = window.allNodeData || [];
        const program = allNodes.find(node => node.id === programId);
        if (program) {
            window.showSidebarContent(program);
        }
    }
};