/* ============================================================
   Home Office spend analysis — core analysis in SQL (T-SQL)
   Question: is the "March budget flush" real at the Home Office?
   Data: Home Office spending over £25,000, FY2025-26.

   Load the cleaned dataset (data/ho_fy2526_combined.csv) into a table
   called dbo.ho_spend with columns:
     Department, Entity, [Date] date, ExpenseType, ExpenseArea,
     Supplier, TransactionNumber, Amount decimal(18,2), [Month] char(7)
   ============================================================ */

/* ---- 1. Monthly spend, transaction count and median -------------
   The three-way test: a spike in TOTAL can be faked by one big
   contract, so we also look at COUNT and MEDIAN. A real year-end
   flush would lift total AND count. */
SELECT DISTINCT
    [Month],
    SUM(Amount)  OVER (PARTITION BY [Month]) AS total_spend,
    COUNT(*)     OVER (PARTITION BY [Month]) AS txn_count,
    PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY Amount)
                 OVER (PARTITION BY [Month]) AS median_txn
FROM dbo.ho_spend
ORDER BY [Month];

/* ---- 2. Share of each month's spend from contracts over £1m ------
   This is the rigour check. If April's total is high but 78% of it
   is single payments over £1m, the spike is a few big annual
   contracts, not a broad increase in spending. */
SELECT
    [Month],
    SUM(Amount)                                                   AS total_spend,
    SUM(CASE WHEN Amount > 1000000 THEN Amount ELSE 0 END)        AS big_contract_spend,
    CAST(100.0 * SUM(CASE WHEN Amount > 1000000 THEN Amount ELSE 0 END)
         / SUM(Amount) AS decimal(5,1))                           AS big_contract_pct
FROM dbo.ho_spend
GROUP BY [Month]
ORDER BY big_contract_pct DESC;

/* ---- 3. Rank the months by total spend --------------------------
   Confirms March is mid-pack (5th), April is the largest. */
SELECT
    [Month],
    SUM(Amount)                                        AS total_spend,
    RANK() OVER (ORDER BY SUM(Amount) DESC)            AS spend_rank
FROM dbo.ho_spend
GROUP BY [Month]
ORDER BY spend_rank;

/* ---- 4. Top suppliers driving April (the big contracts) ---------- */
SELECT TOP 10
    Supplier,
    SUM(Amount) AS april_spend
FROM dbo.ho_spend
WHERE [Month] = '2025-04'
GROUP BY Supplier
ORDER BY april_spend DESC;
