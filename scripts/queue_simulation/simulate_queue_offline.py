from __future__ import annotations

import argparse
import csv
import json
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from statistics import median
from typing import Dict, List, Optional, Tuple


BAND_FLOORS = {
    6: 700000.0,
    5: 300000.0,
    4: 150000.0,
    3: 50000.0,
    2: 10000.0,
    1: 0.0,
}

DEFAULT_BAND_HOURS = {
    6: 1,
    5: 2,
    4: 3,
    3: 4,
    2: 8,
    1: 12,
}

DEFAULT_NORMAL_QUOTAS = {
    6: 8,
    5: 8,
    4: 8,
    3: 7,
    2: 7,
    1: 6,
}

VIDEO_AGE_BUCKETS = ("new_0_3d", "recent_4_7d", "warm_8_30d", "old_30d_plus")


UTC = timezone.utc


def parse_datetime(value: Optional[str]) -> Optional[datetime]:
    if not value:
        return None

    normalized = value.strip().replace("Z", "+00:00")

    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError:
        return None

    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=UTC)

    return parsed.astimezone(UTC)


def parse_bool(value: Optional[str], default: bool = True) -> bool:
    if value is None or value == "":
        return default

    normalized = value.strip().lower()
    if normalized in {"true", "t", "1", "yes", "y"}:
        return True
    if normalized in {"false", "f", "0", "no", "n"}:
        return False

    return default


def parse_band_map(raw: str, label: str) -> Dict[int, int]:
    result: Dict[int, int] = {}

    for part in raw.split(","):
        chunk = part.strip()
        if not chunk:
            continue

        if "=" not in chunk:
            raise ValueError(f"{label} invalido: {chunk}")

        band_str, value_str = chunk.split("=", 1)
        band = int(band_str.strip())
        value = int(value_str.strip())

        if band < 1 or band > 6:
            raise ValueError(f"{label} com banda fora do intervalo 1-6: {band}")

        result[band] = value

    missing = {1, 2, 3, 4, 5, 6} - set(result)
    if missing:
        raise ValueError(
            f"{label} incompleto. Bandas ausentes: {sorted(missing)}"
        )

    return result


def format_dt(value: Optional[datetime]) -> str:
    if value is None:
        return ""
    return value.astimezone(UTC).isoformat()


def calculate_priority_band(priority_score: float) -> int:
    if priority_score >= 700000:
        return 6
    if priority_score >= 300000:
        return 5
    if priority_score >= 150000:
        return 4
    if priority_score >= 50000:
        return 3
    if priority_score >= 10000:
        return 2
    return 1


def calculate_check_band(total_checks: int) -> str:
    if total_checks < 3:
        return "needs_coverage"
    if total_checks <= 49:
        return "covered_3_49"
    if total_checks <= 199:
        return "overchecked_50_199"
    if total_checks <= 499:
        return "overchecked_200_499"
    return "overchecked_500_plus"


def calculate_video_age_bucket(post_date: Optional[datetime], now: datetime) -> str:
    if post_date is None:
        return "old_30d_plus"

    age_days = (now - post_date).total_seconds() / 86400.0

    if age_days <= 3:
        return "new_0_3d"
    if age_days <= 7:
        return "recent_4_7d"
    if age_days <= 30:
        return "warm_8_30d"
    return "old_30d_plus"


@dataclass
class SimulationConfig:
    batch_size: int
    guardrail_slots: int
    duration_hours: int
    new_post_interval_hours: int
    band_hours: Dict[int, int]
    normal_quotas: Dict[int, int]
    warm_high_hours: int
    warm_low_hours: int
    old_all_hours: int


@dataclass
class QueuePost:
    post_id: str
    priority_score: float
    created_at: datetime
    post_date: datetime
    total_checks: int
    last_checked: Optional[datetime]
    next_check: datetime
    needs_update: bool
    failure_status: str
    is_synthetic: bool = False

    def priority_band(self) -> int:
        return calculate_priority_band(self.priority_score)

    def video_age_bucket(self, now: datetime) -> str:
        return calculate_video_age_bucket(self.post_date, now)

    def check_band(self) -> str:
        return calculate_check_band(self.total_checks)

    def staleness_days(self, now: datetime) -> float:
        anchor = self.last_checked or self.created_at
        return max((now - anchor).total_seconds() / 86400.0, 0.0)

    def to_row(self, now: datetime) -> Dict[str, str]:
        return {
            "post_id": self.post_id,
            "priority_score": f"{self.priority_score:.2f}",
            "priority_band": str(self.priority_band()),
            "video_age_bucket": self.video_age_bucket(now),
            "check_band": self.check_band(),
            "total_checagens": str(self.total_checks),
            "last_checked": format_dt(self.last_checked),
            "next_check": format_dt(self.next_check),
            "created_at": format_dt(self.created_at),
            "post_date": format_dt(self.post_date),
            "failure_status": self.failure_status,
            "needs_update": str(self.needs_update).lower(),
            "is_synthetic": str(self.is_synthetic).lower(),
        }


def calculate_next_check(
    post: QueuePost,
    checked_at: datetime,
    config: SimulationConfig,
) -> datetime:
    band = post.priority_band()
    base_next_check = checked_at + timedelta(hours=config.band_hours[band])
    video_age_bucket = post.video_age_bucket(checked_at)

    if post.total_checks < 3:
        return base_next_check

    if video_age_bucket in {"new_0_3d", "recent_4_7d"}:
        return base_next_check

    if video_age_bucket == "warm_8_30d":
        if band in {5, 6}:
            return max_datetime(
                base_next_check,
                checked_at + timedelta(hours=config.warm_high_hours),
            )
        return max_datetime(
            base_next_check,
            checked_at + timedelta(hours=config.warm_low_hours),
        )

    if video_age_bucket == "old_30d_plus":
        return max_datetime(
            base_next_check,
            checked_at + timedelta(hours=config.old_all_hours),
        )

    return base_next_check


def max_datetime(first: datetime, second: datetime) -> datetime:
    if first >= second:
        return first
    return second


def load_posts(snapshot_path: Path) -> List[QueuePost]:
    rows: List[QueuePost] = []

    with snapshot_path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        for raw in reader:
            post_id = (raw.get("post_id") or "").strip()
            if not post_id:
                continue

            failure_status = (raw.get("failure_status") or "active").strip() or "active"
            if failure_status == "unavailable":
                continue

            created_at = parse_datetime(raw.get("created_at"))
            post_date = parse_datetime(raw.get("post_date"))
            last_checked = parse_datetime(raw.get("last_checked"))
            next_check = parse_datetime(raw.get("next_check"))

            if created_at is None:
                created_at = last_checked or next_check or datetime.now(UTC)
            if post_date is None:
                post_date = created_at
            if next_check is None:
                next_check = last_checked or created_at

            rows.append(
                QueuePost(
                    post_id=post_id,
                    priority_score=float(raw.get("priority_score") or 0.0),
                    created_at=created_at,
                    post_date=post_date,
                    total_checks=int(raw.get("total_checagens") or raw.get("total_checks") or 0),
                    last_checked=last_checked,
                    next_check=next_check,
                    needs_update=parse_bool(raw.get("needs_update"), default=True),
                    failure_status=failure_status,
                    is_synthetic=False,
                )
            )

    return rows


def infer_start_time(posts: List[QueuePost]) -> datetime:
    anchors: List[datetime] = []
    for post in posts:
        anchors.append(post.created_at)
        anchors.append(post.post_date)
        anchors.append(post.next_check)
        if post.last_checked is not None:
            anchors.append(post.last_checked)

    latest = max(anchors) if anchors else datetime.now(UTC)
    return latest.replace(minute=0, second=0, microsecond=0)


def build_new_post_band_profile(
    posts: List[QueuePost],
    now: datetime,
) -> List[Tuple[int, float, float]]:
    scores_by_band: Dict[int, List[float]] = {band: [] for band in range(1, 7)}

    for post in posts:
        if post.failure_status == "unavailable" or not post.needs_update:
            continue
        bucket = post.video_age_bucket(now)
        if bucket not in {"new_0_3d", "recent_4_7d"}:
            continue
        scores_by_band[post.priority_band()].append(post.priority_score)

    total_recent = sum(len(scores) for scores in scores_by_band.values())
    if total_recent == 0:
        weights = {
            1: 0.40,
            2: 0.30,
            3: 0.15,
            4: 0.10,
            5: 0.04,
            6: 0.01,
        }
    else:
        weights = {
            band: len(scores_by_band[band]) / total_recent for band in range(1, 7)
        }

    profile: List[Tuple[int, float, float]] = []
    cumulative = 0.0
    for band in range(1, 7):
        cumulative += weights.get(band, 0.0)
        band_scores = scores_by_band[band]
        if band_scores:
            representative_score = float(median(band_scores))
        else:
            representative_score = BAND_FLOORS[band]
        profile.append((band, cumulative, representative_score))

    if profile:
        last_band, _, last_score = profile[-1]
        profile[-1] = (last_band, 1.0, last_score)

    return profile


def deterministic_band_choice(
    index: int,
    profile: List[Tuple[int, float, float]],
) -> Tuple[int, float]:
    if not profile:
        return 1, 0.0

    probe = ((index % 100) + 0.5) / 100.0

    for band, cumulative, representative_score in profile:
        if probe <= cumulative:
            return band, representative_score

    band, _, representative_score = profile[-1]
    return band, representative_score


def inject_new_posts(
    posts: List[QueuePost],
    now: datetime,
    next_index: int,
    profile: List[Tuple[int, float, float]],
) -> int:
    band, score = deterministic_band_choice(next_index, profile)
    post_id = f"synthetic-{now.strftime('%Y%m%d%H%M')}-{next_index:05d}"

    posts.append(
        QueuePost(
            post_id=post_id,
            priority_score=score,
            created_at=now,
            post_date=now,
            total_checks=0,
            last_checked=None,
            next_check=now,
            needs_update=True,
            failure_status="active",
            is_synthetic=True,
        )
    )

    return next_index + 1


def select_batch(
    posts: List[QueuePost],
    now: datetime,
    config: SimulationConfig,
) -> List[QueuePost]:
    eligible = [
        post
        for post in posts
        if post.needs_update
        and post.failure_status != "unavailable"
        and post.next_check <= now
    ]

    eligible.sort(key=lambda post: post.post_id)

    guardrail_candidates = [post for post in eligible if post.total_checks < 3]
    guardrail_candidates.sort(
        key=lambda post: (
            post.total_checks,
            post.next_check,
            post.created_at,
            -post.priority_score,
            post.post_id,
        )
    )
    guardrail_slice = guardrail_candidates[: config.guardrail_slots]
    selected_ids = {post.post_id for post in guardrail_slice}

    primary_slice: List[QueuePost] = []
    for band in range(6, 0, -1):
        candidates = [
            post
            for post in eligible
            if post.total_checks >= 3
            and post.priority_band() == band
            and post.post_id not in selected_ids
        ]
        candidates.sort(
            key=lambda post: (
                post.next_check,
                post.last_checked or datetime.min.replace(tzinfo=UTC),
                post.post_id,
            )
        )
        take = config.normal_quotas[band]
        chosen = candidates[:take]
        primary_slice.extend(chosen)
        selected_ids.update(post.post_id for post in chosen)

    remaining = [post for post in eligible if post.post_id not in selected_ids]
    remaining.sort(
        key=lambda post: (
            post.next_check,
            0 if post.total_checks < 3 else 1,
            post.last_checked or datetime.min.replace(tzinfo=UTC),
            -post.priority_band(),
            post.post_id,
        )
    )

    refill_slots = max(
        config.batch_size - len(guardrail_slice) - len(primary_slice),
        0,
    )
    refill_slice = remaining[:refill_slots]

    final_batch = guardrail_slice + primary_slice + refill_slice
    return final_batch[: config.batch_size]


def summarize_posts(
    posts: List[QueuePost],
    now: datetime,
) -> List[Dict[str, str]]:
    groups: Dict[Tuple[str, str, int], Dict[str, object]] = {}

    for post in posts:
        if not post.needs_update or post.failure_status == "unavailable":
            continue

        key = (
            post.video_age_bucket(now),
            post.check_band(),
            post.priority_band(),
        )
        group = groups.setdefault(
            key,
            {
                "video_age_bucket": key[0],
                "check_band": key[1],
                "priority_band": key[2],
                "total_posts": 0,
                "posts_vencidos": 0,
                "synthetic_posts": 0,
            },
        )
        group["total_posts"] = int(group["total_posts"]) + 1
        if post.next_check <= now:
            group["posts_vencidos"] = int(group["posts_vencidos"]) + 1
        if post.is_synthetic:
            group["synthetic_posts"] = int(group["synthetic_posts"]) + 1

    rows = list(groups.values())
    rows.sort(
        key=lambda row: (
            -int(row["posts_vencidos"]),
            -int(row["total_posts"]),
            str(row["video_age_bucket"]),
            str(row["check_band"]),
            int(row["priority_band"]),
        )
    )
    return [{key: str(value) for key, value in row.items()} for row in rows]


def write_csv(path: Path, rows: List[Dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        with path.open("w", encoding="utf-8", newline="") as handle:
            handle.write("")
        return

    fieldnames = list(rows[0].keys())
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def run_simulation(
    posts: List[QueuePost],
    start_time: datetime,
    config: SimulationConfig,
) -> Tuple[List[Dict[str, str]], List[Dict[str, str]], Dict[str, object]]:
    current_time = start_time
    end_time = start_time + timedelta(hours=config.duration_hours)
    next_arrival_time = start_time + timedelta(hours=config.new_post_interval_hours)
    next_synthetic_index = 1
    profile = build_new_post_band_profile(posts, start_time)
    hourly_rows: List[Dict[str, str]] = []

    while current_time <= end_time:
        while current_time >= next_arrival_time:
            next_synthetic_index = inject_new_posts(
                posts=posts,
                now=next_arrival_time,
                next_index=next_synthetic_index,
                profile=profile,
            )
            next_arrival_time += timedelta(hours=config.new_post_interval_hours)

        due_now = sum(
            1
            for post in posts
            if post.needs_update
            and post.failure_status != "unavailable"
            and post.next_check <= current_time
        )

        batch = select_batch(posts=posts, now=current_time, config=config)
        guardrail_executed = sum(1 for post in batch if post.total_checks < 3)

        hourly_rows.append(
            {
                "simulation_hour": str(int((current_time - start_time).total_seconds() // 3600)),
                "timestamp_utc": format_dt(current_time),
                "due_now_before_batch": str(due_now),
                "batch_size_executed": str(len(batch)),
                "guardrail_executed": str(guardrail_executed),
                "synthetic_posts_so_far": str(
                    sum(1 for post in posts if post.is_synthetic)
                ),
            }
        )

        for post in batch:
            post.last_checked = current_time
            post.total_checks += 1
            post.next_check = calculate_next_check(
                post=post,
                checked_at=current_time,
                config=config,
            )

        current_time += timedelta(hours=1)

    final_summary = summarize_posts(posts=posts, now=end_time)
    overall = {
        "start_time_utc": format_dt(start_time),
        "end_time_utc": format_dt(end_time),
        "duration_hours": config.duration_hours,
        "batch_size": config.batch_size,
        "guardrail_slots": config.guardrail_slots,
        "new_post_interval_hours": config.new_post_interval_hours,
        "synthetic_posts_created": sum(1 for post in posts if post.is_synthetic),
        "total_posts_final": len(posts),
    }
    return hourly_rows, final_summary, overall


def build_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Simula offline o andamento da fila de rechecagem com entradas novas "
            "a cada 2 horas e regra de next_check configuravel por banda."
        )
    )
    parser.add_argument(
        "--input",
        required=True,
        help=(
            "CSV com snapshot da fila. Colunas minimas: post_id, priority_score, "
            "created_at, post_date, total_checagens, last_checked, next_check, "
            "needs_update, failure_status."
        ),
    )
    parser.add_argument(
        "--output-dir",
        default="scripts/queue_simulation/output",
        help="Diretorio para gravar relatorios CSV e JSON.",
    )
    parser.add_argument(
        "--hours",
        type=int,
        default=72,
        help="Duracao da simulacao em horas.",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=50,
        help="Tamanho total do batch do worker por execucao.",
    )
    parser.add_argument(
        "--guardrail-slots",
        type=int,
        default=6,
        help="Quantidade de slots reservados ao guardrail por execucao.",
    )
    parser.add_argument(
        "--new-post-interval-hours",
        type=int,
        default=2,
        help="Intervalo de entrada dos novos posts sinteticos.",
    )
    parser.add_argument(
        "--band-hours",
        default="6=1,5=2,4=3,3=4,2=8,1=12",
        help="Regra base por banda em horas. Ex.: 6=1,5=2,4=3,3=4,2=8,1=12",
    )
    parser.add_argument(
        "--normal-quotas",
        default="6=8,5=8,4=8,3=7,2=7,1=6",
        help="Cotas nominais da fila normal por banda.",
    )
    parser.add_argument(
        "--warm-high-hours",
        type=int,
        default=12,
        help="Minimo em horas para warm_8_30d coberto nas bandas 5 e 6.",
    )
    parser.add_argument(
        "--warm-low-hours",
        type=int,
        default=24,
        help="Minimo em horas para warm_8_30d coberto nas bandas 1 a 4.",
    )
    parser.add_argument(
        "--old-all-hours",
        type=int,
        default=24,
        help="Minimo em horas para old_30d_plus coberto em todas as bandas.",
    )
    parser.add_argument(
        "--start-time",
        default="",
        help=(
            "Inicio da simulacao em UTC. Se omitido, usa o maior timestamp do snapshot "
            "arredondado para a hora."
        ),
    )
    return parser


def main() -> None:
    parser = build_argument_parser()
    args = parser.parse_args()

    snapshot_path = Path(args.input)
    output_dir = Path(args.output_dir)

    config = SimulationConfig(
        batch_size=args.batch_size,
        guardrail_slots=args.guardrail_slots,
        duration_hours=args.hours,
        new_post_interval_hours=args.new_post_interval_hours,
        band_hours=parse_band_map(args.band_hours, "band-hours"),
        normal_quotas=parse_band_map(args.normal_quotas, "normal-quotas"),
        warm_high_hours=args.warm_high_hours,
        warm_low_hours=args.warm_low_hours,
        old_all_hours=args.old_all_hours,
    )

    posts = load_posts(snapshot_path)
    start_time = parse_datetime(args.start_time) if args.start_time else None
    if start_time is None:
        start_time = infer_start_time(posts)

    hourly_rows, final_summary, overall = run_simulation(
        posts=posts,
        start_time=start_time,
        config=config,
    )

    output_dir.mkdir(parents=True, exist_ok=True)
    write_csv(output_dir / "hourly_metrics.csv", hourly_rows)
    write_csv(output_dir / "final_queue_summary.csv", final_summary)

    final_queue_rows = [post.to_row(start_time + timedelta(hours=config.duration_hours)) for post in posts]
    write_csv(output_dir / "final_posts_snapshot.csv", final_queue_rows)

    report = {
        "config": {
            "batch_size": config.batch_size,
            "guardrail_slots": config.guardrail_slots,
            "duration_hours": config.duration_hours,
            "new_post_interval_hours": config.new_post_interval_hours,
            "band_hours": config.band_hours,
            "normal_quotas": config.normal_quotas,
            "warm_high_hours": config.warm_high_hours,
            "warm_low_hours": config.warm_low_hours,
            "old_all_hours": config.old_all_hours,
        },
        "overall": overall,
    }

    with (output_dir / "simulation_report.json").open("w", encoding="utf-8") as handle:
        json.dump(report, handle, ensure_ascii=True, indent=2)

    print("Simulacao concluida.")
    print(f"Inicio: {overall['start_time_utc']}")
    print(f"Fim:    {overall['end_time_utc']}")
    print(f"Posts sinteticos criados: {overall['synthetic_posts_created']}")
    print(f"Relatorios gravados em: {output_dir}")


if __name__ == "__main__":
    main()
