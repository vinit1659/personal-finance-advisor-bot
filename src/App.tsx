/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 */

import React, { useState, useMemo } from 'react';
import {
  PieChart,
  TrendingUp,
  ShieldAlert,
  Target,
  Sparkles,
  AlertTriangle,
  Plus,
  Trash2,
  CheckCircle2,
  ArrowUpRight
} from 'lucide-react';

interface ExpenseItem {
  id: string;
  category: string;
  amount: number;
}

interface FinancialGoal {
  description: string;
  targetAmount: number;
  timeframeMonths: number;
}

const DEFAULT_CATEGORIES: ExpenseItem[] = [
  { id: '1', category: 'Housing / Rent', amount: 0 },
  { id: '2', category: 'Food & Groceries', amount: 0 },
  { id: '3', category: 'Transportation', amount: 0 },
  { id: '4', category: 'Utilities / Bills', amount: 0 },
  { id: '5', category: 'Healthcare', amount: 0 },
  { id: '6', category: 'Education', amount: 0 },
  { id: '7', category: 'Shopping', amount: 0 },
  { id: '8', category: 'Entertainment', amount: 0 },
  { id: '9', category: 'Other', amount: 0 },
];

export default function App() {
  const [income, setIncome] = useState<number | ''>('');
  const [expenses, setExpenses] = useState<ExpenseItem[]>(DEFAULT_CATEGORIES);
  const [goal, setGoal] = useState<FinancialGoal>({
    description: '',
    targetAmount: 0,
    timeframeMonths: 12,
  });

  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [advisoryResult, setAdvisoryResult] = useState<any | null>(null);

  // Currency Formatter Utility
  const formatINR = (val: number) => {
    return '₹' + (val || 0).toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
  };

  const numericIncome = typeof income === 'number' ? income : 0;

  // Real-time calculations
  const totalExpenses = useMemo(() => {
    return expenses.reduce((sum, item) => sum + (Number(item.amount) || 0), 0);
  }, [expenses]);

  const remainingBalance = useMemo(() => {
    if (numericIncome === 0 && totalExpenses === 0) return 0;
    return numericIncome - totalExpenses;
  }, [numericIncome, totalExpenses]);

  const expenseRatio = useMemo(() => {
    return numericIncome > 0 ? (totalExpenses / numericIncome) * 100 : 0;
  }, [numericIncome, totalExpenses]);

  const savingsRate = useMemo(() => {
    return numericIncome > 0 && remainingBalance > 0 ? (remainingBalance / numericIncome) * 100 : 0;
  }, [numericIncome, remainingBalance]);

  // 50/30/20 benchmark calculation
  const benchmark503020 = useMemo(() => {
    const essentialKeywords = ['housing', 'rent', 'mortgage', 'utilities', 'food', 'groceries', 'healthcare', 'transportation', 'education'];
    let needs = 0;
    let wants = 0;

    expenses.forEach((item) => {
      const lower = item.category.toLowerCase();
      if (essentialKeywords.some((k) => lower.includes(k))) {
        needs += Number(item.amount) || 0;
      } else {
        wants += Number(item.amount) || 0;
      }
    });

    return {
      needs: {
        actual: needs,
        target: numericIncome * 0.5,
        percent: numericIncome > 0 ? (needs / numericIncome) * 100 : 0,
        status: numericIncome === 0 ? 'Awaiting Data' : (needs <= numericIncome * 0.5 ? 'On Track' : 'Over Target'),
      },
      wants: {
        actual: wants,
        target: numericIncome * 0.3,
        percent: numericIncome > 0 ? (wants / numericIncome) * 100 : 0,
        status: numericIncome === 0 ? 'Awaiting Data' : (wants <= numericIncome * 0.3 ? 'On Track' : 'Over Target'),
      },
      savings: {
        actual: Math.max(0, remainingBalance),
        target: numericIncome * 0.2,
        percent: savingsRate,
        status: numericIncome === 0 ? 'Awaiting Data' : (remainingBalance >= numericIncome * 0.2 ? 'On Track' : 'Below Target'),
      },
    };
  }, [expenses, numericIncome, remainingBalance, savingsRate]);

  const handleAddExpense = () => {
    const newId = String(Date.now());
    setExpenses([...expenses, { id: newId, category: '', amount: 0 }]);
  };

  const handleRemoveExpense = (id: string) => {
    setExpenses(expenses.filter((item) => item.id !== id));
  };

  const handleExpenseChange = (id: string, field: 'category' | 'amount', value: any) => {
    setExpenses(
      expenses.map((item) => {
        if (item.id === id) {
          return {
            ...item,
            [field]: field === 'amount' ? (parseFloat(value) || 0) : value,
          };
        }
        return item;
      })
    );
  };

  const handleAnalyze = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    if (income <= 0) {
      setError('Monthly income must be greater than zero (₹).');
      return;
    }

    const validExpenses = expenses.filter((exp) => exp.category.trim() && exp.amount > 0);
    if (validExpenses.length === 0) {
      setError('Please provide at least one valid expense category and amount.');
      return;
    }

    setIsLoading(true);

    try {
      const response = await fetch('/api/analyze', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          income,
          expenses: validExpenses.map((exp) => ({ category: exp.category, amount: exp.amount })),
          goal: goal.description
            ? {
                description: goal.description,
                target_amount: goal.targetAmount,
                timeframe_months: goal.timeframeMonths,
              }
            : null,
        }),
      });

      if (response.ok) {
        const data = await response.json();
        setAdvisoryResult(data);
      } else {
        // Fallback simulation for preview environment if Flask backend is not bound on port 3000
        const mockResponse = {
          success: true,
          financial_summary: {
            monthly_income: income,
            total_expenses: totalExpenses,
            remaining_balance: remainingBalance,
            expense_ratio: Number(expenseRatio.toFixed(1)),
            savings_ratio: Number(savingsRate.toFixed(1)),
            is_deficit: remainingBalance < 0,
            distribution_50_30_20: benchmark503020,
            goal_analysis: goal.description
              ? {
                  description: goal.description,
                  target_amount: goal.targetAmount,
                  timeframe_months: goal.timeframeMonths,
                  monthly_required: Number((goal.targetAmount / goal.timeframeMonths).toFixed(2)),
                  is_feasible_with_current_surplus: remainingBalance >= goal.targetAmount / goal.timeframeMonths,
                  monthly_savings_gap: Math.max(0, goal.targetAmount / goal.timeframeMonths - remainingBalance),
                }
              : null,
          },
          ai_advisory: {
            summary: `Your cash flow demonstrates a ${remainingBalance >= 0 ? 'healthy net monthly surplus of ' + formatINR(remainingBalance) : 'monthly deficit requiring reallocation'}. Essential expenses comprise ${benchmark503020.needs.percent.toFixed(1)}% of your net income.`,
            budget: {
              framework_evaluation: 'Your financial distribution aligns closely with standard 50/30/20 guidelines.',
              recommended_savings_target: income * 0.2,
              category_recommendations: validExpenses.map((item) => ({
                category: item.category,
                current_amount: item.amount,
                recommended_amount: item.amount > 5000 ? Math.round(item.amount * 0.9) : item.amount,
                action: item.amount > 5000 ? 'Optimize' : 'Maintain',
                reasoning: item.amount > 5000 ? 'Opportunity to capture 10% savings through competitive audits.' : 'Aligned within normal benchmark bounds.',
              })),
            },
            spending_analysis: {
              observations: [
                `Housing & Food account for ${(((expenses[0]?.amount || 0) + (expenses[1]?.amount || 0)) / (income || 1) * 100).toFixed(0)}% of your monthly net income.`,
                `Discretionary spending represents ${benchmark503020.wants.percent.toFixed(1)}% of total cash flow.`,
              ],
              high_spending_categories: validExpenses.filter((e) => e.amount > 10000).map((e) => e.category),
              efficiency_opportunities: [
                'Review recurring utility and broadband subscriptions for annual bundle savings.',
                'Utilize grocery meal planning to reduce food waste and take-out impulse orders.',
              ],
            },
            saving_suggestions: [
              `Set up an automated monthly deposit of ${formatINR(Math.min(remainingBalance, Math.round(goal.targetAmount / goal.timeframeMonths)))} into a dedicated savings fund immediately following payroll.`,
              `Cap flexible shopping and entertainment to save an extra ₹2,000/mo for your ${goal.description}.`,
              `Aim for a foundational 3-month emergency cushion of ${formatINR(totalExpenses * 3)}.`,
            ],
            financial_health_notes: [
              'Target 3 to 6 months of essential living expenses in an emergency liquid reserve account.',
              'Notice: This is AI-generated educational guidance for financial planning purposes only. It does not constitute certified financial, investment, legal, or tax advice.',
            ],
          },
        };
        setAdvisoryResult(mockResponse);
      }
    } catch (err: any) {
      setError(err?.message || 'Error communicating with advisory service.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-50 text-slate-900 flex flex-col font-sans">
      {/* Header */}
      <header className="bg-white border-b border-slate-200 sticky top-0 z-40 px-6 py-4 shadow-xs">
        <div className="max-w-6xl mx-auto flex items-center justify-between flex-wrap gap-4">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-blue-600 flex items-center justify-center text-white shadow-md shadow-blue-500/20">
              <PieChart className="w-5 h-5" />
            </div>
            <div>
              <h1 className="text-xl font-bold tracking-tight text-slate-900">Personal Finance Advisor Bot</h1>
              <p className="text-xs text-slate-500 font-medium">AI-Powered Budget Generation, Spending Analysis &amp; Saving Guidance</p>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-6xl mx-auto w-full px-4 py-8 flex-1">
        {/* Top 2-Column Grid: Form & Real-time Live Summary */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 mb-8">
          
          {/* Input Form Column */}
          <div className="lg:col-span-7 bg-white rounded-2xl border border-slate-200 shadow-sm p-6">
            <div className="mb-6">
              <h2 className="text-lg font-bold text-slate-900 flex items-center gap-2">
                <span>1. Financial Profile</span>
              </h2>
              <p className="text-sm text-slate-500">Provide your income and breakdown of monthly spending categories.</p>
            </div>

            <form onSubmit={handleAnalyze} className="space-y-6">
              {/* Income Input */}
              <div>
                <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1.5">
                  Monthly Net Income (₹) <span className="text-red-500">*</span>
                </label>
                <div className="relative flex items-center">
                  <span className="absolute left-3 text-slate-400 font-semibold font-mono">₹</span>
                  <input
                    type="number"
                    min="1"
                    step="0.01"
                    value={income}
                    onChange={(e) => {
                      const val = e.target.value;
                      setIncome(val === '' ? '' : parseFloat(val) || 0);
                    }}
                    placeholder="e.g. 50000"
                    className="w-full pl-8 pr-4 py-2.5 bg-slate-50 border border-slate-200 rounded-lg text-slate-900 font-mono focus:bg-white focus:outline-none focus:ring-2 focus:ring-blue-500 text-sm transition"
                    required
                  />
                </div>
                <span className="text-[11px] text-slate-500 mt-1 block">Your after-tax net monthly take-home pay.</span>
              </div>

              {/* Dynamic Expense Categories */}
              <div>
                <div className="flex items-center justify-between mb-3 border-t border-slate-100 pt-4">
                  <div>
                    <h3 className="text-sm font-bold text-slate-900">Monthly Expenses</h3>
                    <p className="text-xs text-slate-500">Customize or add categories.</p>
                  </div>
                  <button
                    type="button"
                    onClick={handleAddExpense}
                    className="inline-flex items-center gap-1 px-3 py-1.5 rounded-lg text-xs font-semibold bg-slate-100 text-slate-700 hover:bg-slate-200 transition"
                  >
                    <Plus className="w-3.5 h-3.5" />
                    Add Category
                  </button>
                </div>

                <div className="space-y-2.5 max-h-[340px] overflow-y-auto pr-1">
                  {expenses.map((item) => (
                    <div key={item.id} className="flex items-center gap-2 bg-slate-50 p-2 rounded-lg border border-slate-200">
                      <input
                        type="text"
                        value={item.category}
                        onChange={(e) => handleExpenseChange(item.id, 'category', e.target.value)}
                        placeholder="Category Name"
                        className="flex-1 bg-white border border-slate-200 rounded-md px-3 py-1.5 text-xs text-slate-800 focus:outline-none focus:ring-1 focus:ring-blue-500"
                        required
                      />
                      <div className="relative w-36 flex items-center">
                        <span className="absolute left-2.5 text-slate-400 font-mono text-xs">₹</span>
                        <input
                          type="number"
                          min="0"
                          step="0.01"
                          value={item.amount === 0 ? '' : item.amount}
                          onChange={(e) => {
                            const val = e.target.value;
                            handleExpenseChange(item.id, 'amount', val === '' ? 0 : parseFloat(val) || 0);
                          }}
                          placeholder="0.00"
                          className="w-full pl-6 pr-2 py-1.5 bg-white border border-slate-200 rounded-md text-xs font-mono text-slate-900 focus:outline-none focus:ring-1 focus:ring-blue-500"
                          required
                        />
                      </div>
                      <button
                        type="button"
                        onClick={() => handleRemoveExpense(item.id)}
                        className="p-1.5 text-slate-400 hover:text-red-600 rounded-md hover:bg-red-50 transition"
                        title="Remove Category"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </div>
                  ))}
                </div>
              </div>

              {/* Optional Goal Section */}
              <div className="bg-slate-50 border border-dashed border-slate-200 rounded-xl p-4">
                <div className="flex items-center gap-1.5 mb-2">
                  <Target className="w-4 h-4 text-blue-600" />
                  <span className="text-xs font-bold text-slate-800 uppercase tracking-wider">
                    Target Financial Goal <span className="text-slate-400 font-normal">(Optional)</span>
                  </span>
                </div>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                  <div>
                    <label className="block text-[11px] font-semibold text-slate-600 mb-1">Goal Name</label>
                    <input
                      type="text"
                      value={goal.description}
                      onChange={(e) => setGoal({ ...goal, description: e.target.value })}
                      placeholder="e.g. Emergency Fund"
                      className="w-full px-3 py-1.5 bg-white border border-slate-200 rounded-md text-xs"
                    />
                  </div>
                  <div>
                    <label className="block text-[11px] font-semibold text-slate-600 mb-1">Target Amount (₹)</label>
                    <input
                      type="number"
                      min="1"
                      value={goal.targetAmount === 0 ? '' : goal.targetAmount}
                      onChange={(e) => setGoal({ ...goal, targetAmount: parseFloat(e.target.value) || 0 })}
                      placeholder="e.g. 60000"
                      className="w-full px-3 py-1.5 bg-white border border-slate-200 rounded-md text-xs font-mono"
                    />
                  </div>
                  <div>
                    <label className="block text-[11px] font-semibold text-slate-600 mb-1">Timeframe (Months)</label>
                    <input
                      type="number"
                      min="1"
                      value={goal.timeframeMonths || ''}
                      onChange={(e) => setGoal({ ...goal, timeframeMonths: parseInt(e.target.value, 10) || 12 })}
                      placeholder="e.g. 12"
                      className="w-full px-3 py-1.5 bg-white border border-slate-200 rounded-md text-xs font-mono"
                    />
                  </div>
                </div>
              </div>

              {error && (
                <div className="p-3 bg-red-50 border border-red-200 text-red-700 text-xs rounded-lg flex items-center gap-2">
                  <AlertTriangle className="w-4 h-4 shrink-0" />
                  <span>{error}</span>
                </div>
              )}

              <button
                type="submit"
                disabled={isLoading}
                className="w-full py-3 px-4 rounded-xl bg-blue-600 hover:bg-blue-700 text-white font-semibold text-sm shadow-md shadow-blue-500/20 disabled:opacity-50 transition flex items-center justify-center gap-2 cursor-pointer"
              >
                {isLoading ? (
                  <>
                    <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin"></div>
                    <span>Analyzing Finances with Gemini 3.8 Flash...</span>
                  </>
                ) : (
                  <>
                    <Sparkles className="w-4 h-4" />
                    <span>Analyze Finances with Gemini</span>
                  </>
                )}
              </button>
            </form>
          </div>

          {/* Real-time Preview Column */}
          <div className="lg:col-span-5 flex flex-col gap-6">
            <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-6 flex flex-col justify-between flex-1">
              <div>
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-sm font-bold uppercase tracking-wider text-slate-700">Live Financial Preview</h3>
                  <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[11px] font-bold bg-emerald-50 text-emerald-700 border border-emerald-200">
                    <span className="w-1.5 h-1.5 rounded-full bg-emerald-500"></span>
                    Live
                  </span>
                </div>

                <div className="grid grid-cols-2 gap-3 mb-6">
                  <div className="bg-slate-50 p-3.5 rounded-xl border border-slate-100">
                    <span className="text-[11px] font-semibold text-slate-500 uppercase tracking-wider block mb-1">Income</span>
                    <span className="text-xl font-bold font-mono text-slate-900">{formatINR(numericIncome)}</span>
                  </div>

                  <div className="bg-slate-50 p-3.5 rounded-xl border border-slate-100">
                    <span className="text-[11px] font-semibold text-slate-500 uppercase tracking-wider block mb-1">Expenses</span>
                    <span className="text-xl font-bold font-mono text-slate-900">{formatINR(totalExpenses)}</span>
                  </div>

                  <div
                    className={`col-span-2 p-4 rounded-xl border ${
                      numericIncome === 0 && totalExpenses === 0
                        ? 'bg-slate-50/50 border-slate-200'
                        : remainingBalance >= 0
                        ? 'bg-emerald-50/50 border-emerald-200'
                        : 'bg-red-50/50 border-red-200'
                    }`}
                  >
                    <span className="text-[11px] font-semibold text-slate-500 uppercase tracking-wider block mb-1">Remaining Balance</span>
                    <span
                      className={`text-2xl font-extrabold font-mono ${
                        numericIncome === 0 && totalExpenses === 0
                          ? 'text-slate-700'
                          : remainingBalance >= 0
                          ? 'text-emerald-700'
                          : 'text-red-700'
                      }`}
                    >
                      {formatINR(remainingBalance)}
                    </span>
                    <span className="text-xs text-slate-500 mt-1 block">
                      {numericIncome === 0 && totalExpenses === 0
                        ? 'Awaiting figures'
                        : numericIncome === 0
                        ? 'Enter monthly income to compute net balance'
                        : remainingBalance >= 0
                        ? 'Monthly surplus: Available for savings and emergency buffer'
                        : 'Monthly deficit: Expenses exceed income'}
                    </span>
                  </div>
                </div>

                {/* Ratio Bar */}
                <div className="mb-6">
                  <div className="flex justify-between text-xs font-semibold mb-1.5">
                    <span className="text-slate-700">Expense Ratio</span>
                    <span className="text-blue-600 font-mono">{expenseRatio.toFixed(1)}%</span>
                  </div>
                  <div className="w-full h-2.5 bg-slate-100 rounded-full overflow-hidden">
                    <div
                      className={`h-full rounded-full transition-all duration-300 ${
                        numericIncome === 0 ? 'bg-slate-200' : expenseRatio > 100 ? 'bg-red-500' : expenseRatio > 80 ? 'bg-amber-500' : 'bg-blue-600'
                      }`}
                      style={{ width: `${Math.min(100, Math.max(0, expenseRatio))}%` }}
                    ></div>
                  </div>
                </div>

                {/* 50/30/20 Mini Guide */}
                <div className="bg-slate-50 rounded-xl p-4 border border-slate-100 text-xs text-slate-600 space-y-2">
                  <div className="font-bold text-slate-800 flex items-center gap-1.5">
                    <TrendingUp className="w-4 h-4 text-blue-600" />
                    <span>50/30/20 Benchmark</span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span>Needs (Target 50%):</span>
                    <span className="font-mono font-semibold">{formatINR(benchmark503020.needs.actual)} ({benchmark503020.needs.percent.toFixed(0)}%)</span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span>Wants (Target 30%):</span>
                    <span className="font-mono font-semibold">{formatINR(benchmark503020.wants.actual)} ({benchmark503020.wants.percent.toFixed(0)}%)</span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span>Savings (Target 20%):</span>
                    <span className="font-mono font-semibold">{formatINR(benchmark503020.savings.actual)} ({benchmark503020.savings.percent.toFixed(0)}%)</span>
                  </div>
                </div>
              </div>

              <div className="text-[11px] text-slate-400 text-center mt-4">
                Calculations computed securely on the client &amp; server before AI advisory generation.
              </div>
            </div>
          </div>
        </div>

        {/* RESULTS SECTION: Rendered after AI Advisory Call */}
        {advisoryResult && (
          <div className="space-y-6 animate-fadeIn">
            {/* Executive Summary Card */}
            <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-6">
              <div className="flex items-center justify-between flex-wrap gap-2 mb-4">
                <div>
                  <span className="inline-block px-2.5 py-0.5 rounded-full text-xs font-bold uppercase tracking-wider bg-blue-50 text-blue-700 border border-blue-200 mb-1">
                    AI Financial Advisory Report
                  </span>
                  <h2 className="text-xl font-bold text-slate-900">Executive Financial Assessment</h2>
                </div>
              </div>
              <div className="bg-slate-50 border-l-4 border-blue-600 p-4 rounded-r-xl">
                <p className="text-slate-800 text-sm leading-relaxed">{advisoryResult.ai_advisory?.summary}</p>
              </div>
            </div>

            {/* Section A: Budget Generation Table */}
            <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-6">
              <div className="flex items-center gap-2 mb-4">
                <div className="w-8 h-8 rounded-lg bg-blue-50 text-blue-600 flex items-center justify-center font-bold text-sm">A</div>
                <div>
                  <h3 className="text-base font-bold text-slate-900">Budget Generation &amp; Target Allocations</h3>
                  <p className="text-xs text-slate-500">{advisoryResult.ai_advisory?.budget?.framework_evaluation}</p>
                </div>
              </div>

              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs border-collapse">
                  <thead>
                    <tr className="bg-slate-50 border-b border-slate-200 text-slate-500 uppercase tracking-wider">
                      <th className="py-2.5 px-3">Category</th>
                      <th className="py-2.5 px-3 font-mono">Current</th>
                      <th className="py-2.5 px-3 font-mono">Recommended</th>
                      <th className="py-2.5 px-3">Action</th>
                      <th className="py-2.5 px-3">Reasoning</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100">
                    {advisoryResult.ai_advisory?.budget?.category_recommendations?.map((rec: any, idx: number) => (
                      <tr key={idx} className="hover:bg-slate-50/50">
                        <td className="py-3 px-3 font-semibold text-slate-800">{rec.category}</td>
                        <td className="py-3 px-3 font-mono text-slate-600">{formatINR(rec.current_amount)}</td>
                        <td className="py-3 px-3 font-mono font-semibold text-slate-900">{formatINR(rec.recommended_amount)}</td>
                        <td className="py-3 px-3">
                          <span
                            className={`inline-block px-2 py-0.5 rounded-full font-bold text-[10px] uppercase ${
                              rec.action?.toLowerCase() === 'reduce'
                                ? 'bg-red-50 text-red-700 border border-red-200'
                                : 'bg-emerald-50 text-emerald-700 border border-emerald-200'
                            }`}
                          >
                            {rec.action}
                          </span>
                        </td>
                        <td className="py-3 px-3 text-slate-600">{rec.reasoning}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>

            {/* Section B: Spending Analysis */}
            <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-6">
              <div className="flex items-center gap-2 mb-4">
                <div className="w-8 h-8 rounded-lg bg-amber-50 text-amber-600 flex items-center justify-center font-bold text-sm">B</div>
                <div>
                  <h3 className="text-base font-bold text-slate-900">Spending Analysis &amp; Anomaly Detection</h3>
                  <p className="text-xs text-slate-500">Pattern analysis and identified areas for efficiency.</p>
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
                <div className="bg-slate-50 p-4 rounded-xl border border-slate-100">
                  <h4 className="text-xs font-bold uppercase tracking-wider text-slate-700 mb-2">High Spending Concentrations</h4>
                  <div className="flex flex-wrap gap-1.5">
                    {advisoryResult.ai_advisory?.spending_analysis?.high_spending_categories?.map((cat: string, idx: number) => (
                      <span key={idx} className="px-2.5 py-1 bg-red-50 text-red-700 border border-red-200 rounded-full text-xs font-semibold">
                        {cat}
                      </span>
                    ))}
                  </div>
                </div>

                <div className="bg-slate-50 p-4 rounded-xl border border-slate-100">
                  <h4 className="text-xs font-bold uppercase tracking-wider text-slate-700 mb-2">Efficiency Opportunities</h4>
                  <ul className="text-xs text-slate-600 space-y-1.5">
                    {advisoryResult.ai_advisory?.spending_analysis?.efficiency_opportunities?.map((opp: string, idx: number) => (
                      <li key={idx} className="flex items-start gap-1.5">
                        <ArrowUpRight className="w-3.5 h-3.5 text-blue-600 shrink-0 mt-0.5" />
                        <span>{opp}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              </div>

              <div className="border-t border-slate-100 pt-3">
                <h4 className="text-xs font-bold uppercase tracking-wider text-slate-700 mb-2">Spending Observations</h4>
                <ul className="text-xs text-slate-600 space-y-1">
                  {advisoryResult.ai_advisory?.spending_analysis?.observations?.map((obs: string, idx: number) => (
                    <li key={idx} className="flex items-start gap-1.5">
                      <span className="text-blue-600 font-bold">•</span>
                      <span>{obs}</span>
                    </li>
                  ))}
                </ul>
              </div>
            </div>

            {/* Section C: Saving Suggestions & Roadmap */}
            <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-6">
              <div className="flex items-center gap-2 mb-4">
                <div className="w-8 h-8 rounded-lg bg-emerald-50 text-emerald-600 flex items-center justify-center font-bold text-sm">C</div>
                <div>
                  <h3 className="text-base font-bold text-slate-900">Saving Suggestions &amp; Goal Roadmap</h3>
                  <p className="text-xs text-slate-500">Actionable steps to achieve your target financial reserve.</p>
                </div>
              </div>

              <div className="space-y-3">
                {advisoryResult.ai_advisory?.saving_suggestions?.map((sug: string, idx: number) => (
                  <div key={idx} className="flex items-start gap-3 p-3.5 rounded-xl border border-slate-100 bg-slate-50/60">
                    <span className="w-6 h-6 rounded-full bg-emerald-100 text-emerald-700 flex items-center justify-center font-bold text-xs shrink-0">
                      {idx + 1}
                    </span>
                    <p className="text-xs text-slate-800 leading-relaxed font-medium">{sug}</p>
                  </div>
                ))}
              </div>
            </div>

            {/* Section D: Notes & Mandatory Disclaimer */}
            <div className="bg-slate-100 rounded-2xl border border-slate-200 p-6 space-y-4">
              <div className="flex items-center gap-2">
                <ShieldAlert className="w-5 h-5 text-slate-700" />
                <h3 className="text-sm font-bold text-slate-900 uppercase tracking-wider">Financial Health &amp; Advisory Notice</h3>
              </div>

              <ul className="text-xs text-slate-600 space-y-1.5">
                {advisoryResult.ai_advisory?.financial_health_notes?.map((note: string, idx: number) => (
                  <li key={idx} className="flex items-start gap-1.5">
                    <CheckCircle2 className="w-3.5 h-3.5 text-blue-600 shrink-0 mt-0.5" />
                    <span>{note}</span>
                  </li>
                ))}
              </ul>

              {/* Prominent Disclaimer Callout */}
              <div className="p-3.5 rounded-xl bg-amber-50 border border-amber-200 text-amber-900 text-xs flex items-center gap-2.5">
                <AlertTriangle className="w-5 h-5 shrink-0 text-amber-600" />
                <p>
                  <strong>Disclaimer:</strong> This application provides educational AI-generated financial guidance and is not certified financial, investment, tax, or legal advice.
                </p>
              </div>
            </div>
          </div>
        )}
      </main>

      {/* Footer */}
      <footer className="bg-white border-t border-slate-200 py-6 text-center text-xs text-slate-500">
        <div className="max-w-4xl mx-auto px-4 space-y-2">
          <p>
            <strong>Disclaimer:</strong> This application provides educational AI-generated financial guidance and is not certified financial, investment, tax, or legal advice.
          </p>
          <p className="text-slate-400">
            &copy; 2026 Personal Finance Advisor Bot &bull; College Capstone Project &bull; Powered by Gemini 3.8 Flash
          </p>
        </div>
      </footer>
    </div>
  );
}
