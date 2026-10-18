#!/usr/bin/env python3
"""Deterministic science-poster generator and optional Instagram publisher.

This builds the poster from structured claims, equations, vector diagrams, and typography.
No text-to-image model is used. Publishing occurs only when --publish is provided.
"""
from __future__ import annotations
import argparse, json, os, random, sys, time
from pathlib import Path
from typing import Any
import requests
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
CONTENT_FILE = ROOT / "content" / "arrow_of_time.json"
OUT_FILE = ROOT / "docs" / "generated" / "arrow_of_time.jpg"
CAPTION_FILE = ROOT / "artifacts" / "instagram_caption.txt"
W, H = 1080, 1350
BG, INK, MUTED = "#F4F1E9", "#152D3A", "#52656C"
TEAL, CORAL, GOLD = "#158B8C", "#E7644B", "#D9A633"
PALE_TEAL, PALE_CORAL, WHITE = "#DCEDE7", "#F7E1D8", "#FFFEFA"
FONT_DIR = Path("/usr/share/fonts/truetype/lato")


def font(size: int, bold: bool = False, italic: bool = False):
    name = "Lato-Italic.ttf" if italic else ("Lato-Bold.ttf" if bold else "Lato-Regular.ttf")
    path = FONT_DIR / name
    if not path.exists():
        path = Path("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf")
    return ImageFont.truetype(str(path), size=size)


def validate_content(c: dict[str, Any]) -> list[str]:
    errors = []
    for key in ("title", "subtitle", "second_law", "boltzmann", "microscopic", "cosmic", "takeaway", "caption"):
        if not c.get(key):
            errors.append(f"Missing required field: {key}")
    if c.get("second_law", {}).get("equation") != "ΔS ≥ 0":
        errors.append("Second-law equation must be ΔS ≥ 0 for an isolated system.")
    if c.get("boltzmann", {}).get("equation") != "S = k_B ln Ω":
        errors.append("Boltzmann equation should be S = k_B ln Ω.")
    all_claims = " ".join([str(c.get("thesis", "")), str(c.get("microscopic", {}).get("body", "")),
                           str(c.get("cosmic", {}).get("body", "")), str(c.get("second_law", {}).get("body", ""))]).lower()
    for phrase in ("low", "time-reversal", "isolated system"):
        if phrase not in all_claims:
            errors.append(f"Scientific QA: explanation must address '{phrase}'.")
    if len(c.get("hashtags", [])) < 3:
        errors.append("Caption needs at least three hashtags.")
    return errors


def rounded(draw, box, radius, fill, outline=None, width=1):
    draw.rounded_rectangle(box, radius=radius, fill=fill, outline=outline, width=width)


def wrap_text(draw, text, fnt, max_width):
    lines, current = [], ""
    for word in text.split():
        candidate = word if not current else current + " " + word
        if draw.textlength(candidate, font=fnt) <= max_width:
            current = candidate
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


def paragraph(draw, xy, text, fnt, fill, max_width, leading=5, max_lines=None):
    x, y = xy
    lines = wrap_text(draw, text, fnt, max_width)
    if max_lines:
        lines = lines[:max_lines]
    for line in lines:
        draw.text((x, y), line, font=fnt, fill=fill)
        y += fnt.size + leading
    return y


def draw_dot_state(draw, box, state, seed):
    x0, y0, x1, y1 = box
    rng = random.Random(seed)
    cols, rows = 7, 5
    for j in range(rows):
        for i in range(cols):
            if state == "ordered":
                x = x0 + 12 + i * (x1-x0-24)/(cols-1)
                y = y0 + 12 + j * (y1-y0-24)/(rows-1)
            elif state == "mixed":
                x = x0 + 12 + i * (x1-x0-24)/(cols-1) + rng.uniform(-7, 7)
                y = y0 + 12 + j * (y1-y0-24)/(rows-1) + rng.uniform(-6, 6)
            else:
                x = rng.uniform(x0 + 8, x1 - 8)
                y = rng.uniform(y0 + 5, y1 - 5)
            r = 4 if state == "dispersed" else 5
            d = TEAL if (int(x)+int(y)) % 2 else CORAL
            draw.ellipse((int(x)-r, int(y)-r, int(x)+r, int(y)+r), fill=d)


def draw_arrow(draw, start, end, fill, width=4):
    import math
    draw.line((start, end), fill=fill, width=width)
    angle = math.atan2(end[1]-start[1], end[0]-start[0])
    size = 17
    p1 = (end[0] + size*math.cos(angle+2.55), end[1] + size*math.sin(angle+2.55))
    p2 = (end[0] + size*math.cos(angle-2.55), end[1] + size*math.sin(angle-2.55))
    draw.polygon([end, p1, p2], fill=fill)


def render_poster(c, path=OUT_FILE):
    path.parent.mkdir(parents=True, exist_ok=True)
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)
    d.rectangle((0, 0, W, 16), fill=INK)
    d.text((58, 42), "SCIENCE / PHYSICS NOTE  01", font=font(18, True), fill=TEAL)
    d.text((54, 72), "THE ARROW", font=font(83, True), fill=INK)
    d.text((54, 148), "OF TIME", font=font(83, True), fill=CORAL)
    paragraph(d, (60, 246), c["subtitle"], font(27, True), INK, 940, leading=4, max_lines=2)
    d.line((60, 320, 1020, 320), fill=INK, width=2)
    d.text((60, 344), "FROM ONE SPECIAL START", font=font(19, True), fill=MUTED)
    d.text((60, 375), "to many more ways for things to be", font=font(30, True), fill=INK)

    boxes = [(60, 435, 340, 620), (390, 435, 690, 620), (740, 435, 1020, 620)]
    specs = [("PAST", "ordered", PALE_TEAL, 7), ("PRESENT", "mixed", WHITE, 42), ("FUTURE", "dispersed", PALE_CORAL, 81)]
    for i, (box, (label, state, fill, seed)) in enumerate(zip(boxes, specs)):
        rounded(d, box, 18, fill, outline="#D4D9D1", width=2)
        x0,y0,x1,y1 = box
        d.text((x0+18, y0+14), label, font=font(21, True), fill=INK)
        d.text((x0+18, y0+43), c["timeline"][i]["detail"], font=font(16), fill=MUTED)
        draw_dot_state(d, (x0+19,y0+76,x1-19,y1-16), state, seed)
    draw_arrow(d, (345, 526), (378, 526), GOLD)
    draw_arrow(d, (695, 526), (728, 526), GOLD)
    d.text((60, 633), "Illustration: accessible microscopic configurations, not a map of the whole universe.", font=font(15, italic=True), fill=MUTED)

    rounded(d, (60, 667, 1020, 809), 22, INK)
    d.text((88, 686), c["second_law"]["heading"], font=font(20, True), fill="#A9E2D8")
    d.text((88, 715), c["second_law"]["equation"], font=font(55, True), fill=WHITE)
    paragraph(d, (535, 713), c["second_law"]["body"], font(18), WHITE, 445, leading=5, max_lines=4)

    rounded(d, (60, 835, 520, 1080), 18, WHITE, outline="#D4D9D1", width=2)
    d.text((84, 856), c["boltzmann"]["heading"], font=font(21, True), fill=TEAL)
    d.text((84, 890), c["boltzmann"]["equation"], font=font(38, True), fill=INK)
    paragraph(d, (84, 944), c["boltzmann"]["body"], font(18), MUTED, 405, leading=5, max_lines=5)

    rounded(d, (545, 835, 1020, 1080), 18, PALE_CORAL, outline="#EBC4B7", width=2)
    d.text((570, 856), c["microscopic"]["heading"], font=font(21, True), fill=CORAL)
    d.text((570, 890), c["microscopic"]["equation"], font=font(29, True), fill=INK)
    paragraph(d, (570, 934), c["microscopic"]["body"], font(17), INK, 420, leading=4, max_lines=6)

    rounded(d, (60, 1100, 1020, 1215), 18, "#E2E9E5")
    d.text((84, 1116), c["cosmic"]["heading"], font=font(22, True), fill=INK)
    paragraph(d, (84, 1149), c["cosmic"]["body"], font(18), INK, 900, leading=4, max_lines=3)
    d.rectangle((0, 1235, W, H), fill=INK)
    d.text((58, 1253), "THE TAKEAWAY", font=font(18, True), fill="#A9E2D8")
    paragraph(d, (58, 1280), c["takeaway"], font(25, True), WHITE, 950, leading=2, max_lines=2)
    img.save(path, format="JPEG", quality=94, optimize=True, progressive=True)


def write_caption(c):
    CAPTION_FILE.parent.mkdir(parents=True, exist_ok=True)
    text = c["caption"].strip() + "\n\n" + " ".join(c["hashtags"])
    if len(text) > 2200:
        raise ValueError("Caption too long for conservative publishing limit")
    CAPTION_FILE.write_text(text + "\n", encoding="utf-8")


def verify_instagram_account() -> str:
    """Validate the configured token and fail closed unless it identifies @wowscifi."""
    token = os.environ.get("META_ACCESS_TOKEN", "").strip()
    ig_user_id = os.environ.get("IG_USER_ID", "").strip()
    version = os.environ.get("META_GRAPH_API_VERSION", "v26.0").strip()
    if not token:
        raise RuntimeError("Missing GitHub Actions secret META_ACCESS_TOKEN.")
    if not ig_user_id:
        raise RuntimeError("Missing GitHub Actions secret IG_USER_ID.")
    if not version.startswith("v"):
        raise RuntimeError("META_GRAPH_API_VERSION must start with v.")
    response = requests.get(
        f"https://graph.facebook.com/{version}/{ig_user_id}",
        params={"fields": "username", "access_token": token},
        timeout=25,
    )
    try:
        data = response.json()
    except ValueError:
        data = {}
    if not response.ok or (isinstance(data, dict) and data.get("error")):
        message = data.get("error", {}).get("message", str(data)) if isinstance(data, dict) else str(data)
        raise RuntimeError(f"Meta credential preflight failed: HTTP {response.status_code}: {message}")
    username = str(data.get("username", "")).lstrip("@").casefold()
    if username != "wowscifi":
        raise RuntimeError(
            f"SAFETY STOP: IG_USER_ID resolves to @{username or 'unknown'}, not @wowscifi. "
            "No post will be created."
        )
    print("ACCOUNT_SECRET_PREFLIGHT_PASS: credentials resolve to @wowscifi")
    return username


def publish_to_instagram(image_url, caption):
    token = os.environ.get("META_ACCESS_TOKEN", "").strip()
    ig_user_id = os.environ.get("IG_USER_ID", "").strip()
    version = os.environ.get("META_GRAPH_API_VERSION", "v26.0").strip()
    if not token or not ig_user_id:
        raise RuntimeError("Missing GitHub secrets IG_USER_ID and/or META_ACCESS_TOKEN")
    if not version.startswith("v"):
        raise RuntimeError("META_GRAPH_API_VERSION must start with v")
    base = f"https://graph.facebook.com/{version}"
    session = requests.Session()

    def checked(response, stage):
        try:
            data = response.json()
        except ValueError:
            data = {}
        if not response.ok or (isinstance(data, dict) and data.get("error")):
            msg = data.get("error", {}).get("message", str(data)) if isinstance(data, dict) else str(data)
            raise RuntimeError(f"Instagram API failed at {stage}: HTTP {response.status_code}: {msg}")
        return data

    profile = checked(session.get(f"{base}/{ig_user_id}", params={
        "fields": "username", "access_token": token
    }, timeout=25), "verify destination account")
    actual_username = str(profile.get("username", "")).lstrip("@").casefold()
    expected_username = "wowscifi"
    if actual_username != expected_username:
        raise RuntimeError(
            f"SAFETY STOP: IG_USER_ID resolves to @{actual_username or 'unknown'}, "
            f"not the required @{expected_username}. No media was created or published."
        )
    print("TARGET_ACCOUNT_VERIFIED: @wowscifi")

    head = session.head(image_url, timeout=25, allow_redirects=True)
    if not head.ok or not head.headers.get("content-type", "").lower().startswith("image/"):
        raise RuntimeError(f"Image URL must be publicly accessible and return an image (HTTP {head.status_code})")
    created = checked(session.post(f"{base}/{ig_user_id}/media", data={
        "image_url": image_url, "caption": caption, "access_token": token
    }, timeout=45), "create media container")
    container_id = created.get("id")
    if not container_id:
        raise RuntimeError("Instagram returned no media container ID")
    state = "IN_PROGRESS"
    for _ in range(12):
        detail = checked(session.get(f"{base}/{container_id}", params={
            "fields": "status_code,status", "access_token": token
        }, timeout=25), "check image processing")
        state = detail.get("status_code", "FINISHED")
        if state == "FINISHED":
            break
        if state == "ERROR":
            raise RuntimeError(f"Instagram processing error: {detail.get('status', 'unknown')}")
        time.sleep(5)
    if state != "FINISHED":
        raise RuntimeError("Instagram image container was not ready within 60 seconds")
    published = checked(session.post(f"{base}/{ig_user_id}/media_publish", data={
        "creation_id": container_id, "access_token": token
    }, timeout=45), "publish media")
    media_id = published.get("id")
    if not media_id:
        raise RuntimeError("Instagram did not return a published media ID")
    details = checked(session.get(f"{base}/{media_id}", params={
        "fields": "id,permalink,timestamp,media_type", "access_token": token
    }, timeout=25), "verify published media")
    url = details.get("permalink") or media_id
    print(f"PUBLISH_SUCCESS media_id={media_id} permalink={url}")
    (ROOT / "artifacts" / "publication_receipt.txt").write_text(
        f"Published at: {url}\nImage URL: {image_url}\n", encoding="utf-8"
    )
    return url


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check-account", action="store_true", help="Validate Meta secrets resolve to @wowscifi")
    parser.add_argument("--publish", action="store_true", help="Publish after rendering and quality checks")
    parser.add_argument("--image-url", default="", help="Public HTTPS URL to the committed PNG")
    args = parser.parse_args()
    if args.check_account:
        verify_instagram_account()
        return 0
    c = json.loads(CONTENT_FILE.read_text(encoding="utf-8"))
    problems = validate_content(c)
    if problems:
        for p in problems:
            print(f"QA_FAIL: {p}", file=sys.stderr)
        return 2
    print("CONTENT_QA_PASS: required claims, equations and caveats found")
    render_poster(c)
    write_caption(c)
    with Image.open(OUT_FILE) as image:
        if image.size != (W, H) or image.format != "JPEG" or OUT_FILE.stat().st_size < 40000:
            raise RuntimeError(f"Layout QA failed: {image.size}, {image.format}, {OUT_FILE.stat().st_size} bytes")
    print(f"LAYOUT_QA_PASS: {OUT_FILE} {W}x{H} {OUT_FILE.stat().st_size} bytes")
    print(f"CAPTION_READY: {CAPTION_FILE}")
    if args.publish:
        if not args.image_url.startswith("https://"):
            raise RuntimeError("Publishing requires a public HTTPS URL via --image-url")
        publish_to_instagram(args.image_url, CAPTION_FILE.read_text(encoding="utf-8").strip())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
