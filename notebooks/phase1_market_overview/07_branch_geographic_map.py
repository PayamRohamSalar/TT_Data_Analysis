"""
نقشه‌ی جغرافیایی توزیع و عملکرد شعب به تفکیک استان (درخواست جانبی کاربر، ۲۰۲۶-۰۹-۰۴):
دو نقشه‌ی کنار هم — رنگ‌آمیزی بر اساس نسبت NPL تسهیلات (کیفیت اعتباری) در برابر سود پرداختی سپرده
(قدرت سپرده‌ای)، به‌علاوه اندازه‌ی حباب مرکز هر استان بر اساس تعداد شعبه.

⚠️ نکات مهم:
- `Base_Branch.ProvinceName` (که در vw_Branch_Dim به city_name تغییر نام یافته) در واقع نام «شهر»
  است، نه استان (شرح کامل در docs/04_data_gap_resolution_report.md). هیچ نگاشت شهر→استان در
  دیتابیس بانک وجود ندارد؛ نگاشت زیر (CITY_TO_PROVINCE) دستی و بر مبنای جغرافیای اداری ایران ساخته
  شده است، نه داده‌ای از بانک — قبل از استفاده در گزارش نهایی، صحت آن باید بازبینی شود.
- مرز استان‌ها از منبع باز geoBoundaries (OpenStreetMap-derived, ODbL) گرفته شده، نه از بانک؛
  در data/raw/geo/iran_provinces.geojson ذخیره شده (برای بازتولید بدون اتصال اینترنت).
- «نا معلوم» (۱ شعبه) از نگاشت خارج و در نقشه نادیده گرفته می‌شود.

خروجی: reports/figures/phase1_market_overview/branch_geographic_performance_map.png
"""

import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.collections import PatchCollection
from matplotlib.patches import Polygon as MplPolygon

from tt_bank.common.persian_plot import fa, setup_persian_font, to_persian_digits
from tt_bank.db.connection import get_engine

PROJECT_ROOT = Path(__file__).resolve().parents[2]
FIGURES_DIR = PROJECT_ROOT / "reports" / "figures" / "phase1_market_overview"
GEOJSON_PATH = PROJECT_ROOT / "data" / "raw" / "geo" / "iran_provinces.geojson"
FIGURES_DIR.mkdir(parents=True, exist_ok=True)
setup_persian_font()

LATEST_MONTH = 140412

PROVINCE_FA = {
    "Tehran": "تهران", "Alborz": "البرز", "Qazvin": "قزوین", "Qom": "قم", "Markazi": "مرکزی",
    "Isfahan": "اصفهان", "Fars": "فارس", "Khuzestan": "خوزستان",
    "Kohgiluyeh and Boyer-Ahmad": "کهگیلویه و بویراحمد", "Bushehr": "بوشهر", "Hormozgan": "هرمزگان",
    "Kerman": "کرمان", "Sistan and Baluchestan": "سیستان و بلوچستان", "Yazd": "یزد",
    "South Khorasan": "خراسان جنوبی", "Razavi Khorasan": "خراسان رضوی", "North Khorasan": "خراسان شمالی",
    "Semnan": "سمنان", "Golestan": "گلستان", "Mazandaran": "مازندران", "Gilan": "گیلان",
    "Ardabil": "اردبیل", "East Azerbaijan": "آذربایجان شرقی", "West Azerbaijan": "آذربایجان غربی",
    "Zanjan": "زنجان", "Kurdistan": "کردستان", "Kermanshah": "کرمانشاه", "Ilam": "ایلام",
    "Lorestan": "لرستان", "Hamadan": "همدان", "Chaharmahal and Bakhtiari": "چهارمحال و بختیاری",
}

# ⚠️ نگاشت دستی شهر (city_name واقعی در vw_Branch_Dim) -> استان — منبع: جغرافیای اداری ایران،
# نه داده‌ی بانک (شرح در docstring بالا).
CITY_TO_PROVINCE = {
    "تهران": "Tehran", "اسلامشهر": "Tehran", "بومهن": "Tehran", "پاکدشت": "Tehran", "دماوند": "Tehran",
    "رباط کريم": "Tehran", "شهريار": "Tehran", "قدس": "Tehran", "ورامين": "Tehran", "فيروزکوه": "Tehran",
    "کرج": "Alborz", "اشتهارد": "Alborz", "نظرآباد": "Alborz", "هشتگرد": "Alborz", "طالقان": "Alborz",
    "قزوين": "Qazvin", "آبيک": "Qazvin", "بوئين زهرا": "Qazvin", "تاکستان": "Qazvin",
    "قم": "Qom",
    "اراک": "Markazi", "ساوه": "Markazi", "خمين": "Markazi", "دليجان": "Markazi", "تفرش": "Markazi",
    "شازند": "Markazi", "کميجان": "Markazi", "محلات": "Markazi", "فرمهين": "Markazi", "زرند ساوه": "Markazi",
    "اصفهان": "Isfahan", "نجف آباد": "Isfahan", "کاشان": "Isfahan", "اردستان": "Isfahan",
    "آران و بيدگل": "Isfahan", "سميرم سفلي": "Isfahan", "زرين شهر": "Isfahan", "خميني شهر": "Isfahan",
    "خوانسار": "Isfahan", "دهاقان": "Isfahan", "تيران": "Isfahan", "چادگان": "Isfahan", "نائين": "Isfahan",
    "نطنز": "Isfahan", "گلپايگان": "Isfahan", "مبارکه": "Isfahan", "شاهين شهر": "Isfahan",
    "شهرضا": "Isfahan", "فريدن": "Isfahan", "فريدون شهر": "Isfahan", "فلاور جان": "Isfahan",
    "شيراز": "Fars", "ارسنجان": "Fars", "اقليد": "Fars", "استهبان": "Fars", "آباده": "Fars",
    "داراب": "Fars", "سپيدان": "Fars", "جهرم": "Fars", "کازرون": "Fars", "قيرو کارزين": "Fars",
    "ممسني": "Fars", "مرودشت": "Fars", "لار": "Fars", "لامرد": "Fars", "ني ريز": "Fars",
    "فسا": "Fars", "فيروز آباد": "Fars",
    "اهواز": "Khuzestan", "ايذه": "Khuzestan", "اميديه": "Khuzestan", "انديمشک": "Khuzestan",
    "آبادان": "Khuzestan", "بندر ماهشهر": "Khuzestan", "بهبهان": "Khuzestan", "شادگان": "Khuzestan",
    "سوسنگرد": "Khuzestan", "خرمشهر": "Khuzestan", "دزفول": "Khuzestan", "رامهرمز": "Khuzestan",
    "لالي": "Khuzestan", "مسجد سليمان": "Khuzestan", "شوش": "Khuzestan", "شوشتر": "Khuzestan",
    "هنديجان": "Khuzestan",
    "ياسوج": "Kohgiluyeh and Boyer-Ahmad", "بهمئي کهکيلويه": "Kohgiluyeh and Boyer-Ahmad",
    "دهدشت": "Kohgiluyeh and Boyer-Ahmad", "دوگنبدان": "Kohgiluyeh and Boyer-Ahmad",
    "بوشهر": "Bushehr", "بندر ديلم": "Bushehr", "برازجان": "Bushehr", "تنگستان": "Bushehr",
    "دشتي": "Bushehr", "دير": "Bushehr", "جم": "Bushehr", "کنگان": "Bushehr", "عسلويه": "Bushehr",
    "گناوه": "Bushehr",
    "بندرعباس": "Hormozgan", "بستک": "Hormozgan", "بندرلنگه": "Hormozgan", "رودان": "Hormozgan",
    "کيش": "Hormozgan", "ميناب": "Hormozgan", "قشم": "Hormozgan",
    "کرمان": "Kerman", "سيرجان": "Kerman", "انار رفسنجان": "Kerman", "بم": "Kerman", "بافت": "Kerman",
    "بردسير": "Kerman", "جيرفت": "Kerman", "راور": "Kerman", "رفسنجان": "Kerman", "زرند": "Kerman",
    "شهر بابک": "Kerman", "کهنوج": "Kerman", "کوهبنان": "Kerman",
    "زاهدان": "Sistan and Baluchestan", "ايرانشهر": "Sistan and Baluchestan",
    "سراوان": "Sistan and Baluchestan", "زهک": "Sistan and Baluchestan", "چابهار": "Sistan and Baluchestan",
    "خاش": "Sistan and Baluchestan", "کنارک": "Sistan and Baluchestan", "زابل": "Sistan and Baluchestan",
    "يزد": "Yazd", "ابرکوه": "Yazd", "اردکان": "Yazd", "بافق": "Yazd", "تفت": "Yazd", "خاتم": "Yazd",
    "مهريز": "Yazd", "ميبد": "Yazd",
    "بيرجند": "South Khorasan", "بشرويه": "South Khorasan", "زيركوه-حاجي آباد": "South Khorasan",
    "سرايان": "South Khorasan", "نهبندان": "South Khorasan", "طبس": "South Khorasan",
    "قائن": "South Khorasan", "فردوس": "South Khorasan",
    "مشهد": "Razavi Khorasan", "بردسکن": "Razavi Khorasan", "تايباد": "Razavi Khorasan",
    "سبزوار": "Razavi Khorasan", "سرخس": "Razavi Khorasan", "تربت جام": "Razavi Khorasan",
    "تربت حيدريه": "Razavi Khorasan", "خواف": "Razavi Khorasan", "چناران": "Razavi Khorasan",
    "کاشمر": "Razavi Khorasan", "قوچان": "Razavi Khorasan", "فريمان": "Razavi Khorasan",
    "گناباد": "Razavi Khorasan", "نيشابور": "Razavi Khorasan",
    "بجنورد": "North Khorasan", "اسفراين": "North Khorasan", "جاجرم": "North Khorasan",
    "مانه و سملقان": "North Khorasan", "شيروان": "North Khorasan", "فاروج": "North Khorasan",
    "سمنان": "Semnan", "شاهرود": "Semnan", "دامغان": "Semnan", "سرخه": "Semnan",
    "مهدي شهر": "Semnan", "گرمسار": "Semnan",
    "گرگان": "Golestan", "آزادشهر": "Golestan", "آق قلا": "Golestan", "بندر ترکمن": "Golestan",
    "بندر گز": "Golestan", "راميان": "Golestan", "کرد کوی": "Golestan", "کلاله": "Golestan",
    "علی آباد کتول": "Golestan", "مينودشت": "Golestan", "گمیشان": "Golestan", "گنبدکاووس": "Golestan",
    "ساري": "Mazandaran", "قائمشهر": "Mazandaran", "بابل": "Mazandaran", "آمل": "Mazandaran",
    "بابلسر": "Mazandaran", "بهشهر": "Mazandaran", "سوادکوه": "Mazandaran", "تنکابن": "Mazandaran",
    "جويبار": "Mazandaran", "چالوس": "Mazandaran", "رامسر": "Mazandaran", "عباس آباد": "Mazandaran",
    "فريدون کنار": "Mazandaran", "محمود آباد": "Mazandaran", "نور": "Mazandaran", "نوشهر": "Mazandaran",
    "نکاء": "Mazandaran", "گلوگاه": "Mazandaran",
    "رشت": "Gilan", "املش": "Gilan", "آستارا": "Gilan", "آستانه اشرفيه": "Gilan",
    "بندر انزلي": "Gilan", "تالش": "Gilan", "رضوانشهر": "Gilan", "رودبار": "Gilan", "رودسر": "Gilan",
    "سياهکل": "Gilan", "شفت": "Gilan", "صومعه سرا": "Gilan", "لاهيجان": "Gilan", "لنگرود": "Gilan",
    "ماسال شاندرمن": "Gilan", "فومن": "Gilan",
    "اردبيل": "Ardabil", "بيله سوار": "Ardabil", "پارس آباد": "Ardabil", "خلخال": "Ardabil",
    "نمين": "Ardabil", "مشگين شهر": "Ardabil", "گرمي": "Ardabil", "نير اردبيل": "Ardabil",
    "تبريز": "East Azerbaijan", "آذرشهر": "East Azerbaijan", "اهر": "East Azerbaijan",
    "بستان آباد": "East Azerbaijan", "بناب": "East Azerbaijan", "چهار اويماق": "East Azerbaijan",
    "سراب": "East Azerbaijan", "کليبر": "East Azerbaijan", "ملکان": "East Azerbaijan",
    "ميانه": "East Azerbaijan", "هادي شهر": "East Azerbaijan", "هشترود": "East Azerbaijan",
    "مراغه": "East Azerbaijan", "مرند": "East Azerbaijan", "عجب شير": "East Azerbaijan",
    "شبستر": "East Azerbaijan", "ورزقان": "East Azerbaijan",
    "اروميه": "West Azerbaijan", "بوکان": "West Azerbaijan", "پيرانشهر": "West Azerbaijan",
    "سردشت": "West Azerbaijan", "سلماس": "West Azerbaijan", "خوي": "West Azerbaijan",
    "مهاباد": "West Azerbaijan", "مياندوآب": "West Azerbaijan", "ماکو": "West Azerbaijan",
    "نقده": "West Azerbaijan", "شاهين دژ": "West Azerbaijan",
    "زنجان": "Zanjan", "ابهر": "Zanjan", "خدابنده": "Zanjan", "خرمدره": "Zanjan",
    "طارم عليا": "Zanjan", "ماه نشان": "Zanjan",
    "سنندج": "Kurdistan", "بانه": "Kurdistan", "بيجار": "Kurdistan", "دهگلان": "Kurdistan",
    "ديواندره": "Kurdistan", "سرو آباد": "Kurdistan", "سقز": "Kurdistan", "قروه": "Kurdistan",
    "کامياران": "Kurdistan", "مريوان": "Kurdistan",
    "کرمانشاه": "Kermanshah", "اسلام آباد غرب": "Kermanshah", "پاوه": "Kermanshah",
    "سرپل ذهاب": "Kermanshah", "سنقر": "Kermanshah", "جوانرود": "Kermanshah", "قصرشیرین": "Kermanshah",
    "گيلانغرب": "Kermanshah", "صحنه": "Kermanshah", "هرسين": "Kermanshah", "کنگاور": "Kermanshah",
    "ايلام": "Ilam", "آبدانان": "Ilam", "دره شهر": "Ilam", "ايوان ايلام": "Ilam",
    "مسجد دهلران": "Ilam", "شيروان چرداول": "Ilam", "مهران": "Ilam",
    "خرم آباد": "Lorestan", "اليگودرز": "Lorestan", "ازنا": "Lorestan", "بروجرد": "Lorestan",
    "پلدختر": "Lorestan", "دورود": "Lorestan", "سلسله": "Lorestan", "کوهدشت": "Lorestan",
    "همدان": "Hamadan", "اسدآباد": "Hamadan", "بهار همدان": "Hamadan", "درگزين": "Hamadan",
    "رزن": "Hamadan", "تويسرکان": "Hamadan", "کبودر آهنگ": "Hamadan", "ملاير": "Hamadan",
    "لالجين": "Hamadan", "نهاوند": "Hamadan", "فامنين": "Hamadan",
    "شهرکرد": "Chaharmahal and Bakhtiari", "اردل": "Chaharmahal and Bakhtiari",
    "بروجن": "Chaharmahal and Bakhtiari", "بلداجي بروجن": "Chaharmahal and Bakhtiari",
    "لردگان": "Chaharmahal and Bakhtiari", "فارسان": "Chaharmahal and Bakhtiari",
    "فرخ شهر": "Chaharmahal and Bakhtiari",
}


def polygon_to_patches(geometry: dict, **kwargs) -> list[MplPolygon]:
    """یک Polygon/MultiPolygon از GeoJSON را به لیستی از matplotlib Polygon patch تبدیل می‌کند."""
    patches = []
    coords = geometry["coordinates"]
    rings = coords if geometry["type"] == "Polygon" else [ring for poly in coords for ring in poly[:1]]
    for ring in rings:
        patches.append(MplPolygon(np.array(ring), closed=True, **kwargs))
    return patches


def approx_centroid(geometry: dict) -> tuple[float, float]:
    """مرکز تقریبی (میانگین نقاط بزرگ‌ترین حلقه‌ی بیرونی) — کافی برای جای‌گذاری برچسب/حباب."""
    coords = geometry["coordinates"]
    rings = coords if geometry["type"] == "Polygon" else [poly[0] for poly in coords]
    biggest = max(rings, key=len)
    arr = np.array(biggest)
    return arr[:, 0].mean(), arr[:, 1].mean()


def main() -> None:
    engine = get_engine()

    loan_df = pd.read_sql(
        f"""
        SELECT branch_name, city_name, SUM(total_balance) AS loan_balance, SUM(total_npl_balance) AS npl_balance
        FROM dbo.vw_Loan_Remain_By_Branch_Month
        WHERE year_month = {LATEST_MONTH}
        GROUP BY branch_name, city_name
        """,
        engine,
    )
    deposit_df = pd.read_sql(
        """
        SELECT b.branch_name, b.city_name, SUM(ibs.Amount) AS deposit_interest_paid
        FROM dbo.Interset_branch_sum ibs
        JOIN dbo.vw_Branch_Dim b
            ON b.branch_code = LTRIM(RTRIM(REPLACE(REPLACE(ibs.BranchCode, CHAR(13), ''), CHAR(10), '')))
        WHERE REPLACE(REPLACE(ibs.Year_Mounth, CHAR(13), ''), CHAR(10), '') = '1404/12'
        GROUP BY b.branch_name, b.city_name
        """,
        engine,
    )
    branch_dim = pd.read_sql("SELECT branch_name, city_name FROM dbo.vw_Branch_Dim", engine).drop_duplicates()

    branches = branch_dim.merge(loan_df, on=["branch_name", "city_name"], how="left") \
        .merge(deposit_df, on=["branch_name", "city_name"], how="left")
    branches[["loan_balance", "npl_balance", "deposit_interest_paid"]] = branches[
        ["loan_balance", "npl_balance", "deposit_interest_paid"]
    ].fillna(0)

    branches["province"] = branches["city_name"].map(CITY_TO_PROVINCE)
    unmapped = branches[branches["province"].isna()]["city_name"].unique()

    # ⚠️ رفع محاسبه (بازبینی مستقل Claude Opus، ۲۰۲۶-۰۹-۱۱، بند ۲.۱۰): نسخه‌ی اول «سهم نگاشت‌نشده» را فقط
    # نسبت به مجموع پس از merge با vw_Branch_Dim محاسبه می‌کرد — که خودش از قبل فقط زیرمجموعه‌ی
    # branch-attributed است (طبق docs/05، تنها ~۴۷٪ مانده‌ی Loan_Remain اصلاً به یک شعبه وصل می‌شود؛
    # ۵۳٪ باقی، بدون هیچ branch_name، در همان مرحله‌ی merge بی‌صدا افت می‌کرد). محاسبه‌ی درست باید
    # نسبت به مبنای کل پرتفوی (۱,۲۸۱.۶ هزار میلیارد ریال، عدد تأییدشده‌ی چند سند مستقل) باشد.
    TOTAL_PORTFOLIO_BALANCE = 1_281_628_119_052_734
    total_loan_all = branches["loan_balance"].sum()
    branch_unattributed_pct = (1 - total_loan_all / TOTAL_PORTFOLIO_BALANCE) * 100
    unmapped_loan = branches.loc[branches["province"].isna(), "loan_balance"].sum()
    city_to_province_gap_pct = (unmapped_loan / total_loan_all * 100) if total_loan_all else 0.0
    total_unmapped_pct = (1 - (total_loan_all - unmapped_loan) / TOTAL_PORTFOLIO_BALANCE) * 100
    print(f"شهرهای بدون نگاشت به استان (نادیده گرفته می‌شوند): {list(unmapped)}")
    print(f"→ {branch_unattributed_pct:.1f}٪ از کل مانده‌ی تسهیلات اصلاً به هیچ شعبه‌ای وصل نیست (سؤال باز docs/05) "
          f"— این بخش از ابتدا وارد این نقشه نمی‌شود.")
    print(f"→ از میان همان بخش branch-attributed، فقط {city_to_province_gap_pct:.1f}٪ نگاشت شهر→استان ندارد.")
    print(f"→ سهم کل مانده‌ی تسهیلات که در این نقشه دیده نمی‌شود (هر دو علت): {total_unmapped_pct:.1f}٪ از کل پرتفوی.")

    prov = (
        branches.dropna(subset=["province"])
        .groupby("province")
        .agg(
            branch_count=("branch_name", "nunique"),
            loan_balance=("loan_balance", "sum"),
            npl_balance=("npl_balance", "sum"),
            deposit_interest_paid=("deposit_interest_paid", "sum"),
        )
        .reset_index()
    )
    prov["npl_ratio_pct"] = (prov["npl_balance"] / prov["loan_balance"].replace(0, np.nan) * 100).fillna(0)
    # سود سپرده به‌ازای هر شعبه (نه مجموع خام) — تهران با ۶۷ شعبه در برابر ۶-۲۴ شعبه‌ی بقیه‌ی استان‌ها،
    # مجموع خام را کاملاً می‌بلعد؛ نسخه‌ی سرانه مقایسه‌ی منصفانه‌تری بین استان‌ها می‌دهد.
    prov["deposit_interest_per_branch"] = prov["deposit_interest_paid"] / prov["branch_count"]
    print("\n=== خلاصه‌ی عملکرد به تفکیک استان (نگاشت‌شده از شهر) ===")
    print(prov.sort_values("loan_balance", ascending=False).to_string(index=False))
    prov.to_csv(PROJECT_ROOT / "data" / "processed" / "phase1_market_overview" / "branch_province_summary.csv", index=False)

    geo = json.load(open(GEOJSON_PATH, encoding="utf-8"))
    prov_lookup = prov.set_index("province").to_dict("index")

    fig, axes = plt.subplots(1, 2, figsize=(18, 9))
    panels = [
        ("npl_ratio_pct", "YlOrRd", "نسبت NPL تسهیلات (درصد) — وضعیت تسهیلات‌گیرندگان", "%", 1),
        ("deposit_interest_per_branch", "Blues", "سود سپرده به‌ازای هر شعبه (میلیارد ریال) — وضعیت سپرده‌گذاران", "", 1e9),
    ]
    for ax, (metric, cmap_name, title, unit, divisor) in zip(axes, panels):
        values = [prov_lookup.get(name, {}).get(metric, np.nan) for name in
                  [f["properties"]["shapeName"] for f in geo["features"]]]
        vals_arr = np.array(values, dtype=float)
        vmin, vmax = np.nanmin(vals_arr), np.nanmax(vals_arr)
        cmap = plt.get_cmap(cmap_name)

        patches, colors = [], []
        centroids = {}
        for feat in geo["features"]:
            name = feat["properties"]["shapeName"]
            row = prov_lookup.get(name)
            val = row[metric] if row else np.nan
            color = cmap((val - vmin) / (vmax - vmin)) if not np.isnan(val) and vmax > vmin else (0.9, 0.9, 0.9, 1)
            for patch in polygon_to_patches(feat["geometry"]):
                patches.append(patch)
                colors.append(color)
            centroids[name] = approx_centroid(feat["geometry"])

        pc = PatchCollection(patches, facecolor=colors, edgecolor="white", linewidths=0.6)
        ax.add_collection(pc)

        # ⚠️ افزودن برچسب نام استان (بازبینی مستقل Claude Opus، ۲۰۲۶-۰۹-۱۱، بند ۲.۱۰): نسخه‌ی قبلی
        # هیچ برچسبی روی نقشه نداشت — خواننده نمی‌توانست بفهمد کدام رنگ مربوط به کدام استان است.
        max_bc = prov["branch_count"].max()
        for name, (cx, cy) in centroids.items():
            bc = prov_lookup.get(name, {}).get("branch_count", 0)
            if bc:
                ax.scatter([cx], [cy], s=20 + (bc / max_bc) * 300, color="black", alpha=0.25, zorder=3)
            ax.annotate(fa(PROVINCE_FA.get(name, name)), (cx, cy), fontsize=5.5, ha="center", va="center",
                        zorder=4, color="black")

        ax.set_xlim(43, 64)
        ax.set_ylim(24, 40)
        ax.set_aspect("equal")
        ax.axis("off")
        ax.set_title(fa(title), fontsize=12)

        sm = plt.cm.ScalarMappable(cmap=cmap, norm=plt.Normalize(vmin=vmin, vmax=vmax))
        cbar = fig.colorbar(sm, ax=ax, shrink=0.6, orientation="horizontal", pad=0.02)
        cbar.ax.xaxis.set_major_locator(plt.MaxNLocator(nbins=5))
        # نکته: divisor/unit باید با آرگومان پیش‌فرض به لامبدا bind شوند، وگرنه چون matplotlib این
        # فرمتر را دیرتر (هنگام fig.savefig، بعد از پایان کل حلقه) صدا می‌زند، هر دو محور رنگ از
        # آخرین مقدار divisor/unit حلقه استفاده می‌کنند (باگ کلاسیک Late Binding closure در پایتون).
        cbar.ax.xaxis.set_major_formatter(
            lambda v, pos, divisor=divisor, unit=unit: to_persian_digits(f"{v / divisor:,.1f}") + unit
        )

    fig.suptitle(fa("توزیع جغرافیایی عملکرد شعب به تفکیک استان (اسفند ۱۴۰۴) — اندازه‌ی نقطه: تعداد شعبه"),
                 fontsize=14, y=0.98)
    # ⚠️ رفع (بازبینی مستقل Claude Opus، ۲۰۲۶-۰۹-۱۱، بند ۲.۱۰): (۱) فونت Vazirmatn گلیف فلش را رندر
    # نمی‌کند (همان مشکل قبلی ماتریس انتقال ریسک) — «→» با «به» جایگزین شد. (۲) سهم مانده‌ی نگاشت‌نشده
    # اکنون صریحاً در پانویس اعلام می‌شود، نه فقط در کنسول.
    fig.text(0.5, 0.02,
             fa(f"⚠️ نگاشت شهر به استان دستی و بر مبنای جغرافیای اداری ایران است، نه داده‌ای از بانک؛ نیازمند بازبینی. "
                f"{total_unmapped_pct:.1f}٪ از مانده‌ی کل تسهیلات (فاقد شعبه یا فاقد نگاشت شهر→استان) در این نقشه لحاظ نیست."),
              ha="center", fontsize=8, color="gray")
    fig.savefig(FIGURES_DIR / "branch_geographic_performance_map.png", dpi=160, bbox_inches="tight")
    plt.close(fig)
    print(f"\nنقشه ذخیره شد: {FIGURES_DIR / 'branch_geographic_performance_map.png'}")


if __name__ == "__main__":
    main()
