from pathlib import Path
import json
import unittest


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]


class NativeAwsDeploymentTests(unittest.TestCase):
    def test_all_remotion_packages_use_one_exact_version(self):
        package_files = (
            "dashboard/package.json",
            "render-service/package.json",
            "remotion/package.json",
        )
        versions = {}

        for package_file in package_files:
            manifest = json.loads(
                (REPOSITORY_ROOT / package_file).read_text(encoding="utf-8")
            )
            for dependency_group in ("dependencies", "devDependencies"):
                for name, version in manifest.get(dependency_group, {}).items():
                    if name == "remotion" or name.startswith("@remotion/"):
                        versions[f"{package_file}:{name}"] = version

        self.assertTrue(versions)
        unique_versions = set(versions.values())
        self.assertEqual(1, len(unique_versions), versions)
        for version in unique_versions:
            self.assertRegex(version, r"^\d+\.\d+\.\d+$")
        self.assertTrue(
            (REPOSITORY_ROOT / "remotion/package-lock.json").is_file(),
            "The Remotion composition workspace must have a committed lockfile",
        )

    def test_renderer_binds_to_loopback_only(self):
        server_source = (
            REPOSITORY_ROOT / "render-service/src/server.ts"
        ).read_text(encoding="utf-8")
        service_unit = (
            REPOSITORY_ROOT
            / "deploy/aws-native/openshorts-renderer.service"
        ).read_text(encoding="utf-8")

        self.assertIn('const HOST = process.env.HOST || "127.0.0.1";', server_source)
        self.assertIn("app.listen(PORT, HOST,", server_source)
        self.assertIn(
            "ExecStart=/usr/bin/env HOST=127.0.0.1 PORT=3100 ",
            service_unit,
        )

    def test_landing_page_does_not_advertise_removed_docker_runtime(self):
        landing_source = (
            REPOSITORY_ROOT / "dashboard/src/Landing.jsx"
        ).read_text(encoding="utf-8")
        page_metadata = (
            REPOSITORY_ROOT / "dashboard/index.html"
        ).read_text(encoding="utf-8")

        for stale_phrase in (
            "Deploy with Docker",
            "Docker Compose setup",
            "requires Docker self-hosting",
            "runs on any system with Docker installed",
            "Self-host with Docker",
        ):
            self.assertNotIn(stale_phrase, landing_source)

        self.assertNotIn("Docker", landing_source)
        self.assertNotIn("Docker", page_metadata)


if __name__ == "__main__":
    unittest.main()
