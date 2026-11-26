import argparse
import json
import logging
from pathlib import Path

from . import AssetReader

logger = logging.getLogger(__package__)


def _create_reader(
    in_dir: Path, is_dh2: bool, delta_reader: AssetReader | None = None
) -> AssetReader | None:
    manifest_path = in_dir / "manifest.json"
    if not manifest_path.is_file():
        return None
    with open(manifest_path, "rt") as f:
        manifest = json.load(f)
    return AssetReader(in_dir, manifest, "DH2" if is_dh2 else "DH1", delta_reader)


def _test_extracted_archive(
    in_dir: Path, log_dir: Path, is_dh2: bool, delta_reader: AssetReader | None = None
) -> None:
    reader = _create_reader(in_dir, is_dh2, delta_reader)
    if reader is None:
        return

    logger.setLevel(logging.DEBUG)
    handler = logging.FileHandler(log_dir / f"{in_dir.name}.log")
    handler.setFormatter(logging.Formatter("%(levelname)s: %(message)s"))
    logger.addHandler(handler)

    string_map: dict[str, str] = reader.manifest["strings"]
    chunk_map: dict[str, dict] = reader.manifest["chunks"]
    for chunk_id in chunk_map.keys():
        name = string_map[chunk_id]
        if ":" not in name:
            continue
        category, _, stored_path = name.partition(":")

        if category == "SKL":
            skl_path = in_dir / (stored_path + ".SKL")
            if not skl_path.is_file():
                continue
            try:
                reader.read_skl(skl_path)
            except:
                logger.exception('Failed to read SKL file at "%s"', skl_path)

        elif category == "MSH":
            msh_path = in_dir / (stored_path + ".MSH")
            if not msh_path.is_file():
                continue
            try:
                reader.read_msh(msh_path)
            except:
                logger.exception('Failed to read MSH file at "%s"', msh_path)

    logger.removeHandler(handler)
    handler.close()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "in_dir",
        type=Path,
        help="path to an extracted .bin.gz archive",
    )
    parser.add_argument(
        "-n",
        "--nested",
        action="store_true",
        help="treat each folder in in_dir as an extracted .bin.gz archive",
    )
    parser.add_argument(
        "--dh2",
        action="store_true",
        help="use when reading archives from Deathly Hallows - Part 2",
    )
    args = parser.parse_args()
    in_dir: Path = args.in_dir
    is_nested: bool = args.nested
    is_dh2: bool = args.dh2

    log_dir = Path("./logs/")
    if is_dh2:
        log_dir = log_dir / "dh2"
    else:
        log_dir = log_dir / "dh1"
    log_dir.mkdir(parents=True, exist_ok=True)

    if is_nested:
        delta_reader = None
        delta_dir = in_dir / "delta-global"
        if delta_dir.is_dir():
            delta_reader = _create_reader(delta_dir, is_dh2)

        for sub_dir in in_dir.iterdir():
            if not sub_dir.is_dir():
                continue
            _test_extracted_archive(sub_dir, log_dir, is_dh2, delta_reader)
    else:
        _test_extracted_archive(in_dir, log_dir, is_dh2)


if __name__ == "__main__":
    main()
