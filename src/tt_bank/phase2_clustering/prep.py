"""آماده‌سازی ویژگی‌های هسته‌ی زمانی (ردیف A) برای خوشه‌بندی فاز ۲.

مشخصات تبدیل (تبدیل لگاریتمی، بریدن در صدک‌های مرجع، استانداردسازی، وزن بلوک) روی جمعیت مرجع (مدل، ۱۴۰۴) برازش می‌شود
و برای همه‌ی سال‌ها بدون تغییر اعمال می‌شود تا خوشه‌ها در طول زمان قابل‌مقایسه بمانند.
ورودی: جدول features_customer_year (خروجی S2)."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
import pandas as pd

# (نام نهایی، بلوک، قاعده‌ی تبدیل از ستون‌های ذخیره‌ی ویژگی، نوع)  نوع: c=پیوسته (بریده می‌شود)، b=دودویی/کراندار
SPEC = [
    ("bal_mean_log", "size", lambda d: np.log1p(d.bal_mean_r.clip(lower=0)), "c"),
    ("bal_end_log", "size", lambda d: np.log1p(d.bal_end_r.clip(lower=0)), "c"),
    ("flow_total_log", "flow", lambda d: np.log1p((d.cr_sum_r + d.db_sum_r).clip(lower=0)), "c"),
    ("flow_ratio", "flow", lambda d: d.flow_ratio, "b"),
    ("turnover_speed_log", "flow", lambda d: np.log1p(d.turnover_speed.clip(lower=0)), "c"),
    ("net_flow_ratio", "flow", lambda d: d.net_flow_ratio, "c"),
    ("ticket_cr_log", "flow", lambda d: np.log1p(d.ticket_cr_r.clip(lower=0)), "c"),
    ("ticket_db_log", "flow", lambda d: np.log1p(d.ticket_db_r.clip(lower=0)), "c"),
    ("crn_log", "activity", lambda d: np.log1p(d.crn_sum.clip(lower=0)), "c"),
    ("dbn_log", "activity", lambda d: np.log1p(d.dbn_sum.clip(lower=0)), "c"),
    ("turn_share", "activity", lambda d: d.turn_share, "b"),
    ("bal_cv", "stability", lambda d: d.bal_cv, "c"),
    ("bal_trend", "stability", lambda d: d.bal_trend, "c"),
    ("drawdown", "stability", lambda d: d.drawdown, "b"),
    ("acc_mean_log", "structure", lambda d: np.log1p(d.acc_mean.clip(lower=0)), "c"),
    ("tenure_years", "structure", lambda d: d.tenure_months / 12.0, "c"),
    ("has_loan", "loan", lambda d: d.has_loan_dec.astype(float), "b"),
    ("loan_log", "loan", lambda d: np.log1p(d.loan_dec_r.clip(lower=0)), "c"),
    ("loan_to_dep_log", "loan", lambda d: np.log1p(d.loan_to_dep.clip(lower=0)), "c"),
    ("npl_share", "loan", lambda d: d.npl_share, "b"),
    ("n_loan_log", "loan", lambda d: np.log1p(d.n_loan_dec.clip(lower=0)), "c"),
    ("loan_months_y", "loan", lambda d: d.loan_months / 12.0, "b"),
    ("guar_log", "loan", lambda d: np.log1p(d.guar_dec_r.clip(lower=0)), "c"),
]
NAMES = [s[0] for s in SPEC]
BLOCKS = [s[1] for s in SPEC]
KIND = [s[3] for s in SPEC]


def raw_transform(df: pd.DataFrame) -> pd.DataFrame:
    """تبدیل‌های بدون پارامتر (لگاریتم و مقیاس‌دهی ساده)."""
    out = pd.DataFrame({n: fn(df).astype("float64").to_numpy() for n, _, fn, _ in SPEC}, index=df.index)
    return out.fillna(0.0)


# ستون‌های پولی که برای مقایسه‌پذیری بین سال‌ها به توزیع سال مرجع (۱۴۰۴) هم‌تراز می‌شوند (هم‌ترازی چندکی درون سال)
ALIGN_COLS = ["bal_mean_r", "bal_end_r", "cr_sum_r", "db_sum_r", "ticket_cr_r", "ticket_db_r", "loan_dec_r", "guar_dec_r"]
NQ = 1001


@dataclass
class Prep:
    lo: dict = field(default_factory=dict)
    hi: dict = field(default_factory=dict)
    mean: dict = field(default_factory=dict)
    std: dict = field(default_factory=dict)
    weight: dict = field(default_factory=dict)
    q: tuple = (0.005, 0.995)
    align: dict = field(default_factory=dict)      # {col: {year: [quantiles]}}
    ref_year: int = 1404
    annualize: bool = False   # سالانه‌سازی جمع گردش و تعداد تراکنش برای مشتریان با کمتر از 12 ماه مشاهده (نسخه‌ی 2)

    def _ann(self, df: pd.DataFrame) -> pd.DataFrame:
        if not self.annualize or "obs_months" not in df.columns:
            return df
        f = 12.0 / df.obs_months.clip(lower=1, upper=12)
        out = df.copy()
        for c in ("cr_sum_r", "db_sum_r", "crn_sum", "dbn_sum"):
            out[c] = out[c] * f
        return out

    def fit(self, ref: pd.DataFrame, block_weights: bool = True, panel: pd.DataFrame | None = None) -> "Prep":
        """ref: مدل 1404؛ panel: همه‌ی سال‌های گروه مدل برای هم‌ترازی چندکی (اختیاری)."""
        ref = self._ann(ref)
        panel = self._ann(panel) if panel is not None else None
        if panel is not None:
            grid = np.linspace(0, 1, NQ)
            for c in ALIGN_COLS:
                self.align[c] = {}
                for y, g in panel.groupby("y"):
                    v = g[c][g[c] > 0]
                    self.align[c][int(y)] = np.quantile(v, grid).tolist() if len(v) > 50 else None
        R = raw_transform(ref)
        for n, k in zip(NAMES, KIND):
            x = R[n]
            lo, hi = (x.quantile(self.q[0]), x.quantile(self.q[1])) if k == "c" else (x.min(), x.max())
            self.lo[n], self.hi[n] = float(lo), float(hi)
            xc = x.clip(lo, hi)
            self.mean[n], self.std[n] = float(xc.mean()), float(xc.std() or 1.0)
        cnt = pd.Series(BLOCKS).value_counts()
        for n, b in zip(NAMES, BLOCKS):
            self.weight[n] = float(1.0 / np.sqrt(cnt[b])) if block_weights else 1.0
        return self

    def _align(self, df: pd.DataFrame) -> pd.DataFrame:
        out = df.copy()
        for c in ALIGN_COLS:
            ref_q = np.asarray(self.align[c][self.ref_year])
            v = out[c].to_numpy().astype("float64"); res = v.copy()
            for y in out.y.unique():
                qy = self.align[c].get(int(y))
                if qy is None or int(y) == self.ref_year:
                    continue
                m = ((out.y == y) & (out[c] > 0)).to_numpy()
                res[m] = np.interp(v[m], np.asarray(qy), ref_q)
            out[c] = res
        return out

    def transform(self, df: pd.DataFrame, winsorize: bool = True, aligned: bool | None = None) -> np.ndarray:
        use = bool(self.align) if aligned is None else aligned
        df = self._ann(df)
        if use:
            df = self._align(df)
        R = raw_transform(df)
        cols = []
        for n in NAMES:
            x = R[n].to_numpy()
            if winsorize:
                x = np.clip(x, self.lo[n], self.hi[n])
            cols.append((x - self.mean[n]) / self.std[n] * self.weight[n])
        return np.column_stack(cols).astype("float32")

    def to_json(self, path: Path) -> None:
        Path(path).write_text(json.dumps(self.__dict__, ensure_ascii=False, indent=1), encoding="utf-8")

    @classmethod
    def from_json(cls, path: Path) -> "Prep":
        d = json.loads(Path(path).read_text(encoding="utf-8"))
        o = cls()
        o.__dict__.update(d)
        o.align = {c: {int(y): v for y, v in yy.items()} for c, yy in o.align.items()}
        return o
