#!/usr/bin/env bash
# Linux terminal cheat sheet — run individual commands, don't execute this whole file

# ── Navigation ──────────────────────────────────────────────────
pwd          # print working directory
ls -la       # list files (long format, including hidden)
cd projects/ # change into a directory

# ── Create / Copy / Move / Remove ───────────────────────────────
mkdir notes
cp a.txt b.txt
mv b.txt archive/
rm old_file.txt

# ── Read & Edit ─────────────────────────────────────────────────
cat notes.txt        # print file to terminal
nano notes.txt       # simple terminal text editor

# ── System / Admin ──────────────────────────────────────────────
sudo apt update      # refresh package list
sudo apt upgrade     # apply updates
uname -a             # kernel / OS info
whoami               # current user
