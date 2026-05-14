"""
strip_extra_opts.py

Sanitises a YOLOv5 checkpoint trained on Windows so it loads cleanly on Linux
(and vice-versa).  Run this once after training, before copying the model over.

What it fixes
─────────────
  • pathlib.WindowsPath / PosixPath objects embedded in the checkpoint –
    converted to plain strings via a scoped pickle_module override so that
    Python's own path code is never touched.
  • Extra top-level keys not present in the reference model (e.g. 'opt', 'git').
  • Extra opt sub-keys not present in the reference model.
  • cache='ram' forced to False (prevents the dataset being loaded into RAM).

Usage
─────
  # Compare against a known-good reference checkpoint:
  python strip_extra_opts.py --reference working.pt --target best.pt --output best_clean.pt

  # No reference — just fix paths + cache, keep everything else:
  python strip_extra_opts.py --target best.pt --output best_clean.pt
"""

import argparse
import pickle
import pathlib
import sys
import types
import torch


# ──────────────────────────────────────────────────────────────────────────────
# Cross-platform loader
#
# The problem: PyTorch pickles live Path objects into checkpoints.
# WindowsPath can't be constructed on Linux, PosixPath can't be constructed
# on Windows.  Patching pathlib *globally* breaks Python's own path code
# (e.g. `Path(__file__).resolve()` in yolov5/models/yolo.py).
#
# The fix: pass a custom pickle_module to torch.load.  This intercepts path
# construction *only* during deserialization and leaves the rest of Python alone.
# ──────────────────────────────────────────────────────────────────────────────

def _make_pickle_module():
    """
    Return a drop-in pickle module whose Unpickler converts any pathlib
    WindowsPath or PosixPath into a plain str during deserialization.
    """
    class _CrossPlatformUnpickler(pickle.Unpickler):
        def find_class(self, module, name):
            if module == "pathlib" and name in ("WindowsPath", "PosixPath", "Path"):
                # Return a plain-string factory — works on any OS
                return lambda *parts: str(pathlib.PurePosixPath(*parts))
            return super().find_class(module, name)

    # Build a module-like object that looks like `pickle` but swaps Unpickler
    mod = types.ModuleType("_cross_platform_pickle")
    mod.__dict__.update(pickle.__dict__)
    mod.Unpickler = _CrossPlatformUnpickler
    return mod


_PICKLE_MODULE = _make_pickle_module()


def _ensure_yolov5_on_path():
    """Add the pip-installed yolov5 package dir to sys.path if needed."""
    try:
        import models  # noqa: F401 – already importable, nothing to do
        return
    except ImportError:
        pass
    try:
        import yolov5 as _yv5
        yv5_dir = str(pathlib.Path(_yv5.__file__).parent)
        if yv5_dir not in sys.path:
            sys.path.insert(0, yv5_dir)
    except ImportError:
        pass  # user must have the yolov5 repo on PYTHONPATH themselves


def load_ckpt(path):
    """
    Load a YOLOv5 .pt checkpoint on any OS, regardless of where it was saved.
    """
    _ensure_yolov5_on_path()
    return torch.load(path, map_location="cpu", weights_only=False,
                      pickle_module=_PICKLE_MODULE)


# ──────────────────────────────────────────────────────────────────────────────
# Opt helpers
# ──────────────────────────────────────────────────────────────────────────────

def _opt_as_dict(opt):
    if opt is None:
        return {}
    if isinstance(opt, dict):
        return opt
    return vars(opt)


def _set_opt_key(opt, key, value):
    if isinstance(opt, dict):
        opt[key] = value
    else:
        setattr(opt, key, value)


def _del_opt_key(opt, key):
    if isinstance(opt, dict):
        del opt[key]
    else:
        delattr(opt, key)


# ──────────────────────────────────────────────────────────────────────────────
# Main sanitise function
# ──────────────────────────────────────────────────────────────────────────────

def strip_extra_opts(target_path, output_path, reference_path=None):

    print(f"Loading target    : {target_path}")
    tgt = load_ckpt(target_path)

    ref_keys = set()
    ref_opt_keys = set()
    if reference_path:
        print(f"Loading reference : {reference_path}")
        ref = load_ckpt(reference_path)
        ref_keys = set(ref.keys())
        ref_opt_keys = set(_opt_as_dict(ref.get("opt")).keys())

    # ── 1. Remove top-level keys absent from reference ────────────────────────
    if reference_path:
        extra_top = set(tgt.keys()) - ref_keys
        if extra_top:
            print(f"\nRemoving top-level keys not in reference: {sorted(extra_top)}")
            for k in sorted(extra_top):
                print(f"  - '{k}': {repr(tgt[k])[:100]}")
                del tgt[k]
        else:
            print("\nNo extra top-level keys found.")

    # ── 2. Remove opt sub-keys absent from reference ──────────────────────────
    if reference_path and "opt" in tgt:
        tgt_opt_dict = _opt_as_dict(tgt["opt"])
        extra_opt = set(tgt_opt_dict.keys()) - ref_opt_keys
        if extra_opt:
            print(f"\nRemoving opt sub-keys not in reference: {sorted(extra_opt)}")
            for k in sorted(extra_opt):
                print(f"  - opt['{k}']: {repr(tgt_opt_dict[k])[:80]}")
                _del_opt_key(tgt["opt"], k)

    # ── 3. Always sanitise cache and stray Path objects inside opt ────────────
    if "opt" in tgt:
        opt = tgt["opt"]
        opt_dict = _opt_as_dict(opt)

        # Force cache off — 'ram' causes the entire dataset to be loaded into memory
        cache = opt_dict.get("cache")
        if cache and cache is not False:
            print(f"\n  ⚠  opt.cache = {repr(cache)} → False  (was causing RAM explosion)")
            _set_opt_key(opt, "cache", False)

        # Belt-and-suspenders: stringify any Path values that slipped through
        for k, v in list(opt_dict.items()):
            if isinstance(v, pathlib.PurePath):
                _set_opt_key(opt, k, str(v))

    # ── 4. Save ───────────────────────────────────────────────────────────────
    torch.save(tgt, output_path)
    print(f"\n✅  Saved to: {output_path}")

    # ── 5. Verify round-trip ──────────────────────────────────────────────────
    verify = load_ckpt(output_path)
    print(f"    Top-level keys : {sorted(verify.keys())}")
    if "opt" in verify:
        print(f"    opt keys       : {sorted(_opt_as_dict(verify['opt']).keys())}")
        print(f"    opt.cache      : {_opt_as_dict(verify['opt']).get('cache')}")


# ──────────────────────────────────────────────────────────────────────────────
# CLI
# ──────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Sanitise a YOLOv5 checkpoint for cross-platform deployment.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument("--target",    required=True,  help="Checkpoint to clean (e.g. best.pt)")
    parser.add_argument("--output",    required=True,  help="Where to write the cleaned checkpoint")
    parser.add_argument("--reference", required=False, help="Known-good checkpoint to diff against (optional)")
    args = parser.parse_args()

    strip_extra_opts(
        target_path=args.target,
        output_path=args.output,
        reference_path=args.reference,
    )