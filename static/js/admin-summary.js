(function () {
    const payloadElement = document.getElementById("adminSummaryInitialData");
    const initialPayload = payloadElement ? JSON.parse(payloadElement.textContent || "{}") : {};

    const rangePreset = document.getElementById("rangePreset");
const dateRangePicker = document.getElementById("dateRangePicker");

    const locationFilterWrap = document.getElementById("locationFilter");
    const zoneFilterWrap = document.getElementById("zoneFilter");
    const lotTypeFilterWrap = document.getElementById("lotTypeFilter");

    const locationFilterTrigger = document.getElementById("locationFilterTrigger");
    const zoneFilterTrigger = document.getElementById("zoneFilterTrigger");
    const lotTypeFilterTrigger = document.getElementById("lotTypeFilterTrigger");

    const locationFilterOptions = document.getElementById("locationFilterOptions");
    const zoneFilterOptions = document.getElementById("zoneFilterOptions");
    const lotTypeFilterOptions = document.getElementById("lotTypeFilterOptions");
    const locationFilterSearch = document.getElementById("locationFilterSearch");

    const resetFiltersButton = document.getElementById("resetFilters");
    const applyFiltersButton = document.getElementById("applyFilters");
    const sendReminderForm = document.getElementById("sendReminderForm");

    const tableSearch = document.getElementById("tableSearch");
    const tableCommonFilter = document.getElementById("tableCommonFilter");

    const exportPdfButton = document.getElementById("exportPdfBtn");
    const exportCsvButton = document.getElementById("exportCsvBtn");
    const emailReportForm = document.getElementById("emailReportForm");

    const tableBody = document.getElementById("adminSummaryTableBody");
    const tableCountLabel = document.getElementById("tableCountLabel");
    const tableRangeLabel = document.getElementById("tableRangeLabel");
    const prevPageButton = document.getElementById("prevPage");
    const nextPageButton = document.getElementById("nextPage");
    const pageSizeSelect = document.getElementById("pageSize");

    const kpiRevenue = document.getElementById("kpiRevenue");
    const kpiBookings = document.getElementById("kpiBookings");
    const kpiUsers = document.getElementById("kpiUsers");
    const kpiLocation = document.getElementById("kpiLocation");
    const trendRevenue = document.getElementById("trendRevenue");
    const trendBookings = document.getElementById("trendBookings");
    const trendUsers = document.getElementById("trendUsers");
    const trendLocation = document.getElementById("trendLocation");

    const insightRevenue = document.getElementById("insightRevenue");
    const insightLocation = document.getElementById("insightLocation");
    const insightPeakTime = document.getElementById("insightPeakTime");
    const insightLowOccupancy = document.getElementById("insightLowOccupancy");

    let payload = initialPayload;
    let sortState = { key: "in_time", direction: "desc" };
    let page = 1;
    let pageSize = Number(pageSizeSelect ? pageSizeSelect.value : 10) || 10;
    let charts = {};
    let picker = null;

    const filterState = {
        startDate: "",
        endDate: "",
        locations: [],
        zones: [],
        lot_types: [],
    };

    const optionMap = {
        locations: [],
        zones: [],
        lot_types: [],
    };

    const labelMap = {
        locations: "Locations",
        zones: "Zones",
        lot_types: "Types",
    };

    const dropdownWraps = [locationFilterWrap, zoneFilterWrap, lotTypeFilterWrap].filter(Boolean);

    const formatCurrency = (value) => `Rs ${Number(value || 0).toFixed(2)}`;

    const trendMarkup = (value) => {
        const n = Number(value || 0);
        if (!n) return { text: "0%", className: "kpi-trend" };
        const up = n > 0;
        return { text: `${up ? "?" : "?"} ${Math.abs(n).toFixed(1)}%`, className: `kpi-trend ${up ? "up" : "down"}` };
    };

    const parseDate = (value) => {
        if (!value || value === "In Progress") return null;
        const parsed = new Date(String(value).replace(" ", "T"));
        return Number.isNaN(parsed.getTime()) ? null : parsed;
    };

    const formatDateDisplay = (iso) => {
        if (!iso) return "";
        const [y, m, d] = String(iso).split("-");
        return y && m && d ? `${d}-${m}-${y}` : "";
    };

    const selectedLabel = (key, fallback) => {
        const selected = filterState[key] || [];
        if (!selected.length) return fallback;
        if (selected.length === 1) return selected[0];
        return `${selected.length} ${labelMap[key]} selected`;
    };

    const setTriggerLabel = (trigger, text) => {
        const valueNode = trigger ? trigger.querySelector(".value") : null;
        if (valueNode) valueNode.textContent = text;
    };

    const updateTriggerLabels = () => {
        setTriggerLabel(locationFilterTrigger, selectedLabel("locations", "All Locations"));
        setTriggerLabel(zoneFilterTrigger, selectedLabel("zones", "All Zones"));
        setTriggerLabel(lotTypeFilterTrigger, selectedLabel("lot_types", "All Types"));
    };

    const currentFilters = () => ({
        range: rangePreset ? rangePreset.value : "30d",
        start_date: filterState.startDate,
        end_date: filterState.endDate,
        locations: filterState.locations,
        zones: filterState.zones,
        lot_types: filterState.lot_types,
    });

    const toQueryString = (filters) => {
        const params = new URLSearchParams();
        params.set("range", filters.range || "30d");
        if (filters.start_date) params.set("start_date", filters.start_date);
        if (filters.end_date) params.set("end_date", filters.end_date);
        if (filters.locations.length) params.set("locations", filters.locations.join(","));
        if (filters.zones.length) params.set("zones", filters.zones.join(","));
        if (filters.lot_types.length) params.set("lot_types", filters.lot_types.join(","));
        return params.toString();
    };

    const syncExportLinks = () => {
        const filters = currentFilters();
        const query = toQueryString(filters);
        if (exportPdfButton) exportPdfButton.href = `/admin/summary/export-pdf?${query}`;
        if (exportCsvButton) exportCsvButton.href = `/admin/summary/export-csv?${query}`;

        if (emailReportForm) {
            const map = {
                range: filters.range,
                start_date: filters.start_date,
                end_date: filters.end_date,
                locations: filters.locations.join(","),
                zones: filters.zones.join(","),
                lot_types: filters.lot_types.join(","),
            };
            Object.keys(map).forEach((key) => {
                const input = emailReportForm.querySelector(`input[name="${key}"]`);
                if (input) input.value = map[key];
            });
        }
    };

    const statusBadge = (status) => {
        const key = String(status || "").toLowerCase();
        if (key === "completed") return `<span class="status-badge status-completed">${status}</span>`;
        if (key === "cancelled") return `<span class="status-badge status-cancelled">${status}</span>`;
        return `<span class="status-badge status-active">${status}</span>`;
    };

    const paymentBadge = (payment) => {
        const key = String(payment || "").toLowerCase();
        if (key === "paid" || key === "settled") return `<span class="payment-badge payment-${key}">${payment}</span>`;
        if (key === "failed") return `<span class="payment-badge payment-failed">${payment}</span>`;
        return `<span class="payment-badge payment-pending">${payment || "Pending"}</span>`;
    };

    const renderDropdownOptions = (container, key, searchTerm) => {
        if (!container) return;
        const selected = new Set(filterState[key] || []);
        const keyword = String(searchTerm || "").trim().toLowerCase();
        const list = (optionMap[key] || []).filter((v) => String(v).toLowerCase().includes(keyword));

        if (!list.length) {
            container.innerHTML = '<div class="small text-muted px-2 py-2">No options found</div>';
            return;
        }

        container.innerHTML = list.map((value) => {
            const active = selected.has(value);
            return `<button type="button" class="filter-option ${active ? "active" : ""}" data-key="${key}" data-value="${value}">
                        <span class="tick">${active ? "<i class='bi bi-check-lg'></i>" : ""}</span>
                        <span>${value}</span>
                    </button>`;
        }).join("");
    };

    const renderFilterDropdowns = () => {
        renderDropdownOptions(locationFilterOptions, "locations", locationFilterSearch ? locationFilterSearch.value : "");
        renderDropdownOptions(zoneFilterOptions, "zones", "");
        renderDropdownOptions(lotTypeFilterOptions, "lot_types", "");
        updateTriggerLabels();
    };

    const filteredRows = () => {
        const rows = payload.bookings || [];
        const keyword = String(tableSearch ? tableSearch.value : "").trim().toLowerCase();
        const common = String(tableCommonFilter ? tableCommonFilter.value : "all").toLowerCase();

        return rows.filter((row) => {
            if (keyword) {
                const full = [row.booking_id, row.user, row.location, row.zone, row.in_time, row.out_time, row.duration, row.status, row.revenue, row.payment_status].join(" ").toLowerCase();
                if (!full.includes(keyword)) return false;
            }

            if (common !== "all") {
                if (common.startsWith("status:")) {
                    const expected = common.split(":")[1] || "";
                    if (String(row.status || "").toLowerCase() !== expected) return false;
                }
                if (common.startsWith("payment:")) {
                    const expected = common.split(":")[1] || "";
                    if (String(row.payment_status || "").toLowerCase() !== expected) return false;
                }
            }
            return true;
        });
    };

    const sortRows = (rows) => {
        const key = sortState.key;
        const dir = sortState.direction === "asc" ? 1 : -1;
        return rows.slice().sort((a, b) => {
            const av = a[key];
            const bv = b[key];
            let cmp = 0;
            if (["booking_id", "revenue", "duration_minutes"].includes(key)) cmp = Number(av || 0) - Number(bv || 0);
            else if (["in_time", "out_time"].includes(key)) cmp = (parseDate(av)?.getTime() || 0) - (parseDate(bv)?.getTime() || 0);
            else cmp = String(av || "").localeCompare(String(bv || ""));
            return cmp * dir;
        });
    };

    const pagedRows = (rows) => {
        const total = rows.length;
        const pages = Math.max(Math.ceil(total / pageSize), 1);
        if (page > pages) page = pages;
        const startIndex = (page - 1) * pageSize;
        const endIndex = Math.min(startIndex + pageSize, total);
        return { pageRows: rows.slice(startIndex, endIndex), total, pages, startIndex, endIndex };
    };

    const renderTable = () => {
        if (!tableBody) return;
        const rows = sortRows(filteredRows());
        const info = pagedRows(rows);

        if (!info.pageRows.length) {
            tableBody.innerHTML = '<tr><td colspan="9" class="text-center py-4 text-muted">No bookings match the current filters.</td></tr>';
        } else {
            tableBody.innerHTML = info.pageRows.map((row) => `<tr>
                <td>${row.booking_id}</td>
                <td>${row.user || "-"}</td>
                <td>${row.location || "-"}</td>
                <td>${row.in_time || "-"}</td>
                <td>${row.out_time || "-"}</td>
                <td>${row.duration || "-"}</td>
                <td>${statusBadge(row.status)}</td>
                <td>${formatCurrency(row.revenue)}</td>
                <td>${paymentBadge(row.payment_status)}</td>
            </tr>`).join("");
        }

        if (tableCountLabel) tableCountLabel.textContent = `${info.total} booking${info.total === 1 ? "" : "s"}`;
        if (tableRangeLabel) tableRangeLabel.textContent = `Showing ${info.total ? info.startIndex + 1 : 0}-${info.endIndex} of ${info.total}`;
        if (prevPageButton) prevPageButton.disabled = page <= 1;
        if (nextPageButton) nextPageButton.disabled = page >= info.pages;
    };

    const destroyChart = (key) => {
        if (charts[key]) {
            charts[key].destroy();
            charts[key] = null;
        }
    };

    const getGradient = (ctx, start, end) => {
        const grad = ctx.createLinearGradient(0, 0, 0, 260);
        grad.addColorStop(0, start);
        grad.addColorStop(1, end);
        return grad;
    };

    const renderCharts = () => {
        if (typeof Chart === "undefined") return;

        const summaryCharts = payload.charts || {};
        const revenueCtx = document.getElementById("revenueTrendChart");
        const peakCtx = document.getElementById("peakHoursChart");
        const topLocationCtx = document.getElementById("topLocationsChart");
        const statusCtx = document.getElementById("statusDonutChart");
        const occupancyCtx = document.getElementById("occupancyChart");
        const revenueByLocCtx = document.getElementById("revenueByLocationChart");

        ["revenue", "peak", "topLocations", "status", "occupancy", "revenueByLocation"].forEach(destroyChart);

        if (revenueCtx) {
            const ctx = revenueCtx.getContext("2d");
            charts.revenue = new Chart(revenueCtx, {
                type: "line",
                data: {
                    labels: (summaryCharts.revenue_trend || {}).labels || ["No Data"],
                    datasets: [{
                        label: "Revenue",
                        data: (summaryCharts.revenue_trend || {}).values || [0],
                        borderColor: "#7b59ff",
                        backgroundColor: getGradient(ctx, "rgba(123, 89, 255, 0.35)", "rgba(123, 89, 255, 0.02)"),
                        tension: 0.35,
                        fill: true,
                        pointRadius: 2.8,
                    }],
                },
                options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { display: false }, tooltip: { mode: "index", intersect: false } } },
            });
        }

        if (peakCtx) {
            const peakData = summaryCharts.peak_booking_hours || {};
            const values = peakData.values || Array(24).fill(0);
            const colors = values.map((_, idx) => (idx === peakData.peak_hour ? "#aa5fff" : "rgba(123, 89, 255, 0.55)"));
            charts.peak = new Chart(peakCtx, {
                type: "line",
                data: {
                    labels: peakData.labels || Array.from({ length: 24 }, (_, i) => String(i)),
                    datasets: [{ label: "Bookings", data: values, borderColor: "#7b59ff", backgroundColor: "rgba(123, 89, 255, 0.14)", pointBackgroundColor: colors, pointRadius: 3, tension: 0.3, fill: true }],
                },
                options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { display: false }, tooltip: { mode: "index", intersect: false } } },
            });
        }

        if (topLocationCtx) {
            const rows = summaryCharts.top_locations || [];
            charts.topLocations = new Chart(topLocationCtx, {
                type: "bar",
                data: { labels: rows.length ? rows.map((r) => r.location) : ["No Data"], datasets: [{ data: rows.length ? rows.map((r) => r.bookings) : [0], borderRadius: 8, backgroundColor: ["#6f4bff", "#7c57ff", "#8b67ff", "#9a77ff", "#aa87ff", "#b896ff", "#c6a4ff", "#d3b3ff"] }] },
                options: { indexAxis: "y", responsive: true, maintainAspectRatio: false, plugins: { legend: { display: false } } },
            });
        }

        if (statusCtx) {
            const dist = summaryCharts.status_distribution || { Completed: 0, Cancelled: 0, Active: 0 };
            charts.status = new Chart(statusCtx, {
                type: "doughnut",
                data: { labels: ["Completed", "Cancelled", "Active"], datasets: [{ data: [dist.Completed || 0, dist.Cancelled || 0, dist.Active || 0], backgroundColor: ["#6f4bff", "#bf8bff", "#35a3ff"], borderWidth: 2, borderColor: "#ffffff" }] },
                options: { cutout: "66%", responsive: true, maintainAspectRatio: false, plugins: { legend: { position: "bottom" } } },
            });
        }

        if (occupancyCtx) {
            const rows = summaryCharts.occupancy_by_location || [];
            charts.occupancy = new Chart(occupancyCtx, {
                type: "bar",
                data: {
                    labels: rows.length ? rows.map((r) => r.location) : ["No Data"],
                    datasets: [{
                        label: "Occupancy %",
                        data: rows.length ? rows.map((r) => r.occupancy) : [0],
                        borderRadius: 8,
                        backgroundColor: (rows.length ? rows.map((r) => r.occupancy) : [0]).map((v) => {
                            const alpha = Math.max(Math.min(Number(v || 0) / 100, 1), 0.15);
                            return `rgba(111, 75, 255, ${alpha.toFixed(2)})`;
                        }),
                    }],
                },
                options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { display: false } } },
            });
        }

        if (revenueByLocCtx) {
            const rows = summaryCharts.revenue_by_location || [];
            charts.revenueByLocation = new Chart(revenueByLocCtx, {
                type: "bar",
                data: { labels: rows.length ? rows.map((r) => r.location) : ["No Data"], datasets: [{ label: "Revenue", data: rows.length ? rows.map((r) => r.revenue) : [0], borderRadius: 8, backgroundColor: "rgba(123, 89, 255, 0.72)" }] },
                options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { display: false } } },
            });
        }
    };

    const renderKpis = () => {
        const kpis = payload.kpis || {};
        const trends = kpis.trends || {};
        if (kpiRevenue) kpiRevenue.textContent = formatCurrency(kpis.total_revenue);
        if (kpiBookings) kpiBookings.textContent = String(kpis.total_bookings || 0);
        if (kpiUsers) kpiUsers.textContent = String(kpis.active_users || 0);
        if (kpiLocation) {
            kpiLocation.textContent = kpis.most_booked_location || "N/A";
            kpiLocation.title = kpis.most_booked_location || "N/A";
        }

        [[trendRevenue, trends.total_revenue], [trendBookings, trends.total_bookings], [trendUsers, trends.active_users], [trendLocation, trends.most_booked_location]].forEach(([el, val]) => {
            if (!el) return;
            const t = trendMarkup(val);
            el.className = t.className;
            el.textContent = t.text;
        });
    };

    const renderInsights = () => {
        const i = payload.insights || {};
        if (insightRevenue) {
            const v = Number(i.revenue_change || 0);
            insightRevenue.textContent = `${v > 0 ? "+" : ""}${v.toFixed(1)}%`;
        }
        if (insightLocation) insightLocation.textContent = i.most_active_location || "N/A";
        if (insightPeakTime) insightPeakTime.textContent = i.peak_usage_time || "--:--";
        if (insightLowOccupancy) {
            const low = i.low_occupancy_zones || [];
            insightLowOccupancy.textContent = low.length ? low.join(", ") : "No critical zones";
        }
    };

    const hydrateFilterData = () => {
        const filters = (payload.meta || {}).filters || {};
        optionMap.locations = filters.location_options || [];
        optionMap.zones = filters.zone_options || [];
        optionMap.lot_types = filters.lot_type_options || [];
        renderFilterDropdowns();
    };

    const hydrateDateRange = () => {
        const range = (payload.meta || {}).range || {};
        if (!filterState.startDate) filterState.startDate = range.start_date || "";
        if (!filterState.endDate) filterState.endDate = range.end_date || "";

        if (picker && filterState.startDate && filterState.endDate) {
            picker.setDate([filterState.startDate, filterState.endDate], false);
            if (dateRangePicker) {
                dateRangePicker.value = `${formatDateDisplay(filterState.startDate)} to ${formatDateDisplay(filterState.endDate)}`;
            }
        }
    };

    const renderAll = () => {
        hydrateDateRange();
        hydrateFilterData();
        renderKpis();
        renderInsights();
        renderCharts();
        renderTable();
        syncExportLinks();
    };

    const fetchSummary = async () => {
        const query = toQueryString(currentFilters());
        if (applyFiltersButton) {
            applyFiltersButton.disabled = true;
            applyFiltersButton.textContent = "Loading...";
        }

        try {
            const response = await fetch(`/api/admin/summary?${query}`);
            if (!response.ok) throw new Error("Failed to fetch summary data");
            payload = await response.json();
            page = 1;
            renderAll();
        } catch (err) {
            console.error(err);
        } finally {
            if (applyFiltersButton) {
                applyFiltersButton.disabled = false;
                applyFiltersButton.textContent = "Apply";
            }
        }
    };

    const closeDropdowns = () => dropdownWraps.forEach((w) => w.classList.remove("open"));

    const toggleDropdown = (wrap) => {
        if (!wrap) return;
        const willOpen = !wrap.classList.contains("open");
        closeDropdowns();
        if (willOpen) wrap.classList.add("open");
    };

    document.querySelectorAll("[data-sort]").forEach((head) => {
        head.addEventListener("click", () => {
            const key = head.getAttribute("data-sort");
            if (!key) return;
            if (sortState.key === key) sortState.direction = sortState.direction === "asc" ? "desc" : "asc";
            else {
                sortState.key = key;
                sortState.direction = "asc";
            }
            renderTable();
        });
    });

    if (rangePreset) {
        rangePreset.addEventListener("change", () => {
            const now = new Date();
            if (rangePreset.value === "7d") {
                const start = new Date(now);
                start.setDate(now.getDate() - 6);
                filterState.startDate = start.toISOString().slice(0, 10);
                filterState.endDate = now.toISOString().slice(0, 10);
                if (picker) picker.setDate([filterState.startDate, filterState.endDate], true);
            } else if (rangePreset.value === "30d") {
                const start = new Date(now);
                start.setDate(now.getDate() - 29);
                filterState.startDate = start.toISOString().slice(0, 10);
                filterState.endDate = now.toISOString().slice(0, 10);
                if (picker) picker.setDate([filterState.startDate, filterState.endDate], true);
            } else {
                filterState.startDate = "";
                filterState.endDate = "";
                if (picker) picker.clear();
                if (dateRangePicker) dateRangePicker.value = "";
            }
            syncExportLinks();
        });
    }

    if (locationFilterTrigger) locationFilterTrigger.addEventListener("click", () => toggleDropdown(locationFilterWrap));
    if (zoneFilterTrigger) zoneFilterTrigger.addEventListener("click", () => toggleDropdown(zoneFilterWrap));
    if (lotTypeFilterTrigger) lotTypeFilterTrigger.addEventListener("click", () => toggleDropdown(lotTypeFilterWrap));

    document.addEventListener("click", (event) => {
        const target = event.target;
        const inside = dropdownWraps.some((w) => w.contains(target));
        if (!inside) closeDropdowns();
    });

    [locationFilterOptions, zoneFilterOptions, lotTypeFilterOptions].forEach((container) => {
        if (!container) return;
        container.addEventListener("click", (event) => {
            const btn = event.target.closest(".filter-option");
            if (!btn) return;
            const key = btn.getAttribute("data-key");
            const value = btn.getAttribute("data-value");
            if (!key || !value) return;
            const selected = new Set(filterState[key] || []);
            if (selected.has(value)) selected.delete(value);
            else selected.add(value);
            filterState[key] = Array.from(selected);
            renderFilterDropdowns();
            renderTable();
            syncExportLinks();
        });
    });

    document.querySelectorAll(".filter-clear").forEach((btn) => {
        btn.addEventListener("click", (event) => {
            event.stopPropagation();
            const key = btn.getAttribute("data-clear");
            if (!key) return;
            filterState[key] = [];
            if (key === "locations" && locationFilterSearch) locationFilterSearch.value = "";
            renderFilterDropdowns();
            renderTable();
            syncExportLinks();
        });
    });

    if (locationFilterSearch) {
        locationFilterSearch.addEventListener("input", () => {
            renderDropdownOptions(locationFilterOptions, "locations", locationFilterSearch.value);
        });
    }

    if (tableSearch) {
        tableSearch.addEventListener("input", () => {
            page = 1;
            renderTable();
        });
    }

    if (tableCommonFilter) {
        tableCommonFilter.addEventListener("change", () => {
            page = 1;
            renderTable();
        });
    }

    if (pageSizeSelect) {
        pageSizeSelect.addEventListener("change", () => {
            pageSize = Number(pageSizeSelect.value) || 10;
            page = 1;
            renderTable();
        });
    }

    if (prevPageButton) {
        prevPageButton.addEventListener("click", () => {
            if (page > 1) {
                page -= 1;
                renderTable();
            }
        });
    }

    if (nextPageButton) {
        nextPageButton.addEventListener("click", () => {
            page += 1;
            renderTable();
        });
    }

    if (applyFiltersButton) applyFiltersButton.addEventListener("click", fetchSummary);

    if (resetFiltersButton) {
        resetFiltersButton.addEventListener("click", () => {
            if (rangePreset) rangePreset.value = "30d";
            filterState.startDate = "";
            filterState.endDate = "";
            filterState.locations = [];
            filterState.zones = [];
            filterState.lot_types = [];
            if (picker) picker.clear();
            if (dateRangePicker) dateRangePicker.value = "";
            if (locationFilterSearch) locationFilterSearch.value = "";
            if (tableSearch) tableSearch.value = "";
            if (tableCommonFilter) tableCommonFilter.value = "all";
            sortState = { key: "in_time", direction: "desc" };
            page = 1;
            renderFilterDropdowns();
            fetchSummary();
        });
    }

    if (sendReminderForm) {
        sendReminderForm.addEventListener("submit", () => {
            const btn = sendReminderForm.querySelector("button[type='submit']");
            if (btn) {
                btn.disabled = true;
                btn.textContent = "Sending...";
            }
        });
    }

    if (dateRangePicker && typeof flatpickr !== "undefined") {
        picker = flatpickr(dateRangePicker, {
    mode: "range",
    dateFormat: "Y-m-d",
    onChange: (dates) => {
        if (dates.length === 2) {
            filterState.startDate = dates[0].toISOString().slice(0, 10);
            filterState.endDate = dates[1].toISOString().slice(0, 10);
            dateRangePicker.value = `${formatDateDisplay(filterState.startDate)} to ${formatDateDisplay(filterState.endDate)}`;
        } else if (!dates.length) {
            filterState.startDate = "";
            filterState.endDate = "";
            dateRangePicker.value = "";
        }
        syncExportLinks();
        renderTable(); // 👉 yaha hona chahiye
    }
});
    }

    if (prevPageButton) {
        prevPageButton.addEventListener("click", () => {
            if (page > 1) {
                page -= 1;
                renderTable();
            }
        });
    }

    if (nextPageButton) {
        nextPageButton.addEventListener("click", () => {
            page += 1;
            renderTable();
        });
    }

    if (sendReminderForm) {
        sendReminderForm.addEventListener("submit", () => {
            const btn = sendReminderForm.querySelector("button[type='submit']");
            if (btn) {
                btn.disabled = true;
                btn.textContent = "Sending...";
            }
        });
    }

    syncExportLinks();
    renderAll();
}());
