# GEN220: High Throughput Biological Data Analysis - Fall 2026

Course website for GEN220 at UC Riverside: <https://biodataprog.github.io/GEN220_2026/>

## Layout

- `docs/` - the website (Jekyll, [Just the Docs](https://just-the-docs.com/) theme). `docs/index.md` is the home page.
  - `UNIX/`, `Python/`, `Bioinformatics/`, `Misc/` - lectures
  - `Assignments/` - homework and project instructions
  - `Resources/` - syllabus, git and SSH guides
- `.github/workflows/jekyll-gh-pages.yml` - builds and deploys the site on every push to `main` that touches `docs/`.

## Adding or editing a lecture

1. Write or edit the markdown file in the right folder. Lecture files do not need front matter.
2. For a new file, add a line for it in the `defaults:` section of `docs/_config.yml` (title, parent section, `nav_order`) so it shows up in the sidebar, and link it from `docs/index.md`.
3. Rebuild the PDF handouts with `make` inside that folder (requires `pandoc` and a LaTeX install). PDFs are committed alongside the markdown.

## Previewing locally

```bash
gem install jekyll bundler
cd docs
cat > Gemfile <<'EOF'
source "https://rubygems.org"
gem "github-pages", group: :jekyll_plugins
gem "webrick"
EOF
bundle install
bundle exec jekyll serve
```

(Don't commit that `Gemfile`; the GitHub Pages action supplies its own.)
