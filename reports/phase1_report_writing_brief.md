# پرامپت شروع نگارش گزارش نهایی فاز ۱ — برای چت/نشست جدید

> این سند برای شروع یک نشست **جدید** (در بخش Code، همین پوشه‌ی پروژه، ترجیحاً مدل Opus با Effort بالا)
> نوشته شده. نشست قبلی که این کار در آن انجام شد بیش‌ازحد طولانی شده بود. همه‌ی اطلاعات لازم برای شروع
> بدون نیاز به تاریخچه‌ی چت قبلی، در همین سند و اسناد ارجاع‌داده‌شده موجود است.

---

## ۱. زمینه و وضعیت فعلی پروژه

پروژه‌ی «تحلیل رفتار مشتریان بانک توسعه تعاون» — منبع داده: بک‌آپ کامل SQL Server بانک
(`Alzahra_Final_DB`، ۱۴ جدول). **فاز ۱** (گزارش وضعیت موجود/Market Overview) از نظر تحلیلی **کاملاً
تمام شده**؛ آنچه باقی مانده فقط **نگارش خودِ گزارش نهایی** از روی یافته‌های آماده‌شده است.

کار فاز ۱ در چند نشست پیاپی با Claude Code انجام شد: آماده‌سازی داده → نقشه‌ی روابط جداول → View های
SQL → فهرست ۴بخشی تحلیل (الف: توصیفی، ب: ترکیبی، پ: پیشرفته، ت: کیفیت داده) → نقشه‌ی جغرافیایی →
**یک بازبینی مستقل کامل توسط Claude Opus** (که چند باگ واقعی در کد پیدا کرد) → رفع باگ‌ها → ۷ تحلیل
تکمیلی (تمرکز ریسک، خلاصه‌ی جمعیتی، پلکان سپرده، سررسید تسهیلات، NPL به تفکیک اندازه، ریزش سالانه،
داشبورد KPI).

---

## ۲. نقشه‌ی مستندات — کجا چه چیزی نوشته شده (به ترتیب اولویت خواندن)

| اولویت | فایل | محتوا |
|---|---|---|
| **۱ (شروع از اینجا)** | `docs/12_phase1_findings_and_gaps.md` | **مرجع اصلی برای نگارش گزارش.** تجمیع همه‌ی یافته‌ها، محدودیت‌ها، ردیف‌های تکراری، تمرکز ریسک، باگ‌های رفع‌شده، ابهامات باز، و تصمیم‌های روش‌شناختی که نیاز به تأیید کاربر دارند. |
| ۲ | `docs/12_phase1_readiness_review.md` | بازبینی مستقل و کامل Claude Opus روی کل کدبیس/داده (منبع اصلی سند بالا) — شامل جدول اعداد تأییدشده و توضیح فنی هر مسئله. |
| ۳ | `docs/EXECUTION_LOG.md` | تاریخچه‌ی زمانی کامل همه‌ی اقدامات، تصمیم‌ها و باگ‌ها به ترتیب نشست — برای جزئیات اجرایی هر موضوع. |
| ۴ | `docs/05_entity_relationships.md` | نقشه‌ی روابط ۱۴ جدول + یافته‌ی ایزوله‌بودن `Customer_Profile`. |
| ۵ | `docs/08_data_landscape_report.md` | آمار واقعی هر ۱۴ جدول + یافته‌ی حیاتی مقیاس جمعیت (دیتابیس زیرمجموعه‌ی بانک است). |
| ۶ | `docs/06_phase1_sql_views.md` | مستندسازی View های SQL. |
| ۷ | `docs/07_sampling_methodology.md` | متدولوژی نمونه‌گیری تاریخی (فاز ۰) — چارچوب مرجع RFM. |
| ۸ | `docs/04_data_gap_resolution_report.md`, `docs/03_data_dictionary.md` | دیکشنری داده و رفع ابهامات اولیه. |
| پس‌زمینه | `docs/phase1_review_prompt.md` | خلاصه‌ی قبل از بازبینی Opus (تا حدی توسط `docs/12_phase1_findings_and_gaps.md` به‌روز شده). |
| مرجع ستونی | `reports/data_profile/Table_Profiles.xlsx` | شناسنامه‌ی ستون‌به‌ستون هر ۱۴ جدول خام. |

---

## ۳. کد — کجاست و هر فایل چه می‌کند

همه در `notebooks/phase1_market_overview/`، هرکدام مستقل قابل‌اجرا، از ماژول مشترک
`src/tt_bank/common/persian_plot.py` (فونت فارسی) استفاده می‌کنند:

| فایل | محتوا |
|---|---|
| `01_depositors_overview.py` | پرتفوی سپرده، جمعیت فعال سپرده‌گذار |
| `02_loans_and_receivables_overview.py` | مانده و طبقه‌بندی مطالبات تسهیلات |
| `03_profit_and_loss_overview.py` | برآورد سود/زیان ماهانه («حاشیه‌ی ناخالص مالی برآوردی») |
| `04_descriptive_deep_dive.py` | بخش الف: توزیع نوع/اندازه‌ی تسهیلات، Top شعب، رشد سالانه، LDR، جغرافیا |
| `05_combined_analysis.py` | بخش ب: Cross-sell، نرخ سود مؤثر/هزینه‌ی تأمین مالی، پوشش وثیقه، عمق اعتباراسنادی، کوهورت، Vintage |
| `06_advanced_analysis.py` | بخش پ: چندضامنی، نوسان سپرده، ماتریس انتقال ریسک، DPD، Pareto، کارنامه‌ی شعب، کارمزد/گردش |
| `07_branch_geographic_map.py` | نقشه‌ی جغرافیایی عملکرد شعب به تفکیک استان |
| `08_data_quality_investigations.py` | بخش ت: ریشه‌یابی ۸ ابهام کیفیت داده (orphan، تکرارها، Cross-sell مستقل، ...) |
| `09_risk_concentration_analysis.py` | تمرکز تک‌نامی Top ۲۰ مشتری + تمرکز مشتری در اعتبارات اسنادی |
| `10_customer_population_overview.py` | خلاصه‌ی جمعیتی سه‌گانه (Venn: سپرده‌گذار/تسهیلات‌گیرنده/تراکنشی) |
| `11_supplementary_analyses.py` | پلکان مانده‌ی سپرده + سررسید تسهیلات + NPL به تفکیک اندازه + ریزش سالانه (۴ بخش در یک فایل) |
| `12_kpi_dashboard.py` | داشبورد ۱۵شاخصی — همه از CSV های بالا خوانده می‌شود، نه Hardcode |

کد ۱۲ View مستقر در `sql/views/*.sql` (هرکدام کامنت مستندساز محدودیت/باگ در بالای فایل دارد).

---

## ۴. خروجی‌های تصویری فعلی (۴۱ فایل PNG در `reports/figures/phase1_market_overview/`)

**سپرده/تسهیلات پایه:** `deposit_portfolio_composition`, `deposit_balance_trend`, `loan_type_distribution`,
`loan_size_histogram`, `top_branches_by_loan`, `top_branches_by_deposit_interest`, `yoy_growth`,
`loan_to_deposit_ratio`, `geographic_distribution_loans`, `receivables_classification_trend`,
`receivables_by_sector_latest`, `profit_and_loss_estimate_trend`

**ترکیبی/پیشرفته:** `cross_sell_ratio`, `effective_rate_loan_by_type`, `effective_rate_deposit_by_type`,
`collateral_coverage_by_loan_type`, `collateral_coverage_by_sector`, `letters_of_credit_npl_trend`,
`letters_of_credit_type_composition`, `deposit_cohort_retention`, `loan_vintage_analysis`,
`guarantor_complexity_npl`, `deposit_volatility_distribution`, `risk_transition_matrix`,
`dpd_distribution_overall`, `dpd_by_loan_type`, `concentration_lorenz_curve`, `branch_scorecard_bubble`,
`fee_to_turnover_distribution`

**کیفیت داده/جغرافیا:** `dq_orphan_loanfile_trend`, `dq_cross_sell_definition_sensitivity`,
`branch_geographic_performance_map`

**تکمیلی (جدیدترین):** `single_name_concentration_top20`, `loc_customer_concentration_top10`,
`customer_population_venn`, `deposit_balance_ladder`, `loan_maturity_profile`, `npl_by_loan_size`,
`npl_by_branch_size`, `deposit_annual_churn_rate`, `kpi_dashboard`

جداول CSV هم‌نام (و چند مورد اضافه) در `data/processed/phase1_market_overview/` موجودند.

---

## ۵. سه محدودیت بنیادی که باید همان صفحات اول گزارش اعلام شوند

۱. **`Customer_Profile` ایزوله است** — هیچ تحلیل جمعیت‌شناختی (سن/جنسیت/حقیقی-حقوقی) ممکن نیست.
۲. **فقط ~۴۷٪ مانده‌ی تسهیلات به شعبه وصل می‌شود.**
۳. **۲۲.۴٪ مانده‌ی تسهیلات رکورد قرارداد ندارد** (`Loan_Contract_Info`).

جزئیات کامل و ۱۰+ محدودیت دیگر (با همان شدت اهمیت) در `docs/12_phase1_findings_and_gaps.md`.

---

## ۶. درخواست از شما

1. **`docs/12_phase1_findings_and_gaps.md` و `docs/12_phase1_readiness_review.md` را کامل بخوانید** —
   این دو، چارچوب صحت/محدودیت کل گزارش‌اند.
2. کدبیس، View ها، و چند نمونه از CSV/PNG های بالا را مستقیماً بررسی کنید تا با خودِ داده هم تطبیق داده
   شود (نه فقط اعتماد به این خلاصه).
3. طبق تصمیم قبلی کاربر: **هیچ ابهام/سؤال بازی گزارش را متوقف نمی‌کند** — همه باید با توضیح شفاف در
   بخش «محدودیت‌ها/سؤالات از بانک» گزارش نهایی بیایند.
4. **ابتدا فقط ساختار پیشنهادی گزارش نهایی** (فهرست فصل‌ها/بخش‌ها، بدون محتوا) را ارائه دهید.
5. بعد از تأیید ساختار، **بخش‌به‌بخش** (نه یک‌جا) محتوای کامل گزارش را بنویسید.
