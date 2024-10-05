// chart-scripts.js

var finalValue = chartJSON.data[0].value;
var totalOutcomes = BigInt("72057594037927900");  // Use BigInt for precise large number handling

// Set initial value to 0
chartJSON.data[0].value = 0;
chartJSON.data[0].gauge.threshold.value = 0;

// Function to animate the outcomes count
function animateOutcomes(current) {
    if (current <= totalOutcomes) {
        document.getElementById('outcomes-count').textContent = current.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ",");
        setTimeout(() => animateOutcomes(current + totalOutcomes / 200n), 25);
    }
}

// Start the outcomes animation
animateOutcomes(BigInt(0));

var config = {
    responsive: true,
    displayModeBar: false,
    staticPlot: true
};

// Create the gauge chart
function createGaugeChart() {
    Plotly.newPlot('gauge-chart', chartJSON.data, {
        ...chartJSON.layout,
        datarevision: new Date().getTime(),
        gauge: {
            ...chartJSON.layout.gauge,
            axis: { visible: false },
        },
        number: { valueformat: '.2f', suffix: '%' },
        margin: { t: 0, b: 133, l: 0, r: 0 },
        paper_bgcolor: 'rgba(0,0,0,0)',
        plot_bgcolor: 'rgba(0,0,0,0)',
        height: 400
    }, config).then(function() {
        animateGauge(0);
    });
}

function animateGauge(value) {
    let increment = (finalValue - value > 1) ? 0.37 : 0.01;

    if (value <= finalValue) {
        Plotly.animate('gauge-chart', {
            data: [{
                value: value,
                gauge: {
                    threshold: { value: value },
                }
            }],
            traces: [0],
            layout: {}
        }, {
            transition: { duration: 0 },
            frame: { duration: 0, redraw: false }
        });

        setTimeout(function() { animateGauge(value + increment); }, 0);
    }
}

// Function to modify the line chart layout
function modifyLineChartLayout(layout) {
    if (layout.xaxis && layout.xaxis.tickvals && layout.xaxis.tickvals.length > 1) {
        layout.xaxis.tickmode = 'array';
        layout.xaxis.tickvals = [layout.xaxis.tickvals[0], layout.xaxis.tickvals[layout.xaxis.tickvals.length - 1]];

        // Convert dates to month abbreviations
        layout.xaxis.ticktext = layout.xaxis.ticktext.map(date => {
            const monthAbbreviations = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
            const dateObj = new Date(date);
            return monthAbbreviations[dateObj.getMonth()];
        });

        layout.xaxis.showticklabels = true;
        layout.xaxis.showline = true;
    }
    return layout;
}

// Create the line chart
function createLineChart() {
    // Modify the layout to show only start and end dates
    let modifiedLayout = modifyLineChartLayout(lineChartJSON.layout);

    Plotly.newPlot('line-chart', lineChartJSON.data, {
        ...modifiedLayout,
        paper_bgcolor: 'rgba(0,0,0,0)',
        plot_bgcolor: 'rgba(0,0,0,0)',
        height: 133,
        margin: { t: 0, b: 20, l: 40, r: 20 },
        xaxis: {
            ...modifiedLayout.xaxis,
            showgrid: false,
        },
        yaxis: {
            visible: false,
            showgrid: false,
        }
    }, config)
        .then(function() {
            console.log('Line chart created successfully');
        })
        .catch(function(err) {
            console.error('Error creating line chart:', err);
        });
}

function updateChart() {
    fetch('/update_chart', { method: 'POST' })
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success') {
                return fetch('/');
            }
        })
        .then(response => response.text())
        .then(html => {
            const parser = new DOMParser();
            const doc = parser.parseFromString(html, 'text/html');
            const newChartJSON = JSON.parse(doc.getElementById('chart-data').textContent);

            // Update the gauge chart
            Plotly.react('gauge-chart', newChartJSON.data, {
                ...newChartJSON.layout,
                paper_bgcolor: 'rgba(0,0,0,0)',
                plot_bgcolor: 'rgba(0,0,0,0)',
                height: 400,
                margin: { t: 0, b: 133, l: 0, r: 0 }
            }, config);

            // Update the line chart
            const newLineChartJSON = JSON.parse(doc.getElementById('line-chart-data').textContent);
            let modifiedLayout = modifyLineChartLayout(newLineChartJSON.layout);
            Plotly.react('line-chart', newLineChartJSON.data, {
                ...modifiedLayout,
                paper_bgcolor: 'rgba(0,0,0,0)',
                plot_bgcolor: 'rgba(0,0,0,0)',
                height: 133,
                margin: { t: 0, b: 20, l: 40, r: 20 },
                xaxis: {
                    ...modifiedLayout.xaxis,
                    showgrid: false,
                },
                yaxis: {
                    visible: false,
                    showgrid: false,
                }
            }, config);
        })
        .catch(error => console.error('Error updating charts:', error));
}

// Initialize charts
document.addEventListener('DOMContentLoaded', function() {
    if (typeof chartJSON !== 'undefined' && typeof lineChartJSON !== 'undefined') {
        createGaugeChart();
        createLineChart();
        // Update the chart every 10 minutes
        setInterval(updateChart, 600000);
    } else {
        console.error('Chart data is not available');
    }
});