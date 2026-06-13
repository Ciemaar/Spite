import zipfile

from spite.packager import create_zip_payload, init_local_repo


def test_create_zip_payload():
    specs = {
        "REQUIREMENTS.md": "# Requirements\n\n- Do stuff",
        "AGENTS.md": "# Agents\n\n- Be smart",
    }

    zip_buffer = create_zip_payload(specs)

    with zipfile.ZipFile(zip_buffer, 'r') as zf:
        assert set(zf.namelist()) == {"REQUIREMENTS.md", "AGENTS.md"}
        assert zf.read("REQUIREMENTS.md").decode() == "# Requirements\n\n- Do stuff"

def test_init_local_repo():
    repo_path = init_local_repo()
    assert repo_path.exists()
    assert repo_path.is_dir()
    assert (repo_path / ".git").exists()
