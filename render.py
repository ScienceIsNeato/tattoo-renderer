from __future__ import annotations

import argparse
import math
from dataclasses import dataclass
from pathlib import Path


CANVAS_WIDTH = 1600
CANVAS_HEIGHT = 920
COMBINED_WIDTH = 1600
COMBINED_HEIGHT = 920


@dataclass(frozen=True)
class DiffractionModel:
    wavelength: float = 18.0
    slit_separation: float = 240.0
    slit_width: float = 28.0
    gaussian_waist_angle: float = 0.55
    screen_distance: float = 520.0
    center_y: float = 460.0


MODEL = DiffractionModel()


@dataclass(frozen=True)
class ExperimentLayout:
    source_x: float = 112.0
    source_y: float = MODEL.center_y
    source_wall_x: float = 496.0
    double_wall_x: float = 831.0
    wall_width: float = 96.0
    wall_top: float = 86.0
    wall_bottom: float = 834.0
    source_slit_height: float = 41.0
    double_slit_height: float = 28.0
    projection_x: float = 1376.0
    projection_width: float = 112.0


LAYOUT = ExperimentLayout()


def clamp(value: float, minimum: float, maximum: float) -> float:
    return max(minimum, min(maximum, value))


def sinc(value: float) -> float:
    if abs(value) < 1e-9:
        return 1.0
    return math.sin(value) / value


def deterministic_noise(a: int, b: int, seed: int = 17) -> float:
    value = (a * 374761393 + b * 668265263 + seed * 2246822519) & 0xFFFFFFFF
    value = (value ^ (value >> 13)) * 1274126177 & 0xFFFFFFFF
    return ((value ^ (value >> 16)) & 0xFFFFFFFF) / 0xFFFFFFFF


def photon_amplitude(y: float, model: DiffractionModel = MODEL) -> float:
    theta = math.atan2(y - model.center_y, model.screen_distance)
    beta = math.pi * model.slit_width * math.sin(theta) / model.wavelength
    gamma = math.pi * model.slit_separation * math.sin(theta) / model.wavelength
    gaussian = math.exp(-0.5 * (theta / model.gaussian_waist_angle) ** 2)
    return 2.0 * gaussian * sinc(beta) * math.cos(gamma)


def photon_intensity(y: float, model: DiffractionModel = MODEL) -> float:
    amplitude = photon_amplitude(y, model)
    return amplitude * amplitude


def amplitude_envelope(y: float, model: DiffractionModel = MODEL) -> float:
    theta = math.atan2(y - model.center_y, model.screen_distance)
    beta = math.pi * model.slit_width * math.sin(theta) / model.wavelength
    gaussian = math.exp(-0.5 * (theta / model.gaussian_waist_angle) ** 2)
    return abs(2.0 * gaussian * sinc(beta))


def screen_bounds() -> tuple[float, float]:
    height = 742.0
    return MODEL.center_y - height / 2, height


def normalized_profile(top: float, height: float, samples: int) -> list[tuple[float, float, float]]:
    raw = [(top + height * index / (samples - 1), 0.0) for index in range(samples)]
    raw = [(y, photon_intensity(y)) for y, _ in raw]
    maximum = max(value for _, value in raw) or 1.0
    return [(y, math.sqrt(value / maximum), value / maximum) for y, value in raw]


def normalized_envelope_profile(top: float, height: float, samples: int) -> list[tuple[float, float]]:
    raw = [(top + height * index / (samples - 1), 0.0) for index in range(samples)]
    raw = [(y, amplitude_envelope(y)) for y, _ in raw]
    maximum = max(value for _, value in raw) or 1.0
    return [(y, value / maximum) for y, value in raw]


def svg_header(width: int, height: int) -> str:
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" '
        f'width="{width}" height="{height}" role="img">\n'
        '  <rect width="100%" height="100%" fill="#f7f7f3"/>\n'
    )


def ring_path(cx: float, cy: float, radius: float, start_angle: float, end_angle: float) -> str:
    start_x = cx + math.cos(start_angle) * radius
    start_y = cy + math.sin(start_angle) * radius
    end_x = cx + math.cos(end_angle) * radius
    end_y = cy + math.sin(end_angle) * radius
    large_arc = 1 if abs(end_angle - start_angle) > math.pi else 0
    sweep = 1 if end_angle > start_angle else 0
    return f"M {start_x:.2f} {start_y:.2f} A {radius:.2f} {radius:.2f} 0 {large_arc} {sweep} {end_x:.2f} {end_y:.2f}"


def forward_semicircle_path(slit_x: float, slit_y: float, radius: float) -> str:
    center_x = slit_x + radius
    top_y = slit_y - radius
    bottom_y = slit_y + radius
    return f"M {slit_x:.2f} {top_y:.2f} A {radius:.2f} {radius:.2f} 0 0 1 {slit_x:.2f} {bottom_y:.2f}"


def wall_segments(x: float, width: float, top: float, bottom: float, slits: list[tuple[float, float]], indent: str = "  ") -> list[str]:
    segments: list[str] = []
    cursor = top
    for center, height in sorted(slits):
        slit_top = center - height / 2
        slit_bottom = center + height / 2
        if slit_top > cursor:
            segments.append(
                f'{indent}<rect x="{x - width / 2:.2f}" y="{cursor:.2f}" width="{width:.2f}" height="{slit_top - cursor:.2f}" fill="#111" rx="5"/>'
            )
        cursor = slit_bottom
    if cursor < bottom:
        segments.append(
            f'{indent}<rect x="{x - width / 2:.2f}" y="{cursor:.2f}" width="{width:.2f}" height="{bottom - cursor:.2f}" fill="#111" rx="5"/>'
        )
    return segments


def slit_layer(layout: ExperimentLayout = LAYOUT, indent: str = "  ") -> list[str]:
    slit_centers = [MODEL.center_y - MODEL.slit_separation / 2, MODEL.center_y + MODEL.slit_separation / 2]
    lines: list[str] = []
    lines.extend(wall_segments(layout.source_wall_x, layout.wall_width, layout.wall_top, layout.wall_bottom, [(MODEL.center_y, layout.source_slit_height)], indent))
    lines.extend(
        wall_segments(
            layout.double_wall_x,
            layout.wall_width,
            layout.wall_top,
            layout.wall_bottom,
            [(slit_centers[0], layout.double_slit_height), (slit_centers[1], layout.double_slit_height)],
            indent,
        )
    )
    return lines


def phase_fronts(cx: float, cy: float, start_radius: float, stop_radius: float, step: float, opacity: float, indent: str = "  ") -> list[str]:
    paths: list[str] = []
    radius = start_radius
    index = 0
    while radius <= stop_radius:
        paths.append(
            f'{indent}<path d="{forward_semicircle_path(cx, cy, radius)}" fill="none" '
            f'stroke="#141414" stroke-width="{clamp(2.6 - index * 0.04, 1.0, 2.6):.2f}" '
            f'opacity="{clamp(opacity - index * 0.012, 0.05, opacity):.3f}"/>'
        )
        radius += step
        index += 1
    return paths


def experiment_layer(layout: ExperimentLayout = LAYOUT, indent: str = "  ") -> list[str]:
    slit_centers = [MODEL.center_y - MODEL.slit_separation / 2, MODEL.center_y + MODEL.slit_separation / 2]
    top, height = screen_bounds()
    emitter_x = layout.source_x
    emitter_y = layout.source_y
    nozzle_x = emitter_x + 24
    slit_entrance_x = layout.source_wall_x - layout.wall_width / 2
    lines = [
        f'{indent}<circle cx="{emitter_x:.2f}" cy="{emitter_y:.2f}" r="22" fill="none" stroke="#111" stroke-width="3.8" opacity="0.92"/>',
        f'{indent}<circle cx="{emitter_x:.2f}" cy="{emitter_y:.2f}" r="13" fill="none" stroke="#111" stroke-width="2.4" opacity="0.72"/>',
        f'{indent}<circle cx="{emitter_x:.2f}" cy="{emitter_y:.2f}" r="5.8" fill="#111" opacity="0.90"/>',
        f'{indent}<path d="M {emitter_x + 15:.2f} {emitter_y - 9:.2f} L {nozzle_x:.2f} {emitter_y - 5:.2f} L {nozzle_x:.2f} {emitter_y + 5:.2f} L {emitter_x + 15:.2f} {emitter_y + 9:.2f} Z" fill="#111" opacity="0.88"/>',
        f'{indent}<line x1="{nozzle_x + 7:.2f}" y1="{emitter_y:.2f}" x2="{slit_entrance_x - 16:.2f}" y2="{emitter_y:.2f}" stroke="#111" stroke-width="2.2" opacity="0.38" stroke-dasharray="8 14"/>',
        f'{indent}<circle cx="{nozzle_x + 22:.2f}" cy="{emitter_y:.2f}" r="2.7" fill="#111" opacity="0.70"/>',
        f'{indent}<circle cx="{nozzle_x + 44:.2f}" cy="{emitter_y:.2f}" r="2.2" fill="#111" opacity="0.62"/>',
        f'{indent}<circle cx="{nozzle_x + 66:.2f}" cy="{emitter_y:.2f}" r="1.9" fill="#111" opacity="0.56"/>',
    ]
    lines.extend(phase_fronts(layout.source_wall_x, MODEL.center_y, 40, 318, MODEL.wavelength * 2.56, 0.34, indent))
    for slit_y in slit_centers:
        lines.extend(phase_fronts(layout.double_wall_x, slit_y, 40, 438, MODEL.wavelength * 2.08, 0.31, indent))
    for slit_y in slit_centers:
        for target_index, fraction in enumerate([0.16, 0.28, 0.4, 0.5, 0.6, 0.72, 0.84]):
            target_y = top + height * fraction
            control_y = slit_y * 0.64 + target_y * 0.36
            opacity = 0.08 if target_index != 3 else 0.13
            lines.append(
                f'{indent}<path d="M {layout.double_wall_x + layout.wall_width / 2:.2f} {slit_y:.2f} C 705 {control_y:.2f}, 870 {target_y:.2f}, {layout.projection_x - layout.projection_width:.2f} {target_y:.2f}" '
                f'fill="none" stroke="#111" stroke-width="1.1" opacity="{opacity:.2f}"/>'
            )
    return lines


def weighted_y_samples(top: float, height: float, samples: int, count: int, seed: int) -> list[tuple[float, float]]:
    profile = normalized_profile(top, height, samples)
    weights = [max(intensity, 0.0005) for _, _, intensity in profile]
    total = sum(weights)
    cumulative: list[float] = []
    running = 0.0
    for weight in weights:
        running += weight / total
        cumulative.append(running)

    picked: list[tuple[float, float]] = []
    cursor = 0
    for index in range(count):
        target = deterministic_noise(index, seed, 701)
        while cursor < len(cumulative) - 1 and cumulative[cursor] < target:
            cursor += 1
        while cursor > 0 and cumulative[cursor - 1] >= target:
            cursor -= 1
        sample_y, _, intensity = profile[cursor]
        jitter = (deterministic_noise(seed, index, 733) - 0.5) * (height / samples) * 1.6
        picked.append((clamp(sample_y + jitter, top, top + height), intensity))
    return picked


def projection_points(center_x: float, top: float, height: float, width: float, count: int, seed: int) -> list[tuple[float, float, float]]:
    points: list[tuple[float, float, float]] = []
    envelope_maximum = max(amplitude_envelope(MODEL.center_y), 1e-9)
    for index, (dot_y, intensity) in enumerate(weighted_y_samples(top, height, 1100, count, seed)):
        normalized_envelope = amplitude_envelope(dot_y) / envelope_maximum
        lateral_limit = max(1.8, normalized_envelope ** 1.12 * width)
        lateral = (deterministic_noise(index, seed, 809) * 2.0 - 1.0) * lateral_limit
        points.append((center_x + lateral, dot_y, intensity))
    return points


def envelope_outline(center_x: float, top: float, height: float, width: float) -> str:
    profile = normalized_envelope_profile(top, height, 520)
    right = [f"{center_x + envelope ** 1.12 * width:.2f},{sample_y:.2f}" for sample_y, envelope in profile]
    left = [f"{center_x - envelope ** 1.12 * width:.2f},{sample_y:.2f}" for sample_y, envelope in reversed(profile)]
    return "M " + " L ".join(right + left) + " Z"


def amplitude_wave_path(center_x: float, top: float, height: float, width: float, mirror: int) -> str:
    points = [f"{center_x + mirror * amplitude ** 1.36 * width:.2f},{sample_y:.2f}" for sample_y, amplitude, _ in normalized_profile(top, height, 1100)]
    return "M " + " L ".join(points)


def wall_projection_layer(center_x: float = LAYOUT.projection_x, width: float = LAYOUT.projection_width, indent: str = "  ") -> list[str]:
    top, height = screen_bounds()
    lines = [
        f'{indent}<path d="{envelope_outline(center_x, top, height, width)}" fill="none" stroke="#111" stroke-width="1.5" opacity="0.36"/>',
        f'{indent}<path d="{amplitude_wave_path(center_x, top, height, width, 1)}" fill="none" stroke="#111" stroke-width="2.5" opacity="0.78"/>',
        f'{indent}<path d="{amplitude_wave_path(center_x, top, height, width, -1)}" fill="none" stroke="#111" stroke-width="2.5" opacity="0.78"/>',
    ]
    for index, (x, y, intensity) in enumerate(projection_points(center_x, top, height, width, 24000, 29)):
        radius = 0.24 + 1.34 * intensity * deterministic_noise(index, 5, 811)
        opacity = 0.22 + 0.75 * intensity
        lines.append(f'{indent}<circle cx="{x:.2f}" cy="{y:.2f}" r="{radius:.2f}" fill="#050505" opacity="{opacity:.3f}"/>')
    return lines


def wrap_group(content: list[str], x: float = 0.0, y: float = 0.0, scale: float = 1.0, label: str | None = None) -> list[str]:
    lines = [f'  <g transform="translate({x:.2f} {y:.2f}) scale({scale:.4f})">']
    if label:
        lines.append(f'    <title>{label}</title>')
    lines.extend(f"  {line}" for line in content)
    lines.append("  </g>")
    return lines


def standalone_svg(content: list[str], title: str, width: int = CANVAS_WIDTH, height: int = CANVAS_HEIGHT) -> str:
    lines = [svg_header(width, height), f'  <title>{title}</title>', '  <g stroke-linecap="round" stroke-linejoin="round">']
    lines.extend(content)
    lines.extend(['  </g>', '</svg>'])
    return "\n".join(lines)


def render_wall_projection_svg() -> str:
    return standalone_svg(wall_projection_layer(), "WALL_PROJECTION")


def render_slits_svg() -> str:
    return standalone_svg(slit_layer(), "SLITS")


def render_experiment_svg() -> str:
    return standalone_svg(experiment_layer(), "EXPERIMENT")


def render_combined_svg() -> str:
    right_scale = 0.53
    left_scale = 0.78
    lines = [svg_header(COMBINED_WIDTH, COMBINED_HEIGHT), '  <title>COMBINED</title>']
    lines.extend(
        [
            f'  <line x1="{COMBINED_WIDTH / 2:.2f}" y1="54" x2="{COMBINED_WIDTH / 2:.2f}" y2="866" stroke="#111" stroke-width="2" stroke-dasharray="18 20" opacity="0.55"/>',
            '  <g stroke-linecap="round" stroke-linejoin="round">',
        ]
    )
    lines.extend(wrap_group(wall_projection_layer(), -460, 100, left_scale, "left arm: WALL_PROJECTION"))
    right_content = experiment_layer() + slit_layer()
    lines.extend(wrap_group(right_content, 800, 190, right_scale, "right arm: EXPERIMENT plus SLITS"))
    lines.extend(['  </g>', '</svg>'])
    return "\n".join(lines)


def write_outputs(output_dir: Path) -> list[Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    outputs = {
        "WALL_PROJECTION.svg": render_wall_projection_svg(),
        "SLITS.svg": render_slits_svg(),
        "EXPERIMENT.svg": render_experiment_svg(),
        "COMBINED.svg": render_combined_svg(),
    }
    paths: list[Path] = []
    for name, content in outputs.items():
        path = output_dir / name
        path.write_text(content, encoding="utf-8")
        paths.append(path)
    return paths


def main() -> None:
    parser = argparse.ArgumentParser(description="Render double-slit tattoo stencil SVG layers.")
    parser.add_argument("--output-dir", type=Path, default=Path("."), help="Directory for generated SVG files.")
    args = parser.parse_args()

    for path in write_outputs(args.output_dir):
        print(f"Wrote {path}")


if __name__ == "__main__":
    main()