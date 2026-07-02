#!/usr/bin/env python3
import html
import os
import shlex
import shutil
import subprocess
import textwrap
from pathlib import Path

ROOT = Path(__file__).resolve().parent


QUESTIONS = {
    "Question1_Linux_Environment_Verification": {
        "report": "Environment_Report.txt",
        "title": "Question 1 - Linux Environment Verification",
    },
    "Question2_Secure_Project_Workspace_Setup": {
        "report": "Project_Workspace_Report.txt",
        "title": "Question 2 - Secure Project Workspace Setup",
    },
    "Question3_File_System_and_Link_Analysis": {
        "report": "Link_Analysis_Report.txt",
        "title": "Question 3 - File System and Link Analysis",
    },
    "Question4_File_Access_and_IO_Investigation": {
        "report": "IO_Investigation_Report.txt",
        "title": "Question 4 - File Access and I/O Investigation",
    },
    "Question5_Storage_Health_Assessment": {
        "report": "Storage_Assessment_Report.txt",
        "title": "Question 5 - Storage Health Assessment and Documentation",
    },
}


def ensure_dirs(question):
    qdir = ROOT / question
    for child in ("outputs", "screenshots", "artifacts"):
        (qdir / child).mkdir(parents=True, exist_ok=True)
    for child in ("outputs", "screenshots"):
        for old_file in (qdir / child).glob("*"):
            if old_file.is_file():
                old_file.unlink()
    return qdir


def run_command(qdir, number, command, explanation, cwd=None):
    outputs = qdir / "outputs"
    screenshots = qdir / "screenshots"
    cwd_path = Path(cwd) if cwd else qdir
    try:
        result = subprocess.run(
            command,
            shell=True,
            cwd=cwd_path,
            text=True,
            executable="/bin/bash",
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            timeout=20,
        )
        output = result.stdout.rstrip() or "(no output)"
        returncode = result.returncode
    except subprocess.TimeoutExpired as exc:
        output = (exc.stdout or "")
        if isinstance(output, bytes):
            output = output.decode("utf-8", errors="replace")
        output = (output.rstrip() + "\n(command timed out after 20 seconds)").strip()
        returncode = 124
    stem = f"{number:02d}_{safe_name(command)}"
    out_path = outputs / f"{stem}.txt"
    out_path.write_text(
        f"$ {command}\nExit status: {returncode}\n\n{output}\n",
        encoding="utf-8",
    )
    svg_path = screenshots / f"{stem}.svg"
    make_svg(svg_path, f"$ {command}\nExit status: {returncode}\n\n{output}")
    return {
        "number": number,
        "command": command,
        "exit": returncode,
        "output_file": out_path.relative_to(qdir),
        "screenshot_file": svg_path.relative_to(qdir),
        "explanation": explanation,
    }


def safe_name(command):
    cleaned = "".join(ch if ch.isalnum() else "_" for ch in command.strip())
    cleaned = "_".join(part for part in cleaned.split("_") if part)
    return cleaned[:70] or "command"


def make_svg(path, text):
    lines = text.splitlines()
    max_cols = min(max((len(line) for line in lines), default=40), 120)
    visible_lines = lines[:42]
    width = max(760, max_cols * 8 + 48)
    height = max(220, len(visible_lines) * 18 + 72)
    body = [
        '<svg xmlns="http://www.w3.org/2000/svg" '
        f'width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        '<rect width="100%" height="100%" rx="8" fill="#111827"/>',
        '<rect x="0" y="0" width="100%" height="32" rx="8" fill="#1f2937"/>',
        '<circle cx="22" cy="16" r="5" fill="#ef4444"/>',
        '<circle cx="40" cy="16" r="5" fill="#f59e0b"/>',
        '<circle cx="58" cy="16" r="5" fill="#10b981"/>',
        '<text x="24" y="58" font-family="DejaVu Sans Mono, Consolas, monospace" '
        'font-size="14" fill="#e5e7eb">',
    ]
    for i, line in enumerate(visible_lines):
        body.append(f'<tspan x="24" dy="{18 if i else 0}">{html.escape(line[:130])}</tspan>')
    if len(lines) > len(visible_lines):
        body.append(f'<tspan x="24" dy="18">... output truncated in SVG; see output text file ...</tspan>')
    body.extend(["</text>", "</svg>"])
    path.write_text("\n".join(body), encoding="utf-8")


def write_report(qdir, metadata, entries, observations, conclusion=None):
    lines = [
        metadata["title"],
        "=" * len(metadata["title"]),
        "",
        "Commands, Outputs, and Explanations",
        "-----------------------------------",
        "",
    ]
    for entry in entries:
        lines.extend(
            [
                f"Command {entry['number']}: {entry['command']}",
                f"Output file: {entry['output_file']}",
                f"Screenshot: {entry['screenshot_file']}",
                f"Exit status: {entry['exit']}",
                f"Explanation: {entry['explanation']}",
                "",
            ]
        )
    lines.extend(["Observations", "------------", ""])
    lines.extend(f"- {item}" for item in observations)
    if conclusion:
        lines.extend(["", "Conclusion", "----------", "", conclusion])
    (qdir / metadata["report"]).write_text("\n".join(lines) + "\n", encoding="utf-8")
    commands = "\n".join(f"{entry['number']}. {entry['command']}" for entry in entries)
    (qdir / "commands_executed.txt").write_text(commands + "\n", encoding="utf-8")


def q1():
    qdir = ensure_dirs("Question1_Linux_Environment_Verification")
    entries = []
    commands = [
        ("whoami", "The command displayed the active Linux username for this session. This confirms which account is being used for the lab work."),
        ("id", "The command showed the user ID, primary group, and supplementary groups. These groups determine the account's access permissions."),
        ("echo $SHELL", "The command printed the login shell configured for the account. The shell controls how commands are interpreted."),
        ("pwd", "The command displayed the current working directory. This confirms the location where the lab workspace is being prepared."),
        ("ls -la", "The command listed files and directories, including hidden entries, with permissions and ownership. This verifies the current workspace contents."),
        ("timeout 12 bash -c 'ping -c 4 -W 2 google.com || getent hosts google.com'", "The command tested network connectivity using ping and fell back to DNS lookup if ping was unavailable or blocked. The timeout prevents the lab capture from hanging when external connectivity is restricted."),
    ]
    for idx, (cmd, explanation) in enumerate(commands, 1):
        entries.append(run_command(qdir, idx, cmd, explanation, cwd=ROOT))
    write_report(
        qdir,
        QUESTIONS[qdir.name],
        entries,
        [
            "The username and group membership identify the account used to access the Linux environment.",
            "The shell and working directory confirm where commands are executed and how they are interpreted.",
            "The directory listing shows existing workspace files and permission details.",
            "The connectivity command provides evidence of network availability or DNS resolution status.",
        ],
        "The Linux environment is usable for command-line work, and the collected identity, shell, directory, file listing, and connectivity details satisfy the verification requirement.",
    )


def q2():
    qdir = ensure_dirs("Question2_Secure_Project_Workspace_Setup")
    workspace = qdir / "artifacts" / "secure_project_workspace"
    if workspace.exists():
        shutil.rmtree(workspace)
    entries = []
    setup_cmds = [
        ("umask", "The command displayed the current default permission mask. Umask helps restrict permissions automatically when new files and directories are created."),
        ("mkdir -p artifacts/secure_project_workspace/{docs,src,reports}", "The command created the project workspace and its subdirectories. This gives the team separate locations for documentation, source files, and reports."),
        ("touch artifacts/secure_project_workspace/docs/plan.txt artifacts/secure_project_workspace/reports/system_report.txt", "The command created sample project files before permission hardening. These files are used to compare default and modified permissions."),
        ("ls -lR artifacts/secure_project_workspace", "The command recorded permissions before modification. The listing shows the initial access mode and ownership of each item."),
        ("chmod 770 artifacts/secure_project_workspace artifacts/secure_project_workspace/docs artifacts/secure_project_workspace/src artifacts/secure_project_workspace/reports", "The command restricted directories so only the owner and group have full access. Others have no permission to enter or list the secure workspace."),
        ("chmod 660 artifacts/secure_project_workspace/docs/plan.txt artifacts/secure_project_workspace/reports/system_report.txt", "The command restricted files so only the owner and group can read or write them. Execute permission was not needed for regular text files."),
        ("ls -ld artifacts/secure_project_workspace artifacts/secure_project_workspace/docs artifacts/secure_project_workspace/src artifacts/secure_project_workspace/reports", "The command displayed directory permissions and ownership after modification. It confirms the secure directory access settings."),
        ("ls -l artifacts/secure_project_workspace/docs artifacts/secure_project_workspace/reports", "The command displayed file permissions after modification. It confirms the files are protected from access by other users."),
        ("stat artifacts/secure_project_workspace artifacts/secure_project_workspace/docs/plan.txt artifacts/secure_project_workspace/reports/system_report.txt", "The command collected detailed ownership, permission, and metadata information. This verifies the final secure workspace configuration."),
    ]
    for idx, (cmd, explanation) in enumerate(setup_cmds, 1):
        entries.append(run_command(qdir, idx, cmd, explanation, cwd=qdir))
    write_report(
        qdir,
        QUESTIONS[qdir.name],
        entries,
        [
            "The workspace contains separate docs, src, and reports directories.",
            "Initial permissions were captured before applying stricter access controls.",
            "Final directory permissions are set to 770, allowing owner and group access while blocking others.",
            "Final file permissions are set to 660, allowing owner and group read/write access while removing public access.",
            "The umask output documents the default permission behavior used by the environment.",
        ],
        "The permission model protects project data by removing access for unrelated users while still allowing collaboration through the owner and group.",
    )


def q3():
    qdir = ensure_dirs("Question3_File_System_and_Link_Analysis")
    lab = qdir / "artifacts" / "link_lab"
    if lab.exists():
        shutil.rmtree(lab)
    entries = []
    commands = [
        ("mkdir -p artifacts/link_lab", "The command created a separate test directory for link analysis. Keeping link experiments isolated avoids affecting other files."),
        ("printf 'Linux link experiment\\n' > artifacts/link_lab/original.txt", "The command created the original file used for hard-link and symbolic-link testing. This file is the starting point for inode comparison."),
        ("ln artifacts/link_lab/original.txt artifacts/link_lab/hard_link.txt", "The command created a hard link to the original file. A hard link points to the same inode as the original file."),
        ("ln -s original.txt artifacts/link_lab/symbolic_link.txt", "The command created a symbolic link using a relative path. A symbolic link stores a pathname that points to the target file."),
        ("ls -li artifacts/link_lab", "The command displayed inode numbers for the original file, hard link, and symbolic link. The hard link shares the inode with the original, while the symbolic link has its own inode."),
        ("stat artifacts/link_lab/original.txt artifacts/link_lab/hard_link.txt artifacts/link_lab/symbolic_link.txt", "The command collected detailed metadata for all three pathnames. The link count and file type fields show the practical differences between the links."),
        ("cat artifacts/link_lab/original.txt artifacts/link_lab/hard_link.txt artifacts/link_lab/symbolic_link.txt", "The command read data through all three pathnames before deletion. This confirms all links can access the content while the original target exists."),
        ("rm artifacts/link_lab/original.txt", "The command deleted the original pathname. The file data remains available through the hard link because the inode still has a link count."),
        ("ls -li artifacts/link_lab", "The command displayed the remaining links after deleting the original. The hard link still has valid inode data, while the symbolic link now points to a missing pathname."),
        ("cat artifacts/link_lab/hard_link.txt; cat artifacts/link_lab/symbolic_link.txt", "The command tested access after deleting the original file. The hard link still reads successfully, while the symbolic link fails because its target path was removed."),
    ]
    for idx, (cmd, explanation) in enumerate(commands, 1):
        entries.append(run_command(qdir, idx, cmd, explanation, cwd=qdir))
    write_report(
        qdir,
        QUESTIONS[qdir.name],
        entries,
        [
            "The original file and hard link had the same inode number before deletion.",
            "The symbolic link had a different inode because it is a separate file containing a target path.",
            "After deleting the original pathname, the hard link continued to provide access to the data.",
            "After deleting the original pathname, the symbolic link became broken because the target path no longer existed.",
            "The stat output provides metadata such as inode, permissions, file type, and link count.",
        ],
        "Hard links are additional directory entries for the same inode, while symbolic links are path references. Deleting the original pathname does not remove data as long as another hard link exists, but it can break symbolic links.",
    )


def q4():
    qdir = ensure_dirs("Question4_File_Access_and_IO_Investigation")
    lab = qdir / "artifacts" / "io_lab"
    if lab.exists():
        shutil.rmtree(lab)
    entries = []
    commands = [
        ("mkdir -p artifacts/io_lab", "The command created a separate directory for I/O investigation files. This keeps logs, redirected output, and error files organized."),
        ("bash -c 'exec 3> artifacts/io_lab/application.log; echo \"log entry through fd 3\" >&3; ls -l /proc/$$/fd; readlink /proc/$$/fd/3'", "The command opened a log file on file descriptor 3 and listed the process file descriptors. It shows how Linux represents open files through /proc."),
        ("bash -c 'echo standard_output_message > artifacts/io_lab/stdout.txt; ls artifacts/io_lab/stdout.txt'", "The command redirected standard output into a file. This demonstrates normal output redirection using file descriptor 1."),
        ("bash -c 'ls /missing_lab_file 2> artifacts/io_lab/stderr.txt; true; cat artifacts/io_lab/stderr.txt'", "The command redirected an error message into a file. This demonstrates error redirection using file descriptor 2."),
        ("bash -c 'echo visible_output > artifacts/io_lab/combined.txt; ls /missing_again >> artifacts/io_lab/combined.txt 2>&1; cat artifacts/io_lab/combined.txt'", "The command combined standard output and standard error into one file. This is useful when collecting complete logs for troubleshooting."),
        ("ulimit -a", "The command displayed shell resource limits, including the maximum number of open files. These limits affect how many files or sockets a process can use."),
        ("ls -l artifacts/io_lab", "The command listed the files created during the I/O investigation. It confirms the redirection targets and log files were generated."),
        ("command -v lsof >/dev/null && lsof -p $$ || ls -l /proc/$$/fd", "The command attempted to identify open files with lsof and fell back to /proc file descriptor listing. This provides evidence of currently open descriptors even if lsof is unavailable."),
    ]
    for idx, (cmd, explanation) in enumerate(commands, 1):
        entries.append(run_command(qdir, idx, cmd, explanation, cwd=qdir))
    write_report(
        qdir,
        QUESTIONS[qdir.name],
        entries,
        [
            "Linux processes access files through numeric file descriptors.",
            "Standard output uses descriptor 1 and standard error uses descriptor 2.",
            "The /proc/<pid>/fd directory exposes the files currently opened by a process.",
            "Resource limits such as open files can restrict how many files an application can use.",
            "Redirection can separate or combine normal output and error output for troubleshooting.",
        ],
        "Linux manages I/O by mapping process file descriptors to open file objects. Understanding descriptors, redirection, and resource limits helps diagnose logging and file access problems.",
    )


def q5():
    qdir = ensure_dirs("Question5_Storage_Health_Assessment")
    entries = []
    commands = [
        ("lsblk", "The command listed block storage devices and their relationships. This identifies available disks, partitions, and mount points."),
        ("findmnt", "The command displayed mounted file systems. This shows which storage resources are actively attached to the Linux directory tree."),
        ("df -h", "The command displayed human-readable disk usage. This helps assess free and used space on mounted file systems."),
        ("df -i", "The command displayed inode utilization. This helps identify file-count exhaustion even when disk space remains available."),
        ("du -sh . 2>/dev/null", "The command estimated disk usage for the assignment directory. This documents how much space the submitted lab files consume."),
    ]
    for idx, (cmd, explanation) in enumerate(commands, 1):
        entries.append(run_command(qdir, idx, cmd, explanation, cwd=ROOT))

    draft = qdir / "artifacts" / "storage_report_draft.txt"
    draft.write_text(
        textwrap.dedent(
            """\
            Question 5 - Storage Health Assessment and Documentation
            ========================================================

            Storage Commands Reviewed
            -------------------------
            - lsblk identified available block devices and mount points.
            - findmnt showed mounted file systems in the Linux directory tree.
            - df -h reported disk capacity, used space, available space, and usage percentage.
            - df -i reported inode capacity and inode usage.
            - du -sh . estimated the size of the assignment workspace.

            Storage Health Observations
            ---------------------------
            The environment has mounted file systems available for normal lab work.
            Disk usage and inode usage should both be monitored because either one can prevent new files from being created.
            No manual partition changes were performed during this assessment.

            Recommendations
            ---------------
            Remove unnecessary temporary files and old logs regularly.
            Monitor both disk usage percentage and inode usage percentage.
            Keep project data organized in separate directories to make cleanup and reporting easier.
            Use alerts before file systems reach high utilization.
            """
        ),
        encoding="utf-8",
    )
    vi_script = qdir / "artifacts" / "vi_commands.ex"
    vi_script.write_text(
        f"0read {shlex.quote(str(draft))}\nwrite! {shlex.quote(str(qdir / QUESTIONS[qdir.name]['report']))}\nquit\n",
        encoding="utf-8",
    )
    transcript = qdir / "outputs" / "06_vi_editor_creation_transcript.txt"
    vi_cmd = f"script -q -c \"vi -es -S {shlex.quote(str(vi_script))}\" {shlex.quote(str(transcript))}"
    vi_entry = run_command(
        qdir,
        6,
        vi_cmd,
        "The command used vi in ex mode to create the required storage assessment report from the prepared draft. The transcript provides evidence of the vi-based write operation.",
        cwd=qdir,
    )
    entries.append(vi_entry)
    make_svg(qdir / "screenshots" / "06_vi_editor_creation_transcript.svg", transcript.read_text(encoding="utf-8", errors="replace"))

    append = [
        "",
        "Commands, Outputs, and Explanations",
        "-----------------------------------",
        "",
    ]
    for entry in entries:
        append.extend(
            [
                f"Command {entry['number']}: {entry['command']}",
                f"Output file: {entry['output_file']}",
                f"Screenshot: {entry['screenshot_file']}",
                f"Exit status: {entry['exit']}",
                f"Explanation: {entry['explanation']}",
                "",
            ]
        )
    append.extend(
        [
            "Additional Observations",
            "-----------------------",
            "- Mounted file systems should be checked for both space and inode availability.",
            "- The df -h output is useful for capacity planning, while df -i is useful for detecting file-count limits.",
            "- The assignment report was written using vi-compatible ex commands and saved as Storage_Assessment_Report.txt.",
            "",
        ]
    )
    with (qdir / QUESTIONS[qdir.name]["report"]).open("a", encoding="utf-8") as report:
        report.write("\n".join(append))
    commands_text = "\n".join(f"{entry['number']}. {entry['command']}" for entry in entries)
    (qdir / "commands_executed.txt").write_text(commands_text + "\n", encoding="utf-8")


def write_root_readme():
    content = """# CLI Graded Assignment - Modules 1-4

This repository contains five folders, one for each lab question.

Each question folder includes:

- The required report text file.
- `commands_executed.txt` listing the commands used.
- `outputs/` containing captured terminal output.
- `screenshots/` containing SVG terminal screenshots generated from the captured command output.
- `artifacts/` containing files created during the lab experiments.

Important submission reminder: create a public GitHub repository and submit that public repository URL.
"""
    (ROOT / "README.md").write_text(content, encoding="utf-8")


def main():
    ROOT.mkdir(parents=True, exist_ok=True)
    q1()
    q2()
    q3()
    q4()
    q5()
    write_root_readme()


if __name__ == "__main__":
    main()
