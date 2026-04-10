"""Unified test: environment version check, CDM calculation, and demo smoke test.

Usage:
    python -m pytest tests/test_environment_and_smoke.py -v
    python -m pytest tests/test_environment_and_smoke.py::TestEnvironmentVersions -v
    python -m pytest tests/test_environment_and_smoke.py::TestCDMCalculation -v
    python -m pytest tests/test_environment_and_smoke.py -m slow -v -s  # includes full demo eval
"""

import json
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))


# ---------------------------------------------------------------------------
# Docker reference versions (from ENV_VERSION_MANIFEST_REPRO.md)
# ---------------------------------------------------------------------------
DOCKER_REFERENCE = {
    "python": "3.10",
    "texlive_year": "2025",
    "pdflatex_version": "3.141592653-2.6-1.40.28",
    "imagemagick_version": "7.1.1-47",
    "ghostscript_version": "9.55.0",
    "cjk_font_family": "gkai",
    "pip": "26.0.1",
    "setuptools": "82.0.1",
    "wheel": "0.46.3",
}


# ===========================================================================
# Test 1: Environment version comparison
# ===========================================================================
class TestEnvironmentVersions:
    """Output current environment versions and compare against Docker reference."""

    def test_environment_versions(self):
        from src.runtime.eval_report import collect_runtime_environment_report

        report = collect_runtime_environment_report()
        system = report.get("system", {})
        ext_tools = report.get("external_tools", {})
        py_packages = report.get("python_packages", {})
        texlive = report.get("texlive", {})

        # -- Collect current versions --
        python_ver = system.get("python_version", "").split()[0]
        python_major_minor = ".".join(python_ver.split(".")[:2])

        pdflatex_out = ext_tools.get("pdflatex", {}).get("output", "")
        pdflatex_match = re.search(r"pdfTeX\s+([\d.-]+)", pdflatex_out)
        pdflatex_ver = pdflatex_match.group(1) if pdflatex_match else "not found"

        texlive_match = re.search(r"TeX Live (\d{4})", pdflatex_out)
        texlive_year = texlive_match.group(1) if texlive_match else "not found"

        magick_out = ext_tools.get("magick", {}).get("output", "")
        magick_match = re.search(r"ImageMagick\s+([\d.-]+)", magick_out)
        magick_ver = magick_match.group(1) if magick_match else "not found"

        gs_out = ext_tools.get("ghostscript", {}).get("output", "")
        gs_ver = gs_out.split("|")[0].strip() if gs_out else "not found"

        cjk_family = texlive.get("cjk_font_family", "not found")

        pip_ver = py_packages.get("pip", "not found")
        setuptools_ver = py_packages.get("setuptools", "not found")
        wheel_ver = py_packages.get("wheel", "not found")

        current = {
            "python": python_major_minor,
            "texlive_year": texlive_year,
            "pdflatex_version": pdflatex_ver,
            "imagemagick_version": magick_ver,
            "ghostscript_version": gs_ver,
            "cjk_font_family": cjk_family,
            "pip": pip_ver,
            "setuptools": setuptools_ver,
            "wheel": wheel_ver,
        }

        # -- Print comparison table --
        print("\n" + "=" * 72)
        print(f"{'Component':<25} {'Current':<25} {'Docker Reference':<20}")
        print("-" * 72)

        mismatches = []
        for key in DOCKER_REFERENCE:
            cur = current.get(key, "N/A")
            ref = DOCKER_REFERENCE[key]
            match_str = "OK" if cur == ref else "DIFF"
            if match_str == "DIFF":
                mismatches.append(key)
            print(f"{key:<25} {cur:<25} {ref:<20} {match_str}")

        print("=" * 72)
        if mismatches:
            print(f"\nMismatched components: {', '.join(mismatches)}")
            print("Note: Minor version differences (e.g. pip, setuptools) are acceptable.")
            print("Critical components: python, texlive_year, cjk_font_family")
        else:
            print("\nAll versions match Docker reference.")

        # -- Assertions for critical components --
        assert python_major_minor == DOCKER_REFERENCE["python"], \
            f"Python version mismatch: {python_major_minor} vs {DOCKER_REFERENCE['python']}"
        assert texlive_year == DOCKER_REFERENCE["texlive_year"], \
            f"TeX Live year mismatch: {texlive_year} vs {DOCKER_REFERENCE['texlive_year']}"
        assert cjk_family == DOCKER_REFERENCE["cjk_font_family"], \
            f"CJK font family mismatch: {cjk_family} vs {DOCKER_REFERENCE['cjk_font_family']}"

    def test_critical_tools_available(self):
        """Verify critical external tools are on PATH."""
        from src.metrics.cdm.modules.texlive_env import build_tex_env, resolve_tex_binary

        tex_env = build_tex_env()
        pdflatex = resolve_tex_binary("pdflatex")
        kpsewhich = resolve_tex_binary("kpsewhich")

        assert shutil.which(pdflatex, path=tex_env.get("PATH")) or shutil.which(pdflatex), \
            f"pdflatex not found: {pdflatex}"
        assert shutil.which(kpsewhich, path=tex_env.get("PATH")) or shutil.which(kpsewhich), \
            f"kpsewhich not found: {kpsewhich}"
        assert shutil.which("gs"), "Ghostscript (gs) not found on PATH"
        assert shutil.which("magick") or shutil.which("convert"), \
            "ImageMagick (magick or convert) not found on PATH"

    def test_cjk_resources(self):
        """Verify TeX Live CJK resources are installed."""
        from src.metrics.cdm.modules.texlive_env import build_tex_env, resolve_tex_binary

        tex_env = build_tex_env()
        kpsewhich = resolve_tex_binary("kpsewhich")

        for resource in ["CJK.sty", "c70gkai.fd"]:
            r = subprocess.run(
                [kpsewhich, resource],
                capture_output=True, text=True, timeout=10, env=tex_env,
            )
            assert r.returncode == 0 and r.stdout.strip(), \
                f"CJK resource not found: {resource}"


# ===========================================================================
# Test 2: CDM calculation test cases
# ===========================================================================
class TestCDMCalculation:
    """Test CDM metric with known LaTeX pairs."""

    def test_cdm_identical(self):
        """Identical LaTeX should give CDM F1 = 1.0."""
        from src.metrics.cdm.cdm import cdm

        latex = r"E = mc^2"
        score = cdm(latex, latex)
        assert score == pytest.approx(1.0, abs=0.01), \
            f"CDM of identical LaTeX should be ~1.0, got {score}"

    def test_cdm_basic_cjk(self):
        """CDM of a non-trivial CJK formula should return a valid score."""
        from src.metrics.cdm.cdm import cdm

        latex = r"\mathrm{传动侧} + \text{效率} = \frac{1}{2}"
        score = cdm(latex, latex)
        assert 0.9 <= score <= 1.0, f"CDM self-score should be near 1.0, got {score}"

    def test_cdm_different(self):
        """CDM of different formulas should be < 1.0."""
        from src.metrics.cdm.cdm import cdm

        latex_gt = r"\frac{a}{b} + c"
        latex_pred = r"\frac{x}{y} - z"
        score = cdm(latex_gt, latex_pred)
        assert 0.0 <= score < 1.0, f"CDM of different formulas should be < 1.0, got {score}"

    def test_cdm_metrics_returns_dict(self):
        """cdm_metrics should return a dict with expected keys."""
        from src.metrics.cdm.cdm import cdm_metrics

        result = cdm_metrics(r"a + b", r"a + b")
        assert isinstance(result, dict)
        for key in ["recall", "precision", "F1_score"]:
            assert key in result, f"Missing key: {key}"
            assert 0.0 <= result[key] <= 1.0

    def test_latex2bbox_smoke(self):
        """Verify latex2bbox_color renders a LaTeX string to bbox + PNG."""
        from src.metrics.cdm.cdm import gen_color_list
        from src.metrics.cdm.modules.latex2bbox_color import latex2bbox_color

        latex = r"\mathrm{传动侧} + \text{效率} = \frac{1}{2}"
        color_list = gen_color_list(num=5800)

        with tempfile.TemporaryDirectory(prefix="test_cdm_") as tmpdir:
            tmp = Path(tmpdir)
            output_root = tmp / "output"
            temp_root = tmp / "temp"
            (output_root / "bbox").mkdir(parents=True)
            (output_root / "vis").mkdir(parents=True)
            temp_root.mkdir(parents=True)

            latex2bbox_color((latex, "test_case", str(output_root), str(temp_root), color_list))

            bbox_path = output_root / "bbox" / "test_case.jsonl"
            base_png = output_root / "vis" / "test_case_base.png"
            assert bbox_path.exists(), f"bbox not generated: {bbox_path}"
            assert base_png.exists(), f"base PNG not generated: {base_png}"

            lines = [l for l in bbox_path.read_text().splitlines() if l.strip()]
            assert len(lines) > 0, "bbox jsonl is empty"


# ===========================================================================
# Test 3: Demo end-to-end smoke test
# ===========================================================================
class TestDemoSmoke:
    """Verify the project can load configs and run the demo evaluation."""

    def test_core_imports(self):
        """Core modules should be importable."""
        from src.core import matching, metrics, pipeline, preprocess, registry
        assert callable(pipeline.run_config_file)
        assert callable(matching.match_gt2pred_quick)
        assert callable(metrics.show_result)
        assert callable(preprocess.normalized_table)
        assert callable(preprocess.strip_formula_tags)

    def test_load_end2end_config(self):
        """configs/end2end.yaml should load and contain expected structure."""
        from src.core.pipeline import load_config

        config_path = REPO_ROOT / "configs" / "end2end.yaml"
        assert config_path.exists(), f"Config not found: {config_path}"

        config = load_config(config_path)
        assert "end2end_eval" in config

    def test_demo_data_exists(self):
        """Demo data files required by end2end.yaml should exist."""
        gt_path = REPO_ROOT / "demo_data" / "omnidocbench_demo" / "OmniDocBench_demo.json"
        pred_path = REPO_ROOT / "demo_data" / "end2end"

        assert gt_path.exists(), f"GT data not found: {gt_path}"
        assert pred_path.exists(), f"Prediction data not found: {pred_path}"

        with open(gt_path, "r") as f:
            gt = json.load(f)
        assert len(gt) > 0, "GT data is empty"

        md_files = list(pred_path.glob("*.md"))
        assert len(md_files) > 0, "No prediction markdown files found"

    def test_registry_registrations(self):
        """Core registries should have expected entries."""
        from src.core.registry import describe_registries

        registries = describe_registries()
        assert "end2end_eval" in str(registries), \
            f"end2end_eval not registered: {registries}"

    def test_preprocess_functions(self):
        """Preprocessing functions should produce expected output."""
        from src.core.preprocess import normalized_table, strip_formula_tags

        html = normalized_table(
            "<table><tr><td>A</td><td>B</td></tr></table>", "html"
        )
        assert "<table>" in html.lower() or "<tr>" in html.lower()

        formula = strip_formula_tags(r"$$a=b \tag{1}$$")
        assert r"\tag" not in formula

    @pytest.mark.slow
    def test_demo_end2end(self):
        """Run the full demo end-to-end evaluation (configs/end2end.yaml).

        This test actually runs the pipeline and can take several minutes
        (especially CDM rendering). Mark with @pytest.mark.slow.
        Run with: pytest -m slow -v -s
        """
        import os

        config_path = REPO_ROOT / "configs" / "end2end.yaml"
        original_cwd = os.getcwd()

        try:
            os.chdir(REPO_ROOT)
            from src.core.pipeline import run_config_file
            run_config_file(config_path)
        finally:
            os.chdir(original_cwd)

        result_dir = REPO_ROOT / "result"
        metric_files = list(result_dir.glob("*_metric_result.json"))
        assert len(metric_files) > 0, "No metric result files generated"

        with open(metric_files[0], "r") as f:
            result = json.load(f)

        for element in ["text_block", "display_formula", "table", "reading_order"]:
            assert element in result, f"Missing element: {element}"
