# Claude Code Guidelines for cnd-teanga Project

## Python Code Standards

### Exception Handling
- **Avoid long try-except blocks** - keep them focused and minimal
- **Never use generic `Exception`** - always catch specific exception types
- Use multiple specific exception handlers rather than one broad catch-all

### Logging Standards
- **Build logging into scripts from the start** - it's not optional
- Follow proper log levels:
  - `INFO` - Key milestones, workflow progress, successful operations
  - `DEBUG` - Detailed diagnostic information, data dumps, trace info
  - `WARNING` - Something unexpected but recoverable happened
  - `ERROR` - Operation failed but application continues
  - `CRITICAL` - System-level failure

- **More logging is better than less**, but must be tunable
- Enable log level filtering so we can turn off the firehose when needed
- **Use colors, formatting, and emojis** to enhance log readability
  - Make logs human-friendly AND machine-parseable
  - This is a log-heavy project where logs will be consumed by other agents
  - Clear, well-formatted logs are critical for debugging complex orchestrations

### Log Consumption Pattern
- Logs will frequently be read and analyzed by other AI agents
- Lack of visibility into system state makes complex systems hard to debug
- Design logs with both human operators and automated analysis in mind

### File Naming Conventions
- **Never use `test_*.py` for demo/trial scripts** - this prefix is reserved for unit tests
- Use descriptive names like `demo_*.py`, `try_*.py`, `run_*.py`, or `example_*.py` for experimental scripts
- Keep `test_*.py` exclusively for proper unit tests in the `tests/` directory

## Collaboration Style

### Decision Making
- **When asked "should we X?" - DO NOT implement X immediately**
- Wait for confirmation and discussion first
- Offer multiple solution options when available (within reason)
- Present trade-offs clearly

### Technology Constraints

#### Conductor Framework
- **Stick to using Orkes Conductor** for orchestration
- Use the **Python SDK for Conductor**
- **We are using `conductor-oss`** (open source version)
- **NOT using enterprise Orkes Conductor** - no enterprise-only features
- Always double-check suggested approaches don't require enterprise features

#### Reference Materials
- Local repositories available at `~/projects/git/`:
  - Check these repos when in doubt about OSS vs Enterprise features
  - Reference actual conductor-oss capabilities and examples

## Project Context
This is an AI orchestration project for Irish language (Gaeilge) learning materials:
- Multi-agent workflows (Claude + OpenAI)
- Audio processing and transcription
- Complex workflow chains in Conductor
- High observability requirements due to system complexity

---

**Last Updated:** October 2025
**Project:** Conductor's Gaeilge Lab
