import importlib.util
import os
import pathlib
import tempfile
import unittest

import matplotlib

matplotlib.use("Agg", force=True)

SCRIPT = (
    pathlib.Path(__file__).parents[1]
    / "skills"
    / "nature-figure"
    / "scripts"
    / "civil_engineering_style.py"
)
SPEC = importlib.util.spec_from_file_location("civil_engineering_style", SCRIPT)
STYLE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(STYLE)


class CivilEngineeringPngAuditTests(unittest.TestCase):
    def audit_with_text(self, font_pt, min_font_pt=None):
        import matplotlib.pyplot as plt

        STYLE.apply_civil_engineering_style()
        fig, ax = plt.subplots(figsize=(3.4, 2.6))
        ax.plot([0, 1], [0, 1])
        ax.set_xlabel("x")
        ax.set_ylabel("y")
        fig.text(0.5, 0.97, "font threshold probe", ha="center", va="top",
                 fontsize=font_pt)
        fig.subplots_adjust(left=0.2, bottom=0.2, right=0.95, top=0.84)
        with tempfile.TemporaryDirectory(
            dir=os.environ.get("NATURE_FIGURE_TEST_TMP") or None
        ) as directory:
            output = pathlib.Path(directory) / "probe.png"
            fig.savefig(output, dpi=300)
            kwargs = {} if min_font_pt is None else {"min_font_pt": min_font_pt}
            report = STYLE.audit_png_output(fig, output, [ax], dpi=300, **kwargs)
        plt.close(fig)
        return report

    def test_three_point_text_fails_five_point_threshold(self):
        report = self.audit_with_text(3, min_font_pt=5)
        self.assertEqual(report["minimum_font_size_check"], "FAIL")
        self.assertTrue(any("below minimum font size 5 pt" in item
                            for item in report["findings"]))

    def test_text_at_configured_threshold_passes(self):
        report = self.audit_with_text(8, min_font_pt=8)
        self.assertEqual(report["minimum_text_artist_size_pt"], 8.0)
        self.assertEqual(report["minimum_font_size_check"], "PASS")

    def test_normal_civil_engineering_text_passes_default_eight_point_floor(self):
        report = self.audit_with_text(10.5)
        self.assertEqual(report["minimum_font_size_pt"], 8.0)
        self.assertEqual(report["minimum_font_size_check"], "PASS")


if __name__ == "__main__":
    unittest.main()
