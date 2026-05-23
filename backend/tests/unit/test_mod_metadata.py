import json
import zipfile

from app.services.mod_metadata import read_mod_metadata


def test_reads_fabric_environment_from_jar(tmp_path):
    jar_path = tmp_path / "client-env-mod.jar"
    with zipfile.ZipFile(jar_path, "w") as jar:
        jar.writestr(
            "fabric.mod.json",
            json.dumps(
                {
                    "id": "client-env-mod",
                    "name": "Client Env Mod",
                    "version": "1.0.0",
                    "environment": "client",
                }
            ),
        )

    metadata = read_mod_metadata(jar_path)

    assert metadata is not None
    assert metadata.mod_id == "client-env-mod"
    assert metadata.environment == "client"
    assert metadata.source == "fabric.mod.json"


def test_reads_quilt_environment_from_jar(tmp_path):
    jar_path = tmp_path / "quilt-client.jar"
    with zipfile.ZipFile(jar_path, "w") as jar:
        jar.writestr(
            "quilt.mod.json",
            json.dumps(
                {
                    "quilt_loader": {
                        "id": "quilt-client",
                        "version": "1.0.0",
                        "metadata": {"name": "Quilt Client"},
                    },
                    "environment": "client",
                }
            ),
        )

    metadata = read_mod_metadata(jar_path)

    assert metadata is not None
    assert metadata.mod_id == "quilt-client"
    assert metadata.environment == "client"
    assert metadata.source == "quilt.mod.json"


def test_invalid_jar_returns_none(tmp_path):
    jar_path = tmp_path / "not-real.jar"
    jar_path.write_text("not a zip", encoding="utf-8")

    assert read_mod_metadata(jar_path) is None
