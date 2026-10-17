
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
let isLoading = false;

async function fetchAPI(endpoint, filters = false) {
    const url = new URL(`${API_BASE}/${endpoint}`, window.location.origin);

    if (filters) {
        const country = document.getElementById("country-filter").value;
        const sort = document.getElementById("sort-by").value;
        const startDate = document.getElementById("start-date").value;
        const endDate = document.getElementById("end-date").value;

        url.searchParams.set("country", country);
        url.searchParams.set("sort", sort);

        if (startDate) url.searchParams.set("start_date", startDate);
        if (endDate) url.searchParams.set("end_date", endDate);
    }

    const response = await fetch(url);

    if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.message || `Gagal mengambil ${endpoint}`);
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

function getSortLabel() {
    const select = document.getElementById("sort-by");
    return select.options[select.selectedIndex].text;
}

async function loadCountries() {
    const select = document.getElementById("country-filter");

    try {
        const countries = await fetchAPI("countries");
        const previousValue = select.value || "all";

        select.replaceChildren();

        const allOption = document.createElement("option");
        allOption.value = "all";
        allOption.textContent = "All Countries";
        select.appendChild(allOption);

        countries.forEach(country => {
            const option = document.createElement("option");
            option.value = country;
            option.textContent = country;
            select.appendChild(option);
        });

        select.value = countries.includes(previousValue)
            ? previousValue
            : "all";
    } catch (error) {
        console.error("Gagal memuat daftar negara:", error);
        setText("filter-message", "Daftar negara gagal dimuat.");
    }
}

function renderRevenueChart(rows) {
    // Grafik tren tetap kronologis agar perubahan waktu mudah dibaca.
    const sortedRows = [...rows].sort((a, b) =>
        a.month.localeCompare(b.month)
    );

    const config = {
        type: "line",
        data: {
            labels: sortedRows.map(row => row.month),
            datasets: [{
                label: "Revenue (£)",
                data: sortedRows.map(row => Number(row.revenue)),
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
                        label: context =>
                            currencyFormat.format(context.parsed.y)
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
    const sortBy = document.getElementById("sort-by").value;

    const metric = sortBy === "quantity" ? "quantity" : "revenue";
    const label = metric === "quantity" ? "Quantity Sold" : "Revenue (£)";

    const sortedRows = [...rows].sort((a, b) => {
        if (sortBy === "date") {
            return String(b.latest_date || "").localeCompare(
                String(a.latest_date || "")
            );
        }

        if (sortBy === "country") {
            return String(b.product).localeCompare(String(a.product));
        }

        return Number(b[metric]) - Number(a[metric]);
    });

    const config = {
        type: "bar",
        data: {
            labels: sortedRows.map(row => row.product),
            datasets: [{
                label,
                data: sortedRows.map(row => Number(row[metric])),
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
                        label: context => metric === "revenue"
                            ? currencyFormat.format(context.parsed.x)
                            : numberFormat.format(context.parsed.x)
                    }
                }
            },
            scales: {
                x: {
                    beginAtZero: true,
                    ticks: {
                        callback: value => metric === "revenue"
                            ? "£" + Number(value).toLocaleString("en-GB")
                            : Number(value).toLocaleString("en-GB")
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
        productsChart.options = config.options;
        productsChart.update();
    } else {
        productsChart = new Chart(
            document.getElementById("products-chart"),
            config
        );
    }
}

function renderCountriesChart(rows) {
    const sortBy = document.getElementById("sort-by").value;

    const sortedRows = [...rows].sort((a, b) => {
        if (sortBy === "country") {
            return String(b.country).localeCompare(String(a.country));
        }

        if (sortBy === "date") {
            return String(b.latest_date || "").localeCompare(
                String(a.latest_date || "")
            );
        }

        if (sortBy === "quantity") {
            return Number(b.quantity) - Number(a.quantity);
        }

        return Number(b.revenue) - Number(a.revenue);
    });

    const config = {
        type: "bar",
        data: {
            labels: sortedRows.map(row => row.country),
            datasets: [{
                label: sortBy === "quantity" ? "Quantity Sold" : "Revenue (£)",
                data: sortedRows.map(row =>
                    Number(sortBy === "quantity" ? row.quantity : row.revenue)
                ),
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
                        label: context => sortBy === "quantity"
                            ? numberFormat.format(context.parsed.y)
                            : currencyFormat.format(context.parsed.y)
                    }
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        callback: value => sortBy === "quantity"
                            ? Number(value).toLocaleString("en-GB")
                            : "£" + Number(value).toLocaleString("en-GB")
                    }
                }
            }
        }
    };

    if (countriesChart) {
        countriesChart.data = config.data;
        countriesChart.options = config.options;
        countriesChart.update();
    } else {
        countriesChart = new Chart(
            document.getElementById("countries-chart"),
            config
        );
    }
}

async function loadDashboard() {
    if (isLoading) return;

    isLoading = true;

    const refreshButton = document.getElementById("refresh-button");
    const applyButton = document.getElementById("apply-filters");

    refreshButton.disabled = true;
    refreshButton.textContent = "Loading...";

    if (applyButton) applyButton.disabled = true;

    try {
        const [summary, monthly, products, countries] = await Promise.all([
            fetchAPI("summary", true),
            fetchAPI("revenue-monthly", true),
            fetchAPI("top-products", true),
            fetchAPI("top-countries", true)
        ]);

        setText("total-revenue",
            currencyFormat.format(Number(summary.total_revenue)));
        setText("total-invoices",
            numberFormat.format(Number(summary.total_invoices)));
        setText("total-customers",
            numberFormat.format(Number(summary.total_customers)));
        setText("units-sold",
            numberFormat.format(Number(summary.units_sold)));

        renderRevenueChart(monthly);
        renderProductsChart(products);
        renderCountriesChart(countries);

        setText("last-updated",
            "Last updated: " + new Date().toLocaleTimeString("id-ID"));

        setText(
            "filter-message",
            `Filter aktif: ${document.getElementById("country-filter").selectedOptions[0].text} · Sort: ${getSortLabel()}`
        );
    } catch (error) {
        console.error("Dashboard error:", error);
        setText("last-updated", "Gagal memuat data.");
        setText("filter-message", error.message);
    } finally {
        refreshButton.disabled = false;
        refreshButton.textContent = "↻ Refresh Data";

        if (applyButton) applyButton.disabled = false;

        isLoading = false;
    }
}

function resetFilters() {
    document.getElementById("country-filter").value = "all";
    document.getElementById("sort-by").value = "revenue";
    document.getElementById("start-date").value = "";
    document.getElementById("end-date").value = "";
    loadDashboard();
}

document.getElementById("refresh-button")
    .addEventListener("click", loadDashboard);

document.getElementById("apply-filters")
    .addEventListener("click", () => {
        const startDate = document.getElementById("start-date").value;
        const endDate = document.getElementById("end-date").value;

        if (startDate && endDate && startDate > endDate) {
            setText("filter-message",
                "Tanggal awal tidak boleh melewati tanggal akhir.");
            return;
        }

        loadDashboard();
    });

document.getElementById("reset-filters")
    .addEventListener("click", resetFilters);

async function initializeDashboard() {
    await loadCountries();
    await loadDashboard();
}

initializeDashboard();
setInterval(loadDashboard, 30000);
