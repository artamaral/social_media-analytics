from __future__ import annotations

import argparse
import csv
import os
import re
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable


REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_SAMPLE = REPO_ROOT / "docs" / "external_data" / "33_AMOSTRA_PILOTO_10_VIDEOS_V1.csv"
DEFAULT_OUTPUT = REPO_ROOT / "docs" / "external_data" / "38_TRANSCRICOES_90S_WHISPER_LOCAL_R1.csv"
DEFAULT_WORKDIR = REPO_ROOT / "tmp" / "whisper_pilot_90s"

OUTPUT_FIELDS = [
    "post_id",
    "video_url",
    "transcription_status",
    "input_duration_seconds",
    "transcribed_duration_seconds",
    "transcript_90s",
    "language",
    "whisper_model",
    "compute_type",
    "source_method",
    "error_message",
    "created_at",
]


@dataclass(frozen=True)
class Video:
    post_id: str
    duration_seconds: int

    @property
    def url(self) -> str:
        return f"https://www.youtube.com/watch?v={self.post_id}"

    @property
    def target_duration(self) -> int:
        return min(self.duration_seconds, 90)


def run_command(args: list[str], timeout: int) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env["PYTHONWARNINGS"] = "ignore"
    return subprocess.run(
        args,
        cwd=REPO_ROOT,
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=timeout,
        check=False,
    )


def load_primary_videos(sample_path: Path) -> list[Video]:
    with sample_path.open("r", encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))

    videos: list[Video] = []
    for row in rows:
        if not row["slot_group"].endswith("_primary"):
            continue
        duration_raw = row["duration_seconds"]
        if not duration_raw.isdigit() and row.get("selection_reason", "").isdigit():
            # Doc 33 still has two titles with unquoted commas, shifting columns.
            duration_raw = row["selection_reason"]
        videos.append(
            Video(
                post_id=row["post_id"],
                duration_seconds=int(float(duration_raw)),
            )
        )
    return videos


def ensure_runtime_imports() -> tuple[object, str]:
    try:
        import imageio_ffmpeg
        from faster_whisper import WhisperModel
    except ImportError as exc:
        raise RuntimeError(
            "Dependencias ausentes. Instale yt-dlp, faster-whisper e imageio-ffmpeg."
        ) from exc

    ffmpeg_path = imageio_ffmpeg.get_ffmpeg_exe()
    if not ffmpeg_path or not Path(ffmpeg_path).exists():
        raise RuntimeError("imageio-ffmpeg nao retornou um binario ffmpeg valido.")
    return WhisperModel, ffmpeg_path


def download_audio(video: Video, output_path: Path, ffmpeg_path: str) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_template = str(output_path.with_suffix(""))
    end_timestamp = seconds_to_timestamp(video.target_duration)
    command = build_yt_dlp_command(
        video=video,
        output_template=output_template,
        ffmpeg_path=ffmpeg_path,
        download_section=f"*00:00:00-{end_timestamp}",
    )
    result = run_command(command, timeout=240)
    if result.returncode != 0 and video.duration_seconds <= 90:
        command = build_yt_dlp_command(
            video=video,
            output_template=output_template,
            ffmpeg_path=ffmpeg_path,
            download_section=None,
        )
        result = run_command(command, timeout=240)
    if result.returncode != 0:
        detail = (result.stderr or result.stdout).strip()
        detail = re.sub(r".*RequestsDependencyWarning.*\n.*warnings\.warn\(.*\n?", "", detail)
        raise RuntimeError(detail[:1200] if detail else "yt-dlp falhou sem detalhe.")

    if not output_path.exists():
        candidates = sorted(output_path.parent.glob(f"{output_path.stem}.*"))
        if not candidates:
            raise RuntimeError("audio baixado nao foi encontrado no caminho esperado.")
        candidates[0].replace(output_path)


def build_yt_dlp_command(
    video: Video,
    output_template: str,
    ffmpeg_path: str,
    download_section: str | None,
) -> list[str]:
    command = [
        sys.executable,
        "-m",
        "yt_dlp",
        "--quiet",
        "--no-warnings",
        "--no-playlist",
        "--extract-audio",
        "--audio-format",
        "wav",
        "--audio-quality",
        "0",
        "--ffmpeg-location",
        ffmpeg_path,
        "--force-overwrites",
        "-o",
        f"{output_template}.%(ext)s",
        video.url,
    ]
    if download_section:
        command[6:6] = ["--download-sections", download_section]
    return command


def seconds_to_timestamp(seconds: int) -> str:
    minutes, remainder = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    return f"{hours:02d}:{minutes:02d}:{remainder:02d}"


def transcribe_audio(model: object, audio_path: Path, language: str) -> str:
    segments, _info = model.transcribe(str(audio_path), language=language, vad_filter=True)
    transcript = " ".join(segment.text.strip() for segment in segments if segment.text.strip())
    return " ".join(transcript.split())


def empty_row(
    video: Video,
    status: str,
    model_name: str,
    compute_type: str,
    source_method: str,
    error_message: str = "",
    transcript: str = "",
) -> dict[str, str]:
    created_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
    return {
        "post_id": video.post_id,
        "video_url": video.url,
        "transcription_status": status,
        "input_duration_seconds": str(video.duration_seconds),
        "transcribed_duration_seconds": str(video.target_duration if status in {"success", "partial"} else 0),
        "transcript_90s": transcript,
        "language": "pt",
        "whisper_model": model_name,
        "compute_type": compute_type,
        "source_method": source_method,
        "error_message": error_message,
        "created_at": created_at,
    }


def write_rows(output_path: Path, rows: Iterable[dict[str, str]]) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=OUTPUT_FIELDS, quoting=csv.QUOTE_ALL)
        writer.writeheader()
        writer.writerows(rows)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Transcreve localmente os primeiros 90s da amostra piloto com Whisper."
    )
    parser.add_argument("--sample", type=Path, default=DEFAULT_SAMPLE)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--workdir", type=Path, default=DEFAULT_WORKDIR)
    parser.add_argument("--model", default="small")
    parser.add_argument("--compute-type", default="int8")
    parser.add_argument("--language", default="pt")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    videos = load_primary_videos(args.sample)
    if len(videos) != 10:
        raise SystemExit(f"Esperados 10 videos primarios; encontrados {len(videos)}.")

    WhisperModel, ffmpeg_path = ensure_runtime_imports()
    os.environ["PATH"] = str(Path(ffmpeg_path).parent) + os.pathsep + os.environ.get("PATH", "")
    model = WhisperModel(args.model, device="cpu", compute_type=args.compute_type)

    rows: list[dict[str, str]] = []
    for index, video in enumerate(videos, start=1):
        audio_path = args.workdir / f"{index:02d}_{video.post_id}_90s.wav"
        try:
            download_audio(video, audio_path, ffmpeg_path)
            transcript = transcribe_audio(model, audio_path, args.language)
            status = "success" if transcript else "partial"
            error = "" if transcript else "transcricao vazia"
            rows.append(
                empty_row(
                    video=video,
                    status=status,
                    model_name=args.model,
                    compute_type=args.compute_type,
                    source_method="yt-dlp+faster-whisper-local",
                    error_message=error,
                    transcript=transcript,
                )
            )
        except Exception as exc:
            rows.append(
                empty_row(
                    video=video,
                    status="failed",
                    model_name=args.model,
                    compute_type=args.compute_type,
                    source_method="yt-dlp+faster-whisper-local",
                    error_message=str(exc),
                )
            )
        finally:
            if audio_path.exists():
                audio_path.unlink()
            write_rows(args.output, rows)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
