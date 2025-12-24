#!/usr/bin/env python3
"""
Upstream test case for Task Composer plugin loading.

This test demonstrates plugin loading behavior on macOS.
Use this to debug/report issues to tesseract_python_nanobind.

Run with: python tests/test_task_composer_plugin_loading.py
"""
from __future__ import annotations

import os
import sys
from pathlib import Path


def find_config_file() -> Path | None:
    """Search for task_composer_plugins.yaml in common locations."""
    candidates = [
        # User install location
        Path.home() / "Code/CADCAM/tesseract_python_nanobind/ws/install/share/tesseract_task_composer/config/task_composer_plugins.yaml",
        # System install
        Path("/usr/local/share/tesseract_task_composer/config/task_composer_plugins.yaml"),
        # Conda env
        Path(sys.prefix) / "share/tesseract_task_composer/config/task_composer_plugins.yaml",
    ]

    # Also check TESSERACT_TASK_COMPOSER_CONFIG_FILE env var
    env_path = os.environ.get("TESSERACT_TASK_COMPOSER_CONFIG_FILE")
    if env_path:
        candidates.insert(0, Path(env_path))

    for p in candidates:
        if p.exists():
            return p
    return None


def test_import_modules():
    """Test that tesseract modules can be imported."""
    print("\n=== Testing Module Imports ===")

    try:
        import tesseract_robotics
        print(f"✓ tesseract_robotics imported (version: {getattr(tesseract_robotics, '__version__', 'unknown')})")
    except ImportError as e:
        print(f"✗ Failed to import tesseract_robotics: {e}")
        return False

    try:
        from tesseract_robotics import tesseract_task_composer as tc
        print("✓ tesseract_task_composer imported")
    except ImportError as e:
        print(f"✗ Failed to import tesseract_task_composer: {e}")
        return False

    try:
        from tesseract_robotics.tesseract_common import GeneralResourceLocator
        print("✓ GeneralResourceLocator imported")
    except ImportError as e:
        print(f"✗ Failed to import GeneralResourceLocator: {e}")
        return False

    return True


def test_config_file():
    """Test that config file can be found."""
    print("\n=== Testing Config File ===")

    config_path = find_config_file()
    if config_path is None:
        print("✗ No task_composer_plugins.yaml found")
        print("  Checked locations:")
        for p in [
            Path.home() / "Code/CADCAM/tesseract_python_nanobind/ws/install/share/tesseract_task_composer/config/task_composer_plugins.yaml",
            Path("/usr/local/share/tesseract_task_composer/config/task_composer_plugins.yaml"),
            Path(sys.prefix) / "share/tesseract_task_composer/config/task_composer_plugins.yaml",
        ]:
            print(f"    {p} {'(exists)' if p.exists() else '(not found)'}")
        return None

    print(f"✓ Found config: {config_path}")
    print(f"  Size: {config_path.stat().st_size} bytes")

    # Show first few lines
    with open(config_path) as f:
        lines = f.readlines()[:20]
        print("  Content preview:")
        for line in lines:
            print(f"    {line.rstrip()}")

    return config_path


def test_factory_creation(config_path: Path):
    """Test creating TaskComposerPluginFactory."""
    print("\n=== Testing Factory Creation ===")

    from tesseract_robotics import tesseract_task_composer as tc
    from tesseract_robotics.tesseract_common import GeneralResourceLocator

    loc = GeneralResourceLocator()
    print(f"✓ Created GeneralResourceLocator")

    try:
        factory = tc.createTaskComposerPluginFactory(str(config_path), loc)
        print(f"✓ Created TaskComposerPluginFactory")
        return factory
    except Exception as e:
        print(f"✗ Failed to create factory: {e}")
        return None


def test_executor_creation(factory):
    """Test creating executors from factory."""
    print("\n=== Testing Executor Creation ===")

    from tesseract_robotics import tesseract_task_composer as tc

    # Try to list available executors
    executor_names = ["TaskflowExecutor", "taskflow_executor"]

    for name in executor_names:
        print(f"\nTrying to create executor: '{name}'")
        try:
            executor = factory.createTaskComposerExecutor(name)
            if executor is None:
                print(f"  ✗ Factory returned None for '{name}'")
            else:
                print(f"  ✓ Created executor '{name}'")
                return executor
        except Exception as e:
            print(f"  ✗ Exception creating '{name}': {e}")

    # Try creating directly
    print("\nTrying direct TaskflowTaskComposerExecutor creation:")
    try:
        executor = tc.TaskflowTaskComposerExecutor("test_executor", 4)
        print(f"  ✓ Created TaskflowTaskComposerExecutor directly")
        return executor
    except Exception as e:
        print(f"  ✗ Exception: {e}")

    return None


def test_task_creation(factory):
    """Test creating task nodes from factory."""
    print("\n=== Testing Task Creation ===")

    task_names = [
        "CartesianPipeline",
        "FreespaceMotionPipelineTask",
        "SimpleMotionPlannerTask",
        "OMPLMotionPlannerTask",
        "TrajOptMotionPlannerTask",
        "DescartesFMotionPlannerTask",
    ]

    for name in task_names:
        print(f"\nTrying to create task: '{name}'")
        try:
            task = factory.createTaskComposerNode(name)
            if task is None:
                print(f"  ✗ Factory returned None for '{name}'")
            else:
                print(f"  ✓ Created task '{name}'")
        except Exception as e:
            print(f"  ✗ Exception creating '{name}': {e}")


def test_available_plugins(factory):
    """Try to enumerate available plugins."""
    print("\n=== Checking Available Plugins ===")

    # Check if factory has methods to list plugins
    factory_attrs = [a for a in dir(factory) if not a.startswith('_')]
    print(f"Factory methods: {factory_attrs}")

    # Try common method patterns
    list_methods = [
        "getAvailableExecutors",
        "getExecutorNames",
        "listExecutors",
        "getAvailableTasks",
        "getTaskNames",
        "listTasks",
    ]

    for method in list_methods:
        if hasattr(factory, method):
            try:
                result = getattr(factory, method)()
                print(f"  {method}(): {result}")
            except Exception as e:
                print(f"  {method}(): Exception - {e}")


def test_environment_vars():
    """Show relevant environment variables."""
    print("\n=== Environment Variables ===")

    relevant_vars = [
        "DYLD_LIBRARY_PATH",
        "DYLD_FALLBACK_LIBRARY_PATH",
        "LD_LIBRARY_PATH",
        "TESSERACT_RESOURCE_PATH",
        "TESSERACT_TASK_COMPOSER_CONFIG_FILE",
        "PATH",
        "CONDA_PREFIX",
    ]

    for var in relevant_vars:
        val = os.environ.get(var, "(not set)")
        if len(val) > 100:
            val = val[:100] + "..."
        print(f"  {var}: {val}")


def main():
    """Run all tests."""
    print("=" * 60)
    print("Task Composer Plugin Loading Test")
    print("=" * 60)
    print(f"Python: {sys.version}")
    print(f"Platform: {sys.platform}")
    print(f"Prefix: {sys.prefix}")

    test_environment_vars()

    if not test_import_modules():
        print("\n❌ Module import failed - cannot continue")
        return 1

    config_path = test_config_file()
    if config_path is None:
        print("\n❌ Config file not found - cannot continue")
        return 1

    factory = test_factory_creation(config_path)
    if factory is None:
        print("\n❌ Factory creation failed - cannot continue")
        return 1

    test_available_plugins(factory)
    test_executor_creation(factory)
    test_task_creation(factory)

    print("\n" + "=" * 60)
    print("Test complete")
    print("=" * 60)
    return 0


if __name__ == "__main__":
    sys.exit(main())
