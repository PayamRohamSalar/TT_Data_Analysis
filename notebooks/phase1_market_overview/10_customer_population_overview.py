"""
خلاصه‌ی جمعیتی داده‌ی بانک (درخواست صریح کاربر، ۲۰۲۶-۰۹-۱۱): بعد از حذف کامل ردیف‌های تکراری، چند
مشتری منحصربه‌فرد در هرکدام از سه گروه اصلی داریم (سپرده‌گذاران، تسهیلات‌گیرندگان، مشتریان دارای
تراکنش/کارمزد)، و این سه گروه چقدر با هم همپوشانی دارند؟

⚠️ نکته‌ی روش‌شناختی حیاتی (طبق یافته‌ی بخش ت/پ این پروژه): «تسهیلات‌گیرنده» در این تحلیل از
Loan_Remain.customer_id می‌آید که شامل **همه‌ی طرفین قرارداد (وام‌گیرنده + تمام ضامن‌ها)** است، نه فقط
گیرنده‌ی اصلی — همان جمعیتی که در بخش ب/پ هم استفاده شده. عدد جایگزین (فقط گیرنده‌ی اصلی رسمی،
Loan_Grant_Customer) هم جداگانه گزارش می‌شود تا مقایسه ممکن باشد.

سه جمعیت:
- سپرده‌گذاران: main_customer_id یکتا در Deposit_Accoutnt_Info
- تسهیلات‌گیرندگان: customer_id یکتا در Loan_Remain (همه‌ی طرفین) + عدد جایگزین از Loan_Grant_Customer
- مشتریان تراکنشی/کارمزدی: main_customer_id یکتا در Customer_Monthly_Activity (⚠️ این جدول طبق
  docs/11 فقط زیرمجموعه‌ای از کل مشتریان است، نه جمعیت پایه‌ی کامل)

خروجی: نمودار Venn سه‌دایره‌ای + جدول خلاصه در reports/figures و data/processed.
"""

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
from matplotlib_venn import venn3

from tt_bank.common.persian_plot import fa, setup_persian_font, to_persian_digits
from tt_bank.db.connection import get_engine

PROJECT_ROOT = Path(__file__).resolve().parents[2]
FIGURES_DIR = PROJECT_ROOT / "reports" / "figures" / "phase1_market_overview"
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed" / "phase1_market_overview"
FIGURES_DIR.mkdir(parents=True, exist_ok=True)
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
setup_persian_font()


def main() -> None:
    engine = get_engine()

    depositors = set(pd.read_sql(
        """
        SELECT DISTINCT CAST(LTRIM(RTRIM(MAIN_CUSTOMER_ID)) AS numeric(38,0)) AS customer_id
        FROM dbo.Deposit_Accoutnt_Info
        WHERE ISNUMERIC(LTRIM(RTRIM(MAIN_CUSTOMER_ID))) = 1
        """,
        engine,
    )["customer_id"])

    loan_all_parties = set(pd.read_sql(
        "SELECT DISTINCT customer_id FROM dbo.Loan_Remain", engine
    )["customer_id"])

    loan_primary_only = set(pd.read_sql(
        "SELECT DISTINCT ID AS customer_id FROM dbo.Loan_Grant_Customer", engine
    )["customer_id"])

    transactional = set(pd.read_sql(
        """
        SELECT DISTINCT CAST(LTRIM(RTRIM(main_customer_id)) AS numeric(38,0)) AS customer_id
        FROM dbo.Customer_Monthly_Activity
        WHERE ISNUMERIC(LTRIM(RTRIM(main_customer_id))) = 1
        """,
        engine,
    )["customer_id"])

    print("=== جمعیت منحصربه‌فرد هر گروه (بعد از حذف کامل تکرار) ===")
    print(f"سپرده‌گذاران (Deposit_Accoutnt_Info):                 {len(depositors):>10,}")
    print(f"تسهیلات‌گیرندگان (Loan_Remain، همه‌ی طرفین/شامل ضامن): {len(loan_all_parties):>10,}")
    print(f"تسهیلات‌گیرندگان (Loan_Grant_Customer، فقط گیرنده‌ی اصلی): {len(loan_primary_only):>10,}")
    print(f"مشتریان تراکنشی/کارمزدی (Customer_Monthly_Activity):  {len(transactional):>10,}")

    all_three_ids = depositors | loan_all_parties | transactional
    print(f"\nاتحاد کل سه گروه (حداقل یک رابطه از این سه نوع): {len(all_three_ids):,}")

    # --- جدول همپوشانی دقیق (بر مبنای تعریف «شامل ضامن‌ها») ---
    d_only = depositors - loan_all_parties - transactional
    l_only = loan_all_parties - depositors - transactional
    t_only = transactional - depositors - loan_all_parties
    d_l = (depositors & loan_all_parties) - transactional
    d_t = (depositors & transactional) - loan_all_parties
    l_t = (loan_all_parties & transactional) - depositors
    d_l_t = depositors & loan_all_parties & transactional

    overlap_table = pd.DataFrame([
        {"segment": "فقط سپرده‌گذار", "customer_count": len(d_only)},
        {"segment": "فقط تسهیلات‌گیرنده", "customer_count": len(l_only)},
        {"segment": "فقط تراکنشی/کارمزدی", "customer_count": len(t_only)},
        {"segment": "سپرده‌گذار + تسهیلات‌گیرنده (نه تراکنشی)", "customer_count": len(d_l)},
        {"segment": "سپرده‌گذار + تراکنشی (نه تسهیلات‌گیرنده)", "customer_count": len(d_t)},
        {"segment": "تسهیلات‌گیرنده + تراکنشی (نه سپرده‌گذار)", "customer_count": len(l_t)},
        {"segment": "هر سه گروه", "customer_count": len(d_l_t)},
    ])
    overlap_table["share_of_union_pct"] = (overlap_table["customer_count"] / len(all_three_ids) * 100).round(2)
    print("\n=== جدول همپوشانی دقیق سه گروه ===")
    print(overlap_table.to_string(index=False))
    print(f"\n→ {len(depositors & loan_all_parties) / len(loan_all_parties) * 100:.1f}٪ از کل تسهیلات‌گیرندگان "
          f"(شامل ضامن) سپرده‌گذار هم هستند — همان یافته‌ی ۹۹.۹٪ بخش ب.")
    print(f"→ {len(depositors & loan_primary_only) / len(loan_primary_only) * 100:.1f}٪ از گیرندگان اصلیِ رسمی "
          f"تسهیلات سپرده‌گذار هم هستند — یافته‌ی مستقل بخش ت (۲۵.۲٪).")
    print(f"→ فقط {len(transactional) / len(all_three_ids) * 100:.1f}٪ از کل جمعیت شناخته‌شده در این سه جدول، "
          f"رکورد تراکنشی/کارمزدی هم دارند — طبق docs/11، Customer_Monthly_Activity زیرمجموعه‌ای از کل است.")

    overlap_table.to_csv(PROCESSED_DIR / "customer_population_overlap.csv", index=False)
    pd.DataFrame([{
        "depositors": len(depositors),
        "loan_takers_all_parties": len(loan_all_parties),
        "loan_takers_primary_only": len(loan_primary_only),
        "transactional_customers": len(transactional),
        "union_total": len(all_three_ids),
    }]).to_csv(PROCESSED_DIR / "customer_population_summary.csv", index=False)

    # --- نمودار Venn سه‌دایره‌ای ---
    fig, ax = plt.subplots(figsize=(9, 8))
    v = venn3(
        subsets=(len(d_only), len(l_only), len(d_l), len(t_only), len(d_t), len(l_t), len(d_l_t)),
        set_labels=(fa("سپرده‌گذاران"), fa("تسهیلات‌گیرندگان\n(شامل ضامن)"), fa("مشتریان تراکنشی/کارمزدی")),
        ax=ax,
    )
    for sid in ("100", "010", "110", "001", "101", "011", "111"):
        label = v.get_label_by_id(sid)
        if label is not None:
            label.set_text(to_persian_digits(f"{int(label.get_text()):,}"))
            label.set_fontsize(9)
    for text in v.set_labels:
        if text is not None:
            text.set_fontsize(11)
    ax.set_title(fa("همپوشانی سه جمعیت اصلی مشتریان بانک (بعد از حذف کامل تکرار)"), fontsize=13)
    fig.tight_layout()
    fig.savefig(FIGURES_DIR / "customer_population_venn.png", dpi=150)
    plt.close(fig)

    print(f"\nخروجی‌ها در {PROCESSED_DIR} و {FIGURES_DIR} ذخیره شدند.")


if __name__ == "__main__":
    main()
