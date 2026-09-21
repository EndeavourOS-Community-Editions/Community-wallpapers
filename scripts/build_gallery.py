#!/usr/bin/env python3
"""
EndeavourOS Community Wallpapers Gallery Generator
Builds a static, responsive web gallery with optimized WebP thumbnails for GitHub Pages.
"""

import argparse
import html
import json
import os
import sys
from concurrent.futures import ProcessPoolExecutor
from urllib.parse import quote

from PIL import Image, ImageDraw


def format_file_size(bytes_size: int) -> str:
    for unit in ["B", "KB", "MB", "GB"]:
        if bytes_size < 1024.0:
            return f"{bytes_size:.1f} {unit}" if unit == "MB" else f"{int(bytes_size)} {unit}"
        bytes_size /= 1024.0
    return f"{bytes_size:.1f} GB"


def create_error_placeholder(dest_path: str, width: int = 480, height: int = 270):
    img = Image.new("RGB", (width, height), color=(36, 40, 59))
    draw = ImageDraw.Draw(img)
    text = "Corrupted / Empty Image"
    # Basic rectangle and text
    draw.rectangle([(2, 2), (width - 3, height - 3)], outline=(247, 118, 142), width=3)
    # PIL default font may be small, draw a simple visual warning
    draw.text((width // 2 - 70, height // 2 - 10), text, fill=(247, 118, 142))
    img.save(dest_path, "WEBP", quality=80)


def process_image(task):
    src_path, dest_thumb_path, category, base_url, max_width, quality = task
    fname = os.path.basename(src_path)
    file_size = os.path.getsize(src_path)
    name_no_ext, ext = os.path.splitext(fname)

    raw_url = f"{base_url}/{category}/{quote(fname)}"
    thumb_fname = f"{fname}.webp"
    thumb_rel_url = f"thumbnails/{category}/{quote(thumb_fname)}"

    os.makedirs(os.path.dirname(dest_thumb_path), exist_ok=True)

    is_corrupt = False
    width, height = 0, 0

    try:
        if file_size < 16:  # Unusually small or empty file
            raise ValueError(f"File too small ({file_size} bytes)")

        with Image.open(src_path) as img:
            width, height = img.size

            # Ensure image is in RGB or RGBA mode
            if img.mode in ("P", "LA"):
                img = img.convert("RGBA")
            elif img.mode not in ("RGB", "RGBA"):
                img = img.convert("RGB")

            # Calculate resize maintaining aspect ratio
            if width > max_width:
                calc_height = int((max_width / width) * height)
                thumb = img.resize((max_width, calc_height), Image.Resampling.LANCZOS)
            else:
                thumb = img.copy()

            thumb.save(dest_thumb_path, "WEBP", quality=quality, method=6)
    except Exception as e:
        print(f"Warning: Failed to process {src_path} ({e}). Creating placeholder.", file=sys.stderr)
        is_corrupt = True
        create_error_placeholder(dest_thumb_path)
        width, height = 0, 0

    return {
        "name": fname,
        "title": name_no_ext.replace("_", " ").replace("-", " ").strip(),
        "category": category,
        "width": width,
        "height": height,
        "size_bytes": file_size,
        "size_human": format_file_size(file_size),
        "raw_url": raw_url,
        "thumb_url": thumb_rel_url,
        "is_corrupt": is_corrupt,
    }


def generate_html(wallpapers, categories, output_dir, repo_name="EndeavourOS-Community-Editions/Community-wallpapers", has_collage=False, raw_collage_url=""):
    wallpapers_json = json.dumps(wallpapers, ensure_ascii=False)

    total_count = len(wallpapers)
    classic_count = sum(1 for w in wallpapers if "classic" in w["category"])
    community_count = sum(1 for w in wallpapers if "community" in w["category"])

    collage_html = ""
    if has_collage:
        collage_html = f'''
      <div class="hero-collage">
        <img src="collage.webp" alt="EndeavourOS Community Collage" loading="eager" onerror="this.onerror=null; this.src='{raw_collage_url}';">
      </div>'''

    html_template = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <meta name="theme-color" content="#1a1b26">
  <title>EndeavourOS Community Wallpapers</title>
  <link rel="icon" href="https://raw.githubusercontent.com/EndeavourOS-Community-Editions/Community-wallpapers/main/eos_wallpapers_classic/endeavouros_default_background.png" type="image/png">
  <style>
    :root {{
      --bg-dark: #15161e;
      --bg-card: #1a1b26;
      --bg-hover: #24283b;
      --accent-purple: #7f3fbf;
      --accent-magenta: #ff007f;
      --accent-blue: #7aa2f7;
      --accent-cyan: #7dcfff;
      --accent-subtle: #414868;
      --text-main: #c0caf5;
      --text-muted: #9aa5ce;
      --text-dim: #565f89;
      --danger: #f7768e;
      --radius-sm: 6px;
      --radius-md: 12px;
      --radius-lg: 18px;
      --shadow: 0 4px 20px rgba(0, 0, 0, 0.4);
    }}

    * {{
      box-sizing: border-box;
      margin: 0;
      padding: 0;
    }}

    body {{
      font-family: system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', sans-serif;
      background-color: var(--bg-dark);
      color: var(--text-main);
      line-height: 1.5;
      min-height: 100vh;
      display: flex;
      flex-direction: column;
    }}

    header {{
      background: linear-gradient(135deg, #1f1d36 0%, #15161e 100%);
      border-bottom: 1px solid var(--accent-subtle);
      padding: 2.5rem 1.5rem 2rem;
      text-align: center;
      position: relative;
    }}

    .header-content {{
      max-width: 900px;
      margin: 0 auto;
    }}

    .logo-badge {{
      display: inline-flex;
      align-items: center;
      gap: 0.5rem;
      padding: 0.35rem 0.9rem;
      background: rgba(127, 63, 191, 0.2);
      border: 1px solid var(--accent-purple);
      border-radius: 9999px;
      font-size: 0.85rem;
      font-weight: 600;
      color: var(--accent-cyan);
      margin-bottom: 1rem;
    }}

    h1 {{
      font-size: 2.25rem;
      font-weight: 800;
      letter-spacing: -0.025em;
      background: linear-gradient(90deg, #c0caf5 0%, #7aa2f7 50%, #ff007f 100%);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
      margin-bottom: 0.75rem;
    }}

    p.subtitle {{
      color: var(--text-muted);
      font-size: 1.05rem;
      max-width: 650px;
      margin: 0 auto 1.5rem;
    }}

    .stats-bar {{
      display: flex;
      justify-content: center;
      gap: 1.5rem;
      font-size: 0.9rem;
      color: var(--text-muted);
      flex-wrap: wrap;
    }}

    .stat-item {{
      background: rgba(36, 40, 59, 0.6);
      padding: 0.35rem 0.85rem;
      border-radius: var(--radius-sm);
      border: 1px solid var(--accent-subtle);
    }}

    .stat-item strong {{
      color: #fff;
    }}

    .container {{
      max-width: 1400px;
      margin: 0 auto;
      padding: 1.5rem;
      flex: 1;
      width: 100%;
    }}

    .toolbar {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      gap: 1rem;
      margin-bottom: 2rem;
      flex-wrap: wrap;
      background: var(--bg-card);
      padding: 1rem 1.25rem;
      border-radius: var(--radius-md);
      border: 1px solid var(--accent-subtle);
    }}

    .filter-tabs {{
      display: flex;
      gap: 0.5rem;
      flex-wrap: wrap;
    }}

    .filter-btn {{
      background: transparent;
      border: 1px solid transparent;
      color: var(--text-muted);
      padding: 0.45rem 1rem;
      border-radius: var(--radius-sm);
      font-weight: 600;
      font-size: 0.9rem;
      cursor: pointer;
      transition: all 0.2s ease;
    }}

    .filter-btn:hover {{
      color: #fff;
      background: var(--bg-hover);
    }}

    .filter-btn.active {{
      background: var(--accent-purple);
      color: #fff;
      border-color: var(--accent-purple);
      box-shadow: 0 0 12px rgba(127, 63, 191, 0.4);
    }}

    .search-sort-group {{
      display: flex;
      gap: 0.75rem;
      flex: 1;
      max-width: 450px;
      justify-content: flex-end;
    }}

    .search-box {{
      position: relative;
      flex: 1;
    }}

    .search-box input {{
      width: 100%;
      background: var(--bg-dark);
      border: 1px solid var(--accent-subtle);
      border-radius: var(--radius-sm);
      padding: 0.45rem 1rem;
      font-size: 0.9rem;
      color: var(--text-main);
      outline: none;
      transition: border-color 0.2s;
    }}

    .search-box input:focus {{
      border-color: var(--accent-blue);
    }}

    .sort-select {{
      background: var(--bg-dark);
      border: 1px solid var(--accent-subtle);
      border-radius: var(--radius-sm);
      padding: 0.45rem 0.75rem;
      font-size: 0.9rem;
      color: var(--text-main);
      outline: none;
      cursor: pointer;
    }}

    .gallery-grid {{
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
      gap: 1.5rem;
    }}

    .card {{
      background: var(--bg-card);
      border: 1px solid var(--accent-subtle);
      border-radius: var(--radius-md);
      overflow: hidden;
      display: flex;
      flex-direction: column;
      box-shadow: var(--shadow);
      transition: transform 0.2s ease, border-color 0.2s ease, box-shadow 0.2s ease;
    }}

    .card:hover {{
      transform: translateY(-4px);
      border-color: var(--accent-purple);
      box-shadow: 0 8px 25px rgba(127, 63, 191, 0.25);
    }}

    .card-image-wrap {{
      position: relative;
      width: 100%;
      aspect-ratio: 16 / 9;
      background: #111218;
      overflow: hidden;
      cursor: pointer;
    }}

    .card-image-wrap img {{
      width: 100%;
      height: 100%;
      object-fit: cover;
      display: block;
      transition: transform 0.3s ease;
    }}

    .card-image-wrap:hover img {{
      transform: scale(1.05);
    }}

    .card-body {{
      padding: 1rem;
      display: flex;
      flex-direction: column;
      flex: 1;
    }}

    .card-title {{
      font-size: 0.95rem;
      font-weight: 600;
      color: var(--text-main);
      margin-bottom: 0.5rem;
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
    }}

    .card-meta {{
      display: flex;
      justify-content: space-between;
      font-size: 0.8rem;
      color: var(--text-muted);
      margin-bottom: 0.85rem;
    }}

    .category-badge {{
      display: inline-block;
      font-size: 0.72rem;
      font-weight: 700;
      padding: 0.15rem 0.45rem;
      border-radius: 4px;
      text-transform: uppercase;
      letter-spacing: 0.05em;
    }}

    .category-classic {{
      background: rgba(122, 162, 247, 0.15);
      color: var(--accent-blue);
      border: 1px solid rgba(122, 162, 247, 0.3);
    }}

    .category-community {{
      background: rgba(255, 0, 127, 0.15);
      color: var(--accent-magenta);
      border: 1px solid rgba(255, 0, 127, 0.3);
    }}

    .card-actions {{
      margin-top: auto;
      display: flex;
      gap: 0.5rem;
    }}

    .btn {{
      display: inline-flex;
      align-items: center;
      justify-content: center;
      gap: 0.4rem;
      padding: 0.45rem 0.85rem;
      font-size: 0.85rem;
      font-weight: 600;
      border-radius: var(--radius-sm);
      text-decoration: none;
      cursor: pointer;
      transition: all 0.2s ease;
      border: none;
    }}

    .btn-preview {{
      flex: 1;
      background: var(--bg-hover);
      color: var(--text-main);
      border: 1px solid var(--accent-subtle);
    }}

    .btn-preview:hover {{
      background: #2f354f;
      color: #fff;
    }}

    .btn-download {{
      background: var(--accent-purple);
      color: #fff;
    }}

    .btn-download:hover {{
      background: #904dd6;
    }}

    .btn-mix {{
      display: inline-flex;
      align-items: center;
      justify-content: center;
      gap: 0.35rem;
      background: linear-gradient(135deg, var(--accent-purple) 0%, var(--accent-magenta) 100%);
      color: #fff;
      border: none;
      padding: 0.45rem 1rem;
      border-radius: var(--radius-sm);
      font-size: 0.9rem;
      font-weight: 700;
      cursor: pointer;
      box-shadow: 0 2px 10px rgba(127, 63, 191, 0.35);
      transition: all 0.2s ease;
      white-space: nowrap;
    }}

    .btn-mix:hover {{
      transform: translateY(-2px);
      box-shadow: 0 4px 15px rgba(255, 0, 127, 0.45);
      filter: brightness(1.12);
    }}

    .empty-state {{
      text-align: center;
      padding: 4rem 1rem;
      color: var(--text-muted);
      grid-column: 1 / -1;
    }}

    .hero-collage {{
      margin-top: 2rem;
      border-radius: var(--radius-md);
      overflow: hidden;
      border: 1px solid var(--accent-subtle);
      box-shadow: 0 10px 40px rgba(0, 0, 0, 0.6);
      background: #10121a;
    }}

    .hero-collage img {{
      width: 100%;
      height: auto;
      max-height: 480px;
      object-fit: cover;
      display: block;
    }}

    /* Lightbox Modal */
    .modal {{
      display: none;
      position: fixed;
      z-index: 9999;
      inset: 0;
      background: rgba(10, 11, 16, 0.92);
      backdrop-filter: blur(8px);
      align-items: center;
      justify-content: center;
      padding: 1.5rem;
    }}

    .modal.active {{
      display: flex;
    }}

    .modal-content {{
      position: relative;
      max-width: 92vw;
      max-height: 92vh;
      display: flex;
      flex-direction: column;
      background: var(--bg-card);
      border-radius: var(--radius-lg);
      border: 1px solid var(--accent-subtle);
      overflow: hidden;
      box-shadow: 0 10px 40px rgba(0, 0, 0, 0.8);
    }}

    .modal-header {{
      padding: 0.75rem 1.25rem;
      display: flex;
      justify-content: space-between;
      align-items: center;
      border-bottom: 1px solid var(--accent-subtle);
      background: var(--bg-dark);
    }}

    .modal-title {{
      font-size: 1.05rem;
      font-weight: 700;
      color: #fff;
      display: flex;
      align-items: center;
      gap: 0.75rem;
    }}

    .modal-close {{
      background: transparent;
      border: none;
      color: var(--text-muted);
      font-size: 1.5rem;
      cursor: pointer;
      line-height: 1;
      padding: 0.25rem;
    }}

    .modal-close:hover {{
      color: #fff;
    }}

    .modal-image-container {{
      position: relative;
      display: flex;
      align-items: center;
      justify-content: center;
      background: #0d0e14;
      overflow: hidden;
      min-height: 300px;
    }}

    .modal-image-container img {{
      max-width: 100%;
      max-height: 72vh;
      object-fit: contain;
      display: block;
    }}

    .modal-footer {{
      padding: 0.85rem 1.25rem;
      display: flex;
      justify-content: space-between;
      align-items: center;
      border-top: 1px solid var(--accent-subtle);
      background: var(--bg-dark);
      flex-wrap: wrap;
      gap: 0.75rem;
    }}

    .modal-meta {{
      font-size: 0.85rem;
      color: var(--text-muted);
    }}

    .nav-btn {{
      position: absolute;
      top: 50%;
      transform: translateY(-50%);
      background: rgba(26, 27, 38, 0.7);
      border: 1px solid var(--accent-subtle);
      color: #fff;
      font-size: 1.5rem;
      padding: 0.75rem 0.9rem;
      cursor: pointer;
      border-radius: var(--radius-sm);
      transition: background 0.2s;
    }}

    .nav-btn:hover {{
      background: var(--accent-purple);
    }}

    .nav-btn.prev {{ left: 1rem; }}
    .nav-btn.next {{ right: 1rem; }}

    footer {{
      background: var(--bg-card);
      border-top: 1px solid var(--accent-subtle);
      padding: 1.5rem;
      text-align: center;
      font-size: 0.85rem;
      color: var(--text-muted);
      margin-top: auto;
    }}

    footer a {{
      color: var(--accent-blue);
      text-decoration: none;
    }}

    footer a:hover {{
      text-decoration: underline;
    }}

    @media (max-width: 768px) {{
      header {{ padding: 1.5rem 1rem; }}
      h1 {{ font-size: 1.75rem; }}
      .toolbar {{ flex-direction: column; align-items: stretch; }}
      .search-sort-group {{ max-width: 100%; }}
      .nav-btn {{ display: none; }}
    }}
  </style>
</head>
<body>

  <header>
    <div class="header-content">
      <div class="logo-badge">
        <span>🚀 EndeavourOS Gallery</span>
      </div>
      <h1>EndeavourOS Community Wallpapers</h1>
      <p class="subtitle">A curated collection of past default backgrounds and stunning artwork created by the EndeavourOS community.</p>
      
      <div class="stats-bar">
        <div class="stat-item">Total: <strong id="stat-total">{total_count}</strong></div>
        <div class="stat-item">Classic: <strong>{classic_count}</strong></div>
        <div class="stat-item">Community: <strong>{community_count}</strong></div>
      </div>
      {collage_html}
    </div>
  </header>

  <div class="container">
    <div class="toolbar">
      <div class="filter-tabs">
        <button class="filter-btn active" data-filter="all">All Wallpapers ({total_count})</button>
        <button class="filter-btn" data-filter="eos_wallpapers_classic">Classic ({classic_count})</button>
        <button class="filter-btn" data-filter="eos_wallpapers_community">Community ({community_count})</button>
      </div>

      <div class="search-sort-group">
        <div class="search-box">
          <input type="text" id="searchInput" placeholder="Search wallpapers..." autocomplete="off">
        </div>
        <select class="sort-select" id="sortSelect">
          <option value="name-asc">Name (A-Z)</option>
          <option value="name-desc">Name (Z-A)</option>
          <option value="res-desc">Resolution (High to Low)</option>
          <option value="random">🎲 Random Shuffle</option>
        </select>
        <button class="btn-mix" id="mixBtn" title="Show a random wallpaper">🎲 Mix</button>
      </div>
    </div>

    <div class="gallery-grid" id="galleryGrid"></div>
  </div>

  <!-- Lightbox Modal -->
  <div class="modal" id="lightboxModal">
    <div class="modal-content">
      <div class="modal-header">
        <div class="modal-title" id="modalTitle">Wallpaper Preview</div>
        <button class="modal-close" id="modalClose">&times;</button>
      </div>
      <div class="modal-image-container">
        <button class="nav-btn prev" id="modalPrev">&#10094;</button>
        <img id="modalImage" src="" alt="Wallpaper preview">
        <button class="nav-btn next" id="modalNext">&#10095;</button>
      </div>
      <div class="modal-footer">
        <div class="modal-meta" id="modalMeta"></div>
        <div style="display:flex; gap:0.5rem; flex-wrap:wrap;">
          <button class="btn btn-preview" id="modalRandomBtn" title="Show another random wallpaper">🎲 Random</button>
          <a class="btn btn-preview" id="modalDirectLink" target="_blank" rel="noopener">Open Raw</a>
          <button class="btn btn-download" id="modalDownload">Download Original</button>
        </div>
      </div>
    </div>
  </div>

  <footer>
    <p>Maintained by the <a href="https://github.com/{repo_name}" target="_blank" rel="noopener">EndeavourOS Community</a>. Automatically generated via GitHub Actions &amp; GitHub Pages.</p>
  </footer>

  <script>
    const wallpapers = {wallpapers_json};
    let currentFilter = 'all';
    let searchQuery = '';
    let currentSort = 'name-asc';
    let filteredWallpapers = [...wallpapers];
    let activeModalIndex = -1;

    const grid = document.getElementById('galleryGrid');
    const searchInput = document.getElementById('searchInput');
    const sortSelect = document.getElementById('sortSelect');
    const filterButtons = document.querySelectorAll('.filter-btn');

    const modal = document.getElementById('lightboxModal');
    const modalImage = document.getElementById('modalImage');
    const modalTitle = document.getElementById('modalTitle');
    const modalMeta = document.getElementById('modalMeta');
    const modalDownload = document.getElementById('modalDownload');
    const modalDirectLink = document.getElementById('modalDirectLink');
    const modalClose = document.getElementById('modalClose');
    const modalPrev = document.getElementById('modalPrev');
    const modalNext = document.getElementById('modalNext');

    function applyFilters() {{
      filteredWallpapers = wallpapers.filter(w => {{
        const matchesCategory = currentFilter === 'all' || w.category === currentFilter;
        const matchesSearch = !searchQuery || w.name.toLowerCase().includes(searchQuery) || w.title.toLowerCase().includes(searchQuery);
        return matchesCategory && matchesSearch;
      }});

      if (currentSort === 'random') {{
        for (let i = filteredWallpapers.length - 1; i > 0; i--) {{
          const j = Math.floor(Math.random() * (i + 1));
          [filteredWallpapers[i], filteredWallpapers[j]] = [filteredWallpapers[j], filteredWallpapers[i]];
        }}
      }} else {{
        filteredWallpapers.sort((a, b) => {{
          if (currentSort === 'name-asc') return a.name.localeCompare(b.name);
          if (currentSort === 'name-desc') return b.name.localeCompare(a.name);
          if (currentSort === 'res-desc') return (b.width * b.height) - (a.width * a.height);
          return 0;
        }});
      }}

      renderGrid();
    }}

    function renderGrid() {{
      if (filteredWallpapers.length === 0) {{
        grid.innerHTML = `<div class="empty-state"><h3>No wallpapers found</h3><p>Try clearing your search query or filters.</p></div>`;
        return;
      }}

      grid.innerHTML = filteredWallpapers.map((w, index) => {{
        const catClass = w.category.includes('classic') ? 'category-classic' : 'category-community';
        const catName = w.category.includes('classic') ? 'Classic' : 'Community';
        const resText = w.width && w.height ? `${{w.width}} &times; ${{w.height}}` : (w.is_corrupt ? '⚠️ Broken File' : 'Original');

        return `
          <div class="card" data-index="${{index}}">
            <div class="card-image-wrap" onclick="openModal(${{index}})">
              <img src="${{w.thumb_url}}" alt="${{escapeHtml(w.name)}}" loading="lazy" onerror="this.onerror=null; this.src='${{w.raw_url}}';">
            </div>
            <div class="card-body">
              <div class="card-title" title="${{escapeHtml(w.name)}}">${{escapeHtml(w.name)}}</div>
              <div class="card-meta">
                <span class="category-badge ${{catClass}}">${{catName}}</span>
                <span>${{resText}} &bull; ${{w.size_human}}</span>
              </div>
              <div class="card-actions">
                <button class="btn btn-preview" onclick="openModal(${{index}})">Preview</button>
                <button class="btn btn-download" onclick="downloadImage('${{w.raw_url}}', '${{escapeHtml(w.name)}}', this)">Download</button>
              </div>
            </div>
          </div>
        `;
      }}).join('');
    }}

    function escapeHtml(str) {{
      return str.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
    }}

    async function downloadImage(url, filename, btn) {{
      const originalText = btn ? btn.textContent : '';
      if (btn) {{
        btn.textContent = 'Saving...';
        btn.disabled = true;
      }}
      try {{
        const res = await fetch(url);
        if (!res.ok) throw new Error('HTTP ' + res.status);
        const blob = await res.blob();
        const blobUrl = URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = blobUrl;
        link.download = filename;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        setTimeout(() => URL.revokeObjectURL(blobUrl), 1000);
      }} catch (err) {{
        console.warn('Direct blob download fallback to new tab:', err);
        window.open(url, '_blank');
      }} finally {{
        if (btn) {{
          btn.textContent = originalText;
          btn.disabled = false;
        }}
      }}
    }}

    function openModal(index) {{
      if (index < 0 || index >= filteredWallpapers.length) return;
      activeModalIndex = index;
      const w = filteredWallpapers[index];

      modalTitle.textContent = w.name;
      // Progressive load: show thumbnail immediately, then upgrade to full resolution
      modalImage.src = w.thumb_url;
      if (!w.is_corrupt) {{
        const fullImg = new Image();
        fullImg.src = w.raw_url;
        fullImg.onload = () => {{
          if (activeModalIndex === index) {{
            modalImage.src = w.raw_url;
          }}
        }};
      }}

      const resStr = w.width && w.height ? `${{w.width}} &times; ${{w.height}}` : (w.is_corrupt ? '⚠️ Corrupted File' : 'Original');
      const catLabel = w.category.includes('classic') ? 'Classic Wallpapers' : 'Community Wallpapers';
      modalMeta.innerHTML = `<strong>Resolution:</strong> ${{resStr}} &nbsp;|&nbsp; <strong>Size:</strong> ${{w.size_human}} &nbsp;|&nbsp; <strong>Collection:</strong> ${{catLabel}}`;
      modalDirectLink.href = w.raw_url;
      modalDownload.onclick = () => downloadImage(w.raw_url, w.name, modalDownload);

      modal.classList.add('active');
      document.body.style.overflow = 'hidden';
    }}

    function closeModal() {{
      modal.classList.remove('active');
      modalImage.src = '';
      activeModalIndex = -1;
      document.body.style.overflow = '';
    }}

    modalClose.addEventListener('click', closeModal);
    modal.addEventListener('click', (e) => {{
      if (e.target === modal) closeModal();
    }});

    modalPrev.addEventListener('click', (e) => {{
      e.stopPropagation();
      if (activeModalIndex > 0) openModal(activeModalIndex - 1);
      else openModal(filteredWallpapers.length - 1);
    }});

    modalNext.addEventListener('click', (e) => {{
      e.stopPropagation();
      if (activeModalIndex < filteredWallpapers.length - 1) openModal(activeModalIndex + 1);
      else openModal(0);
    }});

    document.addEventListener('keydown', (e) => {{
      if (!modal.classList.contains('active')) return;
      if (e.key === 'Escape') closeModal();
      else if (e.key === 'ArrowLeft') modalPrev.click();
      else if (e.key === 'ArrowRight') modalNext.click();
    }});

    // Search and Sort events
    searchInput.addEventListener('input', (e) => {{
      searchQuery = e.target.value.toLowerCase().trim();
      applyFilters();
    }});

    sortSelect.addEventListener('change', (e) => {{
      currentSort = e.target.value;
      applyFilters();
    }});

    filterButtons.forEach(btn => {{
      btn.addEventListener('click', () => {{
        filterButtons.forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        currentFilter = btn.dataset.filter;
        applyFilters();
      }});
    }});

    const mixBtn = document.getElementById('mixBtn');
    const modalRandomBtn = document.getElementById('modalRandomBtn');

    function showRandomWallpaper() {{
      if (filteredWallpapers.length === 0) return;
      let randIdx = Math.floor(Math.random() * filteredWallpapers.length);
      if (filteredWallpapers.length > 1 && randIdx === activeModalIndex) {{
        randIdx = (randIdx + 1) % filteredWallpapers.length;
      }}
      openModal(randIdx);
    }}

    if (mixBtn) mixBtn.addEventListener('click', showRandomWallpaper);
    if (modalRandomBtn) modalRandomBtn.addEventListener('click', showRandomWallpaper);

    // Initial render
    applyFilters();
  </script>
</body>
</html>
"""

    os.makedirs(output_dir, exist_ok=True)
    index_path = os.path.join(output_dir, "index.html")
    with open(index_path, "w", encoding="utf-8") as f:
        f.write(html_template)
    print(f"Generated gallery HTML at: {index_path}")


def main():
    parser = argparse.ArgumentParser(description="Generate wallpaper gallery for GitHub Pages")
    parser.add_argument("--output", default="_site", help="Destination folder for static site")
    parser.add_argument("--base-url", default="https://raw.githubusercontent.com/EndeavourOS-Community-Editions/Community-wallpapers/main", help="Base URL for raw images")
    parser.add_argument("--thumb-width", type=int, default=540, help="Max width for thumbnails")
    parser.add_argument("--thumb-quality", type=int, default=80, help="WebP compression quality")
    parser.add_argument("--repo-name", default="EndeavourOS-Community-Editions/Community-wallpapers", help="Repository slug")
    args = parser.parse_args()

    categories = ["eos_wallpapers_classic", "eos_wallpapers_community"]
    valid_exts = {".png", ".jpg", ".jpeg", ".webp"}

    tasks = []
    for cat in categories:
        if not os.path.exists(cat):
            print(f"Notice: category folder '{cat}' does not exist, skipping.")
            continue

        for fname in sorted(os.listdir(cat)):
            ext = os.path.splitext(fname)[1].lower()
            if ext in valid_exts:
                src_file = os.path.join(cat, fname)
                dest_thumb = os.path.join(args.output, "thumbnails", cat, f"{fname}.webp")
                tasks.append((src_file, dest_thumb, cat, args.base_url, args.thumb_width, args.thumb_quality))

    print(f"Processing {len(tasks)} wallpapers into '{args.output}'...")

    results = []
    # Use ProcessPoolExecutor for parallel thumbnail processing
    max_workers = min(os.cpu_count() or 4, 8)
    with ProcessPoolExecutor(max_workers=max_workers) as executor:
        for item in executor.map(process_image, tasks):
            results.append(item)

    # Sort default by name
    results.sort(key=lambda x: x["name"].lower())

    collage_src = "EndeavourOS Community Collage.png"
    has_collage = False
    raw_collage_url = f"{args.base_url}/{quote('EndeavourOS Community Collage.png')}"

    if os.path.exists(collage_src):
        try:
            dest_collage = os.path.join(args.output, "collage.webp")
            with Image.open(collage_src) as img:
                if img.mode not in ("RGB", "RGBA"):
                    img = img.convert("RGB")
                img.save(dest_collage, "WEBP", quality=85, method=6)
            has_collage = True
            print(f"Generated collage WebP at '{dest_collage}'")
        except Exception as e:
            print(f"Warning: Failed to convert collage image ({e})", file=sys.stderr)

    print(f"Generating HTML gallery with {len(results)} items...")
    generate_html(results, categories, args.output, repo_name=args.repo_name, has_collage=has_collage, raw_collage_url=raw_collage_url)
    print("Build complete!")


if __name__ == "__main__":
    main()
