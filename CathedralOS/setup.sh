#!/usr/bin/env bash
# ==============================================================================
# TERMUX ENVIRONMENT INITIALIZER & WORKSPACE SETUP
# ==============================================================================
# A unified automation script to prepare the core toolchain, clean up packages,
# configure system architecture directories, and inject optimized bash shortcuts.
# ==============================================================================

set -e # Exit immediately if a command exits with a non-zero status

echo "[*] Initiating Termux environment alignment..."

# 1. Update Core Repositories & Packages
echo "[*] Updating package mirrors and upgrading existing tools..."
pkg update -y && pkg upgrade -y

# 2. Install Essential Toolchains and Utilities
echo "[*] Installing development packages, compilers, and utilities..."
pkg install -y \
    coreutils \
    build-essential \
    clang \
    make \
    cmake \
    git \
    tur-repo \
    termux-api \
    nano \
    vim \
    curl \
    wget \
    tree \
    htop

# 3. Establish Structured Workspace Directory Tree
echo "[*] Setting up localized workspace directories..."
mkdir -p ~/workspace/core
mkdir -p ~/workspace/projects
mkdir -p ~/workspace/archive
mkdir -p ~/.config

# 4. Configure Environmental Shortcuts (~/.bashrc)
echo "[*] Injecting optimized aliases and shell configurations..."
BASHRC="$HOME/.bashrc"

# Back up existing bashrc if it exists
if [ -f "$BASHRC" ]; then
    cp "$BASHRC" "${BASHRC}.bak"
fi

cat << 'EOF' > "$BASHRC"
# --- Termux Custom Environment Config ---

# Color definitions for prompt
COLOR_BLUE="\[\033[01;34m\]"
COLOR_GREEN="\[\033[01;32m\]"
COLOR_CYAN="\[\033[01;36m\]"
COLOR_RESET="\[\033[00m\]"

# Clean, structured prompt design
export PS1="${COLOR_CYAN}[Termux]${COLOR_GREEN} \w ${COLOR_BLUE}-->${COLOR_RESET} "

# General Quality of Life Aliases
alias ls='ls --color=auto -h'
alias ll='ls -la'
alias grep='grep --color=auto'
alias ..='cd ..'
alias ...='cd ../..'
alias htop='htop -d 10'

# Navigation Shortcuts
alias ws='cd ~/workspace'
alias wsc='cd ~/workspace/core'
alias wsp='cd ~/workspace/projects'

# Git Workflow Accelerators
alias gs='git status'
alias gd='git diff'
alias ga='git add'
alias gcm='git commit -m'
alias gpl='git pull'
alias gps='git push'
alias gl='git log --oneline --graph --decorate'

# Quick System Checks
alias sysinfo='echo "OS: Termux $(uname -o)"; echo "Kernel: $(uname -r)"; echo "Uptime: $(uptime -p)"'
alias mem='free -h'

# Welcome Banner
clear
sysinfo
echo -e "\n${COLOR_GREEN}Workspace core ready. Access your projects with 'ws'.${COLOR_RESET}\n"
EOF

# 5. Request Storage Permissions (Crucial for cross-device file interaction)
echo "[*] Requesting Android storage permission bridge..."
echo "Please accept the system storage prompt if it appears on screen."
termux-setup-storage

# 6. Finalization
echo "=============================================================================="
echo "[+] Setup complete! Reloading environment..."
echo "=============================================================================="

# Reload bash profile to apply changes immediately
source "$BASHRC"

