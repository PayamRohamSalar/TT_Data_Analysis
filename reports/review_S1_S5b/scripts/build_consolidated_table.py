import pandas as pd

tasks = [
    {
        'task': 'W1',
        'stage': 'S1',
        'description': 'حضور مشتری 186027389 در 12/1404 و عدم خروج در تمامی ماه‌ها',
        'claimed': 'حاضر در همه‌ی ماه‌ها تا 12/1404؛ 328,117 حساب؛ مانده 4.605e10 ریال',
        'reproduced': 'حاضر در 72 ماه؛ 328,117 حساب؛ مانده 46,050,660,000 ریال؛ اصلاح اسناد تایید شد',
        'status': 'تأیید کامل (انطباق ۱۰۰٪)',
        'script': 'reports/review_S1_S5b/scripts/w01_check_customer_186027389.py, w01b_verify_186027389_data.py'
    },
    {
        'task': 'W2',
        'stage': 'S1',
        'description': 'صحت قاعده‌ی گیرنده‌ی استنتاجی روی قراردادهای تک‌طرفه دارای شناسنامه',
        'claimed': '315,146 از 315,146 قرارداد تک‌طرفه برابر MAIN_CUSTOMER_ID (دقت 100%)',
        'reproduced': '315,146 منطبق، 0 مغایرت از 315,146 قرارداد فعال دارای شناسنامه (100.0%)',
        'status': 'تأیید کامل (انطباق ۱۰۰٪)',
        'script': 'reports/review_S1_S5b/scripts/w02_test_loan_contract_parties_active.py'
    },
    {
        'task': 'W3',
        'stage': 'S4b',
        'description': 'رتبه‌بندی روش‌های S4b در کارت امتیاز نگارش ۲',
        'claimed': 'M2 بوردا 1.25؛ M3 بوردا 2.00؛ انطباق جدول گزارش با CSV',
        'reproduced': 'M2 بوردا 1.25 (رتبه‌های 2، 1، 1، 1)؛ M3 بوردا 2.00 (رتبه‌های 1، 2، 2، 3)؛ انطباق کامل',
        'status': 'تأیید کامل (انطباق ۱۰۰٪)',
        'script': 'reports/review_S1_S5b/scripts/w03_check_s4b_scorecard.py'
    },
    {
        'task': 'W4',
        'stage': 'S1-S4',
        'description': 'تغییر نام راکد/خروج به کم‌فعال شدن و غیبت واقعی مشتریان ۱۴۰۳ در ۱۴۰۴',
        'claimed': 'فقط 20 از 591,369 مشتری مدل 1403 در 1404 غایب‌اند؛ تغییر نام در اسناد',
        'reproduced': 'دقیقاً 20 مشتری غایب؛ 32,541 نفر به idle_token تبدیل شدند؛ در S4 هنوز در خطوط 25 و 63 واژه خروج مانده',
        'status': 'تأیید با ملاحظه جزئی نگارشی',
        'script': 'reports/review_S1_S5b/scripts/w04_check_churn_and_absence.py, w04_inspect_reports_terminology.py'
    },
    {
        'task': 'W5',
        'stage': 'S5',
        'description': 'شمار گروه‌های جمعیتی سال 1404 در پانل سالانه',
        'claimed': 'مدل 636,016؛ بی‌فعالیت 66,191؛ نوپا 10,126؛ نهادی 574؛ سایر 1؛ گروه T برابر 101,399؛ اصلی 534,617',
        'reproduced': 'مدل 636,016؛ بی‌فعالیت 66,191؛ نوپا 10,126؛ نهادی 574؛ سایر 1؛ T=101,399؛ اصلی 534,617',
        'status': 'تأیید کامل (انطباق ۱۰۰٪)',
        'script': 'reports/review_S1_S5b/scripts/w05_verify_population_counts.py'
    },
    {
        'task': 'W6',
        'stage': 'S5',
        'description': 'بازتولید مستقل گروه T و تحلیل حساسیت آستانه‌ها',
        'claimed': 'T = 101,399؛ حساسیت به 2 و 4 ماه و 2 و 10 میلیون ریال',
        'reproduced': 'T بازتولید شد (101,399)؛ حساسیت شدید به مانده (63k در 2M تا 134k در 10M) و حساسیت کم به ماه‌ها',
        'status': 'تأیید کامل (انطباق ۱۰۰٪)',
        'script': 'reports/review_S1_S5b/scripts/w06_test_group_t_sensitivity.py'
    },
    {
        'task': 'W7',
        'stage': 'S5',
        'description': 'اندازه خوشه‌های نهایی C1 تا C8 و مجموع',
        'claimed': 'C1 67,566; C2 76,683; C3 92,179; C4 30,275; C5 97,212; C6 43,250; C7 44,917; C8 82,535; جمع 534,617',
        'reproduced': 'تمامی خوشه‌ها با اختلاف 0 بازتولید شدند؛ مجموع خوشه‌های اصلی دقیقاً 534,617',
        'status': 'تأیید کامل (انطباق ۱۰۰٪)',
        'script': 'reports/review_S1_S5b/scripts/w07_verify_cluster_sizes.py'
    },
    {
        'task': 'W8',
        'stage': 'S5',
        'description': 'سهم سپرده/تسهیلات/غیرجاری خوشه‌ها و ارقام کنترل بانک',
        'claimed': 'سپرده 84.77 همت؛ تسهیلات منتسب 124.97 (99.45+25.52)؛ غیرجاری 10.66 همت؛ C1: 60.8%، 51.4%، 37.5%؛ T: 8.7%، 30.1%',
        'reproduced': 'سپرده 84.77؛ تسهیلات 124.97 (99.45 قراردادی + 25.52 استنتاجی)؛ غیرجاری 10.66 همت؛ C1 و T کاملاً منطبق',
        'status': 'تأیید کامل (انطباق ۱۰۰٪)',
        'script': 'reports/review_S1_S5b/scripts/w08_check_cluster_profiles.py, w08b_verify_loan_totals.py'
    },
    {
        'task': 'W9',
        'stage': 'S5',
        'description': 'انتخاب k در S5: پایداری نیم‌نمونه، پایداری زمانی و DB برای k=6 تا 10',
        'claimed': 'k=8: ARI نیم‌نمونه 0.986؛ زمانی 0.811؛ DB 1.81؛ سهم خوشه کمینه 5.7%',
        'reproduced': 'k=8: نیم‌نمونه 0.9855؛ زمانی 0.8112؛ DB 1.8101؛ کمینه 5.66%؛ k=7 پایداری زمانی ضعیف 0.535 دارد',
        'status': 'تأیید کامل (انطباق ۱۰۰٪)',
        'script': 'reports/review_S1_S5b/scripts/w09_check_kselect.py, w09_reproduce_kselect_stability.py'
    },
    {
        'task': 'W10',
        'stage': 'S5',
        'description': 'وفاداری درخت جانشین در عمق‌های 4، 6، 8، 10',
        'claimed': 'وفاداری 0.76، 0.84، 0.87، 0.89',
        'reproduced': 'عمق 4: 0.7580 (0.76)؛ عمق 6: 0.8342 (0.84)؛ عمق 8: 0.8662 (0.87)؛ عمق 10: 0.8874 (0.89)',
        'status': 'تأیید کامل (انطباق ۱۰۰٪)',
        'script': 'reports/review_S1_S5b/scripts/w10_to_w12_tree_fidelity_ari_prep.py'
    },
    {
        'task': 'W11',
        'stage': 'S5',
        'description': 'شاخص ARI خوشه‌های نهایی در برابر M1 و M2',
        'claimed': 'ARI اصلی در برابر M1 برابر 0.22؛ در برابر M2 (k=7) برابر 0.32',
        'reproduced': 'اصلی در برابر M1: 0.2185 (0.22)؛ اصلی در برابر M2: 0.3214 (0.32)',
        'status': 'تأیید کامل (انطباق ۱۰۰٪)',
        'script': 'reports/review_S1_S5b/scripts/w10_to_w12_tree_fidelity_ari_prep.py'
    },
    {
        'task': 'W12',
        'stage': 'S5',
        'description': 'بررسی نشت اطلاعات در prep_spec_v2.json و تأثیر سالانه‌سازی',
        'claimed': 'پارامترهای برازش فقط از 1404؛ سالانه‌سازی گردش برای ماه‌های کمتر از 12',
        'reproduced': 'بدون نشت؛ پارامترها صرفاً روی 1404؛ 16,752 مشتری (3.13%) مشمول فاکتور 1.09 تا 2.0؛ بدون اثر بر نوپا',
        'status': 'تأیید کامل (انطباق ۱۰۰٪)',
        'script': 'reports/review_S1_S5b/scripts/w12_inspect_prep_details.py, w12_check_annualization_impact.py'
    },
    {
        'task': 'W13',
        'stage': 'S5b',
        'description': 'محاسبه دقیق DPD جلالی و تحلیل ناهنجاری دفتر اقساط',
        'claimed': 'تأخیر>30 روز 28.7%؛ >90 روز 6.9%؛ هر تأخیر 57.9%؛ همه اقساط payed_date دارند',
        'reproduced': 'نمونه 10k انطباق 100% با میلادی (خطا=0)؛ کل 14.78M قسط دارای تاریخ پرداخت؛ تأخیر 57.89%؛ >30 روز 28.68%؛ >90 روز 6.89%',
        'status': 'تأیید کامل (انطباق ۱۰۰٪)',
        'script': 'reports/review_S1_S5b/scripts/w13_verify_jalali_dpd.py, audit_ledger_table.py'
    },
    {
        'task': 'W14',
        'stage': 'S5b',
        'description': 'لنز سپرده: اندازه خوشه‌ها و سهم از مانده سپرده/تسهیلات',
        'claimed': '143,619 / 187,879 / 158,197 / 42,143 / 104,178؛ سهم سپرده: 95.8% / 0.7% / 3.0% / 0.5% / 0.0%',
        'reproduced': 'اندازه‌ها دقیقاً منطبق؛ سهم سپرده: 95.85% / 0.65% / 2.95% / 0.53% / 0.01%',
        'status': 'تأیید کامل (انطباق ۱۰۰٪)',
        'script': 'reports/review_S1_S5b/scripts/w14_w15_print_tables.py'
    },
    {
        'task': 'W15',
        'stage': 'S5b',
        'description': 'لنز اعتبار: اندازه خوشه‌ها، نسبت غیرجاری و سهم غیرجاری',
        'claimed': 'اندازه‌ها: 150k/64k/125k/16k/18k؛ نسبت NPL: 1.0/21.5/0.7/21.3/52.6%؛ سهم: 6.5/23.7/0.9/43.5/25.4%؛ مجموع 2،4،5 برابر 92.6%',
        'reproduced': 'ارقام دقیقاً منطبق؛ سهم غیرجاری خوشه‌های 2، 4، 5 مجموعاً 92.57% (92.6%) در 26.27% وام‌گیران',
        'status': 'تأیید کامل (انطباق ۱۰۰٪)',
        'script': 'reports/review_S1_S5b/scripts/w14_w15_print_tables.py'
    },
    {
        'task': 'W16',
        'stage': 'S5b',
        'description': 'سنجش واریانس تفکیک ناشی از پرچم‌های گمشدگی در لنز اعتبار',
        'claimed': 'بررسی اثر no_ledger و no_contract_attr؛ برازش بدون پرچم‌ها',
        'reproduced': 'پرچم‌ها 50.12% کل واریانس جدایی را می‌سازند؛ با حذف آن‌ها ARI با مدل اصلی به 0.2803 سقوط می‌کند (خوشه‌های 4 و 5 ساختگی‌اند)',
        'status': 'یافته تحلیلی انتقادی (ضعف متدولوژی اثبات شد)',
        'script': 'reports/review_S1_S5b/scripts/w16_credit_lens_flags_audit.py'
    },
    {
        'task': 'W17',
        'stage': 'S5b',
        'description': 'شاخص AUC بیرونی لنزهای اعتبار و سپرده با اعتبارسنجی متقاطع',
        'claimed': 'لنز اعتبار: ورود به غیرجاری 0.556؛ دیرکرد سال بعد 0.525؛ لنز سپرده: کم‌فعال شدن 0.772',
        'reproduced': 'لنز اعتبار: 0.5558 و 0.5250؛ لنز سپرده: 0.7720؛ انطباق کامل',
        'status': 'تأیید کامل (انطباق ۱۰۰٪)',
        'script': 'reports/review_S1_S5b/scripts/w17_w18_verify_auc_and_ari.py'
    },
    {
        'task': 'W18',
        'stage': 'S5b',
        'description': 'شاخص ARI لنزها با خوشه‌بندی اصلی و ماتریس‌های عبور',
        'claimed': 'ARI لنز سپرده با اصلی 0.28؛ لنز اعتبار با اصلی 0.06',
        'reproduced': 'ARI سپرده با اصلی: 0.2839 (0.28)؛ ARI اعتبار با اصلی: 0.0589 (0.06)؛ ماتریس‌های عبور بازتولید شدند',
        'status': 'تأیید کامل (انطباق ۱۰۰٪)',
        'script': 'reports/review_S1_S5b/scripts/w17_w18_verify_auc_and_ari.py'
    }
]

df = pd.DataFrame(tasks)
df.to_csv('reports/review_S1_S5b/results/consolidated_w01_to_w18_verification.csv', index=False, encoding='utf-8-sig')
print("Successfully generated reports/review_S1_S5b/results/consolidated_w01_to_w18_verification.csv")
