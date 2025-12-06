from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

plt.rcParams["font.family"] = "Tahoma"

# -------------------------------------------------------------------
#  A. BOSS GUILD SUMMARY
# -------------------------------------------------------------------
def build_boss_guild_summary(df_raw: pd.DataFrame):
    """
    input: df_raw มีคอลัมน์อย่างน้อย
        Member, Score_str, Boss_name, Time, Image

    return:
        df_summary -> ไว้ export Excel
        df_full    -> df พร้อมตัวเลขใช้ทำกราฟ
    """
    df = df_raw.copy()

    # แปลงคะแนนเป็นตัวเลข
    df["Score_num"] = df["Score_str"].str.replace(",", "", regex=False).astype("int64")
    df["Time"] = df["Time"].fillna(0).astype("int64")

    # ---------- รวมทุกบอสต่อ Member ----------
    totals = (
        df.groupby("Member")
        .agg(Total_raw=("Score_num", "sum"), Total_time=("Time", "sum"))
        .reset_index()
    )

    totals["Total_All_M"] = (totals["Total_raw"] / 1_000_000).round(2)
    totals["Avg_All_M"] = np.where(
        totals["Total_time"] > 0,
        (totals["Total_raw"] / totals["Total_time"] / 1_000_000).round(2),
        0,
    )

    sum_all_raw = totals["Total_raw"].sum()
    if sum_all_raw > 0:
        totals["CR_Total_pct"] = (totals["Total_raw"] / sum_all_raw * 100).round(1)
    else:
        totals["CR_Total_pct"] = 0.0

    # Guild average (ใช้คำนวณ Efficiency ของทั้งกิลด์)
    guild_total_raw = totals["Total_raw"].sum()
    guild_total_time = totals["Total_time"].sum()
    if guild_total_time > 0:
        guild_avg_all_M = guild_total_raw / guild_total_time / 1_000_000
    else:
        guild_avg_all_M = 0.0

    if guild_avg_all_M > 0:
        totals["Eff_All"] = (totals["Avg_All_M"] / guild_avg_all_M).round(2)
    else:
        totals["Eff_All"] = 0.0

    # ---------- รวมต่อ Member+Boss ----------
    mb_totals = (
        df.groupby(["Member", "Boss_name"])
        .agg(Boss_raw=("Score_num", "sum"), Boss_time=("Time", "sum"))
        .reset_index()
    )

    mb_totals["Total_Boss_M"] = (mb_totals["Boss_raw"] / 1_000_000).round(2)
    mb_totals["Avg_Boss_M"] = np.where(
        mb_totals["Boss_time"] > 0,
        (mb_totals["Boss_raw"] / mb_totals["Boss_time"] / 1_000_000).round(2),
        0,
    )

    # ---------- Boss Efficiency Index ----------
    boss_stat = (
        df.groupby("Boss_name")
        .agg(sum_score=("Score_num", "sum"), sum_time=("Time", "sum"))
        .reset_index()
    )
    boss_stat["Guild_Avg_Boss_M"] = np.where(
        boss_stat["sum_time"] > 0,
        boss_stat["sum_score"] / boss_stat["sum_time"] / 1_000_000,
        0,
    )

    mb_totals = mb_totals.merge(
        boss_stat[["Boss_name", "Guild_Avg_Boss_M"]],
        on="Boss_name",
        how="left",
    )

    mb_totals["Eff_Boss"] = np.where(
        mb_totals["Guild_Avg_Boss_M"] > 0,
        (mb_totals["Avg_Boss_M"] / mb_totals["Guild_Avg_Boss_M"]).round(2),
        0,
    )

    # ---------- Contribution Rate per Boss ----------
    boss_sum = df.groupby("Boss_name")["Score_num"].sum()

    def calc_cr_boss(row):
        total_boss = boss_sum.get(row["Boss_name"], 0)
        if total_boss <= 0:
            return 0.0
        return round(row["Boss_raw"] / total_boss * 100, 1)

    mb_totals["CR_Boss_pct"] = mb_totals.apply(calc_cr_boss, axis=1)

    # ---------- Best Boss per Member ----------
    best = (
        mb_totals.sort_values(["Member", "Eff_Boss"], ascending=[True, False])
        .drop_duplicates("Member")
        .loc[:, ["Member", "Boss_name"]]
        .rename(columns={"Boss_name": "Best Boss"})
    )

    # ---------- รวมข้อมูลกลับเข้า df ----------
    df = df.merge(
        totals[
            ["Member", "Total_All_M", "Avg_All_M", "CR_Total_pct", "Eff_All"]
        ],
        on="Member",
        how="left",
    )

    df = df.merge(
        mb_totals[
            [
                "Member",
                "Boss_name",
                "Total_Boss_M",
                "Avg_Boss_M",
                "CR_Boss_pct",
                "Eff_Boss",
            ]
        ],
        on=["Member", "Boss_name"],
        how="left",
    )

    df = df.merge(best, on="Member", how="left")

    # ---------- เตรียม df_summary สำหรับ Excel ----------
    df["Score_M"] = (df["Score_num"] / 1_000_000).round(2)

    df = df.sort_values(["Member", "Boss_name"])
    df["row_in_group"] = df.groupby("Member").cumcount()

    def first_row_only(col_name):
        return df.apply(
            lambda r: r[col_name] if r["row_in_group"] == 0 else "",
            axis=1,
        )

    df["Members_display"] = first_row_only("Member")
    df["Total_All_display"] = first_row_only("Total_All_M")
    df["Avg_All_display"] = first_row_only("Avg_All_M")
    df["CR_Total_display"] = first_row_only("CR_Total_pct")
    df["Eff_All_display"] = first_row_only("Eff_All")
    df["Best_Boss_display"] = first_row_only("Best Boss")

    df_summary = df[
        [
            "Members_display",
            "Score_M",
            "Boss_name",
            "Time",
            "Total_Boss_M",
            "Avg_Boss_M",
            "Total_All_display",
            "Avg_All_display",
            "CR_Boss_pct",
            "CR_Total_display",
            "Eff_Boss",
            "Eff_All_display",
            "Best_Boss_display",
            "Image",
        ]
    ].copy()

    df_summary = df_summary.rename(
        columns={
            "Members_display": "Members",
            "Score_M": "Score (M)",
            "Boss_name": "Boss_name",
            "Total_Boss_M": "Total Dmg (Boss)",
            "Avg_Boss_M": "Avg.Score (Boss)",
            "Total_All_display": "Total Dmg (All)",
            "Avg_All_display": "Avg.Score (All)",
            "CR_Boss_pct": "Contribution Rate per Boss (%)",
            "CR_Total_display": "Contribution Rate Total (%)",
            "Eff_Boss": "Boss Efficiency Index",
            "Eff_All_display": "Guild Efficiency Index",
            "Best_Boss_display": "Best Boss",
        }
    )

    # df_full (ใช้ทำกราฟ) = df แบบไม่ตัดคอลัมน์สำคัญ
    df_full = df.copy()
    return df_summary, df_full


# -------------------------------------------------------------------
#  B. CASTLE SUMMARY
# -------------------------------------------------------------------
def build_castle_summary(df_raw: pd.DataFrame):
    """
    input: df_raw มีคอลัมน์
        Member, Score_str, Boss_name (ให้ใช้เป็น Castle), Image
    ไม่มี Time -> นับจำนวนรูป = จำนวนครั้ง
    """
    df = df_raw.copy()
    df = df.rename(columns={"Boss_name": "Castle"})

    df["Score_num"] = df["Score_str"].str.replace(",", "", regex=False).astype("int64")

    # ---------- รวมทุกปราสาทต่อ Member ----------
    totals = (
        df.groupby("Member")
        .agg(Total_raw=("Score_num", "sum"), Count=("Score_num", "size"))
        .reset_index()
    )

    totals["Total_All_M"] = (totals["Total_raw"] / 1_000_000).round(2)
    totals["Avg_All_M"] = np.where(
        totals["Count"] > 0,
        (totals["Total_raw"] / totals["Count"] / 1_000_000).round(2),
        0,
    )

    sum_all_raw = totals["Total_raw"].sum()
    if sum_all_raw > 0:
        totals["CR_Total_pct"] = (totals["Total_raw"] / sum_all_raw * 100).round(1)
    else:
        totals["CR_Total_pct"] = 0.0

    guild_total_raw = totals["Total_raw"].sum()
    guild_total_count = totals["Count"].sum()
    if guild_total_count > 0:
        guild_avg_all_M = guild_total_raw / guild_total_count / 1_000_000
    else:
        guild_avg_all_M = 0.0

    if guild_avg_all_M > 0:
        totals["Eff_All"] = (totals["Avg_All_M"] / guild_avg_all_M).round(2)
    else:
        totals["Eff_All"] = 0.0

    # ---------- รวมต่อ Member+Castle ----------
    mc_totals = (
        df.groupby(["Member", "Castle"])
        .agg(Castle_raw=("Score_num", "sum"), Count=("Score_num", "size"))
        .reset_index()
    )

    mc_totals["Total_Castle_M"] = (mc_totals["Castle_raw"] / 1_000_000).round(2)
    mc_totals["Avg_Castle_M"] = np.where(
        mc_totals["Count"] > 0,
        (mc_totals["Castle_raw"] / mc_totals["Count"] / 1_000_000).round(2),
        0,
    )

    # ---------- Boss Efficiency Index (ต่อ Castle) ----------
    castle_stat = (
        df.groupby("Castle")
        .agg(sum_score=("Score_num", "sum"), Count=("Score_num", "size"))
        .reset_index()
    )
    castle_stat["Guild_Avg_Castle_M"] = np.where(
        castle_stat["Count"] > 0,
        castle_stat["sum_score"] / castle_stat["Count"] / 1_000_000,
        0,
    )

    mc_totals = mc_totals.merge(
        castle_stat[["Castle", "Guild_Avg_Castle_M"]], on="Castle", how="left"
    )

    mc_totals["Eff_Castle"] = np.where(
        mc_totals["Guild_Avg_Castle_M"] > 0,
        (mc_totals["Avg_Castle_M"] / mc_totals["Guild_Avg_Castle_M"]).round(2),
        0,
    )

    # ---------- Contribution Rate per Castle ----------
    castle_sum = df.groupby("Castle")["Score_num"].sum()

    def calc_cr_castle(row):
        total_castle = castle_sum.get(row["Castle"], 0)
        if total_castle <= 0:
            return 0.0
        return round(row["Castle_raw"] / total_castle * 100, 1)

    mc_totals["CR_Castle_pct"] = mc_totals.apply(calc_cr_castle, axis=1)

    # ---------- Best Castle per Member ----------
    best = (
        mc_totals.sort_values(["Member", "Eff_Castle"], ascending=[True, False])
        .drop_duplicates("Member")
        .loc[:, ["Member", "Castle"]]
        .rename(columns={"Castle": "Best Castle"})
    )

    # ---------- รวมกลับเข้า df ----------
    df = df.merge(
        totals[
            ["Member", "Total_All_M", "Avg_All_M", "CR_Total_pct", "Eff_All"]
        ],
        on="Member",
        how="left",
    )

    df = df.merge(
        mc_totals[
            [
                "Member",
                "Castle",
                "Total_Castle_M",
                "Avg_Castle_M",
                "CR_Castle_pct",
                "Eff_Castle",
            ]
        ],
        on=["Member", "Castle"],
        how="left",
    )

    df = df.merge(best, on="Member", how="left")

    df["Score_M"] = (df["Score_num"] / 1_000_000).round(2)
    df = df.sort_values(["Member", "Castle"])
    df["row_in_group"] = df.groupby("Member").cumcount()

    def first_row_only(col_name):
        return df.apply(
            lambda r: r[col_name] if r["row_in_group"] == 0 else "",
            axis=1,
        )

    df["Members_display"] = first_row_only("Member")
    df["Total_All_display"] = first_row_only("Total_All_M")
    df["Avg_All_display"] = first_row_only("Avg_All_M")
    df["CR_Total_display"] = first_row_only("CR_Total_pct")
    df["Eff_All_display"] = first_row_only("Eff_All")
    df["Best_Castle_display"] = first_row_only("Best Castle")

    df_summary = df[
        [
            "Members_display",
            "Score_M",
            "Castle",
            "Total_Castle_M",
            "Total_All_display",
            "Avg_All_display",
            "CR_Castle_pct",
            "CR_Total_display",
            "Eff_Castle",
            "Eff_All_display",
            "Best_Castle_display",
            "Image",
        ]
    ].copy()

    df_summary = df_summary.rename(
        columns={
            "Members_display": "Members",
            "Score_M": "Score (M)",
            "Castle": "Castle",
            "Total_Castle_M": "Total Dmg (Castle)",
            "Total_All_display": "Total Dmg (All)",
            "Avg_All_display": "Avg.Score (All)",
            "CR_Castle_pct": "Contribution Rate per Castle (%)",
            "CR_Total_display": "Contribution Rate Total (%)",
            "Eff_Castle": "Boss Efficiency Index",
            "Eff_All_display": "Guild Efficiency Index",
            "Best_Castle_display": "Best Castle",
        }
    )

    df_full = df.copy()
    return df_summary, df_full


# -------------------------------------------------------------------
#  C. กราฟ BOSS GUILD
# -------------------------------------------------------------------
def generate_boss_guild_graphs(df: pd.DataFrame, output_dir: Path):
    output_dir.mkdir(parents=True, exist_ok=True)

    # 1) CR_Total ranking (bar แนวนอน)
    cr = (
        df.groupby("Member")["CR_Total_pct"]
        .max()
        .reset_index()
        .sort_values("CR_Total_pct", ascending=False)
    )

    plt.figure(figsize=(10, max(4, len(cr) * 0.3)))
    plt.barh(cr["Member"], cr["CR_Total_pct"])
    plt.xlabel("Contribution Rate Total (%)")
    plt.title("Boss Guild - Contribution Total Ranking")
    plt.gca().invert_yaxis()
    plt.tight_layout()
    plt.savefig(output_dir / "cr_total_ranking.png")
    plt.close()

    # 2) Damage per Boss per Player (grouped bar)
    dmg = (
        df.groupby(["Member", "Boss_name"])["Score_num"]
        .sum()
        .reset_index()
    )
    dmg["Score_M"] = dmg["Score_num"] / 1_000_000

    table = (
        dmg.pivot(index="Member", columns="Boss_name", values="Score_M")
        .fillna(0)
    )

    members = table.index.tolist()
    bosses = table.columns.tolist()
    x = np.arange(len(members))
    n_boss = len(bosses)
    width = 0.8 / max(1, n_boss)

    plt.figure(figsize=(max(10, len(members) * 0.6), 6))
    for i, boss in enumerate(bosses):
        plt.bar(
            x + (i - (n_boss - 1) / 2) * width,
            table[boss],
            width,
            label=boss,
        )

    plt.xticks(x, members, rotation=45, ha="right")
    plt.ylabel("Total Damage (ล้าน)")
    plt.title("Boss Guild - Total Damage per Boss per Player")
    plt.legend(title="Boss")
    plt.tight_layout()
    plt.savefig(output_dir / "total_dmg_per_boss_per_player.png")
    plt.close()

    # 3) Contribution per Boss (bar แนวนอน แยกไฟล์)
    for boss in bosses:
        sub = dmg[dmg["Boss_name"] == boss].copy()
        if sub.empty:
            continue
        sub = sub.sort_values("Score_M", ascending=False)

        plt.figure(figsize=(8, max(4, len(sub) * 0.3)))
        plt.barh(sub["Member"], sub["Score_M"])
        plt.xlabel("Total Damage (ล้าน)")
        plt.title(f"Boss Guild - Contribution by Player ({boss})")
        plt.gca().invert_yaxis()
        plt.tight_layout()
        plt.savefig(output_dir / f"contribution_by_player_{boss}.png")
        plt.close()


# -------------------------------------------------------------------
#  D. กราฟ CASTLE
# -------------------------------------------------------------------
def generate_castle_graphs(df: pd.DataFrame, output_dir: Path):
    output_dir.mkdir(parents=True, exist_ok=True)

    # 1) CR_Total ranking
    cr = (
        df.groupby("Member")["CR_Total_pct"]
        .max()
        .reset_index()
        .sort_values("CR_Total_pct", ascending=False)
    )

    plt.figure(figsize=(10, max(4, len(cr) * 0.3)))
    plt.barh(cr["Member"], cr["CR_Total_pct"])
    plt.xlabel("Contribution Rate Total (%)")
    plt.title("Castle - Contribution Total Ranking")
    plt.gca().invert_yaxis()
    plt.tight_layout()
    plt.savefig(output_dir / "cr_total_ranking_castle.png")
    plt.close()

    # 2) Damage per Castle per Player (grouped bar)
    dmg = (
        df.groupby(["Member", "Castle"])["Score_num"]
        .sum()
        .reset_index()
    )
    dmg["Score_M"] = dmg["Score_num"] / 1_000_000

    table = (
        dmg.pivot(index="Member", columns="Castle", values="Score_M")
        .fillna(0)
    )

    members = table.index.tolist()
    castles = table.columns.tolist()
    x = np.arange(len(members))
    n_castle = len(castles)
    width = 0.8 / max(1, n_castle)

    plt.figure(figsize=(max(10, len(members) * 0.6), 6))
    for i, castle in enumerate(castles):
        plt.bar(
            x + (i - (n_castle - 1) / 2) * width,
            table[castle],
            width,
            label=castle,
        )

    plt.xticks(x, members, rotation=45, ha="right")
    plt.ylabel("Total Damage (ล้าน)")
    plt.title("Castle - Total Damage per Castle per Player")
    plt.legend(title="Castle")
    plt.tight_layout()
    plt.savefig(output_dir / "total_dmg_per_castle_per_player.png")
    plt.close()

    # 3) Contribution per Castle (by player)
    for castle in castles:
        sub = dmg[dmg["Castle"] == castle].copy()
        if sub.empty:
            continue
        sub = sub.sort_values("Score_M", ascending=False)

        plt.figure(figsize=(8, max(4, len(sub) * 0.3)))
        plt.barh(sub["Member"], sub["Score_M"])
        plt.xlabel("Total Damage (ล้าน)")
        plt.title(f"Castle - Contribution by Player ({castle})")
        plt.gca().invert_yaxis()
        plt.tight_layout()
        plt.savefig(output_dir / f"contribution_by_player_{castle}.png")
        plt.close()
