"use client";

/**
 * Voxora AI — Dashboard Header Navigation & Date Controls.
 *
 * Implements exact specifications from user mockups:
 * 1. Granularity Pill Switcher: Daily | Monthly | Yearly
 * 2. Contextual Picker Button:
 *    - Daily mode:   📅 10 Sep 2026 ▾ (opens single-day calendar popover)
 *    - Monthly mode: 📅 September 2026 ▾ (opens 12-month picker with Year selector)
 *    - Yearly mode:  2026 ▾ (opens single-year dropdown: 2023-2027)
 * 3. Immediate context-driven data loading:
 *    - Daily: loads single day revenue & hourly breakdown (defaults to current date: 10 Sep 2026)
 *    - Monthly: loads single month revenue (defaults to current month: September 2026)
 *    - Yearly: loads single year revenue (defaults to this year: 2026)
 * 4. Empty State: Displays clear "No data available" when choosing an out-of-range date/month/year.
 */

import React, { useState, useRef, useEffect } from "react";
import { useDashboardStore, Granularity } from "@/stores/dashboardStore";
import styles from "./DashboardHeaderNav.module.css";

const YEARS = [2023, 2024, 2025, 2026, 2027];

const MONTH_NAMES = [
  "January", "February", "March", "April", "May", "June",
  "July", "August", "September", "October", "November", "December"
];

const MONTH_SHORT = [
  "Jan", "Feb", "Mar", "Apr", "May", "Jun",
  "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"
];

const WEEKDAYS = ["Su", "Mo", "Tu", "We", "Th", "Fr", "Sa"];

export default function DashboardHeaderNav() {
  const {
    granularity,
    selectedDate,
    selectedMonth,
    selectedYear,
    data,
    selectDaily,
    selectMonthly,
    selectYearly,
    setGranularity,
    resetToDefaultRange,
  } = useDashboardStore();

  const [popoverOpen, setPopoverOpen] = useState(false);
  const popoverRef = useRef<HTMLDivElement>(null);

  // Local browsing states for Monthly & Daily popovers
  const [browseYear, setBrowseYear] = useState<number>(selectedYear || 2026);
  const [browseMonth, setBrowseMonth] = useState<number>(selectedMonth?.month ?? 8);

  // Sync browsing year/month when store changes
  useEffect(() => {
    if (selectedYear) setBrowseYear(selectedYear);
  }, [selectedYear]);

  useEffect(() => {
    if (selectedMonth?.month !== undefined) setBrowseMonth(selectedMonth.month);
  }, [selectedMonth]);

  // Click outside to close popover
  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (popoverRef.current && !popoverRef.current.contains(e.target as Node)) {
        setPopoverOpen(false);
      }
    };
    if (popoverOpen) {
      document.addEventListener("mousedown", handleClickOutside);
    }
    return () => {
      document.removeEventListener("mousedown", handleClickOutside);
    };
  }, [popoverOpen]);

  // ── Date Formatting Helpers ─────────────────────────────────

  // Format Daily label: e.g. "10 Sep 2026"
  const getDailyButtonLabel = () => {
    if (!selectedDate) return "10 Sep 2026";
    const parts = selectedDate.split("-");
    if (parts.length !== 3) return selectedDate;
    const year = parts[0];
    const monthIndex = parseInt(parts[1], 10) - 1;
    const day = parseInt(parts[2], 10);
    return `${day < 10 ? "0" + day : day} ${MONTH_SHORT[monthIndex] || ""} ${year}`;
  };

  // Format Monthly label: e.g. "September 2026"
  const getMonthlyButtonLabel = () => {
    const m = selectedMonth?.month ?? 8;
    const y = selectedMonth?.year ?? 2026;
    return `${MONTH_NAMES[m]} ${y}`;
  };

  // Check if current dataset returned 0 orders or revenue
  const totalOrdersKpi = data?.kpis.find((k) =>
    k.id.includes("order") || k.id.includes("total") || k.id.includes("cust")
  );
  const revenueKpi = data?.kpis.find((k) => k.id.includes("revenue") || k.id.includes("rev"));
  const isNoData =
    data !== null &&
    (!revenueKpi || revenueKpi.value === 0) &&
    (!totalOrdersKpi || totalOrdersKpi.value === 0);

  // ── Handlers for User Selection ─────────────────────────────

  const handleSelectYear = async (year: number) => {
    setPopoverOpen(false);
    await selectYearly(year);
  };

  const handleSelectMonth = async (monthIndex: number) => {
    setPopoverOpen(false);
    await selectMonthly(browseYear, monthIndex);
  };

  const handleSelectDay = async (day: number) => {
    const monthStr = String(browseMonth + 1).padStart(2, "0");
    const dayStr = String(day).padStart(2, "0");
    const fullDate = `${browseYear}-${monthStr}-${dayStr}`;
    setPopoverOpen(false);
    await selectDaily(fullDate);
  };

  const handlePrevMonth = () => {
    if (browseMonth === 0) {
      setBrowseMonth(11);
      setBrowseYear((y) => y - 1);
    } else {
      setBrowseMonth((m) => m - 1);
    }
  };

  const handleNextMonth = () => {
    if (browseMonth === 11) {
      setBrowseMonth(0);
      setBrowseYear((y) => y + 1);
    } else {
      setBrowseMonth((m) => m + 1);
    }
  };

  // ── Calendar Grid Computation ───────────────────────────────

  const renderCalendarDays = () => {
    const daysInMonth = new Date(browseYear, browseMonth + 1, 0).getDate();
    const firstDayOfWeek = new Date(browseYear, browseMonth, 1).getDay(); // 0 = Sun
    const daysInPrevMonth = new Date(browseYear, browseMonth, 0).getDate();

    const cells: React.ReactNode[] = [];

    // Preceding trailing days from previous month
    for (let i = firstDayOfWeek - 1; i >= 0; i--) {
      const prevDay = daysInPrevMonth - i;
      cells.push(
        <button
          key={`prev-${prevDay}`}
          type="button"
          className={`${styles.dayCell} ${styles.dayCellTrailing}`}
          onClick={() => {
            const prevMonth = browseMonth === 0 ? 11 : browseMonth - 1;
            const prevYear = browseMonth === 0 ? browseYear - 1 : browseYear;
            const dateStr = `${prevYear}-${String(prevMonth + 1).padStart(2, "0")}-${String(prevDay).padStart(2, "0")}`;
            setPopoverOpen(false);
            selectDaily(dateStr);
          }}
        >
          {prevDay}
        </button>
      );
    }

    // Days of current month
    for (let day = 1; day <= daysInMonth; day++) {
      const dayIso = `${browseYear}-${String(browseMonth + 1).padStart(2, "0")}-${String(day).padStart(2, "0")}`;
      const isSelected = selectedDate === dayIso && granularity === "daily";

      cells.push(
        <button
          key={`curr-${day}`}
          type="button"
          className={`${styles.dayCell} ${isSelected ? styles.dayCellActive : ""}`}
          onClick={() => handleSelectDay(day)}
        >
          {day}
        </button>
      );
    }

    // Trailing days from next month to complete 35 or 42 grid cells
    const totalCellsSoFar = cells.length;
    const targetTotal = totalCellsSoFar <= 35 ? 35 : 42;
    const nextDaysNeeded = targetTotal - totalCellsSoFar;

    for (let nextDay = 1; nextDay <= nextDaysNeeded; nextDay++) {
      cells.push(
        <button
          key={`next-${nextDay}`}
          type="button"
          className={`${styles.dayCell} ${styles.dayCellTrailing}`}
          onClick={() => {
            const nextMonth = browseMonth === 11 ? 0 : browseMonth + 1;
            const nextYear = browseMonth === 11 ? browseYear + 1 : browseYear;
            const dateStr = `${nextYear}-${String(nextMonth + 1).padStart(2, "0")}-${String(nextDay).padStart(2, "0")}`;
            setPopoverOpen(false);
            selectDaily(dateStr);
          }}
        >
          {nextDay}
        </button>
      );
    }

    return cells;
  };

  return (
    <div className={styles.navContainer}>
      <div className={styles.topBar}>
        <div className={styles.filterRow}>
          {/* ── 1. Daily | Monthly | Yearly Pill Group ────── */}
          <div className={styles.granularityGroup} role="radiogroup" aria-label="Granularity">
            <button
              type="button"
              className={`${styles.granularityBtn} ${
                granularity === "daily" ? styles.granularityBtnActive : ""
              }`}
              onClick={() => setGranularity("daily")}
            >
              Daily
            </button>
            <button
              type="button"
              className={`${styles.granularityBtn} ${
                granularity === "monthly" ? styles.granularityBtnActive : ""
              }`}
              onClick={() => setGranularity("monthly")}
            >
              Monthly
            </button>
            <button
              type="button"
              className={`${styles.granularityBtn} ${
                granularity === "yearly" ? styles.granularityBtnActive : ""
              }`}
              onClick={() => setGranularity("yearly")}
            >
              Yearly
            </button>
          </div>

          {/* ── 2. Contextual Picker Button & Popovers ───── */}
          <div className={styles.popoverContainer} ref={popoverRef}>
            {/* Contextual Trigger Button */}
            <button
              type="button"
              className={`${styles.contextTrigger} ${popoverOpen ? styles.contextTriggerActive : ""}`}
              onClick={() => setPopoverOpen(!popoverOpen)}
              title={
                granularity === "daily"
                  ? "Select specific date"
                  : granularity === "monthly"
                  ? "Select specific month"
                  : "Select specific year"
              }
            >
              {granularity === "daily" && (
                <>
                  <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <rect x="3" y="4" width="18" height="18" rx="2" ry="2" />
                    <line x1="16" y1="2" x2="16" y2="6" />
                    <line x1="8" y1="2" x2="8" y2="6" />
                    <line x1="3" y1="10" x2="21" y2="10" />
                  </svg>
                  <span>{getDailyButtonLabel()}</span>
                </>
              )}

              {granularity === "monthly" && (
                <>
                  <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <rect x="3" y="4" width="18" height="18" rx="2" ry="2" />
                    <line x1="16" y1="2" x2="16" y2="6" />
                    <line x1="8" y1="2" x2="8" y2="6" />
                    <line x1="3" y1="10" x2="21" y2="10" />
                  </svg>
                  <span>{getMonthlyButtonLabel()}</span>
                </>
              )}

              {granularity === "yearly" && (
                <span>{selectedYear || 2026}</span>
              )}

              {/* Chevron Down Icon */}
              <svg
                width="12"
                height="12"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="2"
                className={`${styles.chevronIcon} ${popoverOpen ? styles.chevronIconOpen : ""}`}
              >
                <polyline points="6 9 12 15 18 9" />
              </svg>
            </button>

            {/* ── Popover Content based on Granularity Mode ── */}
            {popoverOpen && (
              <div className={styles.popoverCard}>
                {/* ── Mode A: Yearly Dropdown (Image 2) ───── */}
                {granularity === "yearly" && (
                  <div className={styles.yearDropdownList}>
                    {YEARS.map((y) => {
                      const isSelected = selectedYear === y;
                      return (
                        <button
                          key={y}
                          type="button"
                          className={`${styles.yearItem} ${isSelected ? styles.yearItemActive : ""}`}
                          onClick={() => handleSelectYear(y)}
                        >
                          <span>{y}</span>
                          {isSelected && (
                            <svg className={styles.checkIcon} width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                              <polyline points="20 6 9 17 4 12" />
                            </svg>
                          )}
                        </button>
                      );
                    })}
                  </div>
                )}

                {/* ── Mode B: Monthly Popover (Image 3) ──── */}
                {granularity === "monthly" && (
                  <div className={styles.monthPopoverCard}>
                    {/* Top Row: YEAR dropdown */}
                    <div className={styles.popoverHeaderRow}>
                      <span className={styles.fieldLabel}>YEAR</span>
                      <select
                        className={styles.selectDropdown}
                        value={browseYear}
                        onChange={(e) => setBrowseYear(parseInt(e.target.value, 10))}
                      >
                        {YEARS.map((y) => (
                          <option key={y} value={y}>
                            {y}
                          </option>
                        ))}
                      </select>
                    </div>

                    {/* 12-Month Grid */}
                    <div className={styles.monthGrid}>
                      {MONTH_SHORT.map((shortName, idx) => {
                        const isSelected =
                          selectedMonth?.year === browseYear && selectedMonth?.month === idx;
                        return (
                          <button
                            key={shortName}
                            type="button"
                            className={`${styles.monthCell} ${isSelected ? styles.monthCellActive : ""}`}
                            onClick={() => handleSelectMonth(idx)}
                          >
                            {shortName}
                          </button>
                        );
                      })}
                    </div>
                  </div>
                )}

                {/* ── Mode C: Daily Calendar Popover (Image 4) ── */}
                {granularity === "daily" && (
                  <div className={styles.dailyPopoverCard}>
                    {/* Top Controls: Year & Month selects */}
                    <div className={styles.topControlsRow}>
                      <div className={styles.controlField}>
                        <span className={styles.fieldLabel}>YEAR</span>
                        <select
                          className={styles.selectDropdown}
                          value={browseYear}
                          onChange={(e) => setBrowseYear(parseInt(e.target.value, 10))}
                        >
                          {YEARS.map((y) => (
                            <option key={y} value={y}>
                              {y}
                            </option>
                          ))}
                        </select>
                      </div>

                      <div className={styles.controlField}>
                        <span className={styles.fieldLabel}>MONTH</span>
                        <select
                          className={styles.selectDropdown}
                          value={browseMonth}
                          onChange={(e) => setBrowseMonth(parseInt(e.target.value, 10))}
                        >
                          {MONTH_NAMES.map((name, idx) => (
                            <option key={name} value={idx}>
                              {name}
                            </option>
                          ))}
                        </select>
                      </div>
                    </div>

                    {/* Month Nav Header: < Month Year > */}
                    <div className={styles.monthNavHeader}>
                      <button
                        type="button"
                        className={styles.navArrowBtn}
                        onClick={handlePrevMonth}
                        title="Previous Month"
                      >
                        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                          <polyline points="15 18 9 12 15 6" />
                        </svg>
                      </button>

                      <span className={styles.monthNavTitle}>
                        {MONTH_NAMES[browseMonth]} {browseYear}
                      </span>

                      <button
                        type="button"
                        className={styles.navArrowBtn}
                        onClick={handleNextMonth}
                        title="Next Month"
                      >
                        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                          <polyline points="9 18 15 12 9 6" />
                        </svg>
                      </button>
                    </div>

                    {/* Calendar Days Matrix */}
                    <div className={styles.calendarGrid}>
                      {WEEKDAYS.map((wd) => (
                        <div key={wd} className={styles.weekdayHeader}>
                          {wd}
                        </div>
                      ))}
                      {renderCalendarDays()}
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      </div>

      {/* ── 4. No Data Available Warning Banner ─────────── */}
      {isNoData && (
        <div className={styles.noDataBanner}>
          <div className={styles.noDataLeft}>
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <circle cx="12" cy="12" r="10" />
              <line x1="12" y1="8" x2="12" y2="12" />
              <line x1="12" y1="16" x2="12.01" y2="16" />
            </svg>
            <span>
              {granularity === "daily" && (
                <>
                  <strong>No transactions recorded for {getDailyButtonLabel()}.</strong> Data is populated from <strong>10 Sep 2024</strong> to <strong>10 Sep 2026</strong>.
                </>
              )}
              {granularity === "monthly" && (
                <>
                  <strong>No transactions recorded for {getMonthlyButtonLabel()}.</strong> Data is populated from <strong>Sept 2024</strong> to <strong>Sept 2026</strong>.
                </>
              )}
              {granularity === "yearly" && (
                <>
                  <strong>No transactions recorded for Year {selectedYear}.</strong> Data is populated for years <strong>2024, 2025, and 2026</strong>.
                </>
              )}
            </span>
          </div>

          <button
            type="button"
            className={styles.resetBtn}
            onClick={resetToDefaultRange}
          >
            {granularity === "daily"
              ? "Reset to Current Date (10 Sep 2026)"
              : granularity === "monthly"
              ? "Reset to Current Month (Sep 2026)"
              : "Reset to This Year (2026)"}
          </button>
        </div>
      )}
    </div>
  );
}
