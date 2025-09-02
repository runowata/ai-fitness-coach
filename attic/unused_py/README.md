# Development Tools

This directory contains development and debugging tools that are not needed in production.

## Management Commands

The `management_commands/` directory contains Django management commands for:

- **Debug tools**: Commands for debugging specific issues (debug_workout_video.py, etc.)
- **Test tools**: Commands for testing AI integration and video systems
- **Smoke tests**: Basic connectivity and functionality tests (ai_gpt5_smoke.py)
- **Verification tools**: Commands to verify comprehensive AI workflows

### Usage

To use these commands in development, you can either:

1. **Copy back to apps/** - Copy the command to appropriate app's `management/commands/` directory
2. **Run directly** - Some commands can be run as standalone Python scripts

### Production Note

These tools should NOT be deployed to production. They are for development/testing only.