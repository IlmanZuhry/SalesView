
const API_BASE = "/api";

const numberFormat = new Intl.NumberFormat("en-GB");
const currencyFormat = new Intl.NumberFormat("en-GB", {
    style: "currency",
    currency: "GBP",
    maximumFractionDigits: 2
});

let revenueChart = null;
let productsChart = null;
let countriesChart = null;

async function fetchAPI(endpoint) {
    const response = await fetch(`${API_BASE}/${endpoint}`);

    if (!response.ok) {
        throw new Error(`Gagal mengambil data: ${endpoint}`);
    }

    const result = await response.json();

    if (result.status !== "success") {
        throw new Error(result.message || "API mengembalikan error.");
    }

    return result.data;
}

function setText(id, value) {
    document.getElementById(id).textContent = value;
}

function renderRevenueChart(rows) {
    const labels = rows.map(row => row.month);
    const values = rows.map(row => Number(row.revenue));

    const config = {
        type: "line",
        data: {
            labels,
            datasets: [{
                label: "Revenue (£)",
                data: values,
                borderColor: "#6655e8",
                backgroundColor: "rgba(102, 85, 232, 0.12)",
                fill: true,
                tension: 0.35,
                pointRadius: 2,
                pointHoverRadius: 5
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            interaction: { intersect: false, mode: "index" },
            plugins: {
                legend: { display: false },
                tooltip: {
                    callbacks: {
                        label: context => currencyFormat.format(context.parsed.y)
                    }
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        callback: value =>
                            "£" + Number(value).toLocaleString("en-GB")
                    }
                }
            }
        }
    };

    if (revenueChart) {
        revenueChart.data = config.data;
        revenueChart.update();
    } else {
        revenueChart = new Chart(
            document.getElementById("revenue-chart"),
            config
        );
    }
}

function renderProductsChart(rows) {
    const labels = rows.map(row => row.product);
    const values = rows.map(row => Number(row.revenue));

    const config = {
        type: "bar",
        data: {
            labels,
            datasets: [{
                label: "Revenue (£)",
                data: values,
                backgroundColor: "#8174f5",
                borderRadius: 5
            }]
        },
        options: {
            indexAxis: "y",
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false },
                tooltip: {
                    callbacks: {
                        label: context => currencyFormat.format(context.parsed.x)
                    }
                }
            },
            scales: {
                x: {
                    beginAtZero: true,
                    ticks: {
                        callback: value =>
                            "£" + Number(value).toLocaleString("en-GB")
                    }
                },
                y: {
                    ticks: {
                        autoSkip: false,
                        font: { size: 10 }
                    }
                }
            }
        }
    };

    if (productsChart) {
        productsChart.data = config.data;
        productsChart.update();
    } else {
        productsChart = new Chart(
            document.getElementById("products-chart"),
            config
        );
    }
}

function renderCountriesChart(rows) {
    const labels = rows.map(row => row.country);
    const values = rows.map(row => Number(row.revenue));

    const config = {
        type: "bar",
        data: {
            labels,
            datasets: [{
                label: "Revenue (£)",
                data: values,
                backgroundColor: "#36b89a",
                borderRadius: 5
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false },
                tooltip: {
                    callbacks: {
                        label: context => currencyFormat.format(context.parsed.y)
                    }
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        callback: value =>
                            "£" + Number(value).toLocaleString("en-GB")
                    }
                }
            }
        }
    };

    if (countriesChart) {
        countriesChart.data = config.data;
        countriesChart.update();
    } else {
        countriesChart = new Chart(
            document.getElementById("countries-chart"),
            config
        );
    }
}

async function loadDashboard() {
    const refreshButton = document.getElementById("refresh-button");
    refreshButton.disabled = true;
    refreshButton.textContent = "Loading...";

    try {
        const [summary, monthly, products, countries] = await Promise.all([
            fetchAPI("summary"),
            fetchAPI("revenue-monthly"),
            fetchAPI("top-products"),
            fetchAPI("top-countries")
        ]);

        setText("total-revenue", currencyFormat.format(
            Number(summary.total_revenue)
        ));
        setText("total-invoices", numberFormat.format(
            Number(summary.total_invoices)
        ));
        setText("total-customers", numberFormat.format(
            Number(summary.total_customers)
        ));
        setText("units-sold", numberFormat.format(
            Number(summary.units_sold)
        ));

        renderRevenueChart(monthly);
        renderProductsChart(products);
        renderCountriesChart(countries);

        setText(
            "last-updated",
            "Last updated: " + new Date().toLocaleTimeString("id-ID")
        );
    } catch (error) {
        console.error("Dashboard error:", error);
        setText("last-updated", "Gagal memuat data. Periksa koneksi API.");
    } finally {
        refreshButton.disabled = false;
        refreshButton.textContent = "↻ Refresh Data";
    }
}

document.getElementById("refresh-button")
    .addEventListener("click", loadDashboard);

loadDashboard();
setInterval(loadDashboard, 30000);
