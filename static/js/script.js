/**
 * Personal Finance Advisor Bot - Client Application Controller
 * =============================================================
 * Capstone Project: Personal Finance Advisor Bot
 * AI Engine: Gemini 3.8 Flash
 * 
 * Responsibilities:
 * 1. Default and dynamic expense category rows (Add / Remove)
 * 2. Real-time client-side financial preview (Income, Expenses, Net Balance, Savings Ratio)
 * 3. Form input validation (positive income, non-negative expenses)
 * 4. Asynchronous communication via Fetch API to POST /api/analyze
 * 5. UI loading states and graceful error handling
 * 6. Dynamic rendering of the unified AI financial advisory dashboard
 * 7. Enforcing educational AI disclaimer visibility
 */

// Default categories matching capstone specifications (clean initial state)
const DEFAULT_CATEGORIES = [
    { name: "Housing / Rent", amount: "" },
    { name: "Food & Groceries", amount: "" },
    { name: "Transportation", amount: "" },
    { name: "Utilities / Bills", amount: "" },
    { name: "Healthcare", amount: "" },
    { name: "Education", amount: "" },
    { name: "Shopping", amount: "" },
    { name: "Entertainment", amount: "" },
    { name: "Other", amount: "" }
];

document.addEventListener("DOMContentLoaded", () => {
    // DOM Element References
    const financeForm = document.getElementById("finance-form");
    const incomeInput = document.getElementById("monthly-income");
    const expenseList = document.getElementById("expense-list");
    const addExpenseBtn = document.getElementById("add-expense-btn");
    const formErrorBanner = document.getElementById("form-error-banner");
    const analyzeBtn = document.getElementById("analyze-btn");
    const btnSpinner = document.getElementById("btn-spinner");
    const btnText = document.getElementById("btn-text");

    // Preview Elements
    const previewIncome = document.getElementById("preview-income");
    const previewExpenses = document.getElementById("preview-expenses");
    const previewBalance = document.getElementById("preview-balance");
    const previewBalanceStatus = document.getElementById("preview-balance-status");
    const previewBalanceTile = document.getElementById("preview-balance-tile");
    const previewSavings = document.getElementById("preview-savings");
    const previewSavingsRate = document.getElementById("preview-savings-rate");
    const previewRatioText = document.getElementById("preview-ratio-text");
    const previewProgressBar = document.getElementById("preview-progress-bar");
    const previewProgressFill = document.getElementById("preview-progress-fill");
    const previewRatioCaption = document.getElementById("preview-ratio-caption");

    // Dynamic UI Sections
    const loadingCard = document.getElementById("loading-card");
    const apiErrorCard = document.getElementById("api-error-card");
    const apiErrorMessage = document.getElementById("api-error-message");
    const resultsDashboard = document.getElementById("results-dashboard");
    const recalculateBtn = document.getElementById("recalculate-btn");

    // Initialize with clean default category rows (no demo amounts)
    DEFAULT_CATEGORIES.forEach(cat => {
        addExpenseRow(cat.name, cat.amount);
    });

    // Ensure income field is clean and empty
    incomeInput.value = "";

    // Compute initial clean live preview
    updateLivePreview();

    // Event Listeners
    incomeInput.addEventListener("input", updateLivePreview);
    addExpenseBtn.addEventListener("click", () => {
        addExpenseRow("", "");
        updateLivePreview();
    });

    if (recalculateBtn) {
        recalculateBtn.addEventListener("click", () => {
            window.scrollTo({ top: 0, behavior: "smooth" });
            incomeInput.focus();
        });
    }

    // Handle Form Submission
    financeForm.addEventListener("submit", async (e) => {
        e.preventDefault();
        hideFormError();
        hideApiError();

        // 1. Client-Side Input Validation
        const rawIncome = incomeInput.value.trim();
        const income = parseFloat(rawIncome);

        if (!rawIncome || isNaN(income) || income <= 0) {
            showFormError("Please enter a valid monthly net income greater than zero (₹).");
            incomeInput.focus();
            return;
        }

        const expenseRows = document.querySelectorAll(".expense-row");
        const expenses = [];
        let hasNegativeExpense = false;

        expenseRows.forEach((row, idx) => {
            const catNameInput = row.querySelector(".expense-category-input");
            const catAmountInput = row.querySelector(".expense-amount-input");

            const category = catNameInput.value.trim();
            const rawAmount = catAmountInput.value.trim();

            if (!category && !rawAmount) return; // Ignore completely blank rows

            const amount = parseFloat(rawAmount);

            if (isNaN(amount) || amount < 0) {
                hasNegativeExpense = true;
                catAmountInput.focus();
                return;
            }

            if (category && amount > 0) {
                expenses.push({ category, amount });
            }
        });

        if (hasNegativeExpense) {
            showFormError("Expense amounts cannot be negative. Please check your entries.");
            return;
        }

        if (expenses.length === 0) {
            showFormError("Please provide at least one expense category with an amount greater than zero.");
            return;
        }

        // Optional Goal Data
        const goalDesc = document.getElementById("goal-desc").value.trim();
        const rawGoalTarget = document.getElementById("goal-target").value.trim();
        const rawGoalTimeframe = document.getElementById("goal-timeframe").value.trim();

        let goal = null;
        if (goalDesc) {
            const targetAmount = parseFloat(rawGoalTarget);
            const timeframe = parseInt(rawGoalTimeframe, 10);
            goal = {
                description: goalDesc,
                target_amount: !isNaN(targetAmount) && targetAmount > 0 ? targetAmount : 0,
                timeframe_months: !isNaN(timeframe) && timeframe > 0 ? timeframe : 12
            };
        }

        // 2. Transition UI to Loading State
        setLoading(true);
        resultsDashboard.classList.add("hidden");

        // 3. Dispatch Async API Request to Flask Backend
        try {
            const response = await fetch("/api/analyze", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "Accept": "application/json"
                },
                body: JSON.stringify({
                    income: income,
                    expenses: expenses,
                    goal: goal
                })
            });

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.error || `Server responded with status ${response.status}`);
            }

            if (!data.success || !data.ai_advisory) {
                throw new Error("Invalid response format received from the advisory service.");
            }

            // 4. Render Dashboard Results
            renderResults(data);
            resultsDashboard.classList.remove("hidden");
            resultsDashboard.scrollIntoView({ behavior: "smooth" });

        } catch (err) {
            console.error("Advisory API Error:", err);
            showApiError(err.message || "Failed to generate financial advice. Please check your network and try again.");
        } finally {
            setLoading(false);
        }
    });

    /**
     * Adds an expense category input row to the DOM.
     */
    function addExpenseRow(categoryName = "", categoryAmount = "") {
        const row = document.createElement("div");
        row.className = "expense-row";
        row.innerHTML = `
            <input 
                type="text" 
                class="form-control expense-category-input" 
                placeholder="Category Name" 
                value="${escapeHtml(categoryName)}" 
                required 
                aria-label="Expense Category Name"
            >
            <div class="input-with-icon">
                <span class="currency-symbol" aria-hidden="true">₹</span>
                <input 
                    type="number" 
                    class="form-control expense-amount-input" 
                    placeholder="0.00" 
                    min="0" 
                    step="0.01" 
                    value="${categoryAmount !== '' ? categoryAmount : ''}" 
                    required 
                    aria-label="Expense Amount in Rupees"
                >
            </div>
            <button type="button" class="btn-remove-category" title="Remove Category" aria-label="Remove ${categoryName || 'this'} category">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
                    <line x1="18" y1="6" x2="6" y2="18"></line>
                    <line x1="6" y1="6" x2="18" y2="18"></line>
                </svg>
            </button>
        `;

        // Row listeners for real-time recalculation
        row.querySelector(".expense-category-input").addEventListener("input", updateLivePreview);
        row.querySelector(".expense-amount-input").addEventListener("input", updateLivePreview);

        row.querySelector(".btn-remove-category").addEventListener("click", () => {
            row.remove();
            updateLivePreview();
        });

        expenseList.appendChild(row);
    }

    /**
     * Computes client-side live metrics and updates the preview card.
     */
    function updateLivePreview() {
        const rawIncome = parseFloat(incomeInput.value) || 0;
        let totalExpenses = 0;

        const amountInputs = document.querySelectorAll(".expense-amount-input");
        amountInputs.forEach(input => {
            const val = parseFloat(input.value);
            if (!isNaN(val) && val > 0) {
                totalExpenses += val;
            }
        });

        // Clean empty-state handling when income has not yet been provided
        if (rawIncome === 0) {
            previewIncome.textContent = "₹0.00";
            previewExpenses.textContent = formatCurrency(totalExpenses);
            previewBalance.textContent = totalExpenses > 0 ? formatCurrency(-totalExpenses) : "₹0.00";
            previewSavings.textContent = "₹0.00";
            previewSavingsRate.textContent = "0.0% of income";
            previewRatioText.textContent = "0%";
            previewProgressFill.style.width = "0%";
            previewProgressFill.style.backgroundColor = "var(--primary)";
            previewProgressBar.setAttribute("aria-valuenow", "0");

            if (totalExpenses === 0) {
                previewBalanceStatus.textContent = "Awaiting figures";
                previewRatioCaption.textContent = "Enter your figures to see budget health metrics.";
            } else {
                previewBalanceStatus.textContent = "Enter monthly income to determine net balance";
                previewRatioCaption.textContent = "Enter monthly income to evaluate expense ratio.";
            }
            previewBalanceTile.style.borderColor = "var(--border-color)";
            previewBalance.style.color = "var(--secondary)";
            return;
        }

        // When valid income is entered
        const remaining = rawIncome - totalExpenses;
        const isDeficit = remaining < 0;
        const ratio = (totalExpenses / rawIncome * 100);
        const savingsRatio = !isDeficit ? (remaining / rawIncome * 100) : 0;

        // Update preview metrics
        previewIncome.textContent = formatCurrency(rawIncome);
        previewExpenses.textContent = formatCurrency(totalExpenses);
        previewBalance.textContent = formatCurrency(remaining);
        previewSavings.textContent = formatCurrency(Math.max(0, remaining));

        // Format balance status
        if (isDeficit) {
            previewBalanceStatus.textContent = "Monthly Deficit (Expenses exceed income)";
            previewBalanceTile.style.borderColor = "var(--danger-border)";
            previewBalance.style.color = "var(--danger)";
        } else {
            previewBalanceStatus.textContent = "Monthly Surplus (Available to save/invest)";
            previewBalanceTile.style.borderColor = "var(--success-border)";
            previewBalance.style.color = "var(--success)";
        }

        previewSavingsRate.textContent = `${savingsRatio.toFixed(1)}% of income`;

        // Progress bar calculations
        const cappedRatio = Math.min(100, Math.max(0, ratio));
        previewRatioText.textContent = `${ratio.toFixed(1)}%`;
        previewProgressFill.style.width = `${cappedRatio}%`;
        previewProgressBar.setAttribute("aria-valuenow", cappedRatio.toFixed(0));

        if (ratio > 100) {
            previewProgressFill.style.backgroundColor = "var(--danger)";
            previewRatioCaption.textContent = "⚠️ Critical: Spending exceeds 100% of income.";
        } else if (ratio > 80) {
            previewProgressFill.style.backgroundColor = "var(--warning)";
            previewRatioCaption.textContent = "Notice: Over 80% allocated to expenses. Thin savings cushion.";
        } else {
            previewProgressFill.style.backgroundColor = "var(--primary)";
            previewRatioCaption.textContent = "Healthy: Expenses are well within incoming cash flow.";
        }
    }

    /**
     * Renders the unified AI financial advisory dashboard from backend JSON.
     */
    function renderResults(data) {
        const summary = data.financial_summary;
        const advisory = data.ai_advisory;

        // 1. Timestamp & Executive Summary
        const now = new Date();
        document.getElementById("results-timestamp").textContent =
            `Generated on ${now.toLocaleDateString()} at ${now.toLocaleTimeString()} with Gemini 3.8 Flash`;
        document.getElementById("advisory-summary").textContent =
            advisory.summary || "Your financial profile has been analyzed.";

        // 2. Verified KPI Grid
        document.getElementById("kpi-income").textContent = formatCurrency(summary.monthly_income);
        document.getElementById("kpi-expenses").textContent = formatCurrency(summary.total_expenses);
        document.getElementById("kpi-expense-ratio").textContent = `${summary.expense_ratio}% of income`;

        const kpiBalance = document.getElementById("kpi-balance");
        kpiBalance.textContent = formatCurrency(summary.remaining_balance);
        kpiBalance.className = `kpi-value ${summary.is_deficit ? 'text-danger' : 'text-success'}`;
        document.getElementById("kpi-balance-status").textContent =
            summary.is_deficit ? "Monthly Deficit" : "Net Monthly Surplus";

        document.getElementById("kpi-savings").textContent = formatCurrency(Math.max(0, summary.remaining_balance));
        document.getElementById("kpi-savings-rate").textContent = `${summary.savings_ratio}% current rate`;

        // 3. 50/30/20 Framework Breakdown
        document.getElementById("framework-evaluation-text").textContent =
            advisory.budget?.framework_evaluation || "Comparison against standard 50/30/20 financial allocations.";

        const benchmarkGrid = document.getElementById("benchmark-grid");
        benchmarkGrid.innerHTML = "";

        const dist = summary.distribution_50_30_20 || {};
        const categories = [
            { key: "needs", name: "Essential Needs (50%)", targetPct: "50%", data: dist.needs },
            { key: "wants", name: "Discretionary Wants (30%)", targetPct: "30%", data: dist.wants },
            { key: "savings", name: "Savings & Reserves (20%)", targetPct: "20%", data: dist.savings }
        ];

        categories.forEach(cat => {
            const info = cat.data || {};
            const isOver = info.status === "Over Benchmark" || info.status === "Below Target";
            const badgeClass = isOver ? "badge-over" : "badge-ontrack";

            const card = document.createElement("div");
            card.className = "benchmark-card";
            card.innerHTML = `
                <div class="benchmark-card-header">
                    <span class="benchmark-cat-name">${cat.name}</span>
                    <span class="badge-status ${badgeClass}">${info.status || 'Calculated'}</span>
                </div>
                <div class="benchmark-amounts">${formatCurrency(info.actual_amount || 0)}</div>
                <div class="benchmark-sub">Target: ${formatCurrency(info.target_amount || 0)} (${cat.targetPct})</div>
                <div class="progress-track">
                    <div class="progress-fill" style="width: ${Math.min(100, info.actual_percent || 0)}%; background-color: ${isOver ? 'var(--warning)' : 'var(--success)'};"></div>
                </div>
            `;
            benchmarkGrid.appendChild(card);
        });

        // 4. Budget Recommendations Table
        const tbody = document.getElementById("budget-recommendations-body");
        tbody.innerHTML = "";

        const recs = advisory.budget?.category_recommendations || [];
        if (recs.length === 0) {
            tbody.innerHTML = `<tr><td colspan="5" style="text-align: center; color: var(--slate-400);">No specific category changes recommended. Current limits are balanced.</td></tr>`;
        } else {
            recs.forEach(rec => {
                const tr = document.createElement("tr");
                const actionClass = getActionBadgeClass(rec.action);

                tr.innerHTML = `
                    <td><strong>${escapeHtml(rec.category)}</strong></td>
                    <td class="td-amount">${formatCurrency(rec.current_amount)}</td>
                    <td class="td-amount">${formatCurrency(rec.recommended_amount)}</td>
                    <td><span class="badge-action ${actionClass}">${escapeHtml(rec.action || 'Maintain')}</span></td>
                    <td>${escapeHtml(rec.reasoning || '')}</td>
                `;
                tbody.appendChild(tr);
            });
        }

        // 5. Spending Analysis & Anomalies
        const highSpendingContainer = document.getElementById("high-spending-tags");
        highSpendingContainer.innerHTML = "";
        const flagged = advisory.spending_analysis?.high_spending_categories || [];
        if (flagged.length === 0) {
            highSpendingContainer.innerHTML = `<span style="font-size: 0.85rem; color: var(--slate-400);">No abnormal spending spikes detected.</span>`;
        } else {
            flagged.forEach(item => {
                const tag = document.createElement("span");
                tag.className = "flag-tag";
                tag.textContent = item;
                highSpendingContainer.appendChild(tag);
            });
        }

        const effList = document.getElementById("efficiency-opportunities-list");
        effList.innerHTML = "";
        const opps = advisory.spending_analysis?.efficiency_opportunities || [];
        if (opps.length === 0) {
            effList.innerHTML = `<li>Review monthly recurring subscriptions for unused services.</li>`;
        } else {
            opps.forEach(op => {
                const li = document.createElement("li");
                li.textContent = op;
                effList.appendChild(li);
            });
        }

        const obsList = document.getElementById("spending-observations-list");
        obsList.innerHTML = "";
        const observations = advisory.spending_analysis?.observations || [];
        observations.forEach(obs => {
            const li = document.createElement("li");
            li.textContent = obs;
            obsList.appendChild(li);
        });

        // 6. Practical Saving Suggestions & Goal Roadmap
        const goalBox = document.getElementById("goal-progress-box");
        const goalData = summary.goal_analysis;

        if (goalData && goalData.description) {
            goalBox.classList.remove("hidden");
            goalBox.innerHTML = `
                <div class="goal-highlight-title">🎯 Goal Roadmap: ${escapeHtml(goalData.description)}</div>
                <p style="font-size: 0.85rem; color: var(--slate-600);">
                    Target: ${formatCurrency(goalData.target_amount)} in ${goalData.timeframe_months} months
                </p>
                <div class="goal-highlight-grid">
                    <div class="goal-stat-item">
                        <div class="goal-stat-label">Monthly Required</div>
                        <div class="goal-stat-val">${formatCurrency(goalData.monthly_required)}/mo</div>
                    </div>
                    <div class="goal-stat-item">
                        <div class="goal-stat-label">Current Feasibility</div>
                        <div class="goal-stat-val ${goalData.is_feasible_with_current_surplus ? 'text-success' : 'text-danger'}">
                            ${goalData.is_feasible_with_current_surplus ? '✓ On Track' : `Gap of ${formatCurrency(goalData.monthly_savings_gap)}/mo`}
                        </div>
                    </div>
                    <div class="goal-stat-item">
                        <div class="goal-stat-label">Projected Completion</div>
                        <div class="goal-stat-val">
                            ${goalData.projected_months_at_current_rate ? `${goalData.projected_months_at_current_rate} mos` : 'Adjust Spending'}
                        </div>
                    </div>
                </div>
            `;
        } else {
            goalBox.classList.add("hidden");
            goalBox.innerHTML = "";
        }

        const suggestionsContainer = document.getElementById("saving-suggestions-container");
        suggestionsContainer.innerHTML = "";
        const suggestions = advisory.saving_suggestions || [];

        suggestions.forEach((sug, idx) => {
            const card = document.createElement("div");
            card.className = "suggestion-card";
            card.innerHTML = `
                <div class="suggestion-index">${idx + 1}</div>
                <div class="suggestion-body">${escapeHtml(sug)}</div>
            `;
            suggestionsContainer.appendChild(card);
        });

        // 7. Health Notes
        const healthList = document.getElementById("health-notes-list");
        healthList.innerHTML = "";
        const notes = advisory.financial_health_notes || [];
        notes.forEach(note => {
            // Skip redundant disclaimers in the bullet list since the prominent box is displayed below
            if (note.includes("AI-generated") && note.includes("disclaimer")) return;
            const li = document.createElement("li");
            li.textContent = note;
            healthList.appendChild(li);
        });
    }

    /**
     * Sets button and UI loading state.
     */
    function setLoading(isLoading) {
        if (isLoading) {
            analyzeBtn.disabled = true;
            btnSpinner.classList.remove("hidden");
            btnText.textContent = "Analyzing with Gemini 3.8 Flash...";
            loadingCard.classList.remove("hidden");
            loadingCard.scrollIntoView({ behavior: "smooth" });
        } else {
            analyzeBtn.disabled = false;
            btnSpinner.classList.add("hidden");
            btnText.textContent = "Analyze Finances with Gemini";
            loadingCard.classList.add("hidden");
        }
    }

    function showFormError(msg) {
        formErrorBanner.textContent = msg;
        formErrorBanner.classList.remove("hidden");
        formErrorBanner.scrollIntoView({ behavior: "smooth" });
    }

    function hideFormError() {
        formErrorBanner.textContent = "";
        formErrorBanner.classList.add("hidden");
    }

    function showApiError(msg) {
        apiErrorMessage.textContent = msg;
        apiErrorCard.classList.remove("hidden");
        apiErrorCard.scrollIntoView({ behavior: "smooth" });
    }

    function hideApiError() {
        apiErrorCard.classList.add("hidden");
    }

    function formatCurrency(amount) {
        const val = typeof amount === "number" ? amount : parseFloat(amount) || 0;
        return "₹" + val.toLocaleString("en-IN", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
    }

    function getActionBadgeClass(action = "") {
        const act = action.toLowerCase();
        if (act.includes("reduce")) return "action-reduce";
        if (act.includes("maintain")) return "action-maintain";
        return "action-optimize";
    }

    function escapeHtml(str) {
        if (str === null || str === undefined) return "";
        return String(str)
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;")
            .replace(/'/g, "&#039;");
    }
});
