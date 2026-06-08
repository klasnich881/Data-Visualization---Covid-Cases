const METRIC_COLORS = {
    new_cases: "#dc2626",
    new_vaccinations: "#2563eb",
    new_cases_roll3: "#0f766e"
};

async function updateChart() {
    const country = document.getElementById("countrySelect").value;
    const metric = document.getElementById("metricSelect").value;
    const heading = document.getElementById("chartHeading");

    const response = await fetch(`/data?country=${encodeURIComponent(country)}&metric=${encodeURIComponent(metric)}`);
    if (!response.ok) {
        throw new Error("Unable to load chart data.");
    }

    const payload = await response.json();
    const dates = payload.series.map((r) => r.date);
    const values = payload.series.map((r) => r[payload.metric]);
    const color = METRIC_COLORS[payload.metric] || "#1f2937";

    const trace = {
        x: dates,
        y: values,
        mode: "lines+markers",
        type: "scatter",
        name: payload.metric_label,
        line: { color, width: 3 },
        marker: { size: 6, color },
        hovertemplate: "<b>%{x}</b><br>" + payload.metric_label + ": %{y:.2f}<extra></extra>"
    };

    const layout = {
        title: `${payload.metric_label} Over Time - ${payload.country}`,
        xaxis: { title: "Month" },
        yaxis: { title: payload.metric_label },
        legend: { orientation: "h", y: 1.1, x: 0 },
        margin: { l: 62, r: 24, t: 68, b: 62 },
        paper_bgcolor: "#ffffff",
        plot_bgcolor: "#f8fafc"
    };

    Plotly.react("chart", [trace], layout, { responsive: true, displayModeBar: false });
    heading.textContent = `${payload.metric_label} Trend`;
}

function wireEvents() {
    document.getElementById("countrySelect").addEventListener("change", updateChart);
    document.getElementById("metricSelect").addEventListener("change", updateChart);
}

document.addEventListener("DOMContentLoaded", async () => {
    try {
        wireEvents();
        await updateChart();
    } catch (error) {
        document.getElementById("chart").innerHTML = "<p class='error'>Could not load chart data.</p>";
        console.error(error);
    }
});