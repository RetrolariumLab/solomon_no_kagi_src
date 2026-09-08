#!/usr/bin/env python3
"""Check or normalize the project's ca65 assembly style."""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


MNEMONICS = frozenset(
    """
    ADC AND ASL BCC BCS BEQ BIT BMI BNE BPL BRK BVC BVS CLC CLD CLI CLV
    CMP CPX CPY DEC DEX DEY EOR INC INX INY JMP JSR LDA LDX LDY LSR NOP
    ORA PHA PHP PLA PLP ROL ROR RTI RTS SBC SEC SED SEI STA STX STY TAX
    TAY TSX TXA TXS TYA
    """.split()
)
DATA_DIRECTIVES = frozenset(
    {".addr", ".asciiz", ".byte", ".dbyt", ".faraddr", ".incbin", ".literal", ".res", ".tag", ".word"}
)
BLOCK_OPENERS = frozenset(
    {".enum", ".macro", ".proc", ".repeat", ".scope", ".struct", ".union"}
)
BLOCK_CLOSERS = frozenset(
    {".endenum", ".endmacro", ".endproc", ".endrepeat", ".endscope", ".endstruct", ".endunion"}
)
BLOCK_MIDDLES = frozenset({".else", ".elseif"})
DIRECTIVE_RE = re.compile(r"^\.[A-Za-z][A-Za-z0-9]*")
LABEL_RE = re.compile(r"^(?P<label>[A-Za-z_@.?][A-Za-z0-9_@.?]*:)(?P<tail>.*)$")
TOKEN_RE = re.compile(r"^[A-Za-z][A-Za-z0-9]*")
ASSIGNMENT_RE = re.compile(r"^[A-Za-z_@.?][A-Za-z0-9_@.?]*\s*=")
MACHINE_CODE_COMMENT_RE = re.compile(
    r"^\$[0-9A-Fa-f]{4}(?:\s+[0-9A-Fa-f]{2})*$"
)


@dataclass(frozen=True)
class Issue:
    path: Path
    line: int
    code: str
    message: str

    def render(self) -> str:
        return f"{self.path.as_posix()}:{self.line}: [{self.code}] {self.message}"


def split_comment(line: str) -> tuple[str, str | None]:
    quote: str | None = None
    escaped = False
    for index, character in enumerate(line):
        if escaped:
            escaped = False
        elif character == "\\" and quote is not None:
            escaped = True
        elif quote is not None:
            if character == quote:
                quote = None
        elif character in {'"', "'"}:
            quote = character
        elif character == ";":
            return line[:index], line[index + 1 :]
    return line, None


def source_files(paths: Iterable[Path]) -> list[Path]:
    files: set[Path] = set()
    for path in paths:
        if path.is_dir():
            files.update(path.rglob("*.asm"))
            files.update(path.rglob("*.inc"))
        elif path.suffix.lower() in {".asm", ".inc"}:
            files.add(path)
    return sorted(files, key=lambda item: item.as_posix().lower())


def is_opener(directive: str) -> bool:
    return directive in BLOCK_OPENERS or directive.startswith(".if")


def is_closer(directive: str) -> bool:
    return directive in BLOCK_CLOSERS or directive == ".endif"


def statement_indent(depth: int) -> int:
    return max(depth, 1) * 4


def directive_indent(directive: str, depth: int) -> int:
    if is_closer(directive) or directive in BLOCK_MIDDLES:
        return max(depth - 1, 0) * 4
    if is_opener(directive):
        return depth * 4
    return statement_indent(depth) if directive in DATA_DIRECTIVES else depth * 4


def next_depth(directive: str, depth: int) -> int:
    if is_closer(directive):
        return max(depth - 1, 0)
    return depth + 1 if is_opener(directive) else depth


def lint_file(path: Path) -> list[Issue]:
    try:
        payload = path.read_bytes()
        text = payload.decode("utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        return [Issue(path, 1, "read-error", str(exc))]

    issues: list[Issue] = []
    if b"\r" in payload:
        issues.append(Issue(path, 1, "line-ending", "use LF line endings"))
    if not payload.endswith(b"\n") or payload.endswith(b"\n\n"):
        issues.append(Issue(path, 1, "final-newline", "file must end with exactly one LF"))
    for line_number, line in enumerate(text.splitlines(), 1):
        if any(character not in "\t" and not " " <= character <= "~" for character in line):
            issues.append(Issue(path, line_number, "ascii-only", "only printable ASCII and LF are allowed"))
        if "\t" in line:
            issues.append(Issue(path, line_number, "tab", "tabs are not allowed"))
        if line.rstrip(" \t") != line:
            issues.append(Issue(path, line_number, "trailing-whitespace", "remove trailing whitespace"))

    lines = text.splitlines()
    if lines and not lines[0].strip():
        issues.append(Issue(path, 1, "file-start", "remove blank lines at the start"))
    depth = 0
    previous_blank = False
    for line_number, line in enumerate(lines, 1):
        if not line.strip():
            if previous_blank:
                issues.append(Issue(path, line_number, "blank-lines", "keep at most one consecutive blank line"))
            previous_blank = True
            continue
        previous_blank = False
        before, comment = split_comment(line)
        if comment is not None:
            content = comment.strip()
            if not comment.startswith(" ") or comment.startswith("  "):
                issues.append(Issue(path, line_number, "comment-space", "use exactly one space after ';'"))
            if content.endswith("."):
                issues.append(Issue(path, line_number, "comment-period", "remove the terminal comment period"))
            if MACHINE_CODE_COMMENT_RE.fullmatch(content):
                issues.append(
                    Issue(
                        path,
                        line_number,
                        "machine-code-comment",
                        "remove the address/byte dump or add a meaningful explanation",
                    )
                )
            if before.strip() and len(before) - len(before.rstrip(" ")) != 2:
                issues.append(Issue(path, line_number, "inline-comment-gap", "use two spaces before an inline comment"))
        if not before.strip():
            if before:
                issues.append(Issue(path, line_number, "comment-indent", "standalone comments start at column zero"))
            continue

        leading = len(before) - len(before.lstrip(" "))
        statement = before.strip()
        label = LABEL_RE.match(statement)
        if label:
            if leading:
                issues.append(Issue(path, line_number, "label-indent", "labels start at column zero"))
            if comment is not None or label.group("tail").strip():
                issues.append(Issue(path, line_number, "label-line", "put labels and statements on separate lines"))
            continue
        directive = DIRECTIVE_RE.match(statement)
        if directive:
            token = directive.group(0)
            normalized = token.lower()
            if token != normalized:
                issues.append(Issue(path, line_number, "directive-case", "write directives in lowercase"))
            if leading != directive_indent(normalized, depth):
                issues.append(Issue(path, line_number, "directive-indent", "incorrect directive indentation"))
            rest = statement[len(token) :]
            if rest and (not rest.startswith(" ") or rest.startswith("  ")):
                issues.append(Issue(path, line_number, "operand-gap", "use one space before operands"))
            depth = next_depth(normalized, depth)
            continue
        token = TOKEN_RE.match(statement)
        if token and token.group(0).upper() in MNEMONICS:
            mnemonic = token.group(0)
            if mnemonic != mnemonic.upper():
                issues.append(Issue(path, line_number, "mnemonic-case", "write mnemonics in uppercase"))
            if leading != statement_indent(depth):
                issues.append(Issue(path, line_number, "instruction-indent", "incorrect instruction indentation"))
            rest = statement[len(mnemonic) :]
            if rest and (not rest.startswith(" ") or rest.startswith("  ")):
                issues.append(Issue(path, line_number, "operand-gap", "use one space before operands"))
        elif ASSIGNMENT_RE.match(statement):
            if leading:
                issues.append(Issue(path, line_number, "assignment-indent", "assignments start at column zero"))
        elif leading != statement_indent(depth):
            issues.append(Issue(path, line_number, "statement-indent", "incorrect statement indentation"))
    if depth:
        issues.append(Issue(path, len(lines) or 1, "block-depth", f"{depth} assembly block(s) not closed"))
    return issues


def compose(code: str, comment: str | None) -> str:
    if comment is None:
        return code
    content = comment.strip().rstrip(".")
    if not content:
        return code
    if MACHINE_CODE_COMMENT_RE.fullmatch(content):
        return code
    return f"{code}  ; {content}" if code else f"; {content}"


def normalize_statement(statement: str, depth: int) -> tuple[str, int]:
    label = LABEL_RE.match(statement)
    if label and not label.group("tail").strip():
        return label.group("label"), depth
    directive = DIRECTIVE_RE.match(statement)
    if directive:
        token = directive.group(0).lower()
        rest = statement[len(directive.group(0)) :].strip()
        code = token if not rest else f"{token} {rest}"
        return " " * directive_indent(token, depth) + code, next_depth(token, depth)
    token = TOKEN_RE.match(statement)
    if token and token.group(0).upper() in MNEMONICS:
        mnemonic = token.group(0).upper()
        rest = statement[len(token.group(0)) :].strip()
        code = mnemonic if not rest else f"{mnemonic} {rest}"
        return " " * statement_indent(depth) + code, depth
    if ASSIGNMENT_RE.match(statement):
        return statement, depth
    return " " * statement_indent(depth) + statement, depth


def format_file(path: Path) -> bool:
    original = path.read_text(encoding="utf-8")
    logical: list[tuple[str, str | None]] = []
    for raw in original.replace("\r\n", "\n").replace("\r", "\n").split("\n"):
        before, comment = split_comment(raw.expandtabs(4).rstrip())
        statement = before.strip()
        label = LABEL_RE.match(statement)
        if label and label.group("tail").strip():
            logical.extend(((label.group("label"), None), (label.group("tail").strip(), comment)))
        elif label and comment is not None:
            logical.extend((("", comment), (label.group("label"), None)))
        else:
            logical.append((statement, comment))

    output: list[str] = []
    depth = 0
    for statement, comment in logical:
        if statement:
            code, depth = normalize_statement(statement, depth)
            line = compose(code, comment)
        else:
            line = compose("", comment)
        if line:
            output.append(line)
        elif output and output[-1]:
            output.append("")
    while output and not output[-1]:
        output.pop()
    normalized = "\n".join(output) + "\n"
    if normalized == original:
        return False
    path.write_text(normalized, encoding="utf-8", newline="\n")
    return True


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("paths", nargs="*", type=Path, default=[Path("src")])
    parser.add_argument("--fix", action="store_true")
    args = parser.parse_args()
    files = source_files(args.paths)
    if not files:
        print("[ERROR] No .asm or .inc source files found", file=sys.stderr)
        return 1
    changed = sum(format_file(path) for path in files) if args.fix else 0
    issues = [issue for path in files for issue in lint_file(path)]
    if issues:
        for issue in issues:
            print(issue.render(), file=sys.stderr)
        print(f"[ERROR] Assembly style check failed with {len(issues)} issue(s)", file=sys.stderr)
        return 1
    action = f"Formatted {changed} and validated" if args.fix else "Validated"
    print(f"[OK] {action} {len(files)} assembly source files")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
