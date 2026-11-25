#!/usr/bin/env bash

set -u

usage() {
  echo "Usage: $0 [--user USER] [--restart] [--status] [--close]" >&2
  echo "" >&2
  echo "Open SSH control/master sockets for the CERN tunnels:" >&2
  echo "  - ~/.ssh/socket_lxtunnel" >&2
  echo "  - ~/.ssh/socket_dbloader-mtd" >&2
  echo "" >&2
  echo "Options:" >&2
  echo "  --user USER   SSH username to use (default: mtd)" >&2
  echo "  --restart     Close any existing sockets and reopen them" >&2
  echo "  --status      Just check the status of the sockets and exit" >&2
  echo "  --close       Close the sockets and exit" >&2
  echo "  -h, --help    Show this help" >&2
  echo ""
}

USER="mtd"
RESTART=false
STATUS=false
CLOSE=false

while [[ $# -gt 0 ]]; do
  case "$1" in
    --user)
      if [[ $# -lt 2 ]]; then
        echo "Error: --user requires a value." >&2
        usage
        exit 1
      fi
      USER="$2"
      shift 2
      ;;
    --restart)
      RESTART=true
      shift
      ;;
    --status)
      STATUS=true
      shift
      ;;
    --close)
      CLOSE=true
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Error: unknown argument: $1" >&2
      usage
      exit 1
      ;;
  esac
done

check_socket() {
  local socket_path="$1"
  local remote_host="$2"

  [[ -S "$socket_path" ]] && ssh -S "$socket_path" -O check "${USER}@${remote_host}" >/dev/null 2>&1
}

close_socket() {
  local socket_path="$1"
  local remote_host="$2"

  if [[ -S "$socket_path" ]]; then
    ssh -S "$socket_path" -O exit "${USER}@${remote_host}" >/dev/null 2>&1 || true
    rm -f "$socket_path"
  fi
}

report_status() {
  local lx_status=false
  local db_status=false

  if check_socket "$HOME/.ssh/socket_lxtunnel" "lxtunnel.cern.ch"; then
    echo "lxtunnel socket: OK"
    lx_status=true
  else
    echo "lxtunnel socket: NOT OPEN"
  fi

  if check_socket "$HOME/.ssh/socket_dbloader-mtd" "dbloader-mtd.cern.ch"; then
    echo "dbloader-mtd socket: OK"
    db_status=true
  else
    echo "dbloader-mtd socket: NOT OPEN"
  fi

  [[ "$lx_status" == true && "$db_status" == true ]]
}

if [[ "$STATUS" == true ]]; then
  report_status
  exit 0
fi

if [[ "$CLOSE" == true ]]; then
  close_socket "$HOME/.ssh/socket_lxtunnel" "lxtunnel.cern.ch"
  close_socket "$HOME/.ssh/socket_dbloader-mtd" "dbloader-mtd.cern.ch"
  echo "Closed sockets:"
  echo "  $HOME/.ssh/socket_lxtunnel"
  echo "  $HOME/.ssh/socket_dbloader-mtd"
  exit 0
fi

if [[ "$RESTART" == false ]]; then
  if report_status; then
    exit 0
  fi
  RESTART=true
fi

if [[ "$RESTART" == true ]]; then
  close_socket "$HOME/.ssh/socket_lxtunnel" "lxtunnel.cern.ch"
  close_socket "$HOME/.ssh/socket_dbloader-mtd" "dbloader-mtd.cern.ch"
fi

if ! check_socket "$HOME/.ssh/socket_lxtunnel" "lxtunnel.cern.ch"; then
  echo "Opening lxtunnel socket for ${USER}@lxtunnel.cern.ch ..."
  ssh -f -N -M -S "$HOME/.ssh/socket_lxtunnel" "${USER}@lxtunnel.cern.ch"
fi

if ! check_socket "$HOME/.ssh/socket_dbloader-mtd" "dbloader-mtd.cern.ch"; then
  echo "Opening dbloader socket for ${USER}@dbloader-mtd.cern.ch ..."
  ssh -f -N -M -S "$HOME/.ssh/socket_dbloader-mtd" \
    -o "ProxyCommand=ssh -S $HOME/.ssh/socket_lxtunnel -W %h:%p ${USER}@lxtunnel.cern.ch" \
    "${USER}@dbloader-mtd.cern.ch"
fi

if check_socket "$HOME/.ssh/socket_lxtunnel" "lxtunnel.cern.ch" && check_socket "$HOME/.ssh/socket_dbloader-mtd" "dbloader-mtd.cern.ch"; then
  echo "Sockets are ready:"
  echo "  $HOME/.ssh/socket_lxtunnel"
  echo "  $HOME/.ssh/socket_dbloader-mtd"
else
  echo "Socket setup failed. One or more sockets are not connected:" >&2
  if ! check_socket "$HOME/.ssh/socket_lxtunnel" "lxtunnel.cern.ch"; then
    echo "  - $HOME/.ssh/socket_lxtunnel (not ready)" >&2
  fi
  if ! check_socket "$HOME/.ssh/socket_dbloader-mtd" "dbloader-mtd.cern.ch"; then
    echo "  - $HOME/.ssh/socket_dbloader-mtd (not ready)" >&2
  fi
  exit 1
fi
