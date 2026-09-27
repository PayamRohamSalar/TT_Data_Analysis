import re
import warnings
from pathlib import Path
import pandas as pd
import numpy as np

# Suppress pandas warnings about openpyxl styling
warnings.filterwarnings("ignore", category=UserWarning, module="openpyxl")

# Define paths
PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_ROOT / "data" / "provinces_branches"
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed" / "phase1_market_overview"
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

MILLION = 1e6

KNOWN_PREFIX_PROVINCE = {"17": "تهران", "38": "یزد", "40": "خراسان جنوبی", "41": "البرز"}

def normalize(text: str) -> str:
    if pd.isna(text):
        return ""
    text = str(text).replace("ي", "ی").replace("ك", "ک").replace("\u200c", " ")
    text = re.sub(r"\s+", " ", text).strip()
    
    synonyms = {
        "سیستان و بلوچستان": "سیستان وبلوچستان",
        "چهارمحال و بختیاری": "چهارمحال وبختیاری",
        "کهکیلویه و بویراحمد": "کهگیلویه وبویراحمد",
        "کهگیلویه و بویراحمد": "کهگیلویه وبویراحمد",
    }
    return synonyms.get(text, text)

COLUMN_RULES = {
    "rial_resources": (lambda h: "مانده منابع ریالی" in h or ("منابع کل" in h and "ارزی" in h), True),
    "loans": (lambda h: h.startswith("مانده تسهیلات اعطایی") and "پایان" not in h, True),
    "npl": (lambda h: ("مطالبات غیرجاری" in h or "مطالبات غیر جاری" in h or h == "NPL") and "نسبت" not in h and "پایان سال" not in h, False),
    "gharz_current": (lambda h: h.endswith("قرض الحسنه جاری") or "قرض الحسنه جاری" in h, False),
    "gharz_saving": (lambda h: h.endswith("قرض الحسنه پس انداز") or "پس انداز" in h, False),
    "short_term": (lambda h: h.endswith("کوتاه مدت") or "کوتاه مدت" in h, False),
    "long_term": (lambda h: h.endswith("بلندمدت") or "بلند مدت" in h, False),
    "branch_code": (lambda h: "کد" in h and "شعبه" in h, False),
    "branch_name": (lambda h: ("نام" in h and "شعبه" in h) or h == "شعبه", False),
    "province_col": (lambda h: "استان" in h, False),
}

def report_month(sheet: pd.DataFrame, path: Path) -> int | None:
    # Look for month in first 4 rows
    title = " ".join(str(v) for v in sheet.iloc[:4, 0] if pd.notna(v))
    found = re.search(r"(1[34]\d{2})/(\d{1,2})/\d{1,2}", title)
    if found:
        return int(found.group(1)) * 100 + int(found.group(2))
    
    # Check title row if it was in col 1 or 2 (merged cells sometimes appear there)
    for c in range(1, min(3, len(sheet.columns))):
        title = " ".join(str(v) for v in sheet.iloc[:4, c] if pd.notna(v))
        found = re.search(r"(1[34]\d{2})/(\d{1,2})/\d{1,2}", title)
        if found:
            return int(found.group(1)) * 100 + int(found.group(2))
            
    digits = re.sub(r"\D", "", path.stem)
    if len(digits) >= 8:
        return int(digits[:6])
    elif len(digits) == 6:
        return int(digits)
    return None

def branch_prefix(codes: pd.Series) -> pd.Series:
    return pd.Series(np.where(codes >= 10_000, codes.astype(str), codes.astype(str).str[:2]), index=codes.index)

def parse_sheet(sheet: pd.DataFrame, is_branch_level: bool = True) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Returns parsed dataframe and the total row (if found)."""
    if is_branch_level:
        is_code_0 = pd.to_numeric(sheet[0], errors="coerce")
        is_code_1 = pd.to_numeric(sheet[1], errors="coerce")
        key_col = 0 if is_code_0.notna().sum() > is_code_1.notna().sum() else 1
    else:
        # Province level sheet, province name is usually in col 0
        key_col = 0
        
    if is_branch_level:
        is_data = pd.to_numeric(sheet[key_col], errors="coerce").notna()
    else:
        # Filter out NaN, and words like 'جمع', 'total', 'وضعیت'
        def is_valid_prov(x):
            s = normalize(str(x))
            return len(s) > 1 and "جمع" not in s and "وضعیت" not in s and "نام استان" not in s and "*" not in s and "توسعه ملی" not in s
        is_data = sheet[key_col].map(is_valid_prov) & sheet[key_col].notna()

    if not is_data.any():
        raise ValueError("داده‌ای پیدا نشد")
        
    first_data_row = int(is_data.idxmax())
    
    header = {c: normalize(" ".join(str(v) for v in sheet.iloc[:first_data_row, c] if pd.notna(v))) for c in sheet.columns}
    
    cols = {}
    for key, (rule, required) in COLUMN_RULES.items():
        match = next((c for c, h in header.items() if rule(h)), None)
        if match is not None:
            cols[key] = match
        elif required:
            # specifically for 140012 and 140111 province sheets where 'rial_resources' rule might fail
            if key == 'rial_resources':
                # Try finding any column with 'منابع' in header
                match_fallback = next((c for c, h in header.items() if "منابع" in h), None)
                if match_fallback is not None:
                    cols[key] = match_fallback
                    continue
            raise KeyError(f"ستون اجباری «{key}» پیدا نشد. سرستون‌ها: {header}")

    data = sheet[is_data].copy()
    
    result = pd.DataFrame()
    if is_branch_level:
        code_col = cols.get("branch_code", key_col)
        name_col = cols.get("branch_name", key_col + 1)
        result["branch_code"] = pd.to_numeric(data[code_col]).astype(int)
        result["branch_name"] = data[name_col].map(normalize)
        
        if "province_col" in cols:
            province_series = sheet[cols["province_col"]].ffill()
            result["province"] = province_series[is_data].map(normalize)
    else:
        prov_col = cols.get("province_col", key_col)
        result["province"] = data[prov_col].map(normalize)
        
    for k, c in cols.items():
        if k not in ["branch_code", "branch_name", "province_col"]:
            result[k] = pd.to_numeric(data[c], errors="coerce").fillna(0)
            
    # Find total row
    total_row_df = pd.DataFrame()
    if "rial_resources" in cols:
        def is_total(x):
            return "جمع کل" == normalize(str(x))
        total_idx = sheet[0].map(is_total)
        if total_idx.any():
            total_row_df = pd.DataFrame({
                "rial_resources": [pd.to_numeric(sheet.loc[total_idx.idxmax(), cols["rial_resources"]], errors="coerce")]
            })

    return result, total_row_df


def main():
    print("شروع پردازش فایل‌های بانک...")
    branch_frames = []
    province_only_frames = []
    qc_failures = []
    
    # 1. Read files
    files = list(DATA_DIR.rglob("*.xls*"))
    for path in sorted(files):
        try:
            book = pd.ExcelFile(path)
            # month might be in sheet 0
            sheet0 = pd.read_excel(book, sheet_name=0, header=None)
            month = report_month(sheet0, path)
            
            if month is None or month < 140001:
                continue
                
            has_branch_level = True
            if month in [140012, 140111]:
                has_branch_level = False
                
            is_new_format = month >= 140304
            
            if is_new_format:
                df, total_row = parse_sheet(sheet0, is_branch_level=True)
                df["year_month"] = month
                df["source_format"] = "new"
                branch_frames.append(df)
                
                # QC
                if not total_row.empty:
                    file_total = total_row["rial_resources"].iloc[0]
                    calc_total = df["rial_resources"].sum()
                    if file_total:
                        diff = abs(calc_total - file_total) / file_total * 100
                        if diff > 0.01:
                            qc_failures.append(f"ماه {month}: اختلاف جمع کل شعبه‌ها ({calc_total}) با ردیف فایل ({file_total}) = {diff:.4f}%")
            else:
                if has_branch_level:
                    # Branches usually in sheet 1
                    sheet1 = pd.read_excel(book, sheet_name=1, header=None)
                    df, _ = parse_sheet(sheet1, is_branch_level=True)
                    df["year_month"] = month
                    df["source_format"] = "old"
                    
                    # Convert unit
                    for col in ["rial_resources", "loans", "npl", "gharz_current", "gharz_saving", "short_term", "long_term"]:
                        if col in df.columns:
                            df[col] = df[col] * MILLION
                    
                    branch_frames.append(df)
                else:
                    # Province only
                    df, _ = parse_sheet(sheet0, is_branch_level=False)
                    df["year_month"] = month
                    df["source_format"] = "old"
                    
                    # Convert unit
                    for col in ["rial_resources", "loans", "npl", "gharz_current", "gharz_saving", "short_term", "long_term"]:
                        if col in df.columns:
                            df[col] = df[col] * MILLION
                            
                    province_only_frames.append(df)
                    
        except Exception as e:
            print(f"خطا در پردازش {path.name}: {e}")

    all_branches = pd.concat(branch_frames, ignore_index=True)
    
    # 2. Handle branch codes (17313 -> 313, remove 100)
    all_branches["branch_code"] = all_branches["branch_code"].replace(17313, 313)
    all_branches = all_branches[all_branches["branch_code"] != 100]
    all_branches = all_branches[all_branches["branch_code"].notna()]
    
    # 3. Build province mapping (One-pass logic)
    new_format_map = all_branches[all_branches["source_format"] == "new"].dropna(subset=["province"])
    new_map_dict = new_format_map.groupby("branch_code")["province"].last().to_dict()
    new_map_dict[313] = "شعب مستقل"
    
    map_records = []
    final_map_dict = {}
    
    all_unique_codes = all_branches["branch_code"].unique()
    for code in all_unique_codes:
        if code in new_map_dict:
            prov = new_map_dict[code]
            final_map_dict[code] = prov
            
            prefix = str(code)[:2]
            fallback = "شعب مستقل" if code == 313 else KNOWN_PREFIX_PROVINCE.get(prefix, "نامشخص")
            
            if prov == fallback or fallback == "نامشخص":
                source = "direct_new_format"
            else:
                source = "backfilled_from_new"
            map_records.append({"branch_code": code, "province": prov, "source": source})
        else:
            prefix = str(code)[:2]
            fallback = KNOWN_PREFIX_PROVINCE.get(prefix, "نامشخص")
            final_map_dict[code] = fallback
            map_records.append({"branch_code": code, "province": fallback, "source": "prefix_fallback"})
            
    map_df = pd.DataFrame(map_records)
    map_df.to_csv(PROCESSED_DIR / "official_branch_province_map.csv", index=False)
    
    # Ensure all branches have a province
    all_branches["province"] = all_branches["branch_code"].map(final_map_dict)
    
    # 4. Admin units
    admin_keywords = ["مدیریت", "خزانه", "سرپرستی", "ستاد", "امور حقوقی", "بین الملل", "بین‌الملل"]
    def is_admin(name):
        n = normalize(str(name))
        return any(kw in n for kw in admin_keywords)
        
    all_branches["is_admin_unit"] = all_branches["branch_name"].map(is_admin)
    all_branches.loc[all_branches["branch_code"] == 313, "is_admin_unit"] = True
    
    # 5. Output files
    
    # Month level
    cols_to_sum = ["rial_resources", "loans", "npl", "gharz_current", "gharz_saving", "short_term", "long_term"]
    for col in cols_to_sum:
        if col not in all_branches.columns:
            all_branches[col] = 0
            
    # Add province_only data to all_branches for aggregation
    province_only_df = pd.concat(province_only_frames, ignore_index=True) if province_only_frames else pd.DataFrame()
    for col in cols_to_sum:
        if col not in province_only_df.columns:
            province_only_df[col] = 0
            
    # bank_official_monthly_by_province.csv
    prov_monthly_branch = all_branches.groupby(["year_month", "province"], as_index=False)[cols_to_sum].sum()
    prov_monthly_branch["source_format"] = all_branches.groupby(["year_month", "province"])["source_format"].first().values
    
    if not province_only_df.empty:
        # province only df has 'province', 'year_month', and cols_to_sum. 
        prov_monthly_only = province_only_df.groupby(["year_month", "province"], as_index=False)[cols_to_sum].sum()
        prov_monthly_only["source_format"] = "old"
        prov_monthly = pd.concat([prov_monthly_branch, prov_monthly_only], ignore_index=True)
    else:
        prov_monthly = prov_monthly_branch

    # Apply NaN for {140012, 140111} in prov_monthly
    special_months = [140012, 140111]
    cols_to_nan = ["npl", "gharz_current", "gharz_saving", "short_term", "long_term"]
    prov_monthly.loc[prov_monthly["year_month"].isin(special_months), cols_to_nan] = np.nan
    
    # Add rial_resources_pure
    prov_monthly["rial_resources_pure"] = ~prov_monthly["year_month"].isin(special_months)
    
    # Add npl_available
    prov_monthly["npl_available"] = ~prov_monthly["year_month"].isin(special_months)

    # Add deposit_breakdown_reliable
    prov_monthly["deposit_breakdown_reliable"] = ~prov_monthly["year_month"].isin([140012, 140111, 140411, 140412])
    # Add has_branch_level_data
    prov_monthly["has_branch_level_data"] = ~prov_monthly["year_month"].isin(special_months)
    prov_monthly["n_branches_reporting"] = 0
    
    branch_counts = all_branches.groupby(["year_month", "province"])["branch_code"].count().reset_index(name="n_branches_reporting")
    prov_monthly = prov_monthly.drop(columns=["n_branches_reporting"]).merge(branch_counts, on=["year_month", "province"], how="left")
    prov_monthly["n_branches_reporting"] = prov_monthly["n_branches_reporting"].fillna(0).astype(int)
    
    prov_monthly.to_csv(PROCESSED_DIR / "bank_official_monthly_by_province.csv", index=False)
    
    bank_monthly = prov_monthly.groupby("year_month", as_index=False).agg({
        "rial_resources": "sum",
        "loans": "sum",
        "npl": "sum",
        "gharz_current": "sum",
        "gharz_saving": "sum",
        "short_term": "sum",
        "long_term": "sum",
        "n_branches_reporting": "sum"
    })
    
    # Apply NaN for {140012, 140111} in bank_monthly
    bank_monthly.loc[bank_monthly["year_month"].isin(special_months), cols_to_nan] = np.nan
    
    bank_monthly["deposit_breakdown_reliable"] = ~bank_monthly["year_month"].isin([140012, 140111, 140411, 140412])
    bank_monthly["has_branch_level_data"] = ~bank_monthly["year_month"].isin(special_months)
    bank_monthly["rial_resources_pure"] = ~bank_monthly["year_month"].isin(special_months)
    bank_monthly["npl_available"] = ~bank_monthly["year_month"].isin(special_months)
    
    # source_format for bank level
    source_format_map = prov_monthly.groupby("year_month")["source_format"].first().to_dict()
    bank_monthly["source_format"] = bank_monthly["year_month"].map(source_format_map)
    
    bank_monthly = bank_monthly.sort_values("year_month").reset_index(drop=True)
    bank_monthly.to_csv(PROCESSED_DIR / "bank_official_monthly.csv", index=False)
    
    # bank_official_monthly_by_branch.csv
    branch_export = all_branches[["year_month", "branch_code", "province", "rial_resources", "loans", "npl", "gharz_current", "gharz_saving", "short_term", "long_term", "is_admin_unit"]].copy()
    branch_export.to_csv(PROCESSED_DIR / "bank_official_monthly_by_branch.csv", index=False)
    
    # 6. Printing Control Table
    print("\n--- معیارهای تحویل ---")
    
    # 1. Row count
    print(f"1. تعداد ردیف bank_official_monthly.csv: {len(bank_monthly)} (مورد انتظار: 60)")
    
    # 2. Gaps
    expected_months = []
    for y in range(1400, 1405):
        for m in range(1, 13):
            expected_months.append(y * 100 + m)
    missing = set(expected_months) - set(bank_monthly["year_month"])
    print(f"2. ماه‌های جاافتاده: {sorted(list(missing)) if missing else 'هیچ (بدون شکاف)'}")
    
    # 3. 140312
    row_140312 = bank_monthly[bank_monthly["year_month"] == 140312]
    if not row_140312.empty:
        r = row_140312.iloc[0]
        npl_ratio = (r['npl'] / r['loans'] * 100) if r['loans'] else 0
        print(f"3. ماه 140312: منابع={r['rial_resources']:,.0f}, مصارف={r['loans']:,.0f}, NPL={r['npl']:,.0f} (نسبت NPL: {npl_ratio:.2f}%)")
    
    # 4. 140412
    row_140412 = bank_monthly[bank_monthly["year_month"] == 140412]
    if not row_140412.empty:
        r = row_140412.iloc[0]
        npl_ratio = (r['npl'] / r['loans'] * 100) if r['loans'] else 0
        print(f"4. ماه 140412: منابع={r['rial_resources']:,.0f}, مصارف={r['loans']:,.0f}, NPL={r['npl']:,.0f} (نسبت NPL: {npl_ratio:.2f}%)")
        
    # 5. deposit_breakdown_reliable
    unreliable = bank_monthly[~bank_monthly["deposit_breakdown_reliable"]]["year_month"].tolist()
    reliable = bank_monthly[bank_monthly["deposit_breakdown_reliable"]]["year_month"].tolist()
    print(f"5. ماه‌های نامعتبر تفکیک سپرده: {unreliable} (مورد انتظار: 140012, 140111, 140411, 140412) - بقیه {len(reliable)} ماه معتبرند.")
    
    # 6. has_branch_level_data
    no_branch = bank_monthly[~bank_monthly["has_branch_level_data"]]["year_month"].tolist()
    print(f"6. ماه‌های فاقد دیتای شعبه: {no_branch} (مورد انتظار: 140012, 140111)")
    
    # 6.1 flags check
    not_pure = bank_monthly[~bank_monthly["rial_resources_pure"]]["year_month"].tolist()
    no_npl = bank_monthly[~bank_monthly["npl_available"]]["year_month"].tolist()
    print(f"6.1. ماه‌های با منابع ناخالص (ارزی+ریالی): {not_pure} | فاقد NPL: {no_npl} (مورد انتظار: 140012, 140111)")
    
    # 7. Map checks
    code_313_prov = map_df[map_df["branch_code"] == 313]["province"].iloc[0] if 313 in map_df["branch_code"].values else "یافت نشد"
    alborz_backfills = map_df[(map_df["province"] == "البرز") & (map_df["source"] == "backfilled_from_new")]
    print(f"7. استان کد 313: {code_313_prov} | تعداد کدهای البرز با source=backfilled_from_new: {len(alborz_backfills)}")
    
    # 8. QC limits
    if qc_failures:
        print("8. خطاهای جمع کل (اختلاف > 0.01%):")
        for f in qc_failures:
            print(f"   {f}")
    else:
        print("8. تطابق جمع کل شعب و فایل در تمامی ماه‌های قالب جدید (اختلاف < 0.01%).")
        
    # 9. Province counts
    prov_counts = prov_monthly.groupby("year_month")["province"].nunique()
    abnormal_provs = prov_counts[prov_counts != 31]
    if not abnormal_provs.empty:
        print("\n9. ماه‌هایی با تعداد استان غیر از 31:")
        for y_m, c in abnormal_provs.items():
            print(f"   ماه {y_m}: {c} استان")
    else:
        print("\n9. تمامی ماه‌ها دقیقاً 31 استان دارند.")
        
    # 10. Non-province share
    non_prov_names = ["ستاد", "ستاد-امورمالی", "شعب مستقل"]
    print("\n10. سهم غیراستانی (ستاد/شعب مستقل) از کل منابع ریالی:")
    for m in [140001, 140212, 140304, 140412]:
        pm = prov_monthly[prov_monthly["year_month"] == m]
        non_prov_res = pm[pm["province"].isin(non_prov_names)]["rial_resources"].sum()
        bm = bank_monthly[bank_monthly["year_month"] == m]
        if not bm.empty:
            total_res = bm["rial_resources"].iloc[0]
            pct = (non_prov_res / total_res * 100) if total_res else 0
            print(f"   ماه {m}: {pct:.2f}% ({non_prov_res:,.0f} ریال)")

if __name__ == "__main__":
    main()
