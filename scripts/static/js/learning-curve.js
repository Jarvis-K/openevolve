// learning-curve.js - Learning curve visualization functionality

export function renderLearningCurve(data) {
    const container = document.getElementById('learning-curve-chart');
    if (!container || !data.learning_curve || data.learning_curve.length === 0) {
        if (container) {
            container.innerHTML = '<p>No learning curve data available.</p>';
        }
        return;
    }

    // Clear existing content
    container.innerHTML = '';

    const margin = { top: 20, right: 30, bottom: 40, left: 60 };
    const width = Math.min(1000, container.offsetWidth) - margin.left - margin.right;
    const height = 400 - margin.top - margin.bottom;

    // Create SVG
    const svg = d3.select(container)
        .append('svg')
        .attr('width', width + margin.left + margin.right)
        .attr('height', height + margin.top + margin.bottom);

    const g = svg.append('g')
        .attr('transform', `translate(${margin.left},${margin.top})`);

    const learningData = data.learning_curve;

    // Scales
    const xScale = d3.scaleLinear()
        .domain(d3.extent(learningData, d => d.iteration))
        .range([0, width]);

    const yScale = d3.scaleLinear()
        .domain(d3.extent(learningData, d => d.score))
        .nice()
        .range([height, 0]);

    // Line generator
    const line = d3.line()
        .x(d => xScale(d.iteration))
        .y(d => yScale(d.score))
        .curve(d3.curveStepAfter); // Step curve to show that score is maintained

    // Add grid lines
    g.append('g')
        .attr('class', 'grid')
        .attr('transform', `translate(0,${height})`)
        .call(d3.axisBottom(xScale)
            .tickSize(-height)
            .tickFormat('')
        )
        .style('stroke-dasharray', '3,3')
        .style('opacity', 0.3);

    g.append('g')
        .attr('class', 'grid')
        .call(d3.axisLeft(yScale)
            .tickSize(-width)
            .tickFormat('')
        )
        .style('stroke-dasharray', '3,3')
        .style('opacity', 0.3);

    // Add the line
    g.append('path')
        .datum(learningData)
        .attr('fill', 'none')
        .attr('stroke', '#3b82f6')
        .attr('stroke-width', 2)
        .attr('d', line);

    // Add dots for each data point
    const dots = g.selectAll('.dot')
        .data(learningData)
        .enter().append('circle')
        .attr('class', 'dot')
        .attr('cx', d => xScale(d.iteration))
        .attr('cy', d => yScale(d.score))
        .attr('r', 4)
        .attr('fill', '#3b82f6')
        .style('cursor', 'pointer')
        .on('mouseover', function(event, d) {
            // Highlight the dot
            d3.select(this)
                .attr('r', 6)
                .attr('fill', '#1d4ed8');

            // Show tooltip
            showTooltip(event, d);
        })
        .on('mouseout', function(event, d) {
            // Reset dot
            d3.select(this)
                .attr('r', 4)
                .attr('fill', '#3b82f6');

            // Hide tooltip
            hideTooltip();
        })
        .on('click', function(event, d) {
            // Show code viewer
            showCodeViewer(d);
        });

    // Add axes
    g.append('g')
        .attr('transform', `translate(0,${height})`)
        .call(d3.axisBottom(xScale))
        .append('text')
        .attr('x', width / 2)
        .attr('y', 35)
        .attr('fill', 'currentColor')
        .style('text-anchor', 'middle')
        .style('font-size', '12px')
        .text('Iteration Step');

    g.append('g')
        .call(d3.axisLeft(yScale))
        .append('text')
        .attr('transform', 'rotate(-90)')
        .attr('y', -40)
        .attr('x', -height / 2)
        .attr('fill', 'currentColor')
        .style('text-anchor', 'middle')
        .style('font-size', '12px')
        .text('Best Score');

    // Add title
    g.append('text')
        .attr('x', width / 2)
        .attr('y', -5)
        .attr('text-anchor', 'middle')
        .style('font-size', '14px')
        .style('font-weight', 'bold')
        .attr('fill', 'currentColor')
        .text('Learning Curve - Best Score Over Time');

    // Add styles if not already added
    if (!document.getElementById('learning-curve-styles')) {
        const style = document.createElement('style');
        style.id = 'learning-curve-styles';
        style.textContent = `
            .learning-container {
                padding: 20px;
                max-width: 1200px;
                margin: 0 auto;
            }
            
            .learning-container h2 {
                color: var(--text-color);
                margin-bottom: 20px;
            }
            
            #learning-curve-chart {
                background: var(--toolbar-bg);
                border: 1px solid var(--border-color);
                border-radius: 8px;
                padding: 20px;
                margin-bottom: 20px;
            }
            
            .code-viewer {
                background: var(--toolbar-bg);
                border: 1px solid var(--border-color);
                border-radius: 8px;
                padding: 20px;
            }
            
            .code-viewer h3 {
                color: var(--text-color);
                margin-top: 0;
                margin-bottom: 15px;
                font-size: 16px;
            }
            
            .code-viewer pre {
                background: var(--main-bg);
                border: 1px solid var(--border-color);
                border-radius: 4px;
                padding: 15px;
                overflow-x: auto;
                font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
                font-size: 13px;
                line-height: 1.4;
                color: var(--text-color);
                margin: 0;
                max-height: 400px;
                overflow-y: auto;
            }
            
            .tooltip {
                position: absolute;
                background: var(--toolbar-bg);
                border: 1px solid var(--border-color);
                border-radius: 4px;
                padding: 8px;
                font-size: 12px;
                color: var(--text-color);
                pointer-events: none;
                z-index: 1000;
                box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
            }
            
            .grid line {
                stroke: var(--border-color);
            }
            
            .grid path {
                stroke-width: 0;
            }
        `;
        document.head.appendChild(style);
    }
}

function showTooltip(event, data) {
    const tooltip = d3.select('body').append('div')
        .attr('class', 'tooltip')
        .style('opacity', 0);

    tooltip.transition()
        .duration(200)
        .style('opacity', .9);

    tooltip.html(`
        <strong>Iteration:</strong> ${data.iteration}<br/>
        <strong>Score:</strong> ${data.score.toFixed(4)}<br/>
        <strong>Program:</strong> ${data.program_id.substring(0, 8)}...<br/>
        <em>Click to view code</em>
    `)
        .style('left', (event.pageX + 10) + 'px')
        .style('top', (event.pageY - 28) + 'px');
}

function hideTooltip() {
    d3.selectAll('.tooltip').remove();
}

function showCodeViewer(data) {
    const codeViewer = document.getElementById('code-viewer');
    const codeIteration = document.getElementById('code-iteration');
    const codeContent = document.getElementById('code-content');

    if (codeViewer && codeIteration && codeContent) {
        codeIteration.textContent = data.iteration;
        codeContent.textContent = data.code || 'No code available';
        codeViewer.style.display = 'block';

        // Scroll to code viewer
        codeViewer.scrollIntoView({ behavior: 'smooth' });
    }
}

// Make functions globally available for integration
window.renderLearningCurve = renderLearningCurve;