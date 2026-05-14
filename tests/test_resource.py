import os
import unittest

from nte_auto_fish.utils.resource import app_root, bundled_root, project_root, resource_path


class TestResourcePaths(unittest.TestCase):
    def test_project_root_is_absolute_repo_root(self):
        self.assertTrue(os.path.isabs(project_root()))
        self.assertTrue(os.path.exists(os.path.join(project_root(), "start_gui.py")))

    def test_resource_path_resolves_assets_from_source_tree(self):
        logo_path = resource_path(os.path.join("assets", "chiz_logo_header_transparent.png"))

        self.assertTrue(os.path.isabs(logo_path))
        self.assertTrue(os.path.exists(logo_path))

    def test_app_and_bundled_roots_match_source_root_when_not_frozen(self):
        self.assertEqual(app_root(), project_root())
        self.assertEqual(bundled_root(), project_root())


if __name__ == "__main__":
    unittest.main()
