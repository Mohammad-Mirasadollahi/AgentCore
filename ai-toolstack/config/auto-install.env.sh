# Host dependency auto-install (sourced by ./ai-toolstack/install.sh).
# On-prem: downloads public RTK release from GitHub when RTK is missing.
#
# 0 = warn only; 1 = install when possible (default).
export AI_TOOLSTACK_AUTO_INSTALL=1

export AI_TOOLSTACK_AUTO_INSTALL_JQ=1
export AI_TOOLSTACK_AUTO_INSTALL_PIPX=1
export AI_TOOLSTACK_AUTO_INSTALL_NODE=0
export AI_TOOLSTACK_AUTO_INSTALL_RTK=1

# Pin RTK release (rtk-ai/rtk on GitHub). Override RTK_INSTALL_CMD for air-gapped installs.
export RTK_VERSION=0.43.0

# Node (when AI_TOOLSTACK_AUTO_INSTALL_NODE=1): root + apt only. Air-gap: preinstall node or set NODE_INSTALL_CMD.
# Set AI_TOOLSTACK_ALLOW_NODESOURCE=0 to skip NodeSource download; optional NODESETUP_URL to pin setup script URL.
