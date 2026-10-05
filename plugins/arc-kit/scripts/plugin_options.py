import os


def option(key, default):
    # Claude Code exports each userConfig key uppercased: CLAUDE_PLUGIN_OPTION_<KEY>.
    return os.environ.get(f"CLAUDE_PLUGIN_OPTION_{key.upper()}", "").strip() or default
